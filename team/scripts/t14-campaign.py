"""T14 correctness gates then identical-image T13 replay; no builds or publishing."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PERF = ROOT / "team/workloads/vdot-perf"
sys.path.insert(0, str(PERF))
import analyze
import campaign
import check


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    pins = load(args.hardware_pins)
    check.require(pins["VDOT_T14_FUSED_INPUT"] == "1", "candidate variant missing")
    check.require(pins["emu_sha256"] == sha(args.emu), "wrong candidate EMU")
    check.require(pins["VDOT_T12_TRACE"] == pins["VDOT_T13_TRACE"] == "1", "missing observers")
    frozen = ROOT / "team/evidence/t13-performance-20261015"
    for name, digest in load(frozen / "file-manifest.json")["files"].items():
        check.require(sha(frozen / name) == digest, "baseline archive drift: " + name)
    for kind in ("files", "dependency_files"):
        for name, digest in pins[kind].items():
            check.require(sha(ROOT / name) == digest, "candidate source drift: " + name)
    baseline = load(frozen / "support/analysis-v1/result.json")
    check.require(baseline["status"] == "T13_FAIR_CYCLE_COMPARISON_PASS", "baseline not accepted")
    paths = dict(reference=args.t12_root / "nemu/reference/build/riscv64-nemu-interpreter-so",
                 flash=args.t12_root / "repo/team/workloads/hello-vadd/build/boot-flash.bin")
    check.require(sha(paths["reference"]) == "efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4", "reference drift")
    check.require(sha(paths["flash"]) == "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994", "flash drift")
    state = dict(status="STARTED", source=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                 started=campaign.now(), hardware_pins_sha256=sha(args.hardware_pins),
                 driver_sha256=sha(Path(__file__)), selected_images=[], external_files={str(path): sha(path) for path in [args.emu, *paths.values()]})
    save(out / "campaign-state.json", state)
    command = [sys.executable, "-B", str(ROOT / "team/scripts/run-t12-suite.py"),
               "--output", str(out / "t12"), "--hardware-pins", str(args.hardware_pins),
               "--emu", str(args.emu), "--reference-root", str(args.t12_root / "nemu/reference"),
               "--negative-reference", str(args.t12_root / "build-evidence/negative-reference.so"),
               "--flash", str(paths["flash"]),
               "--hello", str(args.t12_root / "repo/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin"),
               "--control", str(args.t12_root / "runs/control-03"),
               "--matrix", str(args.t12_root / "runs/t11-matrix-canonical"),
               "--jobs", str(args.jobs), "--fu-latency", "2"]
    save(out / "t12-command.json", command)
    state["status"] = "T12_RUNNING"
    save(out / "campaign-state.json", state)
    with (out / "t12-driver.log").open("w") as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    check.require(result.returncode == 0, "candidate T12 gate failed; inspect t12-driver.log")
    check.require(load(out / "t12/result.json")["status"] == "T12_FULLCORE_SUITE_PASS", "incomplete T12 coverage")
    print("T14_T12_GATE_PASS", flush=True)
    cal_build = args.t13_root / "runs/smoke-build-02"
    cal_inventory = out / "calibration-input"
    cal_inventory.mkdir()
    save(cal_inventory / "images.json", {"images": [dict(name="calibration", path=str(cal_build), replays=1)]})
    state["status"] = "CALIBRATION_RUNNING"
    save(out / "campaign-state.json", state)
    campaign.run(SimpleNamespace(output=out / "calibration", images=cal_inventory,
                                 emu=args.emu, jobs=1, **paths))
    calibration = check.verify(cal_build, out / "calibration/calibration-r0")
    check.require(len(calibration["samples"]) == 13, "calibration count")
    save(out / "calibration-check.json", calibration)
    print("T14_CALIBRATION_GATE_PASS", flush=True)
    images = []
    for group, stream_only in (("images-v3", False), ("images-stream-v4", True)):
        image_root = args.t13_root / "runs" / group
        for item in load(image_root / "images.json")["images"]:
            stream = item["suite"] == "performance" and item["shard"] in (7, 8, 9)
            if stream != stream_only:
                continue
            image = image_root / item["name"]
            for artifact in ("vdot-perf.bin", "vdot-perf.elf", "data/manifest.json"):
                check.require(sha(image / artifact) == sha(frozen / group / item["name"] / artifact),
                              "compiled input differs from frozen T13: " + item["name"])
            images.append(dict(item, path=str(image)))
            state["selected_images"].append(dict(name=item["name"], group=group, binary_sha256=sha(image / "vdot-perf.bin")))
    check.require(len(images) == 48 and len({x["name"] for x in images}) == 48, "wrong image selection")
    check.require(sum(x["replays"] for x in images) == 126, "wrong replay plan")
    inventory = out / "input"
    inventory.mkdir()
    save(inventory / "images.json", {"images": images})
    state["status"] = "PERFORMANCE_RUNNING"
    save(out / "campaign-state.json", state)
    campaign.run(SimpleNamespace(output=out / "performance", images=inventory,
                                 emu=args.emu, jobs=args.jobs, **paths))
    state["status"] = "ANALYZING"
    save(out / "campaign-state.json", state)
    accepted = analyze.analyze(args.t13_root / "runs/images-v3", out / "performance",
                               args.t13_root / "runs/images-stream-v4", out / "performance",
                               out / "analysis", fu_latency=2)
    check.require(accepted["status"] == "T13_FAIR_CYCLE_COMPARISON_PASS", "performance gate failed")
    for path, digest in state["external_files"].items():
        check.require(sha(Path(path)) == digest, "external binary changed during campaign")
    for kind in ("files", "dependency_files"):
        for name, digest in pins[kind].items():
            check.require(sha(ROOT / name) == digest, "candidate source drift during campaign: " + name)
    state.update(status="T14_CANDIDATE_FULLCORE_PASS", finished=campaign.now())
    save(out / "campaign-state.json", state)
    print(state["status"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("t13-root", "t12-root", "output", "hardware-pins", "emu"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--jobs", type=int, choices=(1, 2, 4, 8), default=8)
    args = parser.parse_args()
    try:
        main(args)
    except Exception as exc:
        status_path = args.output / "campaign-state.json"
        if status_path.exists():
            state = load(status_path)
            state.update(status="FAILED", failed_stage=state["status"],
                         error=repr(exc), finished=campaign.now())
            save(status_path, state)
        raise
