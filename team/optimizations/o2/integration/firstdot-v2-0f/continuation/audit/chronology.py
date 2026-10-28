"""Narrow forensic supplement for one frozen wall-clock discontinuity.
Never edits timestamps, reruns EMU, reorders records, or grants wall-clock PASS.
Caller still must perform full raw/semantic audit independently.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path

CONTRACT = "zjhwork-firstdot-causal-order-wall-clock-limited-v1"
LEAF = "team/optimizations/o2/integration/firstdot-v2-0f"
SOURCES = {
    LEAF + "/combination.py": "22a418c4a95c47b8226d2e0b1453b0b09f02c62cfe2add09aef135b10c7fe7bc",
    "team/optimizations/o2/r2-safe-tail/merged_screen.py": "ff75464c5b0f75349fc4321bdd80a7a85985a54ae415ad347c3ce04fdf4bd885",
    "team/optimizations/o2/r2-safe-tail/fullcore_screen.py": "5f5c719a9a5b675f4de166ca30a3d89bd52c944c667cee302f66da94fa2779f2",
    LEAF + "/continuation/matrix/continuation.py": "cefc280fe142428b79c858eb83cc4db59aeb011dd8165b4b69c188ec71d35482",
    LEAF + "/continuation/matrix/audit_snapshot.py": "f0a5419a751d25404a51deb6555e162116f16a542b336d85d37fcfdcc4037d98",
    LEAF + "/continuation/matrix/CONTRACT.md": "6ebd06e56746f65d3a0974ae70f0fb0d6f45b01bc96367f14947620be4463e87",
}
RECEIPTS = {
    "combination-run-01.command.json": "49d9ab8d8f46a96e7bb2c3bb6c7f7830e6d5ef510576482a86afaa14600312ee",
    "combination-run-01.command.stdout.log": "7148cdd1f421409ed8cfbb793926e9f09a2eb4e7d1b9371ff241548742abe72e",
    "combination-run-01.command.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "combination-resume-01.command.json": "bc766a94d1c3b704b377205eb3de22e5985817e32b7626501740de14f04db36d",
    "combination-resume-01.command.stdout.log": "7a8865037f0b4e3e552692fb8e61437200ef1b686900429ea865509512eeaee3",
    "combination-resume-01.command.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
A = "formal-performance-s1-d0-s01"
B = "formal-performance-s1-d1-s01"
BOUND_RECORDS = {
    A: dict(sha256="bdca4b1645c29b71bece59985ffe01284e8c69af5abb8f8e6f046609040c582b",
            started="2026-10-26T07:03:35.152993+00:00",
            finished="2026-10-26T07:07:55.796377+00:00", pid=1252, exit_code=0),
    B: dict(sha256="e578b7a006286be7d9e5d916a7f16a55a8c3baafe67e310959869eac42cd2a49",
            started="2026-10-26T07:07:55.252896+00:00",
            finished="2026-10-26T07:12:16.488504+00:00", pid=1437, exit_code=0),
}

def require(ok, reason):
    if not ok:
        raise ValueError("causal chronology: " + reason)

def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for raw in iter(lambda: stream.read(1048576), b""):
            value.update(raw)
    return value.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def stamp(value):
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, "timezone required")
    return result

def verify(a, repo, run, ordered_labels, all_records, locations):
    """Return explicit limited causal proof and physical input closure; read only."""
    repo, run = Path(repo).resolve(), Path(run).resolve()
    inputs = read(run / "continuation-inputs.json")
    prior = Path(inputs["prior_root"]).resolve()
    require(run.name == "combination-resume-01" and prior.name == "combination-run-01"
            and run.parent == prior.parent, "only the frozen recorded attempts allowed")
    require(inputs["repo"] == str(repo), "repo differs")
    labels = list(ordered_labels)
    require(len(labels) == len(set(labels)) == 33 and
            labels == list(read(run / "run-locations.json")) and
            locations == read(run / "run-locations.json"), "frozen dispatch inventory/order")
    if isinstance(all_records, dict):
        require(set(all_records) == set(labels), "record dictionary inventory")
        rows = [all_records[label] for label in labels]
    else:
        rows = list(all_records)
    require(len(rows) == 33, "complete records required")
    receipts = {str(run.parent / name): digest for name, digest in RECEIPTS.items()}
    sources = {str(repo / name): digest for name, digest in SOURCES.items()}
    external = sources | receipts
    for filename, digest in external.items():
        require(sha(filename) == digest, "frozen source/parent receipt changed: " + filename)
    for filename in ("continuation-inputs.json", "run-locations.json", "runtime-inputs.json",
                     "prior-evidence-snapshot.json", "interrupted-processes.json",
                     "state.json", "results.json"):
        external[str(run / filename)] = sha(run / filename)
    external[str(prior / "runtime-inputs.json")] = sha(prior / "runtime-inputs.json")
    old_common, common = read(prior / "runtime-inputs.json"), read(run / "runtime-inputs.json")
    require(old_common == common, "runtime closure differs")
    for rel in tuple(SOURCES)[:3]:
        require(common.get(str(repo / rel)) == SOURCES[rel], "blocking source missing from runtime closure")
    expected_controller = {str(repo / name): digest for name, digest in SOURCES.items()
                           if "/continuation/" in name}
    require(inputs["controller_files"] == expected_controller, "continuation source closure")
    for filename, digest in common.items():
        require(sha(filename) == digest, "physical runtime input changed: " + filename)
    external.update(common)
    for index, (label, row) in enumerate(zip(labels, rows)):
        directory = Path(locations[label])
        expected = (prior if index < 12 else run) / "runs" / label
        require(directory == expected and row == read(directory / "result.json"), "record/location mismatch")
        require(row["cwd"] == str(directory / "cwd") and row.get("process_started") is True
                and type(row.get("pid")) is int and row["pid"] > 0
                and not row.get("timed_out"), "actual process identity/completion")
        require(stamp(row["started"]) <= stamp(row["finished"]), "within-record reversed time")
        expected_status = "EXPECTED_VDOT_HIGHBIT_REJECTION" if index == 0 else "R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS"
        require(row["status"] == expected_status and type(row.get("exit_code")) is int
                and row["exit_code"] == (1 if index == 0 else 0), "record acceptance/exit")
        external[str(directory / "result.json")] = sha(directory / "result.json")
    for label, expected in BOUND_RECORDS.items():
        row = rows[labels.index(label)]
        require(external[str(Path(locations[label]) / "result.json")] == expected["sha256"]
                and all(row[k] == v for k, v in expected.items() if k != "sha256"),
                "unique anomaly receipt changed")
    anomalies = []
    for (la, ra), (lb, rb) in zip(zip(labels, rows), zip(labels[1:], rows[1:])):
        ta, tb = stamp(ra["finished"]), stamp(rb["started"])
        if ta > tb:
            delta = ta - tb
            micros = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
            require((la, lb, micros) == (A, B, 543481), "unrecognized wall-clock reversal")
            anomalies.append(dict(before_label=la, after_label=lb,
                before_record_sha256=BOUND_RECORDS[A]["sha256"],
                after_record_sha256=BOUND_RECORDS[B]["sha256"],
                before_finished=ra["finished"], after_started=rb["started"],
                backward_microseconds=micros))
    require(len(anomalies) == 1, "exactly the frozen single anomaly required")
    old_command, new_command = [read(run.parent / (name + ".command.json")) for name in (prior.name, run.name)]
    require(old_command["command"] == ["python3", "-B", str(repo / LEAF / "combination.py"),
        "--identity", inputs["identity"], "--action", "run", "--build", inputs["build"],
        "--output", str(prior)], "original command differs")
    require(new_command["command"] == ["python3", "-B", str(repo / LEAF / "continuation/matrix/continuation.py"),
        "--action", "run", "--repo", str(repo), "--identity", inputs["identity"],
        "--build", inputs["build"], "--prior", str(prior), "--output", str(run),
        "--operation-id", "20261026-cc77-builder-firstdot-resume"], "continuation command differs")
    for command in (old_command, new_command):
        require(command["cwd"] == str(repo) and type(command["pid"]) is int and command["pid"] > 0
                and type(command["child_pid"]) is int and command["child_pid"] > 0
                and command["pid"] != command["child_pid"], "parent process binding")
    require("finished" not in old_command and "exit_code" not in old_command,
            "interrupted original parent must not acquire synthetic exit")
    require(new_command["exit_code"] == 0 and
            stamp(old_command["started"]) <= stamp(rows[0]["started"]) and
            stamp(new_command["started"]) <= stamp(rows[12]["started"]) and
            stamp(rows[-1]["finished"]) <= stamp(new_command["finished"]), "parent lifecycle bounds")
    old_lines = (run.parent / (prior.name + ".command.stdout.log")).read_text().splitlines()
    new_text = (run.parent / (run.name + ".command.stdout.log")).read_text()
    new_lines = new_text.splitlines(keepends=True)
    require(old_lines == [label + " " + row["status"] for label, row in zip(labels[:12], rows[:12])],
            "original completion stdout order")
    require([line.rstrip("\n") for line in new_lines[:21]] ==
            [label + " " + row["status"] for label, row in zip(labels[12:], rows[12:])],
            "continuation completion stdout order")
    require(json.loads("".join(new_lines[21:])) ==
            {k: v for k, v in read(run / "results.json").items() if k not in ("runs", "samples", "rows")},
            "continuation parent final result differs")
    proof = dict(contract=CONTRACT, wall_clock_chronology="FAIL", causal_serial_order="PASS",
        clock_cause="UNCONFIRMED", monotonic_timestamps_recorded=False, anomalies=anomalies,
        source_files=sources, receipt_files=receipts, new_emu_runs=0,
        ordering="frozen_controller_dispatch_sequence", timestamp_values_modified=False,
        records_reordered=False, tolerance_applied=False, qualified_processes=33,
        original_parent_completion="INTERRUPTED_NO_RECORDED_EXIT",
        continuation_parent_completion="EXIT_ZERO",
        causal_evidence=[
            "combination launch synchronously calls merged execute; serial loop waits for return",
            "merged execute calls fullcore spawn; spawn blocks on proc.wait before returning",
            "finished is sampled with datetime.now(timezone.utc), not a monotonic timestamp",
            "PASS stdout is emitted after synchronous execute returns, in the frozen dispatch order"],
        limitations=[
            "No direct monotonic timeline was recorded; the wall-clock reversal cause is unconfirmed.",
            "Concurrent independent C execution is a host-resource fact, not proof of clock-adjustment cause.",
            "Host wall-clock timestamps have no role in the DUT cycle counters; functional/cycle raw audit remains separate.",
            "This explicitly limited causal proof does not convert wall-clock chronology to PASS."])
    return proof, external
