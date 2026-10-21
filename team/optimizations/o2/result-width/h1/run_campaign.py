#!/usr/bin/env python3
"""Sequential H1 local validation; no full-core build, commit, or publication."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--o4-work", type=Path, required=True)
    args = parser.parse_args()
    work, o4 = args.work.resolve(), args.o4_work.resolve()
    if work.is_relative_to(ROOT) or (work / "campaign-state.json").exists():
        raise ValueError("work must be outside checkout and have no prior campaign")
    work.mkdir(parents=True, exist_ok=True)
    paths = subprocess.check_output([
        "git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
        "src", "build.sc", ".mill-version", "team/scripts/activate.sh",
        "team/models/vdot", "team/rtl/vdot", "team/optimizations/o2/fu",
        "team/optimizations/o2/parent", "team/optimizations/o2/run_rtl.py",
        "team/optimizations/o2/check_negative_fu.py", "team/optimizations/o2/test_negative_fu.py",
        "team/optimizations/o4/*.py", "team/optimizations/o4/*.scala",
        "team/optimizations/o4/toolchain-lock.json",
        "team/optimizations/o2/result-width/h1/run_campaign.py"], cwd=ROOT).split(b"\0")
    pins = {p.decode(): sha(ROOT / p.decode()) for p in paths if p and (ROOT / p.decode()).is_file()}
    r0 = ROOT / "team/optimizations/o2/repro/baseline-lock.json"
    identity = {"base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "source_sha256": pins, "r0_lock_sha256": sha(r0),
                "candidate": "O2 H1 result32 (base commit plus saved patch and file hashes)",
                "tools": {n: sha(o4 / "tools/root/usr/bin" / n) for n in ("yosys", "berkeley-abc", "sta")},
                "library_sha256": sha(o4 / "library/NangateOpenCellLibrary_typical.lib")}
    write(work / "candidate-inputs.json", identity)
    (work / "working-tree.patch").write_bytes(subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=ROOT))
    (work / "source-status.txt").write_bytes(subprocess.check_output(["git", "status", "--short"], cwd=ROOT))
    for rel in ["src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala",
                "src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala"]:
        target = work / "source" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / rel).read_bytes())
    commands = [
        ("model", ["bash", "team/scripts/check-vdot-model.sh"]),
        ("fu", ["python3", "-B", "team/optimizations/o2/run_rtl.py", "fu", str(work / "fu-01")]),
        ("parent", ["python3", "-B", "team/optimizations/o2/run_rtl.py", "parent", str(work / "parent-01")]),
        ("parent-host", ["python3", "-B", "-m", "unittest", "discover", "-s", "team/optimizations/o2/parent", "-v"]),
        ("parent-replay", ["python3", "-B", "team/optimizations/o2/parent/check_trace.py", "--log", str(work / "parent-01/result.log"), "--output", str(work / "parent-replay.json")]),
    ]
    for boundary in ("fu", "parent"):
        gen, mapping, sta = [work / (boundary + suffix) for suffix in ("-cost-01", "-map-01", "-sta-01")]
        commands.extend([
            (boundary + "-elaborate", ["python3", "-B", "team/optimizations/o4/elaborate.py", "o2", boundary, str(gen)]),
            (boundary + "-map", ["python3", "-B", "team/optimizations/o4/synthesize.py", str(gen), str(mapping), "--work", str(o4)]),
            (boundary + "-sta", ["python3", "-B", "team/optimizations/o4/timing.py", str(mapping), str(sta), "--work", str(o4)]),
        ])
    env = dict(os.environ, PYTHONUNBUFFERED="1", JAVA_OPTS="-Xmx12G -Xss16m", BUILD_JOBS="2")
    state = {"started": stamp(), "pid": os.getpid(), "status": "running", "steps": [], "fullcore_run": False}
    def unchanged():
        if pins != {name: sha(ROOT / name) for name in pins} or sha(r0) != identity["r0_lock_sha256"]:
            raise ValueError("candidate inputs or R0 lock changed during campaign")
    try:
        for name, cmd in commands:
            unchanged()
            step = {"name": name, "command": cmd, "start": stamp(), "status": "running", "log": name + ".log"}
            state["steps"].append(step)
            write(work / "campaign-state.json", state)
            print("START", name, flush=True)
            with (work / (name + ".log")).open("wb") as stream:
                process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
                step["pid"] = process.pid
                write(work / "campaign-state.json", state)
                rc = process.wait()
            step.update(exit_code=rc, end=stamp(), status="passed" if rc == 0 else "failed")
            write(work / "campaign-state.json", state)
            if rc:
                raise RuntimeError("failed step " + name + "; inspect retained log")
            unchanged()
            print("PASS", name, flush=True)
        state["status"] = "passed"
        state["source_and_r0_lock_unchanged"] = True
    except BaseException as error:
        state.update(status="failed", error=repr(error))
        raise
    finally:
        state["finished"] = stamp()
        write(work / "campaign-state.json", state)
    print("O2_H1_LOCAL_CAMPAIGN_PASS", flush=True)


if __name__ == "__main__":
    main()
