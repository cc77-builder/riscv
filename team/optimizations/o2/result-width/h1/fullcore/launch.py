#!/usr/bin/env python3
"""Run the authorized H1 full-core build and unchanged G3 regression once."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

REPO = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
WORK = Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021")
B0_BUILD = Path("/home/riscv/riscv-lab/o2-b0-build-before-h1-20261021")
OLD_H1 = Path("/home/riscv/riscv-lab/o2-h1-result32-20261021")
SOURCE_COMMIT = "8b5024fcbd96986871cc40ce8c9fb71a67c495eb"
B0_EMU = "ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57"
R0_LOCK = "8bc49ced46926b4015b900185bd657bee13bb606a27fc6482d4f169c1766c29e"

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
    pins = json.loads((OLD_H1 / "candidate-inputs.json").read_text())
    for rel, expected in pins["source_sha256"].items():
        need(sha(REPO / rel) == expected, "H1 source changed: " + rel)
    need(sha(REPO / "team/optimizations/o2/repro/baseline-lock.json") == R0_LOCK, "B0 lock changed")
    need(not subprocess.check_output(["git", "diff", "HEAD", "--", "src", "scripts", "build.sc", "Makefile", "Makefile.test", "team/scripts/activate.sh"], cwd=REPO), "dirty hardware")

def preserve_b0():
    original = REPO / "build"
    need(original.is_dir() and not original.is_symlink(), "old build must be real directory")
    need(not B0_BUILD.exists(), "B0 preservation directory already exists")
    need(original.resolve() == REPO / "build", "old build resolved path differs")
    need(B0_BUILD.parent.resolve() == REPO.parents[1], "B0 target outside expected lab")
    need(sha(original / "emu") == B0_EMU, "old build is not frozen B0")
    need(sha(Path("/home/riscv/riscv-lab/o2-r0-repro-20261021/baseline-binaries/o2-emu")) == B0_EMU, "cached B0 identity differs")
    original.rename(B0_BUILD)
    need(sha(B0_BUILD / "emu") == B0_EMU and not original.exists(), "B0 preserve verification failed")
    save(WORK / "b0-preservation.json", {"original": str(original), "preserved": str(B0_BUILD),
         "emu_sha256": B0_EMU, "operation": "same-filesystem directory rename; no deletion",
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
                preserve_b0()
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
                need(pins["emu_sha256"] != B0_EMU, "new build unexpectedly equals B0")
                need(pins["source_commit"] == SOURCE_COMMIT, "new build source identity differs")
            print("PASS", name, flush=True)
        state.update(status="passed", finished=stamp(), h1_fullcore_validation_pass=True,
                     source_and_r0_lock_unchanged=True)
        print("H1_FULLCORE_CAMPAIGN_PASS", flush=True)
    except BaseException as error:
        state.update(status="failed", error=repr(error), finished=stamp())
        print("H1_FULLCORE_CAMPAIGN_FAILED", repr(error), flush=True)
        raise
    finally:
        save(state_path, state)

if __name__ == "__main__":
    main()
