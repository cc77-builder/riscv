"""Seal firstdot campaigns and recompute their conclusions from original bytes.

The portable archive omits physical hardware/toolchain trees. Offline auditing
replays the unchanged architectural and O2 checkers; it launches no simulator.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import types

import firstdot_candidate as c
import firstdot_gate as g
import firstdot_experiment as a

PORTABLE = Path("team/optimizations/o2/fullcore/portable.py")
HELPERS = {
    str(PORTABLE): "7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b",
    str(g.REL / "merged_evidence.py"): "ae648951a8258ea20d239e977ea616f1c03ef00e4e83e0d2f7878354434026be",
    str(g.ENTRY / "entry_evidence.py"): "039f81a2c7e216514c94939b8807647787c4b046413a48fb4c7e33293c027db3",
}
EXTRA = set(HELPERS) | {str(g.S1 / n) for n in
    ("firstdot_evidence.py", "test_firstdot.py", "test_firstdot_evidence.py", "FIRSTDOT_CONTRACT.md")}
BYTE_PASS = "FIRSTDOT_ARCHIVE_BYTES_PASS"
AUDIT_PASS = "FIRSTDOT_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def modules(repo, identity):
    g.bind(repo)
    a.t17.validate_identity(repo, identity)
    for rel, expected in HELPERS.items():
        g.require(g.sha(repo / rel) == expected, "frozen evidence helper changed: " + rel)
    portable = g.load("firstdot_portable", repo / PORTABLE)
    f, m = a.runtime(repo, identity)
    m.SOURCE, m.EMU = identity["source_commit"], identity["hardware_profile"]["emu_sha256"]
    m.META = dict(identity["metadata_sha256"])
    old = g.load("firstdot_entry_evidence_helpers", repo / g.ENTRY / "entry_evidence.py")
    old.g, old.c, old.a = g, c, types.SimpleNamespace(read=a.read, frozen_f=f)
    common = g.load("firstdot_common_evidence", repo / g.REL / "merged_evidence.py")
    proxy = types.SimpleNamespace(**vars(g))
    def load(label, path):
        if Path(path).resolve() != (repo / g.O3 / "check.py").resolve():
            return g.load(label, path)
        check = g.counter_adapter(repo)
        verify = check.verify
        def invoke(*args, **kwargs):
            result = verify(*args, **kwargs)
            result["scope"] = a.SCOPE
            return result
        check.verify = invoke
        return check
    proxy.load = load
    common.g, common.m, common.f = proxy, m, f
    return portable, f, m, old, common


def include(values, path, sha):
    g.require(path not in values or values[path] == sha, "conflicting evidence identity: " + path)
    values[path] = sha


def cohort(scope):
    g.require(scope in ("probe", "matrix"), "firstdot archive scope")
    return a.inventory([3], [0]) if scope == "probe" else a.inventory([1, 3, 5, 7], [0, 1, 2])


def pack(repo, identity_path, runs, output, scope, support):
    g.require(os.name == "posix", "physical sealing requires native Linux inputs")
    identity = a.parent_identity(repo, identity_path)
    portable, f, m, _, _ = modules(repo, identity)
    cohort(scope)
    g.require(runs and len(set(runs)) == len(runs) and len({p.name for p in runs}) == len(runs), "duplicate campaigns")
    inputs, builds, cfg = {}, {}, identity["configuration"]
    for root in runs:
        state = a.read(root / "state.json")
        g.require(state["status"] in (a.RUN_PASS, "FIRSTDOT_PARTIAL_PASS") and state["active_pid"] is None and
                  state["active_result"] is None and state.get("finished"), "incomplete campaign")
        current = a.read(root / "configuration.json")
        g.require({k: v for k, v in current.items() if k != "canonical_builds"} == cfg, "mixed configurations")
        for name in current["canonical_builds"]:
            path = Path(name)
            g.require(path.is_absolute() and (path.name not in builds or builds[path.name] == path), "ambiguous build")
            builds[path.name] = path
        for path, sha in a.read(root / "runtime-inputs.json").items():
            include(inputs, path, sha)
        for path in (root / "runs").glob("*/result.json"):
            for name, sha in a.read(path)["files"].items():
                include(inputs, name, sha)
    a.outside_inputs(output, [repo, identity_path.parent, *runs, *builds.values(),
                             cfg["hardware_source"], cfg["build_record"], cfg["am_home"]])
    g.require(not output.exists(), "archive output exists")
    for root in builds.values():
        images = a.read(root / "images.json")["images"]
        a.validate_baselines(repo, root, images)
        for image in images:
            a.validate_image(image, root)
            build = Path(image["path"])
            g.verify_build(build, repo)
            receipt = a.read(build / "build.json")
            for path, sha in receipt["external_files"].items():
                include(inputs, path, sha)
            for tool in receipt["toolchain"].values():
                include(inputs, tool["path"], tool["sha256"])
    m.verify_files(inputs)
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
        g.require(not target.exists(), "duplicate logical evidence")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encoded)
        entries.append(dict(original=original, stored=stored.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=digest(raw), stored_bytes=len(encoded), stored_sha256=digest(encoded)))
        originals[original] = logical
    def file(path, logical):
        g.require(path.is_file() and not path.is_symlink(), "missing or linked evidence: " + str(path))
        add(path.read_bytes(), logical, str(path))
    for group, roots in (("campaigns", runs), ("builds", builds.values())):
        for root in sorted(roots):
            for path in sorted(root.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(root)
                if set(relative.parts) & {"objects", "__pycache__"}:
                    continue
                if "cwd" in relative.parts and not (path.parent.name == "build" and path.name in m.AUX):
                    continue
                file(path, group + "/" + root.name + "/" + relative.as_posix())
    for name in m.META:
        file(Path(cfg["build_record"]) / name, "hardware/" + name)
    for name in m.AUX:
        file(Path(cfg["hardware_source"]) / "build" / name, "hardware/" + name)
    file(Path(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py", "hardware/original-build-driver.py")
    for path in sorted(set(inputs) | {str(repo / n) for n in EXTRA}):
        p = Path(path)
        if p.is_relative_to(repo) and path not in originals:
            file(p, "tools/" + p.relative_to(repo).as_posix())
    file(identity_path, "parent-identity.json")
    for path in support:
        g.require(path.is_file() and str(path) not in originals, "support must be a distinct explicit file")
        file(path, "support/" + path.name)
    m.verify_files(inputs)
    add(json_bytes({p: dict(sha256=sha, logical=originals.get(p)) for p, sha in sorted(inputs.items())}),
        "sealed-inputs.json", "generated:sealed-inputs")
    manifest = dict(version=1, contract=c.CONTRACT, qualification_scope=scope, created_utc=f.now(),
        source_root=str(repo), source_commit_at_export=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        parent_identity_path=str(identity_path), campaigns={p.name: str(p) for p in runs},
        builds={n: str(p) for n, p in builds.items()}, files=entries,
        exclusions=["EMU/normal NEMU/flash binaries", "hardware/dependency/generated RTL trees", "AM/GNU binaries",
                    "intermediate objects and incidental simulator output"],
        scope="exact raw evidence; physical external inputs represented by sealed hashes")
    raw = json_bytes(manifest)
    (output / "archive-manifest.json").write_bytes(raw)
    (output / "archive-manifest.sha256").write_text(digest(raw) + "  archive-manifest.json\n")
    result = dict(status=BYTE_PASS, **portable.Archive(output).bytes_result)
    g.save(output / "archive-check.json", result)
    return result


def original_paths(archive, cfg, sealed, m):
    meta, seen = archive.manifest, set()
    hardware = {n: str(PurePosixPath(cfg["build_record"]) / n) for n in m.META}
    hardware.update({n: str(PurePosixPath(cfg["hardware_source"]) / "build" / n) for n in m.AUX})
    hardware["original-build-driver.py"] = str(PurePosixPath(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py")
    for logical, row in archive.records.items():
        original, parts = row["original"], PurePosixPath(logical).parts
        g.require(original not in seen, "duplicate archived original")
        seen.add(original)
        if parts[0] in ("campaigns", "builds"):
            g.require(len(parts) > 2 and parts[1] in meta[parts[0]], "unknown archive collection")
            expected = str(PurePosixPath(meta[parts[0]][parts[1]]) / PurePosixPath(*parts[2:]))
        elif parts[0] == "tools":
            expected = str(PurePosixPath(meta["source_root"]) / PurePosixPath(*parts[1:]))
        elif parts[0] == "hardware":
            expected = hardware.get("/".join(parts[1:]))
        elif logical == "parent-identity.json":
            expected = meta["parent_identity_path"]
        elif logical == "sealed-inputs.json":
            expected = "generated:sealed-inputs"
        elif parts[0] == "support":
            g.require(len(parts) == 2 and PurePosixPath(original).is_absolute() and PurePosixPath(original).name == parts[1], "support path")
            expected = original
        else:
            raise ValueError("unknown archive namespace")
        g.require(expected == original, "archive original/logical association differs")
    for path, row in sealed.items():
        if row["logical"] is not None:
            logical = row["logical"]
            g.require(archive.records[logical]["original"] == path and digest(archive.raw(logical)) == row["sha256"], "sealed association")


def hardware_inputs(cfg, identity):
    root, record = PurePosixPath(cfg["hardware_source"]), PurePosixPath(cfg["build_record"])
    result = {str(record / n): sha for n, sha in identity["metadata_sha256"].items()}
    result.update({str(root / "build" / n): sha for n, sha in a.t17.p.AUX.items()})
    result.update({str(root / "build/emu"): identity["hardware_profile"]["emu_sha256"],
                   cfg["reference"]: identity["reference_sha256"], cfg["flash"]: identity["flash_sha256"],
                   str(root / "team/optimizations/o2/fullcore/build_fullcore.py"): a.t17.p.HELPER,
                   cfg["build_driver"]: a.t17.p.BUILDER})
    return result


def expected_inputs(repo, archive, identity, cfg, images, m):
    result = hardware_inputs(cfg, identity)
    original = PurePosixPath(archive.manifest["source_root"])
    result.update({str(original / Path(p).relative_to(repo).as_posix()): sha for p, sha in m.checker_files(repo).items()})
    for rel in g.SOURCES | set(g.FROZEN) | {str(g.S1 / "gate.py"), str(g.REL / "machine_model.py"),
                                           str(a.REPRO / "clean_entry.py"), str(a.REPRO / "clean_profile.py")}:
        result[str(original / rel)] = g.sha(repo / rel)
    result[archive.manifest["parent_identity_path"]] = a.PARENT_IDENTITY_SHA
    result[str(original / a.BASELINE_MANIFEST)] = a.BASELINE_MANIFEST_SHA
    for path in cfg["canonical_builds"]:
        for name in ("state.json", "images.json", "pairs.json", "baseline-identity.json"):
            result[str(PurePosixPath(path) / name)] = digest(archive.raw("builds/" + PurePosixPath(path).name + "/" + name))
    for image in images:
        root = PurePosixPath(image["path"])
        prefix = "builds/" + root.parent.parent.name + "/images/" + image["name"]
        for name in ("build.json", "data/manifest.json"):
            result[str(root / name)] = digest(archive.raw(prefix + "/" + name))
    return result


def audit(repo, archive_path):
    g.require(os.name == "posix", "exact snapshot regeneration requires Linux/WSL")
    g.require(g.sha(repo / PORTABLE) == HELPERS[str(PORTABLE)], "portable checker drift")
    archive = g.load("firstdot_open_archive", repo / PORTABLE).Archive(archive_path)
    meta = archive.manifest
    g.require(meta["contract"] == c.CONTRACT and digest(archive.raw("parent-identity.json")) == a.PARENT_IDENTITY_SHA,
              "archive contract/parent differs")
    identity = archive.json("parent-identity.json")
    _, f, m, old, common = modules(repo, identity)
    expected = {a.name(i): i for i in cohort(meta["qualification_scope"])}
    g.require(meta["campaigns"] and meta["builds"] and all(PurePosixPath(p).is_absolute() and PurePosixPath(p).name == n
              for values in (meta["campaigns"], meta["builds"]) for n, p in values.items()), "collection paths")
    sealed, cfg = archive.json("sealed-inputs.json"), identity["configuration"]
    original_paths(archive, cfg, sealed, m)
    for rel in EXTRA:
        g.require(digest(archive.raw("tools/" + rel)) == g.sha(repo / rel), "evidence tool drift: " + rel)
    for logical in archive.records:
        if logical.startswith("tools/"):
            g.require(digest(archive.raw(logical)) == g.sha(repo / Path(logical).relative_to("tools")), "sealed source drift")
    for name, sha in identity["metadata_sha256"].items():
        g.require(digest(archive.raw("hardware/" + name)) == sha, "sealed T17 metadata differs")
    hw = lambda n: archive.json("hardware/" + n)
    a.t17.p.validate_metadata(hw("hardware-inputs.json"), hw("build-state.json"), hw("hardware-inputs-before.json"),
        hw("baseline-hardware-inputs.json"), hw("generated-artifacts.json"),
        identity["metadata_sha256"]["executed-builder.py"], identity["metadata_sha256"]["baseline-hardware-inputs.json"])
    configurations = {name: archive.json("campaigns/" + name + "/configuration.json") for name in meta["campaigns"]}
    g.require(all({k: v for k, v in current.items() if k != "canonical_builds"} == cfg for current in configurations.values()), "configuration drift")
    g.require(set(meta["builds"].values()) == {p for current in configurations.values() for p in current["canonical_builds"]}, "build closure")
    images, grouped = [], {}
    for name, root in meta["builds"].items():
        state = archive.json("builds/" + name + "/state.json")
        selected = archive.json("builds/" + name + "/images.json")["images"]
        g.require(state["contract"] == c.CONTRACT and state["status"] == a.BUILD_PASS and state["new_emu_runs"] == 0 and
                  state["images_completed"] == len(selected) and state["parent_identity_sha256"] == a.PARENT_IDENTITY_SHA and
                  type(state["jobs"]) is int and 1 <= state["jobs"] <= 4, "build state differs")
        for image in selected:
            g.require(image["name"] in expected and all(image[k] == v for k, v in expected[image["name"]].items()) and
                      image["path"] == str(PurePosixPath(root) / "images" / image["name"]), "canonical image differs")
        grouped[name] = selected
        images.extend(selected)
    g.require(len(images) == len(expected) and {i["name"] for i in images} == set(expected), "archive cohort differs")
    records, negatives, all_inputs, diagnostics = [], [], {}, []
    with tempfile.TemporaryDirectory(prefix="firstdot-audit-") as tmp:
        extracted, builds, translated = Path(tmp), {}, {}
        for logical in archive.records:
            if logical.startswith(("builds/", "campaigns/")):
                target = extracted / logical
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.raw(logical))
        for image in images:
            prefix = "builds/" + PurePosixPath(image["path"]).parent.parent.name + "/images/" + image["name"]
            build = extracted / prefix
            receipt = a.read(build / "build.json")
            m.validate_selection(image, a.read(build / "data/manifest.json"), receipt)
            old.commands(archive, prefix, image, receipt)
            g.require(g.verify_build(build, repo) == a.read(build / "elf-validation.json"), "cached compiled model differs")
            g.require(g.sha(build / "vdot-perf.bin") == image["image_sha256"], "BIN receipt differs")
            for path, sha in receipt["external_files"].items():
                include(all_inputs, path, sha)
            for tool in receipt["toolchain"].values():
                include(all_inputs, tool["path"], tool["sha256"])
            builds[image["name"]] = build
            translated[image["name"]] = dict(image, path=str(build))
        pairs = a.pairs(list(translated.values()), repo, physical=False)
        for name, selected in grouped.items():
            remapped = [translated[i["name"]] for i in selected]
            g.require(a.pairs(remapped, repo, physical=False) == archive.json("builds/" + name + "/pairs.json"), "build layout cache differs")
            a.validate_baselines(repo, extracted / "builds" / name, remapped)
        suite = g.load("firstdot_audit_banner", repo / "team/optimizations/o2/fullcore/run_suite.py")
        for campaign, root in meta["campaigns"].items():
            prefix, current = "campaigns/" + campaign, configurations[campaign]
            selected = [i for b in current["canonical_builds"] for i in grouped[PurePosixPath(b).name]]
            indexed = {i["name"]: i for i in selected}
            g.require(len(indexed) == len(selected), "duplicate campaign image")
            inputs = expected_inputs(repo, archive, identity, current, selected, m)
            g.require(inputs == archive.json(prefix + "/runtime-inputs.json"), "runtime input inventory differs")
            for path, sha in inputs.items():
                include(all_inputs, path, sha)
            g.require(archive.raw(prefix + "/parent-identity.json") == archive.raw("parent-identity.json") and
                      archive.json(prefix + "/hardware-profile.json") == identity["hardware_profile"], "campaign parent differs")
            g.require(a.pairs([translated[i["name"]] for i in selected], repo, physical=False) == archive.json(prefix + "/pairs.json"), "runtime pair cache differs")
            state, cached = archive.json(prefix + "/state.json"), archive.json(prefix + "/results.json")
            labels = {p[len(prefix + "/runs/"):].split("/")[0] for p in archive.records if p.startswith(prefix + "/runs/") and
                      p.endswith("/result.json") and len(p[len(prefix + "/runs/"):].split("/")) == 2}
            fixture, local, negative, used = None, [], None, set()
            if prefix + "/negative-fixture/fixture.json" in archive.records:
                fixture = archive.json(prefix + "/negative-fixture/fixture.json")
                old.fixture_identity(archive, prefix + "/negative-fixture", fixture, cfg, m)
            for label in sorted(labels):
                run = extracted / prefix / "runs" / label
                record = a.read(run / "result.json")
                image = indexed.get(record["name"])
                g.require(image is not None and type(record["replay"]) is int and record["replay"] in (0, 1) and
                          type(record["negative"]) is bool, "unexpected run identity")
                replay, is_negative = record["replay"], record["negative"]
                key = (record["name"], replay, is_negative)
                g.require(key not in used, "duplicate campaign execution")
                used.add(key)
                if is_negative:
                    wanted = "negative-firstdot-8x32"
                    g.require(negative is None and fixture is not None and record["name"] == "performance-firstdot-d0-s03" and replay == 0, "negative target")
                elif label == "recovery-firstdot-8x32":
                    wanted = label
                    g.require(record["name"] == "performance-firstdot-d0-s03" and replay == 0, "recovery target")
                else:
                    wanted = ("replay-" if replay else "formal-") + record["name"]
                g.require(label == wanted and record["cwd"] == str(PurePosixPath(root) / "runs" / label / "cwd"), "run label/cwd")
                common.run_identity(record, image, replay, is_negative, cfg, fixture, inputs, sealed)
                g.require(record["raw_sha256"] == {n: g.sha(run / n) for n in ("stdout.log", "stderr.log")}, "raw receipt differs")
                suite.validate_runtime((run / "stdout.log").read_text() + (run / "stderr.log").read_text(), record["reference"])
                for path, sha in record["files"].items():
                    include(all_inputs, path, sha)
                if is_negative:
                    before, trace = a.read(run / "negative.json"), a.read(run / "observation.json")
                    details = m.negative_check(repo, builds[image["name"]], run, record)
                    g.require(details == before == record["negative_details"] and a.read(run / "observation.json") == trace and
                              details["vd"] == 0 and details["word"] == "0x0388000b" and details["bit"] == 100, "negative raw replay differs")
                    negative = record
                else:
                    g.require(not replay or image["dataset"] == 0, "unexpected replay dataset")
                    checked = common.normal_audit(repo, builds[image["name"]], run, record, {p: v["sha256"] for p, v in sealed.items()})
                    diagnostics.extend(checked["fu_windows"])
                    local.append(record)
            formal = {r["name"] for r in local if r["replay"] == 0}
            replayed = {r["name"] for r in local if r["replay"] == 1}
            g.require(formal == set(indexed), "missing normal execution")
            coverage = a.qualification(selected, local, negative is not None, bool(replayed))
            verdict = a.RUN_PASS if coverage["negative_and_recovery"] and coverage["all_window_replay"] else "FIRSTDOT_PARTIAL_PASS"
            g.require(state["status"] == cached["status"] == verdict and state["contract"] == cached["contract"] == c.CONTRACT and
                      cached["qualification"] == coverage and cached["parent_identity_sha256"] == a.PARENT_IDENTITY_SHA and
                      state["active_pid"] is None and state["active_result"] is None and state["new_emu_runs"] == len(local) + int(negative is not None) and
                      state["hardware_changed"] is False and state["stable_default_changed"] is False and state["historical_performance_reused"] is False,
                      "campaign qualification differs")
            g.require(isinstance(state["operation_id"], str) and state["operation_id"].strip(), "missing operation")
            chronological = sorted(local + ([negative] if negative else []), key=lambda r: old.times(r)[0])
            expected_order = ["negative-firstdot-8x32", "recovery-firstdot-8x32"] if negative else []
            for image in sorted(selected, key=lambda i: (i["shard"], i["dataset"], a.VARIANTS.index(i["variant"]) ^ ((i["shard"] + i["dataset"]) % 2))):
                if not (negative and image["name"] == negative["name"]):
                    expected_order.append("formal-" + image["name"])
            expected_order.extend("replay-" + i["name"] for i in selected if i["name"] in replayed)
            g.require([PurePosixPath(r["cwd"]).parent.name for r in chronological] == expected_order, "execution order differs")
            ordered = [r for r in chronological if not r["negative"]]
            g.require(cached["runs"] == ordered and cached["negative"] == negative and
                      archive.json(prefix + "/completed-runs.json") == ordered, "cached execution list differs")
            stats = a.summarize(ordered)
            g.require(all(cached[k] == stats[k] for k in stats), "cached statistics differ")
            start, finish = old.times(state)
            g.require(chronological and start <= old.times(chronological[0])[0] and old.times(chronological[-1])[1] <= finish, "campaign timestamps")
            if negative:
                g.require(chronological[:2] == [negative, next(r for r in local if PurePosixPath(r["cwd"]).parent.name == "recovery-firstdot-8x32")], "recovery order")
                common.audit_recovery(chronological[0], chronological[1])
                negatives.append(negative)
            else:
                g.require(fixture is None and all(PurePosixPath(r["cwd"]).parent.name != "recovery-firstdot-8x32" for r in local), "orphan fixture/recovery")
            records.extend(ordered)
        formal, replayed = ([r for r in records if r["replay"] == n] for n in (0, 1))
        wanted_replays = {i["name"] for i in images if i["dataset"] == 0}
        g.require(len(negatives) == 1 and len(formal) == len(expected) and {r["name"] for r in formal} == set(expected) and
                  len(replayed) == len(wanted_replays) and {r["name"] for r in replayed} == wanted_replays, "aggregate coverage differs")
        for record in replayed:
            prior = next(r for r in formal if r["name"] == record["name"])
            g.require(old.times(prior)[1] <= old.times(record)[0] and m.signature(prior) == m.signature(record), "all-window replay differs")
        chronological = sorted(records + negatives, key=lambda r: old.times(r)[0])
        g.require(chronological[0] == negatives[0], "negative did not precede full cohort")
        for before, after in zip(chronological, chronological[1:]):
            g.require(old.times(before)[1] <= old.times(after)[0], "concurrent performance execution")
    logicals = {r["original"]: logical for logical, r in archive.records.items()}
    g.require(sealed == {p: dict(sha256=sha, logical=logicals.get(p)) for p, sha in all_inputs.items()}, "sealed input closure differs")
    external = {str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): m.EMU, cfg["reference"]: identity["reference_sha256"],
                cfg["flash"]: identity["flash_sha256"], **pairs["build_identity"]["external_files"]}
    external.update({t["path"]: t["sha256"] for t in pairs["build_identity"]["toolchain"].values()})
    g.require(all(row["logical"] is not None or external.get(path) == row["sha256"] for path, row in sealed.items()), "unarchived non-external input")
    stats = a.summarize(records)
    return dict(status=AUDIT_PASS, contract=c.CONTRACT, qualification_scope=meta["qualification_scope"], archive=archive.bytes_result,
        formal_images=len(formal), replay_images=len(replayed), expected_negative_runs=1, original_emu_processes=len(records) + 1,
        measured_windows=stats["measured_windows"], all_window_replay_comparisons=24 * len(replayed),
        new_emu_runs=0, new_nemu_runs=0, physical_external_inputs_revalidated=False, hardware_changed=False,
        stable_default_changed=False, whole_suite_acceptance=False, rows=stats["rows"], fu_window_diagnostics=diagnostics,
        scope="sealed ELF/compiled model/full128/CSR/C-ABI retirement/counters/O2/negative/recovery/replay; fixed GEMV invocation")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--action", choices=("pack", "audit", "bytes"), required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--identity", type=Path)
    p.add_argument("--run", type=Path, action="append", default=[])
    p.add_argument("--support", type=Path, action="append", default=[])
    p.add_argument("--scope", choices=("probe", "matrix"))
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    repo, archive = args.repo.resolve(), args.archive.resolve()
    g.require(repo == a.ROOT, "selected evidence checkout differs")
    if args.action == "pack":
        g.require(args.identity and args.scope and args.run, "pack requires identity, scope and campaigns")
        result = pack(repo, args.identity.resolve(), [r.resolve() for r in args.run], archive, args.scope, [r.resolve() for r in args.support])
    else:
        g.require(args.output and not args.output.exists(), "new audit output required")
        a.outside_inputs(args.output.resolve(), [archive, repo])
        if args.action == "audit":
            result = audit(repo, archive)
        else:
            g.require(g.sha(repo / PORTABLE) == HELPERS[str(PORTABLE)], "portable checker drift")
            opened = g.load("firstdot_bytes", repo / PORTABLE).Archive(archive)
            g.require(opened.manifest["contract"] == c.CONTRACT, "archive contract")
            cohort(opened.manifest["qualification_scope"])
            result = dict(status=BYTE_PASS, **opened.bytes_result)
            g.require(a.read(archive / "archive-check.json") == result, "cached byte audit differs")
        g.save(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "fu_window_diagnostics")}, indent=2))


if __name__ == "__main__":
    main()
