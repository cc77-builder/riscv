"""Recheck immutable O1 campaign logs without launching an emulator.

Original checkers are SHA-verified Git blobs from source_commit_at_start. The
new runtime gate and this auditor have separate identities. A completed-only
probe always remains PARTIAL_AUDIT, even when all selected jobs pass.
"""
import argparse
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
JOB_NAMES = ("hello-vadd", "negative-vdot") + tuple(f"functional-{i}" for i in range(8)) + ("control", "dense-batch128")
DRIVERS = ("team/optimizations/o1/fullcore/run_suite.py", "team/optimizations/o1/fullcore/analyze.py",
           "team/optimizations/o1/fullcore/check_control.py", "team/scripts/artifact_guard.py",
           "team/scripts/check-vdot-run.py", "team/workloads/vdot-perf/check.py")
RAW_NAMES = ("stdout.log", "stderr.log", "run.log")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def check_hashes(pins):
    require(isinstance(pins, dict) and bool(pins), "missing nonempty hash inventory")
    for name, digest in pins.items():
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "invalid digest: " + name)
        require(sha(name) == digest, "artifact hash mismatch: " + name)


def git_blobs(repo, revision, names):
    """Read exact immutable blobs, never substitute current checkout bytes."""
    require(isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision), "invalid original source commit")
    resolved = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "--verify", revision + "^{commit}"], text=True).strip()
    require(resolved == revision, "original source revision is not the specified commit")
    names = list(names)
    for name in names:
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and "\n" not in name,
                "unsafe Git blob path")
    requests = "".join(revision + ":" + name + "\n" for name in names).encode()
    data = subprocess.check_output(["git", "-C", str(repo), "cat-file", "--batch"], input=requests)
    stream, result = io.BytesIO(data), {}
    for name in names:
        header = stream.readline().decode().rstrip("\n").split()
        require(len(header) == 3 and header[1] == "blob", "missing original Git blob: " + name)
        size = int(header[2]); body = stream.read(size)
        require(len(body) == size and stream.read(1) == b"\n", "truncated Git blob: " + name)
        result[name] = body
    require(not stream.read(), "extra Git blob output")
    return result


def bind_original_drivers(repo, revision, recorded):
    expected = {str(repo / name) for name in DRIVERS}
    require(set(recorded) == expected, "original driver inventory is not exactly the six frozen checkers")
    blobs = git_blobs(repo, revision, DRIVERS)
    for name, body in blobs.items():
        require(hashlib.sha256(body).hexdigest() == recorded[str(repo / name)],
                "original driver does not match its Git source commit: " + name)
    return blobs


def load_blob(name, path, body):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def inventory(campaign, completed_only):
    present = {p.name for p in campaign.iterdir() if p.is_dir()}
    require(present <= set(JOB_NAMES), "unexpected campaign job directory")
    complete = {}
    for name in JOB_NAMES:
        result = campaign / name / "result.json"
        if result.exists():
            row = read_json(result)
            require(row.get("name") == name and row.get("finished") and row.get("status") != "RUNNING",
                    "incomplete or wrong job receipt: " + name)
            complete[name] = row
    if completed_only:
        require(bool(complete), "no completed job receipts")
    else:
        require(present == set(JOB_NAMES) and set(complete) == set(JOB_NAMES), "whole-suite inventory requires all 12 completed jobs")
    return complete


def check_raw_job(directory, record, command, files, negative_target):
    require(record.get("command") == command, "recorded command differs from frozen job")
    require(record.get("files") == files and record.get("negative_target") == negative_target,
            "recorded job inputs differ from frozen workload/reference")
    runtime = read_json(directory / "runtime.json")
    for field in ("name", "started", "command", "files", "negative_target"):
        require(runtime.get(field) == record.get(field), "runtime/result disagreement: " + field)
    require(datetime.fromisoformat(record["started"]) <= datetime.fromisoformat(record["finished"]), "negative job duration")
    require(set(record.get("raw_logs_sha256", {})) == set(RAW_NAMES), "missing raw stream hashes")
    raw = {name: (directory / name).read_bytes() for name in RAW_NAMES}
    for name, body in raw.items():
        require(hashlib.sha256(body).hexdigest() == record["raw_logs_sha256"][name], "raw log hash mismatch: " + name)
    require(raw["run.log"] == raw["stderr.log"] + raw["stdout.log"], "derived run.log is not stderr + stdout")
    if "raw_sha256" in record:
        require(record["raw_sha256"] == record["raw_logs_sha256"], "secondary raw hash inventory differs")
    rc_text = (directory / "exit-code.txt").read_text(encoding="ascii")
    require(re.fullmatch(r"-?\d+\n", rc_text), "malformed exit-code file")
    rc = int(rc_text)
    require(type(record.get("exit_code")) is int and rc == record["exit_code"], "actual/recorded exit code mismatch")
    # Match original Path.read_text() newline handling; keep raw bytes separate.
    text = io.TextIOWrapper(io.BytesIO(raw["run.log"]), encoding="utf-8", newline=None).read()
    return rc, text


