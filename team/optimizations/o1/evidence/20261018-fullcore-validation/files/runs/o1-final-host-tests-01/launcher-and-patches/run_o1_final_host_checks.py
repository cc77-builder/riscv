#!/usr/bin/env python3
"""Run final host tests after applying both O1 runtime-gate integration patches.

Prepared externally; creating this file executes no tests and changes no source.
Later invocation from the work root:
    python3 -B run_o1_final_host_checks.py
A retry must use a new output, e.g. --output runs/o1-final-host-tests-02.
No emulator or hardware build is launched. Test discovery imports
 test_elaboration_options.py without invoking its standalone Java probe main.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

WORK = Path(__file__).absolute().parent
REPO = WORK / "repo"
RUNS = WORK / "runs"
DEFAULT_OUTPUT = RUNS / "o1-final-host-tests-01"
GROUPS = ("fullcore", "audit")
HELPERS = ("team/scripts/artifact_guard.py", "team/scripts/check-vdot-run.py",
           "team/workloads/vdot-perf/check.py")
PATCHES = (WORK / "o1-runtime-gate-integration.patch", WORK / "o1-runtime-gate-integration-tests.patch")


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def no_symlink(path):
    path = Path(os.path.abspath(path))
    require(all(not p.is_symlink() for p in (path, *path.parents)), "symlink forbidden: " + str(path))
    return path


def sha(path):
    no_symlink(path)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def source_inventory():
    paths = {REPO / name for name in HELPERS}
    for group in GROUPS:
        directory = REPO / "team/optimizations/o1" / group
        no_symlink(directory)
        paths.update(directory.rglob("*.py"))
        require(any(directory.glob("test_*.py")), "missing unittest files: " + group)
    paths.update(PATCHES)
    paths.add(Path(__file__).absolute())
    return {str(p): sha(p) for p in sorted(paths)}


def run_command(label, command, output, env, commands):
    directory = output / label
    directory.mkdir()
    record = {"label": label, "command": command, "cwd": str(REPO), "started_utc": utc()}
    save(directory / "command.json", record)
    try:
        with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
            record["exit_code"] = subprocess.run(command, cwd=REPO, env=env, stdout=stdout, stderr=stderr, check=False).returncode
    except OSError as error:
        record.update(exit_code=None, error=repr(error))
    record["finished_utc"] = utc()
    if type(record.get("exit_code")) is int:
        with (directory / "exit-code.txt").open("x", encoding="ascii") as stream:
            stream.write(str(record["exit_code"]) + "\n")
    record["raw_sha256"] = {p.name: sha(p) for p in sorted(directory.iterdir()) if p.name in ("stdout.log", "stderr.log", "exit-code.txt")}
    record["passed"] = record.get("exit_code") == 0 and "error" not in record
    save(directory / "result.json", record)
    commands.append(record)
    return record


def read_stdout(output, label):
    return (output / label / "stdout.log").read_text(encoding="utf-8").strip()


def evaluate_unittest(record, output):
    stderr = (output / record["label"] / "stderr.log").read_text(encoding="utf-8")
    summaries = re.findall(r"^Ran (\d+) tests? in [^\r\n]+$", stderr, flags=re.M)
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    count = int(summaries[0]) if len(summaries) == 1 else None
    # Empty discovery, skipped-only or unexpected-success suites cannot establish
    # this final gate. The exact count is observed, never hard-coded.
    passed = record["passed"] and count is not None and count > 0 and bool(lines) and lines[-1] == "OK"
    return {"name": record["label"], "status": "HOST_TEST_PASS" if passed else "HOST_TEST_FAILED",
            "exit_code": record.get("exit_code"), "tests_run": count, "unittest_final_line": lines[-1] if lines else None,
            "summary_count": len(summaries), "raw_sha256": record["raw_sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = no_symlink(args.output if args.output.is_absolute() else WORK / args.output)
    require(output.parent == RUNS and output.name.startswith("o1-final-host-tests-"), "output must be a direct runs/o1-final-host-tests-* directory")
    require(not output.exists(), "output exists; keep old evidence and choose a new suffix")
    require(REPO.is_dir() and RUNS.is_dir(), "missing repository or runs directory")
    output.mkdir()
    started = utc()
    commands, tests, errors = [], [], []
    before, after = None, None
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", PYTHONHASHSEED="0")
    result = {"status": "O1_FINAL_HOST_CHECKS_FAILED", "started_utc": started, "cwd": str(REPO),
              "output": str(output), "invocation": [sys.executable, *sys.argv],
              "new_emu_executed": False, "hardware_build_executed": False,
              "scope": "host unittest groups plus read-only integration-patch preflight; no hardware/fullcore validation claim",
              "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONHASHSEED": "0", "PYTHONPATH": None},
              "python_executable": sys.executable, "python_runtime_version": sys.version,
              "commands": commands, "test_groups": tests}
    try:
        before = source_inventory()
        save(output / "source-before.json", before)
        # Preserve exact launcher/patch input bytes alongside their SHA receipts.
        snapshot = output / "launcher-and-patches"
        snapshot.mkdir()
        for path in (Path(__file__).absolute(), *PATCHES):
            body = path.read_bytes()
            require(hashlib.sha256(body).hexdigest() == before[str(path)], "launcher/patch changed before snapshot")
            (snapshot / path.name).write_bytes(body)
        for label, command in (
            ("python-version", [sys.executable, "-VV"]),
            ("git-head-before", ["git", "rev-parse", "HEAD"]),
            ("git-status-before", ["git", "status", "--porcelain=v1", "--untracked-files=all"]),
        ):
            row = run_command(label, command, output, env, commands)
            if not row["passed"]:
                errors.append(label + " failed")
        for index, patch in enumerate(PATCHES, 1):
            # Reverse --check is read-only and proves the expected integration
            # hunks are already present. This launcher never applies a patch.
            row = run_command("integration-patch-" + str(index), ["git", "apply", "--reverse", "--check", str(patch)], output, env, commands)
            if not row["passed"]:
                errors.append("integration patch is not applied cleanly: " + str(patch))
        for group in GROUPS:
            command = [sys.executable, "-B", "-m", "unittest", "discover", "-s",
                       "team/optimizations/o1/" + group, "-p", "test_*.py", "-v"]
            row = run_command(group, command, output, env, commands)
            check = evaluate_unittest(row, output)
            tests.append(check)
            if check["status"] != "HOST_TEST_PASS":
                errors.append(group + " unittest group failed or lacked a clean nonempty summary")
    except BaseException as error:
        errors.append(repr(error))
    finally:
        try:
            after = source_inventory()
            save(output / "source-after.json", after)
            require(before is not None and after == before, "source inventory or SHA changed during tests")
        except BaseException as error:
            errors.append("source-after check: " + repr(error))
        for label, command in (
            ("git-head-after", ["git", "rev-parse", "HEAD"]),
            ("git-status-after", ["git", "status", "--porcelain=v1", "--untracked-files=all"]),
        ):
            try:
                row = run_command(label, command, output, env, commands)
                if not row["passed"]:
                    errors.append(label + " failed")
            except BaseException as error:
                errors.append(label + ": " + repr(error))
        try:
            head_before = read_stdout(output, "git-head-before")
            head_after = read_stdout(output, "git-head-after")
            require(re.fullmatch(r"[0-9a-f]{40}", head_before) and head_before == head_after, "Git HEAD changed or was unavailable")
            result.update(git_head_before=head_before, git_head_after=head_after)
            result["python_version_output"] = read_stdout(output, "python-version")
        except BaseException as error:
            errors.append("version/HEAD check: " + repr(error))
        require(len(tests) <= 2, "internal duplicate test-group result")
        if {row["name"] for row in tests} != set(GROUPS):
            errors.append("both unittest groups did not finish")
        result.update(finished_utc=utc(), source_sha256_before=before, source_sha256_after=after,
                      source_unchanged=before is not None and before == after, errors=errors)
        result["status"] = "O1_FINAL_HOST_CHECKS_PASS" if not errors else "O1_FINAL_HOST_CHECKS_FAILED"
        result["exit_code"] = 0 if not errors else 1
        result["total_tests_run"] = sum(row["tests_run"] or 0 for row in tests)
        save(output / "result.json", result)
        (output / "exit-code.txt").write_text(str(result["exit_code"]) + "\n", encoding="ascii")
    print(json.dumps({key: result[key] for key in ("status", "output", "total_tests_run", "source_unchanged", "exit_code")}))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
