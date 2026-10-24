"""Explain real O2 cancellation windows after the complete strict trace audit.

This diagnostic reports allocation-bound PCs and survivor retirement. It does
not replace workload, DiffTest, build identity or the G3 campaign acceptance.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

import analyze


def diagnose(raw: bytes) -> dict:
    # Decode bytes directly: universal-newline conversion would change identity.
    text = raw.decode("utf-8")
    proof = analyze.analyze(text, require_complete=True)
    events, _ = analyze.extract_events_and_uart(text)
    allocations = defaultdict(list)
    commits = defaultdict(list)
    for cycle, _, kind, fields in sorted(events):
        if kind == "ENQUEUE":
            allocations[fields["rob"]].append(fields)
        elif kind == "COMMIT":
            commits[fields["rob"]].append(fields)
    cycles = {rob: [entry["cycle"] for entry in rows]
              for rob, rows in allocations.items()}
    commit_cycles = {rob: [entry["cycle"] for entry in rows]
                     for rob, rows in commits.items()}
    transactions = {}
    for transaction in proof["transactions"]:
        rob = transaction["rob"]
        index = bisect_right(cycles[rob], transaction["accept_cycle"]) - 1
        analyze.require(index >= 0, "accepted request lacks allocation")
        allocation = allocations[rob][index]
        following = allocations[rob][index + 1:index + 2]
        end = following[0]["cycle"] if following else float("inf")
        # The strict observer retires the old allocation before same-cycle
        # enqueue/reuse. Include that upper boundary, exclude the lower one.
        retirement_cycles = commit_cycles.get(rob, [])
        retired = commits[rob][bisect_right(retirement_cycles, allocation["cycle"]):
                               bisect_right(retirement_cycles, end)]
        analyze.require(len(retired) <= 1, "multiple retirements in one allocation")
        analyze.require(not retired or retired[0]["pc"] == allocation["pc"],
                        "retirement PC differs from allocation")
        transactions[transaction["seq"]] = dict(
            seq=transaction["seq"], rob=rob, pc=hex(allocation["pc"]),
            word=hex(allocation["word"]), pdest=transaction["pdest"],
            accept_cycle=transaction["accept_cycle"],
            outcome=transaction.get("outcome"),
            end_cycle=transaction["end_cycle"],
            expected_data=f"0x{transaction['expected_data']:032x}",
            writeback_stall_events=transaction["writeback_stall_events"],
            commit_cycle=retired[0]["cycle"] if retired else None,
            committed=bool(retired))
    windows = []
    counts = Counter()
    for cycle, _, kind, fields in sorted(events):
        if kind != "STATE" or not (fields["killp"] or fields["killr"]):
            continue
        classification = ("both_slots_cancelled" if fields["killp"] and fields["killr"]
                          else "partial_kill" if fields["occupancy"] == 2
                          else "one_slot_occupied")
        row = dict(cycle=cycle, classification=classification,
                   occupancy=fields["occupancy"], killp=fields["killp"],
                   killr=fields["killr"], outready=fields["outready"])
        for slot in ("p", "r"):
            row[slot] = (transactions[fields[slot + "seq"]].copy()
                         if fields[slot + "valid"] else None)
        if classification == "partial_kill":
            survivor = row["r" if fields["killp"] else "p"]
            victim = row["p" if fields["killp"] else "r"]
            row["survivor_committed"] = survivor["committed"]
            row["victim_committed"] = victim["committed"]
        counts[classification] += 1
        windows.append(row)
    analyze.require(counts["partial_kill"] == proof["counts"].get("PARTIAL_KILL", 0),
                    "diagnosis differs from strict coverage count")
    return dict(schema=1, status="O2_KILL_DIAGNOSIS_COMPLETE",
                raw_sha256=hashlib.sha256(raw).hexdigest(),
                analyzer_sha256=hashlib.sha256(Path(analyze.__file__).read_bytes()).hexdigest(),
                strict_trace_status=proof["status"], counts=proof["counts"],
                classifications=dict(counts), windows=windows,
                scope="Trace diagnosis only; architectural and campaign acceptance remain separate",
                new_emu_runs=0, performance_measured=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    if args.log.suffix == ".gz":
        raw = gzip.decompress(raw)
    result = diagnose(raw)
    # Exclusive creation also protects the source and any earlier evidence.
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(status=result["status"],
                          classifications=result["classifications"])))


if __name__ == "__main__":
    main()
