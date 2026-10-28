#!/usr/bin/env python3
"""Recompute current firstdot raw evidence, then seal a compressed archive.

No simulator process is launched. This reads the original build products and
external inputs; archive integrity does not claim a standalone clean rebuild.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import orchestration_receipt as orchestration

LEAF = Path("team/optimizations/o2/integration/firstdot-v2-0f")
CONTRACT = "zjhwork-0f-firstdot-raw-audit-archive-v1"
PINNED_SOURCE = {'team/optimizations/o2/integration/firstdot-v2-0f/combination.py': '22a418c4a95c47b8226d2e0b1453b0b09f02c62cfe2add09aef135b10c7fe7bc', 'team/optimizations/o2/r2-select/entry_c_api.py': '4e1ae340c5b122d09d634631d7fce322ad121838ba9a4affdf193d2a4d9105fd'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def verify_files(files):
    for path, digest in files.items():
        require(sha(path) == digest, "immutable input drift: " + path)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    Path(path).write_bytes(encoded(value))


def plain(value):
    return json.loads(json.dumps(value))


def timeline(value):
    start, finish = (datetime.fromisoformat(value[k]) for k in ("started", "finished"))
    require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish,
            "invalid process timestamps")
    return start, finish


def fresh_output(output, protected):
    output = Path(output).resolve()
    require(not output.exists(), "new output required; preserve earlier attempts")
    for path in protected:
        path = Path(path).resolve()
        require(not output.is_relative_to(path) and not path.is_relative_to(output),
                "output overlaps protected input: " + str(path))


def load_combination(repo):
    sys.dont_write_bytecode = True
    for rel, digest in PINNED_SOURCE.items():
        require(sha(repo / rel) == digest, "frozen audit dependency changed: " + rel)
    sys.path.insert(0, str(repo / LEAF))
    spec = importlib.util.spec_from_file_location("_current_firstdot_raw_audit_runtime",
                                                 repo / LEAF / "combination.py")
    module = importlib.util.module_from_spec(spec)
    exec(compile((repo / LEAF / "combination.py").read_bytes(),
                 str(repo / LEAF / "combination.py"), "exec"), module.__dict__)
    require(module.ROOT == repo, "combination ROOT differs")
    return module


def matrix_common(combo, repo, identity_path, build, images, hardware_files, m):
    files = dict(hardware_files)
    files.update(m.checker_files(repo))
    g = combo.g
    for rel in g.SOURCES | set(g.FROZEN) | {
            str(g.S1 / "gate.py"), str(g.REL / "machine_model.py"),
            str(combo.REPRO / "clean_entry.py"), str(combo.REPRO / "clean_profile.py")}:
        files[str(repo / rel)] = sha(repo / rel)
    files.update(combo.adapter_files())
    files[str(identity_path)] = sha(identity_path)
    for name in ("state.json", "images.json", "pairs.json", "combination-build.json"):
        files[str(build / name)] = sha(build / name)
    for image in images:
        path = Path(image["path"])
        for name in ("build.json", "data/manifest.json"):
            files[str(path / name)] = sha(path / name)
    return files


def process_receipt(record, image, run, common, cfg, m, negative=False, fixture=None, replay=0):
    """Validate the original execution receipt before trusting transcript numbers."""
    for key in ("suite", "shard", "dataset", "variant", "name", "path", "image_sha256"):
        require(record[key] == image[key], "execution image selection differs: " + key)
    require(record["contract"] == m.CONTRACT and record["mode"] == "merged",
            "execution contract differs")
    require(record["negative"] is negative and type(record["replay"]) is int and
            record["replay"] == replay, "execution role differs")
    reference = fixture["binary"] if negative else cfg["reference"]
    cwd = run / "cwd"
    wanted = dict(common)
    wanted.update({str(cwd / "build" / name): digest for name, digest in m.AUX.items()})
    wanted[str(Path(image["path"]) / "vdot-perf.bin")] = image["image_sha256"]
    if negative:
        wanted[reference] = fixture["negative_sha256"]
    argv = [str(Path(cfg["hardware_source"]) / "build/emu"), "-i",
            str(Path(image["path"]) / "vdot-perf.bin"), "--flash=" + cfg["flash"],
            "--ram-size=128MB", "--diff=" + reference, "--max-cycles=2000000", "--seed=1"]
    require(record["cwd"] == str(cwd) and record["command"] == argv and
            record["reference"] == reference and record["files"] == wanted,
            "execution command/input closure differs")
    require(record.get("process_started") is True and type(record.get("pid")) is int and
            record["pid"] > 0 and not record.get("timed_out") and
            type(record.get("exit_code")) is int and record["exit_code"] == (1 if negative else 0),
            "execution did not complete with the expected real exit")
    require(record["status"] == (m.NEGATIVE_PASS if negative else m.NORMAL_PASS),
            "execution status differs")
    require(record["environment_overrides"] == {
            "XS_NEGATIVE_VECTOR_TARGET": "vdot" if negative else None},
            "negative environment differs")
    require(record["raw_sha256"] == {name: sha(run / name) for name in ("stdout.log", "stderr.log")},
            "raw transcript digest differs")
    timeline(record)
    return wanted


def negative_fixture(run, cfg, m):
    directory = run / "negative-fixture"
    fixture = read(directory / "fixture.json")
    require(fixture["source_sha256"] == m.NEGATIVE_SHA and
            fixture["normal_reference_sha256"] == m.f.REFERENCE and
            fixture["historical_negative_hash_claim"] is False and
            fixture["binary"] == str(directory / "negative-reference.so"),
            "negative fixture identity differs")
    require(sha(directory / "negative-fixture.c") == m.NEGATIVE_SHA and
            sha(directory / "negative-reference.so") == fixture["negative_sha256"],
            "negative fixture bytes differ")
    argv = fixture["command"]
    require(len(argv) == 11 and argv[1:] == [
        "-shared", "-fPIC", "-O2", '-DREF_SO="' + cfg["reference"] + '"',
        str(directory / "negative-fixture.c"), "-Wl,--no-as-needed", cfg["reference"],
        "-ldl", "-o", fixture["binary"]], "negative compilation command differs")
    records = []
    for label, expected in (("compiler", [argv[0], "--version"]), ("compile", argv),
                            ("linkage", [read(directory / "linkage/command.json")["command"][0],
                                         "-d", fixture["binary"]])):
        command = read(directory / label / "command.json")
        require(command["command"] == expected and command["cwd"] == str(directory) and
                command["process_started"] is True and type(command["pid"]) is int and command["pid"] > 0 and
                type(command["exit_code"]) is int and command["exit_code"] == 0 and
                not command.get("timed_out") and command["raw_sha256"] == {
                    name: sha(directory / label / name) for name in ("stdout.log", "stderr.log")},
                "negative compilation receipt differs")
        timeline(command)
        records.append(command)
    require(all(timeline(a)[1] <= timeline(b)[0] for a, b in zip(records, records[1:])),
            "negative compilation chronology differs")
    require("Shared library: [" + cfg["reference"] + "]" in (directory / "linkage/stdout.log").read_text(),
            "negative fixture normal reference linkage differs")
    return fixture


def raw_matrix(combo, repo, identity_path, build, run, output):
    identity, hardware_files, profile = combo.parent_identity(repo, identity_path, physical=True)
    cfg = identity["configuration"]
    f, m = combo.runtime(repo, identity)
    g = combo.g
    state, cached = read(run / "state.json"), read(run / "results.json")
    require(state["status"] == cached["status"] == combo.RUN_PASS and
            state["contract"] == cached["contract"] == combo.CONTRACT and
            state["new_emu_runs"] == 33 and state["active_pid"] is None and state["active_result"] is None,
            "matrix campaign is not complete")
    require(isinstance(state.get("operation_id"), str) and state["operation_id"].strip(),
            "missing operation identity")
    require(state["hardware_changed"] is False and state["stable_default_changed"] is False and
            state["historical_performance_reused"] is False, "matrix qualification scope differs")
    require(cached["hardware_source_commit"] == identity["source_commit"] and
            cached["emu_sha256"] == profile["emu_sha256"] and
            cached["parent_identity_sha256"] == sha(identity_path) and
            cached["historical_pass_reused"] is False, "matrix hardware identity differs")
    require(read(build / "state.json")["status"] == combo.BUILD_PASS, "matrix build incomplete")
    images = read(build / "images.json")["images"]
    expected = {combo.name(item): item for item in combo.inventory([1, 3, 5, 7], [0, 1, 2])}
    require(len(images) == 24 and {i["name"] for i in images} == set(expected), "matrix image inventory")
    combo.verify_build_scope(repo, build, images, identity_path)
    for image in images:
        require(all(image[k] == v for k, v in expected[image["name"]].items()), "matrix image labels")
        combo.validate_image(image, build)
        path = Path(image["path"])
        g.verify_build(path, repo)
        m.validate_selection(image, read(path / "data/manifest.json"), read(path / "build.json"))
        require(sha(path / "vdot-perf.bin") == image["image_sha256"], "matrix load image changed")
    pair_report = combo.pairs(images, repo)
    require(pair_report == read(build / "pairs.json") == read(run / "pairs.json"), "paired layout differs")
    common = matrix_common(combo, repo, identity_path, build, images, hardware_files, m)
    require(common == read(run / "runtime-inputs.json"), "matrix common input inventory differs")
    require(read(run / "configuration.json") == dict(cfg, canonical_builds=[str(build)]),
            "matrix runtime configuration differs")
    require(read(run / "hardware-profile.json") == profile and
            (run / "parent-identity.json").read_bytes() == identity_path.read_bytes(),
            "matrix runtime hardware receipt differs")
    fixture = negative_fixture(run, cfg, m)
    target = next(i for i in images if (i["shard"], i["dataset"], i["variant"]) == (3, 0, "firstdot"))
    ordered = [("negative-firstdot-8x32", target, True, 0),
               ("recovery-firstdot-8x32", target, False, 0)]
    for image in sorted(images, key=lambda i: (i["shard"], i["dataset"],
            combo.VARIANTS.index(i["variant"]) ^ ((i["shard"] + i["dataset"]) % 2))):
        if image["name"] != target["name"]:
            ordered.append(("formal-" + image["name"], image, False, 0))
    ordered.extend(("replay-" + i["name"], i, False, 1) for i in images if i["dataset"] == 0)
    require({p.name for p in (run / "runs").iterdir()} == {x[0] for x in ordered},
            "extra or missing matrix execution")
    suite = g.load("_current_raw_banner", repo / "team/optimizations/o2/fullcore/run_suite.py")
    recomputed, all_records, inputs, negative = [], [], dict(common), None
    for label, image, rejected, replay in ordered:
        directory = run / "runs" / label
        record = read(directory / "result.json")
        wanted = process_receipt(record, image, directory, common, cfg, m, rejected, fixture, replay)
        for path, digest in wanted.items():
            require(path not in inputs or inputs[path] == digest, "mixed immutable input identities")
            inputs[path] = digest
        suite.validate_runtime((directory / "stdout.log").read_text() +
                               (directory / "stderr.log").read_text(), record["reference"])
        if rejected:
            # negative_check writes derived JSON: use a separate scratch directory.
            with tempfile.TemporaryDirectory(prefix="firstdot-negative-raw-") as temp:
                scratch = Path(temp)
                for name in ("stdout.log", "stderr.log"):
                    shutil.copyfile(directory / name, scratch / name)
                detail = m.negative_check(repo, Path(image["path"]), scratch, record)
                require(detail == record["negative_details"] == read(directory / "negative.json") and
                        read(scratch / "observation.json") == read(directory / "observation.json"),
                        "negative raw recomputation differs")
                require(detail["vd"] == 0 and detail["bit"] == 100 and detail["word"] == "0x0388000b",
                        "negative did not target changed firstdot")
            negative = record
        else:
            windows, analysis = f.verify_runtime(repo, Path(image["path"]), directory)
            require(plain(windows) == read(directory / "windows.json") and
                    plain(analysis) == read(directory / "observation.json"), "normal raw recomputation differs")
            manifest = read(Path(image["path"]) / "data/manifest.json")
            require(len(windows["samples"]) == len(manifest["plan"]), "raw sample/plan count differs")
            samples = []
            for sample, plan in zip(windows["samples"], manifest["plan"]):
                row = manifest["rows"][plan["index"]]
                samples.append(dict(sample, mode="merged", variant=image["variant"], shard=image["shard"],
                                    software=row["software"], m=row["m"], k=row["k"], scope=row["scope"],
                                    image_sha256=image["image_sha256"]))
            require(plain(samples) == record["samples"], "recorded samples differ from raw windows")
            recomputed.append(dict(record, samples=plain(samples)))
        all_records.append(record)
        print(label, "RAW_RECOMPUTED", flush=True)
    require(len(recomputed) == 32 and negative is not None, "incomplete raw campaign")
    require(cached["runs"] == recomputed == read(run / "completed-runs.json") and
            cached["negative"] == negative, "cached matrix records differ")
    m.validate_recovery(negative, recomputed[0])
    by = {r["name"]: r for r in recomputed if r["replay"] == 0}
    for repeated in [r for r in recomputed if r["replay"] == 1]:
        require(m.signature(repeated) == m.signature(by[repeated["name"]]), "all-window replay differs")
    summary = combo.summarize(recomputed)
    require(all(cached[k] == v for k, v in summary.items()), "summary differs from raw cycles/instructions")
    require(cached["qualification"] == combo.qualification(images, recomputed, True, True),
            "matrix qualification differs")
    start, finish = timeline(state)
    require(start <= timeline(all_records[0])[0] and timeline(all_records[-1])[1] <= finish and
            all(timeline(x)[1] <= timeline(y)[0] for x, y in zip(all_records, all_records[1:])),
            "matrix chronology differs")
    require(len({r["pid"] for r in all_records}) == 33, "matrix process identity repeated")
    m.verify_files(inputs)
    qualification = combo.matrix_qualification(identity_path, build, run)
    proof = dict(status="CURRENT_FIRSTDOT_MATRIX_RAW_AUDIT_PASS", original_emu_processes=33,
                 normal_runs=32, negative_runs=1, formal_images=24, replay_runs=8,
                 qualification=qualification, **summary)
    save(output / "matrix-raw-proof.json", proof)
    return identity, proof, inputs

def private_c_auditor(combo, repo, identity):
    """Retain upstream raw checks; add the current full hardware input closure."""
    base = combo.c_adapter(repo, identity)
    original = repo / "team/optimizations/o2/r2-select/entry_c_api.py"
    require(sha(original) == PINNED_SOURCE[original.relative_to(repo).as_posix()],
            "C audit source is not the frozen upstream revision")
    source = original.read_text()
    function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "audit_run")
    body = "\n".join(source.splitlines()[function.lineno - 1:function.end_lineno]) + "\n"
    needle = '    g.require(common==expected,"C application common input inventory")'
    require(body.count(needle) == 1, "C audit insertion site drift")
    hardware_files, _ = base.a.frozen_m.hardware_profile(repo, identity["configuration"])
    base.__dict__["_current_hardware_files"] = hardware_files
    patched = body.replace(needle, "    expected.update(_current_hardware_files)\n" + needle, 1)
    exec(compile(patched, str(original) + ":current-closure-adapter", "exec"), base.__dict__)
    return base, dict(
        upstream_sha256=sha(original),
        change="insert expected.update(_current_hardware_files) before exact common inventory equality",
        additional_hardware_files=len(hardware_files),
        private_audit_function_sha256=hashlib.sha256(patched.encode()).hexdigest(),
        source_modified=False,
    )


def raw_c(combo, repo, identity_path, identity, matrix_build, matrix_run, build, run, output):
    base, adaptation = private_c_auditor(combo, repo, identity)
    matrix = combo.matrix_qualification(identity_path, matrix_build, matrix_run)
    anchor = combo.library_anchor(repo, build, matrix_build)
    require(anchor == read(build / "matrix-anchor.json"), "C public matrix leaf anchor differs")
    require(read(build / "combination-c-build.json") == {
        "contract": combo.CONTRACT, "adapter_files": combo.adapter_files()},
        "C integration build identity differs")
    require(read(run / "combination-c-qualification.json") == dict(
        contract=combo.CONTRACT, matrix_proof=matrix, hardware_identity_sha256=sha(identity_path),
        historical_pass_reused=False, public_functions=16, distinct_cases=48,
        normal_case_executions=96, new_emu_runs=3, status="CURRENT_FIRSTDOT_C_APPLICATION_PASS"),
        "C integration qualification differs")
    negative_fixture(run, identity["configuration"], base.a.frozen_m)
    proof = base.audit_run(repo, build, run)
    orchestration_proof = None
    if (run / "independent-c-orchestration.json").exists():
        binding = orchestration.validate_independent_receipt(combo, repo, identity_path, matrix_build, build, run)
        orchestration_proof = read(run / "combination-c-orchestration-proof.json")
        expected = dict(
            status="CURRENT_FIRSTDOT_INDEPENDENT_C_FINALIZATION_PASS",
            binding=binding, raw_c_proof=proof, matrix_proof=matrix,
            private_c_audit_adapter=adaptation,
            finalizer_source_sha256=sha(repo / LEAF / "orchestration/finalize_c.py"),
            audit_source_sha256=sha(__file__),
        )
        require(orchestration_proof == expected, "independent C finalization proof differs")
    else:
        require(not (run / "combination-c-orchestration-proof.json").exists(),
                "orchestration proof without its original independent receipt")
    result = dict(status="CURRENT_FIRSTDOT_C_RAW_AUDIT_PASS", proof=proof,
                  matrix_anchor=anchor, audit_adapter=adaptation, orchestration_proof=orchestration_proof)
    save(output / "c-raw-proof.json", result)
    inputs = read(run / "runtime-inputs.json")
    if orchestration_proof is not None:
        inputs = merge_inputs(inputs, {row["path"]: row["sha256"]
                             for row in orchestration_proof["binding"]["inputs"].values()})
    return result, inputs


def merge_inputs(*mappings):
    merged = {}
    for mapping in mappings:
        for path, digest in mapping.items():
            require(path not in merged or merged[path] == digest, "mixed external inputs: " + path)
            merged[path] = digest
    return merged


def tree_files(root):
    result = []
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "archive source symlink: " + str(path))
        if path.is_file():
            result.append(path)
    return result


def archive_inputs(repo, identity_path, identity, matrix_build, matrix_run, c_build, c_run,
                   inputs, output, combo):
    selected = {}

    def add(logical, path):
        logical_path, path = Path(logical), Path(path).resolve()
        require(not logical_path.is_absolute() and ".." not in logical_path.parts,
                "unsafe archive logical path")
        require(logical not in selected or selected[logical] == path, "archive logical collision")
        require(path.is_file() and not path.is_symlink() and path.name != "emu", "invalid archive source")
        selected[logical] = path

    for label, root in (("matrix-build", matrix_build), ("matrix-run", matrix_run),
                        ("c-build", c_build), ("c-run", c_run)):
        for path in tree_files(root):
            add(label + "/" + path.relative_to(root).as_posix(), path)
    independent_proof = c_run / "combination-c-orchestration-proof.json"
    if independent_proof.exists():
        for name, row in read(independent_proof)["binding"]["inputs"].items():
            add("independent-orchestration/" + name + "/" + Path(row["path"]).name, Path(row["path"]))
    add("identity/identity.json", identity_path)
    if identity["contract"] == "current-o2-h1-div-cancel-hardware-v1":
        lock = Path(identity["hardware_lock"])
        add("identity/hardware-artifact-lock.json", lock)
    elif identity["contract"] == "zjhwork-0f-firstdot-v2-clean-identity-v1":
        require(identity["new_source_build"] is True and identity["support_profile"]["new_sources"] is True and
                identity["support_profile"]["new_support_builds"] is True, "clean identity support scope differs")
        for category in ("adapter_files", "support_files"):
            for index, (original, digest) in enumerate(sorted(identity[category].items())):
                path = Path(original)
                require(sha(path) == digest, "clean identity archive support input differs")
                require(path.name != "emu" and "riscv64-nemu-interpreter" not in path.name,
                        "do not archive full simulator executables")
                add("identity/clean-" + category + f"/{index:03d}/" + path.name, path)
    else:
        raise ValueError("unsupported archive hardware identity contract")
    # Record original hardware build receipts, not its EMU or dependency trees.
    record = Path(identity["configuration"]["build_record"])
    for name in identity["metadata_sha256"]:
        add("hardware-build-metadata/" + name, record / name)
    for path in inputs:
        path = Path(path)
        if path.is_relative_to(repo / "team"):
            add("source/" + path.relative_to(repo).as_posix(), path)
    for path in tree_files(repo / LEAF):
        if "__pycache__" not in path.parts:
            add("source/" + path.relative_to(repo).as_posix(), path)
    for path in Path(__file__).parent.glob("*.py"):
        add("audit-tools/" + path.name, path)
    for name in ("matrix-raw-proof.json", "c-raw-proof.json", "external-inputs.json", "evidence-inputs.json"):
        add("raw-audit/" + name, output / name)
    return selected


def pack_archive(selected, directory):
    """Independent gzip members with raw/stored hash; stream large transcripts."""
    directory.mkdir(parents=True, exist_ok=False)
    payload = directory / "payload"
    payload.mkdir()
    rows = []
    for index, (logical, original) in enumerate(sorted(selected.items())):
        raw_sha, raw_bytes = sha(original), original.stat().st_size
        target = payload / (f"{index:06d}.gz")
        with target.open("xb") as dest:
            with gzip.GzipFile(filename="", mode="wb", fileobj=dest, mtime=0, compresslevel=6) as zipped:
                with original.open("rb") as source:
                    shutil.copyfileobj(source, zipped, 1024 * 1024)
        require(original.stat().st_size == raw_bytes and sha(original) == raw_sha,
                "archive input changed while reading: " + str(original))
        rows.append(dict(logical=logical, original=str(original), payload=target.relative_to(directory).as_posix(),
                         raw_bytes=raw_bytes, raw_sha256=raw_sha,
                         stored_bytes=target.stat().st_size, stored_sha256=sha(target)))
    manifest = dict(schema=1, contract=CONTRACT, files=rows,
                    archive_type="source-and-raw-evidence; external build inputs remain required for raw re-audit",
                    independent_clean_reproduction=False, original_build_required_for_raw_audit=True,
                    new_emu_runs=0, new_nemu_runs=0)
    save(directory / "manifest.json", manifest)
    result = verify_archive(directory)
    # Recheck every original source after sealing, not just each member separately.
    for row in rows:
        require(sha(row["original"]) == row["raw_sha256"], "archive input drift after sealing")
    return result


def verify_archive(directory):
    directory = Path(directory)
    manifest = read(directory / "manifest.json")
    require(manifest["schema"] == 1 and manifest["contract"] == CONTRACT and
            manifest["independent_clean_reproduction"] is False and
            manifest["original_build_required_for_raw_audit"] is True,
            "archive contract differs")
    require(isinstance(manifest["files"], list) and manifest["files"], "empty archive inventory")
    names, payloads = set(), set()
    raw_total, stored_total = 0, 0
    for row in manifest["files"]:
        logical, payload = Path(row["logical"]), Path(row["payload"])
        require(not logical.is_absolute() and ".." not in logical.parts and row["logical"] not in names,
                "unsafe or duplicate archive logical path")
        require(not payload.is_absolute() and ".." not in payload.parts and payload.parts[0] == "payload"
                and row["payload"] not in payloads, "unsafe or duplicate archive payload")
        names.add(row["logical"])
        payloads.add(row["payload"])
        stored = directory / payload
        require(not stored.is_symlink() and stored.stat().st_size == row["stored_bytes"] and
                sha(stored) == row["stored_sha256"], "stored archive member differs")
        digest, count = hashlib.sha256(), 0
        with gzip.open(stored, "rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
                count += len(chunk)
        require(count == row["raw_bytes"] and digest.hexdigest() == row["raw_sha256"],
                "decompressed archive member differs")
        raw_total += count
        stored_total += row["stored_bytes"]
    require({p.relative_to(directory).as_posix() for p in (directory / "payload").iterdir()} == payloads,
            "extra or missing stored archive member")
    return dict(status="CURRENT_FIRSTDOT_ARCHIVE_HASH_PASS", members=len(names), raw_bytes=raw_total,
                stored_bytes=stored_total, manifest_sha256=sha(directory / "manifest.json"),
                standalone_raw_recomputation=False, independent_clean_reproduction=False, new_emu_runs=0)


def run(repo, identity_path, matrix_build, matrix_run, c_build, c_run, output):
    paths = [Path(p).resolve() for p in (repo, identity_path, matrix_build, matrix_run, c_build, c_run, output)]
    repo, identity_path, matrix_build, matrix_run, c_build, c_run, output = paths
    identity = read(identity_path)
    fresh_output(output, [repo, identity_path.parent, matrix_build, matrix_run, c_build, c_run,
                         *[identity["configuration"][k] for k in ("hardware_source", "build_record", "am_home")]])
    output.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status="RUNNING", started=datetime.now(timezone.utc).isoformat(),
                 audit_tool_sha256=sha(__file__), new_emu_runs=0, new_nemu_runs=0,
                 standalone_raw_recomputation=False, independent_clean_reproduction=False)
    save(output / "state.json", state)
    try:
        evidence_inputs = {str(p): sha(p) for root in (matrix_build, matrix_run, c_build, c_run)
                           for p in tree_files(root)}
        save(output / "evidence-inputs.json", evidence_inputs)
        combo = load_combination(repo)
        identity, matrix, matrix_inputs = raw_matrix(combo, repo, identity_path, matrix_build, matrix_run, output)
        c_proof, c_inputs = raw_c(combo, repo, identity_path, identity, matrix_build, matrix_run, c_build, c_run, output)
        inputs = merge_inputs(matrix_inputs, c_inputs)
        verify_files(inputs)
        save(output / "external-inputs.json", inputs)
        verify_files(evidence_inputs)
        selected = archive_inputs(repo, identity_path, identity, matrix_build, matrix_run, c_build, c_run,
                                  inputs, output, combo)
        archive = pack_archive(selected, output / "archive")
        verify_files(evidence_inputs)
        verify_files(inputs)
        state.update(status="CURRENT_FIRSTDOT_RAW_RECOMPUTATION_AND_ARCHIVE_PASS",
                     original_emu_processes=36, matrix_original_emu_processes=33, c_original_emu_processes=3,
                     formal_windows=384, c_normal_case_executions=96, archive=archive,
                     source_commit=identity["source_commit"], emu_sha256=identity["hardware_profile"]["emu_sha256"])
    except BaseException as error:
        state.update(status="FAILED", error=repr(error))
        raise
    finally:
        state["finished"] = datetime.now(timezone.utc).isoformat()
        save(output / "state.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "identity", "matrix-build", "matrix-run", "c-build", "c-run", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repo, args.identity, args.matrix_build, args.matrix_run,
                         args.c_build, args.c_run, args.output), indent=2))


if __name__ == "__main__":
    main()
