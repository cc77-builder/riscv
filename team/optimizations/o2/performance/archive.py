"""Archive G4 performance evidence without build objects, generated RTL, or old emulators.

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

ROOT = Path(__file__).resolve().parents[4]
EXCLUDED_TOP = set()
EXCLUDED_PARTS = {"products", "preserved-o2-generated-build", "objects", "__pycache__", "rtl", "emu-compile"}
COMPRESS = {".log", ".json", ".txt", ".S", ".h", ".patch", ".cpp", ".hpp", ".csv", ".py", ".md", ".sh", ".graphml"}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(output):
    output = Path(output)
    manifest = json.loads((output / "archive-manifest.json").read_text(encoding="utf-8"))
    assert sha((output / "archive-manifest.json").read_bytes()) == (output / "archive-manifest.sha256").read_text().split()[0]
    expected = set()
    for record in manifest["files"]:
        rel = Path(record["stored"])
        assert not rel.is_absolute() and ".." not in rel.parts
        assert rel.as_posix() not in expected
        expected.add(rel.as_posix())
        stored = (output / rel).read_bytes()
        assert len(stored) == record["stored_bytes"] and sha(stored) == record["stored_sha256"]
        raw = gzip.decompress(stored) if record["encoding"] == "gzip" else stored
        assert len(raw) == record["raw_bytes"] and sha(raw) == record["raw_sha256"]
    actual = {p.relative_to(output).as_posix() for p in (output / "files").rglob("*") if p.is_file()}
    assert actual == expected, "missing or unexpected archive file"
    return dict(status="O1_O2_PERFORMANCE_ARCHIVE_BYTES_PASS", files=len(expected),
                raw_bytes=sum(x["raw_bytes"] for x in manifest["files"]),
                stored_bytes=sum(x["stored_bytes"] for x in manifest["files"]),
                archive_manifest_sha256=sha((output / "archive-manifest.json").read_bytes()),
                scope="byte preservation only; see independent G4 recheck for the performance verdict")

def create(work_root, output):
    work_root, output = work_root.resolve(), output.resolve()
    assert work_root.is_dir() and not output.exists()
    assert not output.is_relative_to(work_root), "archive must be outside its inputs"
    campaign=json.loads((work_root/"campaign-01/result.json").read_text())
    audit=json.loads((work_root/"results-01/verification.json").read_text())
    launch=json.loads((work_root/"launch-state.json").read_text())
    assert campaign["status"]=="O1_O2_PAIRED_PERFORMANCE_PASS" and campaign["new_emu_jobs"]==36
    assert audit["status"]=="OFFLINE_O1_O2_PAIRED_RECHECK_PASS" and audit["original_evidence_unchanged"]
    assert launch["status"]=="ALL_COMMANDS_FINISHED" and all(r["exit_code"]==0 for r in launch["stages"])
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
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stored)
        records.append(dict(original=original, stored=target.relative_to(output).as_posix(),
                            encoding=encoding, raw_bytes=len(raw), raw_sha256=sha(raw),
                            stored_bytes=len(stored), stored_sha256=sha(stored)))
    excluded = []
    for p in sorted(work_root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(work_root)
        if rel.parts[0] in EXCLUDED_TOP or set(rel.parts) & EXCLUDED_PARTS:
            continue
        assert not p.is_symlink(), "unexpected evidence symlink"
        add(p.read_bytes(), Path("runs") / rel, str(p))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for raw in subprocess.check_output(["git", "ls-files", "-z", "--",
            "team/optimizations/o2/performance"], cwd=ROOT).split(b"\0"):
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
