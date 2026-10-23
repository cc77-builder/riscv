"""Seal and replay R4 callable-entry probe/matrix evidence without new EMU runs.

Archived external inputs are represented by hashes. Offline qualification does
not revalidate absent hardware, reference binaries, AM libraries or toolchains.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import types

import entry_candidate as c
import entry_gate as g
import entry_experiment as a

PORTABLE = Path("team/optimizations/o2/fullcore/portable.py")
PINS = {str(PORTABLE): "7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b",
        str(g.REL / "merged_evidence.py"): "ae648951a8258ea20d239e977ea616f1c03ef00e4e83e0d2f7878354434026be",
        str(g.REL / "merged_index.py"): "a67a26ece6413d7a3f06466e503a2a42d2d8ed33a287b0c9110c9e7c4aece764"}
SCOPE = "R4 full-width live DiffTest, one C-ABI call/return, exact retirement and calibrated counters"
IDENTITY = ("kind", "source_commit", "am_revision", "external_files", "toolchain", "snapshot_files", "contract")
BYTE_PASS = "R4_ENTRY_ARCHIVE_BYTES_PASS"
EXTRA = set(PINS) | {str(g.ENTRY / n) for n in
    ("entry_evidence.py", "test_entry.py", "test_entry_evidence.py", "ENTRY_CONTRACT.md")}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def modules(repo):
    repo = Path(repo).resolve()
    for module, name in ((g, "entry_gate.py"), (a, "entry_experiment.py"), (c, "entry_candidate.py")):
        g.require(Path(module.__file__).resolve() == repo / g.ENTRY / name, "R4 evidence module from another checkout")
    g.require(Path(__file__).resolve() == repo / g.ENTRY / "entry_evidence.py", "R4 evidence entry path")
    g.verify_sources(repo)
    a.frozen_f.pinned_modules(repo)
    for name, pin in PINS.items():
        g.require(g.sha(repo / name) == pin, "frozen archive helper drift: " + name)
    portable = g.load("r4_portable_archive", repo / PORTABLE)
    m = g.load("r4_archive_merged", repo / g.REL / "merged_screen.py")
    m.g, m.CONTRACT = g, c.CONTRACT
    e = g.load("r4_archive_common", repo / g.REL / "merged_evidence.py")
    proxy = types.SimpleNamespace(**vars(g))
    def adapted_load(name, path):
        if Path(path).resolve() != (repo / g.O3 / "check.py").resolve():
            return g.load(name, path)
        check = g.counter_adapter(repo)
        verify = check.verify
        def invoke(*args, **kwargs):
            result = verify(*args, **kwargs)
            result["scope"] = SCOPE
            return result
        check.verify = invoke
        return check
    proxy.load = adapted_load
    e.g, e.m, e.f = proxy, m, a.frozen_f
    return portable, m, e


def cohort(scope):
    g.require(scope in ("probe", "matrix"), "unknown R4 evidence scope")
    return a.inventory([3], [0]) if scope == "probe" else a.inventory([1, 3, 5, 7], [0, 1, 2])


def include(target, name, sha):
    g.require(name not in target or target[name] == sha, "conflicting input identity: " + name)
    target[name] = sha


def pack(repo, runs, output, scope, support=()):
    g.require(os.name == "posix", "physical sealing requires recorded Linux input paths")
    repo, output = repo.resolve(), output.resolve()
    portable, m, _ = modules(repo)
    runs = [p.resolve() for p in runs]
    g.require(runs and len(set(runs)) == len(runs) and len({p.name for p in runs}) == len(runs), "duplicate campaign")
    cfg, builds, all_inputs = None, {}, {}
    for run in runs:
        state = a.read(run / "state.json")
        g.require(state["status"] in ("R4_CALLABLE_ENTRY_SCREEN_PASS", "R4_CALLABLE_ENTRY_PARTIAL_PASS") and
                  state["active_pid"] is None and state["active_result"] is None and state.get("finished"),
                  "cannot seal incomplete campaign")
        current = a.read(run / "configuration.json")
        base = {k: v for k, v in current.items() if k != "canonical_builds"}
        cfg = base if cfg is None else cfg
        g.require(base == cfg, "campaign configurations differ")
        for path in current["canonical_builds"]:
            p = Path(path)
            g.require(p.is_absolute() and (p.name not in builds or builds[p.name] == p), "ambiguous build root")
            builds[p.name] = p
        for path, sha in a.read(run / "runtime-inputs.json").items():
            include(all_inputs, path, sha)
        for record in (run / "runs").glob("*/result.json"):
            for path, sha in a.read(record)["files"].items():
                include(all_inputs, path, sha)
    for root in builds.values():
        for image in a.read(root / "images.json")["images"]:
            build = Path(image["path"])
            g.verify_build(build, repo)
            receipt = a.read(build / "build.json")
            for path, sha in receipt["external_files"].items():
                include(all_inputs, path, sha)
            for tool in receipt["toolchain"].values():
                include(all_inputs, tool["path"], tool["sha256"])
    roots = runs + list(builds.values()) + [p.resolve() for p in support]
    g.require(not output.exists() and all(not output.is_relative_to(p) for p in roots), "archive overlaps input or exists")
    m.verify_files(all_inputs)
    output.mkdir(parents=True)
    entries, originals = [], {}
    def add(raw, logical, original):
        portable.safe_relative(logical)
        g.require(original not in originals, "duplicate original: " + original)
        stored, encoded, encoding = Path("files") / logical, raw, "identity"
        if len(raw) >= 4096:
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            if len(compressed) + 64 < len(raw):
                stored, encoded, encoding = stored.with_name(stored.name + ".gz"), compressed, "gzip"
        target = output / stored
        g.require(not target.exists(), "duplicate archive logical path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encoded)
        entries.append(dict(original=original, stored=stored.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=digest(raw), stored_bytes=len(encoded), stored_sha256=digest(encoded)))
        originals[original] = logical
    def file(path, logical):
        g.require(path.is_file() and not path.is_symlink(), "missing or symlink evidence: " + str(path))
        add(path.read_bytes(), logical, str(path))
    for group, collection in (("campaigns", runs), ("builds", builds.values())):
        for root in sorted(collection):
            for path in sorted(root.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(root)
                if set(rel.parts) & {"objects", "__pycache__"}:
                    continue
                if "cwd" in rel.parts and not (path.name in m.AUX and path.parent.name == "build"):
                    continue
                file(path, group + "/" + root.name + "/" + rel.as_posix())
    for name in m.META:
        file(Path(cfg["build_record"]) / name, "hardware/" + name)
    for name in m.AUX:
        file(Path(cfg["hardware_source"]) / "build" / name, "hardware/" + name)
    file(Path(cfg["build_driver"]), "hardware/build-driver.py")
    file(Path(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py", "hardware/original-build-driver.py")
    for path in sorted(set(all_inputs) | {str(repo / rel) for rel in EXTRA}):
        p = Path(path)
        if p.is_relative_to(repo) and path not in originals:
            file(p, "tools/" + p.relative_to(repo).as_posix())
    for path in support:
        path = path.resolve()
        g.require(path.is_file(), "support must be an explicit regular file")
        file(path, "support/" + path.name)
    m.verify_files(all_inputs)
    add(json_bytes({p: dict(sha256=sha, logical=originals.get(p)) for p, sha in sorted(all_inputs.items())}),
        "sealed-inputs.json", "generated:sealed-inputs")
    manifest = dict(version=1, contract=c.CONTRACT, qualification_scope=scope, created_utc=a.frozen_f.now(),
                    source_root=str(repo), source_commit_at_export=subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
                    campaigns={p.name: str(p) for p in runs}, builds={k: str(v) for k, v in builds.items()}, files=entries,
                    exclusions=["EMU/normal NEMU/flash binaries", "hardware/dependency/generated RTL trees",
                                "AM libraries/GNU tool binaries", "intermediate objects/incidental simulator output"],
                    scope="exact evidence bytes; external physical inputs represented by sealed hashes")
    raw = json_bytes(manifest)
    (output / "archive-manifest.json").write_bytes(raw)
    (output / "archive-manifest.sha256").write_text(digest(raw) + "  archive-manifest.json\n")
    archive = portable.Archive(output)
    result = dict(status=BYTE_PASS, **archive.bytes_result)
    g.save(output / "archive-check.json", result)
    return result


def times(record):
    start, finish = (datetime.fromisoformat(record[k]) for k in ("started", "finished"))
    g.require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish,
              "invalid execution timestamps")
    return start, finish


def commands(archive, prefix, image, receipt):
    directory = PurePosixPath(image["path"])
    tools = receipt["toolchain"]
    gcc, make, ld = (tools[k]["path"] for k in ("gcc", "make", "ld"))
    g.require(gcc.endswith("gcc") and len(receipt["commands"]) == 5, "R4 build command inventory")
    common = [gcc, "-march=rv64gcv", "-mabi=lp64d", "-mno-relax"]
    expected = [
        ("make-command", [make, "-C", str(directory / "source"), "ARCH=riscv64-xs", "MARCH=rv64gcv",
                          "CROSS_COMPILE=" + gcc[:-3], "T13_DATA=" + str(directory / "data"),
                          "T13_OBJ_ROOT=" + str(directory / "objects"), "BINARY=" + str(directory / "vdot-perf"),
                          "-o", "am", "-o", "klib", "-j1", "image"]),
        ("reference-command", common + ["-c", str(directory / "data/kernels.S"), "-o", str(directory / "kernels-reference.o")]),
        ("public-reference-command", common + ["-c", str(directory / "data/gemv.S"), "-o", str(directory / "gemv-reference.o")]),
        ("api-c-compile", common + ["-ffreestanding", "-O2", "-I" + str(directory / "data"), "-c",
                                    str(directory / "api-c-smoke.c"), "-o", str(directory / "api-c-smoke.o")]),
        ("api-c-link", [ld, "-r", "--no-relax", str(directory / "api-c-smoke.o"),
                        str(directory / "gemv-reference.o"), "-o", str(directory / "api-c-linked.o")]),
    ]
    previous = None
    for i, (label, argv) in enumerate(expected):
        p = prefix + "/" + label
        command = archive.json(p + "/command.json")
        g.require(command == receipt["commands"][i] and command["command"] == argv and
                  command["cwd"] == archive.manifest["source_root"] and command.get("process_started") is True and
                  type(command.get("pid")) is int and command["pid"] > 0 and
                  type(command.get("exit_code")) is int and command["exit_code"] == 0 and not command.get("timed_out"),
                  "build command receipt differs")
        g.require(command["raw_sha256"] == {n: digest(archive.raw(p + "/" + n)) for n in ("stdout.log", "stderr.log")},
                  "build command raw log differs")
        start, finish = times(command)
        g.require(previous is None or previous <= start, "overlapping commands within one ELF build")
        previous = finish


def fixture_identity(archive, prefix, fixture, cfg, m):
    f = a.frozen_f
    g.require(fixture["source_sha256"] == m.NEGATIVE_SHA and fixture["normal_reference_sha256"] == f.REFERENCE and
              fixture["historical_negative_hash_claim"] is False and
              digest(archive.raw(prefix + "/negative-fixture.c")) == m.NEGATIVE_SHA and
              digest(archive.raw(prefix + "/negative-reference.so")) == fixture["negative_sha256"], "negative fixture identity")
    compiler, directory = fixture["command"][0], PurePosixPath(fixture["binary"]).parent
    argv = [compiler, "-shared", "-fPIC", "-O2", '-DREF_SO="' + cfg["reference"] + '"',
            str(directory / "negative-fixture.c"), "-Wl,--no-as-needed", cfg["reference"], "-ldl", "-o", fixture["binary"]]
    g.require(fixture["command"] == argv, "negative fixture compile command")
    for step in ("compiler", "compile", "linkage"):
        p = prefix + "/" + step
        r = archive.json(p + "/command.json")
        expected = [compiler, "--version"] if step == "compiler" else argv if step == "compile" else [r["command"][0], "-d", fixture["binary"]]
        g.require(r.get("process_started") is True and r.get("exit_code") == 0 and not r.get("timed_out") and
                  r["command"] == expected and r["raw_sha256"] ==
                  {n: digest(archive.raw(p + "/" + n)) for n in ("stdout.log", "stderr.log")}, "fixture build receipt")
    g.require("Shared library: [" + cfg["reference"] + "]" in archive.raw(prefix + "/linkage/stdout.log").decode(),
              "negative fixture lacks direct normal-reference dependency")


def originals(archive, cfg, m, sealed):
    meta, seen = archive.manifest, set()
    hardware = {n: str(PurePosixPath(cfg["build_record"]) / n) for n in m.META}
    hardware.update({n: str(PurePosixPath(cfg["hardware_source"]) / "build" / n) for n in m.AUX})
    hardware.update({"build-driver.py": cfg["build_driver"], "original-build-driver.py":
                     str(PurePosixPath(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py")})
    for logical, record in archive.records.items():
        original, parts = record.get("original"), PurePosixPath(logical).parts
        g.require(isinstance(original, str) and original not in seen, "duplicate archive original")
        seen.add(original)
        if parts[0] in ("campaigns", "builds"):
            g.require(len(parts) > 2 and parts[1] in meta[parts[0]], "unknown archive collection")
            expected = str(PurePosixPath(meta[parts[0]][parts[1]]) / PurePosixPath(*parts[2:]))
        elif parts[0] == "tools":
            expected = str(PurePosixPath(meta["source_root"]) / PurePosixPath(*parts[1:]))
        elif parts[0] == "hardware":
            expected = hardware.get("/".join(parts[1:]))
        elif logical == "sealed-inputs.json":
            expected = "generated:sealed-inputs"
        elif parts[0] == "support":
            g.require(len(parts) == 2 and PurePosixPath(original).is_absolute() and PurePosixPath(original).name == parts[1],
                      "support path identity")
            expected = original
        else:
            raise ValueError("unknown archive namespace: " + logical)
        g.require(expected == original, "archive path identity differs: " + logical)
    for path, entry in sealed.items():
        if entry["logical"] is not None:
            g.require(entry["logical"] in archive.records and archive.records[entry["logical"]]["original"] == path and
                      digest(archive.raw(entry["logical"])) == entry["sha256"], "sealed logical/raw association")


def runtime_inputs(archive, prefix, repo, cfg, images, m):
    recorded = PurePosixPath(archive.manifest["source_root"])
    expected = {str(recorded / Path(p).relative_to(repo).as_posix()): sha for p, sha in m.checker_files(repo).items()}
    for rel in g.SOURCES | {str(g.S1 / "gate.py"), str(g.REL / "machine_model.py")}:
        expected[str(recorded / rel)] = g.sha(repo / rel)
    expected.update({str(PurePosixPath(cfg["build_record"]) / n): sha for n, sha in m.META.items()})
    expected.update({str(PurePosixPath(cfg["hardware_source"]) / "build" / n): sha for n, sha in m.AUX.items()})
    pins = archive.json("hardware/hardware-inputs.json")
    expected.update({str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): m.EMU,
                     cfg["reference"]: a.frozen_f.REFERENCE, cfg["flash"]: a.frozen_f.FLASH,
                     cfg["build_driver"]: pins["build_script_sha256"],
                     str(PurePosixPath(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py"):
                         "8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0"})
    for root in cfg["canonical_builds"]:
        for name in ("state.json", "images.json", "pairs.json"):
            expected[str(PurePosixPath(root) / name)] = digest(archive.raw("builds/" + PurePosixPath(root).name + "/" + name))
    for image in images:
        root = PurePosixPath(image["path"])
        for name in ("build.json", "data/manifest.json"):
            expected[str(root / name)] = digest(archive.raw("builds/" + root.parent.parent.name + "/images/" + image["name"] + "/" + name))
    g.require(archive.json(prefix + "/runtime-inputs.json") == expected, "runtime input inventory differs")
    return expected


def offline_pairs(images, builds, sealed):
    identity, layouts, indexed = None, [], {i["name"]: i for i in images}
    g.require(len(indexed) == len(images), "duplicate image")
    for image in images:
        receipt = a.read(builds[image["name"]] / "build.json")
        current = {k: receipt[k] for k in IDENTITY}
        identity = current if identity is None else identity
        g.require(current == identity and receipt["am_revision"] == a.frozen_f.AM_COMMIT and
                  set(receipt["toolchain"]) == {"gcc", "ld", "ar", "objcopy", "objdump", "readelf", "make"}, "cross-image build identity")
        for path, sha in receipt["external_files"].items():
            g.require(sealed.get(path, {}).get("sha256") == sha, "unsealed AM library")
        for tool in receipt["toolchain"].values():
            g.require(sealed.get(tool["path"], {}).get("sha256") == tool["sha256"], "unsealed GNU tool")
        if image["variant"] == "s0":
            other = a.name(dict(image, variant="s1"))
            g.require(other in indexed, "missing paired image")
            layouts.append(dict(s0=image["name"], s1=other, **g.paired_layout(builds[image["name"]], builds[other])))
    g.require(len(layouts) * 2 == len(images), "incomplete image pairs")
    return dict(status="R4_COMPLETE_LAYOUT_AND_INPUTS_PASS", pairs=len(layouts), build_identity=identity,
                layouts=layouts, historical_samples_reused=False)


def audit(repo, archive_path):
    g.require(os.name == "posix", "exact frozen regeneration requires Linux/WSL")
    repo = repo.resolve()
    portable, m, e = modules(repo)
    archive = portable.Archive(archive_path)
    meta = archive.manifest
    g.require(meta.get("contract") == c.CONTRACT, "wrong R4 archive contract")
    expected = {a.name(i): i for i in cohort(meta["qualification_scope"])}
    g.require(meta["campaigns"] and meta["builds"] and all(PurePosixPath(p).is_absolute() and PurePosixPath(p).name == n
              for values in (meta["campaigns"], meta["builds"]) for n, p in values.items()), "collection identity")
    sealed = archive.json("sealed-inputs.json")
    configurations = {n: archive.json("campaigns/" + n + "/configuration.json") for n in meta["campaigns"]}
    base_configs = [{k: v for k, v in cfg.items() if k != "canonical_builds"} for cfg in configurations.values()]
    cfg = base_configs[0]
    g.require(all(v == cfg for v in base_configs), "mixed runtime configurations")
    g.require(set(meta["builds"].values()) == {p for v in configurations.values() for p in v["canonical_builds"]},
              "unreferenced or missing canonical build")
    originals(archive, cfg, m, sealed)
    for relative in EXTRA:
        logical = "tools/" + relative
        g.require(logical in archive.records and digest(archive.raw(logical)) == g.sha(repo / relative),
                  "missing or changed required evidence tool/contract: " + relative)
    for name, pin in m.META.items():
        g.require(digest(archive.raw("hardware/" + name)) == pin, "hardware metadata identity")
    pins = archive.json("hardware/hardware-inputs.json")
    g.require(pins["source_commit"] == m.SOURCE and pins["emu_sha256"] == m.EMU and
              len(pins["files"]) == 429 and len(pins["dependency_files"]) == 21236 and
              len(archive.json("hardware/generated-artifacts.json")) == 1672 and
              digest(archive.raw("hardware/build-driver.py")) == pins["build_script_sha256"], "hardware provenance metadata")
    for logical in archive.records:
        if logical.startswith("tools/team/") and logical.endswith(".py"):
            g.require(g.sha(repo / Path(logical).relative_to("tools")) == digest(archive.raw(logical)),
                      "offline tool differs from sealed source: " + logical)
    images, group_images = [], {}
    for name, root in meta["builds"].items():
        prefix = "builds/" + name
        state = archive.json(prefix + "/state.json")
        selected = archive.json(prefix + "/images.json")["images"]
        g.require(state["status"] == "R4_CANONICAL_CALLABLE_ELFS_STATIC_PASS_RUNTIME_NOT_RUN" and
                  state["new_emu_runs"] == 0 and state["images_completed"] == len(selected), "canonical build incomplete")
        for image in selected:
            g.require(image["name"] in expected and all(image[k] == v for k, v in expected[image["name"]].items()) and
                      image["path"] == str(PurePosixPath(root) / "images" / image["name"]), "canonical image identity")
        group_images[name] = selected
        images.extend(selected)
    g.require(len(images) == len(expected) and {i["name"] for i in images} == set(expected), "R4 cohort image inventory")
    records, rejected, all_inputs, diagnostics = [], [], {}, []
    profile = None
    with tempfile.TemporaryDirectory(prefix="r4-entry-offline-") as temp:
        extracted, builds = Path(temp), {}
        for logical in archive.records:
            if logical.startswith(("builds/", "campaigns/")):
                target = extracted / logical
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.raw(logical))
        for image in images:
            prefix = "builds/" + PurePosixPath(image["path"]).parent.parent.name + "/images/" + image["name"]
            build = extracted / prefix
            manifest, receipt = a.read(build / "data/manifest.json"), a.read(build / "build.json")
            m.validate_selection(image, manifest, receipt)
            commands(archive, prefix, image, receipt)
            g.require(g.verify_build(build, repo) == a.read(build / "elf-validation.json"), "cached ELF validation differs")
            g.require(g.sha(build / "vdot-perf.bin") == image["image_sha256"], "canonical BIN identity")
            builds[image["name"]] = build
        pairs = offline_pairs(images, builds, sealed)
        identity = pairs["build_identity"]
        g.require(set(identity["external_files"]) == {str(PurePosixPath(cfg["am_home"]) / n) for n in
                  ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")}, "AM library path inventory")
        for name, selected in group_images.items():
            g.require(archive.json("builds/" + name + "/pairs.json") == offline_pairs(selected, builds, sealed),
                      "cached build pair validation differs")
        suite = g.load("r4_offline_runtime_banner", repo / "team/optimizations/o2/fullcore/run_suite.py")
        for campaign, root in meta["campaigns"].items():
            prefix = "campaigns/" + campaign
            config = configurations[campaign]
            selected = [i for b in config["canonical_builds"] for i in group_images[PurePosixPath(b).name]]
            indexed = {i["name"]: i for i in selected}
            g.require(len(indexed) == len(selected), "duplicate campaign image")
            common = runtime_inputs(archive, prefix, repo, config, selected, m)
            for path, sha in common.items():
                include(all_inputs, path, sha)
            g.require(archive.json(prefix + "/pair-layout.json") == offline_pairs(selected, builds, sealed), "cached runtime pairs differ")
            current_profile = archive.json(prefix + "/hardware-profile.json")
            profile = current_profile if profile is None else profile
            g.require(profile == current_profile and profile.get("software_contract") == c.CONTRACT, "campaign hardware profiles differ")
            known_profile = dict(contract=a.frozen_m.CONTRACT, source_commit=m.SOURCE, emu_sha256=m.EMU,
                                 pins_sha256=m.META["hardware-inputs.json"], source_files=429,
                                 dependency_files=21236, generated_files=1672,
                                 build_driver_sha256=pins["build_script_sha256"],
                                 historical_b0_h1_acceptance=False, whole_suite_acceptance=False)
            g.require(all(profile.get(k) == v for k, v in known_profile.items()), "cached hardware facts differ")
            state, cached = archive.json(prefix + "/state.json"), archive.json(prefix + "/results.json")
            g.require(isinstance(state.get("operation_id"), str) and state["operation_id"].strip(), "missing operation identity")
            labels = {p[len(prefix + "/runs/"):].split("/")[0] for p in archive.records
                      if p.startswith(prefix + "/runs/") and p.endswith("/result.json") and
                      len(p[len(prefix + "/runs/"):].split("/")) == 2}
            local, negative, fixture, used = [], None, None, set()
            if prefix + "/negative-fixture/fixture.json" in archive.records:
                fixture = archive.json(prefix + "/negative-fixture/fixture.json")
                fixture_identity(archive, prefix + "/negative-fixture", fixture, cfg, m)
            for label in sorted(labels):
                run = extracted / prefix / "runs" / label
                record = a.read(run / "result.json")
                image = indexed.get(record["name"])
                g.require(image is not None and type(record["replay"]) is int and record["replay"] in (0, 1) and
                          type(record["negative"]) is bool, "unexpected run label/type")
                replay, is_negative = record["replay"], record["negative"]
                key = (record["name"], replay, is_negative)
                g.require(key not in used, "duplicate campaign run")
                used.add(key)
                if is_negative:
                    wanted = "negative-s1-8x32"
                    g.require(negative is None and fixture is not None and record["name"] ==
                              a.name(dict(suite="performance", variant="s1", dataset=0, shard=3)) and replay == 0,
                              "unexpected negative target")
                elif label == "recovery-s1-8x32":
                    wanted = label
                    g.require(record["name"] == a.name(dict(suite="performance", variant="s1", dataset=0, shard=3)) and replay == 0,
                              "unexpected recovery target")
                else:
                    wanted = ("replay-" if replay else "formal-") + record["name"]
                g.require(label == wanted and record["cwd"] == str(PurePosixPath(root) / "runs" / label / "cwd"), "run cwd/label")
                e.run_identity(record, image, replay, is_negative, cfg, fixture, common, sealed)
                g.require(record["raw_sha256"] == {n: g.sha(run / n) for n in ("stdout.log", "stderr.log")}, "raw run transcript identity")
                suite.validate_runtime((run / "stdout.log").read_text() + (run / "stderr.log").read_text(), record["reference"])
                for path, sha in record["files"].items():
                    include(all_inputs, path, sha)
                if is_negative:
                    old_details, old_trace = a.read(run / "negative.json"), a.read(run / "observation.json")
                    details = m.negative_check(repo, builds[image["name"]], run, record)
                    g.require(details == old_details == record["negative_details"] and a.read(run / "observation.json") == old_trace,
                              "negative raw replay differs")
                    negative = record
                else:
                    g.require(not replay or image["dataset"] == 0, "unexpected replay dataset")
                    checked = e.normal_audit(repo, builds[image["name"]], run, record, {p: v["sha256"] for p, v in sealed.items()})
                    diagnostics.extend(checked["fu_windows"])
                    local.append(record)
            normals = {r["name"] for r in local if r["replay"] == 0}
            replays = {r["name"] for r in local if r["replay"] == 1}
            g.require(normals == set(indexed), "missing normal image execution")
            replay_complete = replays == {i["name"] for i in selected if i["dataset"] == 0} and \
                {r["shard"] for r in local if r["replay"]} == {i["shard"] for i in selected}
            qualification = dict(real_negative_and_same_image_recovery=negative is not None,
                                 all_shape_replay_complete=replay_complete, normal_image_count=len(normals),
                                 replay_image_count=len(replays), new_execution_path=True, whole_suite_acceptance=False,
                                 historical_performance_reused=False)
            verdict = "R4_CALLABLE_ENTRY_SCREEN_PASS" if negative and replay_complete else "R4_CALLABLE_ENTRY_PARTIAL_PASS"
            stats = a.summarize(local)
            g.require(state["status"] == cached["status"] == verdict and state["qualification"] == cached["qualification"] == qualification and
                      state["normal_runs"] == len(local) and state["negative_runs"] == int(negative is not None) and
                      state["new_emu_runs"] == len(local) + int(negative is not None) and
                      state["measured_windows"] == stats["measured_windows"] and state["active_pid"] is None and state["active_result"] is None and
                      state["hardware_changed"] is False and state["historical_b0_h1_acceptance"] is False and state["whole_suite_acceptance"] is False,
                      "campaign state/qualification differs")
            g.require(state["contract"] == cached["contract"] == c.CONTRACT and cached["negative"] == negative and
                      len(cached["runs"]) == len(local) and
                      {(r["name"], r["replay"]): r for r in cached["runs"]} == {(r["name"], r["replay"]): r for r in local}, "summary run receipts differ")
            for key in ("rows", "measured_windows"):
                g.require(cached[key] == stats[key], "cached statistics differ: " + key)
            sample_key = lambda s: tuple(s[k] for k in ("variant", "shard", "dataset", "software", "method", "repeat"))
            g.require(sorted(cached["samples"], key=sample_key) == sorted(stats["samples"], key=sample_key), "cached samples differ")
            chronological = sorted(local + ([negative] if negative else []), key=lambda r: times(r)[0])
            expected_order = ["negative-s1-8x32", "recovery-s1-8x32"] if negative else []
            for image in sorted(selected, key=lambda i: (i["shard"], i["dataset"],
                    i["variant"] if (i["shard"] + i["dataset"]) % 2 == 0 else i["variant"] == "s0")):
                if not (negative and image["name"] == negative["name"]):
                    expected_order.append("formal-" + image["name"])
            expected_order.extend("replay-" + i["name"] for i in selected if i["name"] in replays)
            g.require([PurePosixPath(r["cwd"]).parent.name for r in chronological] == expected_order and
                      cached["runs"] == [r for r in chronological if not r["negative"]], "execution order differs from paired plan")
            start, finish = times(state)
            g.require(chronological and start <= times(chronological[0])[0] and times(chronological[-1])[1] <= finish,
                      "campaign does not enclose execution times")
            if negative:
                recovery = next((r for r in local if PurePosixPath(r["cwd"]).parent.name == "recovery-s1-8x32"), None)
                g.require(recovery is not None and chronological[:2] == [negative, recovery], "negative must immediately precede recovery")
                e.audit_recovery(negative, recovery)
                rejected.append(negative)
            else:
                g.require(fixture is None and all(PurePosixPath(r["cwd"]).parent.name != "recovery-s1-8x32" for r in local),
                          "orphan fixture/recovery")
            records.extend(local)
        formal = [r for r in records if not r["replay"]]
        replayed = [r for r in records if r["replay"]]
        wanted_replays = {i["name"] for i in images if i["dataset"] == 0}
        g.require(len(rejected) == 1 and len(formal) == len(expected) and {r["name"] for r in formal} == set(expected) and
                  len(replayed) == len(wanted_replays) and {r["name"] for r in replayed} == wanted_replays, "aggregate qualification incomplete")
        for record in replayed:
            previous = next(r for r in formal if r["name"] == record["name"])
            g.require(times(previous)[1] <= times(record)[0] and m.signature(previous) == m.signature(record),
                      "all-window replay time/signature differs")
        chronological = sorted(records + rejected, key=lambda r: times(r)[0])
        for before, after in zip(chronological, chronological[1:]):
            g.require(times(before)[1] <= times(after)[0], "concurrent performance executions")
        g.require(chronological[0] == rejected[0], "aggregate first execution was not the negative gate")
    for path, sha in identity["external_files"].items():
        include(all_inputs, path, sha)
    for tool in identity["toolchain"].values():
        include(all_inputs, tool["path"], tool["sha256"])
    logicals = {r["original"]: p for p, r in archive.records.items()}
    g.require(sealed == {p: dict(sha256=sha, logical=logicals.get(p)) for p, sha in all_inputs.items()}, "sealed input closure differs")
    external = {str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): m.EMU,
                cfg["reference"]: a.frozen_f.REFERENCE, cfg["flash"]: a.frozen_f.FLASH, **identity["external_files"]}
    external.update({v["path"]: v["sha256"] for v in identity["toolchain"].values()})
    for path, entry in sealed.items():
        if entry["logical"] is None:
            g.require(external.get(path) == entry["sha256"], "unarchived non-external input")
    stats = a.summarize(records)
    return dict(status="R4_ENTRY_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS", contract=c.CONTRACT,
                qualification_scope=meta["qualification_scope"], archive=archive.bytes_result,
                formal_normal_images=len(formal), replay_images=len(replayed), expected_negative_runs=1,
                original_emu_processes=len(records) + 1, formal_windows=stats["measured_windows"],
                all_window_replay_comparisons=len(replayed) * 24, new_emu_runs=0, new_nemu_runs=0,
                physical_hardware_and_reference_inputs_revalidated=False, physical_am_and_toolchain_inputs_revalidated=False,
                historical_b0_h1_acceptance=False, whole_suite_acceptance=False,
                rows=stats["rows"], fu_window_diagnostics=diagnostics,
                scope="sealed ELF/compiled model/full128/CSR/exact call-retirement/counters/O2/negative/recovery/replay; fixed GEMV invocation only")


def byte_check(repo, archive_path):
    portable, _, _ = modules(repo)
    archive = portable.Archive(archive_path)
    g.require(archive.manifest.get("contract") == c.CONTRACT, "wrong R4 archive contract")
    cohort(archive.manifest["qualification_scope"])
    result = dict(status=BYTE_PASS, **archive.bytes_result)
    g.require(a.read(archive_path / "archive-check.json") == result, "cached archive byte check differs")
    return result


def index_check(repo, archive_path):
    byte_check(repo, archive_path)
    return index_bytes(repo, archive_path)


def index_bytes(repo, archive_path):
    """Exact staged bytes for an already byte-validated portable archive."""
    portable, _, _ = modules(repo)
    archive = portable.Archive(archive_path)
    helper = g.load("r4_index_helper", repo / g.REL / "merged_index.py")
    g.require(archive_path.is_relative_to(repo), "archive must be inside selected repository")
    relative = archive_path.relative_to(repo).as_posix()
    expected = {relative + "/" + r["stored"] for r in archive.manifest["files"]}
    expected.update(relative + "/" + n for n in ("archive-manifest.json", "archive-manifest.sha256", "archive-check.json"))
    actual = {p.relative_to(repo).as_posix() for p in archive_path.rglob("*") if p.is_file()}
    g.require(actual == expected, "archive disk inventory differs")
    entries = helper.index_entries(helper.git(repo, "ls-files", "--stage", "-z", "--", relative))
    g.require(set(entries) == expected, "archive Git index inventory incomplete")
    names = sorted(expected)
    stream = io.BytesIO(helper.git(repo, "cat-file", "--batch", data="".join(entries[n]["oid"] + "\n" for n in names).encode()))
    for name in names:
        header = stream.readline().split()
        g.require(len(header) == 3 and header[0].decode() == entries[name]["oid"] and header[1] == b"blob", "missing Git blob")
        raw = stream.read(int(header[2]))
        g.require(stream.read(1) == b"\n" and raw == (repo / name).read_bytes(), "staged evidence bytes differ")
    g.require(not stream.read(), "extra Git blob output")
    return dict(status="R4_ENTRY_ARCHIVE_COMPLETE_GIT_INDEX_PASS", archive=archive.bytes_result,
                archive_files_in_git_index=len(names), missing=0, extra=0,
                git_file_modes=dict(Counter(v["mode"] for v in entries.values())),
                new_emu_runs=0, architecture_replayed=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--action", choices=("pack", "audit", "bytes", "index"), required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--run", type=Path, action="append", default=[])
    p.add_argument("--scope", choices=("probe", "matrix"))
    p.add_argument("--support", type=Path, action="append", default=[])
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    repo, archive = args.repo.resolve(), args.archive.resolve()
    if args.action == "pack":
        g.require(args.run and args.scope, "pack needs explicit run collection and scope")
        result = pack(repo, args.run, archive, args.scope, args.support)
    else:
        g.require(args.output is not None and not args.output.exists() and not args.output.resolve().is_relative_to(archive),
                  "audit output must be new and outside archive")
        result = {"audit": audit, "bytes": byte_check, "index": index_check}[args.action](repo, archive)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        g.save(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "fu_window_diagnostics")}, ensure_ascii=False, indent=2))
