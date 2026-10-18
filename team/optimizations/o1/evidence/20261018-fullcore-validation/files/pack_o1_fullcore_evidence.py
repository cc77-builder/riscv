#!/usr/bin/env python3
"""Archive the finished O1 fullcore campaign after its strict offline recheck.

PREPARED ONLY: writing this script does not run a campaign or create an archive.
Run from the WSL work root only after all 12 jobs, the final strict recheck,
final host checks and final review have finished. Example (replace suffixes):

  python3 -B pack_o1_fullcore_evidence.py \
    --final-recheck runs/o1-fullcore-recheck-01 \
    --final-host-tests runs/o1-final-host-tests-01 \
    --final-review runs/o1-final-review-01

The script never runs EMU, edits evidence or overwrites a destination. It checks
receipts and hashes, packages immutable bytes, then checks the sources again.
A failed packaging attempt leaves a uniquely named INCOMPLETE sibling for audit.
The two external integration patches are preserved as historical drafts only.
"""
import argparse
import codecs
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

WORK = Path(__file__).absolute().parent
REPO = WORK / "repo"
RUNS = WORK / "runs"
CAMPAIGN = RUNS / "o1-fullcore-suite-01"
DESTINATION = REPO / "team/optimizations/o1/evidence/20261018-fullcore-validation"
JOBS = ("hello-vadd", "negative-vdot") + tuple(f"functional-{i}" for i in range(8)) + ("control", "dense-batch128")
RAW = ("stdout.log", "stderr.log", "run.log")
DRIVERS = ("team/optimizations/o1/fullcore/run_suite.py", "team/optimizations/o1/fullcore/analyze.py",
           "team/optimizations/o1/fullcore/check_control.py", "team/scripts/artifact_guard.py",
           "team/scripts/check-vdot-run.py", "team/workloads/vdot-perf/check.py")
REQUIRED_RUNS = (
    "fullcore-parser-boundary-01", "o1-fullcore-build-01", "o1-fullcore-build-02",
    "o1-fullcore-host-01", "o1-fullcore-host-02", "o1-fullcore-launch-01.json",
    "o1-fullcore-log-audit-01", "o1-fullcore-preflight-01", "o1-fullcore-suite-01",
    "o1-generated-review-01", "o1-host-after-compile-fix", "o1-negative-abort-source-review-01",
    "o1-negative-gate-independent-review-01", "o1-negative-gate-recheck-01",
    "o1-observer-history-audit-01", "o1-option-probe-01", "o1-recheck-host-tests-01",
    "o1-recheck-probe-01", "o1-recheck-probe-02",
)
# Discover later attempts too, including failed or deliberately stopped attempts.
RUN_PREFIXES = ("fullcore-parser-", "o1-fullcore-", "o1-generated-review-", "o1-negative-",
                "o1-observer-", "o1-option-probe-", "o1-recheck-", "o1-final-")
EXTERNAL_DRAFTS = ("o1-runtime-gate-integration.patch", "o1-runtime-gate-integration-tests.patch")
SKIP_DIRS = {"aborted-build-products", "__pycache__", ".pytest_cache", ".mypy_cache", ".cache",
             "obj_dir", "objects", "waveforms", ".git", "target", "node_modules"}
BINARY_SUFFIXES = {".bin", ".elf", ".so", ".o", ".a", ".class", ".jar", ".pyc", ".pyo",
                   ".vcd", ".fst", ".vpd", ".fsdb", ".gcda", ".gcno", ".exe", ".dll"}
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".stdout", ".stderr", ".txt", ".md", ".py", ".sh", ".patch", ".diff",
                 ".java", ".scala", ".csv", ".tsv", ".toml", ".yaml", ".yml", ".c", ".cc",
                 ".cpp", ".h", ".hpp", ".s", ".ld", ".mk", ".ini", ".conf", ".xml"}
CHUNK = 1024 * 1024
LARGE_TEXT = 256 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def no_symlinks(path):
    """Reject links in every existing component, including input ancestors."""
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        require(not part.is_symlink(), "symbolic link is forbidden: " + str(part))
    return path


