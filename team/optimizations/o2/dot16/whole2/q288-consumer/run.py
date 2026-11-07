#!/usr/bin/env python3
"""Freeze/review, then run one P/whole2/plain-D/FR Q288 AM. No build or ABI probe."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import time

CONTRACT = "r3-dot16-whole2-q288-v1"
IMAGE_BUILDER_SHA = "211e35d232bc941950e20dee1633a1bea90148ba3b02e90ae3e540e0cf4e4d0d"
IMAGE_ELF_SHA = "9f7978f3d4be2b8793d979c2e6b84636476fc3547bd7da17441e2076ca9ffde0"
IMAGE_BIN_SHA = "ec900613377b8a023435a4eb88b9d3134e0da011675fc0dc4a45aae57d3149eb"
HARDWARE_RESULT_SHA = "e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f"
EMU_SHA = "f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d"
REF_SHA = "cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae"
FLASH_SHA = "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994"
GATE_SHA = "172551fb537e93f33937819b1a7625e39986726c039266750adadb73e8ccc05c"
HELPER_SHA = "db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3"
FLAGS = dict(VDOT_DOT16="1", VDOT_O2_ELASTIC="1", VDOT_T14_FUSED_INPUT="1",
             VDOT_O1_HANDOFF="0", VDOT_O1_TRACE="0", VDOT_O2_TRACE="0",
             VDOT_T12_TRACE="0", VDOT_T13_TRACE="0")
ABI = dict(bytes=1400, regs_int=0, regs_fp=256, csr=512, pc=656,
           hcsr=664, regs_vec=800, vcsr=1312, fcsr=1368, triggercsr=1376)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for raw in iter(lambda: f.read(1024 * 1024), b""):
            h.update(raw)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def read(path):
    return json.loads(Path(path).read_bytes())


def module(path, name, pin):
    need(digest(path) == pin, "module identity: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def check_pins(pins):
    for path, pin in pins.items():
        need(digest(path) == pin, "input changed: " + path)


def preflight(args):
    os.sched_setaffinity(0, {args.cpu})
    out, build = args.output.resolve(), args.image_build.resolve()
    need(args.output.is_absolute() and not out.exists(), "fresh absolute preflight output")
    need(0 < args.max_cycles <= 12000000 and 60 <= args.budget_seconds <= 14400
         and 8388608 <= args.stream_limit <= 268435456, "explicit bounded launch budget")
    need(not out.is_relative_to(build) and not build.is_relative_to(out), "separate image/preflight")
    status = read(build / "status.json")
    need(status["contract"] == CONTRACT and status["status"] == "DOT16_WHOLE2_Q288_IMAGE_STATIC_PASS"
         and status["inputs_unchanged"] is True and status["generated_inputs_unchanged"] is True
         and status["last_process_reaped"] is True and status["last_process_group_absent"] is True,
         "completed actual image build")
    need(digest(build / "paired16-target.elf") == status["elf_sha256"] == IMAGE_ELF_SHA
         and digest(build / "paired16-target.bin") == status["binary_sha256"] == IMAGE_BIN_SHA,
         "fixed actual image")
    builder = module(build / "inputs/image.py", "dot16_q288_frozen_builder", IMAGE_BUILDER_SHA)
    model = module(build / "inputs/model.py", "dot16_q288_frozen_model", builder.MODEL_SHA)
    actual = builder.inspect((build / "paired16-target.elf").read_bytes(),
                             (build / "inputs/base.elf").read_bytes(), model)
    need(json.loads(json.dumps(actual)) == read(build / "elf-check.json"), "actual ELF proof differs")
    manifest = read(build / "manifest.json")
    need(manifest["contract"] == CONTRACT and manifest["call_plan"] == builder.call_plan()
         and manifest["order"] == list(builder.ORDER) and manifest["methods"] == list(builder.METHODS)
         and manifest["calls_by_arm"] == dict(P=6, W=7, D=6, FR=10), "fixed guest plan")
    commands = read(build / "commands.json")
    need(len(commands) == 8 and all(r["exit_code"] == 0 and r["process_group_absent"] for r in commands),
         "all actual GNU children closed")
    check_pins(read(build / "inputs.json"))
    check_pins(read(build / "generated-inputs.json"))
    report_path = args.hardware_result.resolve()
    need(digest(report_path) == HARDWARE_RESULT_SHA, "fixed hardware result")
    report = read(report_path)
    need(report["status"] == "DOT16_FULLCORE_SMOKE_PASS"
         and report["qualification"]["fixed_six_legal_case_fullcore_difftest"] is True
         and report["abi"]["layout"] == ABI and report["abi"]["actual_dynamic_difftest_passed"] is True
         and report["source_identity"]["flags"] == FLAGS, "existing fixed hardware qualification")
    physical = report["runtime_inputs"]
    check_pins(physical)
    def unique(pin):
        paths = [p for p, h in physical.items() if h == pin]
        need(len(paths) == 1, "unique fixed physical input")
        return paths[0]
    emu, ref, flash, gate = (unique(h) for h in (EMU_SHA, REF_SHA, FLASH_SHA, GATE_SHA))
    need(report["emu"]["path"] == emu and report["emu"]["sha256"] == EMU_SHA, "physical EMU identity")
    out.mkdir(parents=True)
    snapshots = out / "inputs"
    snapshots.mkdir()
    for source, name, pin in (
            (Path(__file__).resolve(), "run.py", digest(__file__)),
            (Path(gate), "runtime_gate.py", GATE_SHA),
            (build / "inputs/process_helper.py", "process_helper.py", HELPER_SHA),
            (report_path, "hardware-result.json", HARDWARE_RESULT_SHA)):
        shutil.copyfile(source, snapshots / name)
        need(digest(snapshots / name) == pin, "preflight snapshot differs")
    pins = {str(p): digest(p) for p in build.rglob("*") if p.is_file()}
    pins.update(read(build / "inputs.json"))
    pins.update(physical)
    pins[str(report_path)] = HARDWARE_RESULT_SHA
    pins[str(Path(__file__).resolve())] = digest(__file__)
    pins.update({str(p): digest(p) for p in snapshots.iterdir()})
    check_pins(pins)
    profile = dict(schema=1, contract=CONTRACT, status="FROZEN_BEFORE_EMU",
        image_build=str(build), image=str(build / "paired16-target.bin"),
        image_sha256=IMAGE_BIN_SHA, elf_sha256=IMAGE_ELF_SHA,
        emu=emu, reference=ref, flash=flash, cpu=args.cpu,
        max_cycles=args.max_cycles, budget_seconds=args.budget_seconds,
        stream_limit_bytes=args.stream_limit, ram_size="128MB", seed=1,
        pins=pins, call_plan=builder.call_plan(), order=list(builder.ORDER),
        gate=str(snapshots / "runtime_gate.py"), helper=str(snapshots / "process_helper.py"),
        runtime_source=str(snapshots / "run.py"), runtime_sha256=digest(snapshots / "run.py"),
        hardware_flags=FLAGS, existing_abi=ABI, new_emu_runs=0,
        qualification="static current image plus fixed previously qualified hardware identities",
        target_runtime_qualified=False, performance_qualified=False,
        full_retirement_window_audited=False, asic_ppa_qualified=False)
    save(out / "profile.json", profile)
    result = dict(status="DOT16_WHOLE2_Q288_PREFLIGHT_PASS", profile=str(out / "profile.json"),
                  profile_sha256=digest(out / "profile.json"), input_files=len(pins),
                  new_emu_runs=0, new_builds=0, new_abi_probes=0)
    save(out / "result.json", result)
    print(json.dumps(result))
    return result


def guest_check(raw, reference, profile, gate):
    text = raw.decode("utf-8", errors="strict")
    gate.validate_failure_markers(text)
    plain = gate.normalize_console(text)
    need(re.search(r"CRITICAL ERROR|double trap|PMA check failed|Q_FAIL", plain, re.I) is None,
         "additional runtime/guest failure marker")
    need(plain.count("The first instruction of core 0 has commited. Difftest enabled.") == 1,
         "real DiffTest enabled banner")
    loaded = [v.strip() for v in re.findall(r"The reference model is ([^\r\n]+)", plain)]
    need(loaded == [reference], "exact loaded feature1 reference")
    need(plain.count("HIT GOOD TRAP") == 1, "one GOOD TRAP")
    lines = [line for line in plain.splitlines() if line.startswith(("Q_", "QW"))]
    prefix = [
        "Q_BEGIN contract=" + CONTRACT + " windows=10",
        "Q_MIN checked=1 outputs=288 slots=8",
        "Q_FUNCTIONAL calls=29 controls=5 outputs=8352 warm=10 extra=9"]
    prefix += [f'Q_CALL {i} {r["stage"]} {r["arm"]} {r["dataset"]}'
               for i, r in enumerate(profile["call_plan"])]
    end = "Q_END windows=10 full_calls=29 leaf_calls=0 inline_calls=29 probe_dots=1 failures=0"
    need(len(lines) == 43 and lines[:32] == prefix and lines[-1] == end,
         "complete ordered guest inventory")
    samples = []
    for i, line in enumerate(lines[32:42]):
        m = re.fullmatch(r"QW (\d+) (\d+) (\d+)", line)
        need(m is not None, "malformed QW")
        index, cycles, instructions = map(int, m.groups())
        need(index == i and 0 < cycles < 1 << 64 and 0 < instructions < 1 << 64,
             "QW order or counter range")
        samples.append(dict(index=i, arm=profile["order"][i],
                            cycles=cycles, instructions=instructions))
    return dict(full_q_calls=29, outputs_checked=8352, judge_fault_controls=5,
        judge_fault_controls_scope="shared judge; original first P/dataset1 call",
        fullmin_arm=1, fullmin_kind=0, fullmin_outputs=288, fullmin_performance_sample=False,
        samples=samples, expected_dot16_from_plan=67392, expected_dot8_probe_from_plan=1,
        retired_custom_count_verified=False, full_retirement_window_audited=False,
        loaded_reference=reference, complete_guest_sequence=True)


def run(args):
    profile_path = args.profile.resolve()
    need(digest(profile_path) == args.profile_sha256, "reviewed profile identity")
    profile = read(profile_path)
    need(profile["contract"] == CONTRACT and profile["status"] == "FROZEN_BEFORE_EMU",
         "frozen profile required")
    need(digest(__file__) == profile["runtime_sha256"], "run source differs from reviewed snapshot")
    check_pins(profile["pins"])
    out = args.output.resolve()
    need(args.output.is_absolute() and not out.exists(), "fresh absolute runtime output")
    need(not any(Path(p).is_relative_to(out) for p in profile["pins"]), "output contains input")
    os.sched_setaffinity(0, {profile["cpu"]})
    util = module(profile["helper"], "dot16_q288_runtime_helper", HELPER_SHA)
    gate = module(profile["gate"], "dot16_q288_runtime_gate", GATE_SHA)
    out.mkdir(parents=True)
    cwd = out / "cwd"
    cwd.mkdir()
    argv = [profile["emu"], "-i", profile["image"], "--flash=" + profile["flash"],
            "--ram-size=128MB", "--diff=" + profile["reference"],
            "--max-cycles=" + str(profile["max_cycles"]), "--seed=1"]
    receipt = dict(schema=1, contract=CONTRACT, status="RUNNING", started=util.stamp(),
        profile=str(profile_path), profile_sha256=args.profile_sha256, command=argv, cwd=str(cwd),
        cpu_affinity=sorted(os.sched_getaffinity(0)), budget_seconds=profile["budget_seconds"],
        stream_limit_bytes=profile["stream_limit_bytes"], process_started=False,
        target_runtime_qualified=False, performance_qualified=False,
        full_retirement_window_audited=False, asic_ppa_qualified=False)
    proc = None
    signals = dict(first=None, count=0)
    def interrupt(signum, frame):
        if signals["first"] is None:
            signals["first"] = signum
        signals["count"] += 1
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    def child_limits():
        limit = profile["stream_limit_bytes"]
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
    env = {k: os.environ[k] for k in ("HOME", "PATH") if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", LANG="C.UTF-8", LC_ALL="C.UTF-8", TZ="UTC",
               OMP_NUM_THREADS="1")
    save(out / "status.json", receipt)
    try:
        with (out / "stdout.log").open("wb") as stdout, (out / "stderr.log").open("wb") as stderr:
            need(signals["count"] == 0, "cancelled before child launch")
            deadline = time.monotonic() + profile["budget_seconds"]
            proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                                    start_new_session=True, preexec_fn=child_limits)
            receipt.update(process_started=True, pid=proc.pid, pgid=proc.pid)
            save(out / "status.json", receipt)
            print(json.dumps(dict(event="DOT16_WHOLE2_Q288_PROCESS_STARTED", pid=proc.pid, pgid=proc.pid,
                                  cpu=profile["cpu"], output=str(out))), flush=True)
            while True:
                if signals["count"]:
                    receipt["cancelled"] = True
                    raise InterruptedError("latched runtime signal " + str(signals["first"]))
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    receipt["timed_out"] = True
                    raise TimeoutError("fixed runtime budget exhausted")
                receipt["exit_code"] = proc.poll()
                if receipt["exit_code"] is not None:
                    break
                time.sleep(min(0.25, remaining))
        need(receipt["exit_code"] == 0 and not util.group_exists(proc.pid), "EMU exit/group gate")
        raw = (out / "stderr.log").read_bytes() + (out / "stdout.log").read_bytes()
        checked = guest_check(raw, profile["reference"], profile, gate)
        check_pins(profile["pins"])
        need(digest(profile_path) == args.profile_sha256, "profile changed during run")
        save(out / "checks.json", checked)
        receipt.update(status="DOT16_WHOLE2_Q288_FULLCORE_PASS", target_runtime_qualified=True,
            input_identities_unchanged=True, checks_sha256=digest(out / "checks.json"),
            qualification="this fixed complete-Q288 AM correctness and CSR observations only")
    except BaseException as exc:
        receipt.update(status="FAILED", error=repr(exc), target_runtime_qualified=False)
        raise
    finally:
        if proc is not None:
            try:
                if util.group_exists(proc.pid):
                    receipt["cleanup_requested"] = True
                    receipt["cleanup_complete"] = util.stop_group(proc)
            except BaseException as exc:
                receipt.update(status="FAILED", target_runtime_qualified=False,
                               cleanup_error=repr(exc))
            receipt["exit_code"] = proc.poll()
            receipt["process_reaped"] = proc.returncode is not None
            receipt["process_group_absent"] = not util.group_exists(proc.pid)
            if not receipt["process_reaped"] or not receipt["process_group_absent"]:
                receipt.update(status="FAILED", target_runtime_qualified=False,
                               cleanup_incomplete=True)
        changes = []
        for path, pin in {**profile["pins"], str(profile_path): args.profile_sha256}.items():
            try:
                actual = digest(path)
                if actual != pin:
                    changes.append(dict(path=path, expected=pin, actual=actual))
            except OSError as exc:
                changes.append(dict(path=path, error=repr(exc)))
        receipt["changed_inputs"] = changes
        receipt["input_identities_unchanged"] = not changes
        if changes:
            receipt.update(status="FAILED", target_runtime_qualified=False,
                           input_identity_error="input changed or unreadable after run")
        receipt["raw_logs"] = {n: dict(bytes=(out / n).stat().st_size, sha256=digest(out / n))
                               for n in ("stdout.log", "stderr.log") if (out / n).exists()}
        receipt["signals"] = dict(signals)
        if signals["count"]:
            receipt.update(status="FAILED", target_runtime_qualified=False, cancelled=True)
        receipt["finished"] = util.stamp()
        save(out / "status.json", receipt)
    need(receipt["status"] == "DOT16_WHOLE2_Q288_FULLCORE_PASS", "runtime failed after final checks")
    print(json.dumps(receipt))
    return receipt


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    a = sub.add_parser("preflight")
    a.add_argument("--image-build", required=True, type=Path)
    a.add_argument("--hardware-result", required=True, type=Path)
    a.add_argument("--output", required=True, type=Path)
    a.add_argument("--cpu", required=True, type=int, choices=range(4))
    a.add_argument("--max-cycles", required=True, type=int)
    a.add_argument("--budget-seconds", required=True, type=int)
    a.add_argument("--stream-limit", required=True, type=int)
    a = sub.add_parser("run")
    a.add_argument("--profile", required=True, type=Path)
    a.add_argument("--profile-sha256", required=True)
    a.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    (preflight if args.mode == "preflight" else run)(args)
