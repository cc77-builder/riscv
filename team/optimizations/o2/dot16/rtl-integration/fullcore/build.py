#!/usr/bin/env python3
"""Build one new dot16 MinimalConfig EMU through the unchanged official Makefile."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

HELPER_SHA = "db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3"
PATCH_SHA = "5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416"
FLAGS = dict(VDOT_DOT16="1", VDOT_O2_ELASTIC="1", VDOT_T14_FUSED_INPUT="1",
             VDOT_O1_HANDOFF="0", VDOT_O1_TRACE="0", VDOT_O2_TRACE="0",
             VDOT_T12_TRACE="0", VDOT_T13_TRACE="0")
CACHE = Path("out/dot16-fu-20261106-pro2")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def memory_sample(group):
    rows = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            stat = (path / "stat").read_text().rsplit(") ", 1)[1].split()
            if int(stat[2]) != group:
                continue
            fields = {}
            for line in (path / "status").read_text().splitlines():
                key, value = line.split(":", 1)
                if key in ("Name", "Pid", "PPid", "VmRSS", "VmSize", "VmSwap", "Threads", "Cpus_allowed_list"):
                    fields[key] = value.strip()
            rows.append(fields)
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    return dict(process_group=group, processes=rows, meminfo=Path("/proc/meminfo").read_text(),
                memory_pressure=Path("/proc/pressure/memory").read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--cpus", default="1,2,3")
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--budget-seconds", type=int, default=3600)
    parser.add_argument("--firtool-dir", type=Path, required=True)
    parser.add_argument("--java-home", type=Path, required=True)
    parser.add_argument("--mill", type=Path, required=True)
    parser.add_argument("--verilator", type=Path, required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"
    repo, out = args.repo.resolve(), args.output.resolve()
    here = Path(__file__).resolve().parent
    integration = here.parent
    cpus = {int(x) for x in args.cpus.split(",")}
    require(cpus and cpus <= {0, 1, 2, 3} and args.jobs == len(cpus), "one make slot per assigned CPU, maximum four")
    require(60 <= args.budget_seconds <= 5400, "build wall budget must be 60..5400 seconds")
    require(args.output.is_absolute() and not out.exists() and not out.is_relative_to(repo)
            and not repo.is_relative_to(out), "new absolute output outside checkout required")
    require(not (repo / "build").exists(), "preserve existing ROOT/build; no automatic cleanup or resume")
    require((repo / CACHE).is_dir(), "reviewed Scala cache is absent")
    require((args.java_home / "bin/java").is_file() and args.mill.is_file() and args.verilator.is_file(),
            "explicit Java/Mill/Verilator bootstrap path is absent")
    require(subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", "--", str(CACHE)]).returncode == 0,
            "reviewed Scala cache is not Git ignored")
    helper = integration / "run_fu.py"
    require(sha(helper) == HELPER_SHA, "process helper changed")
    util = module(helper, "dot16_fullcore_process_helper")
    os.sched_setaffinity(0, cpus)
    out.mkdir(parents=True)
    state = dict(schema=1, contract="dot16-production-fullcore-smoke-v1", status="CAPTURING",
                 started=util.stamp(), repo=str(repo), output=str(out), cpus=sorted(cpus),
                 jobs=args.jobs, mill_jobs=1, mill_compile_heap="3G", mill_make_heap="1G",
                 elaboration_heap="8G", budget_seconds=args.budget_seconds,
                 flags=FLAGS, scala_cache=str(repo / CACHE), build_initially_absent=True,
                 fullcore_difftest_qualified=False, performance_measured=False, asic_ppa_qualified=False)
    records, proc = [], None
    deadline = time.monotonic() + args.budget_seconds

    def save_state():
        util.save(out / "status.json", state)

    def command(name, argv, env):
        nonlocal proc
        require(time.monotonic() < deadline, "build wall budget exhausted")
        entry = dict(name=name, command=argv, cwd=str(repo), started=util.stamp(),
                     environment={k: env[k] for k in sorted(env) if k not in ("HOME", "PATH")})
        state.update(status="BUILDING", active_step=name)
        save_state()
        try:
            with (out / (name + ".log")).open("wb") as log:
                proc = subprocess.Popen(argv, cwd=repo, env=env, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                state["active_process_group"] = proc.pid
                save_state()
                with (out / (name + "-memory.jsonl")).open("w", encoding="utf-8") as samples:
                    while True:
                        sample = memory_sample(proc.pid)
                        sample["utc"] = util.stamp()
                        samples.write(json.dumps(sample) + "\n")
                        samples.flush()
                        left = deadline - time.monotonic()
                        if left <= 0:
                            entry["timed_out"] = True
                            entry["cleanup_complete"] = util.stop_group(proc)
                            raise RuntimeError("wall budget exhausted in " + name)
                        try:
                            entry["exit_code"] = proc.wait(timeout=min(30, left))
                            break
                        except subprocess.TimeoutExpired:
                            continue
            require(not util.group_exists(proc.pid), "command left a live process group")
            entry["process_group_absent"] = True
            require(entry["exit_code"] == 0, name + " failed; preserve output")
        finally:
            entry["finished"] = util.stamp()
            records.append(entry)
            util.save(out / "commands.json", records)

    try:
        state["source_head"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        require(state["source_head"] == args.expected_head, "HEAD changed before capture")
        pins = json.loads((integration / "source-manifest.json").read_text())
        require(sha(integration / "candidate.patch") == PATCH_SHA == pins["patch_sha256"], "candidate patch changed")
        candidate = pins["apply_result"] | pins["unchanged_dependency_sha256"]
        require(all(sha(repo / n) == h for n, h in candidate.items()), "production candidate bytes differ")
        sys.path.insert(0, str(repo / "team/optimizations/o1"))
        sys.path.insert(0, str(repo / "team/optimizations/o2/fullcore"))
        import build_inputs
        import live_inputs
        import build_recipe
        inputs = build_inputs.hardware_files(repo)
        dependencies, dependency_files = live_inputs.dependency_snapshot(repo)
        drivers = [Path(__file__), here / "CONTRACT.md", helper, integration / "source-manifest.json",
                   integration / "candidate.patch", Path(build_inputs.__file__), Path(live_inputs.__file__),
                   Path(build_recipe.__file__)]
        driver_hashes = {str(p): sha(p) for p in drivers}
        before = dict(hardware_files=inputs, dependency_files=dependency_files, dependencies=dependencies,
                      driver_files=driver_hashes, candidate_files=candidate)
        util.save(out / "inputs-before.json", before)
        (out / "working-tree.patch").write_bytes(subprocess.check_output(["git", "-C", str(repo), "diff", "--binary", "HEAD"]))
        (out / "source-status.txt").write_bytes(subprocess.check_output(["git", "-C", str(repo), "status", "--short"]))
        snap = out / "source-snapshot"
        snap.mkdir()
        for path in [repo / n for n in candidate] + drivers:
            rel = path.relative_to(repo)
            dest = snap / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            require(sha(path) == sha(dest), "source snapshot changed")
        base_env = {k: os.environ[k] for k in ("HOME", "PATH", "JAVA_HOME", "TEAM_XS_ENV_ROOT", "COURSIER_REPOSITORIES") if k in os.environ}
        base_env["JAVA_HOME"] = str(args.java_home.resolve())
        base_env["PATH"] = os.pathsep.join([str(args.java_home.resolve() / "bin"),
            str(args.mill.absolute().parent), str(args.verilator.absolute().parent), base_env.get("PATH", "/usr/bin:/bin")])
        base_env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", TZ="UTC", PYTHONDONTWRITEBYTECODE="1",
                        GIT_OPTIONAL_LOCKS="0", JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=" + str(len(cpus)))
        probe = "import json,runpy,pathlib,shutil,subprocess,hashlib; m=runpy.run_path(" + repr(str(Path(build_recipe.__file__))) + "); r=m['probe_tools']('direct'," + repr(str(args.firtool_dir.resolve())) + "); p=pathlib.Path(shutil.which('make')).resolve(); r['make']=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),version=subprocess.check_output([str(p),'--version'],text=True)); print(json.dumps(r))"
        activated = "set -euo pipefail\nsource team/scripts/activate.sh\n"
        command("tool-probe", ["bash", "-c", activated + "python3 -B -c " + shlex.quote(probe)], base_env)
        tools = json.loads((out / "tool-probe.log").read_text())
        require(Path(tools["java"]["path"]).resolve() == (args.java_home / "bin/java").resolve()
                and Path(tools["mill"]["path"]).resolve() == args.mill.resolve()
                and Path(tools["verilator"]["path"]).resolve() == args.verilator.resolve(),
                "activation did not retain the explicit bootstrap tool selection")
        # Reuse the mature tool probe, not its fixed legacy build contract.
        util.save(out / "tools.json", tools)
        tool_hashes = {v["path"]: v["sha256"] for v in tools.values()}
        bins = out / "tools"
        bins.mkdir()
        mill = bins / "mill"
        mill.write_text("#!/bin/sh\nif [ \"${1-}\" = -i ]; then shift; fi\nexec " + shlex.join(
            [tools["bash"]["path"], tools["mill"]["path"], "--no-server", "-j", "1"]) + ' "$@"\n')
        mill.chmod(0o755)
        compile_opts, make_opts = out / "mill-compile.opts", out / "mill-make.opts"
        for f, heap in ((compile_opts, "3G"), (make_opts, "1G")):
            f.write_text("-Xmx" + heap + "\n-Xss8m\n-XX:ActiveProcessorCount=" + str(len(cpus)) + "\n")
        shared = dict(base_env, **FLAGS, MILL_OUTPUT_DIR=str(repo / CACHE),
                      CHISEL_FIRTOOL_PATH=str(args.firtool_dir.resolve()))
        compile_env = dict(shared, MILL_JVM_OPTS_PATH=str(compile_opts), JAVA_OPTS="-Xmx3G -Xss8m")
        make_env = dict(shared, MILL_JVM_OPTS_PATH=str(make_opts), JAVA_OPTS="-Xmx1G -Xss8m")
        compile_command = [tools["bash"]["path"], tools["mill"]["path"], "--no-server", "-j", "1",
                           "-Djvm-xmx=8G", "-Djvm-xss=16m", "xiangshan.test.compile"]
        compile_shell = activated + shlex.join(compile_command) + "\n"
        make_args = [tools["make"]["path"], "emu", "CONFIG=MinimalConfig", "NUM_CORES=1", "EMU_THREADS=1",
                     "JVM_XMX=8G", "JVM_XSS=16m", "OPT_FAST=-O3", "OPT_SLOW=-O0", "EMU_TRACE=0",
                     "WITH_CHISELDB=0", "WITH_CONSTANTIN=0", "WITH_ROLLINGDB=0", "NO_DIFF=0",
                     "SHELL=" + tools["bash"]["path"], "CXX=" + tools["cxx"]["path"], "CC=" + tools["cc"]["path"],
                     "TIME_CMD=" + shlex.join([tools["time"]["path"], "-avp", "-o", "$(TIMELOG)"]), "-j" + str(args.jobs)]
        make_shell = activated + "export PATH=" + shlex.quote(str(bins)) + ':"$PATH"\n' + shlex.join(make_args) + "\n"
        for name, shell in (("compile-command.sh", compile_shell), ("build-command.sh", make_shell)):
            (out / name).write_text(shell)
        util.save(out / "environment.json", {"compile": compile_env, "make": make_env})
        state["commands"] = dict(compile=compile_command, make=make_args)
        save_state()
        command("scala-compile", [tools["bash"]["path"], str(out / "compile-command.sh")], compile_env)
        command("emu-build", [tools["bash"]["path"], str(out / "build-command.sh")], make_env)
        after_dependencies, after_dependency_files = live_inputs.dependency_snapshot(repo)
        require(build_inputs.hardware_files(repo) == inputs and after_dependencies == dependencies
                and after_dependency_files == dependency_files, "hardware or dependencies changed during build")
        require(all(sha(p) == h for p, h in driver_hashes.items()), "driver input changed during build")
        require(all(sha(p) == h for p, h in tool_hashes.items()), "compiler tool payload changed during build")
        binary = repo / "build/emu"
        require(binary.is_file(), "make succeeded without EMU")
        generated = [dict(path=str(p.relative_to(repo)), bytes=p.stat().st_size, sha256=sha(p))
                     for p in sorted((repo / "build").rglob("*")) if p.is_file()
                     and (p.suffix in (".sv", ".v", ".h", ".conf") or p == binary)
                     and "emu-compile" not in p.parts]
        util.save(out / "generated-artifacts.json", generated)
        shutil.copyfile(repo / "build/time.log", out / "time.log")
        before.update(emu=dict(path=str(binary), bytes=binary.stat().st_size, sha256=sha(binary)),
                      source_head=state["source_head"], flags=FLAGS, generated_manifest_sha256=sha(out / "generated-artifacts.json"))
        util.save(out / "build-inputs.json", before)
        require(time.monotonic() <= deadline, "build wall budget exceeded during final identity capture")
        state.update(status="DOT16_FULLCORE_BUILD_PASS", finished=util.stamp(), emu=before["emu"],
                     hardware_files=len(inputs), dependencies=len(dependencies), dependency_files=len(dependency_files))
        save_state()
        print(json.dumps(state), flush=True)
        return 0
    except BaseException as exc:
        if proc is not None and util.group_exists(proc.pid):
            state["cleanup_complete"] = util.stop_group(proc)
        state.update(status="FAILED", error=repr(exc), finished=util.stamp())
        save_state()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
