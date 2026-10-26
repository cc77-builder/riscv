"""Bind the independent C launcher receipt to this exact completed campaign."""
from __future__ import annotations

import hashlib
from datetime import datetime
import json
from pathlib import Path

LEAF = Path("team/optimizations/o2/integration/firstdot-v2-0f")
RUNNER = LEAF / "orchestration/run_c_independent.py"
RUNNER_SHA256 = "76353dc7a6929a0c7f3b254062b6ac7ed5ab28fce2b09659b67e6bf703b0da7b"
RECEIPT_FIELDS = {
    "contract", "hardware_identity_sha256", "source_sha256", "source_file",
    "matrix_images_sha256", "source_result", "scope", "combination_qualified", "performance_measured",
}
SCOPE = "independent ordinary C correctness; matrix qualification remains pending"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def validate_independent_receipt(combo, repo, identity_path, matrix, build, run):
    """No writes. Return deterministic input bindings for the later finalizer."""
    repo, identity_path, matrix, build, run = map(Path, (repo, identity_path, matrix, build, run))
    record_path = run / "independent-c-orchestration.json"
    record, state, cfg = read(record_path), read(run / "state.json"), read(run / "configuration.json")
    require(set(record) == RECEIPT_FIELDS, "independent C receipt field inventory differs")
    require(record["contract"] == combo.CONTRACT and record["combination_qualified"] is False and
            record["performance_measured"] is False and record["scope"] == SCOPE,
            "independent C receipt scope differs")
    repo_source = repo / RUNNER
    source = Path(record["source_file"])
    allowed_sources = {repo_source.resolve(), (run.parent / "run_c_independent.py").resolve()}
    require(source.is_absolute() and source in allowed_sources and not source.is_symlink() and
            record["source_file"] == str(source.resolve()) and
            record["source_sha256"] == RUNNER_SHA256 and sha(source) == RUNNER_SHA256 and
            not repo_source.is_symlink() and sha(repo_source) == RUNNER_SHA256,
            "independent C runner path/source differs")
    launcher_path = run.with_name(run.name + ".command.json")
    launcher = read(launcher_path)
    expected_argv = ["python3", "-B", str(source), str(repo), str(identity_path), str(matrix), str(build), str(run)]
    require(launcher["command"] == expected_argv and launcher["cwd"] == str(repo) and
            type(launcher["pid"]) is int and launcher["pid"] > 0 and
            type(launcher["child_pid"]) is int and launcher["child_pid"] > 0 and
            launcher["pid"] != launcher["child_pid"] and
            type(launcher["exit_code"]) is int and launcher["exit_code"] == 0,
            "independent C outer launcher binding differs")
    times = [datetime.fromisoformat(v) for v in
             (launcher["started"], state["started"], state["finished"], launcher["finished"])]
    require(all(t.utcoffset() is not None for t in times) and times == sorted(times),
            "independent C outer launcher chronology differs")
    launcher_stdout = launcher_path.with_suffix(".stdout.log")
    launcher_stderr = launcher_path.with_suffix(".stderr.log")
    marker = "ORDINARY_C_DONE_MATRIX_QUALIFICATION_PENDING"
    lines = launcher_stdout.read_text().splitlines()
    require(lines.count(marker) == 1 and lines[-1] == marker and launcher_stderr.is_file(),
            "independent C outer launcher completion transcript differs")
    require(record["hardware_identity_sha256"] == sha(identity_path) and
            record["matrix_images_sha256"] == sha(matrix / "images.json"),
            "independent C input identity differs")
    identity = combo.parent_identity(repo, identity_path)
    require(cfg == dict(identity["configuration"], canonical_build=str(build), run_root=str(run), source_root=str(repo)),
            "independent C configuration/build/run binding differs")
    require(record["source_result"] == state, "independent C source result differs from completed state")
    require(state["status"] == "R4_C_APPLICATION_CALLS_PASS" and
            state["contract"] == combo.upstream_c.CONTRACT and state["new_emu_runs"] == 3 and
            state["active_pid"] is None and state["active_result"] is None and
            state["performance_measured"] is False and state["whole_suite_acceptance"] is False and
            state["distinct_cases"] == 48 and state["public_functions"] == 16 and
            state["normal_case_executions"] == 96 and state["expected_negative_runs"] == 1 and
            state["normal_runs"] == 2 and isinstance(state["operation_id"], str) and state["operation_id"].strip(),
            "independent C completed-state qualification differs")
    cached = read(run / "results.json")
    require({k: v for k, v in cached.items() if k != "runs"} ==
            {k: v for k, v in state.items() if k != "finished"} and
            cached["runs"] == read(run / "completed-runs.json") and len(cached["runs"]) == 3,
            "independent C cached state/records differ")
    combo.verify_build_scope(repo, matrix, read(matrix / "images.json")["images"], identity_path)
    require(combo.library_anchor(repo, build, matrix) == read(build / "matrix-anchor.json"),
            "independent C matrix leaf anchor differs")
    require(read(build / "combination-c-build.json") ==
            {"contract": combo.CONTRACT, "adapter_files": combo.adapter_files()},
            "independent C adapter identity differs")
    paths = {
        "orchestration_receipt": record_path, "state": run / "state.json",
        "results": run / "results.json", "completed_runs": run / "completed-runs.json",
        "configuration": run / "configuration.json", "matrix_images": matrix / "images.json",
        "matrix_build_scope": matrix / "combination-build.json",
        "c_build": build / "build.json", "c_build_scope": build / "combination-c-build.json",
        "matrix_anchor": build / "matrix-anchor.json", "hardware_identity": identity_path,
        "runner": source, "repo_runner": repo_source, "outer_command": launcher_path,
        "outer_stdout": launcher_stdout, "outer_stderr": launcher_stderr,
    }
    return dict(
        status="CURRENT_FIRSTDOT_INDEPENDENT_C_RECEIPT_BOUND", contract=combo.CONTRACT,
        validator_sha256=sha(__file__),
        inputs={name: {"path": str(path), "sha256": sha(path)} for name, path in paths.items()},
        source_result_exact=True, matrix_qualification_in_receipt=False,
        original_c_processes=3, new_emu_runs=0,
    )
