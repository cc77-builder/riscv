"""Read-only O5 input readiness, never an emulator, build or T17 acceptance gate."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "team/optimizations/o2/fullcore"))
import run_suite as suite

SOURCE_PATHS = list(dict.fromkeys([*suite.live_inputs.HARDWARE,
    "team/optimizations/o2/fullcore", "team/optimizations/o5",
    "team/optimizations/o1/build_recipe.py", "team/optimizations/o1/audit/runtime_gate.py",
    "team/scripts/artifact_guard.py", "team/scripts/check-vdot-run.py", "team/workloads/vdot-perf"]))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_file(path, expected=None, role="input"):
    """Return every missing/drift finding without rewriting any source or receipt."""
    path = Path(path)
    row = dict(path=str(path), role=role, expected_sha256=expected)
    try:
        actual = sha(path)
        row.update(sha256=actual, status="OK" if expected is None or actual == expected else "DRIFT")
    except OSError as error:
        row.update(status="MISSING" if not path.exists() else "UNREADABLE", error=str(error))
    return row


def linked_reference_check(t12_root):
    actual = Path(t12_root) / "nemu/reference/build/riscv64-nemu-interpreter-so"
    required = suite.DEFAULT_T12 / "nemu/reference/build/riscv64-nemu-interpreter-so"
    return dict(status="OK" if actual.resolve() == required.resolve() else "WRONG_LINKED_REFERENCE_PATH",
                selected=str(actual.resolve()), required=str(required.resolve()),
                reason="Frozen negative wrapper binds this normal-reference absolute path; bytes alone cannot relocate it.")


def source_state(expected, root=ROOT):
    git = lambda *args: subprocess.check_output(["git", "-C", str(root), *args], text=True)
    head = git("rev-parse", "HEAD").strip()
    dirty = git("status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=all",
                "--", *SOURCE_PATHS).splitlines()
    return dict(head=head, expected_commit=expected, head_matches=head == expected,
                git_clean=not dirty, dirty_entries=dirty, checked_paths=SOURCE_PATHS,
                scope="Git HEAD/status of listed compiler/G3/O5 input paths only; ignored compiler inputs, dependency pins and native tools not verified")


def collect_inputs(t12, t14, dense, perf):
    rows = []
    paths = {
        "reference": t12 / "nemu/reference/build/riscv64-nemu-interpreter-so",
        "negative": t12 / "build-evidence/negative-reference.so",
        "flash": t12 / "repo/team/workloads/hello-vadd/build/boot-flash.bin",
        "hello": t12 / "repo/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin",
        "control": t14 / "runs/control-sweep-02/vdot-regression.bin",
    }
    for role, digest in suite.FROZEN.items():
        rows.append(inspect_file(paths[role], digest, role))

    def receipt_files(receipt_path, groups, relative_root=None):
        row = inspect_file(receipt_path, role="provenance")
        rows.append(row)
        if row["status"] != "OK":
            return
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if not isinstance(receipt, dict):
                raise ValueError("receipt must be an object")
            for group in groups:
                entries = receipt.get(group)
                if not isinstance(entries, dict) or not entries:
                    raise ValueError("missing nonempty inventory " + group)
                for name, digest in entries.items():
                    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                        raise ValueError("invalid digest in " + group)
                    path = Path(name)
                    if relative_root is not None:
                        path = relative_root / path
                    elif not path.is_absolute():
                        raise ValueError("expected absolute provenance path: " + name)
                    rows.append(inspect_file(path, digest, group))
        except (ValueError, TypeError, OSError) as error:
            row.update(status="INVALID_RECEIPT", error=str(error))

    reference = t12 / "nemu/reference"
    rows.append(inspect_file(reference / ".config", role="NEMU configuration"))
    receipt_files(reference / "build/vdot-provenance.json", ("source_sha256",), reference)
    for index, digest in enumerate(suite.MATRIX_SHA):
        base = t12 / "runs/t11-matrix-canonical"
        build, data = base / f"build-{index}", base / f"data-{index}"
        rows.append(inspect_file(build / "vdot-exceptions.bin", digest, f"matrix-{index}"))
        for name in ("manifest.json", "cases.jsonl", "exceptions.json"):
            rows.append(inspect_file(data / name, role=f"matrix-{index} corpus"))
        receipt_files(build / "workload-provenance.json",
                      ("source_sha256", "inputs_sha256", "images_sha256", "am_libraries_sha256"))
    control = t14 / "runs/control-sweep-02"
    frozen_control = ROOT / "team/evidence/t14-optimization-20261016/control-sweep/build/build.json"
    # Use the frozen inventory, never a possibly changed local receipt, to list
    # required control artifacts even when the entire local directory is absent.
    rows.append(inspect_file(control / "build.json", sha(frozen_control), "control receipt"))
    for name, digest in json.loads(frozen_control.read_text(encoding="utf-8"))["files"].items():
        rows.append(inspect_file(control / name, digest, "control artifact"))
    frozen_dense = ROOT / "team/evidence/t13-performance-20261015/images-v3/performance-d0-s06"
    for name in ("build.json", "vdot-perf.bin", "vdot-perf.elf", "data/manifest.json",
                 "data/kernels.S", "data/cases.h", "source/generate.py", "source/main.c", "source/Makefile"):
        digest = hashlib.sha256(perf.raw_bytes(frozen_dense / name)).hexdigest()
        rows.append(inspect_file(dense / name, digest, "dense frozen artifact"))
    return rows


def assess(args):
    report = dict(schema_version=1, scope="O5 inputs preparation for O2 core G3 only",
                  created_utc=datetime.now(timezone.utc).isoformat(), status="NOT_READY",
                  hardware_checked=False, emulators_executed=0, t17_complete=False,
                  compiler_inventory_checked=False, dependency_pins_checked=False,
                  native_tools_checked=False, supplements_checked=False,
                  human_acknowledgements_checked=False, findings=[])
    before = source_state(args.source_commit)
    report["source"] = before
    if not before["head_matches"]:
        report["findings"].append("SOURCE_COMMIT_MISMATCH")
    if not before["git_clean"]:
        report["findings"].append("SOURCE_GIT_DIRTY: commit the intended candidate before readiness acceptance")
    perf = suite.load_module("o5_input_window_checker", ROOT / "team/workloads/vdot-perf/check.py")
    report["files"] = collect_inputs(args.t12_root, args.t14_root, args.dense_build, perf)
    report["inventory_expansion_complete"] = all(row["status"] == "OK" for row in report["files"]
                                                 if row["role"] == "provenance")
    report["inventory_note"] = "Counts cover listed prerequisites; missing receipts prevent expansion of their transitive source/library inventories."
    report["negative_reference_binding"] = linked_reference_check(args.t12_root)
    if report["negative_reference_binding"]["status"] != "OK":
        report["findings"].append("WRONG_LINKED_REFERENCE_PATH")
    bad = [row for row in report["files"] if row["status"] != "OK"]
    report["input_counts"] = dict(required=len(report["files"]), checked=len(report["files"]) - len(bad), unavailable_or_drifted=len(bad))
    report["strict_frozen_preflight"] = dict(status="NOT_RUN", reason="prerequisite files or linked reference unavailable")
    if not bad and report["negative_reference_binding"]["status"] == "OK":
        try:
            guard = suite.load_module("o5_input_artifact_guard", ROOT / "team/scripts/artifact_guard.py")
            _, _, receipt = suite.preflight(SimpleNamespace(preflight_only=True, t12_root=args.t12_root,
                t14_root=args.t14_root, dense_build=args.dense_build), guard, perf)
            report["strict_frozen_preflight"] = dict(status="PASS", receipt=receipt)
        except Exception as error:
            report["strict_frozen_preflight"] = dict(status="FAIL", error=str(error))
    after = source_state(args.source_commit)
    report["git_state_unchanged_during_check"] = before == after
    if before != after:
        report["findings"].append("SOURCE_CHANGED_DURING_CHECK")
    report["complete_input_identity_checked"] = report["strict_frozen_preflight"]["status"] == "PASS"
    if not bad and not report["findings"] and report["strict_frozen_preflight"]["status"] == "PASS":
        report["status"] = "READY_INPUTS_ONLY"
    report["next_steps"] = [
        "Restore every listed missing/drifted original input and its provenance; preserve original absolute dependencies.",
        "Use a separate versioned source/build contract for any newly rebuilt or relocated input; do not overwrite frozen receipts.",
        "Commit the chosen candidate, rerun this input preflight with its full SHA, then verify complete compiler/dependency/native-tool contracts before building.",
        "Run fresh current-source core and supplements, then matched performance/PPA as required; independent T17 execution and actual human ACK remain separate.",
    ]
    return report


def output_path(value, root=ROOT):
    path = Path(value)
    if not path.is_absolute() or path.resolve().is_relative_to(Path(root).resolve()) or path.exists():
        raise ValueError("output must be a new absolute file outside the checkout")
    return path.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True, help="explicit full candidate Git SHA")
    parser.add_argument("--t12-root", type=Path, default=suite.DEFAULT_T12)
    parser.add_argument("--t14-root", type=Path, default=suite.DEFAULT_T14)
    parser.add_argument("--dense-build", type=Path, default=suite.DEFAULT_DENSE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", args.source_commit) is None:
        parser.error("--source-commit must be a full 40-character lowercase SHA")
    for name in ("t12_root", "t14_root", "dense_build"):
        setattr(args, name, getattr(args, name).resolve())
    destination = output_path(args.output)
    report = assess(args)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(dict(status=report["status"], output=str(destination), **report["input_counts"])))
    return 0 if report["status"] == "READY_INPUTS_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
