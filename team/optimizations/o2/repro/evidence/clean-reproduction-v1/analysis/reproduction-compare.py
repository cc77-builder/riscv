"""Compare two independently audited R4-format cohorts without new EMU runs.

This diagnostic does not require cross-build cycles to be identical, and does
not replace either cohort's architectural, raw-log or physical-source audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError("Run this comparison without Python optimization")

parser = argparse.ArgumentParser(description=__doc__)
for name in ("repo", "baseline", "candidate", "baseline-audit", "candidate-audit", "output"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args()
repo = args.repo.resolve()
sys.path.insert(0, str(repo / "team/optimizations/o2/repro"))
import clean_entry as ce

ce.bind_sources(repo)
portable, _, _ = ce.evidence.modules(repo)
archives = {"baseline": portable.Archive(args.baseline.resolve()),
            "candidate": portable.Archive(args.candidate.resolve())}
proofs = {"baseline": ce.p.read(args.baseline_audit),
          "candidate": ce.p.read(args.candidate_audit)["software_gate_result"]}
keys = ("variant", "shard", "dataset", "software", "method", "repeat")
cohorts = {}
for label, archive in archives.items():
    proof = proofs[label]
    assert proof["status"] == "R4_ENTRY_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS"
    assert proof["archive"] == archive.bytes_result
    records = [row for campaign in archive.manifest["campaigns"]
               for row in archive.json("campaigns/" + campaign + "/results.json")["runs"]]
    indexed = {}
    for row in records:
        assert row["negative"] is False and type(row["replay"]) is int and row["replay"] in (0, 1)
        key = (row["name"], row["replay"])
        assert key not in indexed
        indexed[key] = row
    formal = [r for r in records if r["replay"] == 0]
    replay = [r for r in records if r["replay"] == 1]
    assert len(formal) == 24 and len(replay) == 8 and all(r["dataset"] == 0 for r in replay)
    for row in replay:
        original = indexed[(row["name"], 0)]
        assert ce.a.frozen_m.signature(original) == ce.a.frozen_m.signature(row)
    stats = ce.a.summarize(records)
    assert stats["measured_windows"] == proof["formal_windows"] == 384
    assert stats["rows"] == proof["rows"] and proof["all_window_replay_comparisons"] == 192
    samples = {}
    for row in records:
        for sample in row["samples"]:
            assert all(sample[k] == row[k] for k in ("variant", "shard", "dataset"))
            key = (row["replay"],) + tuple(sample[k] for k in keys)
            assert key not in samples
            samples[key] = sample
    assert len(samples) == 768
    images = {}
    for build in archive.manifest["builds"]:
        for image in archive.json("builds/" + build + "/images.json")["images"]:
            assert image["name"] not in images
            logical = "builds/" + build + "/images/" + image["name"] + "/vdot-perf.bin"
            digest = hashlib.sha256(archive.raw(logical)).hexdigest()
            assert digest == image["image_sha256"]
            images[image["name"]] = digest
    assert len(images) == 24
    cohorts[label] = dict(samples=samples, rows=stats["rows"], images=images)

old, new = cohorts["baseline"], cohorts["candidate"]
assert old["samples"].keys() == new["samples"].keys() and old["images"].keys() == new["images"].keys()
differences, totals = [], {"all_windows": 0, "formal_measured": 0, "replay_all_windows": 0,
                           "same_cycles": 0, "same_instructions": 0, "same_formal_cycles": 0,
                           "same_formal_instructions": 0}
for key in sorted(old["samples"]):
    left, right = old["samples"][key], new["samples"][key]
    for field in ("seq", "phase", "m", "k", "scope"):
        assert left.get(field) == right.get(field), (key, field)
    measured = key[0] == 0 and right["phase"] == "measured"
    totals["all_windows"] += 1
    totals["formal_measured"] += int(measured)
    totals["replay_all_windows"] += int(key[0] == 1)
    for field, count in (("cycles", "cycles"), ("instructions", "instructions")):
        equal = left[field] == right[field]
        totals["same_" + count] += int(equal)
        totals["same_formal_" + count] += int(equal and measured)
    if any(left[field] != right[field] for field in ("cycles", "instructions")):
        differences.append(dict(key=dict(zip(("replay",) + keys, key)), baseline=left, candidate=right))
assert totals["formal_measured"] == 384 and totals["replay_all_windows"] == 192
source_sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
result = dict(status="T17_AUDITED_CROSS_BUILD_COMPARISON_COMPLETE", new_emu_runs=0,
              scope="Cross-build observation only; no historical runtime PASS is transferred and no new application performance is inferred.",
              analysis_source_sha256=source_sha(Path(__file__)),
              baseline_manifest_sha256=source_sha(args.baseline / "archive-manifest.json"),
              candidate_manifest_sha256=source_sha(args.candidate / "archive-manifest.json"),
              baseline_audit_sha256=source_sha(args.baseline_audit), candidate_audit_sha256=source_sha(args.candidate_audit),
              counts=totals, window_differences=differences,
              identical_load_images=sum(old["images"][n] == new["images"][n] for n in old["images"]),
              image_comparison={n: dict(baseline=old["images"][n], candidate=new["images"][n]) for n in sorted(old["images"])},
              baseline_rows=old["rows"], candidate_rows=new["rows"])
assert not args.output.exists()
args.output.write_bytes((json.dumps(result, indent=2) + "\n").encode())
print(json.dumps({k: v for k, v in result.items() if k not in
                 ("window_differences", "image_comparison", "baseline_rows", "candidate_rows")}, indent=2))
