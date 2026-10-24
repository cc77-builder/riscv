"""T17 clean O2/H1 build with a new identity, preserving historical B0/R4 locks."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

CONTRACT = "t17-clean-build-v1"
BASELINE_PINS_SHA = "2c580afa6095cda5e9d1680b7e91939b6f182b21c47357c77402c2d6b09d0a2c"
BASELINE_SOURCE = "6d2abe403b07c297b8830a7d4f06e370b0a8e070"
BUILDER_HELPER_SHA = "8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def helper(repo):
    path = repo / "team/optimizations/o2/fullcore/build_fullcore.py"
    require(sha(path) == BUILDER_HELPER_SHA, "historical snapshot helper changed")
    spec = importlib.util.spec_from_file_location("t17_snapshot_helper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.ROOT == repo, "snapshot helper is from another checkout")
    return module


def environment(args):
    # Tool caches and standard user home may be reused. Compiler/RTL switches
    # and arbitrary inherited make/JVM settings are deliberately not inherited.
    allowed = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG", "LC_ALL",
               "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "no_proxy"}
    env = {k: v for k, v in os.environ.items() if k in allowed}
    env.update(JAVA_HOME=str(args.java_home.resolve()),
               VERILATOR_ROOT=str(args.verilator_root.resolve()),
               CHISEL_FIRTOOL_PATH=str(args.firtool_dir.resolve()),
               TEAM_XS_ENV_ROOT=str(args.environment_root.resolve()),
               JAVA_OPTS=f"-Xmx8G -Xss16m -XX:ActiveProcessorCount={args.jobs}",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    return env


def main(args):
    repo, out = args.repo.resolve(), args.output.resolve()
    require(1 <= args.jobs <= 4, "CPU budget must be between one and four")
    require(not out.exists() and not out.is_relative_to(repo), "use a new output outside checkout")
    require(not (repo / "build").exists() and not (repo / "out").exists(), "checkout has generated build/cache outputs")
    require(sha(args.baseline_pins) == BASELINE_PINS_SHA, "wrong historical comparison inventory")
    baseline = json.loads(args.baseline_pins.read_text())
    require(baseline["source_commit"] == BASELINE_SOURCE, "wrong baseline source")
    b = helper(repo)
    require(not b.git("diff", "HEAD", "--", *b.HARDWARE), "hardware has uncommitted changes")
    require(not b.git("ls-files", "--others", "--exclude-standard", "--", *b.HARDWARE), "untracked hardware input")
    cpus = sorted(os.sched_getaffinity(0))[:args.jobs]
    require(len(cpus) == args.jobs, "insufficient allowed CPUs")
    os.sched_setaffinity(0, cpus)
    out.mkdir(parents=True)
    state = dict(contract=CONTRACT, status="CAPTURING", started_utc=now(), executor=args.executor,
                 source_root=str(repo), source_commit=b.git("rev-parse", "HEAD").decode().strip(),
                 build_exit_code=None, emu_sha256=None, build_executed=False, cpu_affinity=cpus)
    save(out / "build-state.json", state)
    try:
        shutil.copyfile(__file__, out / "executed-builder.py")
        shutil.copyfile(args.baseline_pins, out / "baseline-hardware-inputs.json")
        (out / "source-status.txt").write_bytes(b.git("status", "--short"))
        (out / "working-tree.patch").write_bytes(b.git("diff", "--binary", "HEAD"))
        files = {}
        for raw in b.git("ls-files", "-z", "--", *b.HARDWARE).split(b"\0"):
            if raw and (repo / raw.decode()).is_file():
                files[raw.decode()] = sha(repo / raw.decode())
        dependencies, dependency_files = b.dependency_snapshot()
        require(files == baseline["files"], "current hardware input set/bytes differ from qualified 6d2")
        require(dependency_files == baseline["dependency_files"], "recursive dependency set/bytes differ from qualified 6d2")
        save(out / "dependencies.json", dependencies)
        flags = b.profile_flags("observe")
        env = environment(args)
        pins = dict(source_commit=state["source_commit"], source_root=str(repo), contract=CONTRACT,
                    config="MinimalConfig", NUM_CORES=1, EMU_THREADS=1, JVM_XMX="8G", JVM_XSS="16m",
                    BUILD_JOBS=args.jobs, cpu_affinity=cpus, profile="observe", **flags,
                    files=dict(sorted(files.items())), dependency_files=dependency_files,
                    build_script_sha256=sha(__file__), baseline_pins_sha256=BASELINE_PINS_SHA,
                    hardware_bytes_equal_baseline=True, generated_outputs_reused=False)
        save(out / "hardware-inputs-before.json", pins)
        activation = "set -euo pipefail\nsource team/scripts/activate.sh\n"
        tools = {"java": "java -version", "mill": "mill --version", "verilator": "verilator --version",
                 "clang": "clang++ --version", "make": "make --version", "python": "python3 --version",
                 "firtool": shlex.quote(str(args.firtool_dir.resolve() / "firtool")) + " --version"}
        for name, command in tools.items():
            with (out / (name + "-version.log")).open("wb") as log:
                rc = subprocess.run(["bash", "-c", activation + command], cwd=repo, env=env,
                                    stdout=log, stderr=subprocess.STDOUT).returncode
            require(rc == 0, "tool unavailable: " + name)
        save(out / "effective-environment.json", {k: env[k] for k in
             ("JAVA_HOME", "VERILATOR_ROOT", "CHISEL_FIRTOOL_PATH", "TEAM_XS_ENV_ROOT", "JAVA_OPTS",
              "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")})
        shell = activation + "export " + " ".join(k + "=" + v for k, v in flags.items()) + "\n"
        shell += ("make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=8G JVM_XSS=16m "
                  f"OPT_FAST=-O3 OPT_SLOW=-O0 -j{args.jobs}\n")
        (out / "build-command.sh").write_text(shell, encoding="utf-8")
        state.update(status="BUILDING", build_started_utc=now(), build_executed=True,
                     command=["bash", "-c", shell], profile="observe", flags=flags)
        save(out / "build-state.json", state)
        print("T17_CLEAN_BUILD_STARTED " + str(out), flush=True)
        with (out / "emu-build.log").open("wb") as log:
            rc = subprocess.run(state["command"], cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        state.update(build_exit_code=rc, build_finished_utc=now())
        save(out / "build-state.json", state)
        require(rc == 0, "clean EMU build failed; preserve this attempt")
        for group in (files, dependency_files):
            for path, digest in group.items():
                require(sha(repo / path) == digest, "input changed during build: " + path)
        modules_after, files_after = b.dependency_snapshot()
        require(modules_after == dependencies and files_after == dependency_files, "dependency inventory changed")
        binary = repo / "build/emu"
        require(binary.is_file(), "successful command produced no EMU")
        pins.update(emu_sha256=sha(binary), emu_bytes=binary.stat().st_size, emu_path=str(binary))
        generated = [p for p in sorted((repo / "build").rglob("*")) if p.is_file() and
                     (p.suffix in (".sv", ".v", ".h") or p == binary) and "emu-compile" not in p.parts]
        save(out / "generated-artifacts.json", [dict(path=p.relative_to(repo).as_posix(), bytes=p.stat().st_size,
                                                     sha256=sha(p)) for p in generated])
        save(out / "hardware-inputs.json", pins)
        state.update(status="T17_CLEAN_BUILD_PASS", finished_utc=now(), emu_sha256=pins["emu_sha256"],
                     source_files=len(files), dependency_files=len(dependency_files), dependencies=len(dependencies),
                     generated_files=len(generated), runtime_qualified=False)
        save(out / "build-state.json", state)
        print(json.dumps(state, indent=2), flush=True)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc), finished_utc=now())
        save(out / "build-state.json", state)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "output", "baseline-pins", "java-home", "verilator-root", "firtool-dir", "environment-root"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--executor", required=True)
    main(p.parse_args())
