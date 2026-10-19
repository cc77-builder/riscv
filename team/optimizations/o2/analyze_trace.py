"""Offline O2 feasibility statistics from the sealed, accepted T14/O1 traces.

No EMU, build, golden-model change or counterfactual cycle-saving claim.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "team/optimizations/o1/evidence/20261018-performance-ab"
MANIFEST_SHA = "fceea6ba616cc513d76c019d60bab061fb89d5fef00a7b61619084625aee9354"
CAMPAIGN_SHA = "df5e3ba570c03f0e48634c9eeb1b0edfc0ee7bd2ee1c46ad4d1ad6cd54a0fefb"
VDOT = 1 << 35


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def histogram(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


class Archive:
    """Check both archive bytes and decompressed original bytes on every read."""
    def __init__(self, root):
        self.root = root
        manifest_bytes = (root / "archive-manifest.json").read_bytes()
        require(digest(manifest_bytes) == MANIFEST_SHA, "sealed manifest changed")
        self.manifest = json.loads(manifest_bytes)
        raw_map = (root / "file-map.json").read_bytes()
        require(digest(raw_map) == self.manifest["files"]["file-map.json"], "file map changed")
        self.mapping = json.loads(raw_map)
        self.reads = {}

    def read(self, suffix):
        found = [e for e in self.mapping if e["source"].endswith(suffix)]
        require(len(found) == 1, "missing or ambiguous archive source: " + suffix)
        entry = found[0]
        path = self.root / entry["archive"]
        require(path.resolve().is_relative_to(self.root.resolve()), "archive path escaped")
        raw = path.read_bytes()
        require(digest(raw) == entry["archive_sha256"] == self.manifest["files"][entry["archive"]],
                "stored bytes changed: " + suffix)
        require(len(raw) == entry["archive_bytes"], "stored size changed")
        require(entry["storage"] in ("gzip", "identity"), "unsupported storage")
        data = gzip.decompress(raw) if entry["storage"] == "gzip" else raw
        require(digest(data) == entry["source_sha256"] and len(data) == entry["source_bytes"],
                "decompressed bytes changed: " + suffix)
        self.reads[entry["archive"]] = {
            "original_sha256": digest(data), "stored_sha256": digest(raw),
            "original_bytes": len(data), "stored_bytes": len(raw),
        }
        return data

    def json(self, suffix):
        return json.loads(self.read(suffix))


def commit_cycles(events):
    """Bind commit to accepted seq through allocation generations, not ROB alone."""
    groups = defaultdict(list)
    for cycle, order, kind, fields in events:
        if kind != "SCHEMA":
            groups[cycle].append((kind, fields))
    live, result = {}, {}
    for cycle, group in sorted(groups.items()):
        for kind, f in group:
            if kind == "COMMIT":
                require(f["rob"] in live and live[f["rob"]] is not None, "unbound commit")
                seq = live[f["rob"]]
                require(seq not in result, "duplicate commit sequence")
                result[seq] = cycle
        for kind, f in group:
            if kind == "ENQUEUE":
                live[f["rob"]] = None
        for kind, f in group:
            if kind == "ACCEPT":
                require(f["rob"] in live and live[f["rob"]] is None, "unbound/repeated accept")
                live[f["rob"]] = f["seq"]
    return result


def wait_allocation_generations(events):
    """Bind each vdot WAIT to the current ROB allocation, retaining its later fate."""
    groups = defaultdict(list)
    for cycle, order, kind, fields in events:
        if kind != "SCHEMA":
            groups[cycle].append((kind, fields))
    live, history, waits = {}, [], {}
    for cycle, group in sorted(groups.items()):
        for kind, f in group:
            if kind == "COMMIT":
                require(f["rob"] in live, "unbound generation commit")
                live[f["rob"]]["commit_cycle"] = cycle
        for kind, f in group:
            if kind == "REDIRECT":
                origin_flag, origin_index = map(int, f["rob"].split(":"))
                for entry in live.values():
                    if "commit_cycle" in entry or "cancel_cycle" in entry:
                        continue
                    flag, index = map(int, entry["rob"].split(":"))
                    after = bool(flag ^ origin_flag) ^ (index > origin_index)
                    if after or (entry["rob"] == f["rob"] and f["self"]):
                        entry["cancel_cycle"] = cycle
        for kind, f in group:
            if kind == "ENQUEUE":
                previous = live.get(f["rob"])
                require(previous is None or "commit_cycle" in previous or "cancel_cycle" in previous,
                        "overlapping allocation generations")
                entry = dict(generation=len(history), rob=f["rob"], enqueue_cycle=cycle)
                live[f["rob"]] = entry
                history.append(entry)
        for kind, f in group:
            if kind == "ACCEPT":
                require(f["rob"] in live and "seq" not in live[f["rob"]], "unbound generation accept")
                live[f["rob"]].update(seq=f["seq"], accept_cycle=cycle)
            elif kind == "VFEX4_WAIT" and f["fu"] == VDOT:
                require(cycle not in waits, "multiple vdot waits in same cycle")
                require(f["rob"] in live, "unbound waiting allocation")
                waits[cycle] = live[f["rob"]]
    return waits


def wait_fate(entry, start, stop):
    if "commit_cycle" in entry:
        return ("accepted_and_committed_in_window"
                if start <= entry.get("accept_cycle", -1) < stop and start <= entry["commit_cycle"] < stop
                else "committed_outside_or_accepted_outside_window")
    if "cancel_cycle" in entry:
        return "accepted_then_cancelled" if "seq" in entry else "cancelled_before_accept"
    return "unresolved"


def window_stats(sample, events, transactions, commits, wait_generations=None):
    """Half-open [first rdcycle sample, second rdcycle sample) global interval."""
    start, stop = sample["sample_ticks"][1:3]
    require(stop > start and stop - start == sample["cycles"], "CSR/global clock mismatch")
    require(sample["counter_values"][2] - sample["counter_values"][1] == stop - start,
            "CSR value delta mismatch")
    local = [(kind, f) for cycle, _, kind, f in events if start <= cycle < stop]
    by_kind = defaultdict(list)
    for kind, fields in local:
        by_kind[kind].append(fields)
    accepted = [t for t in transactions if start <= t["accept_cycle"] < stop]
    require([t["seq"] for t in accepted] == [f["seq"] for f in by_kind["ACCEPT"]],
            "transaction/event mismatch")
    waits = by_kind["VFEX4_WAIT"]
    require(len({f["cycle"] for f in waits}) == len(waits), "duplicate wait cycle")
    custom_waits = [f for f in waits if f["fu"] == VDOT]
    gaps = [b["accept_cycle"] - a["accept_cycle"] for a, b in zip(accepted, accepted[1:])]
    require(all(gap > 0 for gap in gaps), "non-increasing accepted cycles")
    crossing = {
        "accepted_before_start_completed_inside": sum(t["accept_cycle"] < start <= t["end_cycle"] < stop for t in transactions),
        "accepted_inside_completed_at_or_after_stop": sum(t["end_cycle"] >= stop for t in accepted),
        "accepted_inside_commit_outside_or_absent": sum(not(start <= commits.get(t["seq"], -1) < stop) for t in accepted),
        "commit_inside_accepted_outside": sum(start <= c < stop and s not in {t["seq"] for t in accepted} for s, c in commits.items()),
        "events_exactly_at_start": sum(c == start for c, _, k, f in events if k != "SCHEMA"),
        "events_exactly_at_stop": sum(c == stop for c, _, k, f in events if k != "SCHEMA"),
    }
    counts = {k: len(by_kind[k]) for k in (
        "ACCEPT", "RESPONSE", "STALL", "KILL", "HANDOFF",
        "VFEX4_ACCEPT", "VFEX4_WAIT", "ENQUEUE", "COMMIT", "REDIRECT", "VFEX4_REDIRECT")}
    wait_cycles = {f["cycle"] for f in custom_waits}
    return {
        **{k: sample[k] for k in ("mode", "scenario", "dataset", "repeat", "image", "seq", "dots", "cycles")},
        "global_start_inclusive": start, "global_stop_exclusive": stop,
        "counts": counts,
        "vdot_wait_by_busy": histogram(f["busy"] for f in custom_waits),
        "vdot_wait_by_allocation_fate": dict(sorted(Counter(
            wait_fate(wait_generations[f["cycle"]], start, stop)
            for f in custom_waits).items())) if wait_generations is not None else {},
        "vdot_wait_by_fate_busy": dict(sorted(Counter(
            wait_fate(wait_generations[f["cycle"]], start, stop) + "/busy=" + str(f["busy"])
            for f in custom_waits).items())) if wait_generations is not None else {},
        "all_wait_by_fu_busy": dict(sorted(Counter(f"{hex(f['fu'])}/busy={f['busy']}" for f in waits).items())),
        "accept_gap_histogram": histogram(gaps),
        "response_latency_histogram": histogram(t["elapsed_cycles"] for t in accepted if t["outcome"] == "response"),
        "first_accept_offset": accepted[0]["accept_cycle"] - start if accepted else None,
        "last_response_to_stop": stop - max((t["end_cycle"] for t in accepted), default=stop),
        "first_to_last_accept_span": accepted[-1]["accept_cycle"] - accepted[0]["accept_cycle"] if accepted else 0,
        "wait_overlap_response_cycles": len(wait_cycles & {f["cycle"] for f in by_kind["RESPONSE"]}),
        "wait_overlap_stall_cycles": len(wait_cycles & {f["cycle"] for f in by_kind["STALL"]}),
        "boundary_audit": crossing,
        "accepted_and_committed_in_window": sum(start <= commits.get(t["seq"], -1) < stop for t in accepted),
    }


def summarize(windows):
    output = []
    for scenario in ("single", "chain", "batch", "stream"):
        for mode in ("t14", "o1"):
            rows = [w for w in windows if w["scenario"] == scenario and w["mode"] == mode]
            require(len(rows) == 12 and {w["dataset"] for w in rows} == {0, 1, 2},
                    "missing formal samples")
            require(all({w["repeat"] for w in rows if w["dataset"] == d} == {2, 3, 4, 5} for d in range(3)),
                    "missing formal repeats")
            merged = {}
            for name in ("counts", "vdot_wait_by_busy", "accept_gap_histogram",
                         "response_latency_histogram", "boundary_audit", "all_wait_by_fu_busy",
                         "vdot_wait_by_allocation_fate", "vdot_wait_by_fate_busy"):
                total = Counter()
                for row in rows:
                    total.update(row[name])
                merged[name] = dict(sorted(total.items()))
            output.append(dict(
                scenario=scenario, mode=mode, windows=len(rows),
                mean_cycles=statistics.mean(w["cycles"] for w in rows),
                mean_first_accept_offset=statistics.mean(w["first_accept_offset"] for w in rows),
                mean_last_response_to_stop=statistics.mean(w["last_response_to_stop"] for w in rows),
                mean_first_to_last_accept_span=statistics.mean(w["first_to_last_accept_span"] for w in rows),
                wait_overlap_response_cycles=sum(w["wait_overlap_response_cycles"] for w in rows),
                wait_overlap_stall_cycles=sum(w["wait_overlap_stall_cycles"] for w in rows),
                **merged))
    return output


def run(archive_root):
    archive = Archive(archive_root)
    base = "/o1-performance-20261018/"
    raw = archive.read(base + "campaign-01/result.json")
    require(digest(raw) == CAMPAIGN_SHA, "campaign identity changed")
    campaign = json.loads(raw)
    require(campaign["status"] == "T14_O1_PAIRED_PERFORMANCE_PASS", "unaccepted campaign")
    prior = archive.json(base + "results-01/verification.json")
    require(prior["status"] == "OFFLINE_T14_O1_PAIRED_RECHECK_PASS"
            and prior["campaign_result_sha256"] == CAMPAIGN_SHA, "missing accepted offline check")
    frozen_observer = archive.read(
        base + "campaign-01/checker-snapshots/team/optimizations/o1/fullcore/analyze.py")
    observer = {"__name__": "frozen_o1_observer"}
    exec(compile(frozen_observer, "<sealed-o1-observer>", "exec"), observer)
    windows, jobs = [], []
    for record in campaign["runs"]:
        if record["stage"] != "performance" or record["replay"] != 0:
            continue
        suffix = base + f"campaign-01/{record['mode']}/performance/{record['image']}-r0/"
        require(archive.json(suffix + "result.json") == record, "campaign/run mismatch")
        require(record["status"] == "PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS" and record["exit_code"] == 0,
                "unaccepted job")
        stdout, stderr = [archive.read(suffix + name) for name in ("stdout.log", "stderr.log")]
        require(digest(stdout) == record["raw_sha256"]["stdout.log"]
                and digest(stderr) == record["raw_sha256"]["stderr.log"], "raw hashes disagree")
        text = (stderr + stdout).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        observation = archive.json(suffix + "observation.json")
        require(observer["analyze"](text) == observation, "observer replay changed")
        require(observation["schema"]["clock"] == "global"
                and observation["schema"]["handoff"] == (record["mode"] == "o1"), "wrong mode/clock")
        checked = archive.json(suffix + "window-result.json")
        require(checked["status"] == "PASS", "unaccepted windows")
        for a, b in zip(checked["samples"], record["samples"]):
            require(all(a[k] == b[k] for k in a), "sample binding mismatch")
        require(len(checked["samples"]) == len(record["samples"]), "sample count mismatch")
        events, _ = observer["extract_events_and_uart"](text)
        commits = commit_cycles(events)
        wait_generations = wait_allocation_generations(events)
        selected = [s for s in record["samples"] if s["phase"] == "measured" and s["method"] == "vdot"]
        require(len(selected) == 4, "wrong selected sample count")
        for sample in selected:
            row = window_stats(sample, events, observation["transactions"], commits, wait_generations)
            require(row["counts"]["ACCEPT"] == row["counts"]["RESPONSE"] == row["counts"]["COMMIT"] == sample["dots"],
                    "formal body instruction binding differs")
            require(row["accepted_and_committed_in_window"] == sample["dots"], "speculative/body identity differs")
            require(not any(row["boundary_audit"].values()), "boundary event needs explicit review")
            windows.append(row)
        jobs.append(dict(mode=record["mode"], image=record["image"], raw_sha256=record["raw_sha256"],
                         observer_input_sha256=observation["input_sha256"], formal_custom_windows=4))
    require(len(jobs) == 24 and len(windows) == 96, "incomplete inventory")
    return dict(
        status="O2_OFFLINE_TRACE_FEASIBILITY_PASS", new_emu_executed=False,
        archive_manifest_sha256=MANIFEST_SHA, campaign_result_sha256=CAMPAIGN_SHA,
        analyzer_sha256=digest(Path(__file__).read_bytes()), frozen_observer_sha256=digest(frozen_observer),
        selected_jobs=24, selected_windows=96,
        selection="performance, replay=0, phase=measured, method=vdot; 2 modes x 4 scenarios x 3 datasets x 4 repeats",
        boundary="[sample_ticks[1], sample_ticks[2]); global ungated clock, matches CSR delta",
        limitations=[
            "WAIT means VFEX4 input valid and not ready; busy is the existing parent busy bit.",
            "busy=1 does not uniquely attribute a root cause; busy=0 does not prove upstream starvation.",
            "Wait events overlap other pipeline activity; do not sum waits across levels or equate them to removable cycles.",
            "Accepted-gap observations are schedule-dependent, not a prediction of O2 performance.",
            "No new O2 RTL, EMU, timing, resource, physical-frequency, upstream-valid or application performance evidence.",
            "Existing sealed window/DiffTest acceptance is reused, and frozen observer is replayed; no new simulation.",
        ],
        summary=summarize(windows), windows=windows, jobs=jobs,
        input_files=archive.reads)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output already exists; keep earlier evidence")
    result = run(args.archive)
    args.output.mkdir(parents=True)
    (args.output / "trace-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "command.json").write_text(json.dumps(dict(
        argv=sys.argv, python=sys.version, new_emu_executed=False,
        analyzer_sha256=result["analyzer_sha256"]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "selected_jobs", "selected_windows", "new_emu_executed")}))