def original_arguments(state, runner):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hardware-pins", type=Path, required=True)
    parser.add_argument("--emu", type=Path, required=True)
    parser.add_argument("--t12-root", type=Path, default=runner.DEFAULT_T12)
    parser.add_argument("--t14-root", type=Path, default=runner.DEFAULT_T14)
    parser.add_argument("--dense-build", type=Path, default=runner.DEFAULT_DENSE)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout", default="120m")
    invocation = state["invocation"]
    require(isinstance(invocation, list) and invocation and invocation[0] in (DRIVERS[0], str(ROOT / DRIVERS[0])), "wrong original runner invocation")
    flags = invocation[1::2]
    require(len(invocation) % 2 == 1 and len(set(flags)) == len(flags), "duplicate/malformed invocation options")
    args = parser.parse_args(invocation[1:])
    args.preflight_only = False
    for field in ("output", "hardware_pins", "emu", "t12_root", "t14_root", "dense_build"):
        setattr(args, field, getattr(args, field).resolve())
    require(args.jobs in (1, 2) and args.jobs == state["jobs"] and args.timeout == state["timeout"], "original execution limits disagree")
    require(str(args.emu) == state["emu"] and str(args.hardware_pins) == state["hardware_pins"] and str(args.output) == state["output"], "original execution paths disagree")
    return args


def original_jobs(args, paths):
    matrix = args.t12_root / "runs/t11-matrix-canonical"
    rows = [("hello-vadd", paths["hello"], None, paths["reference"]),
            ("negative-vdot", matrix / "build-0/vdot-exceptions.bin", None, paths["negative"])]
    rows += [(f"functional-{i}", matrix / f"build-{i}/vdot-exceptions.bin", matrix / f"data-{i}", paths["reference"]) for i in range(8)]
    rows += [("control", paths["control"], None, paths["reference"]), ("dense-batch128", paths["dense"], None, paths["reference"])]
    return rows


def recheck_job(name, image, data, reference, original, campaign, out, args, paths, modules, gate):
    runner, analyze, control, _, functional, perf = modules
    directory = campaign / name
    result_dir = out / name; result_dir.mkdir()
    command = ["timeout", args.timeout, "stdbuf", "-o0", "-e0", str(args.emu), "-i", str(image),
               "--flash=" + str(paths["flash"]), "--ram-size=128MB", "--diff=" + str(reference), "--max-cycles=5000000"]
    files = {str(p): sha(p) for p in (args.emu, paths["reference"], reference, paths["flash"], image)}
    record = {"name": name, "original_status": original["status"], "started": original["started"],
              "finished": original["finished"], "files": files, "new_emu_executed": False}
    try:
        rc, text = check_raw_job(directory, original, command, files, "vdot" if name == "negative-vdot" else None)
        record.update(exit_code=rc, raw_logs_sha256=original["raw_logs_sha256"])
        runner.validate_runtime(text, reference)
        if name == "negative-vdot":
            record["runtime_gate"] = gate.validate_negative(text, rc)
            # This adjacency is checked in stdout itself, not inferred across streams.
            stdout = gate.normalize_console((directory / "stdout.log").read_bytes().decode())
            mismatch, abort = list(gate.MISMATCH.finditer(stdout)), list(gate.ABORT.finditer(stdout))
            require(len(mismatch) == len(abort) == 1 and mismatch[0].end() < abort[0].start() and
                    not stdout[mismatch[0].end():abort[0].start()].strip(), "negative terminal chain not adjacent in raw stdout")
        else:
            require(rc == 0, "normal workload did not exit zero")
            gate.validate_failure_markers(text)
        observation = analyze.analyze(text, require_complete=name != "negative-vdot")
        runner.validate_observation(observation, negative=name == "negative-vdot")
        require(observation["schema"]["handoff"] == 1, "observer schema disagrees with O1 hardware mode")
        save(result_dir / "observation.json", observation)
        _, uart = analyze.extract_events_and_uart(text)
        if name == "negative-vdot":
            record.update(status="EXPECTED_VDOT_HIGHBIT_REJECTION", observation_scope="partial trace until intentional DiffTest stop")
        elif data is not None:
            count = read_json(data / "manifest.json")["smoke_count"]
            require(observation["counts"].get("COMMIT") == count and observation["counts"].get("ACCEPT", 0) >= count > 0, "functional observation count mismatch")
            save(result_dir / "functional-result.json", functional.validate(uart, "full", rc, data, require_diff=True))
            record.update(status="VDOT_MATRIX_SHARD_PASS", expected_vdot_commits=count)
        elif name == "control":
            result = control.check(text, read_json(paths["control"].parent / "data/manifest.json"), rc, analysis=observation)
            save(result_dir / "control-result.json", result)
            record.update(runner.classify_control(result))
        elif name == "dense-batch128":
            result = perf.verify(args.dense_build, directory)
            save(result_dir / "window-result.json", result)
            require(result.get("status") == "PASS" and len(result["samples"]) == 12, "dense calibrated window gate failed")
            count = sum(s["dots"] for s in result["samples"] if s["method"] == "vdot")
            require(observation["counts"].get("COMMIT") == count and observation["counts"].get("ACCEPT", 0) >= count > 0, "dense observation count mismatch")
            require(observation["counts"].get("HANDOFF", 0) > 0, "dense workload did not cover handoff")
            record.update(status="O1_DENSE_HANDOFF_AND_WINDOWS_PASS", checked_windows=12, expected_vdot_commits=count, performance_comparison=False)
        else:
            require(observation["counts"].get("ACCEPT") == observation["counts"].get("COMMIT") == 0, "unexpected vdot in hello/vadd")
            require("HELLO_VADD_PASS" in uart and "HIT GOOD TRAP" in uart, "missing hello/vadd success")
            record["status"] = "HELLO_VADD_PASS"
        record.update(observation_status=observation["status"], observation_counts=observation["counts"])
    except Exception as exc:
        record.update(status="FAILED", error=repr(exc))
    save(result_dir / "result.json", record)
    return record


