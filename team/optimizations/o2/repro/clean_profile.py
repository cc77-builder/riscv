"""T17 hardware identity gate; frozen B0/H1/R4 hardware locks stay unchanged."""
from __future__ import annotations

from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

CONTRACT = "t17-clean-build-v1"
SOURCE = "34bae6d4acceac939f958199dae53c14bc1f6183"
BASELINE = "2c580afa6095cda5e9d1680b7e91939b6f182b21c47357c77402c2d6b09d0a2c"
BUILDER = "9038f134e5f811b1e99a13893dc8fce081a96cf9be0ffe5a9f546a70818a2c7e"
HELPER = "8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0"
META_NAMES = (
    "hardware-inputs.json", "hardware-inputs-before.json", "generated-artifacts.json", "build-state.json",
    "dependencies.json", "build-command.sh", "emu-build.log", "source-status.txt", "working-tree.patch",
    "java-version.log", "python-version.log", "make-version.log", "mill-version.log", "firtool-version.log",
    "clang-version.log", "verilator-version.log", "executed-builder.py", "baseline-hardware-inputs.json",
    "effective-environment.json",
)
AUX = {"constantin.txt": "a1fd1d4de05919fec0257bacb550a3622c0f4ec2373e5cf230fc4233fb98c1bf",
       "plusArgs": "160d9702d313cbe66be84ae88c2f45c3df9ed7b61b65e3ddeea25133ac6765ff"}
FLASH = "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for raw in iter(lambda: stream.read(1048576), b""):
            digest.update(raw)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def validate_metadata(pins, state, before, baseline, generated, builder_sha, baseline_sha):
    require(builder_sha == BUILDER and baseline_sha == BASELINE, "unrecognized clean build recipe/baseline")
    require(pins["contract"] == state["contract"] == before["contract"] == CONTRACT, "wrong clean build contract")
    require(state["status"] == "T17_CLEAN_BUILD_PASS" and state["build_exit_code"] == 0 and
            state["build_executed"] is True and state["runtime_qualified"] is False, "clean build incomplete")
    require(pins["source_commit"] == state["source_commit"] == before["source_commit"] == SOURCE and
            pins["emu_sha256"] == state["emu_sha256"] and pins["source_root"] == state["source_root"],
            "build state and pins identities differ")
    require(pins["build_script_sha256"] == BUILDER and pins["baseline_pins_sha256"] == BASELINE and
            pins["hardware_bytes_equal_baseline"] is True and pins["generated_outputs_reused"] is False,
            "clean build provenance differs")
    require(baseline["source_commit"] == "6d2abe403b07c297b8830a7d4f06e370b0a8e070", "wrong baseline source")
    for key, count in (("files", 429), ("dependency_files", 21236)):
        require(pins[key] == before[key] == baseline[key] and len(pins[key]) == count,
                "current hardware/recursive dependency bytes differ from baseline: " + key)
    require({k: v for k, v in pins.items() if k not in ("emu_sha256", "emu_bytes", "emu_path")} == before,
            "pre-build/post-build pins changed")
    require(pins["profile"] == state["profile"] == "observe" and pins["JVM_XMX"] == "8G" and
            pins["JVM_XSS"] == "16m" and 1 <= pins["BUILD_JOBS"] <= 4 and
            pins["cpu_affinity"] == state["cpu_affinity"] and len(pins["cpu_affinity"]) == pins["BUILD_JOBS"],
            "build resource/profile declaration differs")
    require(state["source_files"] == 429 and state["dependency_files"] == 21236 and state["dependencies"] == 126,
            "build inventory incomplete")
    require(len(generated) == state["generated_files"] == 1672 and len({r["path"] for r in generated}) == 1672,
            "generated output inventory differs")
    stamps = [datetime.fromisoformat(state[k]) for k in ("started_utc", "build_started_utc", "build_finished_utc", "finished_utc")]
    require(all(t.utcoffset() is not None for t in stamps) and stamps == sorted(stamps), "invalid build chronology")


