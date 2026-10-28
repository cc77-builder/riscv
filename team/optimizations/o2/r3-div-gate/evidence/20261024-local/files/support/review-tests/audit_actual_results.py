#!/usr/bin/env python3
"""Read-only independent audit of completed local R3 DIV-gate runs; no hardware execution."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--run-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    need(not args.output.exists(), "refuse existing output")
    args.output.mkdir(parents=True)
    used = {}
    def read(path):
        raw = path.read_bytes()
        used[str(path)] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        return raw
    def txt(path):
        return read(path).decode("utf-8")
    def js(path):
        return json.loads(txt(path))
    def fields(line):
        pairs = [part.split("=", 1) for part in line.split()[1:]]
        need(all(len(v) == 2 for v in pairs), "malformed event")
        row = dict(pairs)
        need(len(row) == len(pairs), "duplicate field")
        return {k: (int(v) if v.isdigit() else v) for k, v in row.items()}
    root = args.run_root
    names = ("red-parent-01", "green-fu-01", "green-parent-01")
    sources, commands, texts = {}, {}, {}
    result = {}
    for name in names:
        run = root / name
        rows = js(run / "commands.json")
        commands[name] = {r["log"]: r for r in rows}
        need(len(commands[name]) == len(rows), "duplicate command log")
        sources[name] = js(run / "source.json")
        texts[name] = txt(run / "result.log")
        status = js(run / "runner.status.json")
        need(status["passed"] == (name != "red-parent-01"), "runner status mismatch")
        for r in rows:
            expected = 1 if r["log"].startswith("inject-") or (name == "red-parent-01" and r["log"] == "result.log") else 0
            need(r["exit_code"] == expected, "unexpected exit code " + name + "/" + r["log"])
        need("--assert" in commands[name]["verilator.log"]["command"], "RTL assertions were not enabled")
        need(commands[name]["result.log"]["command"][0].endswith("VVDotElasticFuTestTop" if name == "green-fu-01" else "VVDotElasticParentTestTop"), "wrong simulator")
        if name != "red-parent-01":
            for item in js(run / "artifacts.json"):
                raw = read(run / item["path"])
                need(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "artifact hash mismatch")
        result[name] = {"status": status, "commands": len(rows), "result_exit_code": commands[name]["result.log"]["exit_code"]}
    diff = {k: {"red": sources["red-parent-01"][k], "green": sources["green-parent-01"][k]}
            for k in sources["red-parent-01"] if sources["red-parent-01"][k] != sources["green-parent-01"].get(k)}
    need(set(sources["red-parent-01"]) == set(sources["green-parent-01"]), "source inventory changed")
    need(set(diff) == {"src/main/scala/xiangshan/backend/exu/ExeUnit.scala"}, "unexpected red/green source delta")
    need(all(sources["green-fu-01"][k] == v for k, v in sources["green-parent-01"].items() if k in sources["green-fu-01"]), "FU and parent shared source mismatch")
    frozen = js(root / "review-tests/frozen-tests.json")
    for name, sha in frozen["files"].items():
        need(hashlib.sha256(read(args.repo / "team/optimizations/o2/parent" / name)).hexdigest() == sha, "frozen test changed: " + name)
    for name in ("red-parent-01", "green-parent-01"):
        for f in ("parent_test.cpp", "check_negative.py", "test_negative.py"):
            need(sources[name]["team/optimizations/o2/parent/" + f] == frozen["files"][f], "run/test frozen SHA mismatch")
    # Independently verify all observation-negative transcripts and actual process RCs.
    fault_sets = {
        "green-fu-01": {k: k for k in ("identity", "wen", "high", "cancel")},
        "green-parent-01": {"identity": "identity", "rob": "identity", "high": "high",
            "metadata": "identity", "wen": "wen", "stall": "stability", "route": "route",
            "double": "route", "clock": "clock", "occupancy": "occupancy", "kill_p": "cancel",
            "kill_r": "cancel", "survivor": "cancel", "duplicate": "ghost", "missing": "response", "reset": "reset"}
    }
    for name, faults in fault_sets.items():
        prefix = "O2_FU" if name == "green-fu-01" else "O2_PARENT"
        need({p.stem[7:] for p in (root/name).glob("inject-*.log")} == set(faults), "negative inventory mismatch")
        result[name]["negative_checks"] = {}
        for fault, category in faults.items():
            neg = txt(root/name/("inject-" + fault + ".log"))
            need(neg.splitlines() == [prefix + "_INJECT " + fault, prefix + "_FAIL " + category], "negative transcript mismatch")
            need(commands[name]["inject-" + fault + ".log"]["exit_code"] == 1, "negative RC")
            check = txt(root/name/("check-" + fault + ".log")).strip()
            expected = (prefix + "_NEGATIVE_GATE_PASS " if prefix == "O2_FU" else prefix + "_NEGATIVE_CHECK_PASS ") + fault
            need(check == expected and commands[name]["check-" + fault + ".log"]["exit_code"] == 0, "negative gate result")
            result[name]["negative_checks"][fault] = {"injected_exit": 1, "checker_exit": 0, "category": category}
    fu_lines = texts["green-fu-01"].splitlines()
    need(len(fu_lines) == 1 and fu_lines[0].startswith("O2_FU_PASS "), "bad FU positive result")
    result["green-fu-01"]["summary"] = fields(fu_lines[0])
    need(result["green-fu-01"]["summary"]["vectors"] == 10022, "FU vector count")
    parent_text = texts["green-parent-01"]
    parent_lines = parent_text.splitlines()
    frames = [fields(line) for line in parent_lines if line.startswith("O2_PARENT_CYCLE ")]
    summary_lines = [line for line in parent_lines if line.startswith("O2_PARENT_PASS ")]
    need(len(summary_lines) == 1 and parent_lines[-1] == summary_lines[0], "parent final PASS shape")
    parent_summary = fields(summary_lines[0])
    need([r["cycle"] for r in frames] == list(range(len(frames))), "parent frame continuity")
    accepts = {r["accept_seq"]: r for r in frames if r["accept"]}
    need(len(accepts) == sum(r["accept"] for r in frames), "duplicate accept seq")
    def owner(row):
        seq = row["divseq"]
        need(seq in accepts and accepts[seq]["cycle"] < row["cycle"], "unknown/late DIV owner")
        return accepts[seq]
    windows = []
    idle_samples = Counter()
    relation_counts = Counter()
    rob_cases = set()
    reset_overlap = Counter()
    reset_active = Counter()
    relations = ((10, 10, False, False), (8, 10, False, False), (12, 10, False, True),
                 (47, 48, False, False), (48, 47, False, True), (95, 0, False, False), (0, 95, False, True))
    for index, row in enumerate(frames):
        if row["kill_div"] and row["case"].startswith(("DIV-cancel-", "DIV-ROB-")):
            old = owner(row)
            need(row["clocks"] & (1 << old["kind"]), "cancel cleaning edge missing")
            following = frames[index+1:index+4]
            need(len(following) == 3, "truncated cancellation window")
            for after in following:
                need(after["case"] == row["case"] and not any(after[k] for k in ("p", "r", "divseq", "offered", "accept", "reset", "te", "redirect")), "non-idle immediate cancellation sample")
                need(after["clocks"] == 0, "clock pulse in immediate cancellation sample")
                idle_samples[old["kind"]] += 1
            windows.append({"case": row["case"], "kind": old["kind"], "cancel_cycle": row["cycle"], "sample_cycles": [x["cycle"] for x in following], "pulses": 0})
        if row["case"].startswith("DIV-ROB-") and row["redirect"]:
            old = owner(row)
            parts = row["case"].split("-")
            kind, rel, phase = int(parts[2][1:]), int(parts[3][1:]), int(parts[4][1:])
            req_at, flush_at, self_flag, kill = relations[rel]
            req = 48 * old["rob_flag"] + old["rob"]
            flush = 48 * row["redirect_flag"] + row["redirect_rob"]
            distance = (req - flush) % 96
            computed_kill = bool(row["self"]) if distance == 0 else 0 < distance < 48
            need((old["kind"], req, flush, bool(row["self"]), bool(row["kill_div"])) == (kind, req_at, flush_at, self_flag, kill), "ROB directed relation mismatch")
            need(computed_kill == kill and phase in (0,1), "ROB independent age mismatch")
            need(row["case"] not in rob_cases, "duplicate ROB directed case")
            rob_cases.add(row["case"])
            relation_counts["killed" if kill else "survived"] += 1
        if row["case"] == "DIV-legacy-reset" and row["reset"] and row["divseq"]:
            old = owner(row)
            reset_active[old["kind"]] += 1
            need(row["te"] == 1 and row["reset_drop"] == 1 and row["kill_div"] == 0 and row["response"] == 0, "DIV reset priority")
            if row["redirect"]:
                need(row["self"] and row["redirect_flag"] == old["rob_flag"] and row["redirect_rob"] == old["rob"], "reset not overlapping matching cancellation")
                reset_overlap[old["kind"]] += 1
    need(len(windows) == 48 and idle_samples == {1:72,2:72}, "cancellation coverage")
    need(len(rob_cases) == 28 and relation_counts == {"killed":12,"survived":16}, "ROB directed coverage")
    need(reset_active == {1:6,2:6} and reset_overlap == {1:3,2:3}, "reset overlap coverage")
    true_idle = [r for r in frames if not any(r[k] for k in ("p","r","divseq","accept","reset","te"))]
    need(all(r["clocks"] == 0 for r in true_idle), "global true-idle pulse")
    recomputed = {"cycles":len(frames), "accepted":sum(r["accept"] for r in frames),
        "responses":sum(r["response"] for r in frames),
        "cancelled":sum(r["kill_p"]+r["kill_r"]+r["kill_div"] for r in frames),
        "reset_dropped":sum(r["reset_drop"] for r in frames)}
    need(all(parent_summary[k] == v for k,v in recomputed.items()), "parent aggregate mismatch")
    frozen_accepts = [r for r in frames if r["case"] == "frozen-vdot-II1" and r["accept"]]
    frozen_responses = [r for r in frames if r["case"] == "frozen-vdot-II1" and r["response"]]
    gaps = Counter(b["cycle"]-a["cycle"] for a,b in zip(frozen_accepts,frozen_accepts[1:]))
    latencies = Counter(r["cycle"]-accepts[r["response_seq"]]["cycle"] for r in frozen_responses)
    need(len(frozen_accepts) == len(frozen_responses) == 10022 and gaps == {1:10021} and latencies == {2:10022}, "frozen stream II/latency")
    result["green-parent-01"].update(summary=parent_summary, independently_recomputed=recomputed,
        per_fu_summaries=[fields(line) for line in parent_lines if line.startswith("O2_PARENT_FU ")],
        direct_cancel_windows=windows, immediate_cancel_samples=dict(idle_samples), idle_clock_pulses=0,
        div_rob_cases=sorted(rob_cases), div_rob_outcomes=dict(relation_counts),
        div_reset_active=dict(reset_active), div_reset_matching_cancel=dict(reset_overlap),
        all_true_idle_frames=len(true_idle),
        frozen_stream={"accepts":10022,"responses":10022,"accept_interval_histogram":dict(gaps),"response_latency_histogram":dict(latencies)})
    red_lines = texts["red-parent-01"].splitlines()
    need(red_lines[-2:] == ["O2_PARENT_FAIL clock", "case=DIV-cancel-92 tick=13330 idle FU retained clock after cancellation/completion"], "red exact expected failure")
    red_frames = [fields(line) for line in red_lines if line.startswith("O2_PARENT_CYCLE ")]
    need(red_frames == frames[:len(red_frames)], "red/green pre-failure prefix mismatch")
    need(len(red_frames) == 13330 and red_frames[-1]["cycle"] == 13329 and red_frames[-1]["kill_div"] == 1 and red_frames[-1]["clocks"] == 2, "red failed at wrong boundary")
    need(not any(line.startswith("O2_PARENT_PASS") for line in red_lines), "red has PASS")
    result["red-parent-01"].update(expected_failure=red_lines[-2:], last_logged_cycle=13329,
        failure_tick=13330, identical_green_prefix_frames=len(red_frames),
        note="Failing tick clocks are checked inside step before frame logging; no exact failing-tick clock bitmask is claimed.")
    # Re-run only the offline checker; subprocess is Python, never a hardware executable.
    command = ["python3","-B",str(args.repo/"team/optimizations/o2/parent/check_trace.py"),
               "--log",str(root/"green-parent-01/result.log"),"--output",str(args.output/"strict-offline-replay.json")]
    run = subprocess.run(command, text=True, capture_output=True)
    (args.output/"strict-offline-replay.stdout.log").write_text(run.stdout)
    (args.output/"strict-offline-replay.stderr.log").write_text(run.stderr)
    (args.output/"strict-offline-replay.command.json").write_text(json.dumps({"command":command,"exit_code":run.returncode},indent=2)+"\n")
    need(run.returncode == 0, "offline checker replay failed")
    output = {"status":"R3_DIV_GATE_ACTUAL_RESULTS_REVIEW_PASS", "source_delta":diff,
        "frozen_tests_unchanged":True, "runs":result,
        "scope":{"hardware_rerun_by_audit":False,"observation_negative_controls":"4 FU + 16 parent; not RTL fault mutation",
          "fullcore_tested":False,"NEMU_difftest_tested":False,"sqrt_dynamic_coverage":False,
          "DIV_all_TE0_reset_coverage":False,"PPA_measured":False,"power_measured":False,
          "application_performance_measured":False,
          "latency_claim":"2 cycles only for the 10,022-sample unblocked parent VDot stream; all-parent observed VDot first-visible latency is 2..25 under control/backpressure"},
        "input_files":used}
    (args.output/"audit.json").write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps({"status":output["status"],"parent_recomputed":recomputed,"cancel_windows":48,"cancel_samples":144,"cancel_pulses":0,"ROB_cases":28,"DIV_reset_overlap":dict(reset_overlap),"negative_modes":20,"frozen_tests_unchanged":True},indent=2))

if __name__ == "__main__":
    main()
