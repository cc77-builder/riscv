"""External postprocessing v2; preserve failed v1 and explicit resource-timeline limit."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

PLAN_SHA = "4dd6b31e1049ba4dff957c6917bb706ff39d070d5d1fb1bdfabe60a67bddc85f"
RECORDER_SHA = "8191e873267ecee72fcffff7211dac4a9c6c35499d2b826c2f9f62f3c8d3713e"
ORDER = ("fullcore_physical", "fullcore_pack", "fullcore_bytes", "fullcore_archive_audit",
         "finalize_c", "combination_audit", "full_comparison")
PASS = {"fullcore": "CURRENT_CLEAN_FULLCORE_PASS",
        "matrix": "CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS",
        "ordinary_c": "R4_C_APPLICATION_CALLS_PASS"}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def absent(path):
    require(not path.exists() and not path.is_symlink(), "preserve existing path: " + str(path))


def option(command, flag):
    require(command.count(flag) == 1, "missing/duplicate option: " + flag)
    return Path(command[command.index(flag) + 1]).resolve()


def load_plan(plan_path, state_dir):
    require(sha(plan_path) == PLAN_SHA, "fixed plan changed")
    plan = read(plan_path)
    repo = Path(plan["repo"]).resolve()
    root = repo.parents[1]
    recorder = plan_path.parent / "run_recorded.py"
    require(sha(recorder) == RECORDER_SHA, "recorder source changed")
    require(state_dir.parent == root and state_dir != root, "state directory must be a fresh clean-root child")
    stages = plan["stages"]
    files = {str(plan_path): PLAN_SHA, str(recorder): RECORDER_SHA,
             str(Path(__file__).resolve()): sha(__file__)}
    closure = plan["external_runtime_closure"]
    require(sha(closure["path"]) == closure["sha256"], "external closure changed")
    actual_closure = read(closure["path"])
    require(actual_closure["files"] == closure["files"] and len(closure["files"]) == 4,
            "exact external four-file runtime closure required")
    for path, expected in closure["files"].items():
        require(sha(path) == expected, "external auditor runtime source changed")
        files[path] = expected
    files[closure["path"]] = closure["sha256"]
    for path, expected in plan["preserved_failed_attempt"].items():
        require(sha(path) == expected, "preserved v1 failure/source changed")
        files[path] = expected
    external_entry = Path(closure["path"]).parent / "current_clean_archive_v2.py"
    require(str(external_entry) in closure["files"], "missing fixed external entry")
    jobs = []
    for name in ORDER:
        command = stages[name]
        require(isinstance(command, list) and command[:2] == ["python3", "-B"]
                and all(isinstance(arg, str) for arg in command), "invalid planned command")
        source = Path(command[2])
        require(source.is_absolute() and (source.is_relative_to(repo) or source == external_entry)
                and source.is_file() and not source.is_symlink(), "invalid planned source")
        files[str(source)] = sha(source)
        receipt = Path(plan["postprocess_receipts"][name])
        require(receipt == root / (name.replace("_", "-") + "-02.command.json"), "new v2 receipt required")
        outputs = ([Path(stages["ordinary_c"]["command"][-1]) / filename for filename in
                    ("combination-c-qualification.json", "combination-c-orchestration-proof.json")]
                   if name == "finalize_c" else [option(command, "--output")])
        if name == "fullcore_pack":
            outputs.append(option(command, "--archive"))
        require(all(path.is_relative_to(root) and not path.is_relative_to(repo)
                    and path != state_dir and not path.is_relative_to(state_dir) for path in outputs),
                "planned output overlaps protected source/state")
        jobs.append(dict(name=name, command=command, receipt=str(receipt),
                         outputs=[str(path) for path in outputs]))
    paths = [state_dir]
    for job in jobs:
        receipt = Path(job["receipt"])
        paths.extend([receipt, receipt.with_suffix(".stdout.log"), receipt.with_suffix(".stderr.log")])
        paths.extend(map(Path, job["outputs"]))
    require(len(paths) == len(set(paths)), "duplicate postprocessing output")
    for path in paths:
        absent(path)
    return plan, repo, recorder, jobs, files


def run(plan_path, state_dir, check_only=False):
    plan, repo, recorder, jobs, inputs = load_plan(plan_path, state_dir)
    if check_only:
        print(json.dumps(dict(status="READ_ONLY_PLAN_CHECK_PASS", plan_sha256=PLAN_SHA,
            stages=jobs, source_files=inputs, cpu=2, new_emu_runs=0), indent=2))
        return
    state_dir.mkdir()
    state = dict(contract="clean-postprocess-v2-wall-clock-limited", status="STARTING", started=now(), pid=os.getpid(), plan=str(plan_path),
        plan_sha256=PLAN_SHA, source_sha256=sha(__file__), source_files=inputs,
        cpu=2, commands_started=0, new_emu_runs=0, new_nemu_runs=0,
        acceptance="ROOT_REVIEW_REQUIRED", dependencies={}, stages=[], active=None)

    def save():
        temporary = state_dir / "state.tmp"
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(state_dir / "state.json")

    def fixed_inputs():
        for filename, digest in inputs.items():
            require(sha(filename) == digest, "postprocessing input changed: " + filename)

    def optional(path):
        try:
            return read(path)
        except (FileNotFoundError, json.JSONDecodeError):
            return None  # Outer recorder rewrites its JSON; retry partial reads.

    def wait_for(names):
        state["status"] = "WAITING_FOR_" + "_AND_".join(name.upper() for name in names)
        save()
        while True:
            fixed_inputs()
            complete = {}
            for name in names:
                stage = plan["stages"][name]
                receipt_path = Path(stage["receipt"])
                receipt = optional(receipt_path)
                output = (Path(stage["command"][-1]) if name == "ordinary_c"
                          else option(stage["command"], "--output"))
                target_path = output / "state.json"
                target = optional(target_path)
                if target and "FAIL" in str(target.get("status", "")):
                    raise RuntimeError(name + " controller failed; dependent commands stopped")
                if not receipt:
                    continue
                require(receipt.get("command") == stage["command"] and receipt.get("cwd") == str(repo),
                        name + " outer command/cwd differs")
                if receipt.get("exit_code") is None:
                    continue
                require(type(receipt["exit_code"]) is int and receipt["exit_code"] == 0,
                        name + " outer command failed")
                require(target is not None and target.get("status") == PASS[name],
                        name + " outer exit zero without required controller status")
                require(type(receipt.get("pid")) is int and type(receipt.get("child_pid")) is int
                        and receipt["pid"] > 0 and receipt["child_pid"] > 0 and "finished" in receipt,
                        name + " outer process receipt incomplete")
                complete[name] = dict(receipt=str(receipt_path), receipt_sha256=sha(receipt_path),
                    state=str(target_path), state_sha256=sha(target_path), status=target["status"])
            if len(complete) == len(names):
                state["dependencies"].update(complete)
                save()
                return
            time.sleep(15)

    def execute(job):
        fixed_inputs()
        receipt = Path(job["receipt"])
        for path in [receipt, receipt.with_suffix(".stdout.log"), receipt.with_suffix(".stderr.log"),
                     *map(Path, job["outputs"])]:
            absent(path)
        argv = ["taskset", "-c", "2", "python3", "-B", str(recorder),
                str(receipt), str(repo), *job["command"]]
        row = dict(job, argv=argv, cwd=str(repo), started=now(), exit_code=None)
        state["stages"].append(row)
        state.update(status="RUNNING_" + job["name"].upper(), active=job["name"])
        save()
        process = subprocess.Popen(argv, cwd=repo)
        row["pid"] = process.pid
        state["commands_started"] += 1
        save()
        code = process.wait()
        row.update(exit_code=code, finished=now())
        state["active"] = None
        save()
        require(code == 0, job["name"] + " recorder returned nonzero")
        actual = read(receipt)
        require(actual["command"] == job["command"] and actual["cwd"] == str(repo)
                and type(actual.get("exit_code")) is int and actual["exit_code"] == 0,
                job["name"] + " actual receipt differs")
        row["receipt_sha256"] = sha(receipt)
        row["transcripts"] = {str(path): sha(path) for path in
                             (receipt.with_suffix(".stdout.log"), receipt.with_suffix(".stderr.log"))}
        require(all(Path(path).exists() for path in job["outputs"]), job["name"] + " output missing")
        fixed_inputs()
        save()
        print(job["name"] + " COMMAND_EXIT_ZERO_REVIEW_PENDING", flush=True)

    save()
    try:
        wait_for(("fullcore",))
        for job in jobs[:4]:
            execute(job)
        wait_for(("matrix", "ordinary_c"))
        for job in jobs[4:]:
            execute(job)
        fixed_inputs()
        state["status"] = "COMMANDS_EXIT_ZERO_REVIEW_PENDING"
    except BaseException as error:
        state.update(status="FAILED", error=repr(error))
        # Preserve every output and receipt. Never kill an existing EMU or a child.
        raise
    finally:
        state["finished"] = now()
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    run(args.plan.resolve(), args.state_dir.resolve(), args.check)
