"""Read-only ordering diagnostic for the already audited 8x32/d0 probe.

No new qualification: hashes bind this extraction to the audited raw records.
Enqueue/accept/response/commit intervals are observations, not stall attribution.
"""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def extract(repo, campaign, archive, output):
    assert not output.exists()
    manifest = read(archive / "archive-manifest.json")
    assert manifest["contract"] == "r2-s1-firstdot-c-abi-v1"
    sealed = {r["original"]: r["raw_sha256"] for r in manifest["files"]}
    observer_path = repo / "team/optimizations/o2/fullcore/analyze.py"
    spec = importlib.util.spec_from_file_location("firstdot_order_observer", observer_path)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    windows, sources = [], {}
    for variant, label in (("firstdot", "recovery-firstdot-8x32"),
                           ("s1", "formal-performance-s1-d0-s03")):
        directory = campaign / "runs" / label
        for name in ("result.json", "observation.json", "stdout.log", "stderr.log"):
            path = directory / name
            actual = sha(path)
            assert sealed[str(path)] == actual
            sources[str(path)] = actual
        record = read(directory / "result.json")
        observation = read(directory / "observation.json")
        assert record["variant"] == variant and record["dataset"] == 0 and record["shard"] == 3
        tool_hashes = [v for k, v in record["files"].items()
                       if k.endswith("/team/optimizations/o2/fullcore/analyze.py")]
        assert tool_hashes == [sha(observer_path)]
        text = (directory / "stderr.log").read_text() + (directory / "stdout.log").read_text()
        assert hashlib.sha256(text.encode()).hexdigest() == observation["input_sha256"]
        events, _ = observer.extract_events_and_uart(text)
        grouped = defaultdict(list)
        for cycle, _, kind, values in events:
            if kind in ("ENQUEUE", "ACCEPT", "COMMIT", "VFEX4_WAIT"):
                grouped[cycle].append((kind, values))
        live, accepts, waits = {}, {}, []
        for cycle, group in sorted(grouped.items()):
            # A retiring ROB allocation precedes same-cycle reallocation.
            for kind, values in group:
                if kind == "COMMIT":
                    entry = live[values["rob"]]
                    assert entry["pc"] == values["pc"] and "commit_cycle" not in entry
                    entry["commit_cycle"] = cycle
            for kind, values in group:
                if kind == "ENQUEUE":
                    live[values["rob"]] = dict(values, enqueue_cycle=cycle)
            for kind, values in group:
                if kind == "ACCEPT":
                    assert values["seq"] not in accepts
                    accepts[values["seq"]] = live[values["rob"]]
                elif kind == "VFEX4_WAIT":
                    waits.append(values)
        for sample in record["samples"]:
            if (sample["software"], sample["method"], sample["phase"]) != ("reuse", "vdot", "measured"):
                continue
            start, stop = sample["sample_ticks"][1:3]
            selected = sorted((t for t in observation["transactions"] if start <= t["accept_cycle"] < stop),
                              key=lambda t: t["accept_cycle"])
            assert len(selected) == sample["dots"] == 32
            rows = []
            for ordinal, transaction in enumerate(selected):
                entry = accepts[transaction["seq"]]
                assert entry["rob"] == transaction["rob"] and transaction["outcome"] == "response"
                assert entry["enqueue_cycle"] <= transaction["accept_cycle"] < transaction["end_cycle"] < entry["commit_cycle"]
                rows.append(dict(accept_ordinal=ordinal, pc=hex(entry["pc"]), word=hex(entry["word"]),
                    vd=(entry["word"] >> 7) & 31, rob=entry["rob"],
                    enqueue_after_start=entry["enqueue_cycle"] - start,
                    accept_after_start=transaction["accept_cycle"] - start,
                    response_after_start=transaction["end_cycle"] - start,
                    commit_after_start=entry["commit_cycle"] - start,
                    enqueue_to_accept=transaction["accept_cycle"] - entry["enqueue_cycle"],
                    response_to_commit=entry["commit_cycle"] - transaction["end_cycle"],
                    accept_gap=None if not rows else transaction["accept_cycle"] - start - rows[-1]["accept_after_start"]))
            window_waits = [w for w in waits if start <= w["cycle"] < stop]
            windows.append(dict(variant=variant, repeat=sample["repeat"], cycles=sample["cycles"],
                sample_ticks=sample["sample_ticks"], vfex4_wait_events=window_waits, transactions=rows,
                enqueue_to_accept_histogram=observer.histogram(r["enqueue_to_accept"] for r in rows),
                response_to_commit_histogram=observer.histogram(r["response_to_commit"] for r in rows)))
    assert len(windows) == 8
    summary = []
    for variant in ("s1", "firstdot"):
        selected = [w for w in windows if w["variant"] == variant]
        first = [w["transactions"][0] for w in selected]
        summary.append(dict(variant=variant, samples=len(selected),
            cycles_mean=statistics.mean(w["cycles"] for w in selected),
            first_accepted_enqueue_after_start_mean=statistics.mean(r["enqueue_after_start"] for r in first),
            first_accepted_enqueue_to_accept_mean=statistics.mean(r["enqueue_to_accept"] for r in first),
            first_accept_after_start_mean=statistics.mean(r["accept_after_start"] for r in first),
            vfex4_wait_events=sum(len(w["vfex4_wait_events"]) for w in selected),
            unique_ordered_pc_sequences=len({tuple(r["pc"] for r in w["transactions"]) for w in selected})))
    result = dict(status="FIRSTDOT_PROBE_ORDERED_DIAGNOSTIC", qualification_recomputed=False,
        new_emu_runs=0, source_script_sha256=sha(Path(__file__)), observer_sha256=sha(observer_path),
        archive_manifest_sha256=sha(archive / "archive-manifest.json"), raw_sources=sources,
        summary=summary, windows=windows,
        limits="Already audited raw trace; enqueue/accept/response/commit boundaries do not identify load, scheduling, vector-config or retirement stall causes.")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(status=result["status"], summary=summary, output=str(output)), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "campaign", "archive", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    extract(args.repo.resolve(), args.campaign.resolve(), args.archive.resolve(), args.output.resolve())
