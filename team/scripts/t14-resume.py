"""Resume T14 after a paired control sweep, retaining the original coverage miss."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "team/workloads/vdot-perf"))
import campaign
import check as c
import analyze


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "team/scripts" / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main(args):
    base = args.base
    out = args.output
    old = base / "runs/fullcore-01"
    old_state = load(old / "campaign-state.json")
    c.require(old_state["status"] == "FAILED" and old_state["failed_stage"] == "T12_RUNNING",
              "original campaign must have stopped at T12")
    original_suite = load(old / "t12/result.json")
    c.require(original_suite["status"] == "T12_FULLCORE_SUITE_FAILED", "unexpected prior suite result")
    records = original_suite["runs"]
    c.require({r["name"] for r in records} == {"control", "hello-vadd", "negative-vdot"} | {f"functional-{i}" for i in range(8)}, "incomplete prior job inventory")
    c.require(len(records) == 11 and {r["name"] for r in records if r["status"] == "FAILED"} == {"control"},
              "unexplained original failures")
    previous_control = load(old / "t12/control/control-result.json")
    c.require(previous_control["architectural_checks"] == "PASS" and
              {k for k, v in previous_control["coverage"].items() if not v} == {"vdot_writeback_backpressure"},
              "unexpected original coverage gap")
    checker = module("t14_resumed_control", "check-vdot-regression.py")
    build = base / "runs/control-sweep-02"
    build_receipt = load(build / "build.json")
    for name, digest in build_receipt["files"].items():
        c.require(sha(build / name) == digest, "control build drift")
    controls = {}
    for variant, latency in (("baseline", 3), ("candidate", 2)):
        path = base / ("runs/control-sweep-" + variant + "-02")
        record = load(path / "result.json")
        c.require(record["status"] == "T12_CONTROL_REGRESSION_PASS", "sweep not fully covered: " + variant)
        for name, digest in record["files"].items():
            c.require(sha(Path(name)) == digest, "control runtime drift")
        for name, digest in record["raw_logs_sha256"].items():
            c.require(sha(path / name) == digest, "control transcript drift")
        c.require((path / "run.log").read_bytes() == (path / "stderr.log").read_bytes() + (path / "stdout.log").read_bytes(),
                  "control raw stream composition")
        result = checker.check((path / "run.log").read_text(), load(build / "data/manifest.json"),
                               record["exit_code"], fu_latency=latency)
        c.require(result["status"] == "T12_CONTROL_REGRESSION_PASS", "sweep recheck failed")
        image = record["command"][record["command"].index("-i") + 1]
        c.require(record["files"][image] == sha(build / "vdot-regression.bin"), "paired control image mismatch")
        hardware_root = args.t13_root if variant == "baseline" else base
        expected_pins = load(hardware_root / "build-evidence/hardware-inputs.json")
        emulator = next(x for x in record["command"] if x.endswith("/build/emu"))
        c.require(record["files"][emulator] == expected_pins["emu_sha256"], "paired sweep hardware mismatch")
        c.require(record["hardware_pins_sha256"] == sha(hardware_root / "build-evidence/hardware-inputs.json"), "sweep hardware receipt drift")
        controls[variant] = record
    pins = load(base / "build-evidence/hardware-inputs.json")
    emu = base / "repo/build/emu"
    c.require(sha(emu) == pins["emu_sha256"] and pins["VDOT_T14_FUSED_INPUT"] == "1", "candidate hardware mismatch")
    frozen = ROOT / "team/evidence/t13-performance-20261015"
    for name, digest in load(frozen / "file-manifest.json")["files"].items():
        c.require(sha(frozen / name) == digest, "baseline archive drift")
    for kind in ("files", "dependency_files"):
        for name, digest in pins[kind].items():
            c.require(sha(ROOT / name) == digest, "candidate source drift")
    out.mkdir(parents=True, exist_ok=False)
    state = dict(status="RECHECKING_T12", source=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                 started=campaign.now(), driver_file="team/scripts/t14-resume.py", driver_sha256=sha(Path(__file__)),
                 hardware_pins_sha256=sha(base / "build-evidence/hardware-inputs.json"),
                 selected_images=[], external_files=old_state["external_files"],
                 prior_campaign=str(old), control_sweep_build=str(build), control_sweep_records=controls,
                 reason="Original candidate coverage miss: no WB stall. Same added F2v sweep image fully passes both hardware variants.")
    save(out / "campaign-state.json", state)
    # Reuse completed jobs byte-for-byte; only the control comes from a new run.
    suite = out / "t12"
    suite.mkdir()
    functional = module("t14_resumed_functional", "check-vdot-run.py")
    for path in (old / "t12").iterdir():
        if path.is_file() and path.name not in ("progress.json", "result.json"):
            shutil.copy2(path, suite / path.name)
    new_records = []
    for record in records:
        name = record["name"]
        source = base / "runs/control-sweep-candidate-02" if name == "control" else old / "t12" / name
        shutil.copytree(source, suite / name)
        actual = load(source / "result.json")
        if name != "control":
            c.require(actual == record, "original suite/job receipt disagreement")
        for filename, digest in actual["files"].items():
            c.require(sha(Path(filename)) == digest, "reused runtime input drift")
        for filename, digest in actual["raw_logs_sha256"].items():
            c.require(sha(source / filename) == digest, "reused raw stream drift")
        if name.startswith("functional-"):
            index = int(name.split("-")[-1])
            text = (source / "run.log").read_text()
            _, uart = checker.extract_events(text)
            functional.validate(uart, "full", actual["exit_code"],
                                args.t12_root / ("runs/t11-matrix-canonical/data-" + str(index)), require_diff=True)
        new_records.append(actual)
    merged = dict(status="T12_FULLCORE_SUITE_PASS", finished=campaign.now(), matrix_unique=117,
                  matrix_executed=124, runs=new_records, control_build=str(build),
                  reused_noncontrol_from=str(old / "t12"), paired_sweep=True)
    save(suite / "result.json", merged)
    save(suite / "progress.json", new_records)
    save(out / "t12-reuse-receipt.json", dict(original_suite_sha256=sha(old / "t12/result.json"),
         original_failure=previous_control, paired_controls=controls,
         copied_job_files={str(p.relative_to(suite)): sha(p) for p in suite.rglob("*") if p.is_file()}))
    print("T14_PAIRED_SWEEP_T12_GATE_PASS", flush=True)
    paths = dict(reference=args.t12_root / "nemu/reference/build/riscv64-nemu-interpreter-so",
                 flash=args.t12_root / "repo/team/workloads/hello-vadd/build/boot-flash.bin")
    for name, digest in state["external_files"].items():
        c.require(sha(Path(name)) == digest, "external input drift")
    cal_build = args.t13_root / "runs/smoke-build-02"
    cal_input = out / "calibration-input"
    cal_input.mkdir()
    save(cal_input / "images.json", {"images": [dict(name="calibration", path=str(cal_build), replays=1)]})
    state["status"] = "CALIBRATION_RUNNING"
    save(out / "campaign-state.json", state)
    campaign.run(SimpleNamespace(output=out / "calibration", images=cal_input, emu=emu, jobs=1, **paths))
    calibration = c.verify(cal_build, out / "calibration/calibration-r0")
    c.require(len(calibration["samples"]) == 13, "calibration count")
    save(out / "calibration-check.json", calibration)
    print("T14_CALIBRATION_GATE_PASS", flush=True)
    images = []
    for group, only_stream in (("images-v3", False), ("images-stream-v4", True)):
        source = args.t13_root / "runs" / group
        for item in load(source / "images.json")["images"]:
            is_stream = item["suite"] == "performance" and item["shard"] in (7, 8, 9)
            if is_stream != only_stream:
                continue
            image = source / item["name"]
            for artifact in ("vdot-perf.bin", "vdot-perf.elf", "data/manifest.json"):
                c.require(sha(image / artifact) == sha(frozen / group / item["name"] / artifact), "performance image drift")
            images.append(dict(item, path=str(image)))
            state["selected_images"].append(dict(name=item["name"], group=group, binary_sha256=sha(image / "vdot-perf.bin")))
    c.require(len(images) == 48 and len({x["name"] for x in images}) == 48 and sum(x["replays"] for x in images) == 126,
              "performance inventory drift")
    inventory = out / "input"
    inventory.mkdir()
    save(inventory / "images.json", {"images": images})
    state["status"] = "PERFORMANCE_RUNNING"
    save(out / "campaign-state.json", state)
    campaign.run(SimpleNamespace(output=out / "performance", images=inventory, emu=emu, jobs=args.jobs, **paths))
    state["status"] = "ANALYZING"
    save(out / "campaign-state.json", state)
    result = analyze.analyze(args.t13_root / "runs/images-v3", out / "performance",
                             args.t13_root / "runs/images-stream-v4", out / "performance", out / "analysis", fu_latency=2)
    c.require(result["status"] == "T13_FAIR_CYCLE_COMPARISON_PASS", "performance gate failed")
    for name, digest in state["external_files"].items():
        c.require(sha(Path(name)) == digest, "external input changed")
    for kind in ("files", "dependency_files"):
        for name, digest in pins[kind].items():
            c.require(sha(ROOT / name) == digest, "candidate source changed")
    state.update(status="T14_CANDIDATE_FULLCORE_PASS", finished=campaign.now())
    save(out / "campaign-state.json", state)
    print(state["status"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "output", "t13-root", "t12-root"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--jobs", type=int, choices=(1, 2, 4, 8), default=8)
    args = parser.parse_args()
    try:
        main(args)
    except Exception as exc:
        status = args.output / "campaign-state.json"
        if status.exists():
            state = load(status)
            state.update(status="FAILED", failed_stage=state["status"], error=repr(exc), finished=campaign.now())
            save(status, state)
        raise
