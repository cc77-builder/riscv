"""Archive B0/H1 performance evidence without build objects, generated RTL, or old emulators.

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
from portable import Archive, require, safe_relative

ROOT = Path(__file__).resolve().parents[6]
EXCLUDED_TOP = set()
EXCLUDED_PARTS = {"products", "preserved-o2-generated-build", "objects", "__pycache__", "rtl", "emu-compile"}
COMPRESS = {".log", ".json", ".txt", ".S", ".h", ".patch", ".cpp", ".hpp", ".csv", ".py", ".md", ".sh", ".graphml"}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(output):
    output = Path(output)
    for name in ("archive-manifest.json", "archive-manifest.sha256", "files"):
        require(not (output / name).is_symlink(), "archive root entry is a symlink: " + name)
    archive = Archive(output)
    return dict(status="B0_H1_PERFORMANCE_ARCHIVE_BYTES_PASS", **archive.bytes_result,
                scope="byte preservation only; see independent B0/H1 recheck for the performance verdict")

def create(work_root, output):
    require(not output.is_symlink(), "archive output is a symlink")
    work_root, output = work_root.resolve(), output.resolve()
    require(work_root.is_dir() and not output.exists(), "missing work root or existing output")
    require(not output.is_relative_to(work_root), "archive must be outside its inputs")
    campaign=json.loads((work_root/"campaign-01/result.json").read_text())
    audit=json.loads((work_root/"results-01/verification.json").read_text())
    launch=json.loads((work_root/"supervisor-state.json").read_text())
    require(campaign["status"]=="B0_H1_PAIRED_PERFORMANCE_PASS" and campaign["new_emu_jobs"]==36,
            "campaign did not complete the expected jobs")
    require(audit["status"]=="OFFLINE_B0_H1_PAIRED_RECHECK_PASS" and audit["original_evidence_unchanged"] is True,
            "offline review failed or original evidence changed")
    require(launch["status"]=="B0_H1_MEASUREMENT_AND_RECHECK_PASS" and launch["steps"]
            and all(r["exit_code"]==0 for r in launch["steps"]), "launcher steps did not all pass")
    output.mkdir(parents=True)
    records = []
    def add(raw, rel, original):
        safe_relative(rel.as_posix())
        stored = raw
        encoding = "identity"
        if rel.suffix in COMPRESS and len(raw) >= 16384:
            stored = gzip.compress(raw, compresslevel=9, mtime=0)
            rel = rel.with_name(rel.name + ".gz")
            encoding = "gzip"
        target = output / "files" / rel
        require(not target.exists() and not target.is_symlink(), "duplicate archive destination")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stored)
        records.append(dict(original=original, stored=target.relative_to(output).as_posix(),
                            encoding=encoding, raw_bytes=len(raw), raw_sha256=sha(raw),
                            stored_bytes=len(stored), stored_sha256=sha(stored)))
    excluded = []
    for p in sorted(work_root.rglob("*")):
        rel = p.relative_to(work_root)
        if rel.parts[0] in EXCLUDED_TOP or set(rel.parts) & EXCLUDED_PARTS:
            continue
        require(not p.is_symlink(), "unexpected evidence symlink")
        require(p.resolve().is_relative_to(work_root), "evidence path escapes work root")
        if not p.is_file():
            continue
        add(p.read_bytes(), Path("runs") / rel, str(p))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tool_names = ["compare.py", "results.py", "build_profile.py", "test_compare.py",
                  "CONTRACT.md", "archive.py", "portable.py", "test_portable.py", "prepare_inputs.py",
                  "test_archive_gates.py"]
    for leaf in tool_names:
        p = Path(__file__).resolve().parent / leaf
        name = p.relative_to(ROOT)
        add(p.read_bytes(), Path("tools") / name, str(p))
    manifest = dict(version=1, created_utc=datetime.now(timezone.utc).isoformat(),
                    source_commit_at_export=commit, work_root=str(work_root),
                    tool_identity_policy="Runtime tools Git-bound in campaign snapshots; later export tools bound by archive file hashes, not claimed present in runtime commit",
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
