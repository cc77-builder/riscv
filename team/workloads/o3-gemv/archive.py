"""Archive O3 application evidence without build objects, generated RTL, or old emulators.

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

ROOT = Path(__file__).resolve().parents[3]
EXCLUDED_TOP = set()
EXCLUDED_PARTS = {"products", "preserved-o2-generated-build", "objects", "__pycache__", "rtl", "emu-compile"}
COMPRESS = {".log", ".json", ".txt", ".S", ".h", ".patch", ".cpp", ".hpp", ".csv", ".py", ".md", ".sh", ".graphml"}


TOOL_DEPENDENCIES = (
    "team/workloads/unified-vdot/generate.py", "team/workloads/unified-vdot/check.py",
    "team/workloads/vdot-perf/check.py",
    "team/optimizations/o2/fullcore/live_inputs.py", "team/optimizations/o1/build_recipe.py",
    "team/optimizations/o1/build_inputs.py", "team/scripts/prepare-core-baseline.py", "team/scripts/activate.sh",
    "team/optimizations/o1/fullcore/analyze.py", "team/optimizations/o2/fullcore/analyze.py",
    "team/optimizations/o1/audit/runtime_gate.py", "team/optimizations/o2/fullcore/workloads/check.py",
    "team/optimizations/o2/performance/compare.py", "team/optimizations/o2/performance/build_profile.py",
)


def tool_paths():
    """Snapshot active tooling, excluding previously delivered evidence trees."""
    directory=Path("team/workloads/o3-gemv")
    tracked=subprocess.check_output(["git", "ls-files", "-z", "--", directory.as_posix()], cwd=ROOT)
    names={raw.decode() for raw in tracked.split(b"\0") if raw and Path(raw.decode()).parent==directory
           and (Path(raw.decode()).suffix in {".py", ".c", ".h", ".md", ".sh", ".ld"} or Path(raw.decode()).name=="Makefile")}
    return sorted(names | set(TOOL_DEPENDENCIES))

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(output):
    output = Path(output)
    manifest = json.loads((output / "archive-manifest.json").read_text(encoding="utf-8"))
    require(sha((output / "archive-manifest.json").read_bytes()) == (output / "archive-manifest.sha256").read_text().split()[0], 'archive manifest digest mismatch')
    expected = set()
    for record in manifest["files"]:
        rel = Path(record["stored"])
        require(not rel.is_absolute() and ".." not in rel.parts and rel.parts and rel.parts[0] == "files", 'unsafe archive path')
        require(rel.as_posix() not in expected, 'duplicate archive file')
        expected.add(rel.as_posix())
        require(not any((output / part).is_symlink() for part in [rel, *rel.parents]), "archive symlink")
        stored = (output / rel).read_bytes()
        require(len(stored) == record["stored_bytes"] and sha(stored) == record["stored_sha256"], 'stored archive hash/size mismatch')
        require(record["encoding"] in ("identity", "gzip"), "unknown archive encoding")
        raw = gzip.decompress(stored) if record["encoding"] == "gzip" else stored
        require(len(raw) == record["raw_bytes"] and sha(raw) == record["raw_sha256"], 'raw archive hash/size mismatch')
    actual = {p.relative_to(output).as_posix() for p in (output / "files").rglob("*") if p.is_file()}
    require(actual == expected, "missing or unexpected archive file")
    return dict(status="O3_APPLICATION_ARCHIVE_BYTES_PASS", files=len(expected),
                raw_bytes=sum(x["raw_bytes"] for x in manifest["files"]),
                stored_bytes=sum(x["stored_bytes"] for x in manifest["files"]),
                archive_manifest_sha256=sha((output / "archive-manifest.json").read_bytes()),
                scope="byte preservation only; see independent O3 recheck for the performance verdict")

def create(work_root, output, campaign_name='campaign-01', results_name='results-01', launch_name='launch-state.json'):
    work_root, output = work_root.resolve(), output.resolve()
    require(work_root.is_dir() and not output.exists(), 'invalid work root or existing output')
    require(not output.is_relative_to(work_root), "archive must be outside its inputs")
    require(all(Path(n).name == n and n not in (".", "..") for n in (campaign_name, results_name, launch_name)), 'unsafe campaign/result/launch name')
    campaign=json.loads((work_root/campaign_name/"result.json").read_text())
    audit=json.loads((work_root/results_name/"verification.json").read_text())
    launch=json.loads((work_root/launch_name).read_text())
    require(campaign.get("status")=="O3_PAIRED_APPLICATION_CAMPAIGN_PASS" and type(campaign.get("real_emu_jobs")) is int and campaign["real_emu_jobs"]==56, 'incomplete campaign')
    require(audit.get("status")=="O3_RAW_EVIDENCE_RECHECK_PASS" and audit.get("original_inputs_unchanged") is True, 'incomplete evidence recheck')
    require(launch.get("status")=="EXITED" and type(launch.get("exit_code")) is int and launch["exit_code"]==0, 'incomplete launcher')
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
        require(not target.exists(), 'archive target collision')
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
        require(not p.is_symlink(), "unexpected evidence symlink")
        add(p.read_bytes(), Path("runs") / rel, str(p))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for name in tool_paths():
        add((ROOT / name).read_bytes(), Path("tools") / name, str(ROOT / name))
    manifest = dict(version=1, created_utc=datetime.now(timezone.utc).isoformat(),
                    source_commit_at_export=commit, work_root=str(work_root),
                    campaign_name=campaign_name, results_name=results_name, launch_name=launch_name,
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
    parser.add_argument("--campaign-name", default="campaign-01")
    parser.add_argument("--results-name", default="results-01")
    parser.add_argument("--launch-name", default="launch-state.json")
    args = parser.parse_args()
    if not args.verify_only and args.work_root is None:
        parser.error("--work-root required")
    print(json.dumps(verify(args.output) if args.verify_only else create(args.work_root, args.output, args.campaign_name, args.results_name, args.launch_name), indent=2))

if __name__ == "__main__":
    main()
