"""Archive G3 evidence without build objects, generated RTL, or old emulators.

All selected source bytes and stored bytes receive independent hashes. Gzip
is deterministic; verification checks decompression too. This is packaging,
not an emulator run or a substitute for recheck.py.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "fullcore"))
import archive_gate
from archive_gate import require

ROOT = Path(__file__).resolve().parents[4]
EXCLUDED_TOP = {"preserved-previous-build", "build-01-generated", "build-02-generated"}
EXCLUDED_PARTS = {"objects", "__pycache__", "rtl"}
COMPRESS = {".log", ".json", ".txt", ".S", ".h", ".patch"}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(output):
    return dict(status="O2_G3_ARCHIVE_BYTES_PASS", **archive_gate.verify(output),
                scope="byte preservation only; see independent G3 recheck for functional verdict")


def create(work_root, output):
    work_root, output = work_root.resolve(), output.resolve()
    require(work_root.is_dir() and not output.exists(), "input directory missing or output exists")
    require(not output.is_relative_to(work_root), "archive must be outside its inputs")
    output.mkdir(parents=True)
    records = []
    def add(raw, rel, original):
        stored = raw
        encoding = "identity"
        if rel.suffix in COMPRESS and len(raw) >= 16384:
            stored = gzip.compress(raw, compresslevel=9, mtime=0)
            rel = rel.with_name(rel.name + ".gz")
            encoding = "gzip"
        target = output / "files" / rel
        require(not target.exists(), "duplicate archive target")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stored)
        records.append(dict(original=original, stored=target.relative_to(output).as_posix(),
                            encoding=encoding, raw_bytes=len(raw), raw_sha256=sha(raw),
                            stored_bytes=len(stored), stored_sha256=sha(stored)))
    excluded = []
    for p in sorted(work_root.rglob("*")):
        require(not p.is_symlink(), "unexpected evidence symlink")
        if not p.is_file():
            continue
        rel = p.relative_to(work_root)
        if rel.parts[0] in EXCLUDED_TOP or set(rel.parts) & EXCLUDED_PARTS:
            continue
        require(not p.is_symlink(), "unexpected evidence symlink")
        add(p.read_bytes(), Path("runs") / rel, str(p))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for raw in subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
            "team/optimizations/o2/fullcore", "team/optimizations/o1/build_inputs.py",
            "team/optimizations/o1/build_recipe.py", "team/scripts/prepare-core-baseline.py",
            "team/scripts/activate.sh"], cwd=ROOT).split(b"\0"):
        if raw:
            name = raw.decode()
            add((ROOT / name).read_bytes(), Path("tools") / name, str(ROOT / name))
    manifest = dict(version=1, created_utc=datetime.now(timezone.utc).isoformat(),
                    source_commit_at_export=commit, work_root=str(work_root),
                    exclusion_policy=dict(top_directories=sorted(EXCLUDED_TOP),
                                          directory_components=sorted(EXCLUDED_PARTS),
                                          reason="generated hardware/build objects and preserved old emulator excluded; metadata, inputs, source, commands, raw logs and failed attempts retained"),
                    files=records)
    data = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (output / "archive-manifest.json").write_bytes(data)
    (output / "archive-manifest.sha256").write_text(sha(data) + "  archive-manifest.json\n")
    result = verify(output)
    (output / "archive-check.json").write_text(json.dumps(result, indent=2) + "\n")
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not args.verify_only and args.work_root is None:
        parser.error("--work-root required")
    print(json.dumps(verify(args.output) if args.verify_only else create(args.work_root, args.output), indent=2))

if __name__ == "__main__":
    main()
