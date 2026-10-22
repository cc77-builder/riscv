#!/usr/bin/env python3
"""Read sealed O4 maps; count physical cells, not signal-name widths.

This is a baseline mapping audit. It neither builds nor measures an H1 candidate.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

O4_MANIFEST_SHA256 = "9f95c19b737b0428afca36686aabd1454d7fb44880040f2bf41109b71c39c0a1"
MAPS = [
    ("o1-fu-map-02", "CommonFuCostTop", "dut.resultReg"),
    ("o2-fu-map-01", "CommonFuCostTop", "dut.rPacket_res_data"),
    ("o1-parent-map-01", "CommonParentCostTop", "dut.Vdot.resultReg"),
    ("o2-parent-map-01", "CommonParentCostTop", "dut.Vdot.rPacket_res_data"),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Evidence:
    def __init__(self, root):
        self.root = Path(root)
        raw = (self.root / "manifest.json").read_bytes()
        require(sha(raw) == O4_MANIFEST_SHA256, "O4 manifest identity mismatch")
        entries = json.loads(raw)["entries"]
        self.entries = {v["path"]: v for v in entries}
        require(len(self.entries) == len(entries), "duplicate manifest path")
        self.used = {}

    def read(self, name):
        entry = self.entries[name]
        path = (self.root / "files" / entry["stored"]).resolve()
        require(path.is_relative_to((self.root / "files").resolve()), "path escape")
        stored = path.read_bytes()
        require(len(stored) == entry["stored_bytes"] and
                sha(stored) == entry["stored_sha256"], "stored hash mismatch: " + name)
        raw = gzip.decompress(stored) if entry["gzip"] else stored
        require(len(raw) == entry["bytes"] and sha(raw) == entry["sha256"],
                "payload hash mismatch: " + name)
        self.used[name] = entry
        return raw


def drivers(module):
    found = {}
    for name, cell in module["cells"].items():
        for pin, direction in cell["port_directions"].items():
            if direction != "output":
                continue
            for bit in cell["connections"][pin]:
                require(isinstance(bit, int), "constant driven by cell")
                require(bit not in found, "multiple drivers: " + str(bit))
                found[bit] = (name, pin)
    return found


def result_registers(module, net, index):
    rows = []
    for position, bit in enumerate(module["netnames"][net]["bits"]):
        row = {"bit": position, "q": bit}
        if isinstance(bit, str):
            row["kind"] = "constant"
        elif bit not in index:
            row["kind"] = "undriven"
        else:
            name, pin = index[bit]
            cell = module["cells"][name]
            row.update(cell=name, type=cell["type"], output_pin=pin)
            row["kind"] = "dff" if cell["type"] == "DFF_X1" and pin == "Q" else "other"
            if row["kind"] == "dff":
                row.update(d=cell["connections"]["D"][0],
                           clock=cell["connections"]["CK"][0])
        rows.append(row)
    return rows


def counts(rows):
    return {"positions": len(rows),
            "unique_q_bits": len({r["q"] for r in rows if isinstance(r["q"], int)}),
            "constant_positions": sum(r["kind"] == "constant" for r in rows),
            "dff_positions": sum(r["kind"] == "dff" for r in rows),
            "unique_dff_cells": len({r["cell"] for r in rows if r["kind"] == "dff"})}


def strip_buffers(bit, module, index):
    seen = set()
    while bit in index:
        name, _ = index[bit]
        cell = module["cells"][name]
        if not cell["type"].startswith("BUF_"):
            break
        require(bit not in seen, "buffer cycle")
        seen.add(bit)
        bit = cell["connections"]["A"][0]
    return bit


def hold_feedback(row, module, index):
    name, _ = index[row["d"]]
    cell = module["cells"][name]
    require(cell["type"] in ("AND2_X1", "NOR2_X1"), "unexpected high-bit D logic")
    inputs = [cell["connections"][p][0] for p in ("A1", "A2")]
    local = [name]
    if cell["type"] == "AND2_X1":
        require(row["q"] in inputs, "AND feedback does not use its own Q")
        control = inputs[1 - inputs.index(row["q"])]
        expression = "D = Q & hold"
        control_role = "hold"
    else:
        matches = []
        for pos, bit in enumerate(inputs):
            inv_name, _ = index.get(bit, (None, None))
            inv = module["cells"].get(inv_name, {})
            if inv.get("type") == "INV_X1" and inv["connections"]["A"] == [row["q"]]:
                matches.append((pos, inv_name))
        require(len(matches) == 1, "NOR feedback lacks unique own-Q inverter")
        pos, inv_name = matches[0]
        local.append(inv_name)
        control = inputs[1 - pos]
        expression = "D = ~(~Q | clear)"
        control_role = "clear"
    return {"expression": expression, "control_role": control_role,
            "control_bit": control,
            "control_without_buffers": strip_buffers(control, module, index),
            "local_cells": local}


def partition_feedback(module, local, register_cells):
    consumers = defaultdict(set)
    for name, cell in module["cells"].items():
        for pin, direction in cell["port_directions"].items():
            if direction == "input":
                for bit in cell["connections"][pin]:
                    consumers[bit].add(name)
    output_bits = {b for p in module["ports"].values() if p["direction"] == "output"
                   for b in p["bits"]}
    exclusive = set(local)
    # A cell feeding a shared cell is also shared. Iterate to a fixed point.
    while True:
        keep = {name for name in exclusive if all(
            consumers[bit] <= exclusive | register_cells and bit not in output_bits
            for pin, direction in module["cells"][name]["port_directions"].items()
            if direction == "output" for bit in module["cells"][name]["connections"][pin])}
        if keep == exclusive:
            return exclusive, set(local) - exclusive
        exclusive = keep


def analyze(module, net, area, inspect_feedback):
    index = drivers(module)
    rows = result_registers(module, net, index)
    require(len(rows) == 128, "expected 128-bit architecture result")
    require(counts(rows)["unique_dff_cells"] == 128, "baseline result FF count changed")
    high = rows[32:]
    local = set()
    shared = set()
    if inspect_feedback:
        for row in high:
            row["feedback"] = hold_feedback(row, module, index)
            local.update(row["feedback"]["local_cells"])
        local, shared = partition_feedback(module, local, {r["cell"] for r in high})
    cell_hist = Counter(c["type"] for c in module["cells"].values())
    local_hist = Counter(module["cells"][n]["type"] for n in local)
    total_area = sum(area[k] * v for k, v in cell_hist.items())
    ff_area = len({r["cell"] for r in high}) * area["DFF_X1"]
    logic_area = sum(area[k] * v for k, v in local_hist.items())
    return {"net": net, "result": counts(rows), "low32": counts(rows[:32]),
            "high96": counts(high), "sign_copies_31_19": counts(rows[19:32]),
            "total_dff_cells": sum(v for k, v in cell_hist.items() if k.startswith("DFF")),
            "total_cell_area": round(total_area, 6),
            "high96_dff_area": round(ff_area, 6),
            "high96_local_feedback_cells": dict(sorted(local_hist.items())),
            "shared_feedback_cells_excluded": [
                {"cell": n, "type": module["cells"][n]["type"]} for n in sorted(shared)],
            "high96_local_feedback_area": round(logic_area, 6),
            "high96_target_local_area": round(ff_area + logic_area, 6),
            "high96_target_share_percent": round(100 * (ff_area + logic_area) / total_area, 6),
            "feedback_inspected": inspect_feedback, "bits": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output already exists")
    evidence = Evidence(args.evidence)
    lib = evidence.read("library/NangateOpenCellLibrary_typical.lib").decode()
    areas = {k: float(v) for k, v in re.findall(
        r"cell\s*\(\s*(\w+)\s*\)\s*\{.*?\barea\s*:\s*([0-9.eE+-]+)", lib, re.S)}
    reports = {}
    for profile, top, net in MAPS:
        raw = evidence.read(profile + "/mapped.json")
        module = json.loads(raw)["modules"][top]
        summary = json.loads(evidence.read(profile + "/summary.json"))
        require(sha(raw) == summary["mapped_json_sha256"], "summary/map mismatch")
        report = analyze(module, net, areas, profile.startswith("o2"))
        require(abs(report["total_cell_area"] - summary["cell_area_sum"]) < 0.0001,
                "area sum mismatch")
        require(report["total_dff_cells"] == summary["cell_histogram"]["DFF_X1"],
                "total FF mismatch")
        report["mapped_sha256"] = sha(raw)
        report["generation"] = summary["generation"]
        reports[profile] = report
        del module
    result = {"status": "O2_R1_MAPPING_AUDIT_PASS", "scope": "baseline maps only",
              "decision": "GO_H1_LOCAL_EXPERIMENT", "candidate_implemented": False,
              "new_synthesis_runs": 0, "new_emu_runs": 0,
              "net_area_saving_measured": False,
              "manifest_sha256": O4_MANIFEST_SHA256,
              "auditor_sha256": sha(Path(__file__).read_bytes()),
              "python": sys.version, "command": sys.argv,
              "inputs": evidence.used, "profiles": reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(result["status"])
    for name, report in reports.items():
        print(name, "result_DFF", report["result"]["unique_dff_cells"],
              "high96_DFF", report["high96"]["unique_dff_cells"],
              "baseline_local_area", report["high96_target_local_area"])


if __name__ == "__main__":
    main()
