#!/usr/bin/env python3
"""Run the authorized R3 DIV-gate full-core build and unchanged G3 regression once."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

REPO = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
WORK = Path("/home/riscv/riscv-lab/o2-r3-div-gate-fullcore-20261024")
OLD_BUILD = Path("/home/riscv/riscv-lab/o2-h1-build-before-r3-div-gate-20261024")
SOURCE_COMMIT = "0f12df675378556670afd0dd2153f47fcb330610"
OLD_EMU = "e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def stamp():
    return datetime.now(timezone.utc).isoformat()

def save(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)

def need(value, message):
    if not value:
        raise ValueError(message)

def frozen():
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    need(actual == SOURCE_COMMIT, "source commit changed")
    pins = json.loads((WORK / "identity.json").read_text())
    for rel, expected in pins["files"].items():
        need(sha(REPO / rel) == expected, "candidate source changed: " + rel)
    need(not subprocess.check_output(["git", "diff", "HEAD", "--", "src", "scripts", "build.sc", "Makefile", "Makefile.test", "team/scripts/activate.sh"], cwd=REPO), "dirty hardware")

def preserve_old_build():
    original = REPO / "build"
    need(original.is_dir() and not original.is_symlink(), "old build must be real directory")
    need(not OLD_BUILD.exists(), "previous H1 preservation directory already exists")
    need(original.resolve() == REPO / "build", "old build resolved path differs")
    need(OLD_BUILD.parent.resolve() == REPO.parents[1], "previous H1 target outside expected lab")
    need(sha(original / "emu") == OLD_EMU, "old build is not frozen previous H1")
    original.rename(OLD_BUILD)
    need(sha(OLD_BUILD / "emu") == OLD_EMU and not original.exists(), "previous H1 preserve verification failed")
    save(WORK / "previous-build-preservation.json", {"original": str(original), "preserved": str(OLD_BUILD),
         "emu_sha256": OLD_EMU, "operation": "same-filesystem directory rename; no deletion",
         "time": stamp()})

def main():
    state_path = WORK / "campaign-state.json"
    need(not state_path.exists(), "campaign already has state; inspect instead of restarting")
    state = {"status": "running", "pid": os.getpid(), "started": stamp(), "source_commit": SOURCE_COMMIT,
             "launcher_sha256": sha(Path(__file__)), "steps": [], "performance_comparison": False}
    save(state_path, state)
    stages = [
        ("preflight", ["python3", "-B", "team/optimizations/o2/fullcore/run_suite.py", "--preflight-only", "--output", str(WORK / "preflight-01")]),
        ("host-fullcore", ["python3", "-B", "-m", "unittest", "discover", "-s", "team/optimizations/o2/fullcore", "-p", "test_*.py", "-v"]),
        ("host-workloads", ["python3", "-B", "-m", "unittest", "discover", "-s", "team/optimizations/o2/fullcore/workloads", "-p", "test_*.py", "-v"]),
        ("build", ["python3", "-B", "team/optimizations/o2/fullcore/build_fullcore.py", "--output", str(WORK / "build-01"), "--profile", "observe"]),
        ("core", ["python3", "-B", "team/optimizations/o2/fullcore/run_suite.py", "--output", str(WORK / "core-01"), "--hardware-pins", str(WORK / "build-01/hardware-inputs.json"), "--emu", str(REPO / "build/emu"), "--jobs", "2"]),
        ("supplements", ["python3", "-B", "team/optimizations/o2/fullcore/run_supplements.py", "--output", str(WORK / "supplements-01"), "--hardware-pins", str(WORK / "build-01/hardware-inputs.json"), "--emu", str(REPO / "build/emu"), "--jobs", "2"]),
        ("recheck", ["python3", "-B", "team/optimizations/o2/fullcore/recheck.py", "--campaign", str(WORK / "core-01"), "--supplements", str(WORK / "supplements-01"), "--output", str(WORK / "recheck-01")]),
    ]
    try:
        for name, command in stages:
            frozen()
            if name == "build":
                preserve_old_build()
            step = {"name": name, "command": command, "started": stamp(), "status": "running", "log": name + ".log"}
            state["steps"].append(step)
            save(state_path, state)
            print("START", name, flush=True)
            with (WORK / (name + ".log")).open("wb") as log:
                process = subprocess.Popen(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT,
                                           env=dict(os.environ, PYTHONUNBUFFERED="1"))
                step["pid"] = process.pid
                save(state_path, state)
                rc = process.wait()
            step.update(exit_code=rc, finished=stamp(), status="passed" if rc == 0 else "failed")
            save(state_path, state)
            need(rc == 0, name + " failed; retain all logs and repair only the affected stage")
            frozen()
            if name == "build":
                pins = json.loads((WORK / "build-01/hardware-inputs.json").read_text())
                need(pins["emu_sha256"] != OLD_EMU, "new build unexpectedly equals previous H1")
                need(pins["source_commit"] == SOURCE_COMMIT, "new build source identity differs")
            print("PASS", name, flush=True)
        state.update(status="passed", finished=stamp(), r3_div_gate_fullcore_validation_pass=True,
                     candidate_source_unchanged=True)
        print("R3_DIV_GATE_FULLCORE_CAMPAIGN_PASS", flush=True)
    except BaseException as error:
        state.update(status="failed", error=repr(error), finished=stamp())
        print("R3_DIV_GATE_FULLCORE_CAMPAIGN_FAILED", repr(error), flush=True)
        raise
    finally:
        save(state_path, state)

if __name__ == "__main__":
    main()
