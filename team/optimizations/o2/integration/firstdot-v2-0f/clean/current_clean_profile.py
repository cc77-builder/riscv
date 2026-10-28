"""Validate a fresh current-0f clean build; never grants historical T17 qualification."""
from __future__ import annotations
from datetime import datetime
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import current_clean_common as c

CONTRACT, BASELINE, HELPER, AUX, FLASH = c.CONTRACT, c.BASELINE_SHA, c.HELPER, c.AUX, c.FLASH
HERE = Path(__file__).resolve().parent
META_NAMES = (
    "hardware-inputs.json", "hardware-inputs-before.json", "generated-artifacts.json", "build-state.json",
    "dependencies.json", "build-command.sh", "emu-build.log", "source-status.txt", "working-tree.patch",
    "java-version.log", "python-version.log", "make-version.log", "mill-version.log", "firtool-version.log",
    "clang-version.log", "verilator-version.log", "executed-builder.py", "baseline-hardware-inputs.json",
    "effective-environment.json",
) + tuple("executed-" + name for name in c.ADAPTER_NAMES)
require, sha, read = c.require, c.sha, c.read

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value

def validate_metadata(pins, state, before, baseline, generated, builder_sha, baseline_sha, expected_source):
    adapters = c.adapter_sources(HERE)
    require(builder_sha == adapters["current_clean_build.py"] and baseline_sha == c.BASELINE_SHA,
            "unrecognized current build recipe/baseline")
    require(pins["contract"] == state["contract"] == before["contract"] == CONTRACT, "wrong current build contract")
    require(re.fullmatch(r"[0-9a-f]{40}", expected_source) and
            pins["source_commit"] == state["source_commit"] == before["source_commit"] == expected_source,
            "source revision differs from explicitly selected identity")
    require(state["status"] == "CURRENT_CLEAN_BUILD_PASS" and state["build_exit_code"] == 0 and
            state["build_executed"] is True and state["runtime_qualified"] is False, "fresh build incomplete")
    require(pins["source_root"] == state["source_root"] and pins["emu_sha256"] == state["emu_sha256"] and
            re.fullmatch(r"[0-9a-f]{64}", pins["emu_sha256"]) and type(pins["emu_bytes"]) is int and pins["emu_bytes"] > 0,
            "build state/output identities differ")
    require(pins["build_script_sha256"] == builder_sha and pins["adapter_sources"] == adapters and
            pins["baseline_pins_sha256"] == c.BASELINE_SHA and pins["baseline_source_commit"] == c.BASELINE_SOURCE and
            pins["hardware_bytes_equal_baseline"] is True and pins["generated_outputs_reused"] is False,
            "fresh build provenance differs")
    require(baseline["source_commit"] == c.BASELINE_SOURCE and baseline["files"][c.EXEUNIT] == c.EXEUNIT_SHA,
            "baseline is not current cancellation fix")
    for key, count in (("files", 429), ("dependency_files", 21236)):
        require(pins[key] == before[key] == baseline[key] and len(pins[key]) == count,
                "hardware/recursive dependency inventory differs: " + key)
    require({k: v for k, v in pins.items() if k not in ("emu_sha256", "emu_bytes", "emu_path")} == before,
            "pre-build/post-build pins differ")
    require(pins["profile"] == state["profile"] == "observe" and pins["config"] == "MinimalConfig"
            and pins["NUM_CORES"] == pins["EMU_THREADS"] == 1 and pins["JVM_XMX"] == "8G"
            and pins["JVM_XSS"] == "16m" and type(pins["BUILD_JOBS"]) is int and 1 <= pins["BUILD_JOBS"] <= 4
            and state["flags"] == c.FLAGS and all(pins[k] == v for k, v in c.FLAGS.items()),
            "selected profile/trace flags differ")
    cpus = pins["cpu_affinity"]
    require(cpus == state["cpu_affinity"] and len(cpus) == pins["BUILD_JOBS"]
            and len(set(cpus)) == len(cpus) and all(type(v) is int and v >= 0 for v in cpus), "CPU budget differs")
    require(state["source_files"] == 429 and state["dependency_files"] == 21236 and state["dependencies"] == 126,
            "build inventory count differs")
    c.validate_generated(generated)
    require(pins["generated_inventory_scope"] == c.GENERATED_SCOPE and len(generated) == state["generated_files"],
            "generated count/scope differs")
    emu = next(row for row in generated if row["path"] == "build/emu")
    require(emu["sha256"] == pins["emu_sha256"] and emu["bytes"] == pins["emu_bytes"], "EMU inventory differs")
    stamps = [datetime.fromisoformat(state[k]) for k in ("started_utc", "build_started_utc", "build_finished_utc", "finished_utc")]
    require(all(t.utcoffset() is not None for t in stamps) and stamps == sorted(stamps), "invalid build chronology")

