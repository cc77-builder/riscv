#!/usr/bin/env python3
"""Run both frozen T12 software plans on a current, source-bound O1 core.

Architectural checks and O1/O2 transaction checks are independent gates. Raw
software counter windows are not calibrated performance or a hardware A/B.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile

from check_extended import extended_audit
from run_extended_core import build_guard, module
from run_trace_core import ROOT, ARCHIVE_SHA256, now, require, save, sha

PLANS = {"original": 190, "lean": 199}


def extract_images(output):
    archive = ROOT / "team/evidence/james-fullcore-20261016/workloads.tar.gz"
    require(sha(archive) == ARCHIVE_SHA256, "frozen software archive changed")
    output.mkdir()
    inventory = {}
    total = 0
    with tarfile.open(archive, "r:gz") as source:
        for item in source:
            if not (item.name.startswith(("software-original/", "software-lean/"))
                    or item.name == "boot-flash.bin"):
                continue
            name = PurePosixPath(item.name)
            require(item.isfile() and not name.is_absolute() and ".." not in name.parts
                    and item.name not in inventory, "unsafe/duplicate software member")
            total += item.size
            require(total < 128 * 1024**2, "software archive exceeds bound")
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.extractfile(item).read())
            inventory[item.name] = sha(target)
    require("boot-flash.bin" in inventory, "missing boot flash")
    return inventory


def verify_plan_profile(profile, manifest, baseline):
    require(baseline in PLANS, "unknown software baseline")
    count = PLANS[baseline]
    require(type(profile.get("start")) is int and profile["start"] == 0 and type(profile.get("limit")) is int
            and profile["limit"] == count, "incomplete compiled software plan")
    require(profile.get("baseline") == manifest.get("baseline", "original") == baseline
            and len(manifest["schedule"]) == count, "wrong software plan identity")
    return count


def verify_archived_build(image):
    """Verify relocated ELF/bin/data against the sealed original build receipt.

    Source/compiler/library identities remain historical; their unavailable
    original absolute paths are not treated as a new compilation on this host.
    The caller separately pins the entire archive and extracted inventory.
    """
    receipt = json.loads((image / "workload-provenance.json").read_text())
    require((receipt["schema_version"], receipt["kind"], receipt["mode"], receipt["arch"])
            == (1, "t12", "full", "riscv64-xs"), "wrong archived build role")
    original = PurePosixPath(receipt["data_dir"]).parent
    for group in ("inputs_sha256", "images_sha256"):
        require(receipt[group], "missing archived artifact inventory")
        for name, digest in receipt[group].items():
            relative = PurePosixPath(name).relative_to(original)
            require(".." not in relative.parts, "unsafe archived build path")
            require(sha(image / relative) == digest, "archived compiled artifact changed: " + str(relative))
    require({PurePosixPath(p).relative_to(original).as_posix() for p in receipt["images_sha256"]}
            == {"test.bin", "test.elf"}, "incomplete archived ELF/bin pair")
    return dict(status="FROZEN_SOFTWARE_BUILD_VERIFIED", new_compilation=False,
                receipt_sha256=sha(image / "workload-provenance.json"))


def check_software(stdout, stderr, image, baseline, returncode, reference):
    compact = module("o1_compact_software", ROOT / "team/scripts/check_t12_compact.py")
    gate = module("o1_software_runtime_gate", ROOT / "team/optimizations/o1/audit/runtime_gate.py")
    require(returncode == 0, "software runtime failed")
    for stream in (stdout, stderr):
        gate.validate_failure_markers(stream)
    text = gate.normalize_console(stderr + stdout)
    require(text.count("Difftest enabled.") == 1, "missing/duplicate live DiffTest")
    require([p.strip() for p in re.findall(r"The reference model is ([^\r\n]+)", text)] == [str(reference)],
            "wrong or ambiguous loaded reference")
    profile = json.loads((image / "current-profile.json").read_text())
    manifest = json.loads((image / "data/manifest.json").read_text())
    count = verify_plan_profile(profile, manifest, baseline)
    checked = compact.check(text, image / "data", 0, count, returncode)
    plan = compact.aggregate([checked], image / "data")
    require(plan["executed"] == count and plan["baseline"] == baseline, "incomplete software plan")
    trace, _ = extended_audit(stderr.splitlines(), mode=2)
    require(trace["protocol"]["rob"]["committed"] > 0, "software lacks VDot commits")
    # T12 programs predate the T13 retirement markers. Preserve their raw
    # counters without presenting them as calibrated O2 retirement windows.
    return dict(status="O1_SOFTWARE_PLAN_PASS", architectural=plan, observation=trace,
                calibrated_performance=False, performance_ab=False)


def run(args):
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    args.created_output = True
    records = []
    save(out / "campaign.json", dict(status="PREPARING", started=now(), runs=records))
    build_guard(args, out, "before")
    guard = module("o1_software_artifacts", ROOT / "team/scripts/artifact_guard.py")
    reference = args.reference_root / "build/riscv64-nemu-interpreter-so"
    save(out / "reference-before.json", guard.verify_nemu(args.reference_root, reference, "reference"))
    images = out / "images"
    inventory = extract_images(images)
    save(out / "software.json", dict(archive_sha256=ARCHIVE_SHA256, files=inventory))
    code = [Path(__file__), *(ROOT / "team/optimizations/o1" / name for name in
            ("run_extended_core.py", "run_trace_core.py", "check_trace.py", "check_extended.py",
             "audit/runtime_gate.py")), ROOT / "team/scripts/check_t12_compact.py",
            ROOT / "team/scripts/artifact_guard.py", ROOT / "team/scripts/prepare-core-baseline.py"]
    emu = args.core / "build/emu"
    pins = {str(p): sha(p) for p in code + [emu, reference]}
    pins.update({str(images / p): h for p, h in inventory.items()})
    for name in ("source-binding.json", "compile-profile.json", "environment.txt", "rtl.sha256", "emu.sha256"):
        pins[str(args.receipt / name)] = sha(args.receipt / name)
    save(out / "inputs.json", pins)
    for path in code:
        target = out / "checker-snapshots" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())

    def stable():
        require(all(sha(Path(path)) == digest for path, digest in pins.items()), "runtime/code input changed")

    # At most two independent emulators; each stays single-core/single-threaded.
    # Only the coordinator writes shared progress, never a worker.
    def job(baseline):
        folder = out / baseline
        folder.mkdir()
        image = images / ("software-" + baseline)
        command = ["timeout", "120m", "stdbuf", "-o0", "-e0", str(emu), "-i", str(image / "test.bin"),
                   "--flash=" + str(images / "boot-flash.bin"), "--ram-size=128MB",
                   "--diff=" + str(reference), "--max-cycles=5000000", "--seed=1"]
        record = dict(baseline=baseline, status="RUNNING", started=now(), command=command,
                      cwd=str(args.core), image_sha256=sha(image / "test.bin"),
                      emu_sha256=sha(emu), reference_sha256=sha(reference),
                      host_concurrency=args.jobs, single_core=True, emu_threads=1)
        save(folder / "runtime.json", record)
        try:
            stable()
            save(folder / "software-build.json", verify_archived_build(image))
            verify_plan_profile(json.loads((image / "current-profile.json").read_text()),
                                json.loads((image / "data/manifest.json").read_text()), baseline)
            env = dict(os.environ)
            env.pop("XS_NEGATIVE_VECTOR_TARGET", None)
            with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
                rc = subprocess.run(command, cwd=args.core, env=env, stdout=stdout, stderr=stderr).returncode
            record.update(exit_code=rc, finished=now(),
                          raw_sha256={n: sha(folder / n) for n in ("stdout.log", "stderr.log")})
            save(folder / "runtime.json", record)
            stable()
            checked = check_software((folder / "stdout.log").read_text(), (folder / "stderr.log").read_text(),
                                     image, baseline, rc, reference)
            verify_archived_build(image)
            save(folder / "checked.json", checked)
            record.update(status=checked["status"], executed=checked["architectural"]["executed"])
        except Exception as error:
            record.update(status="FAILED", error=repr(error), finished=now())
        save(folder / "result.json", record)
        print(baseline, record["status"], record.get("error", ""), flush=True)
        return record

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(job, baseline) for baseline in PLANS]
        for future in as_completed(futures):
            records.append(future.result())
            save(out / "progress.json", records)
    stable()
    build_guard(args, out, "after")
    save(out / "reference-after.json", guard.verify_nemu(args.reference_root, reference, "reference"))
    passed = all(row["status"] == "O1_SOFTWARE_PLAN_PASS" for row in records) and len(records) == 2
    save(out / "campaign.json", dict(status="O1_SOFTWARE_PLANS_PASS" if passed else "FAILED",
         finished=now(), runs=records, emu_sha256=sha(emu), host_concurrency=args.jobs,
         default_o1=False, performance_ab=False))
    return 0 if passed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("core", "receipt", "pack", "reference-root", "output"):
        parser.add_argument("--" + name, type=lambda x: Path(x).resolve(), required=True)
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    try:
        code = run(args)
    except Exception as error:
        if getattr(args, "created_output", False):
            failure = dict(status="FAILED", error=repr(error), finished=now())
            if (args.output / "progress.json").is_file():
                failure["runs"] = json.loads((args.output / "progress.json").read_text())
            save(args.output / "campaign.json", failure)
        raise
    raise SystemExit(code)
