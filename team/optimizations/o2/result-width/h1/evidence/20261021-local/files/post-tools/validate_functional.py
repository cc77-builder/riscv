#!/usr/bin/env python3
"""Read-only H1 FU/parent evidence validation; never invokes hardware tools."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

BASE_COMMIT = "9b6cf074951dbd51e1670c5fbc7111a97c362b3f"
RTL = "src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"
FU_FAULTS = dict(identity="identity", wen="wen", high="high", cancel="cancel")
PARENT_FAULTS = dict(identity="identity", rob="identity", high="high",
    metadata="identity", wen="wen", stall="stability", route="route",
    double="route", clock="clock", occupancy="occupancy", kill_p="cancel",
    kill_r="cancel", survivor="cancel", duplicate="ghost", missing="response", reset="reset")
HISTORICAL_DIFFS = {"build.sc", "src/main/scala/xiangshan/backend/exu/ExeUnit.scala",
    RTL, "src/main/scala/xiangshan/backend/fu/wrapper/VDotO2.scala",
    "src/main/scala/xiangshan/backend/rob/Rob.scala", "team/optimizations/o2/run_rtl.py"}

def require(ok, why):
    if not ok:
        raise ValueError(why)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def fields(line):
    out = {}
    for token in line.split()[1:]:
        require("=" in token, "non-field token")
        key, value = token.split("=", 1)
        require(key not in out, "duplicate field: " + key)
        out[key] = value
    return out

def negative_text(stage, fault, category, inject, checked):
    prefix = "O2_" + stage.upper()
    require(inject.splitlines() == [prefix + "_INJECT " + fault,
        prefix + "_FAIL " + category], "incorrect negative detection " + fault)
    suffix = "_NEGATIVE_GATE_PASS " if stage == "fu" else "_NEGATIVE_CHECK_PASS "
    require(checked.splitlines() == [prefix + suffix + fault], "negative checker marker " + fault)

def validate_cycles(rows):
    """Independently replay exact P/R/DIV identities and prefix conservation."""
    slots = [0, 0, 0]
    live = {}
    totals = [0, 0, 0, 0]
    frozen_accept, frozen_response = {}, {}
    overlap = 0
    for cycle, x in enumerate(rows):
        n = lambda k: int(x[k])
        require(n("schema") == 1 and n("cycle") == cycle, "cycle sequence/schema")
        before = [n("pseq"), n("rseq"), n("divseq")]
        require(before == slots, "slot identity continuity")
        p, r, div = before
        require(n("p") == bool(p) and n("r") == bool(r), "valid/sequence mismatch")
        require(n("occupancy") == bool(p) + bool(r), "pre-edge occupancy")
        require(not div or not (p or r), "simultaneous DIV and VDot")
        accept, response, move = n("accept"), n("response"), n("p_to_r")
        kp, kr, kd, reset = (n(k) for k in ("kill_p", "kill_r", "kill_div", "reset"))
        require(all(v in (0, 1) for v in (accept, response, move, kp, kr, kd, reset)), "nonboolean event")
        def retire(seq, terminal):
            require(seq != 0 and seq in live, "missing/duplicate terminal")
            del live[seq]
            totals[terminal] += 1
        if reset:
            require(not (accept or response or move or kp or kr or kd), "reset priority")
            require(n("reset_drop") == sum(bool(v) for v in before), "reset drop")
            for seq in before:
                if seq:
                    retire(seq, 3)
            p = r = div = 0
        else:
            require(n("reset_drop") == 0, "unexpected reset drop")
            if kp:
                retire(p, 2)
                p = 0
            if kr:
                retire(r, 2)
                r = 0
            if kd:
                retire(div, 2)
                div = 0
            if response:
                seq = r or div
                require(seq == n("response_seq") and seq == min(live), "response identity/order")
                retire(seq, 1)
                if r:
                    r = 0
                else:
                    div = 0
            else:
                require(n("response_seq") == 0, "spurious response sequence")
            if move:
                require(p and not r and not div, "invalid P to R move")
                r, p = p, 0
            if accept:
                seq, kind = n("accept_seq"), n("kind")
                require(n("offered") == 1 and n("ready") == 1, "accepted without handshake")
                require(not n("redirect") and seq == totals[0] + 1 and seq not in live, "accept identity")
                require(kind in (0, 1, 2), "accepted kind")
                if kind == 0:
                    require(not p and not div, "VDot accepted into busy slot")
                    p = seq
                else:
                    require(not (p or r or div), "DIV accepted before drain")
                    div = seq
                live[seq] = kind
                totals[0] += 1
            else:
                require(n("accept_seq") == 0, "spurious accept sequence")
        slots = [p, r, div]
        require(n("next_occupancy") == bool(p) + bool(r), "post-edge occupancy")
        require(len(live) == sum(bool(v) for v in slots) == n("inflight"), "live identities")
        observed = [n(k) for k in ("accepted_total", "responses_total", "cancels_total", "resets_total")]
        require(observed == totals and totals[0] == sum(totals[1:]) + len(live), "prefix conservation")
        overlap += bool(accept and response)
        if x["case"] == "frozen-vdot-II1":
            if accept:
                frozen_accept[n("accept_seq")] = cycle
            if response:
                frozen_response[n("response_seq")] = cycle
    require(not live and not any(slots), "undrained final state")
    require(len(frozen_accept) == len(frozen_response) == 10022, "frozen vector inventory")
    require(frozen_accept.keys() == frozen_response.keys(), "frozen identity inventory")
    require({frozen_response[k] - v for k, v in frozen_accept.items()} == {2}, "frozen latency")
    ticks = list(frozen_accept.values())
    require({b-a for a, b in zip(ticks, ticks[1:])} == {1}, "frozen II")
    return dict(cycles=len(rows), accepted=totals[0], responses=totals[1],
        cancelled=totals[2], reset_dropped=totals[3], overlaps=overlap,
        frozen_vectors=10022, ii1_intervals=10021, latency_cycles=2)

def validate(repo, work, baseline):
    inputs = {}
    def read(path):
        path = path.resolve()
        data = path.read_bytes()
        inputs[str(path)] = dict(sha256=sha(data), bytes=len(data))
        return data
    def text(path):
        return read(path).decode("utf-8")
    def obj(path):
        return json.loads(text(path))
    def child(root, relative):
        p = (root / relative).resolve()
        require(p.is_relative_to(root.resolve()), "manifest path escape")
        return p
    stages = {}
    production_patch = text(work / "h1-production.patch").strip()
    require(production_patch and production_patch.count("diff --git ") == 1
        and "a/" + RTL + " b/" + RTL in production_patch, "production patch boundary")
    for stage, new, old, faults, source_count, generated_count in [
            ("fu", "fu-01", "g1-attempt-01", FU_FAULTS, 429, 4),
            ("parent", "parent-01", "g2-attempt-02", PARENT_FAULTS, 431, 57)]:
        p, b = work / new, baseline / old
        status = obj(p / "runner.status.json")
        require(status["passed"] is True and status["stage"] == stage, "runner not passed")
        require(text(p / "source-commit.log").strip() == BASE_COMMIT, "wrong source base")
        require(text(p / "source-after.status") == "SOURCE_AND_DEPENDENCIES_UNCHANGED\n", "source changed")
        require(production_patch in text(p / "working-tree.patch"), "missing H1 patch")
        sources, old_sources = obj(p / "source.json"), obj(b / "source.json")
        require(len(sources) == source_count and sources.keys() == old_sources.keys(), "source inventory")
        for name, digest in sources.items():
            require(sha(read(child(repo, name))) == digest, "source digest mismatch: " + name)
        require(text(p / "source.sha256") == "".join(f"{v}  {k}\n" for k, v in sources.items()), "source.sha256 mismatch")
        differences = {k for k, v in sources.items() if old_sources[k] != v}
        require(differences == HISTORICAL_DIFFS, "unexpected baseline source changes")
        deps = obj(p / "dependencies.json")
        require(len(deps) == 126 and read(p / "dependencies.json") == read(b / "dependencies.json"), "dependency baseline mismatch")
        require(all(x["pin"] == x["head"] and x["status"] == "" for x in deps), "unpinned dependency")
        require(len({x["path"] for x in deps}) == 126, "duplicate dependency")
        for manifest, count in [("artifacts.json", 2), ("generated-files.json", generated_count)]:
            records = obj(p / manifest)
            require(len(records) == count and len({x["path"] for x in records}) == count, "artifact inventory")
            for x in records:
                data = read(child(p, x["path"]))
                require(sha(data) == x["sha256"] and len(data) == x["bytes"], "artifact digest mismatch")
        vectors = read(p / "vectors.tsv")
        require(vectors == read(b / "vectors.tsv") and len(vectors.splitlines()) == 10022, "vector baseline mismatch")
        result = text(p / "result.log")
        require(result == text(b / "result.log"), "baseline result log differs")
        require(not any(s in result for s in ("_FAIL", "_INJECT", "_FAULT_ESCAPED")), "positive log fault marker")
        markers = [s for s in result.splitlines() if s.startswith("O2_" + stage.upper() + "_PASS ")]
        require(len(markers) == 1, "positive terminal count")
        summary = {k: int(v) for k, v in fields(markers[0]).items()}
        require(summary["accepted"] == summary["responses"] + summary["cancelled"] + summary["reset_dropped"], "terminal conservation")
        commands = obj(p / "commands.json")
        regular = ["git-version.log", "java-version.log", "mill-version.log", "verilator-version.log",
            "cxx-version.log", "clang-version.log", "make-version.log", "firtool-version.log",
            "source-commit.log", "source-status.log", "working-tree.patch", "vectors.log",
            "negative-gate-tests.log", "elaboration.log", "verilator.log", "result.log"]
        if stage == "parent":
            regular.append("positive-replay.log")
        expected_logs = regular + [name for f in faults for name in ("inject-" + f + ".log", "check-" + f + ".log")]
        require([x["log"] for x in commands] == expected_logs, "command inventory/order")
        by_log = {x["log"]: x for x in commands}
        for command in commands:
            expected_rc = 1 if command["log"].startswith("inject-") else 0
            require(command["exit_code"] == expected_rc, "command exit code: " + command["log"])
            read(p / command["log"])
        suffix = "Fu" if stage == "fu" else "Parent"
        executable = str(p / "obj" / ("VVDotElastic" + suffix + "TestTop"))
        positive_args = [executable, str(p / "vectors.tsv")]
        require(by_log["result.log"]["command"] == positive_args, "positive executable/vector binding")
        for fault, category in faults.items():
            require(by_log["inject-" + fault + ".log"]["command"] == positive_args + [fault], "negative executable binding")
            args = by_log["check-" + fault + ".log"]["command"]
            require(args[-6:] == ["--fault", fault, "--return-code", "1", "--log", str(p / ("inject-" + fault + ".log"))], "negative checker binding")
            negative_text(stage, fault, category, text(p / ("inject-" + fault + ".log")), text(p / ("check-" + fault + ".log")))
        rtl = text(p / "rtl/VDotElastic.sv")
        require(re.findall(r"reg\s+\[(\d+):0\]\s+rPacket_res_data;", rtl) == ["31"], "result register width")
        row = dict(source_count=len(sources), dependencies=len(deps), commands=len(commands),
            negative_cases=len(faults), summary=summary, baseline_log_identical=True,
            historical_source_differences=sorted(differences), result_log_sha256=sha(result.encode()))
        if stage == "fu":
            require(summary["vectors"] == 10022 and summary["ii1_intervals"] == 10021
                and summary["latency2_probes"] == 1, "FU frozen stream coverage")
        else:
            groups = [s for s in result.splitlines() if s.startswith("O2_PARENT_GROUP_PASS ")]
            require(len(groups) == summary["groups"] == 12, "parent group inventory")
            rows = [fields(s) for s in result.splitlines() if s.startswith("O2_PARENT_CYCLE ")]
            replay = validate_cycles(rows)
            for k in ("cycles", "accepted", "responses", "cancelled", "reset_dropped", "overlaps"):
                require(replay[k] == summary[k], "parent summary mismatch: " + k)
            require(summary["parent_tested"] == 1 and summary["fullcore_tested"] == summary["performance_measured"] == 0, "scope changed")
            per_fu = [fields(s) for s in result.splitlines() if s.startswith("O2_PARENT_FU ")]
            require([int(x["kind"]) for x in per_fu] == [0, 1, 2], "per-FU inventory")
            for x in per_fu:
                require(int(x["accepted"]) == sum(int(x[k]) for k in ("responded", "killed", "reset_dropped")), "per-FU conservation")
            row.update(independent_replay=replay, groups=groups, per_fu=per_fu)
        stages[stage] = row
    require(read(work / "source" / RTL) == read(repo / RTL), "candidate snapshot mismatch")
    require(sha(read(work / "VDotElastic.baseline.scala")) == "20981203b19e57658c35ee76d134a1aaee918ce4c317d0f139df97c75460491a", "saved baseline RTL mismatch")
    require(read(work / "fu-01/working-tree.patch") == read(work / "parent-01/working-tree.patch"), "stage patch identity differs")
    return dict(status="H1_FUNCTIONAL_VALIDATION_PASS", base_commit=BASE_COMMIT, stages=stages,
        input_files=inputs, limitations=[
            "Old G1/G2 logs are historical behavioral references, not a same-source A/B.",
            "Full 128-bit payload comparison is the unchanged real RTL C++ test result; this offline replay checks events and identities.",
            "Negative cases alter C++ observations, not RTL hardware faults.",
            "No full-core execution, performance measurement, PPA validation, or human ACK is established here."])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("repo", "work", "baseline", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    receipt = out.with_suffix(".command.json")
    require(not out.exists() and not receipt.exists(), "refuse to overwrite validation evidence")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    code = 0
    try:
        result = validate(args.repo.resolve(), args.work.resolve(), args.baseline.resolve())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        code = 1
        result = dict(status="H1_FUNCTIONAL_VALIDATION_FAIL", error=str(error))
    result["checker_sha256"] = sha(Path(__file__).read_bytes())
    result["hardware_tools_executed"] = False
    result["human_ack"] = False
    result["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    receipt.write_text(json.dumps(dict(command=[sys.executable, *sys.argv], started_utc=started,
        finished_utc=result["finished_utc"], exit_code=code, output=str(out),
        output_sha256=sha(out.read_bytes()), checker_sha256=result["checker_sha256"]), indent=2) + "\n")
    print(result["status"])
    raise SystemExit(code)

if __name__ == "__main__":
    main()
