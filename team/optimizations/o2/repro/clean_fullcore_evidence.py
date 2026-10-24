"""Independent T17 fullcore receipt binding and portable raw-log recheck.

The executed controller remains immutable. This auditor additionally binds its
real spawn receipt fields to the final records, then repeats the unchanged
architecture, full-width DiffTest, matrix, control and O2 trace gates.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from types import SimpleNamespace

import clean_fullcore as fc
import clean_evidence as support

p, g, ce = fc.p, fc.g, fc.ce
CONTRACT = "t17-fullcore-evidence-v1"
CONTROLLER = "593298f4119d5a8ce8dd925ec5836c70e0d8bf4cbcf7cf0b221570ffc669f1a2"
SPAWN_FIELDS = ("name", "started", "command", "files", "negative_target", "cwd", "auxiliary_files",
                "environment_overrides", "process_started", "pid", "pid_kind", "actual_new_execution",
                "performance_measured", "exit_code", "timed_out", "terminated_returncode")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def portable(repo):
    path = repo / "team/optimizations/o2/fullcore/portable.py"
    p.require(p.sha(path) == "7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b", "archive reader differs")
    p.require(p.sha(fc.__file__) == CONTROLLER, "executed fullcore controller changed")
    return g.load("t17_fullcore_portable", path)


def spawn_binding(runtime, result):
    for key in SPAWN_FIELDS:
        p.require(type(runtime.get(key)) is type(result.get(key)) and runtime.get(key) == result.get(key),
                  "spawn/final receipt mismatch: " + key)
    p.require(runtime["process_started"] is True and type(runtime["pid"]) is int and runtime["pid"] > 0 and
              type(runtime["exit_code"]) is int and not runtime.get("timed_out") and
              runtime.get("terminated_returncode") is None and runtime["actual_new_execution"] is True and
              runtime["performance_measured"] is False, "spawn receipt is not a completed correctness process")
    return {k: runtime[k] for k in SPAWN_FIELDS if k in runtime}


def process_proof(run):
    state = p.read(run / "state.json")
    p.require(state["status"] == fc.PASS and state["controller_sha256"] == CONTROLLER and
              state["new_emu_runs"] == state["new_emu_launch_attempts"] == 14 and not state["active"] and
              1 <= state["jobs"] <= 4 and len(state["cpu_affinity"]) <= 4, "campaign process closure")
    rows = {}
    events = []
    for directory in sorted((run / "runs").iterdir()):
        row = p.read(directory / "result.json")
        p.require(row["name"] == directory.name and directory.name not in rows, "run identity differs")
        rows[directory.name] = spawn_binding(p.read(directory / "runtime.json"), row)
        start, finish = (datetime.fromisoformat(row[k]) for k in ("started", "finished"))
        p.require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish, "process timeline")
        events.extend(((start, 1), (finish, -1)))
    p.require(set(rows) == fc.CORE | fc.SUPPLEMENTS, "process inventory differs")
    active = peak = 0
    for _, delta in sorted(events):
        active += delta
        peak = max(peak, active)
    p.require(active == 0 and peak <= state["jobs"], "recorded concurrency exceeds worker budget")
    return dict(status="T17_FULLCORE_SPAWN_BINDINGS_PASS", source_new_emu_runs=14,
                peak_overlapping_process_intervals=peak, jobs=state["jobs"], records=rows)


def physical_audit(repo, run, out):
    portable(repo)
    result = fc.audit(repo, run, out)
    proof = process_proof(run)
    g.save(out / "process-bindings.json", proof)
    g.save(out / "audit-controller.json", dict(contract=CONTRACT, audit_source_sha256=p.sha(__file__),
              controller_sha256=CONTROLLER, source_campaign=str(run), source_result_sha256=p.sha(run / "results.json"),
              raw_audit_sha256=p.sha(out / "results.json"), process_bindings_sha256=p.sha(out / "process-bindings.json")))
    return dict(status="T17_FULLCORE_PHYSICAL_AND_SPAWN_AUDIT_PASS", new_emu_runs=0,
                raw_status=result["status"], process_status=proof["status"])


def pack(repo, run, audit, output, support_path):
    reader = portable(repo)
    p.require(not output.exists() and not any(output.is_relative_to(r) or r.is_relative_to(output)
              for r in (repo, run, audit)), "archive overlaps input or exists")
    state, result, checked = p.read(run / "state.json"), p.read(run / "results.json"), p.read(audit / "results.json")
    proof = process_proof(run)
    p.require(state["status"] == result["status"] == fc.PASS and checked["status"] == "T17_FRESH_FULLCORE_RAW_AUDIT_PASS" and
              checked["source_result_sha256"] == p.sha(run / "results.json") and
              proof == p.read(audit / "process-bindings.json"), "physical audit does not bind completed campaign")
    controller = p.read(audit / "audit-controller.json")
    p.require(controller == dict(contract=CONTRACT, audit_source_sha256=p.sha(__file__), controller_sha256=CONTROLLER,
              source_campaign=str(run), source_result_sha256=p.sha(run / "results.json"),
              raw_audit_sha256=p.sha(audit / "results.json"), process_bindings_sha256=p.sha(audit / "process-bindings.json")),
              "physical auditor identity differs")
    inputs = p.read(run / "runtime-inputs.json")
    ce.a.frozen_m.verify_files(inputs)
    identity = p.read(run / "identity.json")
    ce.validate_identity(repo, identity)
    support.validate_support(p.read(support_path), identity)
    cfg = identity["configuration"]
    external = {str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): identity["hardware_profile"]["emu_sha256"]}
    p.require(all(inputs.get(k) == v for k, v in external.items()), "EMU input is not bound")
    output.mkdir(parents=True)
    entries, originals = [], {}
    def add(path, logical):
        reader.safe_relative(logical)
        p.require(path.is_file() and not path.is_symlink(), "archive input missing/symlink")
        raw, original = path.read_bytes(), str(path)
        if original in originals:
            p.require(originals[original] == digest(raw), "input changed while sealing")
            return
        stored, body, encoding = Path("files") / logical, raw, "identity"
        if len(raw) >= 4096:
            zipped = gzip.compress(raw, compresslevel=6, mtime=0)
            if len(zipped) + 64 < len(raw):
                stored, body, encoding = stored.with_name(stored.name + ".gz"), zipped, "gzip"
        target = output / stored
        p.require(not target.exists(), "duplicate stored archive path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        entries.append(dict(original=original, stored=stored.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=digest(raw), stored_bytes=len(body), stored_sha256=digest(body)))
        originals[original] = digest(raw)
    for prefix, root in (("campaign", run), ("physical-audit", audit)):
        for path in sorted(root.rglob("*")):
            p.require(not path.is_symlink(), "symbolic evidence path")
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            if "cwd" in rel.parts and not (path.parent.name == "build" and path.name in p.AUX):
                continue
            add(path, prefix + "/" + rel.as_posix())
    for number, (name, expected) in enumerate(sorted(inputs.items())):
        if name in external:
            continue
        path = Path(name)
        p.require(p.sha(path) == expected, "input changed at export")
        add(path, f"inputs/{number:04d}/" + path.name)
    add(support_path, "support/support-proof.json")
    add(Path(support.__file__).resolve(), "exporter/clean_evidence.py")
    add(Path(__file__).resolve(), "exporter/clean_fullcore_evidence.py")
    info = dict(contract=CONTRACT, source_root=str(repo), campaign=str(run), physical_audit=str(audit),
                external_inputs=external, audit_source_sha256=p.sha(__file__), controller_sha256=CONTROLLER,
                source_result_sha256=p.sha(run / "results.json"),
                scope="All recorded direct inputs except EMU; original hardware/dependency/NEMU/AM source trees and installed toolchain remain physical provenance. No clean-machine installation claim.")
    info_path = output / "evidence-map.json"
    info_path.write_bytes(json_bytes(info))
    add(info_path, "evidence-map.json")
    info_path.unlink()
    # The generated map's original is a logical marker, not a vanished input.
    entries[-1]["original"] = "generated:evidence-map"
    manifest = dict(version=1, contract=CONTRACT, created_utc=ce.a.frozen_f.now(), files=entries)
    raw = json_bytes(manifest)
    (output / "archive-manifest.json").write_bytes(raw)
    (output / "archive-manifest.sha256").write_bytes((digest(raw) + "  archive-manifest.json\n").encode())
    ce.a.frozen_m.verify_files(inputs)
    sealed = reader.Archive(output)
    return dict(status="T17_FULLCORE_ARCHIVE_BYTES_PASS", **sealed.bytes_result, new_emu_runs=0)


class Evidence:
    def __init__(self, repo, path):
        self.archive = portable(repo).Archive(path)
        p.require(self.archive.manifest["contract"] == CONTRACT and
                  {r.name for r in path.iterdir()} == {"files", "archive-manifest.json", "archive-manifest.sha256"},
                  "archive contract/root inventory differs")
        self.info = self.archive.json("evidence-map.json")
        p.require(self.info["contract"] == CONTRACT and self.info["controller_sha256"] == CONTROLLER and
                  self.info["audit_source_sha256"] == p.sha(__file__) == digest(self.archive.raw("exporter/clean_fullcore_evidence.py")),
                  "archive auditor identity differs")
        self.originals = {}
        for logical, row in self.archive.records.items():
            p.require(row["original"] not in self.originals, "duplicate archive original")
            self.originals[row["original"]] = logical
            prefix, _, relative = logical.partition("/")
            if prefix in ("campaign", "physical-audit"):
                root = self.info["campaign" if prefix == "campaign" else "physical_audit"]
                p.require(row["original"] == str(PurePosixPath(root) / relative), "archive original mapping differs")
        self.identity = self.archive.json("campaign/identity.json")
        ce.validate_identity(repo, self.identity)
        self.cfg = self.identity["configuration"]
        self.inputs = self.archive.json("campaign/runtime-inputs.json")
        self.external = {str(PurePosixPath(self.cfg["hardware_source"]) / "build/emu"): self.identity["hardware_profile"]["emu_sha256"]}
        p.require(self.info["external_inputs"] == self.external, "unexpected omitted input")
        for name, sha in self.inputs.items():
            p.require((self.external[name] if name in self.external else digest(self.raw(name))) == sha, "sealed input differs: " + name)

    def raw(self, original):
        p.require(original in self.originals, "unsealed original input: " + original)
        return self.archive.raw(self.originals[original])

    def json(self, original):
        return json.loads(self.raw(original))

    def extract(self, original, out):
        prefix, found = original.rstrip("/") + "/", 0
        for name in self.originals:
            if name.startswith(prefix):
                rel = name[len(prefix):]
                p.require(not PurePosixPath(rel).is_absolute() and ".." not in PurePosixPath(rel).parts, "unsafe extraction")
                target = out / rel
                p.require(not target.exists(), "extraction path exists")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.raw(name)); found += 1
        p.require(found > 0, "empty archive subtree")
        return out


def validate_inputs(e, ctx, repo):
    source, cfg = PurePosixPath(e.info["source_root"]), e.cfg
    expected = {}
    for path, sha in ctx.tools.items():
        key = str(source / Path(path).relative_to(repo).as_posix())
        p.require(digest(e.raw(key)) == sha, "sealed checker differs from executed Git/current tool: " + key)
        expected[key] = sha
    roots = dict(reference=cfg["reference"], flash=cfg["flash"],
                 hello=str(ctx.args.t12_root / "repo/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin"),
                 control=str(ctx.args.t14_root / "runs/control-sweep-02/vdot-regression.bin"),
                 dense=str(ctx.args.dense_build / "vdot-perf.bin"))
    for name, path in roots.items():
        expected[path] = digest(e.raw(path))
        pin = e.identity["reference_sha256"] if name == "reference" else ctx.suite.FROZEN.get(name)
        if pin is not None:
            p.require(expected[path] == pin, "sealed fixed input differs: " + name)
    dense = PurePosixPath(roots["dense"]).parent
    for name in ("build.json", "vdot-perf.bin", "vdot-perf.elf", "data/manifest.json", "data/kernels.S",
                 "data/cases.h", "source/generate.py", "source/main.c", "source/Makefile"):
        path = str(dense / name)
        raw = e.raw(path)
        p.require(raw == ctx.perf.raw_bytes(repo / "team/evidence/t13-performance-20261015/images-v3/performance-d0-s06" / name),
                  "sealed dense input differs from frozen repository archive")
        expected[path] = digest(raw)
    control = PurePosixPath(roots["control"]).parent
    receipt_raw = e.raw(str(control / "build.json"))
    p.require(receipt_raw == (repo / "team/evidence/t14-optimization-20261016/control-sweep/build/build.json").read_bytes(),
              "sealed control build receipt differs")
    expected[str(control / "build.json")] = digest(receipt_raw)
    for name, sha in json.loads(receipt_raw)["files"].items():
        path = str(control / name)
        p.require(digest(e.raw(path)) == sha, "sealed control input differs")
        expected[path] = sha
    parent = source / "team/evidence/t10-t11-fullcore-20261013/parent"
    for name in ("cases.jsonl", "exceptions.json"):
        raw = e.raw(str(parent / name))
        p.require(raw == (repo / "team/evidence/t10-t11-fullcore-20261013/parent" / name).read_bytes(), "parent corpus differs")
        expected[str(parent / name)] = digest(raw)
    corpus = [json.loads(line) for line in e.raw(str(parent / "cases.jsonl")).splitlines()] + e.json(str(parent / "exceptions.json"))
    wanted, seen, count = {r["id"]: r for r in corpus}, {}, 0
    matrix = PurePosixPath(str(ctx.args.t12_root)) / "runs/t11-matrix-canonical"
    builds = []
    for i, pin in enumerate(ctx.suite.MATRIX_SHA):
        build, data = matrix / f"build-{i}", matrix / f"data-{i}"
        image = str(build / "vdot-exceptions.bin")
        p.require(digest(e.raw(image)) == pin, "sealed matrix image differs")
        receipt = e.json(str(build / "workload-provenance.json")); builds.append(receipt)
        p.require(receipt["schema_version"] == 1 and receipt["kind"] == "vdot" and receipt["mode"] == "full" and
                  receipt["arch"] == "riscv64-xs" and receipt["data_dir"] == str(data) and
                  receipt["images_sha256"][image] == pin, "sealed matrix build specification")
        for group in ("source_sha256", "inputs_sha256", "images_sha256", "am_libraries_sha256"):
            for path, sha in receipt.get(group, {}).items():
                p.require(digest(e.raw(path)) == sha, "sealed matrix direct input differs")
                expected[path] = sha
        path = str(build / "workload-provenance.json")
        expected[path] = digest(e.raw(path))
        cases = [json.loads(line) for line in e.raw(str(data / "cases.jsonl")).splitlines()] + e.json(str(data / "exceptions.json"))
        for case in cases:
            p.require(case == wanted.get(case["id"]) and (case["id"] not in seen or case["id"] == "D00"), "sealed corpus matrix differs")
            seen[case["id"]] = case; count += 1
    preflight = e.archive.json("campaign/workload-preflight.json")
    p.require(set(seen) == set(wanted) and len(seen) == 117 and count == 124 and
              preflight == dict(matrix_unique=117, matrix_executed=124, matrix_builds=builds,
                                frozen_workload_images=True, historical_execution_results_reused=False), "sealed matrix preflight differs")
    supplements = {}
    for name, spec in ctx.supplement.JOBS.items():
        build = PurePosixPath(str(spec["default"]))
        receipt, manifest = e.json(str(build / "build.json")), e.json(str(build / "data/manifest.json"))
        p.require(receipt["status"] == "O2_DIAGNOSTIC_BUILD_PASS" and receipt["kind"] == spec["kind"] and
                  manifest["expected_vdot_commits"] == spec["commits"] and digest(e.raw(str(build / spec["image"]))) == spec["image_sha256"],
                  "sealed supplement build differs")
        for group in ("source_sha256", "generated_sha256", "images_sha256", "am_libraries_sha256"):
            for name_, sha in receipt[group].items():
                path = str(PurePosixPath(name_) if PurePosixPath(name_).is_absolute() else build / name_)
                p.require(digest(e.raw(path)) == sha, "sealed supplement direct input differs")
                expected[path] = sha
        for name_ in ("build.json", "data/manifest.json"):
            expected[str(build / name_)] = digest(e.raw(str(build / name_)))
        supplements[name] = dict(kind=spec["kind"], image=str(build / spec["image"]), manifest=manifest)
    metadata = e.identity["metadata_sha256"]
    record = PurePosixPath(cfg["build_record"])
    raw = lambda name: e.raw(str(record / name))
    for name, sha in metadata.items():
        p.require(digest(raw(name)) == sha, "sealed build metadata differs")
        expected[str(record / name)] = sha
    obj = lambda name: json.loads(raw(name))
    p.validate_metadata(obj("hardware-inputs.json"), obj("build-state.json"), obj("hardware-inputs-before.json"),
                        obj("baseline-hardware-inputs.json"), obj("generated-artifacts.json"),
                        metadata["executed-builder.py"], metadata["baseline-hardware-inputs.json"])
    ctx.suite.validate_pin_fields(obj("hardware-inputs.json"))
    hardware = PurePosixPath(cfg["hardware_source"])
    expected.update({str(hardware / "build" / n): sha for n, sha in p.AUX.items()})
    expected.update(e.external)
    expected.update({cfg["reference"]: e.identity["reference_sha256"], cfg["flash"]: p.FLASH,
                     str(hardware / "team/optimizations/o2/fullcore/build_fullcore.py"): p.HELPER,
                     cfg["build_driver"]: p.BUILDER})
    fixture_root = e.info["campaign"] + "/negative-fixture"
    fixture = e.json(fixture_root + "/fixture.json")
    fixture_files = {"negative-fixture.c", "negative-reference.so", "fixture.json"} | {
        step + "/" + name for step in ("compiler", "compile", "linkage") for name in ("command.json", "stdout.log", "stderr.log")}
    present = {name[len(fixture_root)+1:] for name in e.originals if name.startswith(fixture_root + "/")}
    p.require(present == fixture_files and fixture["binary"] == fixture_root + "/negative-reference.so", "fixture inventory/path differs")
    proxy = type("Fixture", (), {"json": lambda self, n: e.json(fixture_root + "/" + n.split("/", 1)[1]),
                                "raw": lambda self, n: e.raw(fixture_root + "/" + n.split("/", 1)[1])})()
    ce.evidence.fixture_identity(proxy, "fixture", fixture, cfg, ce.a.frozen_m)
    expected.update({fixture_root + "/" + name: digest(e.raw(fixture_root + "/" + name)) for name in fixture_files})
    p.require(expected == e.inputs, "sealed direct-input exact set differs")
    support_bundle = e.archive.json("support/support-proof.json")
    p.require(support_bundle["identity_sha256"] == digest(e.archive.raw("campaign/identity.json")) and
              support_bundle["audit_source_sha256"] == p.sha(support.__file__) == digest(e.archive.raw("exporter/clean_evidence.py")),
              "support source/identity differs")
    support.validate_support(support_bundle, e.identity)
    p.require(support_bundle["team_patch_manifest_sha256"] ==
              e.inputs[str(source / "team/patches/nemu/manifest.json")], "support/runtime patch manifest differs")
    p.require(e.archive.json("campaign/hardware-profile.json") == e.identity["hardware_profile"], "runtime hardware profile differs")
    paths = {name: Path(path) for name, path in roots.items()}
    paths["negative"] = Path(fixture["binary"])
    ctx.paths, ctx.fixture, ctx.supplements = paths, fixture, supplements
    jobs = ctx.r.original_jobs(ctx.args, paths) + [(name, Path(row["image"]), None, paths["reference"]) for name, row in supplements.items()]
    ctx.jobs = {row[0]: row for row in jobs}
    p.require(e.archive.json("campaign/jobs.json") == [dict(name=n, image=str(i), data=str(d) if d else None, reference=str(r))
                                                     for n, i, d, r in jobs], "sealed job specification differs")


def audit_archive(repo, path):
    p.require(os.name == "posix", "complete raw regeneration audit requires Linux/WSL")
    e = Evidence(repo, path)
    ctx = fc.bind(repo, e.identity, physical=False)
    validate_inputs(e, ctx, repo)
    state, result, physical = (e.archive.json(n) for n in ("campaign/state.json", "campaign/results.json", "physical-audit/results.json"))
    p.require(state["status"] == result["status"] == fc.PASS and physical["status"] == "T17_FRESH_FULLCORE_RAW_AUDIT_PASS" and
              e.info["source_result_sha256"] == physical["source_result_sha256"] == digest(e.archive.raw("campaign/results.json")),
              "fullcore archive source/audit closure differs")
    p.require(state["identity_sha256"] == result["identity_sha256"] == digest(e.archive.raw("campaign/identity.json")) and
              state["controller_sha256"] == result["controller_sha256"] == CONTROLLER and
              state["started"] == result["started"] and state["finished"] == result["finished"] and
              state["contract"] == result["contract"] == physical["contract"] == fc.CONTRACT and
              state["historical_execution_results_reused"] is False and state["performance_measured"] is False and
              isinstance(state.get("operation_id"), str) and state["operation_id"].strip() and
              physical["new_emu_runs"] == 0 and physical["source_new_emu_runs"] == 14 and
              physical["physical_external_inputs_revalidated"] is True and
              e.archive.json("campaign/configuration.json") == e.cfg,
              "campaign identity/timeline or physical audit scope differs")
    controller = e.archive.json("physical-audit/audit-controller.json")
    p.require(controller == dict(contract=CONTRACT, audit_source_sha256=p.sha(__file__), controller_sha256=CONTROLLER,
              source_campaign=e.info["campaign"], source_result_sha256=digest(e.archive.raw("campaign/results.json")),
              raw_audit_sha256=digest(e.archive.raw("physical-audit/results.json")),
              process_bindings_sha256=digest(e.archive.raw("physical-audit/process-bindings.json"))), "physical audit tool association")
    expected = {r["name"]: r for r in result["records"]}
    p.require(len(result["records"]) == 14 and set(expected) == fc.CORE | fc.SUPPLEMENTS, "recorded qualification inventory")
    # This private auditor's hash API reads verified sealed inputs, never an
    # unrecorded host path. Mathematical validators retain their original bytes.
    def sealed_sha(path_):
        name = str(path_)
        p.require(name in e.inputs, "unrecorded external read during raw audit: " + name)
        return e.external[name] if name in e.external else digest(e.raw(name))
    ctx.r.sha = sealed_sha
    rows, raw_rows = [], []
    with tempfile.TemporaryDirectory(prefix="t17-fullcore-archive-") as temp_name:
        temp = Path(temp_name)
        campaign = e.extract(e.info["campaign"], temp / "campaign")
        p.require(process_proof(campaign) == e.archive.json("physical-audit/process-bindings.json"), "archived spawn bindings differ")
        checks = temp / "checks"; checks.mkdir()
        paths = dict(ctx.paths)
        control = e.extract(str(ctx.paths["control"].parent), temp / "control")
        paths["control"] = control / ctx.paths["control"].name
        dense = e.extract(str(ctx.args.dense_build), temp / "dense")
        original_verify = ctx.perf.verify
        ctx.perf.verify = lambda build, run: original_verify(build, run, external=e.inputs)
        args = SimpleNamespace(**vars(ctx.args)); args.dense_build = dense
        start, finish = (datetime.fromisoformat(state[k]) for k in ("started", "finished"))
        for name, image, data, reference in ctx.jobs.values():
            directory = campaign / "runs" / name
            raw = p.read(directory / "result.json")
            files = {str(v): sealed_sha(v) for v in (ctx.args.emu, ctx.paths["reference"], reference, ctx.paths["flash"], image)}
            negative = name == "negative-vdot"
            p.require(raw["command"] == fc.command(ctx, image, reference) and raw["files"] == files and
                      raw["negative_target"] == ("vdot" if negative else None) and
                      raw["environment_overrides"] == {"XS_NEGATIVE_VECTOR_TARGET": "vdot" if negative else None} and
                      raw["cwd"] == e.info["campaign"] + "/runs/" + name + "/cwd" and raw["auxiliary_files"] == p.AUX and
                      {n: p.sha(directory / "cwd/build" / n) for n in p.AUX} == p.AUX and
                      start <= datetime.fromisoformat(raw["started"]) <= datetime.fromisoformat(raw["finished"]) <= finish,
                      "archived process inputs/environment/timeline differ: " + name)
            if name in fc.CORE:
                data_copy = e.extract(str(data), temp / "data" / name) if data is not None else None
                row = ctx.r.recheck_job(name, image, data_copy, reference, raw, campaign / "runs", checks,
                                       args, paths, ctx.modules, ctx.gate)
                p.require(row["status"] != "FAILED", "sealed architecture gate failed: " + name + ": " + row.get("error", ""))
                if negative:
                    detail = row["runtime_gate"]
                    elf = g.ELF(e.raw(str(image.with_suffix(".elf"))))
                    p.require(int.from_bytes(elf.read(int(detail["pc"], 16), 4), "little") == int(detail["word"], 16),
                              "sealed negative target differs from actual ELF")
            else:
                spec = ctx.supplements[name]
                rc, text = ctx.r.check_raw_job(directory, raw, fc.command(ctx, image, reference), files, None)
                observation, _, checked = ctx.supplement.evaluate(text, rc, spec["kind"], spec["manifest"],
                                                                  reference, ctx.analyze, ctx.workload)
                p.require(observation["schema"]["slots"] == 2, "sealed supplement slot schema differs")
                row = dict(name=name, status="O2_SUPPLEMENT_PASS", started=raw["started"], finished=raw["finished"],
                           files=files, raw_logs_sha256=raw["raw_logs_sha256"], exit_code=rc,
                           observation_status=observation["status"], observation_counts=observation["counts"],
                           expected_vdot_commits=spec["manifest"]["expected_vdot_commits"], workload_status=checked["status"],
                           checked_register_bytes=checked["checked_register_bytes"], performance_measured=False)
            for key in fc.SEMANTIC:
                p.require(row.get(key) == expected[name].get(key) == raw.get(key), "raw/cached semantic mismatch: " + name + "/" + key)
            rows.append(row); raw_rows.append(raw)
        rebuilt = fc.aggregate(ctx, rows, raw_rows)
        p.require(e.archive.json("campaign/completed-runs.json") == sorted(raw_rows, key=lambda r: r["name"]),
                  "completed-run index differs from original raw records")
        audited_rows = {row["name"]: row for row in physical["records"]}
        p.require(len(physical["records"]) == 14 and set(audited_rows) == fc.CORE | fc.SUPPLEMENTS and all(
                  {k: row[k] for k in fc.SEMANTIC if k in row} ==
                  {k: audited_rows[row["name"]][k] for k in fc.SEMANTIC if k in audited_rows[row["name"]]}
                  for row in rows), "physical audit records differ from sealed raw recomputation")
    for key, value in rebuilt.items():
        if key != "records":
            p.require(result.get(key) == value, "cached aggregate differs: " + key)
            if key not in ("status", "new_emu_runs"):
                p.require(physical.get(key) == value, "physical aggregate differs: " + key)
    return dict(status="T17_FULLCORE_ARCHIVE_RAW_AUDIT_PASS", contract=CONTRACT, archive=e.archive.bytes_result,
                audit_source_sha256=p.sha(__file__), source_new_emu_runs=14, new_emu_runs=0,
                complete_normal_traces=13, expected_negative_traces=1, matrix_unique=117, matrix_executed=124,
                normal_reference_recovery=True, suite_coverage=rebuilt["suite_coverage"],
                physical_external_inputs_revalidated=False, historical_fixed_hardware_acceptance=False,
                performance_measured=False)


def index_check(repo, path):
    evidence = Evidence(repo, path)
    helper_path = repo / g.REL / "merged_index.py"
    p.require(p.sha(helper_path) == "a67a26ece6413d7a3f06466e503a2a42d2d8ed33a287b0c9110c9e7c4aece764", "index helper changed")
    helper = g.load("t17_fullcore_index_helper", helper_path)
    p.require(path.is_relative_to(repo), "archive must be in selected publication checkout")
    prefix = path.relative_to(repo).as_posix()
    expected = {prefix + "/" + row["stored"] for row in evidence.archive.manifest["files"]}
    expected.update(prefix + "/" + name for name in ("archive-manifest.json", "archive-manifest.sha256"))
    p.require({f.relative_to(repo).as_posix() for f in path.rglob("*") if f.is_file()} == expected, "archive disk inventory differs")
    entries = helper.index_entries(helper.git(repo, "ls-files", "--stage", "-z", "--", prefix))
    p.require(set(entries) == expected, "archive index inventory differs")
    names = sorted(entries)
    stream = io.BytesIO(helper.git(repo, "cat-file", "--batch", data="".join(entries[n]["oid"] + "\n" for n in names).encode()))
    for name in names:
        header = stream.readline().split()
        p.require(len(header) == 3 and header[0].decode() == entries[name]["oid"] and header[1] == b"blob", "missing staged blob")
        raw = stream.read(int(header[2]))
        p.require(stream.read(1) == b"\n" and raw == (repo / name).read_bytes(), "staged archive byte mismatch")
    p.require(not stream.read(), "extra staged blob output")
    return dict(status="T17_FULLCORE_COMPLETE_GIT_INDEX_PASS", archive=evidence.archive.bytes_result,
                archive_files_in_git_index=len(names), missing=0, extra=0, new_emu_runs=0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--action", choices=("physical", "pack", "audit", "index"), required=True)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--audit", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--support", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    p.require(not out.exists(), "report output must be new")
    if args.action == "physical":
        result = physical_audit(repo, args.run.resolve(), out)
    elif args.action == "pack":
        result = pack(repo, args.run.resolve(), args.audit.resolve(), args.archive.resolve(), args.support.resolve())
        g.save(out, result)
    else:
        result = (audit_archive if args.action == "audit" else index_check)(repo, args.archive.resolve())
        g.save(out, result)
    print(json.dumps(result, indent=2))