def sha(path):
    no_symlinks(path)
    with Path(path).open("rb") as stream:
        return stream_sha(stream)[0]


def stream_sha(stream, text=False):
    digest = hashlib.sha256()
    decoder = codecs.getincrementaldecoder("utf-8")("strict") if text else None
    count = 0
    while block := stream.read(CHUNK):
        digest.update(block)
        count += len(block)
        if decoder:
            require(b"\0" not in block, "NUL bytes in alleged text evidence")
            decoder.decode(block)
    if decoder:
        decoder.decode(b"", final=True)
    return digest.hexdigest(), count


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    no_symlinks(path)
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def save_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def verify_hashes(pins):
    require(isinstance(pins, dict) and pins, "empty hash inventory")
    for name, digest in pins.items():
        require(Path(name).is_absolute(), "hash key must be an absolute source path")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "malformed SHA: " + name)
        require(sha(name) == digest, "source hash drift: " + name)


def assert_same_bytes(left, right):
    while block := left.read(CHUNK):
        require(right.read(len(block)) == block, "round-trip byte comparison failed")
    require(right.read(1) == b"", "round-trip has extra bytes")


def named_rows(rows):
    require(isinstance(rows, list) and len(rows) == len(JOBS), "expected exactly 12 job rows")
    result = {row["name"]: row for row in rows}
    require(set(result) == set(JOBS), "duplicate, missing or unexpected job name")
    return result


def assert_concatenated(directory):
    """Byte equality without materializing large log streams in memory."""
    with (directory / "run.log").open("rb") as combined:
        for leaf in ("stderr.log", "stdout.log"):
            with (directory / leaf).open("rb") as source:
                while block := source.read(CHUNK):
                    require(combined.read(len(block)) == block, "run.log differs from stderr + stdout")
        require(combined.read(1) == b"", "extra bytes in derived run.log")


