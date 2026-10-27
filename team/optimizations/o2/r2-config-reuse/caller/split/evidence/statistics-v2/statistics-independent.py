"""Independent split-v2 arithmetic from exported UART and the fixed plan.

Only Python's standard library is used. No project selector/checker is imported,
and the supplied selection is read only after the independent result exists.
This checks exported statistics, not original hardware trace provenance.
"""
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "recovery-statistics-input.json"
OUTPUT = HERE / "statistics-independent.json"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def precise(value):
    value = Fraction(value)
    with localcontext() as ctx:
        ctx.prec = 60
        decimal = format(Decimal(value.numerator) / Decimal(value.denominator), ".12f")
    return {"fraction": str(value), "decimal": decimal}


def benefit(before, after):
    return Fraction(before - after, before)


def compare(actual, expected, path, errors):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            errors.append(path + ": different object keys/types")
            return
        for key in expected:
            compare(actual[key], expected[key], path + "." + key, errors)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            errors.append(path + ": different list length/type")
            return
        for index, (a, b) in enumerate(zip(actual, expected)):
            compare(a, b, f"{path}[{index}]", errors)
    elif isinstance(expected, float):
        if not isinstance(actual, (int, float)) or isinstance(actual, bool) or not math.isclose(
                actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            errors.append(f"{path}: supplied={actual!r}, independently derived={expected!r}")
    elif type(actual) is not type(expected) or actual != expected:
        errors.append(f"{path}: supplied={actual!r}, independently derived={expected!r}")


def main():
    source_bytes = SOURCE.read_bytes()
    data = json.loads(source_bytes)
    uart, plan, rows = data["uart"], data["plan"], data["rows"]
    lines = uart.splitlines()
    sw = [line for line in lines if line.startswith("SW")]
    require(len(sw) == 252, "exactly 252 SW records")
    parsed = []
    for index, line in enumerate(sw):
        match = re.fullmatch(r"SW (\d+) (\d+) (\d+)", line)
        require(match is not None, "exact SW syntax")
        seq, cycles, instructions = map(int, match.groups())
        require(seq == index and cycles > 0 and instructions > 0, "SW order/value")
        parsed.append((seq, cycles, instructions))
    require([line for line in lines if line.startswith("SPLIT_")] == [
        "SPLIT_BEGIN contract=r2-s3-split-input-8x32-v2 windows=252",
        "SPLIT_FUNCTIONAL calls=84 controls=6",
        "SPLIT_END windows=252 failures=0"], "complete exported UART markers")
    require(len(rows) == 13 and [r["id"] for r in rows] == list(range(13)), "row identities")
    for index, row in enumerate(rows):
        algorithm = index % 6
        mode = "packed" if index < 6 else "split"
        require(row["algorithm"] == algorithm and row["mode"] == mode
                and row["method"] == ("vdot" if algorithm == 0 else "rvv")
                and row["anchor"] is (index == 12), "method/algorithm/anchor mapping")
    require(rows[12]["leaf"] == rows[6]["leaf"], "same anchor vdot implementation")

    # Reconstruct the schedule independently; do not merely trust its labels.
    schedule = []
    for dataset in range(3):
        for repeat in range(6):
            middle = list(range(12))
            if repeat % 2:
                middle.reverse()
            for position, index in enumerate([12] + middle + [12]):
                schedule.append({"index": index, "dataset": dataset, "repeat": repeat,
                    "phase": ("first", "warmup")[repeat] if repeat < 2 else "measured",
                    "order_group": repeat % 2,
                    "anchor_position": "start" if position == 0 else "end" if position == 13 else None})
    require(plan == schedule, "exported plan differs from fixed 3x6x14 schedule")
    formal = []
    for (_, cycles, instructions), step in zip(parsed, schedule):
        if step["repeat"] >= 2:
            formal.append(dict(step, cycles=cycles, instructions=instructions))
    require(len(formal) == 168, "144 ordinary plus 24 formal anchors")

    methods, exact_methods = [], []
    for index in range(12):
        records = [s for s in formal if s["index"] == index]
        require(len(records) == 12 and {(s["dataset"], s["repeat"]) for s in records}
                == {(d, r) for d in range(3) for r in (2, 3, 4, 5)}, "formal method coverage")
        total = sum(s["cycles"] for s in records)
        by_dataset = [sum(s["cycles"] for s in records if s["dataset"] == d) for d in range(3)]
        by_order = [sum(s["cycles"] for s in records if s["order_group"] == o) for o in range(2)]
        cells = [sum(s["cycles"] for s in records if (s["dataset"], s["order_group"]) == (d, o))
                 for d in range(3) for o in range(2)]
        row = rows[index]
        methods.append({"id": index, "mode": row["mode"], "algorithm": row["algorithm"],
            "leaf": row["leaf"], "total": total, "mean": float(Fraction(total, 12)),
            "by_dataset": by_dataset, "by_order": by_order, "by_dataset_order": cells,
            "cycles": [s["cycles"] for s in records],
            "instructions": sorted({s["instructions"] for s in records})})
        exact_methods.append(dict(methods[-1], mean=precise(Fraction(total, 12))))

    pairs, exact_pairs = [], []
    for algorithm in range(6):
        packed, split = methods[algorithm], methods[algorithm + 6]
        p, s = packed["total"], split["total"]
        per_dataset = []
        for dataset, (old, new) in enumerate(zip(packed["by_dataset"], split["by_dataset"])):
            per_dataset.append({"dataset": dataset, "packed_total": old, "split_total": new,
                "reduction_percent": precise(100 * benefit(old, new)),
                "within_one_percent_regression": 100 * new <= 101 * old})
        passed = 100 * s <= 95 * p and all(x["within_one_percent_regression"] for x in per_dataset)
        pairs.append({"algorithm": algorithm, "reduction": float(benefit(p, s)),
            "by_dataset": [float(benefit(a, b)) for a, b in zip(packed["by_dataset"], split["by_dataset"])],
            "passed": passed})
        exact_pairs.append({"algorithm": algorithm, "packed_leaf": packed["leaf"], "split_leaf": split["leaf"],
            "packed_total": p, "split_total": s, "packed_mean": precise(Fraction(p, 12)),
            "split_mean": precise(Fraction(s, 12)), "reduction_percent": precise(100 * benefit(p, s)),
            "at_least_five_percent": 100 * s <= 95 * p, "by_dataset": per_dataset, "passed": passed})

    anchors, exact_anchors = [], []
    for dataset in range(3):
        groups, detailed_groups = [], []
        for order in (0, 1):
            for position in ("start", "end"):
                selected = [s for s in formal if s["index"] == 12 and s["dataset"] == dataset
                            and s["order_group"] == order and s["anchor_position"] == position]
                require(len(selected) == 2, "two samples per anchor cell")
                group = {"order": order, "position": position, "total": sum(s["cycles"] for s in selected)}
                groups.append(group)
                detailed_groups.append(dict(group, cycles=[s["cycles"] for s in selected]))
        low, high = min(g["total"] for g in groups), max(g["total"] for g in groups)
        variation = Fraction(high - low, low)
        passed = 100 * high <= 101 * low
        anchors.append({"dataset": dataset, "groups": groups, "variation": float(variation), "passed": passed})
        exact_anchors.append({"dataset": dataset, "groups": detailed_groups, "min_total": low, "max_total": high,
            "variation_percent": precise(100 * variation), "passed": passed})

    # Only the five split RVV methods may compete for the RVV reference.
    winner = min((m for m in methods if m["mode"] == "split" and m["algorithm"] != 0),
                 key=lambda m: (m["total"], m["algorithm"]))
    vdot = methods[6]
    cell_results = []
    for cell, (v, r) in enumerate(zip(vdot["by_dataset_order"], winner["by_dataset_order"])):
        cell_results.append({"dataset": cell // 2, "order_group": cell % 2,
            "vdot_total": v, "rvv_total": r, "reduction_percent": precise(100 * benefit(r, v)),
            "at_least_half_percent": 1000 * v <= 995 * r})
    interface_ok = all(p["passed"] for p in exact_pairs)
    anchors_ok = all(a["passed"] for a in exact_anchors)
    vdot_ok = all(c["at_least_half_percent"] for c in cell_results)
    decision = ("STOP_INTERFACE" if not interface_ok else "HOLD_CONTEXT_VARIATION" if not anchors_ok
                else "VDOT_PREFERRED_IN_THIS_PLAN" if vdot_ok else "KEEP_RVV_EXPLICIT")
    derived_selection = {"interface_qualified": interface_ok, "pairs": pairs, "methods": methods,
        "anchors": anchors, "decision": decision, "observed_lowest_rvv": winner["leaf"],
        "vdot_reduction_by_dataset": [float(benefit(r, v)) for v, r in zip(vdot["by_dataset"], winner["by_dataset"])],
        "vdot_reduction_by_order": [float(benefit(r, v)) for v, r in zip(vdot["by_order"], winner["by_order"])],
        "selected_method": None if not interface_ok or not anchors_ok else vdot["leaf"] if vdot_ok else winner["leaf"],
        "vdot_reduction_by_dataset_order": [float(benefit(r, v)) for v, r in zip(vdot["by_dataset_order"], winner["by_dataset_order"])],
        "stable_default_changed": False}

    # First use of the supplied selection: compare every field with our result.
    errors = []
    compare(data["selection"], derived_selection, "selection", errors)
    embedded_uart_sha = hashlib.sha256(uart.encode("utf-8")).hexdigest()
    claimed_uart_sha = data["source_sha256"]["uart"]
    packed_sum = sum(m["total"] for m in methods[:6])
    split_sum = sum(m["total"] for m in methods[6:])
    report = {"status": "INDEPENDENT_STATISTICS_MATCH" if not errors else "INDEPENDENT_STATISTICS_MISMATCH",
        "source_file": str(SOURCE), "source_file_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "embedded_uart_sha256": embedded_uart_sha, "claimed_original_uart_sha256": claimed_uart_sha,
        "uart_bytes_match_claim": embedded_uart_sha == claimed_uart_sha,
        "export_representation": data.get("representation"),
        "claimed_source_sha256": data["source_sha256"], "receipt": data["receipt"],
        "scope": "Independent arithmetic from 252 UART SW records; not a fresh audit of original RETIRE/CSR/O2 traces",
        "record_counts": {"all": 252, "formal_methods": 144, "formal_anchors": 24, "excluded_first_warmup": 84},
        "methods": exact_methods, "pairs": exact_pairs, "anchors": exact_anchors,
        "interface_qualified": interface_ok, "anchors_qualified": anchors_ok,
        "lowest_split_rvv": {"id": winner["id"], "leaf": winner["leaf"], "total": winner["total"],
            "mean": precise(Fraction(winner["total"], 12))},
        "vdot_vs_lowest_split_rvv": {"vdot_total": vdot["total"], "rvv_total": winner["total"],
            "vdot_mean": precise(Fraction(vdot["total"], 12)), "rvv_mean": precise(Fraction(winner["total"], 12)),
            "overall_reduction_percent": precise(100 * benefit(winner["total"], vdot["total"])),
            "six_cells": cell_results, "all_cells_qualified": vdot_ok},
        "equal_weight_all_six_pair_aggregate": {"packed_total": packed_sum, "split_total": split_sum,
            "samples_per_side": 72, "packed_mean": precise(Fraction(packed_sum, 72)),
            "split_mean": precise(Fraction(split_sum, 72)),
            "reduction_percent": precise(100 * benefit(packed_sum, split_sum)),
            "scope": "Diagnostic equally weighted tested methods; not an application workload or algorithm ranking"},
        "decision": decision, "selected_method": derived_selection["selected_method"],
        "selection_comparison_float_tolerance": {"relative": 1e-12, "absolute": 1e-12},
        "selection_mismatches": errors}
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "uart_bytes_match_claim", "interface_qualified",
          "anchors_qualified", "lowest_split_rvv", "vdot_vs_lowest_split_rvv", "decision", "selection_mismatches")},
          indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
