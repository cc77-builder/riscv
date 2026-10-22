"""Recompute T14 from sealed raw evidence, independently of WSL absolute paths."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "team/workloads/vdot-perf"))
import analyze
import check as c


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "team/scripts" / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(root, manifest):
    for name, digest in load(root / manifest)["files"].items():
        path = (root / name).resolve()
        c.require(path.is_relative_to(root.resolve()), "archive path escape")
        c.require(sha(path) == digest, "archive byte mismatch " + name)


def verify(root, output):
    seal(root, "file-manifest.json")
    for item in load(root / "archive-files.json")["files"]:
        path = (root / item["path"]).resolve()
        c.require(path.is_relative_to(root.resolve()), "archive path escape")
        c.require(sha(path) == item["sha256"], "stored byte mismatch")
        raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        c.require(len(raw) == item["raw_bytes"] and hashlib.sha256(raw).hexdigest() == item["raw_sha256"],
                  "raw byte mismatch")
    evidence = ROOT / "team/evidence"
    for name, digest in load(root / "dependencies.json").items():
        manifest = "file-manifest.json" if name.startswith("t13-") else "archive-manifest.json"
        c.require(sha(evidence / name / manifest) == digest, "baseline manifest changed")
        seal(evidence / name, manifest)
    baseline = evidence / "t13-performance-20261015"
    pins = load(root / "hardware-build/hardware-inputs.json")
    state = load(root / "fullcore/campaign-state.json")
    c.require(state["status"] == "T14_CANDIDATE_FULLCORE_PASS", "campaign incomplete")
    c.require(pins["VDOT_T14_FUSED_INPUT"] == "1" and pins["VDOT_T13_TRACE"] == "1", "wrong variant")
    c.require(sha(root / "hardware-build/hardware-inputs.json") == state["hardware_pins_sha256"], "hardware pins drift")
    external = load(root / "external-artifacts.json")
    reference = "efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4"
    flash = "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994"
    c.require(external == state["external_files"], "external inventory mismatch")
    c.require(set(external.values()) == {pins["emu_sha256"], reference, flash}, "wrong external pins")
    output.mkdir(parents=True, exist_ok=False)
    t12 = module("t14_archive_t12", "check-t12-archive.py").validate(
        root / "t12", pins["source_commit"], pins["emu_sha256"], reference, flash, fu_latency=2)
    # Compare the actual loaded program digest for every T12 job to the frozen baseline.
    old_suite = load(evidence / "t12-regression-20261014/suite/result.json")
    old_runs = {row["name"]: row for row in old_suite["runs"]}
    for row in load(root / "t12/suite/result.json")["runs"]:
        old = old_runs[row["name"]]
        def image_digest(record):
            image = record["command"][record["command"].index("-i") + 1]
            return record["files"][image]
        if row["name"] != "control":
            c.require(image_digest(row) == image_digest(old), "T12 input changed: " + row["name"])
        else:
            c.require(image_digest(row) == sha(root / "control-sweep/build/vdot-regression.bin"), "sweep image mismatch")
    control_checker = module("t14_sweep_checker", "check-vdot-regression.py")
    sweep_manifest = load(root / "control-sweep/build/data/manifest.json")
    for variant, latency in (("baseline", 3), ("candidate", 2)):
        directory = root / "control-sweep" / variant
        record = load(directory / "result.json")
        for name, digest in record["raw_logs_sha256"].items():
            c.require(c.sha(directory / name) == digest, "sweep raw stream mismatch")
        c.require(c.raw_bytes(directory / "run.log") == c.raw_bytes(directory / "stderr.log") + c.raw_bytes(directory / "stdout.log"), "sweep log composition")
        sweep = control_checker.check(c.read_text(directory / "run.log"), sweep_manifest, record["exit_code"], fu_latency=latency)
        c.require(sweep["status"] == "T12_CONTROL_REGRESSION_PASS", "paired sweep coverage incomplete")
        c.require(sweep == load(directory / "control-result.json"), "paired sweep recheck changed")
        image = record["command"][record["command"].index("-i") + 1]
        c.require(record["files"][image] == sha(root / "control-sweep/build/vdot-regression.bin"), "paired sweep binaries differ")
        expected_emu = load(baseline / "hardware-build/hardware-inputs.json")["emu_sha256"] if variant == "baseline" else pins["emu_sha256"]
        emulator = next(x for x in record["command"] if x.endswith("/build/emu"))
        c.require(record["files"][emulator] == expected_emu, "paired sweep EMU mismatch")
    previous = load(root / "historical/original-control/control-result.json")
    c.require(previous["architectural_checks"] == "PASS" and {k for k,v in previous["coverage"].items() if not v} == {"vdot_writeback_backpressure"}, "lost original coverage miss")
    calibration = c.verify(baseline / "support/smoke-build-02",
                           root / "fullcore/calibration/calibration-r0", external)
    c.require(len(calibration["samples"]) == 13, "calibration count")
    c.require(calibration == load(root / "fullcore/calibration-check.json"), "calibration changed")
    result = analyze.analyze(baseline / "images-v3", root / "fullcore/performance",
                             baseline / "images-stream-v4", root / "fullcore/performance",
                             output / "analysis", external, fu_latency=2)
    c.require(result == load(root / "fullcore/analysis/result.json"), "accepted analysis changed")
    for file in (root / "fullcore/analysis").glob("*.json"):
        c.require(load(file) == load(output / "analysis" / file.name), "analysis artifact changed " + file.name)
    compare = module("t14_archive_compare", "compare-t14.py")
    ablation = compare.compare(baseline / "support/analysis-v1", output / "analysis", output / "ablation")
    original = load(root / "ablation/result.json")
    # Relocation changes provenance paths; CRLF on Windows can change JSON-byte
    # hashes. Both accepted originals were byte-checked above; compare all results.
    c.require({k: v for k, v in ablation.items() if k != "inputs"} ==
              {k: v for k, v in original.items() if k != "inputs"}, "ablation changed")
    for name, directory in (("baseline", baseline / "support/analysis-v1"),
                            ("candidate", root / "fullcore/analysis")):
        c.require(original["inputs"][name]["result_sha256"] == sha(directory / "result.json"),
                  "original ablation input digest mismatch")
    for name in ("paired-windows.json", "summary.json"):
        c.require(load(root / "ablation" / name) == load(output / "ablation" / name), "paired rows changed")
    structure = module("t14_archive_structure", "check-t14-structure.py").audit(
        root / "fu/original/VDotFuTestTop.sv", root / "fu/baseline/rtl/VDotFuTestTop.sv",
        root / "fu/fused/rtl/VDotFuTestTop.sv")
    old_structure = load(root / "support/structure-01.json")
    c.require({k: v for k, v in structure.items() if k != "source_files"} ==
              {k: v for k, v in old_structure.items() if k != "source_files"}, "structure changed")
    for key in structure["source_files"]:
        c.require(structure["source_files"][key]["sha256"] == old_structure["source_files"][key]["sha256"],
                  "structure input hash changed")
    receipt = dict(status="T14_OFFLINE_REPLAY_PASS", hardware_rerun=False, t12=t12,
                   calibration_windows=13, functional_calls=108, performance_windows=1404,
                   identical_image_ablation=True, structure_recomputed=True,
                   scope="Rechecks stored bytes, ELF/golden/trace/state and accepted results; does not rerun the DUT or prove physical timing.")
    (output / "offline-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: value for key, value in receipt.items() if key != "t12"}))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.archive.resolve(), args.output.resolve())