def validate_gate(recheck):
    """Validate the final recheck's identity and all original evidence bindings.

    This is archival validation, not a replacement for running recheck_suite.py.
    An original campaign failure is retained verbatim; only the strict recheck
    may establish the final verdict, as the original driver had a known gate bug.
    """
    final = read_json(recheck / "result.json")
    require(final.get("status") == "O1_OFFLINE_FULL_SUITE_RECHECK_PASS", "no final strict offline PASS")
    for field in ("whole_suite_pass", "checks_passed", "original_evidence_unchanged", "normal_reference_recovery"):
        require(final.get(field) is True, "final recheck requires true " + field)
    for field in ("completed_only", "new_emu_executed", "performance_measured"):
        require(final.get(field) is False, "incorrect recheck scope: " + field)
    require(type(final.get("emulators_executed")) is int and final["emulators_executed"] == 0, "recheck executed an emulator")
    require(final.get("campaign") == str(CAMPAIGN) and final.get("finished"), "wrong or unfinished recheck campaign")
    require(final.get("selected_jobs") == list(JOBS) and final.get("missing_jobs") == [], "recheck did not cover every job")
    audited = named_rows(final["runs"])
    state = read_json(CAMPAIGN / "campaign-state.json")
    preflight = read_json(CAMPAIGN / "preflight.json")
    pins = read_json(CAMPAIGN / "hardware-pins.json")
    original_final = read_json(CAMPAIGN / "result.json")
    require(state.get("preflight_only") is False and state.get("output") == str(CAMPAIGN), "not the actual campaign")
    require(state.get("status") in ("O1_FULLCORE_SUITE_PASS", "O1_FULLCORE_SUITE_FAILED") and state.get("finished"), "campaign still active")
    require(original_final.get("status") == state["status"] and original_final.get("finished") == state["finished"], "original final summary mismatch")
    original_rows = named_rows(original_final["runs"])
    require({p.name for p in CAMPAIGN.iterdir() if p.is_dir()} == set(JOBS), "campaign directory inventory differs")
    require(preflight.get("status") == "O1_FULLCORE_INPUTS_VERIFIED" and preflight.get("hardware_checked") is True, "missing hardware preflight")
    require(final.get("original_campaign_state_snapshot") == state and final.get("original_campaign_state_sha256") == sha(CAMPAIGN / "campaign-state.json"), "recheck did not bind the final campaign state")
    require(final.get("original_source_commit") == state["source_commit_at_start"], "checker source commit mismatch")
    require(final.get("build_source_commit") == state["build_source_commit"] == pins["source_commit"] == original_final["build_source_commit"], "build source commit mismatch")
    require(final.get("hardware_pins_sha256") == preflight["hardware_pins_sha256"] == original_final["hardware_pins_sha256"] == sha(CAMPAIGN / "hardware-pins.json") == sha(state["hardware_pins"]), "hardware pin mismatch")
    require(final.get("emu_sha256") == preflight["emu_sha256"] == sha(state["emu"]), "EMU identity changed since recheck")
    require(pins.get("source_root") == str(REPO), "unexpected hardware source root")
    audit = read_json(recheck / "input-audit.json")
    stable = audit["original_evidence_and_inputs"]
    verify_hashes(stable)
    required_stable = {str(CAMPAIGN / leaf) for leaf in ("campaign-state.json", "result.json", "preflight.json", "hardware-pins.json")}
    for name in JOBS:
        original = read_json(CAMPAIGN / name / "result.json")
        row = audited[name]
        require(original == original_rows[name] and original.get("finished"), "original job receipt differs: " + name)
        require(row == read_json(recheck / name / "result.json"), "recheck per-job summary differs: " + name)
        require(row.get("original_status") == original["status"] and row.get("finished") == original["finished"] and row.get("started") == original["started"], "job lifetime/status binding differs: " + name)
        require(row.get("files") == original.get("files") and row.get("new_emu_executed") is False, "job inputs or scope differ: " + name)
        allowed = {"HELLO_VADD_PASS"} if name == "hello-vadd" else {"EXPECTED_VDOT_HIGHBIT_REJECTION"} if name == "negative-vdot" else {"O1_CONTROL_REGRESSION_PASS", "O1_CONTROL_LEGACY_COMPLETE_HANDOFF_PENDING"} if name == "control" else {"O1_DENSE_HANDOFF_AND_WINDOWS_PASS"} if name == "dense-batch128" else {"VDOT_MATRIX_SHARD_PASS"}
        require(row.get("status") in allowed and "error" not in row, "job did not pass strict recheck: " + name)
        require(row.get("observation_status") == ("O1_PARTIAL_TRACE_AUDIT" if name == "negative-vdot" else "O1_TRACE_PASS"), "wrong trace scope: " + name)
        rc_bytes = (CAMPAIGN / name / "exit-code.txt").read_bytes()
        require(rc_bytes == (b"1\n" if name == "negative-vdot" else b"0\n"), "unexpected real exit code: " + name)
        require(type(row.get("exit_code")) is int and row["exit_code"] == original.get("exit_code") == int(rc_bytes), "recorded exit code differs: " + name)
        require(row.get("raw_logs_sha256") == original.get("raw_logs_sha256") and set(row["raw_logs_sha256"]) == set(RAW), "raw log inventory differs: " + name)
        for leaf in RAW:
            require(sha(CAMPAIGN / name / leaf) == row["raw_logs_sha256"][leaf], "raw stream changed: " + name + "/" + leaf)
        assert_concatenated(CAMPAIGN / name)
        required_stable.update(str(CAMPAIGN / name / leaf) for leaf in ("result.json", "runtime.json", "exit-code.txt") + RAW)
    require(required_stable <= set(stable), "final recheck did not bind all original receipts/raw logs")
    require(audit.get("original_driver_git_revision") == state["source_commit_at_start"], "input-audit Git revision mismatch")
    drivers = final["original_driver_files"]
    require(drivers == preflight["driver_files"] == audit["original_driver_files"] and set(drivers) == {str(REPO / p) for p in DRIVERS}, "original checker inventory differs")
    for name in DRIVERS:
        require(sha(recheck / "original-checkers" / name) == drivers[str(REPO / name)], "archived original checker mismatch: " + name)
    new = final["new_checker_files"]
    require(new == audit["new_checker_files"] and set(new) == {str(REPO / "team/optimizations/o1/audit" / p) for p in ("recheck_suite.py", "runtime_gate.py")}, "new checker inventory differs")
    for name, digest in new.items():
        require(stable.get(name) == digest and sha(recheck / "new-checkers" / Path(name).name) == digest, "strict checker snapshot mismatch")
    coverage = final.get("suite_coverage", {})
    require(coverage.get("legacy_control_complete") is True and coverage.get("handoff_from_dense") is True, "strict suite coverage incomplete")
    # Bind the gate files themselves as well as every input recorded by recheck.
    bound = dict(stable)
    for directory in (recheck,):
        for leaf in ("result.json", "input-audit.json"):
            bound[str(directory / leaf)] = sha(directory / leaf)
    return final, bound


