"""Run source-bound B0/H1 paired full-core measurements, local only."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import statistics
import subprocess
import tarfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_profile import build_profile, validate_pair
from threading import Lock

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
DEFAULT_WORK = Path("/home/riscv/riscv-lab/o2-h1-performance-20261021")
IMAGE_ROOT = Path("/home/riscv/riscv-lab/unified-vdot-benchmark-20261017/runs/ours-images-02")
B0_PINS = Path("/home/riscv/riscv-lab/o2-fullcore-20261019/build-03/hardware-inputs.json")
H1_PINS = Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021/build-01/hardware-inputs.json")
REFERENCE = Path("/home/riscv/riscv-lab/t12-regression-20261013/nemu/reference/build/riscv64-nemu-interpreter-so")
FLASH = Path("/home/riscv/riscv-lab/t12-regression-20261013/repo/team/workloads/hello-vadd/build/boot-flash.bin")
MODES = ("b0", "h1")
SCENARIOS = ("single", "chain", "batch", "stream")
LOCK = Lock()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def validate_loaded_reference(text, reference, normalize):
    paths = [s.strip() for s in re.findall(r"The reference model is ([^\r\n]+)", normalize(text))]
    require(paths == [str(reference)], "wrong or ambiguous loaded reference")


def expected_names():
    return (["smoke-d0-s00"] + [f"functional-d0-s{i:02d}" for i in range(3)]
            + [f"performance-d{d}-s{s:02d}" for d in range(3) for s in range(4)])


def observer_gate(mode, analysis, expected):
    require(mode in MODES, "unknown hardware mode")
    require(analysis["status"] == "O2_TRACE_PASS", "incomplete/wrong O2 observer")
    require(analysis["schema"]["slots"] == 2, "wrong two-slot schema")
    require(all(analysis.get(k) == 0 for k in
                ("pending_count", "pending_div_count", "unfinished_rob_count")),
            "performance trace did not drain")
    require(analysis["counts"].get("COMMIT", 0) == expected,
            "incorrect committed custom instruction count")


def verify_hashes(files):
    for name, digest in files.items():
        require(sha(name) == digest, "artifact hash drift: " + name)


def image_inventory(images, check):
    rows = json.loads((images / "images.json").read_text())["images"]
    require([x["name"] for x in rows] == expected_names(), "exact frozen 16-image inventory required")
    frozen = ROOT / "team/evidence/unified-vdot-20261017/archive"
    archive = frozen / "测试镜像与构建快照.tar.gz"
    expected = json.loads((frozen / "文件校验.json").read_text())["files"]["测试镜像与构建快照.tar.gz"]
    require(sha(archive) == expected, "sealed workload archive drift")
    pins = {str(archive): expected, str(images / "images.json"): sha(images / "images.json")}
    compared = []
    with tarfile.open(archive) as tar:
        for member in tar:
            if member.isfile() and member.name.startswith("ours/"):
                relative = member.name.removeprefix("ours/")
                path = images / relative
                body = tar.extractfile(member).read()
                require(path.read_bytes() == body, "image differs from sealed archive: " + relative)
                pins[str(path)] = hashlib.sha256(body).hexdigest()
                compared.append(relative)
    require(len(compared) == 208, "unexpected sealed ours input inventory")
    plan_count = 0
    for row in rows:
        build = Path(row["path"])
        require(build == images / row["name"], "foreign image path")
        manifest = json.loads((build / "data/manifest.json").read_text())
        require(manifest["variant"] == "ours" and manifest["boundary"] == "pinned-XiangShan-fence-serialized-v2",
                "wrong workload contract")
        check.verify_generation(build, manifest)
        check.check_compiled_cases(build / "vdot-perf.elf", manifest)
        check.elf_kernels(build / "vdot-perf.elf")
        plan_count += len(manifest["plan"])
    require(plan_count == 215, "unexpected total workload windows")
    return rows, pins, {"sealed_ours_files_verified": len(compared), "windows_per_mode": plan_count}


def expected_commits(manifest):
    return sum(manifest["rows"][p["index"]]["dots"] for p in manifest["plan"]
               if manifest["rows"][p["index"]]["method"] == "vdot")


def summarize(samples):
    result = []
    measured = [s for s in samples if s["stage"] == "performance" and s["phase"] == "measured" and s["replay"] == 0]
    require(len(measured) == 192, "expected 192 measured windows")
    for scenario in SCENARIOS:
        per_mode = {}
        paired = {}
        for mode in MODES:
            selected = [s for s in measured if s["mode"] == mode and s["scenario"] == scenario]
            methods = {m: {(s["dataset"], s["repeat"]): s for s in selected if s["method"] == m}
                       for m in ("vdot", "rvv")}
            require(len(methods["vdot"]) == 12 and methods["vdot"].keys() == methods["rvv"].keys(),
                    "missing/duplicate measurement pair")
            require(len(selected) == 24, "duplicate measured rows")
            custom = [methods["vdot"][k]["cycles"] for k in sorted(methods["vdot"])]
            base = [methods["rvv"][k]["cycles"] for k in sorted(methods["rvv"])]
            dots = {s["dots"] for s in selected}
            require(len(dots) == 1 and min(custom + base) > 0, "unequal work or nonpositive cycles")
            n = dots.pop()
            per_mode[mode] = dict(custom_mean_cycles=statistics.mean(custom),
                                  custom_median_cycles=statistics.median(custom),
                                  custom_min_cycles=min(custom), custom_max_cycles=max(custom),
                                  custom_mean_cycles_per_dot=statistics.mean(custom) / n,
                                  rvv_mean_cycles=statistics.mean(base),
                                  rvv_min_cycles=min(base), rvv_max_cycles=max(base),
                                  speedup_ratio_of_sums=sum(base) / sum(custom),
                                  custom_sum_cycles=sum(custom), rvv_sum_cycles=sum(base),
                                  samples_per_method=12, dots=n)
            paired[mode] = methods
        require(paired["b0"]["vdot"].keys() == paired["h1"]["vdot"].keys(), "cross-mode sample keys differ")
        for method in ("vdot", "rvv"):
            for k, a in paired["b0"][method].items():
                b = paired["h1"][method][k]
                require(all(a[f] == b[f] for f in ("instructions", "dots", "n", "seq", "image_sha256")),
                        "cross-mode workload/retirement mismatch")
        t, o = per_mode["b0"], per_mode["h1"]
        result.append(dict(scenario=scenario, **per_mode,
                           custom_cycle_reduction=1 - o["custom_sum_cycles"] / t["custom_sum_cycles"],
                           custom_b0_over_h1=t["custom_sum_cycles"] / o["custom_sum_cycles"],
                           rvv_cycle_reduction=1 - o["rvv_sum_cycles"] / t["rvv_sum_cycles"],
                           investigation_required=any(paired["h1"][method][k]["cycles"] > a["cycles"]
                               for method in ("vdot", "rvv") for k, a in paired["b0"][method].items())))
    return result


def paired_deltas(samples):
    selected = [s for s in samples if s["stage"] == "performance"
                and s["phase"] == "measured" and s["replay"] == 0]
    require(len(selected) == 192, "expected 192 formal windows")
    groups = {m: {} for m in MODES}
    for s in selected:
        require(s["mode"] in MODES, "unknown sample mode")
        key = tuple(s[k] for k in ("scenario", "method", "dataset", "repeat", "seq", "image_sha256"))
        require(key not in groups[s["mode"]], "duplicate paired window")
        require(type(s["cycles"]) is int and s["cycles"] > 0, "nonpositive/noninteger cycles")
        groups[s["mode"]][key] = s
    require(len(groups["b0"]) == len(groups["h1"]) == 96
            and groups["b0"].keys() == groups["h1"].keys(), "missing/mismatched cross-version windows")
    rows = []
    for key, a in sorted(groups["b0"].items()):
        b = groups["h1"][key]
        require(all(a[k] == b[k] for k in ("dots", "n", "instructions")), "work/retirement mismatch")
        rows.append(dict(zip(("scenario", "method", "dataset", "repeat", "seq", "image_sha256"), key),
                         b0_cycles=a["cycles"], h1_cycles=b["cycles"],
                         delta_cycles=b["cycles"] - a["cycles"], instructions=a["instructions"],
                         dots=a["dots"]))
    return rows


def compare_replays(rows):
    baseline = {}
    checked = 0
    for row in rows:
        key = row["mode"], row["image"]
        sample = [(s["seq"], s["cycles"], s["instructions"]) for s in row["samples"]]
        if row["replay"] == 0:
            require(key not in baseline, "duplicate base run")
            baseline[key] = sample
        else:
            require(key in baseline and sample == baseline[key], "nondeterministic replay: " + str(key))
            checked += 1
    require(checked == 4, "expected four additional batch replay jobs")
    return checked


def run(args):
    require(not args.output.exists(), "output already exists; use a new attempt")
    args.output.mkdir(parents=True)
    out = args.output
    state = {"status": "PREFLIGHT", "started_utc": now(), "output": str(out), "new_emu_jobs": 0,
             "host_concurrency": 2, "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
             "command": [os.sys.executable, *os.sys.argv]}
    save(out / "state.json", state)
    records = []
    try:
        check = load_module("o1_unified_window_check", ROOT / "team/workloads/unified-vdot/check.py")
        observers = {
            "b0":load_module("g4_o1_observer",ROOT/"team/optimizations/o2/fullcore/analyze.py"),
            "h1":load_module("g4_o2_observer",ROOT/"team/optimizations/o2/fullcore/analyze.py")}
        gate=load_module("g4_strict_runtime_gate",ROOT/"team/optimizations/o1/audit/runtime_gate.py")
        fatal=load_module("g4_fatal_output",ROOT/"team/optimizations/o2/fullcore/workloads/check.py")
        pins = {m: json.loads(p.read_text()) for m, p in (("b0", args.b0_pins), ("h1", args.h1_pins))}
        validate_pair(pins["b0"], pins["h1"])
        profile_files,profile=build_profile(args.b0_pins.parent,args.h1_pins.parent)
        save(out/"build-profile.json",profile)
        emulators = profile["emulator_paths"]
        files = dict(profile_files)
        for group in ("files", "dependency_files"):
            files.update({str(ROOT / name): digest for name, digest in pins["h1"][group].items()})
        for mode in MODES:
            files[emulators[mode]] = pins[mode]["emu_sha256"]
            save(out / (mode + "-hardware-pins.json"), pins[mode])
        files[str(args.h1_pins)] = sha(args.h1_pins)
        files[str(args.b0_pins)] = sha(args.b0_pins)
        files[str(args.reference)] = "efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4"
        files[str(args.flash)] = "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994"
        for auxiliary in (ROOT / "build/constantin.txt", ROOT / "build/plusArgs"):
            if auxiliary.is_file():
                files[str(auxiliary)] = sha(auxiliary)
        driver_paths = [Path(__file__), HERE/"CONTRACT.md", HERE/"build_profile.py", HERE/"results.py",Path(check.__file__),
                        *[Path(x.__file__) for x in observers.values()],Path(gate.__file__),Path(fatal.__file__),
                        ROOT/"team/workloads/unified-vdot/generate.py"]
        driver_paths = list(dict.fromkeys(driver_paths))
        files.update({str(p): sha(p) for p in driver_paths})
        for p in driver_paths:
            body=subprocess.check_output(["git","show",state["source_commit"]+":"+p.relative_to(ROOT).as_posix()],cwd=ROOT)
            require(hashlib.sha256(body).hexdigest()==sha(p),"runtime driver must be committed: "+str(p))

        images, input_pins, image_check = image_inventory(args.images, check)
        files.update(input_pins)
        verify_hashes(files)
        save(out / "artifact-pins.json", files)
        save(out / "input-audit.json", image_check)
        snapshot = out / "checker-snapshots"
        snapshot.mkdir()
        for p in driver_paths:
            relative = p.relative_to(ROOT)
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
        state.update(status="RUNNING", planned_jobs=36, image_identity="identical frozen ELF/bin for both modes",
                     build_variable="O2 B0/H1 result storage; shared O2/T13 observers", preflight_finished_utc=now())
        save(out / "state.json", state)

        def execute(mode, image, replay):
            directory = out / mode / image["suite"] / (image["name"] + f"-r{replay}")
            directory.mkdir(parents=True)
            build = Path(image["path"])
            binary = build / "vdot-perf.bin"
            emu = emulators[mode]
            command = ["timeout", "120m", "stdbuf", "-o0", "-e0", emu, "-i", str(binary),
                       "--flash=" + str(args.flash), "--ram-size=128MB", "--diff=" + str(args.reference),
                       "--max-cycles=2000000", "--seed=1"]
            record = {"mode": mode, "image": image["name"], "name": mode + "/" + image["name"] + f"-r{replay}",
                      "stage": image["suite"], "build": str(build), "replay": replay,
                      "command": command, "cwd": str(ROOT), "started_utc": now(), "status": "RUNNING",
                      "files": {str(p): files[str(p)] for p in (Path(emu), args.reference, args.flash, binary)},
                      "single_core": True, "emu_threads": 1,
                      "runtime_environment": {k: os.environ.get(k) for k in ("NOOP_HOME", "NEMU_HOME", "CONSTANTIN_ROOT")}}
            save(directory / "runtime.json", record)
            try:
                verify_hashes(files)
                with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
                    rc = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr).returncode
                record["exit_code"] = rc
                (directory / "exit-code.txt").write_text(str(rc) + "\n")
                record["raw_sha256"] = {n: sha(directory / n) for n in ("stdout.log", "stderr.log")}
                save(directory / "result.json", record)
                require(rc == 0, "nonzero EMU exit")
                stdout = (directory / "stdout.log").read_text()
                stderr = (directory / "stderr.log").read_text()
                for stream in (stdout, stderr):
                    fatal.reject_fatal_output(stream)
                    gate.validate_failure_markers(stream)
                validate_loaded_reference(stderr + stdout, args.reference, gate.normalize_console)
                windows = check.verify(build, directory)
                analysis = observers[mode].analyze(stderr+stdout)
                manifest=json.loads((build/"data/manifest.json").read_text())
                expected=expected_commits(manifest)
                observer_gate(mode,analysis,expected)
                record.update(status="PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS",
                              samples=[dict(s, mode=mode, stage=image["suite"], replay=replay,
                                            image=image["name"], image_sha256=sha(binary)) for s in windows["samples"]],
                              observation_counts=analysis["counts"], expected_vdot_commits=expected)
                save(directory / "window-result.json", windows)
                save(directory / "observation.json", analysis)
                verify_hashes(files)
            except Exception as exc:
                record.update(status="FAILED", error=repr(exc))
            record["finished_utc"] = now()
            save(directory / "result.json", record)
            with LOCK:
                records.append(record)
                save(out / "progress.json", [{k: v for k, v in r.items() if k != "samples"} for r in records])
                state["new_emu_jobs"] = len(records)
                save(out / "state.json", state)
                print(record["name"], record["status"], record.get("error", ""), flush=True)
            return record

        def pair(task):
            index, image, replay = task
            order = MODES if (index + replay) % 2 == 0 else tuple(reversed(MODES))
            return [execute(m, image, replay) for m in order]

        for stage in ("smoke", "functional", "performance", "replay"):
            state["stage"] = stage
            save(out / "state.json", state)
            if stage == "replay":
                batch = next(x for x in images if x["name"] == "performance-d0-s02")
                tasks = [(100, batch, replay) for replay in (1, 2)]
            else:
                tasks = [(i, x, 0) for i, x in enumerate(images) if x["suite"] == stage]
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = [f.result() for f in as_completed([pool.submit(pair, t) for t in tasks])]
            require(all(r["status"] == "PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS"
                        for pair_rows in results for r in pair_rows), "stage failed: " + stage)
            print(stage, "PAIRED_STAGE_PASS", flush=True)
        require(len(records) == 36, "incomplete jobs")
        extra = compare_replays(records)
        all_samples = [s for r in records for s in r["samples"]]
        stats = summarize(all_samples)
        deltas = paired_deltas(all_samples)
        for mode in MODES:
            batch_rows = [r for r in records if r["mode"] == mode and r["replay"] == 0 and "s02" in r["image"]
                          and r["stage"] == "performance"]
            key="TRIPLE_OVERLAP"
            require(sum(r["observation_counts"].get(key,0) for r in batch_rows)>0,
                    "selected pipeline behavior not observed: "+mode)
        verify_hashes(files)
        result = {"status": "B0_H1_PAIRED_PERFORMANCE_PASS", "started_utc": state["started_utc"], "finished_utc": now(),
                  "new_emu_jobs": 36, "image_count_per_mode": 16, "validated_windows": len(all_samples),
                  "measured_windows": 192, "additional_deterministic_replays": extra, "rows": stats,
                  "samples": all_samples, "runs": records, "artifact_inputs_unchanged": True,
                  "clock": "RTL global cycles; host elapsed time excluded", "overhead_subtracted": False,
                  "performance_measured": True, "new_github_push": False,
                  "paired_measured_windows": deltas,
                  "cycle_nonregression_pass": all(s["delta_cycles"] <= 0 for s in deltas),
                  "exact_measured_cycle_equality": all(s["delta_cycles"] == 0 for s in deltas)}
        save(out / "result.json", result)
        state.update(status=result["status"], finished_utc=result["finished_utc"])
        save(out / "state.json", state)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        state.update(status="FAILED", error=repr(exc), finished_utc=now())
        save(out / "state.json", state)
        save(out / "failure.json", state)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--images", type=Path, default=IMAGE_ROOT)
    parser.add_argument("--h1-pins", type=Path, default=H1_PINS)
    parser.add_argument("--b0-pins", type=Path, default=B0_PINS)
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--flash", type=Path, default=FLASH)
    raise SystemExit(run(parser.parse_args()))