def validate_final_campaign(state, preflight, pins, originals, final):
    require(state.get("status") in ("O1_FULLCORE_SUITE_PASS", "O1_FULLCORE_SUITE_FAILED") and state.get("finished"), "campaign has not ended")
    require(final.get("status") == state["status"] and len(final.get("runs", [])) == 12, "missing original final campaign inventory")
    require(final.get("hardware_pins_sha256") == preflight["hardware_pins_sha256"] and
            final.get("build_source_commit") == pins["source_commit"] and
            final.get("finished") == state["finished"], "final campaign source/pins/completion metadata disagree")
    listed = {row["name"]: row for row in final["runs"]}
    require(listed == originals and len(listed) == 12, "campaign/per-job receipts disagree")


def summarize_verdict(completed_only, suite_pass, selected_pass):
    return {"status": "O1_PARTIAL_AUDIT" if completed_only else (
                "O1_OFFLINE_FULL_SUITE_RECHECK_PASS" if suite_pass else "O1_OFFLINE_FULL_SUITE_RECHECK_FAILED"),
            "checks_passed": bool(selected_pass) if completed_only else bool(suite_pass),
            "whole_suite_pass": bool(suite_pass) and not completed_only}


def audit(args):
    campaign = args.campaign.resolve(); out = args.output.resolve()
    require(args.output.is_absolute() and not out.exists(), "output must be a new absolute directory")
    require(not out.is_relative_to(campaign) and not campaign.is_relative_to(out) and not out.is_relative_to(ROOT), "output overlaps campaign/source")
    out.mkdir(parents=True)
    result = {"status": "O1_PARTIAL_AUDIT" if args.completed_only else "O1_OFFLINE_FULL_SUITE_RECHECK_FAILED",
              "checks_passed": False, "whole_suite_pass": False, "new_emu_executed": False,
              "emulators_executed": 0, "completed_only": args.completed_only, "campaign": str(campaign),
              "created": datetime.now().astimezone().isoformat(), "runs": [], "performance_measured": False}
    try:
        state_bytes = (campaign / "campaign-state.json").read_bytes()
        state = json.loads(state_bytes)
        preflight = read_json(campaign / "preflight.json")
        pins = read_json(campaign / "hardware-pins.json")
        require(state.get("preflight_only") is False and state.get("output") == str(campaign), "not a real campaign at this path")
        require(preflight.get("status") == "O1_FULLCORE_INPUTS_VERIFIED" and preflight.get("hardware_checked") is True, "campaign inputs were not hardware verified")
        originals = inventory(campaign, args.completed_only)
        stable = {str(campaign / name): sha(campaign / name) for name in ("preflight.json", "hardware-pins.json")}
        for name in originals:
            for leaf in ("result.json", "runtime.json", "exit-code.txt") + RAW_NAMES:
                stable[str(campaign / name / leaf)] = sha(campaign / name / leaf)
        if not args.completed_only:
            final = read_json(campaign / "result.json")
            validate_final_campaign(state, preflight, pins, originals, final)
            for leaf in ("result.json", "campaign-state.json"):
                stable[str(campaign / leaf)] = sha(campaign / leaf)
        blobs = bind_original_drivers(ROOT, state["source_commit_at_start"], preflight["driver_files"])
        names = ("o1_original_runner", "analyze", "o1_original_control", "o1_original_guard", "o1_original_functional", "o1_original_perf")
        modules = [load_blob(name, ROOT / path, blobs[path]) for name, path in zip(names, DRIVERS)]
        runner, _, _, guard, _, perf = modules
        original_args = original_arguments(state, runner)
        require(original_args.output == campaign, "invocation belongs to another campaign")
        require(sha(original_args.hardware_pins) == preflight["hardware_pins_sha256"] and read_json(original_args.hardware_pins) == pins, "original/copy hardware pins disagree")
        require(state.get("build_source_commit") == pins["source_commit"] and pins.get("source_root") == str(ROOT), "hardware source identity mismatch")
        hardware_blobs = git_blobs(ROOT, pins["source_commit"], pins["files"])
        for name, body in hardware_blobs.items():
            require(hashlib.sha256(body).hexdigest() == pins["files"][name], "hardware pin does not match build source commit: " + name)
        _, paths, fresh = runner.preflight(original_args, guard, perf)
        # Current driver bytes may have changed only as separately versioned audit
        # work. Their old identities were verified above from exact Git blobs.
        require({k: v for k, v in fresh.items() if k != "driver_files"} ==
                {k: v for k, v in preflight.items() if k != "driver_files"}, "frozen input/provenance preflight differs")
        gate_path = HERE / "runtime_gate.py"
        gate = load_blob("o1_recheck_runtime_gate", gate_path, gate_path.read_bytes())
        new_checkers = {str(p): sha(p) for p in (Path(__file__), gate_path)}
        (out / "new-checkers").mkdir()
        for path, digest in new_checkers.items():
            body = Path(path).read_bytes()
            require(hashlib.sha256(body).hexdigest() == digest, "new checker changed while snapshotting")
            (out / "new-checkers" / Path(path).name).write_bytes(body)
        stable.update({str(original_args.hardware_pins): preflight["hardware_pins_sha256"]})
        stable.update(preflight["input_files"])
        stable.update(new_checkers)
        check_hashes(stable)
        result.update(original_source_commit=state["source_commit_at_start"], build_source_commit=pins["source_commit"],
                      original_driver_files=preflight["driver_files"], new_checker_files=new_checkers,
                      hardware_pins_sha256=preflight["hardware_pins_sha256"], emu_sha256=preflight["emu_sha256"],
                      hardware_source_git_blobs_verified=len(hardware_blobs), dependency_files_verified=len(pins["dependency_files"]),
                      input_files_verified=len(preflight["input_files"]), selected_jobs=list(originals),
                      missing_jobs=[n for n in JOB_NAMES if n not in originals],
                      original_campaign_state_snapshot=state, original_campaign_state_sha256=hashlib.sha256(state_bytes).hexdigest())
        for name, body in blobs.items():
            target = out / "original-checkers" / name
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(body)
        save(out / "input-audit.json", {"original_evidence_and_inputs": stable, "new_checker_files": new_checkers,
                                       "original_driver_git_revision": state["source_commit_at_start"],
                                       "original_driver_files": preflight["driver_files"]})
        for job in original_jobs(original_args, paths):
            if job[0] in originals:
                result["runs"].append(recheck_job(*job, originals[job[0]], campaign, out, original_args, paths, modules, gate))
        runner.hardware_guard(pins, original_args.emu)
        check_hashes(stable)
        matrix_image = original_args.t12_root / "runs/t11-matrix-canonical/build-0/vdot-exceptions.bin"
        passed, recovery, coverage = runner.assess_suite(result["runs"], matrix_image)
        selected_pass = all(row["status"] != "FAILED" for row in result["runs"])
        result.update(summarize_verdict(args.completed_only, passed, selected_pass))
        result.update(normal_reference_recovery=recovery, suite_coverage=coverage,
                      original_evidence_unchanged=True,
                      coverage_policy="F2v retains seven legacy obligations; dense independently requires HANDOFF>0; local F2v handoff miss stays explicit.")
    except (Exception, SystemExit) as exc:
        result["error"] = repr(exc)
    result["finished"] = datetime.now().astimezone().isoformat()
    result["scope"] = "offline original-evidence recheck with a separately identified runtime gate; no new EMU run or performance comparison"
    save(out / "result.json", result)
    print(json.dumps({k: result[k] for k in ("status", "checks_passed", "whole_suite_pass", "new_emu_executed")}))
    return 0 if result["checks_passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--completed-only", action="store_true")
    return audit(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
