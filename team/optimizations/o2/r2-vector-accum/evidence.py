"""Seal S1 evidence and independently recompute archived architectural results.

An offline PASS rechecks archived bytes and identities, not absent external
hardware, NEMU, AM or toolchain binaries. It starts no simulator.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile

import candidate
import gate as g
import experiment as a

ROOT = Path(__file__).resolve().parents[4]
S1 = candidate.REL
OLD_EVIDENCE_SHA = "ae648951a8258ea20d239e977ea616f1c03ef00e4e83e0d2f7878354434026be"
PORTABLE = Path("team/optimizations/o2/fullcore/portable.py")
PORTABLE_SHA = "7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b"
INDEX_HELPER = g.REL / "merged_index.py"
INDEX_HELPER_SHA = "a67a26ece6413d7a3f06466e503a2a42d2d8ed33a287b0c9110c9e7c4aece764"
IDENTITY_FIELDS = ("kind", "source_commit", "am_revision", "external_files", "toolchain",
                   "s1_candidate_sha256", "snapshot_files")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()

def modules(repo):
    repo = Path(repo).resolve()
    for module, relative in ((a, S1 / "experiment.py"), (g, S1 / "gate.py"),
                             (candidate, S1 / "candidate.py"),
                             (a.legacy_f, g.REL / "fullcore_screen.py"),
                             (a.legacy_m, g.REL / "merged_screen.py"),
                             (g.original, g.REL / "linked_gate.py")):
        g.require(Path(module.__file__).resolve() == (repo / relative).resolve(),
                  "executed module outside selected repository: " + str(relative))
    g.require(Path(__file__).resolve() == (repo / S1 / "evidence.py").resolve(), "evidence entry path")
    g.require(g.sha(repo / g.REL / "merged_evidence.py") == OLD_EVIDENCE_SHA,
              "frozen reusable evidence checker changed")
    g.require(g.sha(repo / INDEX_HELPER) == INDEX_HELPER_SHA, "frozen Git index helper changed")
    a.legacy_m.checker_files(repo)
    f = g.load("s1_evidence_fullcore", repo / g.REL / "fullcore_screen.py")
    f.g = g
    m = g.load("s1_evidence_merged", repo / g.REL / "merged_screen.py")
    m.g, m.f, m.CONTRACT, m.PASS = g, f, a.CONTRACT, a.PASS
    e = g.load("s1_evidence_reusable", repo / g.REL / "merged_evidence.py")
    e.g, e.f, e.m = g, f, m
    return e, m, f

def complete_state(state):
    counts = ("new_emu_runs", "normal_runs", "negative_runs", "replay_runs", "measured_windows")
    g.require(all(type(state.get(k)) is int for k in counts) and
              {"active_pid", "active_result", "started", "finished", "operation_id"} <= set(state),
              "incomplete campaign state schema")
    start, finish = (datetime.fromisoformat(state[k]) for k in ("started", "finished"))
    g.require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish and
              isinstance(state["operation_id"], str) and bool(state["operation_id"].strip()), "campaign time/operation identity")
    g.require(state.get("contract") == a.CONTRACT and state.get("status") == a.PASS and
              state.get("new_emu_runs") == 57 and state.get("normal_runs") == 56 and
              state.get("negative_runs") == 1 and state.get("replay_runs") == 4 and
              state.get("measured_windows") == 768 and state.get("performance_measured") is True and
              state.get("active_pid") is None and state.get("active_result") is None and
              state.get("hardware_changed") is False and state.get("historical_b0_h1_acceptance") is False and
              state.get("whole_suite_acceptance") is False, "S1 campaign incomplete or wrong scope")

def expected_jobs(images):
    jobs = {}
    for image in images:
        if image["suite"] == "smoke":
            label = "recovery-s1-s05" if image["variant"] == "s1" and image["shard"] == 5 else "smoke-" + image["name"]
        else:
            label = "formal-" + image["name"]
        jobs[label] = image, 0, False
        if image["suite"] == "performance" and image["dataset"] == 0 and image["shard"] in (5, 7):
            jobs["replay-" + image["name"]] = image, 1, False
    smoke = next(i for i in images if i["suite"] == "smoke" and i["variant"] == "s1" and i["shard"] == 5)
    jobs["negative-s1-s05"] = smoke, 0, True
    g.require(len(jobs) == 57, "S1 expected job inventory")
    return jobs

def expected_order():
    labels = ["negative-s1-s05", "recovery-s1-s05"]
    labels += ["smoke-" + a.name(i) for i in a.inventory()[:4]
               if not (i["variant"] == "s1" and i["shard"] == 5)]
    for shard in range(8):
        for dataset in range(3):
            for variant in (("s0", "s1") if (shard + dataset) % 2 == 0 else ("s1", "s0")):
                labels.append("formal-" + a.name(dict(suite="performance", shard=shard, dataset=dataset, variant=variant)))
    labels += ["replay-" + a.name(dict(suite="performance", shard=shard, dataset=0, variant=variant))
               for shard in (5, 7) for variant in ("s0", "s1")]
    return labels

def execution_order(records):
    ordered = sorted(records, key=lambda r: datetime.fromisoformat(r["started"]))
    g.require([PurePosixPath(r["cwd"]).parent.name for r in ordered] == expected_order(),
              "actual execution order differs from the paired alternating plan")
    for before, after in zip(ordered, ordered[1:]):
        g.require(datetime.fromisoformat(before["finished"]) <= datetime.fromisoformat(after["started"]),
                  "unexpected concurrent EMU runs")
    return ordered

def pack(repo, run, output, support=()):
    g.require(os.name == "posix", "pack requires Linux/WSL recorded input paths")
    repo, run, output = repo.resolve(), run.resolve(), output.resolve()
    e, m, f = modules(repo)
    complete_state(a.read_json(run / "state.json"))
    cfg, inputs = a.read_json(run / "configuration.json"), a.read_json(run / "runtime-inputs.json")
    canonical, hardware = Path(cfg["canonical_build"]), Path(cfg["build_record"])
    g.require(not output.exists() and not output.is_relative_to(run) and
              not output.is_relative_to(canonical), "archive must be new and outside inputs")
    for item in support:
        g.require(not item.is_dir() or not output.is_relative_to(item.resolve()), "archive inside support input")
    m.verify_files(inputs)
    output.mkdir(parents=True)
    archive_tools = e.portable(repo)
    entries, originals = [], {}

    def add(raw, logical, original):
        archive_tools.safe_relative(logical)
        g.require(original not in originals, "duplicate archive original: " + original)
        path = Path("files") / logical
        data, encoding = raw, "identity"
        # ELF/BIN have substantial padding. Compress any profitable payload,
        # retaining both the exact raw and stored hashes in the v1 manifest.
        if len(raw) >= 4096:
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            if len(compressed) + 64 < len(raw):
                path = path.with_name(path.name + ".gz")
                data, encoding = compressed, "gzip"
        target = output / path
        g.require(not target.exists(), "duplicate archive logical path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append(dict(original=original, stored=path.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=digest(raw),
                            stored_bytes=len(data), stored_sha256=digest(data)))
        originals[original] = logical

    def add_file(path, logical):
        g.require(path.is_file() and not path.is_symlink(), "missing/symlink evidence: " + str(path))
        add(path.read_bytes(), logical, str(path))

    for directory, prefix in ((run, "campaign"), (canonical, "canonical")):
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(directory)
            if set(rel.parts) & {"objects", "__pycache__"}:
                continue
            if "cwd" in rel.parts and not (path.name in m.AUX and path.parent.name == "build"):
                continue
            add_file(path, prefix + "/" + rel.as_posix())
    for name in m.META:
        add_file(hardware / name, "hardware/" + name)
    add_file(Path(cfg["build_driver"]), "hardware/build-driver.py")
    add_file(Path(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py",
             "hardware/original-build-driver.py")
    for name in m.AUX:
        add_file(Path(cfg["hardware_source"]) / "build" / name, "hardware/" + name)
    for name in sorted(inputs):
        path = Path(name)
        if path.is_relative_to(repo):
            add_file(path, "tools/" + path.relative_to(repo).as_posix())
    for rel in (g.REL / "merged_evidence.py", e.PORTABLE, INDEX_HELPER, S1 / "evidence.py",
                S1 / "test_candidate.py", S1 / "test_evidence.py", S1 / "README.md"):
        if str(repo / rel) not in originals:
            add_file(repo / rel, "tools/" + rel.as_posix())
    for item in support:
        path = item.resolve()
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    add_file(child, "support/" + path.name + "/" + child.relative_to(path).as_posix())
        else:
            add_file(path, "support/" + path.name)
    all_inputs = dict(inputs)
    def seal(name, sha):
        g.require(name not in all_inputs or all_inputs[name] == sha, "mixed input identity")
        all_inputs[name] = sha
    for path in (run / "runs").glob("*/result.json"):
        for name, sha in a.read_json(path)["files"].items():
            seal(name, sha)
    for image in a.read_json(canonical / "images.json")["images"]:
        receipt = a.read_json(Path(image["path"]) / "build.json")
        for name, sha in receipt["external_files"].items():
            seal(name, sha)
        for tool in receipt["toolchain"].values():
            seal(tool["path"], tool["sha256"])
    m.verify_files(all_inputs)
    add(json_bytes({name: dict(sha256=sha, logical=originals.get(name))
                    for name, sha in sorted(all_inputs.items())}), "sealed-inputs.json", "generated:sealed-inputs")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    manifest = dict(version=1, contract=a.CONTRACT, created_utc=f.now(), source_commit_at_export=head,
                    source_root=str(repo), work_root=str(run), files=entries,
                    exclusions=["EMU, normal NEMU and flash binaries", "hardware/dependency trees and generated RTL",
                                "AM libraries and GNU tool binaries", "canonical intermediate objects",
                                "incidental simulator cwd output"],
                    scope="exact evidence bytes; external physical inputs represented by sealed hashes")
    raw = json_bytes(manifest)
    (output / "archive-manifest.json").write_bytes(raw)
    (output / "archive-manifest.sha256").write_text(digest(raw) + "  archive-manifest.json\n")
    archive = archive_tools.Archive(output)
    result = dict(status="R2_S1_ARCHIVE_BYTES_PASS", **archive.bytes_result)
    g.save(output / "archive-check.json", result)
    return result

def offline_pairs(images, builds, repo, sealed):
    identity = None
    for image in images:
        record = a.read_json(builds[image["name"]] / "build.json")
        current = {key: record[key] for key in IDENTITY_FIELDS}
        if identity is None:
            identity = current
        g.require(current == identity, "archived cross-image build identity differs")
        g.require(record["am_revision"] == a.legacy_f.AM_COMMIT and len(record["external_files"]) == 2 and
                  sum(p.endswith("/am/build/am-riscv64-xs.a") for p in record["external_files"]) == 1 and
                  sum(p.endswith("/libs/klib/build/klib-riscv64-xs.a") for p in record["external_files"]) == 1,
                  "unexpected archived AM identity")
        g.require(set(record["toolchain"]) == {"gcc", "ld", "ar", "objcopy", "objdump", "readelf", "make"},
                  "unexpected GNU toolchain inventory")
        for path, sha in record["external_files"].items():
            g.require(sealed.get(path, {}).get("sha256") == sha, "unsealed AM library")
        for tool in record["toolchain"].values():
            g.require(sealed.get(tool["path"], {}).get("sha256") == tool["sha256"], "unsealed GNU tool")
    base = candidate.load_base(repo)
    layouts = []
    indexed = {(i["suite"], i["dataset"], i["shard"], i["variant"]): i for i in images}
    for image in images:
        if image["variant"] != "s0":
            continue
        other = indexed[(image["suite"], image["dataset"], image["shard"], "s1")]
        b0, b1 = builds[image["name"]], builds[other["name"]]
        e0, e1 = (g.ELF((b / "vdot-perf.elf").read_bytes()) for b in (b0, b1))
        layout = g.paired_layout(e0, e1, (b0 / "vdot-perf.bin").read_bytes(), (b1 / "vdot-perf.bin").read_bytes())
        layouts.append(dict(s0=image["name"], s1=other["name"], **layout))
        m0, m1 = (a.read_json(b / "data/manifest.json") for b in (b0, b1))
        g.require(m0["plan"] == m1["plan"] and len(m0["rows"]) == len(m1["rows"]) == 4,
                  "archived paired plan differs")
        g.require(all(e0.symbols[f"t13_kernel_{i}"][0] == e1.symbols[f"t13_kernel_{i}"][0] for i in range(4)),
                  "archived paired entry differs")
        for r0, r1 in zip(m0["rows"], m1["rows"]):
            g.require({k: v for k, v in r0.items() if k not in ("body", "r2_variant")} ==
                      {k: v for k, v in r1.items() if k not in ("body", "r2_variant")}, "archived paired math/ABI differs")
            g.require(r0["body"] == base.kernel(r0["m"], r0["k"], r0["method"], r0["software"], r0["scope"]),
                      "archived S0 differs from frozen body")
    return identity, layouts

def fixture_identity(archive, fixture, cfg, m, f):
    prefix = "campaign/negative-fixture/"
    g.require(fixture["source_sha256"] == m.NEGATIVE_SHA and
              fixture["normal_reference_sha256"] == f.REFERENCE and
              fixture["historical_negative_hash_claim"] is False and
              digest(archive.raw(prefix + "negative-fixture.c")) == m.NEGATIVE_SHA and
              digest(archive.raw(prefix + "negative-reference.so")) == fixture["negative_sha256"],
              "negative fixture identity differs")
    compiler = fixture["command"][0]
    directory = PurePosixPath(fixture["binary"]).parent
    argv = [compiler, "-shared", "-fPIC", "-O2", '-DREF_SO="' + cfg["reference"] + '"',
            str(directory / "negative-fixture.c"), "-Wl,--no-as-needed", cfg["reference"],
            "-ldl", "-o", fixture["binary"]]
    g.require(fixture["command"] == argv, "negative fixture compile command")
    for step in ("compiler", "compile", "linkage"):
        location = prefix + step
        receipt = archive.json(location + "/command.json")
        g.require(receipt.get("process_started") is True and receipt.get("exit_code") == 0 and
                  not receipt.get("timed_out") and receipt.get("raw_sha256") ==
                  {name: digest(archive.raw(location + "/" + name)) for name in ("stdout.log", "stderr.log")},
                  "incomplete or changed fixture build receipt")
        expected = ([compiler, "--version"] if step == "compiler" else argv if step == "compile"
                    else [receipt["command"][0], "-d", fixture["binary"]])
        g.require(receipt["command"] == expected, "fixture tool command differs")
    g.require("Shared library: [" + cfg["reference"] + "]" in
              archive.raw(prefix + "linkage/stdout.log").decode(), "fixture normal reference linkage")

def build_commands(archive, image, receipt):
    g.require(receipt.get("contract") == a.CONTRACT, "canonical build contract differs")
    directory = PurePosixPath(image["path"])
    tools = receipt["toolchain"]
    gcc, make = tools["gcc"]["path"], tools["make"]["path"]
    g.require(gcc.endswith("gcc"), "GNU compiler path")
    expected = [
        ("make-command", [make, "-C", str(directory / "source"), "ARCH=riscv64-xs", "MARCH=rv64gcv",
                          "CROSS_COMPILE=" + gcc[:-3], "T13_DATA=" + str(directory / "data"),
                          "T13_OBJ_ROOT=" + str(directory / "objects"), "BINARY=" + str(directory / "vdot-perf"),
                          "-o", "am", "-o", "klib", "-j1", "image"]),
        ("reference-command", [gcc, "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-c",
                               str(directory / "data/kernels.S"), "-o", str(directory / "kernels-reference.o")]),
    ]
    g.require(len(receipt["commands"]) == 2, "canonical build requires two real commands")
    previous_finish = None
    for index, (label, argv) in enumerate(expected):
        logical = "canonical/images/" + image["name"] + "/" + label
        record = archive.json(logical + "/command.json")
        g.require(record == receipt["commands"][index] and record["command"] == argv and
                  record["cwd"] == archive.manifest["source_root"], "canonical build command identity differs")
        g.require(record.get("process_started") is True and type(record.get("pid")) is int and record["pid"] > 0 and
                  type(record.get("exit_code")) is int and record["exit_code"] == 0 and not record.get("timed_out"),
                  "canonical command was not a successful real process")
        g.require(record["raw_sha256"] == {name: digest(archive.raw(logical + "/" + name))
                                          for name in ("stdout.log", "stderr.log")}, "canonical build raw logs differ")
        start, finish = (datetime.fromisoformat(record[k]) for k in ("started", "finished"))
        g.require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish and
                  (previous_finish is None or previous_finish <= start), "canonical build command timestamps differ")
        previous_finish = finish

def common_identity(archive, repo, cfg, images, common, sealed, m, f):
    recorded_repo = PurePosixPath(archive.manifest["source_root"])
    g.require(recorded_repo.is_absolute(), "recorded source root must be absolute")
    expected = {}
    current = a.legacy_m.checker_files(repo)
    for name, sha in current.items():
        relative = Path(name).relative_to(repo)
        expected[str(recorded_repo / relative.as_posix())] = sha
    for relative in (S1 / "candidate.py", S1 / "gate.py", S1 / "experiment.py", g.REL / "machine_model.py"):
        expected[str(recorded_repo / relative.as_posix())] = g.sha(repo / relative)
    for name, sha in m.META.items():
        expected[str(PurePosixPath(cfg["build_record"]) / name)] = sha
    for name, sha in m.AUX.items():
        expected[str(PurePosixPath(cfg["hardware_source"]) / "build" / name)] = sha
    pins = archive.json("hardware/hardware-inputs.json")
    expected.update({str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): m.EMU,
                     cfg["reference"]: f.REFERENCE, cfg["flash"]: f.FLASH,
                     cfg["build_driver"]: pins["build_script_sha256"],
                     str(PurePosixPath(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py"):
                         "8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0"})
    for name in ("images.json", "state.json", "pairs.json"):
        expected[str(PurePosixPath(cfg["canonical_build"]) / name)] = digest(archive.raw("canonical/" + name))
    for image in images:
        for name in ("build.json", "data/manifest.json"):
            expected[str(PurePosixPath(image["path"]) / name)] = digest(
                archive.raw("canonical/images/" + image["name"] + "/" + name))
    g.require(common == expected, "common runtime input inventory differs")
    for name, sha in common.items():
        g.require(sealed.get(name, {}).get("sha256") == sha, "unsealed common runtime input")

def original_identity(archive, cfg, sealed, m):
    source = PurePosixPath(archive.manifest["source_root"])
    run = PurePosixPath(archive.manifest["work_root"])
    g.require(source.is_absolute() and run.is_absolute(), "archive source/run roots must be absolute")
    seen = set()
    hardware = {name: str(PurePosixPath(cfg["build_record"]) / name) for name in m.META}
    hardware.update({name: str(PurePosixPath(cfg["hardware_source"]) / "build" / name) for name in m.AUX})
    hardware.update({"build-driver.py": cfg["build_driver"],
                     "original-build-driver.py": str(PurePosixPath(cfg["hardware_source"]) /
                                                      "team/optimizations/o2/fullcore/build_fullcore.py")})
    for logical, record in archive.records.items():
        original = record.get("original")
        g.require(isinstance(original, str) and original not in seen, "duplicate or invalid archive original")
        seen.add(original)
        if logical.startswith("campaign/"):
            expected = str(run / logical[len("campaign/"):])
        elif logical.startswith("canonical/"):
            expected = str(PurePosixPath(cfg["canonical_build"]) / logical[len("canonical/"):])
        elif logical.startswith("tools/"):
            expected = str(source / logical[len("tools/"):])
        elif logical.startswith("hardware/"):
            expected = hardware.get(logical[len("hardware/"):])
        elif logical == "sealed-inputs.json":
            expected = "generated:sealed-inputs"
        elif logical.startswith("support/"):
            g.require(PurePosixPath(original).is_absolute() and original.endswith("/" + logical[len("support/"):]),
                      "support original path differs")
            expected = original
        else:
            raise ValueError("unexpected archive namespace: " + logical)
        g.require(original == expected, "archive original path differs: " + logical)
    for original, entry in sealed.items():
        logical = entry["logical"]
        if logical is not None:
            g.require(logical in archive.records and archive.records[logical]["original"] == original,
                      "sealed logical/original association differs")

def sealed_closure(archive, common, records, identity, sealed):
    expected = dict(common)
    def include(name, sha):
        g.require(name not in expected or expected[name] == sha, "conflicting sealed input identity")
        expected[name] = sha
    for record in records:
        for name, sha in record["files"].items():
            include(name, sha)
    for name, sha in identity["external_files"].items():
        include(name, sha)
    for tool in identity["toolchain"].values():
        include(tool["path"], tool["sha256"])
    originals = {record["original"]: logical for logical, record in archive.records.items()}
    g.require(sealed == {name: dict(sha256=sha, logical=originals.get(name)) for name, sha in expected.items()},
              "sealed input set is not the exact runtime/build closure")

def retirement_diagnostics(repo, build, run, record):
    """Describe retirement timing after normal_audit; do not infer execute latency."""
    if record["suite"] != "performance" or record["replay"] != 0:
        return []
    checker = g.load("s1_retirement_diagnostic_parser", repo / g.O3 / "check.py")
    decoder = g.auditor(repo)
    manifest = a.read_json(build / "data/manifest.json")
    elf = g.ELF((build / "vdot-perf.elf").read_bytes())
    bodies = []
    for index in range(4):
        name = f"t13_kernel_{index}"
        value = decoder.audit_kernel(elf.symbol_data(name), elf.symbols[name][0])
        bodies.append({int(i["pc"], 16): i for i in value["instructions"]})
    events = checker.base.parse_events((run / "stderr.log").read_text())["RETIRE"]
    windows, current = [], None
    for event in events:
        if event["word"] == checker.base.START:
            g.require(current is None, "nested retirement diagnostic window")
            current = []
        if current is not None:
            current.append(event)
        if event["word"] == checker.base.STOP:
            g.require(current is not None, "retirement diagnostic stop without start")
            windows.append(current); current = None
    g.require(current is None and len(windows) == len(manifest["plan"]) == len(record["samples"]),
              "retirement diagnostic window count differs")
    result = []
    for events, plan, sample in zip(windows, manifest["plan"], record["samples"]):
        if plan["phase"] != "measured":
            continue
        body = bodies[plan["index"]]
        retired = [(event["cycle"], event["pc"] + 4 * j)
                   for event in events for j in range(event["count"]) if event["pc"] + 4 * j in body]
        g.require([pc for _, pc in retired] == list(body), "retirement diagnostic body coverage differs")
        start, stop = sample["sample_ticks"][1:3]
        first, last = retired[0][0], retired[-1][0]
        g.require(start <= first <= last <= stop and stop - start == sample["cycles"],
                  "body retirement lies outside calibrated interval")
        groups = []
        for cycle, pc in retired:
            if not groups or cycle != groups[-1]["cycle"]:
                groups.append(dict(cycle=cycle, instructions=[]))
            groups[-1]["instructions"].append(body[pc])
        gaps = [dict(cycles=right["cycle"] - left["cycle"],
                     next_retired=[dict(pc=i["pc"], mnemonic=i["mnemonic"], operands=i["operands"])
                                   for i in right["instructions"]])
                for left, right in zip(groups, groups[1:])]
        result.append(dict({k: sample[k] for k in
                            ("variant", "shard", "software", "method", "dataset", "repeat", "seq", "cycles", "instructions")},
                           body_instructions=len(retired), distinct_body_retirement_cycles=len(groups),
                           sample_to_first_body_retire=first - start,
                           first_to_last_body_retire=last - first,
                           last_body_retire_to_sample=stop - last,
                           largest_inter_retirement_gaps=sorted(gaps, key=lambda v: -v["cycles"])[:3]))
    return result

def audit(repo, archive_path):
    g.require(os.name == "posix", "architecture audit requires Linux/WSL for exact frozen regeneration; use bytes on native Windows")
    repo = repo.resolve()
    e, m, f = modules(repo)
    archive = e.portable(repo).Archive(archive_path)
    g.require(archive.manifest.get("contract") == a.CONTRACT, "wrong S1 archive contract")
    state = archive.json("campaign/state.json")
    complete_state(state)
    common, sealed = archive.json("campaign/runtime-inputs.json"), archive.json("sealed-inputs.json")
    cfg = archive.json("campaign/configuration.json")
    original_identity(archive, cfg, sealed, m)
    for name, entry in sealed.items():
        if entry["logical"] is not None:
            g.require(digest(archive.raw(entry["logical"])) == entry["sha256"], "sealed bytes differ: " + name)
    for name, sha in m.META.items():
        g.require(digest(archive.raw("hardware/" + name)) == sha, "hardware metadata differs")
    pins = archive.json("hardware/hardware-inputs.json")
    g.require(pins["source_commit"] == m.SOURCE and pins["emu_sha256"] == m.EMU and
              len(pins["files"]) == 429 and len(pins["dependency_files"]) == 21236 and
              len(archive.json("hardware/generated-artifacts.json")) == 1672,
              "wrong archived hardware profile")
    g.require(digest(archive.raw("hardware/build-driver.py")) == pins["build_script_sha256"],
              "actual builder differs")
    # Execute checked-out tools only after matching their sealed export bytes.
    for logical in archive.records:
        if logical.startswith("tools/team/") and logical.endswith(".py"):
            relative = Path(logical).relative_to("tools")
            g.require(g.sha(repo / relative) == digest(archive.raw(logical)),
                      "offline tool differs from sealed source: " + str(relative))
    images = archive.json("canonical/images.json")["images"]
    expected = {a.name(i): i for i in a.inventory()}
    g.require(len(images) == 52 and {i["name"] for i in images} == set(expected), "archived image inventory")
    g.require(archive.json("canonical/state.json")["status"] ==
              "S1_52_CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN", "incomplete archived canonical build")
    for image in images:
        g.require(all(image[k] == v for k, v in expected[image["name"]].items()), "archived image label differs")
        g.require(PurePosixPath(image["path"]) == PurePosixPath(cfg["canonical_build"]) / "images" / image["name"],
                  "archived image path differs")
    jobs = expected_jobs(images)
    found = {p.split("/")[2] for p in archive.records if p.startswith("campaign/runs/") and
             p.endswith("/result.json") and len(p.split("/")) == 4}
    g.require(found == set(jobs), "missing or extra archived S1 job")
    fixture = archive.json("campaign/negative-fixture/fixture.json")
    fixture_identity(archive, fixture, cfg, m, f)
    common_identity(archive, repo, cfg, images, common, sealed, m, f)
    external = {str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): m.EMU,
                cfg["reference"]: f.REFERENCE, cfg["flash"]: f.FLASH}
    first = archive.json("canonical/images/" + images[0]["name"] + "/build.json")
    external.update(first["external_files"])
    for tool in first["toolchain"].values():
        external[tool["path"]] = tool["sha256"]
    for name, entry in sealed.items():
        if entry["logical"] is None:
            g.require(external.get(name) == entry["sha256"], "unarchived non-external input: " + name)
    records, negative, diagnostics, retirements = [], None, [], []
    with tempfile.TemporaryDirectory(prefix="r2-s1-audit-") as tmp:
        extracted = Path(tmp)
        for logical in archive.records:
            if logical.startswith(("canonical/", "campaign/")):
                target = extracted / logical
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.raw(logical))
        builds = {}
        for image in images:
            build = extracted / "canonical/images" / image["name"]
            manifest, receipt = a.read_json(build / "data/manifest.json"), a.read_json(build / "build.json")
            m.validate_selection(image, manifest, receipt)
            build_commands(archive, image, receipt)
            g.verify_build(build, repo)
            g.require(g.sha(build / "vdot-perf.bin") == image["image_sha256"], "archived image bytes differ")
            builds[image["name"]] = build
        identity, layouts = offline_pairs(images, builds, repo, sealed)
        g.require(set(identity["external_files"]) ==
                  {str(PurePosixPath(cfg["am_home"]) / rel) for rel in
                   ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")},
                  "canonical AM paths differ from recorded configuration")
        pair_record = archive.json("canonical/pairs.json")
        g.require(pair_record == archive.json("campaign/pair-layout.json") and
                  pair_record["status"] == "S1_PAIR_LAYOUT_AND_FAIR_INPUTS_PASS" and
                  pair_record["pairs"] == 26 and pair_record["kernel_slot_bytes"] == 8192 and
                  pair_record["nonkernel_loaded_bytes_identical"] is True and pair_record["layouts"] == layouts and
                  pair_record["historical_samples_reused"] is False and pair_record["build_identity"] == identity,
                  "cached pair validation differs")
        suite = g.load("s1_offline_runtime_banner", repo / "team/optimizations/o2/fullcore/run_suite.py")
        for label, (image, replay, is_negative) in jobs.items():
            run = extracted / "campaign/runs" / label
            record = a.read_json(run / "result.json")
            g.require(PurePosixPath(record["cwd"]) ==
                      PurePosixPath(archive.manifest["work_root"]) / "runs" / label / "cwd", "run cwd/label differs")
            e.run_identity(record, image, replay, is_negative, cfg, fixture, common, sealed)
            g.require(record["raw_sha256"] == {p: g.sha(run / p) for p in ("stdout.log", "stderr.log")},
                      "raw transcript receipt differs")
            suite.validate_runtime((run / "stdout.log").read_text() + (run / "stderr.log").read_text(),
                                   record["reference"])
            build = builds[image["name"]]
            if is_negative:
                old_details, old_trace = a.read_json(run / "negative.json"), a.read_json(run / "observation.json")
                details = m.negative_check(repo, build, run, record)
                g.require(details == old_details == record["negative_details"] and
                          a.read_json(run / "observation.json") == old_trace, "negative cached result differs")
                negative = record
            else:
                checked = e.normal_audit(repo, build, run, record, {p: v["sha256"] for p, v in sealed.items()})
                diagnostics.extend(checked["fu_windows"])
                retirements.extend(retirement_diagnostics(repo, build, run, record))
                records.append(record)
        recovery = next(r for r in records if r["suite"] == "smoke" and r["variant"] == "s1" and r["shard"] == 5)
        sealed_closure(archive, common, records + [negative], identity, sealed)
        e.audit_recovery(negative, recovery)
        chronological = execution_order(records + [negative])
        g.require(datetime.fromisoformat(state["started"]) <= datetime.fromisoformat(chronological[0]["started"]) and
                  datetime.fromisoformat(chronological[-1]["finished"]) <= datetime.fromisoformat(state["finished"]),
                  "campaign timestamps do not enclose actual runs")
        for record in records:
            if record["replay"] == 1:
                original = next(r for r in records if r["name"] == record["name"] and r["replay"] == 0)
                g.require(m.signature(original) == m.signature(record), "replay cycles/instructions differ")
    stats = a.summarize(records)
    cached = archive.json("campaign/results.json")
    g.require(cached["status"] == a.PASS and cached["contract"] == a.CONTRACT and cached["negative"] == negative,
              "summary scope or negative differs")
    g.require(len(records) == len(cached["runs"]) == 56 and
              {(r["name"], r["replay"]): r for r in cached["runs"]} ==
              {(r["name"], r["replay"]): r for r in records}, "summary run receipts differ")
    for key in ("rows", "comparisons"):
        g.require(cached[key] == stats[key], "cached statistics differ: " + key)
    sample_key = lambda s: (s["variant"], s["shard"], s["software"], s["method"], s["dataset"], s["repeat"])
    g.require(sorted(cached["samples"], key=sample_key) == sorted(stats["samples"], key=sample_key),
              "cached formal samples differ")
    g.require(len(diagnostics) == 384, "missing formal vdot diagnostic windows")
    g.require(len(retirements) == 768, "missing formal retirement diagnostic windows")
    return dict(status="R2_S1_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS", contract=a.CONTRACT,
                archive=archive.bytes_result, normal_runs=56, expected_negative_runs=1, formal_windows=768,
                replay_runs=4, new_emu_runs=0, new_nemu_runs=0,
                physical_hardware_and_reference_inputs_revalidated=False,
                physical_am_and_toolchain_inputs_revalidated=False,
                historical_b0_h1_acceptance=False, whole_suite_acceptance=False,
                rows=stats["rows"], comparisons=stats["comparisons"], fu_window_diagnostics=diagnostics,
                retirement_window_diagnostics=retirements,
                retirement_diagnostic_scope="retirement geometry and gaps; not instruction execution latency or causal stall attribution",
                fu_diagnostic_scope="accepts/responses inside calibrated cycle intervals; not attribution of whole-window time",
                scope="sealed ELF/golden/CSR/exact retirement/O2 trace/negative/recovery/statistics replay; external physical inputs represented by hashes")

def audit_bytes(repo, archive_path):
    g.require(g.sha(repo / PORTABLE) == PORTABLE_SHA, "portable archive checker changed")
    portable = g.load("s1_portable_bytes", repo / PORTABLE)
    archive = portable.Archive(archive_path)
    g.require(archive.manifest.get("contract") == a.CONTRACT, "wrong S1 archive contract")
    return dict(status="R2_S1_ARCHIVE_BYTES_PASS", **archive.bytes_result,
                architecture_recomputed=False, new_emu_runs=0, new_nemu_runs=0)

def index_helper(repo):
    g.require(g.sha(repo / INDEX_HELPER) == INDEX_HELPER_SHA, "frozen Git index helper changed")
    return g.load("s1_git_index_helper", repo / INDEX_HELPER)

def index_payloads(repo, archive_path, archive, helper):
    """Check actual stage-0 blobs; valid worktree bytes alone do not prove delivery."""
    repo, archive_path = repo.resolve(), archive_path.resolve()
    g.require(archive_path.is_relative_to(repo), "archive must be inside the repository")
    g.require(archive.manifest.get("contract") == a.CONTRACT, "wrong S1 archive contract")
    relative = archive_path.relative_to(repo).as_posix()
    expected = {relative + "/" + r["stored"] for r in archive.manifest["files"]}
    expected.update(relative + "/" + n for n in
                    ("archive-manifest.json", "archive-manifest.sha256", "archive-check.json"))
    actual = {p.relative_to(repo).as_posix() for p in archive_path.rglob("*") if p.is_file()}
    g.require(actual == expected, "archive disk inventory differs from manifest and three metadata files")
    g.require(a.read_json(archive_path / "archive-check.json") ==
              dict(status="R2_S1_ARCHIVE_BYTES_PASS", **archive.bytes_result), "cached byte check differs")
    entries = helper.index_entries(helper.git(repo, "ls-files", "--stage", "-z", "--", relative))
    missing, extra = sorted(expected - set(entries)), sorted(set(entries) - expected)
    g.require(not missing and not extra,
              "archive index inventory incomplete: missing=%d extra=%d; first=%r" %
              (len(missing), len(extra), missing[:3]))
    names = sorted(expected)
    requests = "".join(entries[n]["oid"] + "\n" for n in names).encode("ascii")
    stream = io.BytesIO(helper.git(repo, "cat-file", "--batch", data=requests))
    for name in names:
        header = stream.readline().split()
        g.require(len(header) == 3 and header[0].decode("ascii") == entries[name]["oid"] and
                  header[1] == b"blob", "missing staged blob: " + name)
        raw = stream.read(int(header[2]))
        g.require(stream.read(1) == b"\n" and raw == (repo / name).read_bytes(),
                  "staged archive bytes differ: " + name)
    g.require(not stream.read(), "extra Git blob output")
    return dict(status="R2_S1_ARCHIVE_COMPLETE_GIT_INDEX_PASS",
                created_utc=datetime.now(timezone.utc).isoformat(),
                source_base=helper.git(repo, "rev-parse", "HEAD").decode().strip(),
                checker_sha256=g.sha(Path(__file__)), helper_sha256=INDEX_HELPER_SHA,
                archive=archive.bytes_result, archive_files_in_git_index=len(names), missing=0, extra=0,
                git_file_modes=dict(sorted(Counter(v["mode"] for v in entries.values()).items())),
                architecture_replayed=False, new_emu_runs=0, new_nemu_runs=0,
                scope="Exact manifest inventory, regular stage-0 modes and stored bytes in Git index; architecture audit is separate")

def audit_index(repo, archive_path):
    helper = index_helper(repo)
    g.require(g.sha(repo / PORTABLE) == PORTABLE_SHA, "portable archive checker changed")
    portable = g.load("s1_index_portable", repo / PORTABLE)
    return index_payloads(repo, archive_path, portable.Archive(archive_path), helper)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--action", choices=("pack", "audit", "bytes", "index"), required=True)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--support", action="append", default=[], type=Path)
    args = parser.parse_args()
    if args.action == "pack":
        g.require(args.run is not None, "pack requires --run")
        result = pack(args.repo, args.run, args.archive, args.support)
    else:
        g.require(args.output is not None, "audit requires --output")
        index_helper(args.repo.resolve()).check_output_path(args.archive, args.output)
        result = {"audit": audit, "bytes": audit_bytes, "index": audit_index}[args.action](
            args.repo.resolve(), args.archive)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        g.save(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ("rows", "comparisons", "fu_window_diagnostics", "retirement_window_diagnostics")},
                     ensure_ascii=False, indent=2))
