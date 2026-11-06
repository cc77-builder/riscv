#!/usr/bin/env python3
"""Compile the preserved build-01 C++ with its configured Clang toolchain."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time

BASE_SHA = "38d27240c83763a265dbc1b2d01b65639bc1b7984782bd289d6e6b7d7b0c7ebb"
RECIPE_SHA = "c7a92b27b3c7caf75828e99006322fdd271bc896fc9f0b83ad9033509219fa3f"
FAILED_LOG_SHA = "a700694214f771653c9f2402e9214bfa458ff0c73c1e2ac2c68e20cf4eed7f30"
FAILED_TIME_SHA = "58bae1b648884dd30211f8663d57580ed6fd1e4fbb9acf547ebabda546e72986"
GENERATED_MAKE_SHA = "60e83de481c10859af494d354652c48f3cca8e661a3afd1655da7d7e298703e5"
SUPPORT_MAKE_SHA = "e3053baaccc51c5050faeb4ef437b5fe67e94d5578b8fa087b92b457b449a99f"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def probe_native_tools(recipe_path, firtool_dir, generated_make):
    """Bind the effective installed root, including a relocated Verilator kit."""
    recipe = load_module(Path(recipe_path), "dot16_native_recipe_probe")
    tools = recipe.probe_tools("split-clang-v2", firtool_dir)
    config = subprocess.check_output([tools["verilator"]["path"], "-V"], text=True)
    sections = re.split(r"(?m)^Environment:[ \t]*$", config, maxsplit=1)
    require(len(sections) == 2, "Verilator configuration has no environment section")
    pattern = r"(?m)^[ \t]*VERILATOR_ROOT[ \t]*=[ \t]*(\S+)[ \t]*$"
    defaults = re.findall(pattern, sections[0])
    effective = re.findall(pattern, sections[1])
    require(len(defaults) == 1 and len(effective) <= 1, "ambiguous Verilator root binding")
    root = Path(effective[0] if effective else defaults[0]).resolve()
    make_roots = re.findall(pattern, Path(generated_make).read_text())
    require(len(make_roots) == 1 and root == Path(make_roots[0]).resolve(),
            "effective installed Verilator root differs from frozen generated Makefile")
    return dict(compilers=tools, verilator_support=recipe.verilator_support(root),
                compiler_runtime=recipe.compiler_runtime(tools), verilator_config=config,
                verilator_root_binding=dict(compiled_default=defaults[0],
                    environment=effective[0] if effective else None, effective=str(root),
                    generated_make=make_roots[0]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--parent-build", type=Path, required=True)
    p.add_argument("--generation-freeze", type=Path, required=True)
    p.add_argument("--generation-freeze-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--expected-head", required=True)
    p.add_argument("--cpus", default="1,2,3")
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--budget-seconds", type=int, default=1800)
    a = p.parse_args()
    sys.dont_write_bytecode = True
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"
    repo, parent, out = a.repo.resolve(), a.parent_build.resolve(), a.output.resolve()
    here = Path(__file__).resolve().parent
    base_path = here / "build.py"
    import hashlib
    require(hashlib.sha256(base_path.read_bytes()).hexdigest() == BASE_SHA, "original builder changed")
    base = load_module(base_path, "dot16_native_original_build")
    sha = base.sha
    helper = here.parent / "run_fu.py"
    require(sha(helper) == base.HELPER_SHA, "process helper changed")
    util = load_module(helper, "dot16_native_process_helper")
    cpus = {int(x) for x in a.cpus.split(",")}
    require(cpus and cpus <= {0, 1, 2, 3} and a.jobs == len(cpus), "one make slot per assigned CPU, at most four")
    require(60 <= a.budget_seconds <= 3600, "native wall budget must be 60..3600 seconds")
    require(a.output.is_absolute() and not out.exists() and not out.is_relative_to(repo)
            and not repo.is_relative_to(out) and not out.is_relative_to(parent)
            and not parent.is_relative_to(out), "new independent output outside source and parent required")
    os.sched_setaffinity(0, cpus)
    out.mkdir(parents=True)
    state = dict(schema=1, contract="dot16-production-native-continuation-v2", status="CAPTURING",
                 workflow="reuse-build-01-generation-then-clang-native", started=util.stamp(),
                 repo=str(repo), parent_build=str(parent), output=str(out), cpus=sorted(cpus), jobs=a.jobs,
                 budget_seconds=a.budget_seconds, fullcore_difftest_qualified=False,
                 performance_measured=False, asic_ppa_qualified=False)
    deadline, records, proc = time.monotonic() + a.budget_seconds, [], None

    def save():
        util.save(out / "status.json", state)

    def inventory(root):
        return {str(path.relative_to(root)): dict(bytes=path.stat().st_size, sha256=sha(path))
                for path in sorted(root.rglob("*")) if path.is_file()}

    def unchanged(root, expected):
        return all((root / name).is_file() and (root / name).stat().st_size == row["bytes"]
                   and sha(root / name) == row["sha256"] for name, row in expected.items())

    def step(name, argv, cwd, env):
        nonlocal proc
        require(time.monotonic() < deadline, "native wall budget exhausted")
        row = dict(name=name, command=argv, cwd=str(cwd), started=util.stamp())
        state.update(status="BUILDING", active_step=name)
        save()
        print(json.dumps(dict(event="NATIVE_STEP_START", **row)), flush=True)
        try:
            with (out / (name + ".log")).open("wb") as log:
                proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                state["active_process_group"] = proc.pid
                save()
                with (out / (name + "-memory.jsonl")).open("w") as memory:
                    while True:
                        sample = base.memory_sample(proc.pid)
                        sample["utc"] = util.stamp()
                        memory.write(json.dumps(sample) + "\n")
                        memory.flush()
                        mem = {x.split(":", 1)[0]: x.split(":", 1)[1].strip()
                               for x in sample["meminfo"].splitlines()}
                        print(json.dumps(dict(event="NATIVE_STEP_SAMPLE", name=name, utc=sample["utc"],
                            process_group=proc.pid, process_count=len(sample["processes"]),
                            observed_group_rss_kb=sum(int(x.get("VmRSS", "0 kB").split()[0]) for x in sample["processes"]),
                            available=mem["MemAvailable"], swap_free=mem["SwapFree"],
                            pressure=sample["memory_pressure"])), flush=True)
                        left = deadline - time.monotonic()
                        if left <= 0:
                            row["timed_out"] = True
                            row["cleanup_complete"] = util.stop_group(proc)
                            raise RuntimeError("native wall budget exhausted in " + name)
                        try:
                            row["exit_code"] = proc.wait(timeout=min(30, left))
                            break
                        except subprocess.TimeoutExpired:
                            pass
            require(not util.group_exists(proc.pid), "native command left a live process group")
            row["process_group_absent"] = True
            require(row["exit_code"] == 0, name + " failed; preserve this new attempt")
        finally:
            row["finished"] = util.stamp()
            records.append(row)
            util.save(out / "commands.json", records)
            print(json.dumps(dict(event="NATIVE_STEP_FINISH", **row)), flush=True)

    try:
        old = json.loads((parent / "status.json").read_text())
        parent_commands = json.loads((parent / "commands.json").read_text())
        inputs = json.loads((parent / "inputs-before.json").read_text())
        old_tools = json.loads((parent / "tools.json").read_text())
        require(old["status"] == "FAILED" and old["error"] == "ValueError('emu-build failed; preserve output')"
                and old["repo"] == str(repo) and old["source_head"] == a.expected_head,
                "parent is not the reviewed failed build")
        require([(x["name"], x.get("exit_code"), x.get("process_group_absent")) for x in parent_commands]
                == [("tool-probe", 0, True), ("scala-compile", 0, True), ("emu-build", 2, True)],
                "parent phase results differ")
        require(not util.group_exists(old["active_process_group"]), "parent process group is still present")
        require(sha(parent / "emu-build.log") == FAILED_LOG_SHA and sha(repo / "build/time.log") == FAILED_TIME_SHA,
                "original failed stage evidence differs")
        generated_make = repo / "build/emu-compile/VSimTop.mk"
        require(sha(generated_make) == GENERATED_MAKE_SHA, "generated C++ Makefile changed")
        require(not (repo / "build/emu").exists(), "preserve any existing EMU")
        residues = [str(x.relative_to(repo)) for x in (repo / "build/emu-compile").rglob("*")
                    if x.is_file() and x.suffix in (".o", ".a", ".gch", ".pch")]
        require(not residues, "unreviewed native outputs present: " + repr(residues))
        require(subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == a.expected_head,
                "source HEAD differs")
        require(old["flags"] == base.FLAGS, "generation feature configuration differs")
        sys.path.insert(0, str(repo / "team/optimizations/o1"))
        sys.path.insert(0, str(repo / "team/optimizations/o2/fullcore"))
        import build_inputs
        import live_inputs
        import build_recipe
        require(sha(build_recipe.__file__) == RECIPE_SHA, "shared native tool probe changed")

        def source_gate():
            deps, depfiles = live_inputs.dependency_snapshot(repo)
            require(build_inputs.hardware_files(repo) == inputs["hardware_files"]
                    and deps == inputs["dependencies"] and depfiles == inputs["dependency_files"],
                    "hardware/dependencies differ from the generation input")
            require(all(sha(path) == digest for path, digest in inputs["driver_files"].items()),
                    "parent generation driver changed")
            require(all(sha(repo / path) == digest for path, digest in inputs["candidate_files"].items()),
                    "production candidate changed")

        source_gate()
        freeze_path = a.generation_freeze.resolve()
        require(a.generation_freeze.is_absolute() and re.fullmatch(r"[0-9a-f]{64}", a.generation_freeze_sha256)
                and sha(freeze_path) == a.generation_freeze_sha256, "reviewed generation freeze differs")
        freeze = json.loads(freeze_path.read_text())
        require(freeze["schema"] == 1 and freeze["source_root"] == str(repo)
                and freeze["source_head"] == a.expected_head and freeze["generation_root"] == str(repo / "build")
                and freeze["parent_build"] == str(parent), "generation freeze belongs to different inputs")
        parent_files, generated_before = freeze["parent_files"], freeze["generated_files"]
        require(inventory(parent) == parent_files and inventory(repo / "build") == generated_before,
                "parent record or generated inputs changed after the reviewed freeze")
        util.save(out / "parent-files.json", parent_files)
        util.save(out / "generated-before.json", generated_before)
        drivers = [Path(__file__), here / "RESUME_NATIVE_CONTRACT.md", base_path, helper, Path(build_recipe.__file__), freeze_path]
        driver_hashes = {str(x): sha(x) for x in drivers}
        snap = out / "source-snapshot"
        snap.mkdir()
        for src in drivers:
            shutil.copyfile(src, snap / src.name)
            require(sha(snap / src.name) == driver_hashes[str(src)], "native driver snapshot differs")
        util.save(out / "inputs-before.json", dict(parent_files_sha256=sha(out / "parent-files.json"),
                  generated_before_sha256=sha(out / "generated-before.json"), driver_files=driver_hashes,
                  parent_status_sha256=sha(parent / "status.json"), generation_inputs_sha256=sha(parent / "inputs-before.json")))
        env = {k: os.environ[k] for k in ("HOME", "PATH", "TEAM_XS_ENV_ROOT", "COURSIER_REPOSITORIES") if k in os.environ}
        env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", TZ="UTC", PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0")
        env["JAVA_HOME"] = str(Path(old_tools["java"]["path"]).parent.parent)
        env["PATH"] = os.pathsep.join([str(Path(old_tools[k]["path"]).parent) for k in ("java", "mill", "verilator")]
                                         + [env.get("PATH", "/usr/bin:/bin")])
        probe_args = (str(Path(build_recipe.__file__)), str(Path(old_tools["firtool"]["path"]).parent), str(generated_make))
        probe = ("import runpy,json; m=runpy.run_path(" + repr(str(Path(__file__).resolve()))
                 + "); print(json.dumps(m['probe_native_tools'](*" + repr(probe_args) + ")))" )
        shell = "set -euo pipefail\nsource team/scripts/activate.sh\npython3 -B -c " + shlex.quote(probe)
        step("tool-probe", [old_tools["bash"]["path"], "-c", shell], repo, env)
        linked = json.loads((out / "tool-probe.log").read_text())
        tools, support, runtime = linked["compilers"], linked["verilator_support"], linked["compiler_runtime"]
        for role in ("java", "mill", "verilator", "verilator_bin", "firtool", "bash", "sh", "time"):
            require(tools[role]["path"] == old_tools[role]["path"] and tools[role]["sha256"] == old_tools[role]["sha256"],
                    "generation tool identity changed: " + role)
        m = re.search(r"(?m)^VERILATOR_ROOT\s*=\s*(\S+)\s*$", generated_make.read_text())
        require(m is not None and Path(m[1]).resolve() == Path(support["root"]).resolve(), "Verilator runtime root differs")
        require(support["files"].get("include/verilated.mk") == SUPPORT_MAKE_SHA, "configured native Make rules changed")
        util.save(out / "tools.json", tools)
        util.save(out / "verilator-support.json", support)
        util.save(out / "compiler-runtime.json", runtime)
        (out / "verilator-config.txt").write_text(linked["verilator_config"])
        util.save(out / "verilator-root-binding.json", linked["verilator_root_binding"])
        util.save(out / "environment.json", env)
        command = [tools["make"]["path"], "-C", str(generated_make.parent), "-f", generated_make.name,
                   "VM_PARALLEL_BUILDS=1", "OPT_FAST=-O3", "OPT_SLOW=-O0", "PGO_CFLAGS=", "PGO_LDFLAGS=",
                   "CXX=" + tools["cxx"]["path"], "CC=" + tools["cc"]["path"],
                   "LINK=" + shlex.join([tools["cxx"]["path"], "--ld-path=" + tools["ld"]["path"]]),
                   "AR=" + tools["ar"]["path"], "SHELL=" + tools["bash"]["path"],
                   "PYTHON3=" + tools["python"]["path"], "PERL=" + tools["perl"]["path"], "-j" + str(a.jobs)]
        state.update(source_head=a.expected_head, flags=base.FLAGS, command=command,
                     generated_input_count=len(generated_before), generated_input_bytes=sum(x["bytes"] for x in generated_before.values()),
                     generation_freeze=str(freeze_path), generation_freeze_sha256=a.generation_freeze_sha256,
                     original_build_remains_failed=True, native_output_residues=residues)
        save()
        util.save(out / "native-command.json", command)
        step("native-compile", [tools["time"]["path"], "-v", "-o", str(out / "native.time.log"), *command], repo, env)
        source_gate()
        require(unchanged(parent, parent_files) and inventory(parent) == parent_files, "original failed record changed")
        require(unchanged(repo / "build", generated_before), "original generated inputs or time log changed")
        require(all(sha(x) == digest for x, digest in driver_hashes.items()), "native driver changed")
        for tool in tools.values():
            require(sha(tool["path"]) == tool["sha256"], "native tool payload changed")
            if "payload_path" in tool:
                require(str(Path(tool["path"]).resolve()) == tool["payload_path"], "compiler driver target changed")
        require(build_recipe.verilator_support(support["root"]) == support, "installed runtime/Make support changed")
        require(build_recipe.compiler_runtime(tools) == runtime, "compiler implementation libraries changed")
        require(subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == a.expected_head,
                "source HEAD changed during native compilation")
        binary = repo / "build/emu"
        require(binary.is_file(), "native compilation produced no EMU")
        generated = [dict(path=str(x.relative_to(repo)), bytes=x.stat().st_size, sha256=sha(x))
                     for x in sorted((repo / "build").rglob("*")) if x.is_file()
                     and (x.suffix in (".sv", ".v", ".h", ".conf") or x == binary) and "emu-compile" not in x.parts]
        util.save(out / "generated-artifacts.json", generated)
        native_inputs = dict(inputs, source_head=a.expected_head, flags=base.FLAGS,
                             emu=dict(path=str(binary), bytes=binary.stat().st_size, sha256=sha(binary)),
                             generated_manifest_sha256=sha(out / "generated-artifacts.json"),
                             parent_build=str(parent), parent_status_sha256=sha(parent / "status.json"),
                             native_driver_files=driver_hashes, native_workflow=state["workflow"],
                             generation_freeze_sha256=a.generation_freeze_sha256,
                             generated_before_sha256=sha(out / "generated-before.json"))
        util.save(out / "build-inputs.json", native_inputs)
        require(time.monotonic() <= deadline, "native wall budget exceeded during final identity capture")
        state.update(status="DOT16_FULLCORE_BUILD_PASS", finished=util.stamp(), emu=native_inputs["emu"],
                     original_inputs_unchanged=True, parent_records_unchanged=True,
                     hardware_files=len(inputs["hardware_files"]), dependencies=len(inputs["dependencies"]))
        save()
        print(json.dumps(state), flush=True)
        return 0
    except BaseException as error:
        if proc is not None and util.group_exists(proc.pid):
            state["cleanup_complete"] = util.stop_group(proc)
        state.update(status="FAILED", fullcore_difftest_qualified=False, error=repr(error), finished=util.stamp())
        save()
        print(json.dumps(state), flush=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
