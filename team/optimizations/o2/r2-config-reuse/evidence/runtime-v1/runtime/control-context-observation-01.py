"""Describe unchanged controls in an already audited S3 matrix; no new execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def require(ok, message):
    if not ok:
        raise ValueError(message)


parser = argparse.ArgumentParser(description=__doc__)
for name in ("repo", "archive", "audit", "output"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args()
repo, path, audit_path, output = [getattr(args, name).resolve()
    for name in ("repo", "archive", "audit", "output")]
sys.path.insert(0, str(repo / "team/optimizations/o2/r2-config-reuse"))
import runtime_evidence as e
g, a = e.g, e.a
require(repo == a.ROOT and not output.exists(), "selected checkout and fresh observation required")
a.outside_inputs(output, [repo, path, audit_path])
archive = g.load("s3_control_observation_archive", repo / e.PORTABLE).Archive(path)
audit = a.read(audit_path)
require(audit["status"] == e.AUDIT_PASS and audit["qualification_scope"] == "matrix" and
        audit["archive"] == archive.bytes_result, "complete current raw audit required")
records = {}
for logical in archive.records:
    parts = Path(logical).parts
    if len(parts) == 5 and parts[0] == "campaigns" and parts[2] == "runs" and parts[-1] == "result.json":
        record = archive.json(logical)
        if not record["negative"] and record["replay"] == 0:
            key = record["shard"], record["dataset"], record["variant"]
            require(key not in records, "duplicate formal observation")
            records[key] = record
require(len(records) == 24, "complete formal matrix required")
images = {}
for collection in archive.manifest["builds"]:
    for image in archive.json("builds/" + collection + "/images.json")["images"]:
        images[image["name"]] = "builds/" + collection + "/images/" + image["name"]
groups = []
for shard, software, method in ((5, "basic", "rvv"), (7, "basic", "rvv"),
                                 (7, "reuse", "rvv"), (7, "reuse", "vdot")):
    cells, paired = [], []
    for dataset in range(3):
        before, after = [records[shard, dataset, variant] for variant in a.VARIANTS]
        prefixes = [images[r["name"]] for r in (before, after)]
        manifests = [archive.json(prefix + "/data/manifest.json") for prefix in prefixes]
        require(manifests[0]["plan"] == manifests[1]["plan"], "control invocation plan differs")
        indices = [next(i for i, row in enumerate(m["rows"])
                        if row["software"] == software and row["method"] == method) for m in manifests]
        require(indices[0] == indices[1], "control slot differs")
        index = indices[0]
        rows = [m["rows"][index] for m in manifests]
        require(rows[0]["api_symbol"] == rows[1]["api_symbol"], "control API differs")
        symbol = rows[0]["api_symbol"]
        elfs = [g.ELF(archive.raw(prefix + "/vdot-perf.elf")) for prefix in prefixes]
        leaves = [elf.symbol_data(symbol) for elf in elfs]
        wrappers = [elf.symbol_data("t13_kernel_" + str(index)) for elf in elfs]
        bins = [archive.raw(prefix + "/vdot-perf.bin") for prefix in prefixes]
        slots = [raw[8192 * (index + 1):8192 * (index + 2)] for raw in bins]
        removed = len(rows[1]["config_reuse_proof"]["removed"])
        if method == "rvv":
            require(removed == 0 and leaves[0] == leaves[1] and wrappers[0] == wrappers[1] and
                    len(slots[0]) == 8192 and slots[0] == slots[1], "supposed unchanged RVV control changed")
        require(archive.raw(prefixes[0] + "/data/cases.h") == archive.raw(prefixes[1] + "/data/cases.h"),
                "control inputs differ")
        cells.append(dict(dataset=dataset, symbol=symbol, removed_configs=removed,
            leaf_identical=leaves[0] == leaves[1], wrapper_identical=wrappers[0] == wrappers[1],
            complete_8k_slot_identical=slots[0] == slots[1],
            leaf_sha256=[hashlib.sha256(raw).hexdigest() for raw in leaves],
            slot_sha256=[hashlib.sha256(raw).hexdigest() for raw in slots],
            same_plan=True, same_cases=True, complete_bin_identical=bins[0] == bins[1]))
        samples = [{s["seq"]: s for s in record["samples"]} for record in (before, after)]
        sequences = [sorted(value) for value in samples]
        require(sequences[0] == sequences[1], "control sample sequence differs")
        for position, seq in enumerate(sequences[0]):
            left, right = [value[seq] for value in samples]
            if (left["software"], left["method"], left["phase"]) != (software, method, "measured"):
                continue
            require(all(left[k] == right[k] for k in ("software", "method", "phase", "repeat", "seq")),
                    "control window identities differ")
            prior = sequences[0][position - 1] if position else None
            predecessors = [value[prior] for value in samples] if prior is not None else None
            paired.append(dict(dataset=dataset, seq=seq, repeat=left["repeat"],
                cycles_before=left["cycles"], cycles_after=right["cycles"],
                delta_cycles=right["cycles"] - left["cycles"],
                instructions_before=left["instructions"], instructions_after=right["instructions"],
                preceding_window=None if predecessors is None else dict(seq=prior,
                    software=predecessors[0]["software"], method=predecessors[0]["method"],
                    cycles=[p["cycles"] for p in predecessors], instructions=[p["instructions"] for p in predecessors])))
    require(len(paired) == 12, "control formal sample coverage")
    groups.append(dict(shard=shard, software=software, method=method, cells=cells, formal_windows=paired,
        before_total=sum(r["cycles_before"] for r in paired), after_total=sum(r["cycles_after"] for r in paired),
        minimum_delta=min(r["delta_cycles"] for r in paired), maximum_delta=max(r["delta_cycles"] for r in paired)))
report = dict(status="S3_AUDITED_CONTROL_CONTEXT_OBSERVATION", source_sha256=g.sha(Path(__file__)),
    matrix_manifest_sha256=archive.manifest_sha256, raw_audit_sha256=g.sha(audit_path), groups=groups,
    new_emu_runs=0, new_compilations=0, modifies_frozen_inputs=False,
    scope="observational pairing of original measured windows and unchanged code/plan; no causal attribution or isolated per-function benchmark",
    conclusion="Identical RVV leaves/wrappers/slots and fixed cases/plan can have small window deltas in these different complete images. Retain the fastest actually measured RVV. Do not attribute unchanged-code deltas to configuration deletion in that RVV leaf.")
g.save(output, report)
print(json.dumps({k:v for k,v in report.items() if k != "groups"}, indent=2))
for group in groups:
    print(json.dumps({k:v for k,v in group.items() if k not in ("cells", "formal_windows")}, indent=2))
