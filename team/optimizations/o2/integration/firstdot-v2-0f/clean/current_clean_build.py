"""Build a fresh EMU from a pure-software descendant with exact current-0f hardware."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import current_clean_common as c

def environment(args):
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
    c.require(1 <= args.jobs <= 4, "CPU budget must be 1..4")
    c.require(re.fullmatch(r"[0-9a-f]{40}", args.source_commit), "full expected source revision required")
    c.require(c.git(repo, "rev-parse", "HEAD").decode().strip() == args.source_commit,
              "source revision differs from explicit run selection")
    c.require(subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                             c.BASELINE_SOURCE, args.source_commit], capture_output=True).returncode == 0,
              "source is not selected 0f or its descendant")
    c.require(not out.exists() and not out.is_relative_to(repo), "preserve prior attempt and use outside output")
    c.require(not (repo / "build").exists() and not (repo / "out").exists(), "source has generated outputs")
    c.require(not c.git(repo, "diff", "HEAD", "--"), "clean reconstruction has tracked edits")
    expected = c.baseline(args.baseline_pins)
    files, dependencies, dependency_files = c.snapshot(repo, expected)
    cpus = sorted(os.sched_getaffinity(0))[:args.jobs]
    c.require(len(cpus) == args.jobs, "insufficient CPUs")
    os.sched_setaffinity(0, cpus)
    out.mkdir(parents=True)
    adapter_sources = c.adapter_sources(Path(__file__).parent)
    state = dict(contract=c.CONTRACT, status="CAPTURING", started_utc=c.now(), executor=args.executor,
                 source_root=str(repo), source_commit=args.source_commit, cpu_affinity=cpus,
                 build_executed=False, build_exit_code=None, emu_sha256=None)
    c.save(out / "build-state.json", state)
    try:
        for name in c.ADAPTER_NAMES:
            shutil.copyfile(Path(__file__).with_name(name), out / ("executed-" + name))
        shutil.copyfile(__file__, out / "executed-builder.py")
        shutil.copyfile(args.baseline_pins, out / "baseline-hardware-inputs.json")
        (out / "source-status.txt").write_bytes(c.git(repo, "status", "--short"))
        (out / "working-tree.patch").write_bytes(c.git(repo, "diff", "--binary", "HEAD"))
        c.save(out / "dependencies.json", dependencies)
        pins = dict(source_commit=args.source_commit, source_root=str(repo), contract=c.CONTRACT,
                    config="MinimalConfig", NUM_CORES=1, EMU_THREADS=1, JVM_XMX="8G", JVM_XSS="16m",
                    BUILD_JOBS=args.jobs, cpu_affinity=cpus, profile="observe", **c.FLAGS,
                    files=files, dependency_files=dependency_files,
                    build_script_sha256=c.sha(__file__), adapter_sources=adapter_sources,
                    baseline_pins_sha256=c.BASELINE_SHA, baseline_source_commit=c.BASELINE_SOURCE,
                    hardware_bytes_equal_baseline=True, generated_outputs_reused=False,
                    generated_inventory_scope=c.GENERATED_SCOPE)
        c.save(out / "hardware-inputs-before.json", pins)
        env = environment(args)
        activation = "set -euo pipefail\nsource team/scripts/activate.sh\n"
        commands = {"java": "java -version", "mill": "mill --version", "verilator": "verilator --version",
                    "clang": "clang++ --version", "make": "make --version", "python": "python3 --version",
                    "firtool": shlex.quote(str(args.firtool_dir.resolve() / "firtool")) + " --version"}
        for name, command in commands.items():
            with (out / (name + "-version.log")).open("wb") as log:
                rc = subprocess.run(["bash", "-c", activation + command], cwd=repo, env=env,
                                    stdout=log, stderr=subprocess.STDOUT).returncode
            c.require(rc == 0, "unavailable tool " + name)
        c.save(out / "effective-environment.json", {k: env[k] for k in
               ("JAVA_HOME", "VERILATOR_ROOT", "CHISEL_FIRTOOL_PATH", "TEAM_XS_ENV_ROOT",
                "JAVA_OPTS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")})
        shell = activation + "export " + " ".join(k + "=" + v for k, v in c.FLAGS.items()) + "\n"
        shell += ("make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=8G JVM_XSS=16m "
                  f"OPT_FAST=-O3 OPT_SLOW=-O0 -j{args.jobs}\n")
        (out / "build-command.sh").write_text(shell, encoding="utf-8")
        state.update(status="BUILDING", build_started_utc=c.now(), build_executed=True,
                     command=["bash", "-c", shell], profile="observe", flags=c.FLAGS)
        c.save(out / "build-state.json", state)
        print("CURRENT_CLEAN_BUILD_STARTED " + str(out), flush=True)
        with (out / "emu-build.log").open("wb") as log:
            rc = subprocess.run(state["command"], cwd=repo, env=env, stdout=log,
                                stderr=subprocess.STDOUT).returncode
        state.update(build_exit_code=rc, build_finished_utc=c.now())
        c.save(out / "build-state.json", state)
        c.require(rc == 0, "fresh EMU build failed; preserve this attempt")
        c.require(c.snapshot(repo, expected) == (files, dependencies, dependency_files), "source/dependencies changed")
        c.require(c.git(repo, "rev-parse", "HEAD").decode().strip() == args.source_commit
                  and not c.git(repo, "diff", "HEAD", "--"), "checkout changed during build")
        c.require(c.adapter_sources(Path(__file__).parent) == adapter_sources, "adapter changed during build")
        binary = repo / "build/emu"
        generated = c.generated_inventory(repo)
        c.validate_generated(generated)
        for name, digest in c.AUX.items():
            c.require(c.sha(repo / "build" / name) == digest, "AUX differs")
        pins.update(emu_sha256=c.sha(binary), emu_bytes=binary.stat().st_size, emu_path=str(binary))
        c.save(out / "generated-artifacts.json", generated)
        c.save(out / "hardware-inputs.json", pins)
        state.update(status="CURRENT_CLEAN_BUILD_PASS", finished_utc=c.now(), emu_sha256=pins["emu_sha256"],
                     source_files=len(files), dependency_files=len(dependency_files), dependencies=len(dependencies),
                     generated_files=len(generated), runtime_qualified=False)
        c.save(out / "build-state.json", state)
        print(state["status"], flush=True)
        return state
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc), finished_utc=c.now())
        c.save(out / "build-state.json", state)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "output", "baseline-pins", "java-home", "verilator-root", "firtool-dir", "environment-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--executor", required=True)
    main(parser.parse_args())
