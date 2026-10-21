#!/usr/bin/env python3
"""Read-only B0/H1 mapping and STA audit. Never launches hardware tools."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
O4 = ROOT / "team/optimizations/o4"
sys.path.insert(0, str(O4))
_spec = importlib.util.spec_from_file_location("h1_original_o4_audit", O4 / "audit.py")
AUDIT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AUDIT)
BASELINE = {
    "fu": ("o2-fu-01", "o2-fu-map-01", "o2-fu-sta-02"),
    "parent": ("o2-parent-01", "o2-parent-map-01", "o2-parent-sta-01"),
}
PROFILES = {"nominal": (1, 5), "period050": (.5, 5),
            "period200": (2, 5), "load001": (1, 1), "load020": (1, 20)}
FLAGS = {"VDOT_T14_FUSED_INPUT": "1", "VDOT_O1_HANDOFF": "0",
         "VDOT_O2_ELASTIC": "1", **{key: "0" for key in
         ("VDOT_T12_TRACE", "VDOT_T13_TRACE", "VDOT_O1_TRACE", "VDOT_O2_TRACE")}}
SEALED_MANIFEST_SHA = "9f95c19b737b0428afca36686aabd1454d7fb44880040f2bf41109b71c39c0a1"
GROUPS = ("products", "stage_state", "p_control", "p_perf", "r_control", "r_perf")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def directory_hashes(directory):
    return {str(p.relative_to(directory)): {"sha256": sha(p), "bytes": p.stat().st_size}
            for p in sorted(directory.rglob("*")) if p.is_file()}


def check_sealed_inventory(inventory, entries):
    sealed = {e["path"]: e for e in entries}
    for directory, files in inventory.items():
        expected = {name[len(directory) + 1:]: entry for name, entry in sealed.items()
                    if name.startswith(directory + "/")}
        require(set(files) == set(expected), "baseline evidence file set changed")
        for relative, identity in files.items():
            entry = expected[relative]
            require(identity["sha256"] == entry["sha256"] and identity["bytes"] == entry["bytes"],
                    "baseline evidence differs from sealed manifest: " + directory + "/" + relative)


def module_body(text, module):
    # Preserve string literals while dropping source-location and header comments.
    without_comments = re.sub(
        r'"(?:\\.|[^"\\])*"|/\*.*?\*/|//[^\n]*',
        lambda m: m.group(0) if m.group(0).startswith('"') else " ", text, flags=re.S)
    start = re.search(r"\bmodule\s+" + re.escape(module) + r"\b", without_comments)
    require(start is not None, "missing arithmetic module " + module)
    end = re.search(r"\bendmodule\b", without_comments[start.start():])
    require(end is not None, "missing arithmetic endmodule " + module)
    body = without_comments[start.start():start.start() + end.end()]
    return re.sub(r"\s+", " ", body).strip()


def data_storage(design, boundary, width):
    prefix = "dut." if boundary == "fu" else "dut.Vdot."
    name = prefix + "rPacket_res_data"
    require(name in design["netnames"], "missing result register net " + name)
    bits = design["netnames"][name]["bits"]
    require(len(bits) == width and all(isinstance(b, int) for b in bits)
            and len(set(bits)) == width, "result bits are not unique dynamic bits")
    drivers = {}
    for cell_name, cell in design["cells"].items():
        for pin, direction in cell["port_directions"].items():
            if direction == "output":
                for bit in cell["connections"][pin]:
                    if isinstance(bit, int):
                        require(bit not in drivers, "multiple cell drivers")
                        drivers[bit] = (cell_name, pin)
    names = []
    for bit in bits:
        require(bit in drivers, "undriven result bit")
        cell_name, pin = drivers[bit]
        require(pin == "Q" and design["cells"][cell_name]["type"].startswith("DFF"),
                "result bit is not driven by DFF Q")
        names.append(cell_name)
    require(len(set(names)) == width, "result register cells are aliased")
    output_name = prefix + "io_out_bits_res_data"
    require(output_name in design["netnames"], "missing child output net")
    output = design["netnames"][output_name]["bits"]
    require(len(output) == 128 and output[:32] == bits[:32],
            "child result does not preserve low 32 bits")
    if width == 32:
        require(output[32:] == ["0"] * 96, "child high 96 result bits are not constant zero")
        if boundary == "fu":
            require(design["ports"]["io_out_bits_res_data"]["bits"] == output,
                    "FU public output differs from child output")
    # The parent output contains DIV results. Record it without asserting constant high bits.
    public = {n: {"width": len(p["bits"]),
                  "high96_constant_zero": p["bits"][32:] == ["0"] * 96}
              for n, p in design["ports"].items()
              if p["direction"] == "output" and len(p["bits"]) == 128 and "data" in n}
    return {"net": name, "stored_bits": width, "unique_dff_cells": len(set(names)),
            "dff_cell_names": names, "child_output_high96_zero": output[32:] == ["0"] * 96,
            "public_data_ports": public}


def mapped_metadata(design, boundary):
    prefix = "dut." if boundary == "fu" else "dut.Vdot."
    patterns = {"products": "pProducts_", "stage_state": r"[pr]Valid$",
                "p_control": "pCtrl_", "p_perf": "pPerf_",
                "r_control": "rPacket_ctrl_", "r_perf": "rPacket_perfDebugInfo_"}
    q = {b: name for name, c in design["cells"].items() if c["type"].startswith("DFF")
         for b in c["connections"]["Q"]}
    groups = {}
    for group, pattern in patterns.items():
        bits = {b for n, net in design["netnames"].items()
                if n.startswith(prefix) and re.match(pattern, n[len(prefix):])
                for b in net["bits"] if isinstance(b, int)}
        groups[group] = len({q[b] for b in bits if b in q})
    return groups


def check_groups(baseline, candidate):
    require(set(baseline["groups"]) == set(candidate["groups"]),
            "structure register group names changed")
    require(baseline["groups"]["result"] == 128 and candidate["groups"]["result"] == 32,
            "structure result width is not 128 to 32")
    require(all(baseline["groups"][g] == candidate["groups"][g] for g in GROUPS),
            "control/perf/products/state register count changed: requires explicit review")
    require(candidate["total_bits"] == baseline["total_bits"] - 96,
            "unexpected structural register change beyond 96 result bits")


def timing_changes(baseline, candidate, boundary):
    expected_paths = {"r2r", "i2r", "r2o", "i2o", "ready"}
    if boundary == "parent":
        expected_paths |= {"vdot_r2r", "vdot_i2r", "vdot_r2o", "gate_enable"}
    by_version = []
    for timing in (baseline, candidate):
        profiles = {p["profile"]: p for p in timing["profiles"]}
        require(len(timing["profiles"]) == len(PROFILES) and set(profiles) == set(PROFILES),
                "missing/duplicate STA profile")
        for name, p in profiles.items():
            require((p["period_ns"], p["load_ff"]) == PROFILES[name], "STA profile constraint mismatch")
            require(set(p["paths"]) == expected_paths, "missing/extra required path category")
            require(all(v["exists"] for v in p["paths"].values()), "missing STA path")
        by_version.append(profiles)
    changes = {}
    for name in PROFILES:
        a, b = (v[name] for v in by_version)
        changes[name] = {"period_ns": a["period_ns"], "load_ff": a["load_ff"], "paths": {}}
        for key in sorted(expected_paths):
            old, new = a["paths"][key], b["paths"][key]
            changes[name]["paths"][key] = {
                "baseline": old, "candidate": new,
                "arrival_delta_ns": new["arrival_ns"] - old["arrival_ns"],
                "slack_delta_ns": new["slack_ns"] - old["slack_ns"],
                "arrival_reduction_percent": (old["arrival_ns"] - new["arrival_ns"]) /
                    old["arrival_ns"] * 100 if old["arrival_ns"] else None}
    return changes


def audit_one(work, names, boundary, width, tools_work):
    generation, mapping, timed = (work / n for n in names)
    lib = tools_work / "library/NangateOpenCellLibrary_typical.lib"
    s, design = AUDIT.mapping_audit(mapping, lib)
    require(s["mode"] == "o2" and s["boundary"] == boundary and s["exit_code"] == 0,
            "wrong mapping mode/boundary/exit")
    g = read(generation / "result.json")
    require(s["generation_sha256"] == sha(generation / "result.json")
            and Path(s["generation"]).resolve() == generation.resolve(),
            "generation binding mismatch")
    require(g["mode"] == "o2" and g["boundary"] == boundary and g["exit_code"] == 0
            and g["flags"] == FLAGS, "wrong generation mode/flags/exit")
    for relative, identity in g["rtl"].items():
        require(sha(generation / relative) == identity["sha256"], "generated RTL changed")
    require(sha(mapping / "map.ys") == s["map_script_sha256"], "mapping script changed")
    map_text = (mapping / "map.ys").read_text()
    top = "CommonFuCostTop" if boundary == "fu" else "CommonParentCostTop"
    expected = ["proc", "opt", f"synth -top {top} -flatten -noabc",
                f"dfflibmap -liberty {lib}",
                f"abc -exe {tools_work / 'tools/root/usr/bin/berkeley-abc'} -liberty {lib} -D 1000 -constr {mapping / 'abc.constr'}",
                "clean", "check -assert", f"stat -liberty {lib}"]
    require(all(map_text.splitlines().count(line) == 1 for line in expected),
            "mapping options differ from original contract")
    require((mapping / "abc.constr").read_text() == "set_driving_cell BUF_X1\nset_load 5.0\n",
            "ABC constraints differ")
    t = AUDIT.timing_audit(timed, mapping, design)
    require(t["mode"] == "o2" and t["boundary"] == boundary, "wrong timing boundary/mode")
    histogram = Counter(c["type"] for c in design["cells"].values())
    icg = histogram["CLKGATETST_X1"]
    require(icg == (3 if boundary == "parent" else 0), "clockgate count changed")
    if boundary == "parent":
        replacement = s["clockgate_mapping"]
        require(len(replacement) == 1 and replacement[0]["cell"] == "CLKGATETST_X1",
                "clockgate replacement differs")
        require(sha(mapping / "ClockGate.original.sv") == replacement[0]["sha256"]
                and sha(mapping / "ClockGate.map.v") == replacement[0]["replacement_sha256"],
                "clockgate source/map identity differs")
        require((mapping / "ClockGate.map.v").read_text() ==
                "module ClockGate(input TE, E, CK, output Q);\n"
                "  CLKGATETST_X1 impl(.CK(CK), .E(E), .SE(TE), .GCK(Q));\nendmodule\n",
                "clockgate pin mapping differs")
    storage = data_storage(design, boundary, width)
    metadata = mapped_metadata(design, boundary)
    del design
    structure = AUDIT.register_groups(read(mapping / "structure.json"), "o2")
    arithmetic = {}
    for module in ("VDotProducts", "VDotReduce"):
        p = generation / "rtl" / (module + ".sv")
        body = module_body(p.read_text(), module)
        arithmetic[module] = {"raw_sha256": sha(p),
                              "body_sha256": hashlib.sha256(body.encode()).hexdigest()}
    return {"area": s["cell_area_sum"], "dff_count": sum(v for k, v in histogram.items() if k.startswith("DFF")),
            "icg_count": icg, "cell_count": s["cell_count"], "cell_histogram": dict(histogram),
            "ports": s["ports"], "storage": storage, "mapped_metadata": metadata,
            "structure_register_groups": structure, "timing": t, "arithmetic": arithmetic,
            "input_hashes": {name: directory_hashes(work / name) for name in names}}


def compare(candidate_work, baseline_work):
    manifest = O4 / "evidence/20261020-cost/manifest.json"
    require(sha(manifest) == SEALED_MANIFEST_SHA, "original O4 sealed manifest changed")
    sealed_entries = read(manifest)["entries"]
    pins = read(candidate_work / "candidate-inputs.json")
    state = read(candidate_work / "campaign-state.json")
    require(state["status"] == "passed" and state["source_and_r0_lock_unchanged"],
            "candidate campaign has not completed with fixed source")
    require(sha(ROOT / "team/optimizations/o2/repro/baseline-lock.json") == pins["r0_lock_sha256"],
            "R0 baseline lock changed")
    for name, digest in pins["source_sha256"].items():
        require(sha(ROOT / name) == digest, "candidate source changed: " + name)
    for name in ("src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala",
                 "src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala"):
        require(sha(candidate_work / "source" / name) == pins["source_sha256"][name],
                "candidate saved source differs: " + name)
    tool_record = baseline_work / "tools/executable-identities.json"
    tool_entry = next(e for e in sealed_entries if e["path"] == "tools/executable-identities.json")
    require(sha(tool_record) == tool_entry["sha256"], "original tool identity record changed")
    tool_identities = read(tool_record)
    require(set(pins["tools"]) == set(tool_identities), "tool set changed")
    shared_libraries = {}
    for name, digest in pins["tools"].items():
        require(digest == tool_identities[name]["sha256"], "candidate/B0 tool identity differs: " + name)
        require(sha(baseline_work / "tools/root/usr/bin" / name) == digest, "tool changed: " + name)
        for path, shared_digest in tool_identities[name]["shared_library_sha256"].items():
            require(path not in shared_libraries or shared_libraries[path] == shared_digest,
                    "inconsistent original shared library identity")
            shared_libraries[path] = shared_digest
    for path, digest in shared_libraries.items():
        require(sha(Path(path)) == digest, "tool shared library changed: " + path)
    require(sha(baseline_work / "library/NangateOpenCellLibrary_typical.lib") == pins["library_sha256"],
            "candidate library changed")
    results = {}
    for boundary in ("fu", "parent"):
        baseline = audit_one(baseline_work, BASELINE[boundary], boundary, 128, baseline_work)
        check_sealed_inventory(baseline["input_hashes"], sealed_entries)
        candidate = audit_one(candidate_work, tuple(boundary + s for s in
                             ("-cost-01", "-map-01", "-sta-01")), boundary, 32, baseline_work)
        AUDIT.compare_interfaces(baseline["ports"], candidate["ports"])
        check_groups(baseline["structure_register_groups"], candidate["structure_register_groups"])
        require(baseline["mapped_metadata"] == candidate["mapped_metadata"],
                "mapped control/perf/products/state group counts differ: requires explicit review")
        require({k: v["body_sha256"] for k, v in baseline["arithmetic"].items()} ==
                {k: v["body_sha256"] for k, v in candidate["arithmetic"].items()},
                "arithmetic module body changed")
        results[boundary] = {
            "baseline": baseline, "candidate": candidate,
            "area_delta": candidate["area"] - baseline["area"],
            "area_reduction_percent": (baseline["area"] - candidate["area"]) / baseline["area"] * 100,
            "dff_delta": candidate["dff_count"] - baseline["dff_count"],
            "cell_count_delta": candidate["cell_count"] - baseline["cell_count"],
            "metadata_register_counts_equal": True,
            "timing_changes": timing_changes(baseline["timing"], candidate["timing"], boundary)}
    return {"status": "O2_H1_COST_COMPARISON_PASS", "pass": True,
            "baseline": "O2 B0 sealed O4 mapping", "candidate": pins["candidate"],
            "baseline_sealed_manifest_sha256": SEALED_MANIFEST_SHA,
            "candidate_identity_sha256": sha(candidate_work / "candidate-inputs.json"),
            "campaign_state_sha256": sha(candidate_work / "campaign-state.json"),
            "library_sha256": pins["library_sha256"], "tool_sha256": pins["tools"],
            "tool_identity_record_sha256": sha(tool_record),
            "tool_shared_library_sha256": shared_libraries,
            "source_record": pins, "results": results,
            "scope": "Measured whole-boundary mapped cell-area sums and fixed pre-layout reference-library STA.",
            "not_measured": ["whole-core area", "layout/CTS/SPEF", "power", "new cycles or speedup"],
            "old_local_cost_estimate_used_as_measured_savings": False,
            "hardware_tools_executed_by_this_audit": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-work", type=Path, required=True)
    parser.add_argument("--baseline-work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    command = {"argv": sys.argv, "python": sys.version, "cwd": str(Path.cwd()),
               "start": time.time(), "audit_sha256": sha(Path(__file__)),
               "o4_tool_source_sha256": {name: sha(O4 / name) for name in
                   ("audit.py", "synthesize.py", "timing.py", "compact.py", "canonical.py")}}
    (args.output / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    try:
        result = compare(args.candidate_work.resolve(), args.baseline_work.resolve())
    except BaseException as error:
        (args.output / "failure.json").write_text(json.dumps(
            {"error": repr(error), "end": time.time(), "pass": False}, indent=2) + "\n")
        raise
    result["end"] = time.time()
    (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result["status"])


if __name__ == "__main__":
    main()
