"""Compare accepted T13 baseline and T14 candidate with exact image pairing."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import median


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def paired_rows(base, candidate):
    """Keep all phases/replays/methods; never select on the measured speedup."""
    def keyed(rows):
        result = {}
        for row in rows:
            key = (row["image"], row["replay"], row["seq"])
            require(key not in result, "duplicate sample key")
            result[key] = row
        return result
    a, b = keyed(base), keyed(candidate)
    require(a.keys() == b.keys(), "missing or extra candidate sample")
    rows = []
    contract_keys = ("image", "replay", "seq", "suite", "method", "scenario",
                     "n", "dataset", "repeat", "phase", "dots", "instructions")
    for key in sorted(a):
        old, new = a[key], b[key]
        for field in contract_keys:
            require(old[field] == new[field], "software/retirement contract changed: " + field)
        if old["suite"] != "performance":
            continue
        require(old["cycles"] > 0 and new["cycles"] > 0, "invalid cycle delta")
        rows.append({**{field: old[field] for field in contract_keys},
                     "baseline_cycles": old["cycles"], "candidate_cycles": new["cycles"],
                     "cycles_saved": old["cycles"] - new["cycles"],
                     "hardware_speedup": old["cycles"] / new["cycles"],
                     "cycle_reduction": 1 - new["cycles"] / old["cycles"]})
    return rows


def compare(base, candidate, output):
    output.mkdir(parents=True, exist_ok=False)
    baseresult, newresult = load(base / "result.json"), load(candidate / "result.json")
    for result in (baseresult, newresult):
        require(result["status"] == "T13_FAIR_CYCLE_COMPARISON_PASS", "input not accepted")
        require(result["functional_calls"] == 108 and result["performance_windows"] == 1404,
                "incomplete campaign")
        require(result["fresh_replays"] == 3 and result["replay_identical"], "missing deterministic replay")
    oldruns = {row["name"]: row for row in baseresult["receipt"]}
    newruns = {row["name"]: row for row in newresult["receipt"]}
    require(oldruns.keys() == newruns.keys() and len(oldruns) == 126, "different run inventory")
    fu_totals = {variant: dict(accepted=0, responses=0, killed=0, stalls=0, latency_histogram={}, acceptance_interval_min=None)
                 for variant in ("baseline", "candidate")}
    for name in oldruns:
        old, new = load(base / (name + ".json")), load(candidate / (name + ".json"))
        for field in ("image_sha256", "elf_sha256", "manifest_sha256"):
            require(old[field] == new[field], "A/B image mismatch: " + name + " " + field)
        for variant, row, latency in (("baseline", old, 3), ("candidate", new, 2)):
            fu = row["fu"]
            require(fu["response_latency_min"] >= latency, "response before the FU contract")
            require(fu["accepted"] == fu["responses"] + fu["killed"], "FU conservation")
            totals = fu_totals[variant]
            for field in ("accepted", "responses", "killed", "stalls"):
                totals[field] += fu[field]
            interval = fu["acceptance_interval_min"]
            if interval is not None:
                require(interval > 0, "nonpositive acceptance interval")
                current = totals["acceptance_interval_min"]
                totals["acceptance_interval_min"] = interval if current is None else min(current, interval)
            for delay, count in fu["response_latency_histogram"].items():
                require(int(delay) >= latency, "early response in histogram")
                totals["latency_histogram"][delay] = totals["latency_histogram"].get(delay, 0) + count
    rows = paired_rows(load(base / "samples.json"), load(candidate / "samples.json"))
    require(len(rows) == 1404, "wrong A/B sample count")
    grouped = defaultdict(list)
    for row in rows:
        if row["replay"] == 0 and row["phase"] == "measured":
            grouped[(row["scenario"], row["n"], row["dataset"], row["method"])].append(row)
    summary = []
    for key, group in sorted(grouped.items()):
        require(len(group) == 4, "formal sample count")
        record = dict(zip(("scenario", "n", "dataset", "method"), key))
        record["dots"] = group[0]["dots"]
        for field in ("baseline_cycles", "candidate_cycles", "hardware_speedup", "cycles_saved"):
            values = [row[field] for row in group]
            record.update({field + "_min": min(values), field + "_median": median(values),
                           field + "_max": max(values)})
        summary.append(record)
    require(len(summary) == 78, "39 configurations x 2 methods required")
    for name, data in (("paired-windows", rows), ("summary", summary)):
        save(output / (name + ".json"), data)
        with (output / (name + ".csv")).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    vdot = [row for row in summary if row["method"] == "vdot"]
    rvv = [row for row in summary if row["method"] == "rvv"]
    result = dict(status="T14_IDENTICAL_IMAGE_ABLATION_PASS", compared_runs=126,
                  compared_performance_windows=1404, configurations=39,
                  baseline_fu_minimum_contract=3, candidate_fu_minimum_contract=2, fu_observations=fu_totals,
                  vdot_median_speedup_range=[min(row["hardware_speedup_median"] for row in vdot),
                                            max(row["hardware_speedup_median"] for row in vdot)],
                  rvv_control_median_cycles_saved_range=[min(row["cycles_saved_median"] for row in rvv),
                                                         max(row["cycles_saved_median"] for row in rvv)],
                  inputs={"baseline": {"path": str(base), "result_sha256": hashlib.sha256((base / "result.json").read_bytes()).hexdigest()},
                          "candidate": {"path": str(candidate), "result_sha256": hashlib.sha256((candidate / "result.json").read_bytes()).hexdigest()}},
                  caveat="Cycles only; no Fmax/PPA inference. Negative savings and first samples remain in paired-windows. Identical replays are not independent statistical samples.",
                  summary=summary)
    save(output / "result.json", result)
    print(json.dumps({key: value for key, value in result.items() if key != "summary"}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "candidate", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    compare(args.baseline, args.candidate, args.output)
