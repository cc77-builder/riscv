"""Verify sealed C3-HF raw/stored bytes without EDA, mutation, or extraction."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

def digest(stream):
    h = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
        h.update(block)
        size += len(block)
    return h.hexdigest(), size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    root = a.archive.resolve()
    if a.output.exists():
        raise ValueError("new audit output required")
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    rows = manifest["files"]
    if not rows or len({x["path"] for x in rows}) != len(rows):
        raise ValueError("empty or duplicate logical paths")
    if len({x["stored"] for x in rows}) != len(rows):
        raise ValueError("duplicate payload paths")
    for row in rows:
        p = (root / row["stored"]).resolve()
        if not p.is_relative_to(root):
            raise ValueError("payload path escapes archive")
        with p.open("rb") as stream:
            stored = digest(stream)
        if stored != (row["stored_sha256"], row["stored_bytes"]):
            raise ValueError("stored mismatch " + row["path"])
        if row["compression"] not in ("none", "gzip"):
            raise ValueError("unknown compression")
        opener = gzip.open if row["compression"] == "gzip" else open
        with opener(p, "rb") as stream:
            raw = digest(stream)
        if raw != (row["raw_sha256"], row["raw_bytes"]):
            raise ValueError("raw mismatch " + row["path"])
    with path.open("rb") as stream:
        manifest_sha, _ = digest(stream)
    result = dict(status="C3_HF_ARCHIVE_HASH_PASS", files=len(rows),
                  raw_bytes=sum(x["raw_bytes"] for x in rows),
                  stored_bytes=sum(x["stored_bytes"] for x in rows),
                  candidate_commit=manifest["candidate_commit"],
                  manifest_sha256=manifest_sha,
                  scope="Byte-integrity audit only. Does not rerun RTL, EDA, or numerical qualification.")
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