def run_path(value):
    path = no_symlinks(value if value.is_absolute() else WORK / value)
    require(path.is_relative_to(RUNS) and path != RUNS and path.exists(), "supplement must exist inside runs/: " + str(path))
    return path


def collect_roots(args):
    for leaf in REQUIRED_RUNS:
        require((RUNS / leaf).exists(), "missing preserved historical evidence: " + leaf)
    roots = {RUNS / leaf for leaf in REQUIRED_RUNS}
    roots.update(p for p in RUNS.iterdir() if p.name.startswith(RUN_PREFIXES))
    for value in (args.final_recheck, args.final_host_tests, args.final_review, *args.include_run):
        roots.add(run_path(value))
    for value in (args.final_recheck, args.final_host_tests, args.final_review):
        path = run_path(value)
        require(path.is_dir() and any(path.glob("*.json")), "final attachment requires a directory with a JSON receipt: " + str(path))
    require(len({run_path(args.final_recheck), run_path(args.final_host_tests), run_path(args.final_review)}) == 3, "final attachments must use distinct directories")
    roots.update(WORK / p for p in EXTERNAL_DRAFTS)
    roots.add(Path(__file__).absolute())
    for path in roots:
        no_symlinks(path)
        require(path.exists(), "missing source: " + str(path))
    return sorted(p for p in roots if not any(q != p and q in p.parents for q in roots))


def inventory(roots):
    files, excluded = {}, []

    def visit(path):
        no_symlinks(path)
        mode = path.stat().st_mode
        if stat.S_ISDIR(mode):
            if path.name in SKIP_DIRS:
                excluded.append({"source": str(path), "kind": "directory", "reason": "generated build products or cache; not traversed"})
                return
            for child in sorted(path.iterdir()):
                visit(child)
            return
        require(stat.S_ISREG(mode), "special source file forbidden: " + str(path))
        if path.suffix.lower() in BINARY_SUFFIXES or path.name in {"emu", "riscv64-nemu-interpreter-so"}:
            excluded.append({"source": str(path), "kind": "file", "reason": "binary, object, bytecode or waveform excluded"})
            return
        suffix = path.suffix.lower()
        content_suffix = Path(path.stem).suffix.lower() if suffix == ".gz" else suffix
        require(content_suffix in TEXT_SUFFIXES or path.name in {"Makefile", "CMakeLists.txt"}, "unexpected evidence file type (review explicitly): " + str(path))
        rel = path.relative_to(WORK).as_posix()
        require(rel not in files, "duplicate source mapping: " + rel)
        files[rel] = path

    for path in roots:
        visit(path)
    return files, excluded


