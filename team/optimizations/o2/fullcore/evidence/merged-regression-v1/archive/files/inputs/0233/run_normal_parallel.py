"""Run frozen full-core workloads against one newly built O2 traced emulator.

This driver never builds hardware or images. It keeps every real exit code and
raw stream, continues independent jobs after a failure, and never converts a
partial observation or incomplete control coverage into a passing suite.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path('/home/lizufan/riscv-lab/xiangshan')
HERE = ROOT / "team/optimizations/o2/fullcore"
DEFAULT_T12 = Path("/home/riscv/riscv-lab/t12-regression-20261013")
DEFAULT_T14 = Path("/home/riscv/riscv-lab/t14-optimization-20261015")
DEFAULT_DENSE = Path("/home/riscv/riscv-lab/t13-performance-20261015/runs/images-v3/performance-d0-s06")
PIN_FIELDS = {
    "config": "MinimalConfig", "NUM_CORES": 1, "EMU_THREADS": 1,
    "VDOT_O2_ELASTIC": "1", "VDOT_O1_HANDOFF": "0", "VDOT_O1_TRACE": "0", "VDOT_T14_FUSED_INPUT": "1",
    "VDOT_O2_TRACE": "1", "VDOT_T12_TRACE": "0", "VDOT_T13_TRACE": "1",
}
FROZEN = {
    "reference": "efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4",
    "negative": "9b3aecf362b7c7ddb4f8bace355c2e0ee2cc919fd5f59eefc641db220ab40df0",
    "flash": "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994",
    "hello": "45d47558d3be5909aec37a4a2e1f51111a6019000dd58fe915f3a19390e5c33f",
    "control": "b447c98209f5074072d7e36c77e63e92f8bd51a2cc05e2dbe7cfe857f4d37df7",
}
MATRIX_SHA = (
    "b8b7e1a7032070bdfdfc2a747ab6453011ea9959ebd5ac52ca21b439d4d113b3",
    "00329be8408c06da9511a5557bf9aab9239e4dce6b1d65fec6bee7734bea5b88",
    "a5e6663a9e2cb7348a3bcd2f719ba802c7d5af173f371e9278ec2435a8478923",
    "fd877e6cad537b709984101efd1f56ad1e783cd1740a51e699244c85e73e2f98",
    "7e7904987ba2dedb488b9db0a0d27a9d5a234d31d34be56ac5dfe33196a303dc",
    "1b86f711b441e10c219c0c5a4be43f7d679a108e9fa48a06bb6971aa3b09449b",
    "b91c6aa3e3bfba647c94073a52a2ff2e60d92707b361c87643a68d71b9c0d538",
    "66589580f960d5cd484812d2908ed676fc569a021fff809d76a7a35fd499755b",
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp():
    return datetime.now().astimezone().isoformat()


def save(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Dataclass-based observation models may look up their defining module.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_pin_fields(pins):
    for key, expected in PIN_FIELDS.items():
        require(type(pins.get(key)) is type(expected) and pins.get(key) == expected,
                f"wrong hardware pin {key}: expected {expected!r}")
    require(re.fullmatch(r"[0-9a-f]{40}", pins.get("source_commit", "")) is not None,
            "missing full source_commit")
    require(re.fullmatch(r"[0-9a-f]{64}", pins.get("emu_sha256", "")) is not None,
            "missing EMU SHA-256")
    for group in ("files", "dependency_files"):
        require(isinstance(pins.get(group), dict) and pins[group], "missing " + group)
        for name, digest in pins[group].items():
            path = Path(name)
            require(not path.is_absolute() and ".." not in path.parts,
                    "hardware pin must be a safe checkout-relative path")
            require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
                    "invalid source digest: " + name)


def hardware_guard(pins, emu, root=ROOT):
    validate_pin_fields(pins)
    for group in ("files", "dependency_files"):
        for name, digest in pins[group].items():
            require(sha(root / name) == digest, "hardware source drift: " + name)
    require(sha(emu) == pins["emu_sha256"], "EMU does not match build pins")


def validate_failure_markers(text, negative=False):
    gate = load_module("o2_runtime_gate", ROOT / "team/optimizations/o1/audit/runtime_gate.py")
    gate.validate_failure_markers(text, negative=negative)


def validate_negative(text, return_code):
    gate = load_module("o2_runtime_gate", ROOT / "team/optimizations/o1/audit/runtime_gate.py")
    return gate.validate_negative(text, return_code)


def validate_observation(result, negative=False):
    expected = "O2_PARTIAL_TRACE_AUDIT" if negative else "O2_TRACE_PASS"
    require(result.get("status") == expected, "wrong/incomplete observation status: " + str(result.get("status")))



O2_REQUIRED_COVERAGE = ("MULTI_INFLIGHT", "TRIPLE_OVERLAP", "FULL_STALL",
                        "KILL_P", "KILL_R", "PARTIAL_KILL")


LEGACY_COVERAGE = ("accepted_younger_squashed", "inflight_fu_killed",
                   "shared_vfex4_fu_kinds", "shared_vfex4_backpressure",
                   "vdot_writeback_backpressure", "rob_wrap_repeated", "ftq_wrap_repeated")


def classify_control(result):
    """Legacy F2v coverage must stand alone; report O2 coverage separately."""
    legacy = result.get("legacy_coverage", {})
    require(result.get("legacy_coverage_complete") is True and
            set(legacy) == set(LEGACY_COVERAGE) and all(value is True for value in legacy.values()),
            "control architectural or legacy coverage gate failed")
    require(result.get("status") in ("O2_CONTROL_REGRESSION_PASS", "O2_COVERAGE_INCOMPLETE"),
            "unexpected control coverage verdict")
    required = result.get("o2_coverage", {})
    require(set(required) == {key.lower() for key in O2_REQUIRED_COVERAGE} and
            all(type(v) is bool for v in required.values()), "invalid O2 coverage schema")
    complete = all(required.values())
    require(result.get("o2_coverage_complete") is complete, "contradictory O2 coverage verdict")
    require((result["status"] == "O2_CONTROL_REGRESSION_PASS") is complete,
            "control status disagrees with O2 coverage")
    return {"status": "O2_CONTROL_LEGACY_PASS",
            "control_coverage_status": result["status"],
            "o2_coverage": {key.upper(): value for key, value in required.items()},
            "o2_coverage_complete": complete}


def coverage_union(records):
    sources = {key: [] for key in O2_REQUIRED_COVERAGE}
    for record in records:
        if record.get("observation_status") != "O2_TRACE_PASS" or record.get("status") not in (
                "HELLO_VADD_PASS", "VDOT_MATRIX_SHARD_PASS", "O2_CONTROL_LEGACY_PASS",
                "O2_DENSE_ELASTIC_AND_WINDOWS_PASS", "O2_SUPPLEMENT_PASS"):
            continue
        counts = record.get("observation_counts", {})
        for key in sources:
            value = counts.get(key, 0)
            require(type(value) is int and value >= 0, "invalid coverage count")
            if value:
                sources[key].append({"name": record["name"], "count": value})
    return {"required": list(O2_REQUIRED_COVERAGE), "sources": sources,
            "complete": all(sources.values()),
            "missing": [key for key, evidence in sources.items() if not evidence]}


def assess_suite(records, matrix_image):
    expected = {"hello-vadd", "negative-vdot", "control", "dense-batch128"} | {f"functional-{i}" for i in range(8)}
    by_name = {record["name"]: record for record in records}
    complete_inventory = len(records) == 12 and set(by_name) == expected
    negative = by_name.get("negative-vdot", {})
    normal = by_name.get("functional-0", {})
    negative_image = negative.get("files", {}).get(str(matrix_image))
    recovery = (negative.get("status") == "EXPECTED_VDOT_HIGHBIT_REJECTION" and
                normal.get("status") == "VDOT_MATRIX_SHARD_PASS" and
                negative_image is not None and negative_image == normal.get("files", {}).get(str(matrix_image)) and
                bool(negative.get("finished")) and bool(normal.get("started")) and
                datetime.fromisoformat(normal["started"]) >= datetime.fromisoformat(negative["finished"]))
    ctl = by_name.get("control", {}).get("status")
    dense_complete = by_name.get("dense-batch128", {}).get("status") == "O2_DENSE_ELASTIC_AND_WINDOWS_PASS"
    control_complete = ctl == "O2_CONTROL_LEGACY_PASS"
    coverage = coverage_union(records)
    coverage.update(legacy_control_complete=control_complete, dense_elastic_complete=dense_complete)
    normal_jobs_pass = (by_name.get("hello-vadd", {}).get("status") == "HELLO_VADD_PASS" and
                       all(by_name.get(f"functional-{i}", {}).get("status") == "VDOT_MATRIX_SHARD_PASS" for i in range(8)))
    observation_pass = all(r.get("observation_status") == (
        "O2_PARTIAL_TRACE_AUDIT" if r["name"] == "negative-vdot" else "O2_TRACE_PASS") for r in records)
    return complete_inventory and normal_jobs_pass and observation_pass and recovery and control_complete and dense_complete, recovery, coverage


def validate_runtime(text, selected_ref):
    require("The first instruction of core 0 has commited. Difftest enabled." in text,
            "missing real DiffTest runtime banner")
    uncolored = re.sub(r"\x1b\[[0-9;]*m", "", text)
    loaded = [line.strip() for line in re.findall(r"The reference model is ([^\r\n]+)", uncolored)]
    require(loaded == [str(selected_ref)], "wrong or ambiguous loaded reference path")


def run_process(command, directory, env):
    """Keep streams separate: derived transcript is stderr followed by stdout."""
    with (directory / "stdout.log").open("wb") as out, (directory / "stderr.log").open("wb") as err:
        rc = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err).returncode
    stdout = (directory / "stdout.log").read_bytes()
    stderr = (directory / "stderr.log").read_bytes()
    (directory / "run.log").write_bytes(stderr + stdout)
    (directory / "exit-code.txt").write_text(str(rc) + "\n", encoding="utf-8")
    return rc, {name: sha(directory / name) for name in ("stdout.log", "stderr.log", "run.log")}


def preflight(args, guard, perf):
    pins = None
    if not args.preflight_only:
        pins = json.loads(args.hardware_pins.read_text())
        hardware_guard(pins, args.emu)
    paths = {
        "reference": args.t12_root / "nemu/reference/build/riscv64-nemu-interpreter-so",
        "negative": args.t12_root / "build-evidence/negative-reference.so",
        "flash": args.t12_root / "repo/team/workloads/hello-vadd/build/boot-flash.bin",
        "hello": args.t12_root / "repo/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin",
        "control": args.t14_root / "runs/control-sweep-02/vdot-regression.bin",
    }
    for name, digest in FROZEN.items():
        if name == "negative":
            require(not paths[name].exists(), "partial campaign requires the frozen negative to remain missing")
            continue
        require(sha(paths[name]) == digest, "frozen input drift: " + name)
    paths["dense"] = args.dense_build / "vdot-perf.bin"
    frozen_dense = ROOT / "team/evidence/t13-performance-20261015/images-v3/performance-d0-s06"
    dense_files = ["build.json", "vdot-perf.bin", "vdot-perf.elf", "data/manifest.json",
                   "data/kernels.S", "data/cases.h", "source/generate.py", "source/main.c", "source/Makefile"]
    for name in dense_files:
        # Some sealed evidence stores textual files compressed; its original
        # bytes remain authoritative through the unchanged T13 raw_bytes API.
        require((args.dense_build / name).read_bytes() == perf.raw_bytes(frozen_dense / name),
                "dense input differs from frozen T13 archive: " + name)
    dense_manifest = json.loads((args.dense_build / "data/manifest.json").read_text())
    perf.verify_generation(args.dense_build, dense_manifest)
    perf.check_compiled_cases(args.dense_build / "vdot-perf.elf", dense_manifest)
    # The small fault wrapper has a compiled-in absolute dlopen/DT_NEEDED path.
    linked_reference = DEFAULT_T12 / "nemu/reference/build/riscv64-nemu-interpreter-so"
    require(paths["reference"].resolve() == linked_reference.resolve(),
            "frozen negative wrapper requires its original normal-reference path")
    reference = guard.verify_nemu(args.t12_root / "nemu/reference", paths["reference"], "reference")
    control_build = args.t14_root / "runs/control-sweep-02"
    frozen_control = ROOT / "team/evidence/t14-optimization-20261016/control-sweep/build"
    require((control_build / "build.json").read_bytes() == (frozen_control / "build.json").read_bytes(),
            "control build receipt differs from frozen archive")
    control_receipt = json.loads((control_build / "build.json").read_text())
    for name, digest in control_receipt["files"].items():
        require(sha(control_build / name) == digest, "frozen control build drift: " + name)
    parent = ROOT / "team/evidence/t10-t11-fullcore-20261013/parent"
    corpus = [json.loads(line) for line in (parent / "cases.jsonl").read_text().splitlines()]
    corpus += json.loads((parent / "exceptions.json").read_text())
    expected = {case["id"]: case for case in corpus}
    matrix = args.t12_root / "runs/t11-matrix-canonical"
    builds, seen, executed = [], {}, 0
    for index, digest in enumerate(MATRIX_SHA):
        data, build = matrix / f"data-{index}", matrix / f"build-{index}"
        image = build / "vdot-exceptions.bin"
        require(sha(image) == digest, f"frozen matrix image drift: {index}")
        receipt = guard.verify_build(build, image, data, "vdot", "full")
        builds.append(receipt)
        cases = [json.loads(line) for line in (data / "cases.jsonl").read_text().splitlines()]
        cases += json.loads((data / "exceptions.json").read_text())
        for case in cases:
            require(case == expected.get(case["id"]), "matrix differs from parent corpus")
            require(case["id"] not in seen or case["id"] == "D00", "unexpected matrix duplicate")
            seen[case["id"]] = case
            executed += 1
    require(set(seen) == set(expected) and len(seen) == 117 and executed == 124,
            "incomplete fixed matrix")
    # Include every checker in the run identity; a later checker change cannot
    # silently reinterpret the same run under the original receipt.
    driver_files = [Path(__file__), HERE / "analyze.py", HERE / "check_control.py",
                    ROOT / "team/optimizations/o1/audit/runtime_gate.py",
                    ROOT / "team/scripts/artifact_guard.py", ROOT / "team/scripts/check-vdot-run.py",
                    ROOT / "team/workloads/vdot-perf/check.py", Path(__file__).with_name("schedule_resume.py")]
    input_files = {str(path): sha(path) for name, path in paths.items() if name != "negative"}
    input_files.update({str(args.dense_build / name): sha(args.dense_build / name) for name in dense_files})
    input_files[str(control_build / "build.json")] = sha(control_build / "build.json")
    for name, digest in control_receipt["files"].items():
        input_files[str(control_build / name)] = digest
    for index, receipt in enumerate(builds):
        for group in ("source_sha256", "inputs_sha256", "images_sha256", "am_libraries_sha256"):
            input_files.update(receipt.get(group, {}))
        input_files[str(matrix / f"build-{index}/workload-provenance.json")] = sha(matrix / f"build-{index}/workload-provenance.json")
    return pins, paths, {
        "status": "PARTIAL_NORMAL_INPUTS_VERIFIED_NEGATIVE_MISSING",
        "full_frozen_preflight_pass": False,
        "missing_required_input": {"path": str(paths["negative"]), "sha256": FROZEN["negative"]},
        "hardware_checked": not args.preflight_only,
        "hardware_pins_sha256": None if args.preflight_only else sha(args.hardware_pins),
        "emu_sha256": None if args.preflight_only else sha(args.emu),
        "driver_files": {str(p): sha(p) for p in driver_files},
        "input_files": input_files, "reference_provenance": reference,
        "matrix_unique": 117, "matrix_executed": 124,
        "control_build": str(control_build), "control_build_receipt": control_receipt,
        "matrix_builds": builds,
    }


def execute_jobs(jobs, worker, max_workers, on_progress):
    import schedule_resume
    return schedule_resume.execute(jobs, worker, max_workers, on_progress)


def run(args):
    require(args.preflight_only or (args.hardware_pins is not None and args.emu is not None),
            "--hardware-pins and --emu are required for an actual run")
    require(args.output.is_absolute(), "output must be an absolute new directory")
    out = args.output.resolve()
    require(not out.is_relative_to(ROOT.resolve()), "output must be outside source checkout")
    out.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "PRECHECK_RUNNING", "started": stamp(), "jobs": args.jobs,
                "timeout": args.timeout, "source_commit_at_start": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "output": str(out), "hardware_pins": str(args.hardware_pins) if args.hardware_pins else None,
                "emu": str(args.emu) if args.emu else None, "preflight_only": args.preflight_only,
                "invocation": sys.argv, "fullcore_performance_measured": False}
    save(out / "campaign-state.json", manifest)
    records = []
    try:
        guard = load_module("o2_fullcore_artifact_guard", ROOT / "team/scripts/artifact_guard.py")
        functional = load_module("o2_fullcore_functional", ROOT / "team/scripts/check-vdot-run.py")
        # Allow the adjacent observation modules to import their shared parser.
        sys.path.insert(0, str(HERE))
        analyze = load_module("analyze", HERE / "analyze.py")
        control = load_module("o2_fullcore_control", HERE / "check_control.py")
        perf = load_module("o2_fullcore_performance_window_check", ROOT / "team/workloads/vdot-perf/check.py")
        inspect.signature(analyze.analyze).bind("", require_complete=True)
        inspect.signature(analyze.extract_events_and_uart).bind("")
        inspect.signature(control.check).bind("", {}, 0, analysis={})
        inspect.signature(perf.verify).bind(Path("/example/build"), Path("/example/run"))
        pins, paths, receipt = preflight(args, guard, perf)
        save(out / "preflight.json", receipt)
        if args.preflight_only:
            manifest.update(status="O2_PREFLIGHT_ONLY_PASS", hardware_checked=False,
                            emulators_executed=0, finished=stamp())
            save(out / "campaign-state.json", manifest)
            save(out / "result.json", manifest)
            print("O2_PREFLIGHT_ONLY_PASS hardware_not_checked emulators_executed=0", flush=True)
            return 0
        save(out / "hardware-pins.json", pins)
        manifest.update(status="RUNNING", build_source_commit=pins["source_commit"])
        save(out / "campaign-state.json", manifest)
        matrix = args.t12_root / "runs/t11-matrix-canonical"
        jobs = [("hello-vadd", paths["hello"], None, paths["reference"]),
                ("negative-vdot", matrix / "build-0/vdot-exceptions.bin", None, paths["negative"])]
        jobs += [(f"functional-{i}", matrix / f"build-{i}/vdot-exceptions.bin",
                  matrix / f"data-{i}", paths["reference"]) for i in range(8)]
        jobs += [("control", paths["control"], None, paths["reference"]),
                 ("dense-batch128", paths["dense"], None, paths["reference"])]

        def artifact_guard():
            hardware_guard(pins, args.emu)
            require(sha(args.hardware_pins) == receipt["hardware_pins_sha256"], "hardware receipt drift")
            for group in ("driver_files", "input_files"):
                for path, digest in receipt[group].items():
                    require(sha(path) == digest, "runtime artifact drift: " + path)

        def job(name, image, data, selected_ref):
            if name == "negative-vdot":
                directory = out / name
                directory.mkdir()
                record = {"name": name, "status": "BLOCKED_MISSING_FROZEN_INPUT",
                          "started": stamp(), "finished": stamp(), "emulator_executed": False,
                          "missing_file": str(selected_ref), "expected_sha256": FROZEN["negative"],
                          "files": {}, "reason": "Historical frozen fault fixture unavailable; no replacement accepted."}
                save(directory / "result.json", record)
                return record
            directory = out / name
            directory.mkdir()
            command = ["timeout", args.timeout, "stdbuf", "-o0", "-e0", str(args.emu),
                       "-i", str(image), "--flash=" + str(paths["flash"]), "--ram-size=128MB",
                       "--diff=" + str(selected_ref), "--max-cycles=5000000"]
            record = {"name": name, "status": "RUNNING", "started": stamp(), "command": command,
                      "files": {}, "negative_target": "vdot" if name == "negative-vdot" else None}
            save(directory / "runtime.json", record)
            env = os.environ.copy()
            env.pop("XS_NEGATIVE_VECTOR_TARGET", None)
            if name == "negative-vdot":
                env["XS_NEGATIVE_VECTOR_TARGET"] = "vdot"
            try:
                record["files"] = {str(p): sha(p) for p in (args.emu, paths["reference"], selected_ref, paths["flash"], image)}
                save(directory / "runtime.json", record)
                artifact_guard()
                rc, hashes = run_process(command, directory, env)
                record.update(exit_code=rc, raw_logs_sha256=hashes,
                              log_format="separate-streams-v1; derived run.log = stderr.log + stdout.log")
                artifact_guard()
                text = (directory / "run.log").read_text(encoding="utf-8", errors="strict")
                validate_runtime(text, selected_ref)
                if name != "negative-vdot":
                    validate_failure_markers(text)
                observation = analyze.analyze(text, require_complete=name != "negative-vdot")
                save(directory / "observation.json", observation)
                validate_observation(observation, negative=name == "negative-vdot")
                _, uart = analyze.extract_events_and_uart(text)
                (directory / "uart.log").write_text(uart, encoding="utf-8")
                if name == "negative-vdot":
                    record.update(validate_negative(text, rc), status="EXPECTED_VDOT_HIGHBIT_REJECTION",
                                  observation_scope="partial trace until intentional DiffTest stop")
                elif data is not None:
                    expected_commits = json.loads((data / "manifest.json").read_text())["smoke_count"]
                    require(observation.get("counts", {}).get("COMMIT") == expected_commits and
                            observation.get("counts", {}).get("ACCEPT", 0) >= expected_commits > 0,
                            "functional observations do not bind every legal vdot case")
                    record["expected_vdot_commits"] = expected_commits
                    result = functional.validate(uart, "full", rc, data, require_diff=True)
                    save(directory / "functional-result.json", result)
                    record["status"] = "VDOT_MATRIX_SHARD_PASS"
                elif name == "dense-batch128":
                    # The original checker reads result.json as its runtime
                    # receipt; keep this provisional state until all gates pass.
                    record["raw_sha256"] = record["raw_logs_sha256"]
                    save(directory / "result.json", record)
                    result = perf.verify(args.dense_build, directory)
                    save(directory / "window-result.json", result)
                    require(result.get("status") == "PASS", "dense architectural/window verification failed")
                    expected_commits = sum(sample["dots"] for sample in result["samples"] if sample["method"] == "vdot")
                    require(observation.get("counts", {}).get("COMMIT") == expected_commits and
                            observation.get("counts", {}).get("ACCEPT", 0) >= expected_commits > 0,
                            "dense observations do not bind the verified vdot instruction count")
                    record["expected_vdot_commits"] = expected_commits
                    require(observation.get("counts", {}).get("TRIPLE_OVERLAP", 0) > 0 and
                            observation.get("counts", {}).get("MULTI_INFLIGHT", 0) > 0,
                            "dense workload did not cover real two-slot occupancy and triple overlap")
                    record.update(status="O2_DENSE_ELASTIC_AND_WINDOWS_PASS",
                                  checked_windows=len(result["samples"]), performance_comparison=False)
                elif name == "control":
                    result = control.check(text, json.loads((paths["control"].parent / "data/manifest.json").read_text()),
                                           rc, analysis=observation)
                    save(directory / "control-result.json", result)
                    # Preserve local O2 incompleteness; only qualified same-EMU
                    # traces may contribute each missing target at G3 level.
                    record.update(classify_control(result))
                else:
                    require(observation.get("counts", {}).get("ACCEPT") == 0 and
                            observation.get("counts", {}).get("COMMIT") == 0, "unexpected vdot in hello/vadd trace")
                    require(rc == 0 and "HELLO_VADD_PASS" in uart and "HIT GOOD TRAP" in uart,
                            "hello/vadd did not pass")
                    require(not re.search(r"HIT BAD TRAP|different at pc|Assertion failed", text),
                            "hello/vadd failure")
                    record["status"] = "HELLO_VADD_PASS"
                record["observation_status"] = observation["status"]
                record["observation_counts"] = observation.get("counts", {})
            except Exception as exc:
                record.update(status="FAILED", error=repr(exc))
            record["finished"] = stamp()
            save(directory / "result.json", record)
            print(name, record["status"], record.get("error", ""), flush=True)
            return record

        # Smoke must finish first. The negative/recovery pair stays ordered
        # in one worker; independent shards can use the second worker.
        records = execute_jobs(jobs, job, args.jobs,
                               lambda rows: save(out / "progress.json", rows))
        artifact_guard()
        guard.verify_nemu(args.t12_root / "nemu/reference", paths["reference"], "reference")
        for i in range(8):
            guard.verify_build(matrix / f"build-{i}", matrix / f"build-{i}/vdot-exceptions.bin",
                               matrix / f"data-{i}", "vdot", "full")
        passed, recovery, coverage = assess_suite(records, matrix / "build-0/vdot-exceptions.bin")
        result = {"status": "O2_CORE_REGRESSION_PASS" if passed else "O2_CORE_REGRESSION_FAILED",
                  "started": manifest["started"], "finished": stamp(), "matrix_unique": 117,
                  "matrix_executed": 124, "normal_reference_recovery": recovery,
                  "suite_coverage": coverage,
                  "coverage_policy": "F2v must independently satisfy all seven legacy obligations; dense must exhibit MULTI_INFLIGHT and TRIPLE_OVERLAP. Core campaign pass is separate from six-target G3 coverage; supplemental same-EMU runs may supply missing O2 targets with explicit source records.",
                  "g3_coverage_complete": passed and coverage["complete"],
                  "hardware_pins_sha256": receipt["hardware_pins_sha256"],
                  "build_source_commit": pins["source_commit"], "runs": records,
                  "performance_measured": False}
        save(out / "result.json", result)
        manifest.update(status=result["status"], finished=result["finished"])
        save(out / "campaign-state.json", manifest)
        print(result["status"], flush=True)
        return 0 if passed else 1
    except Exception as exc:
        manifest.update(status="FAILED", failed_stage=manifest["status"], error=repr(exc), finished=stamp())
        save(out / "campaign-state.json", manifest)
        save(out / "result.json", {"status": "O2_FULLCORE_SUITE_FAILED", "error": repr(exc), "runs": records,
                                   "finished": stamp(), "performance_measured": False})
        print("O2_FULLCORE_SUITE_FAILED", repr(exc), file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hardware-pins", type=Path)
    parser.add_argument("--emu", type=Path)
    parser.add_argument("--preflight-only", action="store_true",
                        help="verify frozen inputs and checker APIs without hardware pins or executing EMU")
    parser.add_argument("--t12-root", type=Path, default=DEFAULT_T12)
    parser.add_argument("--t14-root", type=Path, default=DEFAULT_T14)
    parser.add_argument("--dense-build", type=Path, default=DEFAULT_DENSE)
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=2)
    parser.add_argument("--timeout", default="120m")
    args = parser.parse_args()
    for field in ("hardware_pins", "emu", "t12_root", "t14_root", "dense_build"):
        value = getattr(args, field)
        if value is not None:
            setattr(args, field, value.resolve())
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
