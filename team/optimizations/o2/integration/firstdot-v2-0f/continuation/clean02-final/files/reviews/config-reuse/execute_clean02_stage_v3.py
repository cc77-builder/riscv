"""Explicit external clean-02 import/final-check helper. Default is read-only readiness.
Does not launch compilers, EMU, background waiters, Git staging or commits.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
sys.dont_write_bytecode = True

CONTRACT = "clean02-config-reuse-stage-executor-v3-strict-c-retry"
REVIEW_CONTRACT = "clean02-config-reuse-root-review-v3-strict-c-retry"
REVIEW_SCOPE = "clean02-config-reuse-8x32-d0-five-process-with-fullcore-wall-clock-limit"
REVIEW_DECISION = "APPROVE_BOUNDED_PROBE_WITH_SOURCE_BOUND_FULLCORE_CAPACITY"
COMBO = "team/optimizations/o2/integration/firstdot-v2-0f"
S3 = "team/optimizations/o2/r2-config-reuse"
SOURCE = "c823a8786e052c6e26f6915563c42b6d730dd8e3"
EMU = "acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9"
NEMU = "62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca"
ADAPTERS = {"probe.py", "raw_audit.py", "CONTRACT.md", "import-manifest.json"}
POST_JOBS = ("fullcore_physical", "fullcore_pack", "fullcore_bytes",
             "fullcore_archive_audit", "finalize_c", "combination_audit", "full_comparison")
COMMANDS = []

LIMITED_CONTRACT = "zjh-current-clean-fullcore-archive-v2-wall-clock-limited"
CAPACITY_STATUS = "CURRENT_CLEAN_SOURCE_BOUND_CAPACITY_PASS_WALL_CLOCK_LIMITED"
CLOSURE_SHA = "e118d4a02967ac4da225d58502aac2eb6c39c47b039ec4dea167db57b19c0320"
CAPACITY_CASE_SHA = "a48cbceada7c955293e22aefb9e9e9c9e03a3a7a00efcc78d9321820197d968e"
AUDITOR_FILES = {
    "current_clean_archive_v2.py":"805682ac64423eb5416a6138f18a147992ce2c9b6c78fa838a33a0e118f5e346",
    "capacity_proof.py":"bd3c284d4b0291617fa1bc927acbf6cb7c40ec7b87a323607d1526d7562da5e8",
    "runtime-source-lock.json":"91ab1cadc72644177e64387b89a318c1bc646a41fbfd178d254a5fb596e1567c",
    "exact-case.json":CAPACITY_CASE_SHA,
}
LIMITED_FLAGS = dict(wall_clock_capacity="FAIL",source_bound_worker_capacity="PASS",
    os_monotonic_capacity_measured=False,clock_cause="UNCONFIRMED",
    recorded_peak_overlapping_intervals=4,source_bound_max_workers=3,
    exact_anomaly_microseconds=80119,performance_measured=False)


class GateError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise GateError(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(262144), b""):
            h.update(chunk)
    return h.hexdigest()

def read(path, limit=8 * 1024 * 1024):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "missing/nonregular JSON: " + str(path))
    require(path.stat().st_size <= limit, "unexpectedly large metadata JSON: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))

def save_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def absent(path):
    require(not Path(path).exists() and not Path(path).is_symlink(), "preserve existing path: " + str(path))

def stamp(value):
    t = datetime.fromisoformat(value)
    require(t.utcoffset() is not None, "timezone missing")
    return t

def field(value, key):
    for part in key.split("."):
        value = value[part]
    return value

def git(repo, *args):
    argv = ["git", "-C", str(repo), *args]
    run = subprocess.run(argv, capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    COMMANDS.append(dict(command=argv, exit_code=run.returncode,
        stdout=run.stdout.decode("utf-8", "replace"), stderr=run.stderr.decode("utf-8", "replace")))
    require(run.returncode == 0, "read-only Git command failed: " + repr(argv))
    return run.stdout

def validate_plan(plan):
    require(plan.get("contract") == "clean02-config-reuse-launch-plan-v3-strict-c-retry"
            and plan.get("status") == "PLAN_ONLY_NOT_EXECUTED", "unsupported launch plan")
    paths = {key: Path(value) for key, value in plan["paths"].items()}
    clean, repo, out = paths["clean"], paths["repo"], paths["output_root"]
    require(clean.name == "clean-02" and repo == clean/"checkout/source", "wrong clean source")
    require(out.parent == paths["work"] and out != clean and not out.is_relative_to(clean)
            and not clean.is_relative_to(out), "output root overlaps qualified clean input")
    require(paths["adapter"] == out/"adapter" and paths["build"] == out/"build-01"
            and paths["run"] == out/"run-01" and paths["audit"] == out/"audit-01.json",
            "unexpected probe output layout")
    require(Path(plan["identity"]["path"]) == clean/"identity/current.json"
            and plan["source_commit"] == SOURCE and plan["identity"]["emu_sha256"] == EMU
            and plan["identity"]["reference_sha256"] == NEMU, "selected identity differs")
    require(paths["matrix_build"] == clean/"matrix-build-01"
            and paths["matrix_run"] == clean/"matrix-run-01", "matrix selection differs")
    imp = plan["source_import"]
    require(imp["upstream_ref"] == "fcf4a11fc569cb2a8fcb4e18d96ec2764b228557"
            and len(imp["new_files"]) == imp["new_file_count"] == 26
            and len(imp["dependencies_verify_only"]) == imp["dependency_count"] == 39,
            "26+39 source closure required")
    names = []
    for row in imp["new_files"] + imp["dependencies_verify_only"]:
        rel = Path(row["path"])
        require(not rel.is_absolute() and ".." not in rel.parts and ".git" not in rel.parts,
                "unsafe source path")
        require(type(row["bytes"]) is int and row["bytes"] >= 0
                and re.fullmatch("[0-9a-f]{64}", row["sha256"]), "invalid source identity")
        names.append(row["path"])
    require(len(names) == len(set(names)), "duplicate source path")
    require(all(Path(row["path"]).is_relative_to(Path(S3)) for row in imp["new_files"]), "new files escape S3")
    require(set(plan["adapter_copy"]["files"]) == ADAPTERS
            and Path(plan["adapter_copy"]["destination"]) == paths["adapter"], "adapter scope differs")
    resource = plan["resource"]
    require(resource["shape"] == [8, 32] and resource["dataset"] == 0 and resource["shard"] == 3
            and resource["target_emu_processes"] == 5 and resource["images"] == 2
            and resource["normal_all_windows"] == 96 and resource["formal_windows"] == 32,
            "bounded five-process scope differs")
    require(len(plan["release_gate"]["json"]) == 8 and plan["release_gate"]["all_required"] is True,
            "eight release results required")
    require(plan["runtime_contract"] == "zjhwork-clean-config-reuse-8x32-d0-probe-v2"
            and plan["fullcore_limited_audit"]["contract"] == LIMITED_CONTRACT
            and plan["fullcore_limited_audit"]["runtime_closure"]["sha256"] == CLOSURE_SHA,
            "exact limited fullcore and v2 probe contracts required")
    control = plan["postprocess_control"]
    require(Path(control["plan"]) == paths["work"]/"clean-02-postbuild-plan-v3.json"
            and Path(control["driver"]) == paths["work"]/"finish_clean_validation_v3.py",
            "postprocess v2 controller selection differs")
    return paths

def completed_command(path, expected, repo):
    value = read(path)
    require(value.get("command") == expected and value.get("cwd") == str(repo), "command/cwd binding: " + str(path))
    require(type(value.get("exit_code")) is int and value["exit_code"] == 0
            and stamp(value["started"]) <= stamp(value["finished"]), "command is not terminal exit zero: " + str(path))
    for name in ("pid", "child_pid"):
        require(type(value.get(name)) is int and value[name] > 0, "missing actual process ID")
    return sha(path)


def exact_fields(value, expected, message):
    require(all(type(value.get(k)) is type(v) and value.get(k) == v for k,v in expected.items()),message)

def validate_limited_proof(binding, case):
    exact_fields(binding, dict(status="CURRENT_CLEAN_PROCESS_RECEIPTS_PASS_WALL_CLOCK_LIMITED",
        source_new_emu_runs=14,new_emu_runs=0,negative_recovery_same_image=True,**LIMITED_FLAGS),
        "capacity binding must retain all limitations")
    proof = binding["source_bound_capacity_proof"]
    exact_fields(proof, dict(status=CAPACITY_STATUS,source_new_emu_runs=14,new_emu_runs=0,
        jobs=3,max_workers=3,recorded_peak=4,wall_clock_capacity="FAIL",
        source_bound_worker_capacity="PASS",os_monotonic_capacity_measured=False,
        clock_cause="UNCONFIRMED",exact_anomaly=case["anomaly"],exact_case_sha256=CAPACITY_CASE_SHA,
        original_v1_failure="FAIL_PRESERVED",original_wall_gate_verdict_preserved=True,
        timestamps_modified=False,records_reordered=False,tolerance_applied=False,
        semantic_raw_audit_granted=False), "source-bound proof is not the exact limited case")
    require(proof["evidence_inputs"] == case["files"]
            and proof["source_sha256"] == case["source_files"]
            and proof["original_failure_receipt_sha256"] == case["files"][case["original_failure_command"]]
            and proof["original_post_state_sha256"] == case["files"][case["original_post_state"]]
            and proof["controller_stdout_sha256"] == case["files"][case["outer_stdout"]]
            and len(proof["records"]) == 14 and set(proof["records"]) == set(case["expected_names"]),
            "source-bound proof evidence/failure/record closure differs")
    return proof

def capacity_gate_metadata(plan, values, physical, live_physical):
    """Read the bounded four-source/71-input proof closure, never scan a tree."""
    selection=plan["fullcore_limited_audit"]
    paths=plan["paths"];clean=Path(paths["clean"]);work=Path(paths["work"])
    folder=work/"reviews/clean-fullcore-audit-v2"
    closure_path=folder/"runtime-closure.json"
    closure=read(closure_path)
    require(sha(closure_path)==CLOSURE_SHA
            and selection["runtime_closure"]==dict(path=str(closure_path),sha256=CLOSURE_SHA,files=closure["files"])
            and closure["contract"]=="clean-fullcore-v2-runtime-closure-v1"
            and closure["files"]=={str(folder/name):digest for name,digest in AUDITOR_FILES.items()},
            "limited auditor runtime closure differs")
    for name,digest in closure["files"].items():
        require(Path(name).is_file() and not Path(name).is_symlink() and sha(name)==digest,
                "limited auditor source changed")
    case=read(folder/"exact-case.json")
    require(case["schema"]=="current-clean-exact-wall-capacity-case-v1"
            and case["repo"]==paths["repo"] and case["run"]==str(clean/"fullcore-run-01")
            and case["source_commit"]==plan["source_commit"] and case["emu_sha256"]==plan["identity"]["emu_sha256"]
            and case["jobs"]==3 and case["recorded_peak"]==4 and case["source_new_emu_runs"]==14
            and case["anomaly"]["microseconds"]==80119 and len(case["files"])==71,
            "only the fixed 80119us case is supported")
    require(sum(Path(name).stat().st_size for name in case["files"])<8*1024*1024,
            "exact case unexpectedly exceeds bounded metadata budget")
    for name,digest in case["files"].items():
        require(Path(name).is_absolute() and Path(name).is_file() and not Path(name).is_symlink()
                and sha(name)==digest,"fixed capacity evidence changed: "+name)
    failed=selection["preserved_failed_attempt"]
    required_failures={str(work/"clean-02-postbuild-plan.json"),str(work/"finish_clean_validation.py"),
        str(clean/"postprocess-01/state.json"),str(clean/"fullcore-physical-01.command.json"),
        str(clean/"fullcore-physical-01.command.stdout.log"),str(clean/"fullcore-physical-01.command.stderr.log")}
    require(set(failed)==required_failures,"failure evidence inventory differs")
    for name,digest in failed.items():
        require(Path(name).is_file() and not Path(name).is_symlink() and sha(name)==digest
                and (name not in case["files"] or case["files"][name]==digest),
                "v1 failure provenance changed")
    failure=read(case["original_failure_command"]);post=read(case["original_post_state"])
    require(type(failure["exit_code"]) is int and failure["exit_code"]==1
            and post["status"]=="FAILED" and post["commands_started"]==1
            and len(post["stages"])==1 and post["stages"][0]["name"]=="fullcore_physical"
            and post["stages"][0]["exit_code"]==1
            and "recorded concurrency exceeds worker budget" in Path(case["original_failure_stderr"]).read_text(),
            "original v1 failure has been relabelled or lost")
    binding_paths=[clean/"fullcore-physical-02/process-bindings.json",
                   clean/"fullcore-archive-audit-02/process-bindings.json"]
    bindings=[read(path) for path in binding_paths]
    require(bindings[0]==bindings[1],"physical/live capacity proofs differ")
    proof=validate_limited_proof(bindings[0],case)
    for receipt,directory,binding_path in zip((physical,live_physical),
            (clean/"fullcore-physical-02",clean/"fullcore-archive-audit-02"),binding_paths):
        exact_fields(receipt,dict(contract=LIMITED_CONTRACT,**LIMITED_FLAGS),"limited physical flags missing")
        require(receipt["process_bindings_sha256"]==sha(binding_path)
                and receipt["raw_result_sha256"]==sha(directory/"results.json")
                and receipt["auditor_sha256"]==AUDITOR_FILES["current_clean_archive_v2.py"]
                and receipt["capacity_source_sha256"]==AUDITOR_FILES["capacity_proof.py"]
                and receipt["capacity_case_sha256"]==CAPACITY_CASE_SHA,
                "physical limited proof/source/raw-result binding differs")
    for relative in ("fullcore-pack-02.json","fullcore-bytes-02.json",
                     "fullcore-archive-audit-02/archive-live-recheck.json"):
        exact_fields(values[str(clean/relative)],dict(contract=LIMITED_CONTRACT,new_emu_runs=0,**LIMITED_FLAGS),
                     "limited archive flags missing")
    return dict(failed_attempts=failed,
        fullcore_audit_runtime=selection["runtime_closure"],
        fullcore_capacity_qualification=dict(contract=LIMITED_CONTRACT,
            proof_status=proof["status"],exact_case_sha256=CAPACITY_CASE_SHA,
            exact_anomaly=case["anomaly"],evidence_inputs=case["files"],
            proof_files={str(path):sha(path) for path in binding_paths},
            original_v1_failure="FAIL_PRESERVED",**LIMITED_FLAGS))



def c_retry_metadata(plan, post_plan, post):
    clean, repo = Path(plan["paths"]["clean"]), Path(plan["paths"]["repo"])
    retry = plan["retry_evidence"]
    require(retry["C_chronology_contract_relaxed"] is False and retry["old_C_original_processes"] == 3
            and retry["selected_c_run"] == str(clean/"c-run-02")
            and retry["previous_c_run"] == str(clean/"c-run-01"), "C retry scope differs")
    require(retry["preserved"] == post_plan["preserved_c_failed_attempt"]
            and retry["unchanged_semantic_sources"] == post_plan["frozen_semantic_source_files"],
            "C retry provenance maps differ")
    for path,digest in retry["preserved"].items():
        require(Path(path).is_file() and not Path(path).is_symlink() and sha(path) == digest, "preserved C failure changed: " + path)
    expected_sources = {str(repo/COMBO/rel) for rel in
        ("orchestration/finalize_c.py","audit/audit_combination.py","audit/orchestration_receipt.py","reproduction/compare_reproduction.py")}
    require(set(retry["unchanged_semantic_sources"]) == expected_sources, "strict C semantic source inventory")
    for path,digest in retry["unchanged_semantic_sources"].items():
        require(sha(path) == digest and post["source_files"].get(path) == digest, "strict C semantic source changed")
    prior = read(clean/"postprocess-02/state.json")
    failure = read(clean/"finalize-c-02.command.json")
    require(prior["status"] == "FAILED" and prior["commands_started"] == 5
            and len(prior["stages"]) == 5 and prior["stages"][-1]["name"] == "finalize_c"
            and prior["stages"][-1]["exit_code"] == failure["exit_code"] == 1
            and "independent C outer launcher chronology differs" in (clean/"finalize-c-02.command.stderr.log").read_text(),
            "original strict C failure must remain failed")
    old_c = read(clean/"c-run-01/state.json")
    require(old_c["status"] == "R4_C_APPLICATION_CALLS_PASS" and old_c["new_emu_runs"] == 3,
            "original C functional facts changed")
    old_outer = read(clean/"c-run-01.command.json")
    delta = stamp(old_c["finished"]) - stamp(old_outer["finished"])
    require(delta.total_seconds() == 2.455386, "original C clock observation differs")
    require(post_plan["reused_fullcore_stages"] == post["stages"][:4],
            "completed fullcore prefix differs")
    for old,new in zip(prior["stages"][:4],post["stages"][:4]):
        require(new.get("reused") is True and {k:v for k,v in new.items() if k != "reused"} == old
                and old["exit_code"] == 0, "reused fullcore result was altered")
    require(all(row.get("reused") is False for row in post["stages"][4:]), "new postprocess stages mislabeled")
    stage = post_plan["stages"]["ordinary_c"]
    require(stage["receipt"] == str(clean/"c-run-02.command.json")
            and stage["command"][-1] == str(clean/"c-run-02"), "fresh C selection required")
    selected = read(clean/"c-run-02/state.json")
    require(selected["status"] == "R4_C_APPLICATION_CALLS_PASS" and selected["new_emu_runs"] == 3
            and selected["active_pid"] is None and selected["active_result"] is None,
            "selected strict C run incomplete")
    for path,digest in post_plan["reused_fullcore_evidence"].items():
        require(sha(path) == digest and post["source_files"].get(path) == digest, "reused fullcore proof drift")
    require(all(post["source_files"].get(path)==digest for path,digest in retry["preserved"].items()),
            "postprocessor did not bind prior C failure")
    return dict(selected_c_run=str(clean/"c-run-02"),selected_c_state_sha256=sha(clean/"c-run-02/state.json"),
        selected_c_receipt_sha256=sha(clean/"c-run-02.command.json"),selected_c_original_processes=3,
        prior_c_run=str(clean/"c-run-01"),prior_c_original_processes=3,
        prior_c_functional_status="PASS",prior_c_outer_chronology="FAIL_PRESERVED",
        prior_anomaly_seconds=2.455386,selected_C_chronology_contract="UNCHANGED_STRICT",
        preserved_failed_attempt=retry["preserved"],unchanged_semantic_sources=retry["unchanged_semantic_sources"],
        reused_fullcore_postprocess_commands=4,new_postprocess_commands=3)


def gate_metadata(plan):
    """Small named results and command receipts only; no source-tree or artifact inventory walk."""
    paths = plan["paths"]; clean, repo = Path(paths["clean"]), Path(paths["repo"])
    values, gates = {}, {}
    for gate in plan["release_gate"]["json"]:
        path = Path(gate["path"])
        value = read(path)
        require(all(field(value, key) == expected for key, expected in gate["expected"].items()),
                "release status/count/identity mismatch: " + str(path))
        values[str(path)] = value
        gates[str(path)] = sha(path)
    strict_statuses = {
        "fullcore-run-01/state.json":"CURRENT_CLEAN_FULLCORE_PASS",
        "fullcore-physical-02/current-archive-physical.json":"CURRENT_CLEAN_PHYSICAL_RAW_AUDIT_PASS_WALL_CLOCK_LIMITED",
        "fullcore-pack-02.json":"CURRENT_CLEAN_ARCHIVE_BYTES_SEALED_WALL_CLOCK_LIMITED",
        "fullcore-bytes-02.json":"CURRENT_CLEAN_ARCHIVE_BYTES_ONLY_PASS_WALL_CLOCK_LIMITED",
        "fullcore-archive-audit-02/archive-live-recheck.json":"CURRENT_CLEAN_ARCHIVE_LIVE_RAW_AUDIT_PASS_WALL_CLOCK_LIMITED",
        "matrix-run-01/state.json":"CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS",
        "combination-audit-03/state.json":"CURRENT_FIRSTDOT_RAW_RECOMPUTATION_AND_ARCHIVE_PASS",
        "full-reproduction-comparison-03.json":"CURRENT_CLEAN_PROGRAMS_AND_ALL_WINDOWS_EQUAL"}
    require(all(values[str(clean/name)]["status"] == expected
                for name,expected in strict_statuses.items()), "fixed gate status failed")
    require(values[str(clean/"matrix-run-01/state.json")]["new_emu_runs"] == 33,
            "full clean matrix requires exactly 33 processes")
    expected_paths = {
        clean/"fullcore-run-01/state.json", clean/"fullcore-physical-02/current-archive-physical.json",
        clean/"fullcore-pack-02.json", clean/"fullcore-bytes-02.json",
        clean/"fullcore-archive-audit-02/archive-live-recheck.json", clean/"matrix-run-01/state.json",
        clean/"combination-audit-03/state.json", clean/"full-reproduction-comparison-03.json"}
    require(set(map(Path, gates)) == expected_paths, "release result inventory differs")
    identity_path = Path(plan["identity"]["path"])
    identity = read(identity_path)
    require(sha(identity_path) == plan["identity"]["sha256"]
            and identity["source_commit"] == plan["source_commit"]
            and identity["contract"] == "zjhwork-0f-firstdot-v2-clean-identity-v1"
            and identity["hardware_profile"]["emu_sha256"] == plan["identity"]["emu_sha256"]
            and identity["reference_sha256"] == plan["identity"]["reference_sha256"]
            and identity["configuration"]["hardware_source"] == str(repo), "actual clean identity mismatch")
    physical = values[str(clean/"fullcore-physical-02/current-archive-physical.json")]
    result_sha = sha(clean/"fullcore-run-01/results.json")
    require(sha(clean/"fullcore-run-01/identity.json") == plan["identity"]["sha256"]
            and physical["identity_sha256"] == plan["identity"]["sha256"]
            and physical["source_run"] == str(clean/"fullcore-run-01")
            and physical["source_result_sha256"] == result_sha and physical["source_new_emu_runs"] == 14
            and physical["new_emu_runs"] == 0,
            "fullcore physical/source binding")
    manifest = clean/"fullcore-archive-02/archive-manifest.json"
    manifest_sha = sha(manifest)
    pack, byte, live = [values[str(clean/name)] for name in
        ("fullcore-pack-02.json", "fullcore-bytes-02.json", "fullcore-archive-audit-02/archive-live-recheck.json")]
    require(all(row["archive_manifest_sha256"] == manifest_sha for row in (pack, byte, live))
            and type(pack["files"]) is int and pack["files"] > 0
            and pack["files"] == byte["files"] == live["files"], "fullcore archive receipt linkage")
    live_physical_path = clean/"fullcore-archive-audit-02/current-archive-physical.json"
    live_physical = read(live_physical_path)
    require(live["raw_audit_receipt_sha256"] == sha(live_physical_path)
            and live_physical["status"] == "CURRENT_CLEAN_PHYSICAL_RAW_AUDIT_PASS_WALL_CLOCK_LIMITED"
            and live_physical["source_result_sha256"] == result_sha
            and live_physical["identity_sha256"] == plan["identity"]["sha256"]
            and live_physical["source_run"] == str(clean/"fullcore-run-01")
            and live["source_new_emu_runs"] == 14 and live["new_emu_runs"] == 0, "archive/live physical chain")
    capacity_metadata = capacity_gate_metadata(plan, values, physical, live_physical)
    comparison = values[str(clean/"full-reproduction-comparison-03.json")]
    combined = values[str(clean/"combination-audit-03/state.json")]
    require(comparison["identities"]["clean"] == plan["identity"]["sha256"]
            and comparison["identities"]["clean_emu"] == plan["identity"]["emu_sha256"]
            and comparison["windows"]["compared_windows"] == 768
            and combined["source_commit"] == plan["source_commit"]
            and combined["emu_sha256"] == plan["identity"]["emu_sha256"]
            and len(comparison["audits"]) == 2
            and comparison["audits"][1]["audit_sha256"] == gates[str(clean/"combination-audit-03/state.json")]
            and comparison["audits"][1]["status"] == combined["status"]
            and combined["original_emu_processes"] == 36
            and combined["matrix_original_emu_processes"] == 33 and combined["c_original_emu_processes"] == 3
            and combined["formal_windows"] == 384 and combined["c_normal_case_executions"] == 96,
            "comparison/combined audit binding or counts")
    post_plan_path = Path(paths["work"])/"clean-02-postbuild-plan-v3.json"
    post_plan = read(post_plan_path)
    control = plan["postprocess_control"]
    require(sha(post_plan_path) == control["plan_sha256"]
            and post_plan_path == Path(control["plan"])
            and sha(control["driver"]) == control["driver_sha256"]
            and post_plan["contract"] == "clean-02-postbuild-plan-v3-strict-c-retry"
            and post_plan["external_runtime_closure"] == plan["fullcore_limited_audit"]["runtime_closure"]
            and post_plan["preserved_failed_attempt"] == capacity_metadata["failed_attempts"],
            "postprocess v2 plan/driver/limited runtime/failure provenance differs")
    require(post_plan["repo"] == str(repo) and post_plan["identity"] == str(identity_path), "postbuild selection")
    commands = {}
    for name in ("fullcore", "matrix", "ordinary_c"):
        stage = post_plan["stages"][name]
        commands[stage["receipt"]] = completed_command(stage["receipt"], stage["command"], repo)
    for name in POST_JOBS:
        path = clean/(name.replace("_", "-")+("-02.command.json" if name in POST_JOBS[:4] else "-03.command.json"))
        require(post_plan["postprocess_receipts"][name] == str(path), "postprocess receipt path differs")
        commands[str(path)] = completed_command(path, post_plan["stages"][name], repo)
    post_path = clean/"postprocess-03/state.json"
    post = read(post_path)
    require(post["contract"] == "clean-postprocess-v3-strict-c-retry"
            and post["source_sha256"] == control["driver_sha256"]
            and post["source_files"][control["driver"]] == control["driver_sha256"]
            and post["status"] == "COMMANDS_EXIT_ZERO_REVIEW_PENDING" and post.get("active") is None
            and post["commands_started"] == 3 and post["reused_commands"] == 4 and len(post["stages"]) == len(POST_JOBS)
            and stamp(post["started"]) <= stamp(post["finished"]), "postprocess still active or incomplete")
    require(post["plan_sha256"] == sha(post_plan_path), "postprocess plan drift")
    runtime = plan["fullcore_limited_audit"]["runtime_closure"]
    expected_runtime = {runtime["path"]: runtime["sha256"], str(post_plan_path): sha(post_plan_path)}
    expected_runtime.update(runtime["files"])
    expected_runtime.update(capacity_metadata["failed_attempts"])
    require(all(post["source_files"].get(path) == digest for path,digest in expected_runtime.items()),
            "postprocess did not bind exact limited runtime and original failure chain")

    retry_provenance = c_retry_metadata(plan, post_plan, post)
    for row, name in zip(post["stages"], POST_JOBS):
        expected = clean/(name.replace("_", "-")+("-02.command.json" if name in POST_JOBS[:4] else "-03.command.json"))
        require(row["name"] == name and type(row["exit_code"]) is int and row["exit_code"] == 0
                and row["receipt_sha256"] == commands[str(expected)]
                and stamp(row["started"]) <= stamp(row["finished"]), "postprocess outer completion mismatch")
    return dict(gate_files=gates, completion_receipts=commands,
        postprocess_state=dict(path=str(post_path),sha256=sha(post_path)),
        postbuild_plan=dict(path=str(post_plan_path),sha256=sha(post_plan_path)),
        archive_manifest_sha256=manifest_sha, original_current_wall_clock_limit_retained=True,
        c_retry_provenance=retry_provenance, **capacity_metadata)

def review_marker(review):
    name = review["review_id"]
    require(re.fullmatch("[A-Za-z0-9][A-Za-z0-9_-]{2,100}", name), "unsafe review ID")
    return Path(__file__).resolve().parent/"review-consumption"/(name+".json")

def validate_review(plan, plan_path, review_path, readiness, stage):
    require(review_path is not None, "ROOT_REVIEW receipt is required")
    review = read(review_path)
    require(review.get("contract") == REVIEW_CONTRACT and review.get("status") == "ROOT_REVIEW_APPROVED"
            and review.get("decision") == REVIEW_DECISION and review.get("scope") == REVIEW_SCOPE
            and review.get("reviewer") == "codex:/root"
            and review.get("approved_stages") == ["import","after-audit"], "ROOT_REVIEW approval fields")
    stamp(review["reviewed_at"])
    expected = dict(plan_sha256=sha(plan_path), executor_sha256=sha(__file__),
        identity_sha256=plan["identity"]["sha256"],source_commit=plan["source_commit"],
        emu_sha256=plan["identity"]["emu_sha256"],
        adapter_files={str(Path(plan["adapter_copy"]["source"])/name): digest
                       for name,digest in plan["adapter_copy"]["files"].items()})
    require(all(review.get(k) == v for k,v in expected.items()), "ROOT_REVIEW plan/tool/identity/adapter drift")
    for key in ("gate_files","completion_receipts","postprocess_state","postbuild_plan",
                "fullcore_capacity_qualification","failed_attempts","fullcore_audit_runtime","c_retry_provenance"):
        require(review.get(key) == readiness[key], "ROOT_REVIEW actual evidence changed: " + key)
    marker = review_marker(review)
    if stage == "import":
        absent(marker)
    else:
        claimed = read(marker)
        require(claimed["review_sha256"] == sha(review_path)
                and claimed["plan_sha256"] == sha(plan_path)
                and claimed["output_root"] == plan["paths"]["output_root"], "review consumption differs")
        imported = read(Path(plan["paths"]["output_root"])/"preflight/import.json")
        require(imported["status"] == "CONFIG_REUSE_UNTRACKED_IMPORT_IDENTITY_UNCHANGED"
                and imported["review_sha256"] == sha(review_path)
                and imported["review_consumption_sha256"] == sha(marker)
                and imported["plan_sha256"] == sha(plan_path), "after-audit is not bound to approved import")
        preflight = Path(plan["paths"]["output_root"])/"preflight"
        require(imported["before_identity_sha256"] == sha(preflight/"identity-before.json")
                and imported["after_identity_sha256"] == sha(preflight/"identity-after-import.json")
                and read(preflight/"identity-before.json", limit=64 * 1024 * 1024)
                    == read(preflight/"identity-after-import.json", limit=64 * 1024 * 1024),
                "original import physical snapshots changed")
        require(imported["source_commit"] == plan["source_commit"]
                and imported["emu_sha256"] == plan["identity"]["emu_sha256"]
                and imported["imported_files"] == 26 and imported["dependencies_verified"] == 39
                and imported["imported"] == plan["source_import"]["new_files"]
                and imported["adapter_files"] == plan["adapter_copy"]["files"]
                and imported["git_index_unchanged"] is True and imported["tracked_worktree_unchanged"] is True
                and imported["staged"] is False and imported["committed"] is False
                and imported["main_imported"] is False and imported["new_emu_runs"] == 0
                and imported["fullcore_capacity_qualification"] == readiness["fullcore_capacity_qualification"]
                and imported["c_retry_provenance"] == readiness["c_retry_provenance"],
                "approved import scope or source identity changed")
    return review, marker

def capture_identity(plan):
    """Expensive physical verification: execute mode only."""
    repo, identity_path = Path(plan["paths"]["repo"]), Path(plan["identity"]["path"])
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"
    sys.path.insert(0, str(repo/COMBO))
    spec = importlib.util.spec_from_file_location("clean02_stage_combination", repo/COMBO/"combination.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    identity, files, profile = module.parent_identity(repo, identity_path, physical=True)
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    require(head == plan["source_commit"], "HEAD changed")
    require(git(repo, "diff", "HEAD", "--") == b"", "tracked worktree or index differs")
    index = Path(git(repo, "rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = repo/index
    return dict(identity=identity, physical_inputs=files, hardware_profile=profile,
                head=head, index_sha256=sha(index), tracked_diff_empty=True)

def file_bytes(path, row):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "missing/nonregular source: " + str(path))
    raw = path.read_bytes()
    require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "source bytes differ: " + str(path))
    if "git_blob" in row:
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(blob == row["git_blob"], "source Git object differs: " + str(path))
    return raw

def source_inputs(plan, imported=False):
    paths = plan["paths"]; repo = Path(paths["repo"])
    manifest = read(paths["import_manifest"])
    require(manifest["upstream_ref"] == plan["source_import"]["upstream_ref"]
            and manifest["files"] == plan["source_import"]["new_files"]
            and manifest["already_present_dependencies"] == plan["source_import"]["dependencies_verify_only"],
            "import manifest differs from approved plan")
    candidate = repo/S3
    if not imported:
        absent(candidate)
    pending = []
    for row in plan["source_import"]["new_files"]:
        target = repo/row["path"]
        raw = file_bytes(Path(paths["import_source"])/row["path"], row)
        if imported:
            require(file_bytes(target, row) == raw, "imported source changed")
        else:
            absent(target)
        pending.append((target, raw))
    for row in plan["source_import"]["dependencies_verify_only"]:
        file_bytes(repo/row["path"], row)
    for name, digest in plan["adapter_copy"]["files"].items():
        source = Path(plan["adapter_copy"]["source"])/name
        require(source.is_file() and not source.is_symlink() and sha(source) == digest,
                "frozen adapter changed: " + name)
        destination = Path(paths["adapter"])/name
        if imported:
            require(destination.is_file() and not destination.is_symlink() and sha(destination) == digest,
                    "copied adapter changed: " + name)
        else:
            absent(destination)
        pending.append((destination, source.read_bytes()))
    return pending

def execute_import(plan, plan_path, review_path, readiness, review, marker):
    out = Path(plan["paths"]["output_root"])
    absent(out)
    before = capture_identity(plan)
    pending = source_inputs(plan)
    # Re-read all small completed receipts immediately before the first write.
    require(gate_metadata(plan) == readiness, "release evidence changed during preflight")
    validate_review(plan, plan_path, review_path, readiness, "import")
    marker.parent.mkdir(exist_ok=True)
    save_new(marker, dict(contract=CONTRACT, review_id=review["review_id"],
        review_sha256=sha(review_path), plan_sha256=sha(plan_path), executor_sha256=sha(__file__),
        output_root=str(out), claimed_at=now(), pid=os.getpid(),
        meaning="One exclusive attempt. Failure preserves partial output and consumes approval."))
    out.mkdir()
    preflight = out/"preflight"; preflight.mkdir()
    save_new(preflight/"release-gates.json", readiness)
    save_new(preflight/"identity-before.json", before)
    save_new(preflight/"approval-binding.json", dict(review_path=str(review_path),
        review_sha256=sha(review_path), consumption_path=str(marker),
        consumption_sha256=sha(marker), plan_path=str(plan_path), plan_sha256=sha(plan_path)))
    for path, raw in pending:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    after = capture_identity(plan)
    require(after == before, "identity changed during import; preserve evidence, do not run probe")
    save_new(preflight/"identity-after-import.json", after)
    value = dict(contract=CONTRACT, status="CONFIG_REUSE_UNTRACKED_IMPORT_IDENTITY_UNCHANGED",
        plan_sha256=sha(plan_path), review_sha256=sha(review_path),
        review_consumption_sha256=sha(marker), imported=plan["source_import"]["new_files"],
        imported_files=26, dependencies_verified=39, adapter_files=plan["adapter_copy"]["files"],
        before_identity_sha256=sha(preflight/"identity-before.json"),
        after_identity_sha256=sha(preflight/"identity-after-import.json"),
        source_commit=plan["source_commit"], emu_sha256=plan["identity"]["emu_sha256"],
        fullcore_capacity_qualification=readiness["fullcore_capacity_qualification"],
        c_retry_provenance=readiness["c_retry_provenance"],
        git_index_unchanged=True, tracked_worktree_unchanged=True,
        staged=False, committed=False, main_imported=False, new_emu_runs=0, finished=now())
    save_new(preflight/"import.json", value)
    return value

def probe_metadata(plan):
    paths = plan["paths"]; out = Path(paths["output_root"])
    build, campaign, audit_path = Path(paths["build"]), Path(paths["run"]), Path(paths["audit"])
    state = read(campaign/"state.json"); result = read(campaign/"results.json")
    audit = read(audit_path); built = read(build/"probe-build.json"); bs = read(build/"state.json")
    expected_contract = plan["runtime_contract"]
    require(state["contract"] == result["contract"] == audit["contract"] == built["contract"] == expected_contract,
            "probe runtime contract mismatch")
    require(bs["status"] == "CURRENT_CONFIG_REUSE_PROBE_STATIC_PASS"
            and bs["images_completed"] == 2 and bs["new_emu_runs"] == 0
            and built["parent_identity_sha256"] == plan["identity"]["sha256"]
            and len(read(build/"images.json")["images"]) == 2, "probe build identity/counts")
    require(state["new_emu_runs"] == result["new_emu_runs"] == 5
            and state["functional_status"] == result["functional_status"] == "FUNCTIONAL_PASS"
            and state.get("active_pid") is None and stamp(state["started"]) <= stamp(state["finished"])
            and result["parent_identity_sha256"] == plan["identity"]["sha256"]
            and sha(campaign/"parent-identity.json") == plan["identity"]["sha256"],
            "probe functional identity/counts/completion")
    decision = result["performance"]["decision"]
    require(decision in ("PERFORMANCE_CANDIDATE", "REJECT", "INCONCLUSIVE")
            and state["status"] == result["status"] == decision
            and result["default_changed"] is False and result["historical_pass_reused"] is False,
            "probe decision/default mismatch")
    require(audit["status"] == "PROBE_LOCAL_RAW_AUDIT_PASS" and audit["new_emu_runs"] == 0
            and audit["normal_all_windows"] == 96 and audit["measured_windows"] == 32
            and len(audit["records"]) == 5 and audit["functional_status"] == "FUNCTIONAL_PASS"
            and audit["performance"] == result["performance"]
            and audit["campaign"] == str(campaign) and audit["build"] == str(build)
            and audit["complete_runtime_input_closure"] is True
            and audit["physical_common_inputs_verified"] is True
            and audit["private_process_inputs_verified"] is True, "probe raw v2 evidence mismatch")
    require(len(result["runs"]) == 4 and all(len(r["samples"]) == 24 for r in result["runs"]),
            "probe normal all-window inventory")
    receipts = {}
    for action in ("build", "run", "audit"):
        path = out/(action+"-01.command.json")
        row = read(path)
        expected = plan["cli"][action]
        actual = row["command"]
        # Recorder must include a deliberate non-writing Git environment.
        require(actual[:2] == ["env","GIT_OPTIONAL_LOCKS=0"], "probe command lacks Git read-only environment")
        actual = actual[2:]
        if action == "run":
            require(len(actual) >= 4 and actual[:2] == ["taskset","-c"], "probe run affinity not recorded")
            cores = actual[2].split(",")
            require(1 <= len(cores) <= 4 and len(cores) == len(set(cores))
                    and all(re.fullmatch("[0-9]+", v) for v in cores), "probe affinity exceeds four explicit CPUs")
            actual = actual[3:]
        require(actual == expected, "probe command differs from plan")
        receipts[str(path)] = completed_command(path, row["command"], Path(paths["repo"]))
    selected = [campaign/"state.json", campaign/"results.json", campaign/"parent-identity.json",
                build/"state.json", build/"probe-build.json", build/"images.json", audit_path]
    return dict(status="PROBE_SMALL_METADATA_AND_COMPLETED_COMMANDS_PASS",
                results={str(p):sha(p) for p in selected}, completion_receipts=receipts,
                functional_status="FUNCTIONAL_PASS", performance_decision=decision,
                target_emu_processes=5, normal_all_windows=96, measured_windows=32)

def execute_after_audit(plan, plan_path, review_path, readiness, review, marker, metadata):
    out = Path(plan["paths"]["output_root"]); preflight = out/"preflight"
    target = preflight/"identity-after-audit.json"
    absent(target); absent(preflight/"after-audit.json")
    source_inputs(plan, imported=True)
    final = capture_identity(plan)
    require(final == read(preflight/"identity-before.json", limit=64 * 1024 * 1024), "final hardware/index/physical inputs changed")
    require(gate_metadata(plan) == readiness and probe_metadata(plan) == metadata,
            "release/probe evidence changed during final physical verification")
    validate_review(plan, plan_path, review_path, readiness, "after-audit")
    save_new(target, final)
    value = dict(contract=CONTRACT, status="CONFIG_REUSE_PROBE_IDENTITY_UNCHANGED",
        plan_sha256=sha(plan_path),review_sha256=sha(review_path),
        review_consumption_sha256=sha(marker),import_sha256=sha(preflight/"import.json"),
        final_identity_sha256=sha(target),probe=metadata,new_emu_runs=0,
        fullcore_capacity_qualification=readiness["fullcore_capacity_qualification"],
        c_retry_provenance=readiness["c_retry_provenance"],
        hardware_changed=False, default_changed=False, full_matrix_qualified=False, finished=now())
    save_new(preflight/"after-audit.json", value)
    return value

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("import","after-audit"))
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--review", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--execute", action="store_true")
    parser.add_argument("--receipt", type=Path,
        help="External command receipt; must be under this review tool directory, never OUTPUT or CLEAN.")
    args = parser.parse_args(argv)
    started = now()
    mode = "execute" if args.execute else "check"
    root = Path(__file__).resolve().parent
    receipt = args.receipt or root/"stage-receipts"/(
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")+"-"+args.stage+"-"+str(os.getpid())+".json")
    require(receipt.is_absolute() and receipt.resolve().is_relative_to(root)
            and not receipt.is_symlink(), "receipt must stay in the external review tool directory")
    absent(receipt)
    record = dict(contract=CONTRACT,command=[sys.executable,str(Path(__file__).resolve()),*(argv or sys.argv[1:])],
        cwd=os.getcwd(),pid=os.getpid(),started=started,stage=args.stage,mode=mode,
        new_emu_runs=0,new_nemu_runs=0,physical_verification_executed=False)
    code = 0
    try:
        ast.parse(Path(__file__).read_text(encoding="utf-8"))
        plan = read(args.plan); paths = validate_plan(plan)
        record["plan_sha256"] = sha(args.plan)
        readiness = gate_metadata(plan); record["readiness"] = readiness
        review, marker = validate_review(plan,args.plan,args.review,readiness,args.stage)
        record["review_sha256"] = sha(args.review)
        if args.stage == "import":
            absent(paths["output_root"]); absent(paths["repo"]/S3)
            if args.execute:
                record["physical_verification_executed"] = True
                record["result"] = execute_import(plan,args.plan,args.review,readiness,review,marker)
        else:
            metadata = probe_metadata(plan); record["probe_metadata"] = metadata
            if args.execute:
                record["physical_verification_executed"] = True
                record["result"] = execute_after_audit(plan,args.plan,args.review,readiness,review,marker,metadata)
        record["status"] = "EXECUTED_PASS" if args.execute else "CHECK_READY_NO_IMPORT_OR_PHYSICAL_SCAN"
    except Exception as exc:
        code = 1 if args.execute else 2
        record.update(status="EXECUTION_FAILED" if args.execute else "CHECK_NOT_READY",error=repr(exc))
    record.update(exit_code=code,finished=now(),subcommands=COMMANDS)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    save_new(receipt,record)
    print(json.dumps(dict(status=record["status"],exit_code=code,receipt=str(receipt),
        error=record.get("error"),new_emu_runs=0),ensure_ascii=False))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
