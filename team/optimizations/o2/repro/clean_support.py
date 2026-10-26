"""Build the unchanged team NEMU extension and AM libraries from clean sources."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import clean_prepare as prepare


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(args):
    out, repo, am = args.output.resolve(), args.repo.resolve(), args.am_home.resolve()
    prepare.require(not out.exists(), "preserve previous support build")
    prepare.require(not (am / "am/build").exists() and not (am / "libs/klib/build").exists(),
                    "AM libraries must start without build outputs")
    cpus = sorted(os.sched_getaffinity(0))[:4]
    os.sched_setaffinity(0, cpus)
    out.mkdir(parents=True)
    state = dict(contract="t17-clean-support-v1", status="PREPARING", started=prepare.now(),
                 executor=args.executor, cpu_affinity=cpus, jobs_per_component=2,
                 generated_products_copied=False, official_authoritative_programs_modified=False)
    prepare.save(out / "state.json", state)
    records = []
    guard = load("t17_support_guard", repo / "team/scripts/artifact_guard.py")
    manifest = json.loads((repo / "team/patches/nemu/manifest.json").read_text())
    driver = repo / "team/scripts/prepare-nemu-vdot.sh"
    prepare.require(sha(driver) == "bef805d62c5b64aedae63c295c1bb0a8d065147c48187a2ca7406afb92348e8a",
                    "team NEMU preparation recipe changed")
    env = {k: v for k, v in os.environ.items() if k in
           ("HOME", "USER", "LOGNAME", "PATH", "LANG", "LC_ALL", "SHELL", "http_proxy", "https_proxy", "NO_PROXY")}
    env.update(TEAM_XS_ENV_ROOT=str(args.environment_root.resolve()),
               TEAM_NEMU_VDOT_ROOT=str(out / "nemu"), TEAM_NEMU_BASE_ROOT=str(out / "nemu/base"),
               TEAM_EVIDENCE_DIR=str(out / "nemu-evidence"), BUILD_JOBS="2", OMP_NUM_THREADS="1",
               AM_HOME=str(am), LINUX_GNU_TOOLCHAIN="1")
    try:
        with (out / "source-restore.log").open("wb") as log:
            for component in ("base", "reference"):
                target = out / "nemu" / component
                prepare.restore(args.nemu_source, target, manifest["base_rev"], records, log)
                for relative, revision in guard.DEPENDENCIES.items():
                    prepare.restore(args.nemu_cache / relative, target / relative, revision, records, log)
        prepare.save(out / "repositories.json", records)
        for component in ("base", "reference"):
            prepare.require(not (out / "nemu" / component / "build").exists(), "NEMU build output copied")
        am_sources = guard.audit_repo(am, "086a238062fdfb3281b745a537b361983d0154b5",
                                     source_roots=("am/src", "am/include", "libs/klib/src", "libs/klib/include"))
        prepare.save(out / "am-source-before.json", am_sources)
        state.update(status="BUILDING", commands={
            "nemu": ["bash", str(driver), "reference"],
            "am": ["make", "-C", str(am / "am"), "ARCH=riscv64-xs", "CROSS_COMPILE=riscv64-linux-gnu-", "-j2"],
            "klib": ["make", "-C", str(am / "libs/klib"), "ARCH=riscv64-xs", "CROSS_COMPILE=riscv64-linux-gnu-", "-j2"],
        })
        prepare.save(out / "state.json", state)

        def run(name):
            command = state["commands"][name]
            before = prepare.now()
            with (out / (name + ".stdout.log")).open("wb") as stdout, (out / (name + ".stderr.log")).open("wb") as stderr:
                result = subprocess.run(command, cwd=repo, env=env, stdout=stdout, stderr=stderr)
            receipt = dict(command=command, cwd=str(repo), started=before, finished=prepare.now(),
                           exit_code=result.returncode, process_executed=True,
                           raw_sha256={suffix: sha(out / (name + "." + suffix)) for suffix in ("stdout.log", "stderr.log")})
            prepare.save(out / (name + "-command.json"), receipt)
            prepare.require(result.returncode == 0, "support component failed: " + name)

        def libraries():
            run("am")
            run("klib")

        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(run, "nemu"), pool.submit(libraries)]
            for job in jobs:
                job.result()
        reference = out / "nemu/reference/build/riscv64-nemu-interpreter-so"
        provenance = guard.verify_nemu(reference.parents[1], reference, "reference")
        prepare.save(out / "verified-nemu.json", provenance)
        after = guard.audit_repo(am, "086a238062fdfb3281b745a537b361983d0154b5",
                                source_roots=("am/src", "am/include", "libs/klib/src", "libs/klib/include"))
        prepare.require(am_sources == after, "AM source changed during build")
        state.update(status="T17_CLEAN_SUPPORT_BUILD_PASS", reference=str(reference),
                     reference_sha256=sha(reference), am_home=str(am),
                     am_libraries={str(am / n): sha(am / n) for n in
                                   ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")},
                     team_patch_manifest_sha256=sha(repo / "team/patches/nemu/manifest.json"),
                     team_patch_recipe_sha256=sha(driver), runtime_qualified=False)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = prepare.now()
        prepare.save(out / "state.json", state)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "output", "nemu-source", "nemu-cache", "am-home", "environment-root"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--executor", required=True)
    main(p.parse_args())
