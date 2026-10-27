#!/usr/bin/env python3
"""Verify this local-stage archive and replay its frozen checkers; never run RTL."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    archive = args.archive.resolve()
    output = args.output.resolve()
    require(not output.exists() and not output.is_relative_to(archive),
            "output must be new and outside sealed archive")
    manifest_bytes = (archive / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    payloads = {}
    stored = set()
    for entry in manifest["files"]:
        path = (archive / entry["stored"]).resolve()
        require(path.is_relative_to(archive / "files"), "payload escapes files directory")
        require(entry["path"] not in payloads and entry["stored"] not in stored,
                "duplicate manifest entry")
        packed = path.read_bytes()
        require(len(packed) == entry["stored_bytes"] and
                digest(packed) == entry["stored_sha256"], "stored hash/size mismatch")
        raw = gzip.decompress(packed) if entry["gzip"] else packed
        require(len(raw) == entry["raw_bytes"] and
                digest(raw) == entry["raw_sha256"], "raw hash/size mismatch")
        payloads[entry["path"]] = raw
        stored.add(entry["stored"])
    require(stored == {str(p.relative_to(archive)) for p in
                       (archive / "files").rglob("*") if p.is_file()}, "payload inventory mismatch")
    def raw(name):
        return payloads[name]
    def js(name):
        return json.loads(raw(name))
    prefix = "source-candidate/team/optimizations/o2/"
    frozen = js("support/review-tests/frozen-tests.json")
    for name, value in frozen["files"].items():
        require(digest(raw(prefix + "parent/" + name)) == value, "strict test identity mismatch")
    old = js("runs/red-parent-01/source.json")
    new = js("runs/green-parent-01/source.json")
    rtl = "src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
    require(old.keys() == new.keys() and
            [k for k in old if old[k] != new[k]] == [rtl], "red/green inputs changed beyond RTL")
    require(old[rtl] == digest(raw("source-baseline/" + rtl)) and
            new[rtl] == digest(raw("source-candidate/" + rtl)), "RTL snapshot mismatch")
    red_commands = js("runs/red-parent-01/commands.json")
    require(red_commands[-1]["log"] == "result.log" and red_commands[-1]["exit_code"] == 1 and
            all(c["exit_code"] == 0 for c in red_commands[:-1]), "wrong old-RTL rejection stage")
    red = raw("runs/red-parent-01/result.log").decode()
    require(red.endswith("O2_PARENT_FAIL clock\ncase=DIV-cancel-92 tick=13330 idle FU retained clock after cancellation/completion\n")
            and "O2_PARENT_PASS" not in red, "wrong old-RTL rejection")
    results = {}
    with tempfile.TemporaryDirectory(prefix="r3-div-gate-replay-") as temp:
        for name, key in {
            "check_trace.py": prefix + "parent/check_trace.py",
            "check_negative.py": prefix + "parent/check_negative.py",
            "check_negative_fu.py": prefix + "check_negative_fu.py",
        }.items():
            (Path(temp) / name).write_bytes(raw(key))
        sys.path.insert(0, temp)
        import check_trace
        import check_negative
        import check_negative_fu
        for stage, faults, check in (
            ("green-fu-01", ("identity", "wen", "high", "cancel"), check_negative_fu.check_negative),
            ("green-parent-01", check_negative.FAULTS, check_negative.check_negative),
        ):
            root = "runs/" + stage + "/"
            require(js(root + "runner.status.json")["passed"] is True, "runner incomplete")
            commands = {c["log"]: c for c in js(root + "commands.json")}
            require({n for n in commands if n.startswith("inject-")} ==
                    {"inject-" + f + ".log" for f in faults}, "negative inventory mismatch")
            for name, command in commands.items():
                require(command["exit_code"] == (1 if name.startswith("inject-") else 0),
                        "unexpected exit code " + name)
            for fault in faults:
                name = "inject-" + fault + ".log"
                check(fault, commands[name]["exit_code"], raw(root + name).decode())
            results[stage] = {"negative_checks": len(faults), "expected_exit_codes": True}
        green = raw("runs/green-parent-01/result.log").decode()
        trace = check_trace.check_trace(green)
        legacy = check_negative.check_positive(green)
        require(trace["cancel_idle_samples"] == {1: 72, 2: 72} and
                trace["recomputed"]["cancel_idle_clock_on"] == 0, "strict idle result")
        red_rows = [x for x in red.splitlines() if x.startswith("O2_PARENT_CYCLE ")]
        green_rows = [x for x in green.splitlines() if x.startswith("O2_PARENT_CYCLE ")]
        require(len(red_rows) == 13330 and red_rows == green_rows[:len(red_rows)],
                "red/green common prefix differs")
        results["parent_trace"] = trace
        results["parent_transaction_replay"] = legacy
    report = {
        "status": "R3_DIV_GATE_ARCHIVE_REPLAY_PASS",
        "scope": "Archive bytes and frozen-checker replay only; no RTL/NEMU/fullcore/PPA execution",
        "manifest_sha256": digest(manifest_bytes),
        "audit_script_sha256": digest(Path(__file__).read_bytes()),
        "payloads": len(payloads),
        "red_rejection_verified": True,
        "red_green_equal_prefix_frames": len(red_rows),
        "candidate_exeunit_sha256": new[rtl],
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(report["status"], "payloads", len(payloads), "cycles", trace["cycles"])

if __name__ == "__main__":
    main()