def package_file(source, target):
    before = sha(source)
    original_size = source.stat().st_size
    existing_gzip = source.suffix == ".gz"
    compress = not existing_gzip and (source.suffix in {".log", ".stdout", ".stderr"} or original_size >= LARGE_TEXT)
    target = target.with_name(target.name + ".gz") if compress else target
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "archive path collision: " + str(target))
    with source.open("rb") as stream:
        if not existing_gzip:
            stream_sha(stream, text=True)
            stream.seek(0)
        if compress:
            with target.open("xb") as sink:
                with gzip.GzipFile(filename="", mode="wb", fileobj=sink, mtime=0, compresslevel=9) as zipped:
                    shutil.copyfileobj(stream, zipped, CHUNK)
        else:
            with target.open("xb") as sink:
                shutil.copyfileobj(stream, sink, CHUNK)
    require(sha(source) == before and source.stat().st_size == original_size, "source changed while copying: " + str(source))
    if existing_gzip:
        with gzip.open(source, "rb") as raw:
            payload_sha, payload_size = stream_sha(raw, text=True)
        require(sha(target) == before, "existing gzip bytes changed")
    elif compress:
        payload_sha, payload_size = before, original_size
    else:
        payload_sha, payload_size = before, original_size
        require(sha(target) == before, "copied bytes differ")
    if compress or existing_gzip:
        with gzip.open(target, "rb") as raw:
            restored_sha, restored_size = stream_sha(raw, text=True)
        require((restored_sha, restored_size) == (payload_sha, payload_size), "gzip round trip differs: " + str(source))
        opener = gzip.open if existing_gzip else open
        with opener(source, "rb") as original, gzip.open(target, "rb") as restored:
            assert_same_bytes(original, restored)
    return target, {"source": str(source), "source_sha256": before, "source_bytes": original_size,
                    "original_sha256": payload_sha, "original_bytes": payload_size,
                    "storage": "gzip-preserved" if existing_gzip else "gzip" if compress else "identity",
                    "archive_sha256": sha(target), "archive_bytes": target.stat().st_size,
                    "compressed_sha256": sha(target) if compress or existing_gzip else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--final-recheck", required=True, type=Path)
    parser.add_argument("--final-host-tests", required=True, type=Path)
    parser.add_argument("--final-review", required=True, type=Path)
    parser.add_argument("--include-run", action="append", type=Path, default=[], help="additional run directory/file, repeated as necessary")
    args = parser.parse_args()
    no_symlinks(WORK); no_symlinks(DESTINATION)
    require(not DESTINATION.exists(), "destination already exists; never overwrite it")
    recheck = run_path(args.final_recheck)
    final, bound = validate_gate(recheck)  # No archive writes before this gate.
    roots = collect_roots(args)
    sources, excluded = inventory(roots)
    before = {str(p): sha(p) for p in sources.values()}
    require(DESTINATION.parent.is_dir(), "evidence parent directory does not exist")
    stage = Path(tempfile.mkdtemp(prefix=DESTINATION.name + ".INCOMPLETE-", dir=DESTINATION.parent))
    try:
        rows = []
        for relative, source in sorted(sources.items()):
            stored, row = package_file(source, stage / "files" / relative)
            row["archive"] = stored.relative_to(stage).as_posix()
            require(row["source_sha256"] == before[str(source)], "source changed after initial inventory")
            rows.append(row)
        save_json(stage / "file-map.json", rows)
        save_json(stage / "excluded.json", excluded)
        mapping = {row["source"]: row["archive"] for row in rows}
        campaign_gate_files = {name for name in bound if Path(name).is_relative_to(CAMPAIGN)}
        require(campaign_gate_files <= set(mapping), "not all bound campaign files were archived")
        recheck_link = mapping[str(recheck / "result.json")]
        job_table = "\n".join("| " + row["name"] + " | " + row["status"] + " |" for row in final["runs"])
        readme = ("# O1 fullcore validation evidence\n\n"
                  "This archive preserves the completed campaign and its strict offline recheck. "
                  "The verification verdict comes from the [final recheck](" + recheck_link + "). "
                  "Packaging itself runs no emulator and does not create a new validation result.\n\n"
                  "| Job | Strict offline result |\n| --- | --- |\n" + job_table + "\n\n"
                  "- Original failed/aborted attempts, partial probes and the original gate defect remain verbatim.\n"
                  "- Only the final complete recheck establishes the whole-suite verdict; partial audits do not.\n"
                  "- Negative DiffTest intentionally exits 1; its trace remains a partial audit.\n"
                  "- Dense workload windows validate handoff and window integrity, not an A/B speedup claim.\n"
                  "- Derived run.log is stderr followed by stdout; it is not cross-stream chronological evidence.\n"
                  "- External integration patches are historical drafts; inclusion does not imply application.\n"
                  "- Final host checks and review are included as supplied; their own receipts retain their scope.\n\n"
                  "Every source path, original-byte SHA, stored-byte SHA and size is recorded in file-map.json. "
                  "All .log/.stdout/.stderr files and text files at least 256 KiB use gzip with mtime=0; gzip is verified by "
                  "decompression. Existing gzip files retain their original compressed bytes. "
                  "excluded.json records excluded build products, binaries, objects, waveforms and caches. "
                  "Original evidence files are not modified.\n")
        with (stage / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(readme)
        require(collect_roots(args) == roots, "new evidence root appeared during archive")
        now_sources, now_excluded = inventory(roots)
        require(set(now_sources) == set(sources) and now_excluded == excluded, "source inventory changed during archive")
        verify_hashes(before)
        verify_hashes(bound)
        # Validate completed gate receipts again; copying never turns a partial run into PASS.
        final_after, bound_after = validate_gate(recheck)
        require(final_after == final and bound_after == bound, "final gate changed while archiving")
        payload_hashes = {p.relative_to(stage).as_posix(): sha(p) for p in sorted(stage.rglob("*")) if p.is_file()}
        manifest = {"format": "o1-evidence-archive-v1", "created": datetime.now(timezone.utc).isoformat(),
                    "archive_status": "EVIDENCE_ARCHIVE_COMPLETE", "new_emu_executed": False,
                    "final_verdict_source": str(recheck / "result.json"), "final_verdict_source_sha256": sha(recheck / "result.json"),
                    "final_verdict": final["status"], "original_source_commit": final["original_source_commit"],
                    "build_source_commit": final["build_source_commit"], "emu_sha256": final["emu_sha256"],
                    "command": [sys.executable, *sys.argv], "packager_sha256": sha(__file__),
                    "source_roots": [str(p) for p in roots], "final_host_tests": str(run_path(args.final_host_tests)),
                    "final_review": str(run_path(args.final_review)), "files": payload_hashes,
                    "mapped_file_count": len(rows), "original_total_bytes": sum(row["source_bytes"] for row in rows),
                    "stored_total_bytes": sum(row["archive_bytes"] for row in rows),
                    "source_hashes_unchanged": True, "gzip_round_trip_verified": True,
                    "performance_comparison": False,
                    "scope": "archive of existing evidence; strict recheck supplies the validation verdict"}
        save_json(stage / "archive-manifest.json", manifest)
        for relative, digest in payload_hashes.items():
            require(sha(stage / relative) == digest, "archive payload changed during finalization")
        with (stage / "archive-manifest.sha256").open("x", encoding="ascii") as stream:
            stream.write(sha(stage / "archive-manifest.json") + "  archive-manifest.json\n")
        require(not DESTINATION.exists(), "destination appeared during archive; refusing replacement")
        # mkdir reserves the final name without overwrite. It is empty and not a
        # valid archive until a same-filesystem rename atomically replaces it.
        DESTINATION.mkdir()
        os.replace(stage, DESTINATION)
        print(json.dumps({"status": "EVIDENCE_ARCHIVE_COMPLETE", "destination": str(DESTINATION),
                          "manifest_sha256": sha(DESTINATION / "archive-manifest.json"), "files": len(rows)}))
        return 0
    except BaseException as exc:
        if stage.exists():
            failure = stage / "INCOMPLETE.json"
            if not failure.exists():
                save_json(failure, {"archive_status": "INCOMPLETE", "error": repr(exc), "new_emu_executed": False})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
