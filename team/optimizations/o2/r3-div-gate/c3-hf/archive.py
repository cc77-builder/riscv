"""Seal the single C3-HF trial, retaining all failures and source identities."""
import argparse
import datetime
import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--source-repo", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise ValueError("new output required")
    selected = {}
    def add(key, path):
        if key in selected:
            raise ValueError("duplicate " + key)
        selected[key] = Path(path)
    for p in sorted(a.work.rglob("*")):
        rel = p.relative_to(a.work)
        if {"repo", "obj", "__pycache__", "pre-run-documents"}.intersection(rel.parts):
            continue
        if p.is_file():
            add("work/" + rel.as_posix(), p)
    candidate = a.work / "repo"
    module = a.source_repo / "team/optimizations/o2/r3-div-gate/c3-hf"
    for p in sorted(module.rglob("*")):
        rel = p.relative_to(module)
        if {"evidence", "reviews", "__pycache__"}.intersection(rel.parts):
            continue
        if p.is_file() and p.name not in {"RESULT.md", "README.md", "RUN_STATE.json"}:
            add("source/c3-hf/" + rel.as_posix(), p)
    exu = "src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
    add("source/baseline/" + exu, a.source_repo / exu)
    add("source/candidate/" + exu, candidate / exu)
    for rel in ["build.sc", "team/scripts/activate.sh", "team/optimizations/o2/run_rtl.py",
                "team/optimizations/o2/check_negative_fu.py", "team/optimizations/o2/test_negative_fu.py",
                "team/rtl/vdot/prepare_vectors.py"]:
        add("source/fixture/" + rel, candidate / rel)
    for rel in ["team/optimizations/o2/fu", "team/optimizations/o2/parent",
                "team/models/vdot", "team/optimizations/o4"]:
        for p in sorted((candidate / rel).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".scala", ".cpp", ".h", ".json", ".jsonl", ".md"}:
                add("source/fixture/" + p.relative_to(candidate).as_posix(), p)
    old = a.source_repo / "team/optimizations/o2/r3-div-gate"
    for p in sorted((old / "c2/parent").iterdir()):
        if p.is_file():
            add("source/reused-c2-parent/" + p.name, p)
    for rel in ["c2/check_generated_cone.py", "timing-review/review.py", "c2-g0/system_model.py"]:
        add("source/reused/" + rel, old / rel)
    for name in ["control_variants.py", "control-variants-01.json", "command-01.json"]:
        add("source/reused-not-rerun-c3-g0/" + name,
            old / "c3-g0/evidence/candidate-review" / name)
    references = {}
    for rel in ["evidence/20261025-performance-cost/manifest.json", "c1/evidence/20261025-screen/manifest.json",
                "c2/evidence/20261025-local/manifest.json", "c2/cost/evidence/20261025-cost/manifest.json",
                "c3-g0/evidence/manifest.json"]:
        p = old / rel
        references[p.relative_to(a.source_repo).as_posix()] = {"sha256": sha(p), "bytes": p.stat().st_size}
        add("references/" + rel, p)
    baseline_manifest = old / "evidence/20261025-performance-cost/manifest.json"
    baseline_root = Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025")
    baseline_count = 0
    for row in json.loads(baseline_manifest.read_text())["files"]:
        if any(row["path"].startswith("cost/" + x + "/") for x in ["parent-cost-01", "parent-map-01", "parent-sta-01"]):
            rel = row["path"][len("cost/"):]
            p = baseline_root / rel
            if p.stat().st_size != row["raw_bytes"] or sha(p) != row["raw_sha256"]:
                raise ValueError("baseline raw changed: " + rel)
            add("baseline/" + rel, p)
            baseline_count += 1
    if baseline_count != 143:
        raise ValueError("baseline payload set differs")
    tool = Path("/home/riscv/riscv-lab/o4-cost-20261020")
    for rel in ["library/NangateOpenCellLibrary_typical.lib", "tools/executable-identities.json"]:
        add("tools/" + rel, tool / rel)
    a.output.mkdir(parents=True)
    rows = []
    for key, p in sorted(selected.items()):
        raw_hash, size = sha(p), p.stat().st_size
        compressed = size >= 16384
        stored = "payload/" + key + (".gz" if compressed else "")
        target = a.output / stored
        target.parent.mkdir(parents=True, exist_ok=True)
        with p.open("rb") as src, target.open("xb") as dst:
            if compressed:
                with gzip.GzipFile(fileobj=dst, filename="", mode="wb", compresslevel=6, mtime=0) as gz:
                    shutil.copyfileobj(src, gz, 1024 * 1024)
            else:
                shutil.copyfileobj(src, dst, 1024 * 1024)
        if sha(p) != raw_hash:
            raise ValueError("input changed during archive: " + str(p))
        rows.append(dict(path=key, origin=str(p), raw_sha256=raw_hash, raw_bytes=size,
                         stored=stored, stored_sha256=sha(target), stored_bytes=target.stat().st_size,
                         compression="gzip" if compressed else "none"))
    manifest = dict(status="C3_HF_EVIDENCE_SEALED", time=datetime.datetime.now().astimezone().isoformat(),
                    candidate_commit="77d0a1228f0da7d584d5c7375b404dcda9763cf3",
                    baseline_commit="0f12df675378556670afd0dd2153f47fcb330610",
                    reference_archives=references, files=rows,
                    scope="Single trial, local correctness and same-constraint cost. Failed infrastructure attempts retained. No objects/caches/binaries; binary hashes retained. Formal report/ledger outside seal.")
    (a.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(files=len(rows), raw_bytes=sum(x["raw_bytes"] for x in rows),
                          stored_bytes=sum(x["stored_bytes"] for x in rows),
                          manifest_sha256=sha(a.output / "manifest.json")), indent=2))

if __name__ == "__main__":
    main()
