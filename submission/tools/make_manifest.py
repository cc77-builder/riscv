#!/usr/bin/env python3
"""Regenerate submission/MANIFEST.json from the files tracked in the index.

Covers every tracked blob except submodule gitlinks and MANIFEST.json itself.
Stage your changes (git add) before running it; verify.py checks the result.
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "submission" / "MANIFEST.json"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    old = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = []
    for entry in git("ls-files", "-s", "-z").split(b"\0"):
        if not entry:
            continue
        meta, path = entry.decode("utf-8").split("\t", 1)
        if meta.split()[0] == "160000" or path == "submission/MANIFEST.json":
            continue
        data = (ROOT / path).read_bytes()
        files.append({"path": path, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {key: old[key] for key in ("schema", "base_commit", "src_tree", "original_source_files", "submodules")}
    manifest["src_tree"] = git("rev-parse", "HEAD:src").decode().strip()
    manifest["files"] = sorted(files, key=lambda item: item["path"])
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "MANIFEST_WRITTEN", "files": len(files)}))


if __name__ == "__main__":
    main()