def hardware_profile(repo, cfg):
    repo, root, record = Path(repo).resolve(), Path(cfg["hardware_source"]).resolve(), Path(cfg["build_record"]).resolve()
    expected_source = cfg["source_commit"]
    pins, state, before, baseline, generated = (read(record / name) for name in
        ("hardware-inputs.json", "build-state.json", "hardware-inputs-before.json",
         "baseline-hardware-inputs.json", "generated-artifacts.json"))
    validate_metadata(pins, state, before, baseline, generated, sha(record / "executed-builder.py"),
                      sha(record / "baseline-hardware-inputs.json"), expected_source)
    require(str(root) == pins["source_root"] and str(root / "build/emu") == pins["emu_path"], "source/output path differs")
    require(Path(cfg["build_driver"]).resolve() == record / "executed-builder.py", "wrong executed builder selected")
    for name, digest in c.adapter_sources(HERE).items():
        require(sha(record / ("executed-" + name)) == digest, "executed adapter changed")
    require(c.git(root, "rev-parse", "HEAD").decode().strip() == expected_source, "hardware source HEAD differs")
    require(subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor",
                            c.BASELINE_SOURCE, expected_source], capture_output=True).returncode == 0,
            "source is not 0f descendant")
    files, dependencies, dependency_files = c.snapshot(root, baseline)
    require(dependencies == read(record / "dependencies.json"), "dependency revision inventory differs")
    git_checker = module("current_clean_git_sources", repo / "team/optimizations/o2/result-width/h1/performance/build_profile.py")
    git_checker.ROOT = root
    git_checker.verified_git_sources(pins)
    require(c.generated_inventory(root) == generated, "generated physical file set/bytes differ")
    require(state["command"] == ["bash", "-c", (record / "build-command.sh").read_text()], "executed command differs")
    require((record / "working-tree.patch").read_bytes() == b"", "clean build had tracked changes")
    require(not c.git(root, "diff", "HEAD", "--"), "clean checkout tracked source drift")
    env = read(record / "effective-environment.json")
    require(env["JAVA_OPTS"] == f'-Xmx8G -Xss16m -XX:ActiveProcessorCount={pins["BUILD_JOBS"]}'
            and env["OMP_NUM_THREADS"] == env["OPENBLAS_NUM_THREADS"] == "1", "effective resources differ")
    reference = Path(cfg["reference"]).resolve()
    guard = module("current_clean_reference_guard", repo / "team/scripts/artifact_guard.py")
    provenance = guard.verify_nemu(reference.parents[1], reference, "reference")
    metadata = {name: sha(record / name) for name in META_NAMES}
    inputs = {str(record / name): digest for name, digest in metadata.items()}
    inputs.update({str(root / "build" / name): digest for name, digest in AUX.items()})
    inputs.update({str(root / "build/emu"): pins["emu_sha256"], str(reference): provenance["binary_sha256"],
                   cfg["flash"]: FLASH, str(root / "team/optimizations/o2/fullcore/build_fullcore.py"): HELPER})
    for path, digest in inputs.items():
        require(sha(path) == digest, "physical input changed: " + path)
    details = dict(contract=CONTRACT, source_commit=expected_source, selected_hardware_commit=c.BASELINE_SOURCE,
                   emu_sha256=pins["emu_sha256"], pins_sha256=metadata["hardware-inputs.json"],
                   source_files=len(files), dependency_files=len(dependency_files), generated_files=len(generated),
                   generated_inventory_scope=c.GENERATED_SCOPE, reference_provenance=provenance,
                   build_driver_sha256=pins["build_script_sha256"], historical_b0_h1_acceptance=False,
                   historical_t17_acceptance=False, whole_suite_acceptance=False)
    return inputs, details
