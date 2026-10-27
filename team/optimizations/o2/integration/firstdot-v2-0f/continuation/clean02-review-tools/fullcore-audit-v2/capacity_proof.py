"""Exact read-only capacity exception; preserves the original wall-clock FAIL.

Only the named completed clean-02 campaign is accepted. This module does not
launch targets, decode full traces, change timestamps, or grant a raw-audit PASS.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

CASE_FILE = Path(__file__).with_name("exact-case.json")
CASE_SHA256 = "a48cbceada7c955293e22aefb9e9e9c9e03a3a7a00efcc78d9321820197d968e"
SPAWN_FIELDS = (
    "name", "started", "command", "files", "negative_target", "cwd",
    "auxiliary_files", "environment_overrides", "process_started", "pid",
    "pid_kind", "actual_new_execution", "performance_measured", "exit_code",
    "timed_out", "terminated_returncode",
)
STATUS = "CURRENT_CLEAN_SOURCE_BOUND_CAPACITY_PASS_WALL_CLOCK_LIMITED"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def _case():
    raw = CASE_FILE.read_bytes()
    require(digest(raw) == CASE_SHA256, "exact case source changed")
    value = json.loads(raw)
    require(value["schema"] == "current-clean-exact-wall-capacity-case-v1"
            and value["jobs"] == 3 and value["source_new_emu_runs"] == 14
            and value["recorded_peak"] == 4
            and value["anomaly"]["microseconds"] == 80119
            and value["original_wall_clock_capacity"] == "FAIL"
            and value["os_monotonic_capacity_measured"] is False,
            "unexpected exact case contract")
    return value


def source_inputs():
    """Pinned absolute-path -> SHA map; no live-source reads (for sealed bytes)."""
    return dict(_case()["files"])


def _verify_files(files):
    for filename, expected in files.items():
        path = Path(filename)
        require(path.is_absolute() and path.is_file() and not path.is_symlink(),
                "missing/nonregular exact evidence: " + filename)
        require(path.stat().st_size < 8 * 1024 * 1024, "unexpected large input")
        require(digest(path.read_bytes()) == expected,
                "exact evidence changed: " + filename)


def _date(value):
    parsed = datetime.fromisoformat(value)
    require(parsed.utcoffset() is not None, "naive timestamp")
    return parsed


def _timeline(rows, state):
    events = []
    for name, row in rows.items():
        start, finish = _date(row["started"]), _date(row["finished"])
        require(_date(state["started"]) <= start <= finish <= _date(state["finished"]),
                "record outside campaign or reversed")
        events.extend(((start, 1, name), (finish, -1, name)))
    events.sort()  # Original checker orders finish (-1) before start (+1) on ties.
    active, peak, over = set(), 0, []
    for index, (at, delta, name) in enumerate(events):
        if delta == 1:
            require(name not in active, "duplicate start event")
            active.add(name)
        else:
            require(name in active, "finish without start")
            active.remove(name)
        peak = max(peak, len(active))
        if len(active) > state["jobs"]:
            require(index + 1 < len(events), "unclosed overlap")
            end, next_delta, next_name = events[index + 1]
            over.append(dict(
                start=at.isoformat(), finish=end.isoformat(),
                microseconds=(end - at) // timedelta(microseconds=1),
                names=sorted(active), trigger=name, next_event=next_name,
                next_event_delta=next_delta,
            ))
    require(not active, "unclosed process interval")
    return peak, over


def _validate_loaded(case, state, result, rows, runtimes, outer, failure, post,
                     stdout, failure_stderr, e):
    names = set(case["expected_names"])
    require(set(rows) == set(runtimes) == names and len(names) == 14,
            "exact 14 process inventory required")
    require(state["status"] == result["status"] == "CURRENT_CLEAN_FULLCORE_PASS"
            and type(state["jobs"]) is int and state["jobs"] == 3
            and state["cpu_affinity"] == case["cpu_affinity"]
            and state["new_emu_runs"] == state["new_emu_launch_attempts"] == 14
            and type(state["new_emu_runs"]) is int and not state["active"],
            "completed max3 campaign required")
    require(result["source_commit"] == case["source_commit"]
            and result["emu_sha256"] == case["emu_sha256"]
            and result["new_emu_runs"] == result["selected_jobs"] == 14
            and result["reused_execution_verdicts"] == 0
            and result["normal_reference_recovery"] is True
            and result["matrix_unique"] == 117 and result["matrix_executed"] == 124,
            "campaign result identity or counts differ")
    require(state["controller_sha256"] == case["files"][case["controller_source"]]
            and state["identity_sha256"] == case["files"][case["run"] + "/identity.json"],
            "controller/identity receipt binding differs")
    require(tuple(e.SPAWN_FIELDS) == SPAWN_FIELDS
            and str(Path(e.spawn_binding.__code__.co_filename).resolve()) == case["spawn_source"],
            "original spawn binding implementation required")
    bound = {}
    for name in sorted(names):
        row, runtime = rows[name], runtimes[name]
        require(row["name"] == name, "record name differs")
        expected_exit = 1 if name == "negative-vdot" else 0
        require(type(row.get("exit_code")) is int and row["exit_code"] == expected_exit,
                "unexpected target exit")
        require(row.get("process_started") is True
                and row.get("actual_new_execution") is True
                and row.get("performance_measured") is False
                and not row.get("timed_out")
                and row.get("terminated_returncode") is None,
                "incomplete or non-correctness child")
        bound[name] = e.spawn_binding(runtime, row)
    require(len({r["pid"] for r in rows.values()}) == 14,
            "exact case has unexpected PID identity")
    negative, recovery, hello = (rows[n] for n in
                                ("negative-vdot", "functional-0", "hello-vadd"))
    require(negative["status"] == "EXPECTED_VDOT_HIGHBIT_REJECTION"
            and recovery["status"] == "VDOT_MATRIX_SHARD_PASS"
            and _date(negative["finished"]) <= _date(recovery["started"])
            and negative["command"][6:8] == recovery["command"][6:8]
            and negative["command"][6] == "-i",
            "same-image negative/recovery relation differs")
    image = negative["command"][7]
    require(negative["files"][image] == recovery["files"][image],
            "negative/recovery image hash differs")
    require(all(_date(hello["finished"]) <= _date(r["started"])
                for n, r in rows.items() if n != "hello-vadd"),
            "synchronous hello-before-pool relation differs")
    require(type(outer.get("exit_code")) is int and outer["exit_code"] == 0
            and outer["cwd"] == case["repo"]
            and outer["command"][2] == case["controller_source"]
            and outer["command"][outer["command"].index("--jobs") + 1] == "3",
            "actual parent command/exit differs")
    require(_date(outer["started"]) <= _date(state["started"])
            <= _date(state["finished"]) <= _date(outer["finished"])
            <= _date(failure["started"]), "parent/child causal timestamps differ")
    completion = [
        dict(line=index + 1, text=line)
        for index, line in enumerate(stdout.splitlines())
        if line.split(" ", 1)[0] in names
    ]
    require(completion == case["completion_lines"], "controller completion order differs")
    require(type(failure.get("exit_code")) is int and failure["exit_code"] == 1
            and post["status"] == "FAILED" and post["commands_started"] == 1
            and len(post["stages"]) == 1
            and post["stages"][0]["name"] == "fullcore_physical"
            and post["stages"][0]["exit_code"] == 1
            and "recorded concurrency exceeds worker budget" in failure_stderr,
            "original v1 failure not retained")
    peak, anomalies = _timeline(rows, state)
    require(peak == case["recorded_peak"] and anomalies == [case["anomaly"]],
            "not the sole pinned 80119us anomaly")
    return dict(
        status=STATUS, source_new_emu_runs=14, new_emu_runs=0, jobs=3,
        records=bound, wall_clock_capacity="FAIL", recorded_peak=4,
        source_bound_worker_capacity="PASS", max_workers=3,
        os_monotonic_capacity_measured=False, clock_cause="UNCONFIRMED",
        exact_anomaly=case["anomaly"], exact_case_sha256=CASE_SHA256,
        original_v1_failure="FAIL_PRESERVED",
        original_failure_receipt_sha256=case["files"][case["original_failure_command"]],
        original_post_state_sha256=case["files"][case["original_post_state"]],
        controller_stdout_sha256=case["files"][case["outer_stdout"]],
        source_sha256=dict(case["source_files"]),
        evidence_inputs=dict(case["files"]),
        basis="Hash-bound synchronous hello; max3 ThreadPool; one blocking spawn/wait per worker; pair serial; no independent OS overlap measurement.",
        original_wall_gate_verdict_preserved=True,
        acceptance_scope="Separately named source-bound capacity contract; original UTC wall gate stays FAIL",
        timestamps_modified=False, records_reordered=False, tolerance_applied=False,
        semantic_raw_audit_granted=False,
    )


def process_proof(run, e):
    """Pure read of this exact campaign; original architecture/trace audit follows."""
    case = _case()
    run = Path(run)
    require(str(run) == case["run"] and str(run.resolve()) == case["run"],
            "only the exact named completed campaign is supported")
    _verify_files(case["files"])
    rows, runtimes = {}, {}
    actual_names = {p.name for p in (run / "runs").iterdir()}
    require(actual_names == set(case["expected_names"]), "unexpected run directory")
    for name in case["expected_names"]:
        directory = run / "runs" / name
        rows[name] = read(directory / "result.json")
        runtimes[name] = read(directory / "runtime.json")
        require((directory / "exit-code.txt").read_text()
                == str(rows[name]["exit_code"]) + "\n", "real exit file differs")
    proof = _validate_loaded(
        case, read(run / "state.json"), read(run / "results.json"), rows, runtimes,
        read(case["outer_command"]), read(case["original_failure_command"]),
        read(case["original_post_state"]), Path(case["outer_stdout"]).read_text(),
        Path(case["original_failure_stderr"]).read_text(), e,
    )
    _verify_files(case["files"])
    return proof
