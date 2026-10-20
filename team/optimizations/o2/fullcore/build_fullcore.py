"""Build a fresh O2 traced MinimalConfig EMU and bind immutable hardware inputs.

The root checkout build/ must not exist. No deletion, publishing, or fallback to
an old emulator. Test/parser development may proceed outside hardware inputs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "o1"))
from build_inputs import HARDWARE, hardware_files, verify_dependencies, verify_hardware_files
import build_recipe
sys.path.append(str(Path(__file__).resolve().parents[1] / "fullcore"))
import live_inputs

ROOT = Path(__file__).resolve().parents[4]
FLAGS = {"VDOT_O2_ELASTIC": "1", "VDOT_O1_HANDOFF": "0", "VDOT_O1_TRACE": "0", "VDOT_T14_FUSED_INPUT": "1",
         "VDOT_O2_TRACE": "1", "VDOT_T12_TRACE": "0", "VDOT_T13_TRACE": "1"}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def git(*args, repo=ROOT):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def require(ok, message):
    if not ok:
        raise ValueError(message)


def dependency_snapshot():
    return live_inputs.dependency_snapshot(ROOT)


def main(out):
    out = out.resolve()
    require(not out.exists(), "output already exists")
    require(not out.is_relative_to(ROOT), "output must be outside checkout")
    require(not (ROOT / "build").exists(), "existing build/ must be preserved separately first")
    require(not git("diff", "HEAD", "--", *HARDWARE), "commit hardware changes before building")
    require(not git("ls-files", "--others", "--exclude-standard", "--", *HARDWARE),
            "untracked hardware inputs must be committed before building")
    out.mkdir(parents=True)
    state = {"status": "CAPTURING", "started_utc": now(), "source_root": str(ROOT),
             "source_commit": git("rev-parse", "HEAD").decode().strip(), "flags": FLAGS}
    save(out / "build-state.json", state)
    try:
        (out / "source-status.txt").write_bytes(git("status", "--short"))
        (out / "working-tree.patch").write_bytes(git("diff", "--binary", "HEAD"))
        files = hardware_files(ROOT)
        contract = build_recipe.capture(ROOT)
        clean = build_recipe.environment()
        dependencies, dependency_files = dependency_snapshot()
        save(out / "dependencies.json", dependencies)
        pins = {"source_commit": state["source_commit"], "config": "MinimalConfig",
                "NUM_CORES": 1, "EMU_THREADS": 1, "JVM_XMX": "12G", "BUILD_JOBS": 2,
                **FLAGS, "native_build_contract": contract, "files": dict(sorted(files.items())), "dependency_files": dependency_files,
                "build_tools": {str(p.relative_to(ROOT)): sha(p) for p in
                    (Path(__file__), Path(live_inputs.__file__), Path(build_recipe.__file__))},
                "build_script_sha256": sha(Path(__file__)), "source_root": str(ROOT)}
        save(out / "hardware-inputs-before.json", pins)
        activated = "source team/scripts/activate.sh\n"
        tools = {"java": "java -version", "mill": "mill --version", "verilator": "verilator --version",
                 "clang": "clang++ --version", "make": "make --version", "python": "python3 --version",
                 "firtool": '\"$HOME/.cache/llvm-firtool/1.62.1/bin/firtool\" --version'}
        for name, command in tools.items():
            with (out / (name + "-version.log")).open("wb") as log:
                rc = subprocess.run(["bash", "-c", activated + command], cwd=ROOT,
                                    stdout=log, stderr=subprocess.STDOUT, env=clean).returncode
            require(rc == 0, "missing tool " + name)
        shell = activated + "export " + " ".join(k + "=" + v for k, v in FLAGS.items()) + "\n"
        shell += 'export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"\n'
        shell += build_recipe.make_command(contract)
        (out / "build-command.sh").write_text(shell, encoding="utf-8")
        state.update(status="BUILDING", build_started_utc=now(), command=["bash", "-c", shell])
        save(out / "build-state.json", state)
        print("O2_FULLCORE_BUILD_STARTED " + str(out), flush=True)
        with (out / "emu-build.log").open("wb") as log:
            rc = subprocess.run(state["command"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=clean).returncode
        state.update(build_exit_code=rc, build_finished_utc=now())
        save(out / "build-state.json", state)
        require(rc == 0, "EMU build failed; keep emu-build.log and build/ unchanged")
        for group in ("files", "dependency_files"):
            for path, digest in pins[group].items():
                require(sha(ROOT / path) == digest, "source changed during build: " + path)
        require(all(sha(ROOT / name) == digest for name, digest in pins["build_tools"].items()),
                "build tooling changed during compilation")
        verify_hardware_files(ROOT, pins["files"])
        build_recipe.verify(ROOT, contract)
        dep_after, dep_files_after = dependency_snapshot()
        require(dep_after == dependencies and dep_files_after == dependency_files, "dependencies changed")
        binary = ROOT / "build/emu"
        require(binary.is_file(), "successful build has no EMU")
        pins.update(emu_sha256=sha(binary), emu_bytes=binary.stat().st_size, emu_path=str(binary))
        generated = [p for p in sorted((ROOT / "build").rglob("*"))
                     if p.is_file() and (p.suffix in (".sv", ".v", ".h") or p == binary)
                     and "emu-compile" not in p.parts]
        save(out / "generated-artifacts.json", [{"path": p.relative_to(ROOT).as_posix(),
             "bytes": p.stat().st_size, "sha256": sha(p)} for p in generated])
        save(out / "hardware-inputs.json", pins)
        state.update(status="O2_FULLCORE_BUILD_PASS", finished_utc=now(), emu_sha256=pins["emu_sha256"],
                     source_files=len(files), dependency_files=len(dependency_files), dependencies=len(dependencies))
        save(out / "build-state.json", state)
        print(state["status"], flush=True)
        return 0
    except Exception as exc:
        state.update(status="FAILED", error=repr(exc), finished_utc=now())
        save(out / "build-state.json", state)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args().output))
