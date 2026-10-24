"""Fresh 14-process correctness qualification for a separately identified T17 EMU.

Reuses frozen workload bytes and unchanged architectural/trace validators, not
old execution verdicts. Each process has a private cwd; only the negative then
same-image recovery pair is ordered. No performance comparison is made here.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from threading import Lock
from types import SimpleNamespace

import clean_entry as ce

p, g = ce.p, ce.g
CONTRACT = "t17-fresh-fullcore-v1"
PASS = "T17_FRESH_FULLCORE_PASS"
CORE = {"hello-vadd", "negative-vdot", "control", "dense-batch128"} | {f"functional-{i}" for i in range(8)}
SUPPLEMENTS = {"o2-diagnostic", "o2-control-diagnostic"}
SEMANTIC = ("name", "status", "started", "finished", "files", "raw_logs_sha256", "exit_code",
            "observation_status", "observation_counts", "runtime_gate", "expected_vdot_commits",
            "checked_windows", "checked_register_bytes", "workload_status")


def bind(repo, identity, physical):
    ce.install(repo, identity, physical=physical)
    recheck_path = repo / "team/optimizations/o2/fullcore/recheck.py"
    p.require(p.sha(recheck_path) == "8cebe76129f86747cdddf87f93f54d4379a8606dd3c1a20d55008361f2f95140", "frozen raw checker changed")
    r = g.load("t17_fullcore_recheck", recheck_path)
    names = list(r.DRIVERS) + ["team/optimizations/o2/fullcore/recheck.py",
                              "team/optimizations/o2/fullcore/run_supplements.py",
                              "team/optimizations/o2/fullcore/workloads/check.py"]
    blobs = r.git_blobs(repo, p.SOURCE, names)
    tools = {}
    for name, raw in blobs.items():
        p.require((repo / name).read_bytes() == raw, "checker differs from fixed Git blob: " + name)
        tools[str(repo / name)] = hashlib.sha256(raw).hexdigest()
    sys.path.insert(0, str(repo / "team/optimizations/o2/fullcore"))
    def load(name, rel):
        return r.load_blob(name, repo / rel, blobs[rel])
    suite = load("run_suite", r.DRIVERS[0])
    analyze = load("analyze", r.DRIVERS[1])
    control = load("t17_core_control", r.DRIVERS[2])
    guard = load("t17_core_artifact_guard", r.DRIVERS[3])
    functional = load("t17_core_functional", r.DRIVERS[4])
    perf = load("t17_core_perf", r.DRIVERS[5])
    gate = load("t17_core_runtime_gate", r.DRIVERS[6])
    supplement = load("t17_core_supplements", "team/optimizations/o2/fullcore/run_supplements.py")
    workload = load("t17_core_supplement_workload", "team/optimizations/o2/fullcore/workloads/check.py")
    tools.update(ce.a.frozen_m.checker_files(repo))
    tools[str(Path(__file__).resolve())] = p.sha(__file__)
    cfg = identity["configuration"]
    args = SimpleNamespace(t12_root=suite.DEFAULT_T12, t14_root=suite.DEFAULT_T14,
                           dense_build=suite.DEFAULT_DENSE, timeout="120m",
                           emu=Path(cfg["hardware_source"]) / "build/emu")
    return SimpleNamespace(repo=repo, identity=identity, cfg=cfg, r=r, suite=suite, analyze=analyze,
                           guard=guard, perf=perf, gate=gate, supplement=supplement, workload=workload,
                           modules=(suite, analyze, control, guard, functional, perf), tools=tools, args=args)


def add_tree(inputs, root):
    for path in sorted(root.rglob("*")):
        p.require(not path.is_symlink(), "evidence/input symlink: " + str(path))
        if path.is_file() and "__pycache__" not in path.parts:
            inputs[str(path)] = p.sha(path)


def frozen_workloads(ctx):
    """Same frozen input/math checks as run_suite; references use T17 identity."""
    suite, args, repo = ctx.suite, ctx.args, ctx.repo
    paths = dict(reference=Path(ctx.cfg["reference"]), flash=Path(ctx.cfg["flash"]),
                 hello=args.t12_root / "repo/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin",
                 control=args.t14_root / "runs/control-sweep-02/vdot-regression.bin",
                 dense=args.dense_build / "vdot-perf.bin")
    inputs = dict(ctx.tools)
    for name in ("hello", "control", "flash"):
        p.require(p.sha(paths[name]) == suite.FROZEN[name], "frozen workload identity: " + name)
    for path in paths.values():
        inputs[str(path)] = p.sha(path)
    dense_files = ("build.json", "vdot-perf.bin", "vdot-perf.elf", "data/manifest.json", "data/kernels.S",
                   "data/cases.h", "source/generate.py", "source/main.c", "source/Makefile")
    frozen = repo / "team/evidence/t13-performance-20261015/images-v3/performance-d0-s06"
    for name in dense_files:
        path = args.dense_build / name
        p.require(path.read_bytes() == ctx.perf.raw_bytes(frozen / name), "dense frozen input drift: " + name)
        inputs[str(path)] = p.sha(path)
    manifest = p.read(args.dense_build / "data/manifest.json")
    ctx.perf.verify_generation(args.dense_build, manifest)
    ctx.perf.check_compiled_cases(args.dense_build / "vdot-perf.elf", manifest)
    control = paths["control"].parent
    p.require((control / "build.json").read_bytes() ==
              (repo / "team/evidence/t14-optimization-20261016/control-sweep/build/build.json").read_bytes(),
              "control receipt differs from frozen archive")
    receipt = p.read(control / "build.json")
    inputs[str(control / "build.json")] = p.sha(control / "build.json")
    for name, digest in receipt["files"].items():
        p.require(p.sha(control / name) == digest, "control build drift")
        inputs[str(control / name)] = digest
    parent = repo / "team/evidence/t10-t11-fullcore-20261013/parent"
    corpus = [json.loads(line) for line in (parent / "cases.jsonl").read_text().splitlines()]
    corpus += p.read(parent / "exceptions.json")
    expected = {case["id"]: case for case in corpus}
    inputs.update({str(parent / name): p.sha(parent / name) for name in ("cases.jsonl", "exceptions.json")})
    matrix, seen, executed, builds = args.t12_root / "runs/t11-matrix-canonical", {}, 0, []
    for i, digest in enumerate(suite.MATRIX_SHA):
        data, build = matrix / f"data-{i}", matrix / f"build-{i}"
        image = build / "vdot-exceptions.bin"
        p.require(p.sha(image) == digest, "matrix image differs: " + str(i))
        receipt = ctx.guard.verify_build(build, image, data, "vdot", "full")
        builds.append(receipt)
        for group in ("source_sha256", "inputs_sha256", "images_sha256", "am_libraries_sha256"):
            inputs.update(receipt.get(group, {}))
        inputs[str(build / "workload-provenance.json")] = p.sha(build / "workload-provenance.json")
        cases = [json.loads(line) for line in (data / "cases.jsonl").read_text().splitlines()]
        cases += p.read(data / "exceptions.json")
        for case in cases:
            p.require(case == expected.get(case["id"]) and (case["id"] not in seen or case["id"] == "D00"),
                      "matrix corpus or allowed duplicate differs")
            seen[case["id"]] = case
            executed += 1
    p.require(set(seen) == set(expected) and len(seen) == 117 and executed == 124, "matrix is incomplete")
    supplements = {}
    for name, spec in ctx.supplement.JOBS.items():
        build = spec["default"]
        manifest, receipt, image = ctx.supplement.validate_build(spec["kind"], build, ctx.workload)
        for group in ("source_sha256", "generated_sha256", "images_sha256", "am_libraries_sha256"):
            for filename, digest in receipt[group].items():
                path = Path(filename) if Path(filename).is_absolute() else build / filename
                inputs[str(path)] = digest
        for filename in ("build.json", "data/manifest.json"):
            inputs[str(build / filename)] = p.sha(build / filename)
        supplements[name] = dict(build=build, image=image, manifest=manifest, receipt=receipt, kind=spec["kind"])
    ce.a.frozen_m.verify_files(inputs)
    ctx.paths, ctx.supplements = paths, supplements
    return inputs, dict(matrix_unique=117, matrix_executed=124, matrix_builds=builds,
                        frozen_workload_images=True, historical_execution_results_reused=False)


def command(ctx, image, reference):
    return ["timeout", ctx.args.timeout, "stdbuf", "-o0", "-e0", str(ctx.args.emu), "-i", str(image),
            "--flash=" + ctx.cfg["flash"], "--ram-size=128MB", "--diff=" + str(reference), "--max-cycles=5000000"]


def validate_process(ctx, row, directory, image, reference):
    negative = row["name"] == "negative-vdot"
    expected_files = {str(path): p.sha(path) for path in
                      (ctx.args.emu, ctx.paths["reference"], reference, ctx.paths["flash"], image)}
    p.require(row["files"] == expected_files and row["command"] == command(ctx, image, reference), "process inputs/command differ")
    p.require(row.get("process_started") is True and type(row.get("pid")) is int and row["pid"] > 0 and
              row.get("actual_new_execution") is True and not row.get("timed_out") and
              row.get("environment_overrides") == {"XS_NEGATIVE_VECTOR_TARGET": "vdot" if negative else None},
              "process completion or injection identity differs")
    start, finish = (datetime.fromisoformat(row[k]) for k in ("started", "finished"))
    p.require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish, "invalid process time")
    p.require(row["cwd"] == str(directory / "cwd") and row["auxiliary_files"] == p.AUX and
              {n: p.sha(directory / "cwd/build" / n) for n in p.AUX} == p.AUX, "private cwd/AUX changed")
    return expected_files


def evaluate(ctx, name, image, data, reference, raw, campaign, audit):
    directory = campaign / name
    validate_process(ctx, raw, directory, image, reference)
    if name in CORE:
        row = ctx.r.recheck_job(name, image, data, reference, raw, campaign, audit,
                               ctx.args, ctx.paths, ctx.modules, ctx.gate)
        p.require(row["status"] != "FAILED", "raw architectural gate failed: " + name + ": " + row.get("error", ""))
        if name == "negative-vdot":
            detail = row["runtime_gate"]
            elf = g.ELF((image.parent / "vdot-exceptions.elf").read_bytes())
            p.require(int.from_bytes(elf.read(int(detail["pc"], 16), 4), "little") == int(detail["word"], 16),
                      "negative target instruction not in selected ELF")
        return row
    spec = ctx.supplements[name]
    rc, text = ctx.r.check_raw_job(directory, raw, command(ctx, image, reference), raw["files"], None)
    observation, uart, result = ctx.supplement.evaluate(text, rc, spec["kind"], spec["manifest"],
                                                       reference, ctx.analyze, ctx.workload)
    p.require(observation["schema"]["slots"] == 2, "supplement schema differs from T17 O2 hardware")
    out = audit / name
    out.mkdir()
    g.save(out / "observation.json", observation)
    g.save(out / "functional-result.json", result)
    (out / "uart.log").write_text(uart)
    row = dict(name=name, status="O2_SUPPLEMENT_PASS", started=raw["started"], finished=raw["finished"],
               files=raw["files"], raw_logs_sha256=raw["raw_logs_sha256"], exit_code=rc,
               observation_status=observation["status"], observation_counts=observation["counts"],
               expected_vdot_commits=spec["manifest"]["expected_vdot_commits"], workload_status=result["status"],
               checked_register_bytes=result["checked_register_bytes"], performance_measured=False)
    g.save(out / "result.json", row)
    return row


def aggregate(ctx, rows, raw_rows):
    p.require(len(rows) == len(raw_rows) == 14 and {r["name"] for r in rows} == CORE | SUPPLEMENTS and
              {r["name"] for r in raw_rows} == CORE | SUPPLEMENTS, "fullcore exact inventory differs")
    core = [r for r in rows if r["name"] in CORE]
    supplemental = [r for r in rows if r["name"] in SUPPLEMENTS]
    passed, recovery, coverage = ctx.suite.assess_suite(core, ctx.jobs["functional-0"][1])
    p.require(ctx.supplement.assess(supplemental), "two supplements not both qualified")
    combined = ctx.r.combine_g3(passed, core,
                 dict(status="O2_SUPPLEMENT_OFFLINE_RECHECK_PASS", records=supplemental), ctx.suite)
    p.require(passed and recovery and combined["whole_suite_pass"], "new fullcore architectural/coverage gate failed")
    indexed = {r["name"]: r for r in raw_rows}
    negative, normal = (indexed[n] for n in ("negative-vdot", "functional-0"))
    p.require(negative["pid"] != normal["pid"] and
              datetime.fromisoformat(normal["started"]) >= datetime.fromisoformat(negative["finished"]) and
              negative["exit_code"] == 1 and normal["exit_code"] == 0, "negative/normal new-process recovery failed")
    return dict(status=PASS, contract=CONTRACT, hardware_contract=p.CONTRACT,
                source_commit=p.SOURCE, emu_sha256=ctx.identity["hardware_profile"]["emu_sha256"],
                reference_sha256=ctx.identity["reference_sha256"], negative_sha256=ctx.fixture["negative_sha256"],
                new_emu_runs=14, reused_execution_verdicts=0, selected_jobs=14, matrix_unique=117, matrix_executed=124,
                normal_reference_recovery=True, suite_coverage=combined["suite_coverage"],
                historical_fixed_hardware_acceptance=False, historical_fixed_negative_acceptance=False,
                performance_measured=False, records=sorted(rows, key=lambda r: r["name"]))


def prepare(ctx, out, fixture_dir=None):
    inputs, workload = frozen_workloads(ctx)
    hardware, profile = p.hardware_profile(ctx.repo, ctx.cfg)
    p.require(profile == ctx.identity["hardware_profile"], "hardware differs from T17 identity")
    inputs.update(hardware)
    if fixture_dir is None:
        fixture_dir = out / "negative-fixture"
        ctx.fixture = ce.a.frozen_m.build_negative(ctx.repo, ctx.cfg, fixture_dir)
    else:
        ctx.fixture = p.read(fixture_dir / "fixture.json")
    fixture = ctx.fixture
    p.require(fixture["source_sha256"] == ce.a.frozen_m.NEGATIVE_SHA and
              fixture["normal_reference_sha256"] == ctx.identity["reference_sha256"] and
              fixture["historical_negative_hash_claim"] is False and
              fixture["binary"] == str(fixture_dir / "negative-reference.so") and
              p.sha(fixture_dir / "negative-reference.so") == fixture["negative_sha256"] and
              p.sha(fixture_dir / "negative-fixture.c") == fixture["source_sha256"], "negative fixture identity differs")
    ce.evidence.fixture_identity(SimpleNamespace(json=lambda n: p.read(fixture_dir / n.split('/', 1)[1]),
                    raw=lambda n: (fixture_dir / n.split('/', 1)[1]).read_bytes()),
                    "fixture", fixture, ctx.cfg, ce.a.frozen_m)
    add_tree(inputs, fixture_dir)
    ctx.paths["negative"] = Path(fixture["binary"])
    jobs = ctx.r.original_jobs(ctx.args, ctx.paths)
    jobs += [(name, spec["image"], None, ctx.paths["reference"]) for name, spec in ctx.supplements.items()]
    ctx.jobs = {row[0]: row for row in jobs}
    p.require(set(ctx.jobs) == CORE | SUPPLEMENTS and len(jobs) == 14, "job inventory differs")
    ctx.inputs = inputs
    if out is not None:
        g.save(out / "runtime-inputs.json", inputs)
        g.save(out / "workload-preflight.json", workload)
        g.save(out / "hardware-profile.json", profile)
        g.save(out / "jobs.json", [{"name": n, "image": str(i), "data": str(d) if d else None, "reference": str(r)}
                                     for n, i, d, r in jobs])
    return jobs


def run(repo, identity_path, out, operation, jobs):
    p.require(1 <= jobs <= 4 and not out.exists() and not out.is_relative_to(repo), "new output and <=4 workers required")
    value = p.read(identity_path)
    ctx = bind(repo, value, physical=True)
    out.mkdir(parents=True)
    shutil.copyfile(identity_path, out / "identity.json")
    g.save(out / "configuration.json", value["configuration"])
    state = dict(status="PREFLIGHT", contract=CONTRACT, started=ce.a.frozen_f.now(), operation_id=operation,
                 controller_sha256=p.sha(__file__), identity_sha256=p.sha(identity_path), jobs=jobs,
                 new_emu_launch_attempts=0, new_emu_runs=0, active={}, performance_measured=False,
                 cpu_affinity=sorted(os.sched_getaffinity(0)), historical_execution_results_reused=False)
    lock, rows, raw_rows = Lock(), [], []
    def persist():
        g.save(out / "state.json", state)
    persist()
    try:
        ordered = prepare(ctx, out)
        campaign, audit = out / "runs", out / "checks"
        campaign.mkdir(); audit.mkdir()
        state["status"] = "RUNNING"
        persist()
        def worker(item):
            name, image, data, reference = item
            directory = campaign / name
            cwd = directory / "cwd"
            (cwd / "build").mkdir(parents=True)
            for filename, digest in p.AUX.items():
                shutil.copyfile(Path(ctx.cfg["hardware_source"]) / "build" / filename, cwd / "build" / filename)
                p.require(p.sha(cwd / "build" / filename) == digest, "private auxiliary mismatch")
            negative = name == "negative-vdot"
            raw = dict(name=name, status="RUNNING", started=ce.a.frozen_f.now(), command=command(ctx, image, reference),
                       cwd=str(cwd), files={str(path): p.sha(path) for path in
                       (ctx.args.emu, ctx.paths["reference"], reference, ctx.paths["flash"], image)},
                       negative_target="vdot" if negative else None, auxiliary_files=p.AUX,
                       environment_overrides={"XS_NEGATIVE_VECTOR_TARGET": "vdot" if negative else None},
                       process_started=False, pid_kind="timeout process-group leader", actual_new_execution=True,
                       performance_measured=False)
            counted = False
            def progress():
                nonlocal counted
                g.save(directory / "runtime.json", raw)
                with lock:
                    if raw.get("process_started") and not counted:
                        state["new_emu_runs"] += 1
                        counted = True
                    state["active"][name] = dict(pid=raw.get("pid"), result=str(directory / "runtime.json"))
                    persist()
            with lock:
                state["new_emu_launch_attempts"] += 1
            progress()
            try:
                ce.a.frozen_m.verify_files(ctx.inputs)
                env = dict(os.environ)
                env.pop("XS_NEGATIVE_VECTOR_TARGET", None)
                if negative:
                    env["XS_NEGATIVE_VECTOR_TARGET"] = "vdot"
                with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
                    ce.a.frozen_f.spawn(raw["command"], cwd, stdout, stderr, raw, progress, env=env, timeout=7210)
                raw["finished"] = ce.a.frozen_f.now()
                (directory / "run.log").write_bytes((directory / "stderr.log").read_bytes() + (directory / "stdout.log").read_bytes())
                raw["raw_logs_sha256"] = {n: p.sha(directory / n) for n in ctx.r.RAW_NAMES}
                raw["raw_sha256"] = dict(raw["raw_logs_sha256"])
                p.require(type(raw.get("exit_code")) is int and not raw.get("timed_out"), "process did not complete")
                (directory / "exit-code.txt").write_text(str(raw["exit_code"]) + "\n", encoding="ascii")
                raw["status"] = "RAW_EMU_EXITED_AWAITING_RECHECK"
                g.save(directory / "result.json", raw)
                ce.a.frozen_m.verify_files(ctx.inputs)
                row = evaluate(ctx, name, image, data, reference, raw, campaign, audit)
                for key in SEMANTIC:
                    if key in row:
                        raw[key] = row[key]
                g.save(directory / "result.json", raw)
                with lock:
                    rows.append(row); raw_rows.append(raw)
                    g.save(out / "completed-runs.json", sorted(raw_rows, key=lambda r: r["name"]))
                print(name, raw["status"], flush=True)
                return row
            except BaseException as exc:
                raw.update(status="FAILED", error=repr(exc), finished=ce.a.frozen_f.now())
                g.save(directory / "result.json", raw)
                raise
            finally:
                with lock:
                    state["active"].pop(name, None)
                    persist()
        worker(ordered[0])
        def pair():
            worker(ordered[1]); worker(ordered[2])
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = [pool.submit(pair)] + [pool.submit(worker, item) for item in ordered[3:]]
            for future in as_completed(futures):
                future.result()
        ce.a.frozen_m.verify_files(ctx.inputs)
        _, profile = p.hardware_profile(repo, ctx.cfg)
        p.require(profile == value["hardware_profile"], "post-run hardware drift")
        p.require(state["new_emu_runs"] == state["new_emu_launch_attempts"] == 14 and not state["active"], "process count mismatch")
        result = aggregate(ctx, rows, raw_rows)
        state.update(status=PASS, finished=ce.a.frozen_f.now())
        g.save(out / "results.json", dict(result, started=state["started"], finished=state["finished"],
                                         controller_sha256=state["controller_sha256"], identity_sha256=state["identity_sha256"]))
        persist()
        return result
    except BaseException as exc:
        state.update(status="T17_FRESH_FULLCORE_FAILED", error=repr(exc), finished=ce.a.frozen_f.now())
        persist()
        raise


def audit(repo, run, out):
    p.require(not out.exists() and not out.is_relative_to(run), "audit output must be new and separate")
    value, state = p.read(run / "identity.json"), p.read(run / "state.json")
    p.require(state["status"] == PASS and state["controller_sha256"] == p.sha(__file__) and
              state["identity_sha256"] == p.sha(run / "identity.json") and
              state["new_emu_runs"] == state["new_emu_launch_attempts"] == 14 and not state["active"], "source campaign incomplete")
    ctx = bind(repo, value, physical=True)
    prepare(ctx, None, run / "negative-fixture")
    p.require(ctx.inputs == p.read(run / "runtime-inputs.json"), "runtime input closure differs")
    ce.a.frozen_m.verify_files(ctx.inputs)
    p.require({d.name for d in (run / "runs").iterdir()} == CORE | SUPPLEMENTS, "raw run inventory differs")
    out.mkdir(parents=True)
    rows, raw_rows = [], []
    start, finish = (datetime.fromisoformat(state[k]) for k in ("started", "finished"))
    for name, image, data, reference in ctx.jobs.values():
        raw = p.read(run / "runs" / name / "result.json")
        p.require(start <= datetime.fromisoformat(raw["started"]) <= datetime.fromisoformat(raw["finished"]) <= finish,
                  "job outside campaign lifetime")
        row = evaluate(ctx, name, image, data, reference, raw, run / "runs", out)
        p.require(all(row.get(k) == raw.get(k) for k in SEMANTIC if k in row), "raw/cached verdict differs: " + name)
        rows.append(row); raw_rows.append(raw)
    result = aggregate(ctx, rows, raw_rows)
    saved = p.read(run / "results.json")
    p.require(saved["controller_sha256"] == state["controller_sha256"] and saved["identity_sha256"] == state["identity_sha256"] and
              saved["started"] == state["started"] and saved["finished"] == state["finished"], "final identity/timeline differs")
    for key, value in result.items():
        if key == "records":
            old = {row["name"]: row for row in saved[key]}
            p.require(set(old) == CORE | SUPPLEMENTS and all(
                {k: r[k] for k in SEMANTIC if k in r} == {k: old[r["name"]][k] for k in SEMANTIC if k in old[r["name"]]}
                for r in value), "cached aggregate records differ")
        else:
            p.require(saved.get(key) == value, "cached aggregate field differs: " + key)
    p.require(p.read(run / "completed-runs.json") == sorted(raw_rows, key=lambda r: r["name"]), "completed raw set differs")
    ce.a.frozen_m.verify_files(ctx.inputs)
    result.update(status="T17_FRESH_FULLCORE_RAW_AUDIT_PASS", source_new_emu_runs=14, new_emu_runs=0,
                  source_result_sha256=p.sha(run / "results.json"), physical_external_inputs_revalidated=True)
    g.save(out / "results.json", result)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--action", choices=("run", "audit"), required=True)
    ap.add_argument("--identity", type=Path)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--operation-id")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    if args.action == "run":
        p.require(args.identity and args.operation_id, "run needs identity and operation")
        result = run(args.repo.resolve(), args.identity.resolve(), args.output.resolve(), args.operation_id, args.jobs)
    else:
        p.require(args.run, "audit needs campaign")
        result = audit(args.repo.resolve(), args.run.resolve(), args.output.resolve())
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
