"""Bind the opt-in C8 package to current 0f / clean02 runtime evidence.

This module only reparses immutable completed runs; it never launches EMU/NEMU.
INPUTS uses logical roles. Physical evidence paths are recorded in the output.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CONTRACT = "current-c8-package-input-binding-v1"
SOURCE_COMMIT = "c823a8786e052c6e26f6915563c42b6d730dd8e3"
HARDWARE_COMMIT = "0f12df675378556670afd0dd2153f47fcb330610"
EMU_SHA256 = "acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9"
REFERENCE_SHA256 = "62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca"
OBJECT_SHA256 = "f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3"
ASSEMBLY_SHA256 = "9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2"
HEADER_SHA256 = "d6cbdadb8ed601e1ccd4d308970111588c5fe7e10098b821625630e2b5360be9"
TARGET = "config_reuse_gemv_8x32_reuse_vdot"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def load(label, path):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_identity(identity):
    """Semantic checks independent of any candidate-provided digest map."""
    require(isinstance(identity, dict), "identity object required")
    require(identity.get("contract") == "zjhwork-0f-firstdot-v2-clean-identity-v1",
            "current clean identity contract required")
    require(identity.get("source_commit") == SOURCE_COMMIT
            and identity.get("selected_hardware_commit") == HARDWARE_COMMIT,
            "wrong software/hardware identity")
    profile = identity.get("hardware_profile", {})
    require(profile.get("source_commit") == SOURCE_COMMIT
            and profile.get("selected_hardware_commit") == HARDWARE_COMMIT
            and profile.get("emu_sha256") == EMU_SHA256,
            "wrong physical hardware profile")
    require(identity.get("reference_sha256") == REFERENCE_SHA256
            and profile.get("reference_provenance", {}).get("binary_sha256") == REFERENCE_SHA256,
            "wrong NEMU reference")
    config = identity.get("configuration", {})
    require(config.get("source_commit") == SOURCE_COMMIT, "mixed configuration source")
    require(all(isinstance(config.get(key), str) and config[key] for key in
                ("hardware_source", "reference", "build_record", "am_home", "flash")),
            "incomplete physical configuration")
    return dict(source_commit=SOURCE_COMMIT, selected_hardware_commit=HARDWARE_COMMIT,
                emu_sha256=EMU_SHA256, reference_sha256=REFERENCE_SHA256)


def validate_selection(matrix_result, c8_qualification):
    """Keep historical matrix-C NOT_TESTED separate from later C qualification."""
    require(matrix_result.get("contract") ==
            "zjhwork-clean-config-reuse-4shape-3dataset-matrix-v1"
            and matrix_result.get("status") == "CURRENT_CONFIG_REUSE_MATRIX_SCREEN_COMPLETE"
            and matrix_result.get("functional_status") == "FUNCTIONAL_PASS",
            "wrong or incomplete matrix")
    require(type(matrix_result.get("new_emu_runs")) is int
            and matrix_result["new_emu_runs"] == 33
            and matrix_result.get("all_window_replay") is True
            and matrix_result.get("default_changed") is False,
            "incomplete matrix execution/replay")
    decision = matrix_result.get("decisions", {}).get("8x32", {})
    require(decision.get("decision") == "PERFORMANCE_CANDIDATE"
            and decision.get("unexplained_controls") == []
            and decision.get("samples_per_cell") == 12
            and decision.get("ordinary_public_C_application") == "NOT_TESTED"
            and decision.get("stable_default_changed") is False,
            "wrong 8x32 qualification or rewritten historical C boundary")
    require(set(decision.get("dataset_decisions", {})) == {"0", "1", "2"}
            and all(d.get("decision") == "PERFORMANCE_CANDIDATE"
                    and d.get("unexplained_controls") == []
                    and d.get("samples_per_cell") == 4
                    for d in decision["dataset_decisions"].values()),
            "all three datasets must qualify")
    require(c8_qualification.get("contract") == "zjhwork-config-reuse-8x32-c-qualification-v1"
            and c8_qualification.get("status") == "CURRENT_CONFIG_REUSE_8X32_C_QUALIFIED"
            and c8_qualification.get("performance_measured") is False
            and c8_qualification.get("default_changed") is False,
            "wrong C8 qualification")
    anchor = c8_qualification.get("anchor", {})
    require(anchor.get("target_symbol") == TARGET and anchor.get("comparisons_count") == 48
            and anchor.get("target_comparisons") == 12
            and anchor.get("target_functions") == 4
            and anchor.get("target_distinct_cases") == 12
            and anchor.get("target_normal_executions") == 24
            and anchor.get("negative_expected_pc") == "0x80000d64",
            "wrong C8 target/count/negative anchor")
    return dict(matrix="PERFORMANCE_CANDIDATE", matrix_ordinary_C="NOT_TESTED",
                later_ordinary_C="QUALIFIED", new_performance="NOT_TESTED")


def toolchain(inputs):
    """Permit only the explicitly pinned tool aliases and their actual targets."""
    expected = inputs["toolchain"]
    require(set(expected) == {"gcc", "ld", "ar", "objcopy", "objdump", "readelf", "make", "nm"},
            "toolchain role set changed")
    result = {}
    for name, item in expected.items():
        path = Path(item["path"])
        require(path.is_file(), "tool absent: " + name)
        actual = dict(path=str(path),
                      link_text=os.readlink(path) if path.is_symlink() else None,
                      resolved_path=str(path.resolve()), sha256=sha(path))
        require(actual == item, "toolchain path/alias/target changed: " + name)
        completed = subprocess.run([str(path), "--version"], check=True, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        result[name] = dict(actual, version=completed.stdout.splitlines()[0])
    return result


def verify_map(files, aliases=()):
    require(isinstance(files, dict) and files, "nonempty complete input map required")
    allowed = set(aliases)
    for name, digest in files.items():
        path = Path(name)
        require(path.is_file() and (not path.is_symlink() or name in allowed)
                and sha(path) == digest, "sealed input changed: " + name)


def role_files(inputs, roots):
    require(set(inputs["roles"]) == set(roots), "input role set changed")
    result = {}
    for role, members in inputs["roles"].items():
        for relative, expected in members.items():
            rel = Path(relative)
            require(not rel.is_absolute() and ".." not in rel.parts, "unsafe input role")
            path = roots[role] / rel
            require(path.is_file() and not path.is_symlink()
                    and path.stat().st_size == expected["bytes"]
                    and sha(path) == expected["sha256"],
                    "qualified input role changed: " + role + "/" + relative)
            result[role + "/" + relative] = dict(path=str(path), **expected)
    return result


def validate(repo, identity, matrix, c8, output):
    """Reparse completed matrix/C8 runs and return binding evidence.

    All five arguments are paths. output must be a fresh dedicated directory.
    The immutable historical evidence retains its original absolute paths;
    this qualification adapter is not an evidence-archive relocator.
    """
    repo, identity, matrix, c8, output = map(
        lambda value: Path(value).resolve(), (repo, identity, matrix, c8, output))
    inputs = read(HERE / "INPUTS.json")
    require(inputs.get("contract") == CONTRACT, "input binding contract")
    current = read(identity)
    physical_summary = validate_identity(current)
    require(all(inputs[key] == value for key, value in physical_summary.items()),
            "pinset identity differs from fixed contract")
    source = Path(current["configuration"]["hardware_source"]).resolve()
    clean = identity.parent.parent
    workspace = clean.parent
    ctools = workspace / "reviews/config-reuse/c8-v2"
    mtools = workspace / "reviews/config-reuse/expansion-v1"
    protected = (repo, source, clean, matrix, c8, ctools, mtools)
    require(not output.exists() and not any(output == root
            or output.is_relative_to(root) or root.is_relative_to(output)
            for root in protected), "qualification output must be fresh and outside inputs")
    roots = dict(identity=identity.parent, matrix=matrix, c8=c8,
                 c8_tools=ctools, matrix_tools=mtools)
    require(identity.name == "current.json", "current identity role filename")
    bindings = role_files(inputs, roots)
    require(sha(c8 / "build-01/gemv-reference.o") == OBJECT_SHA256
            and (c8 / "build-01/gemv-reference.o").stat().st_size == 27160,
            "wrong complete C8 object")
    for name, digest in (("gemv.S", ASSEMBLY_SHA256), ("gemv.h", HEADER_SHA256)):
        paths = [c8 / "qualified-public" / name, c8 / "build-01/source" / name,
                 repo / "team/optimizations/o2/r2-config-reuse/public" / name]
        require(all(path.is_file() and not path.is_symlink() and sha(path) == digest
                    for path in paths), "qualified/repository public source differs: " + name)
    selection = validate_selection(read(matrix / "run-01/results.json"),
                                   read(c8 / "run-01/current-c-qualification.json"))
    require(read(c8 / "run-01/current-c-qualification.json")["anchor"]["matrix_result_sha256"]
            == sha(matrix / "run-01/results.json"), "mixed matrix/C8 relationship")
    tools = toolchain(inputs)
    aliases = [item["path"] for item in tools.values() if item["link_text"] is not None]
    closure_paths = [c8 / "outer-inputs.json", c8 / "run-01/runtime-inputs.json",
                     matrix / "run-01/runtime-inputs.json"]
    for path in closure_paths:
        verify_map(read(path), aliases)
    output.mkdir(parents=True)
    with (output / "INPUTS.json").open("xb") as stream:
        stream.write((HERE / "INPUTS.json").read_bytes())
    save(output / "inputs-before.json", dict(contract=CONTRACT, roles=bindings,
         input_manifest_sha256=sha(HERE / "INPUTS.json"), toolchain=tools,
         physical=physical_summary, selection=selection))
    # No module import or execution precedes pin/complete input checks.
    module = load("current_c8_package_frozen_c", ctools / "c8.py")
    module.SOURCE, module.ID, module.MATRIX, module.W = source, identity, matrix, workspace
    module.TOOLS = mtools
    experiment = module.CurrentC()
    before = experiment.physical()
    require(before[0] == current and before[2] == current["hardware_profile"],
            "current physical source/EMU/NEMU differs")
    expected_before = read(c8 / "identity-before.json")
    require(list(before) == expected_before, "C8 original physical identity differs")
    module.add_files(experiment.outer, before[1])
    # The historical audit imports the unchanged matrix module by this name.
    prior_matrix = sys.modules.get("matrix")
    sys.modules["matrix"] = experiment.matrix
    try:
        matrix_audit = experiment.audit_module.audit_matrix(
            experiment.p, matrix / "build-01", matrix / "run-01")
    finally:
        if prior_matrix is None:
            sys.modules.pop("matrix", None)
        else:
            sys.modules["matrix"] = prior_matrix
    require(matrix_audit == read(matrix / "audit-01.json"),
            "fresh matrix raw audit differs from preserved proof")
    save(output / "matrix-raw-audit.json", matrix_audit)
    c_audit = experiment.audit(c8 / "build-01", c8 / "run-01", output / "c8-raw-audit.json")
    require(c_audit == read(c8 / "audit-01.json"),
            "fresh C8 raw audit differs from preserved proof")
    experiment.app.verify_build(source, c8 / "build-01")
    require(experiment.physical() == before, "physical identity changed during qualification")
    experiment.check_outer()
    for path in closure_paths:
        verify_map(read(path), aliases)
    require(role_files(inputs, roots) == bindings, "qualified role changed during audit")
    require(toolchain(inputs) == tools, "toolchain changed during audit")
    result = dict(contract=CONTRACT, status="CURRENT_C8_PACKAGE_QUALIFICATION_BOUND",
        current_identity=physical_summary, selection=selection, source=str(source),
        qualified_public=str(c8 / "qualified-public"),
        qualified_object=str(c8 / "build-01/gemv-reference.o"),
        qualified_object_sha256=OBJECT_SHA256, qualified_object_bytes=27160,
        role_files=len(bindings), input_roles=bindings, toolchain=tools,
        validator_sha256=sha(Path(__file__)), cpu_affinity=sorted(os.sched_getaffinity(0)),
        closure_counts={str(path):len(read(path)) for path in closure_paths},
        matrix_raw_processes=33, c8_raw_processes=3, matrix_leaf_anchors=48,
        target_leaf_anchors=12, input_manifest_sha256=sha(HERE / "INPUTS.json"),
        matrix_audit_sha256=sha(output / "matrix-raw-audit.json"),
        c8_audit_sha256=sha(output / "c8-raw-audit.json"),
        runtime_evidence="REVALIDATED_HISTORICAL_RAW",
        new_emu_runs=0, new_nemu_runs=0, new_example_runtime="NOT_TESTED",
        new_performance="NOT_TESTED", default_changed=False,
        historical_records=inputs["historical_records"])
    save(output / "qualification.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "identity", "matrix", "c8", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    # Isolate upstream canonical import names in this short-lived subprocess.
    # A single CPU is sufficient for the read-only audit.
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    result = validate(args.repo, args.identity, args.matrix, args.c8, args.output)
    print(json.dumps({key: result[key] for key in (
        "status", "matrix_raw_processes", "c8_raw_processes",
        "matrix_leaf_anchors", "new_emu_runs", "new_nemu_runs")}, sort_keys=True))


if __name__ == "__main__":
    main()
