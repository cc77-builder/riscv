#!/usr/bin/env python3
"""Seal finished H1 engineering evidence without build caches or executables."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(root):
    data = json.loads((root / "manifest.json").read_text())
    seen = set()
    for entry in data["entries"]:
        if entry["path"] in seen:
            raise ValueError("duplicate payload")
        seen.add(entry["path"])
        path = (root / "files" / entry["stored"]).resolve()
        if not path.is_relative_to((root / "files").resolve()):
            raise ValueError("archive path escape")
        stored = path.read_bytes()
        if len(stored) != entry["stored_bytes"] or sha(stored) != entry["stored_sha256"]:
            raise ValueError("stored bytes differ: " + entry["path"])
        raw = gzip.decompress(stored) if entry["gzip"] else stored
        if len(raw) != entry["bytes"] or sha(raw) != entry["sha256"]:
            raise ValueError("payload differs: " + entry["path"])
    return {"status": "O2_H1_ARCHIVE_BYTE_CHECK_PASS", "files": len(seen),
            "stored_bytes": sum(e["stored_bytes"] for e in data["entries"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify)))
        return
    if not args.work or not args.output:
        parser.error("use --verify, or both --work and --output")
    work, output = args.work.resolve(), args.output.resolve()
    if output.is_relative_to(work) or output.exists():
        raise ValueError("output must be new and outside work")
    state = json.loads((work / "campaign-state.json").read_text())
    if state["status"] != "passed" or not state["source_and_r0_lock_unchanged"]:
        raise ValueError("campaign not complete")
    # The final validation receipt binds both functional and cost audits.
    receipt = json.loads((work / "final-validation.json").read_text())
    if receipt["status"] != "O2_H1_LOCAL_VALIDATION_PASS":
        raise ValueError("final audit not complete")
    output.mkdir(parents=True)
    entries, external = [], []
    for src in sorted(work.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(work)
        if any(part in ("obj", "__pycache__") for part in rel.parts):
            continue
        raw = src.read_bytes()
        if raw.startswith(b"\x7fELF"):
            external.append({"path": str(rel), "bytes": len(raw), "sha256": sha(raw)})
            continue
        compress = len(raw) > 262144
        stored_rel = Path(str(rel) + ".gz") if compress else rel
        payload = gzip.compress(raw, compresslevel=9, mtime=0) if compress else raw
        dest = output / "files" / stored_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        entries.append({"path": str(rel), "stored": str(stored_rel), "gzip": compress,
                        "bytes": len(raw), "sha256": sha(raw), "stored_bytes": len(payload),
                        "stored_sha256": sha(payload)})
    (output / "manifest.json").write_text(json.dumps({"format": 1, "entries": entries}, indent=2) + "\n")
    (output / "external-artifacts.json").write_text(json.dumps({
        "scope": "obj directories excluded; runnable FU/parent binaries are identified by runner artifacts.json",
        "other_elf_files": external}, indent=2) + "\n")
    print(json.dumps(verify(output)))


if __name__ == "__main__":
    main()