def hardware_profile(repo, cfg):
    repo, root, record = Path(repo).resolve(), Path(cfg["hardware_source"]).resolve(), Path(cfg["build_record"]).resolve()
    pins, state, before, baseline, generated = (read(record / name) for name in
        ("hardware-inputs.json", "build-state.json", "hardware-inputs-before.json",
         "baseline-hardware-inputs.json", "generated-artifacts.json"))
    validate_metadata(pins, state, before, baseline, generated, sha(record / "executed-builder.py"),
                      sha(record / "baseline-hardware-inputs.json"))
    require(str(root) == pins["source_root"] and str(root / "build/emu") == pins["emu_path"], "source/output path differs")
    require(Path(cfg["build_driver"]).resolve() == record / "executed-builder.py", "executed builder not selected")
    suite = module("t17_profile_suite", repo / "team/optimizations/o2/fullcore/run_suite.py")
    suite.hardware_guard(pins, root / "build/emu", root=root)
    helper_path = root / "team/optimizations/o2/fullcore/build_fullcore.py"
    require(sha(helper_path) == HELPER, "snapshot helper changed")
    helper = module("t17_profile_snapshot", helper_path)
    require(not helper.git("diff", "HEAD", "--", *helper.HARDWARE) and
            not helper.git("ls-files", "--others", "--exclude-standard", "--", *helper.HARDWARE),
            "uncommitted or additional hardware input")
    dependencies, dependency_files = helper.dependency_snapshot()
    require(dependencies == read(record / "dependencies.json") and dependency_files == pins["dependency_files"],
            "live dependency revisions/inventory changed")
    require(subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() == pins["source_commit"],
            "hardware checkout revision differs")
    git_checker = module("t17_profile_git_sources", repo / "team/optimizations/o2/result-width/h1/performance/build_profile.py")
    git_checker.ROOT = root
    git_checker.verified_git_sources(pins)
    for item in generated:
        rel = Path(item["path"])
        require(not rel.is_absolute() and ".." not in rel.parts and rel.parts[0] == "build", "unsafe generated path")
        path = root / rel
        require(path.stat().st_size == item["bytes"] and sha(path) == item["sha256"], "generated artifact drift: " + str(rel))
    require((root / "build/emu").stat().st_size == pins["emu_bytes"], "EMU size differs")
    require(state["command"] == ["bash", "-c", (record / "build-command.sh").read_text()], "build command differs")
    require((record / "working-tree.patch").read_bytes() == b"", "hardware build had tracked edits")
    env = read(record / "effective-environment.json")
    require(env["JAVA_OPTS"] == f'-Xmx8G -Xss16m -XX:ActiveProcessorCount={pins["BUILD_JOBS"]}' and
            env["OMP_NUM_THREADS"] == env["OPENBLAS_NUM_THREADS"] == "1", "effective resource environment differs")
    reference = Path(cfg["reference"]).resolve()
    guard = module("t17_profile_artifact_guard", repo / "team/scripts/artifact_guard.py")
    provenance = guard.verify_nemu(reference.parents[1], reference, "reference")
    meta = {name: sha(record / name) for name in META_NAMES}
    files = {str(record / name): digest for name, digest in meta.items()}
    files.update({str(root / "build" / name): digest for name, digest in AUX.items()})
    files.update({str(root / "build/emu"): pins["emu_sha256"], cfg["reference"]: provenance["binary_sha256"],
                  cfg["flash"]: FLASH, str(helper_path): HELPER, cfg["build_driver"]: BUILDER})
    for path, digest in files.items():
        require(sha(path) == digest, "physical input changed: " + path)
    details = dict(contract=CONTRACT, source_commit=pins["source_commit"], emu_sha256=pins["emu_sha256"],
                   pins_sha256=meta["hardware-inputs.json"], source_files=429, dependency_files=21236,
                   generated_files=1672, reference_provenance=provenance, build_driver_sha256=BUILDER,
                   historical_b0_h1_acceptance=False, whole_suite_acceptance=False)
    return files, details
