#!/usr/bin/env python3
"""Seal and independently audit the bounded strong-RVV probe's five processes."""
from __future__ import annotations
import argparse
from datetime import datetime
import gzip
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import rvv_probe as p
import merged_evidence as e
import merged_index as index

g, f, m, l = p.g, p.f, p.m, p.l
ENTRY = g.REL / "rvv_probe_evidence.py"


def source_identity(repo):
    p.source_identity(repo)
    e.bind_modules(repo)
    g.require(Path(__file__).resolve() == (repo / ENTRY).resolve(), "probe auditor outside repository")
    g.require(g.sha(repo / g.REL / "merged_evidence.py") ==
              "ae648951a8258ea20d239e977ea616f1c03ef00e4e83e0d2f7878354434026be" and
              g.sha(repo / g.REL / "merged_index.py") ==
              "a67a26ece6413d7a3f06466e503a2a42d2d8ed33a287b0c9110c9e7c4aece764",
              "frozen probe evidence helper drift")


def completed(state):
    g.require(state.get("contract") == p.CONTRACT and state.get("status") == p.PASS and
              state.get("new_emu_runs") == 5 and state.get("normal_runs_completed") == 4 and
              state.get("formal_windows") == 32 and state.get("failed_or_incomplete_emu_runs") == 0 and
              state.get("final_selection_qualified") is False and
              state.get("historical_b0_h1_acceptance") is False and state.get("whole_suite_acceptance") is False and
              state.get("active_pid") is None and state.get("active_result") is None,
              "bounded probe state incomplete or scope changed")


def jobs(images):
    g.require(len(images) == 2, "probe image inventory length")
    for image, item in zip(images, p.inventory()):
        g.require(all(image[k] == v for k, v in item.items()) and image["name"] == f.image_name(item),
                  "probe archived image selection")
    first, strong = images
    return {"negative-rvv1": (strong, 0, True),
            strong["name"] + "-r0": (strong, 0, False),
            first["name"] + "-r0": (first, 0, False),
            first["name"] + "-r1": (first, 1, False),
            strong["name"] + "-r1": (strong, 1, False)}


def pair(archive):
    images = archive.json("canonical/images.json")["images"]
    jobs(images)
    values = []
    for image in images:
        root = "canonical/images/" + image["name"] + "/"
        values.append((g.ELF(archive.raw(root + "vdot-perf.elf")),
                       archive.json(root + "data/manifest.json"), archive.raw(root + "vdot-perf.bin")))
    a, b = values
    result = p.compare(a[0], b[0], a[1], b[1], a[2], b[2])
    g.require(result == archive.json("canonical/pair-layout.json"), "probe archived pair cache differs")
    return result


def archive_open(repo, archive_path):
    source_identity(repo)
    archive = e.portable(repo).Archive(archive_path)
    g.require(archive.manifest.get("contract") == p.CONTRACT, "wrong probe archive contract")
    g.require(archive.raw("support/rvv_probe_evidence.py") == (repo / ENTRY).read_bytes(),
              "probe archive auditor source differs")
    return archive


def pack(repo, run, output, support=()):
    source_identity(repo)
    completed(m.read_json(run / "state.json"))
    cfg, common = m.read_json(run / "configuration.json"), m.read_json(run / "runtime-inputs.json")
    suffix = "/" + p.ENTRY.as_posix()
    g.require([name[:-len(suffix)] for name in common if name.endswith(suffix)] == [repo.as_posix()],
              "probe pack requires original live source root")
    canonical = Path(cfg["canonical_build"])
    g.require(not output.exists() and not output.is_relative_to(run) and not output.is_relative_to(canonical),
              "new probe archive must be outside live inputs")
    for item in support:
        g.require(not item.is_dir() or not output.is_relative_to(item), "archive inside support")
    with p.bindings(repo):
        p.canonical(repo, cfg)
        m.verify_files(common)
    output.mkdir(parents=True)
    entries, originals = [], {}
    portable = e.portable(repo)

    def add(raw, logical, original):
        portable.safe_relative(logical)
        g.require(original not in originals, "duplicate probe original input")
        path = Path("files") / logical
        encoding, data = "identity", raw
        if len(raw) >= 16384:
            path = path.with_name(path.name + ".gz")
            encoding, data = "gzip", gzip.compress(raw, compresslevel=9, mtime=0)
        target = output / path
        g.require(not target.exists(), "duplicate probe stored path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append(dict(original=original, stored=path.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=e.digest(raw),
                            stored_bytes=len(data), stored_sha256=e.digest(data)))
        originals[original] = logical

    def add_file(path, logical):
        g.require(path.is_file() and not path.is_symlink(), "probe evidence missing/symlink")
        add(path.read_bytes(), logical, str(path))

    for directory, prefix in ((run, "campaign"), (canonical, "canonical")):
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(directory)
            if set(relative.parts) & {"objects", "__pycache__"}:
                continue
            if "cwd" in relative.parts and not (path.name in m.AUX and path.parent.name == "build"):
                continue
            add_file(path, prefix + "/" + relative.as_posix())
    for name in m.META:
        add_file(Path(cfg["build_record"]) / name, "hardware/" + name)
    add_file(Path(cfg["build_driver"]), "hardware/build-driver.py")
    add_file(Path(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py",
             "hardware/original-build-driver.py")
    for name in m.AUX:
        add_file(Path(cfg["hardware_source"]) / "build" / name, "hardware/" + name)
    for name in sorted(common):
        path = Path(name)
        if path.is_relative_to(repo):
            add_file(path, "tools/" + path.relative_to(repo).as_posix())
    for rel in (g.REL / "merged_evidence.py", e.PORTABLE):
        if str(repo / rel) not in originals:
            add_file(repo / rel, "tools/" + rel.as_posix())
    for item in [*support, repo / ENTRY]:
        if item.is_dir():
            for child in sorted(item.rglob("*")):
                if child.is_file():
                    add_file(child, "support/" + item.name + "/" + child.relative_to(item).as_posix())
        else:
            add_file(item, "support/" + item.name)
    inputs = dict(common)
    for record_path in (run / "runs").glob("*/result.json"):
        for name, sha in m.read_json(record_path)["files"].items():
            g.require(name not in inputs or inputs[name] == sha, "probe mixed runtime input")
            inputs[name] = sha
    for image in m.read_json(canonical / "images.json")["images"]:
        for name, sha in m.read_json(Path(image["path"]) / "build.json")["external_files"].items():
            g.require(name not in inputs or inputs[name] == sha, "probe mixed AM identity")
            inputs[name] = sha
    m.verify_files(inputs)
    add(e.json_bytes({name: dict(sha256=sha, logical=originals.get(name)) for name, sha in sorted(inputs.items())}),
        "sealed-inputs.json", "generated:sealed-inputs")
    source = dict(head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
                  status=subprocess.check_output(["git", "status", "--short"], cwd=repo, text=True))
    add(e.json_bytes(source), "export-source.json", "generated:export-source")
    manifest = dict(version=1, contract=p.CONTRACT, created_utc=f.now(), source_commit_at_export=source["head"],
                    work_root=str(run), files=entries,
                    exclusions=["physical EMU/normal NEMU/flash/AM libraries", "hardware/dependency trees",
                                "canonical intermediate objects", "incidental simulator cwd output"],
                    scope="bounded dataset0 endtoend probe; original bytes with external input hashes")
    raw = e.json_bytes(manifest)
    (output / "archive-manifest.json").write_bytes(raw)
    (output / "archive-manifest.sha256").write_text(e.digest(raw) + "  archive-manifest.json\n")
    archive = archive_open(repo, output)
    byte_result = dict(status="R2_MERGED_ARCHIVE_BYTES_PASS", **archive.bytes_result)
    g.save(output / "archive-check.json", byte_result)
    return dict(status="R2_STRONG_RVV_PROBE_BYTES_AND_LAYOUT_PASS", archive=archive.bytes_result,
                layout=pair(archive), new_emu_runs=0, architecture_replayed=False)


def fixture_identity(archive, fixture, cfg):
    g.require(fixture["source_sha256"] == m.NEGATIVE_SHA and fixture["normal_reference_sha256"] == f.REFERENCE and
              fixture["historical_negative_hash_claim"] is False and
              e.digest(archive.raw("campaign/negative-fixture/negative-fixture.c")) == m.NEGATIVE_SHA and
              e.digest(archive.raw("campaign/negative-fixture/negative-reference.so")) == fixture["negative_sha256"],
              "probe negative fixture identity")
    compiler = fixture["command"][0]
    root = PurePosixPath(fixture["binary"]).parent
    command = [compiler, "-shared", "-fPIC", "-O2", '-DREF_SO="' + cfg["reference"] + '"',
               str(root / "negative-fixture.c"), "-Wl,--no-as-needed", cfg["reference"], "-ldl", "-o", fixture["binary"]]
    g.require(fixture["command"] == command, "probe fixture argv")
    for step in ("compiler", "compile", "linkage"):
        prefix = "campaign/negative-fixture/" + step + "/"
        receipt = archive.json(prefix + "command.json")
        expected = [compiler, "--version"] if step == "compiler" else command if step == "compile" else \
                   [receipt["command"][0], "-d", fixture["binary"]]
        g.require(receipt.get("process_started") is True and receipt.get("exit_code") == 0 and
                  not receipt.get("timed_out") and receipt["command"] == expected and receipt["raw_sha256"] ==
                  {n: e.digest(archive.raw(prefix + n)) for n in ("stdout.log", "stderr.log")},
                  "probe fixture command receipt")
    g.require("Shared library: [" + cfg["reference"] + "]" in
              archive.raw("campaign/negative-fixture/linkage/stdout.log").decode(), "probe fixture dependency")


def audit(repo, archive_path):
    archive = archive_open(repo, archive_path)
    completed(archive.json("campaign/state.json"))
    layout = pair(archive)
    cfg = archive.json("campaign/configuration.json")
    images = archive.json("canonical/images.json")["images"]
    expected_jobs = jobs(images)
    found = {name.split("/")[2] for name in archive.records if name.startswith("campaign/runs/") and
             name.endswith("/result.json") and len(name.split("/")) == 4}
    g.require(found == set(expected_jobs), "probe archived run inventory")
    common, sealed = archive.json("campaign/runtime-inputs.json"), archive.json("sealed-inputs.json")
    suffix = "/" + p.ENTRY.as_posix()
    roots = [name[:-len(suffix)] for name in common if name.endswith(suffix)]
    g.require(len(roots) == 1 and PurePosixPath(roots[0]).is_absolute(), "probe live root identity")
    source_root = roots[0]
    for logical in archive.records:
        if logical.startswith("tools/team/") and logical.endswith(".py"):
            rel = Path(logical).relative_to("tools")
            g.require((repo / rel).read_bytes() == archive.raw(logical), "probe offline tool differs: " + str(rel))
    for name, sha in m.META.items():
        g.require(e.digest(archive.raw("hardware/" + name)) == sha, "probe hardware metadata differs")
    pins = archive.json("hardware/hardware-inputs.json")
    g.require(pins["source_commit"] == m.SOURCE and pins["emu_sha256"] == m.EMU and
              len(pins["files"]) == 429 and len(pins["dependency_files"]) == 21236 and
              e.digest(archive.raw("hardware/build-driver.py")) == pins["build_script_sha256"], "probe hardware identity")
    fixture = archive.json("campaign/negative-fixture/fixture.json")
    fixture_identity(archive, fixture, cfg)
    with p.bindings(repo):
        f.pinned_modules(repo)
        g.verify_sources(repo)
        expected_common = {source_root + "/" + Path(n).relative_to(repo).as_posix(): sha
                           for n, sha in m.checker_files(repo).items()}
        for rel in (p.ENTRY, p.S1):
            expected_common[source_root + "/" + rel.as_posix()] = g.sha(repo / rel)
        expected_common.update({str(PurePosixPath(cfg["build_record"]) / n): sha for n, sha in m.META.items()})
        expected_common.update({str(PurePosixPath(cfg["hardware_source"]) / "build" / n): sha for n, sha in m.AUX.items()})
        expected_common.update({str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): m.EMU,
            cfg["reference"]: f.REFERENCE, cfg["flash"]: f.FLASH, cfg["build_driver"]: pins["build_script_sha256"],
            str(PurePosixPath(cfg["hardware_source"]) / "team/optimizations/o2/fullcore/build_fullcore.py"):
            "8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0"})
        for n in ("state.json", "images.json", "pair-layout.json"):
            expected_common[str(PurePosixPath(cfg["canonical_build"]) / n)] = e.digest(archive.raw("canonical/" + n))
        for image in images:
            g.require(image["path"] == str(PurePosixPath(cfg["canonical_build"]) / "images" / image["name"]),
                      "probe archived build origin")
            for n in ("build.json", "data/manifest.json"):
                expected_common[str(PurePosixPath(image["path"]) / n)] = \
                    e.digest(archive.raw("canonical/images/" + image["name"] + "/" + n))
        g.require(common == expected_common, "probe complete common input inventory differs")
        expected_sealed = dict(common)
        external = {str(PurePosixPath(cfg["hardware_source"]) / "build/emu"): m.EMU,
                    cfg["reference"]: f.REFERENCE, cfg["flash"]: f.FLASH}
        records, negatives, diagnostics = [], [], []
        with tempfile.TemporaryDirectory(prefix="strong-rvv-audit-") as temporary:
            root = Path(temporary)
            for logical in archive.records:
                if logical.startswith(("canonical/", "campaign/")):
                    target = root / logical
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.raw(logical))
            state = m.read_json(root / "canonical/state.json")
            g.require(state.get("status") == p.BUILD_PASS and state.get("contract") == p.CONTRACT and
                      state.get("canonical_elfs") == 2 and state.get("new_emu_runs") == 0, "probe canonical state")
            identity = None
            for image in images:
                build = root / "canonical/images" / image["name"]
                g.verify_build(build, repo)
                g.require(g.sha(build / "vdot-perf.bin") == image["image_sha256"], "probe image digest")
                receipt = m.read_json(build / "build.json")
                m.validate_selection(image, m.read_json(build / "data/manifest.json"), receipt)
                g.require(receipt["source_root"] == source_root and receipt["commands"][0]["command"][2] ==
                          str(PurePosixPath(image["path"]) / "source"), "probe build source/command origin")
                current = {k: receipt[k] for k in ("kind", "source_base", "source_commit", "am_revision", "external_files", "toolchain")}
                if identity is None:
                    identity = current
                expected_libraries = {str(PurePosixPath(cfg["am_home"]) / name) for name in
                                      ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")}
                g.require(current == identity and receipt["am_revision"] == f.AM_COMMIT and
                          set(receipt["external_files"]) == expected_libraries, "probe build/library identity")
                external.update(receipt["external_files"])
                expected_sealed.update(receipt["external_files"])
            suite = g.load("probe_offline_runtime_banner", repo / "team/optimizations/o2/fullcore/run_suite.py")
            all_records = []
            for name, (image, replay, negative) in expected_jobs.items():
                run = root / "campaign/runs" / name
                record = m.read_json(run / "result.json")
                e.run_identity(record, image, replay, negative, cfg, fixture, common, sealed)
                expected_sealed.update(record["files"])
                g.require(record["raw_sha256"] == {n: g.sha(run / n) for n in ("stdout.log", "stderr.log")},
                          "probe raw transcript changed")
                suite.validate_runtime((run / "stdout.log").read_text() + (run / "stderr.log").read_text(), record["reference"])
                build = root / "canonical/images" / image["name"]
                if negative:
                    detail, observation = m.read_json(run / "negative.json"), m.read_json(run / "observation.json")
                    g.require(m.negative_check(repo, build, run, record) == detail == record["negative_details"] and
                              m.read_json(run / "observation.json") == observation, "probe negative cache differs")
                    negatives.append(record)
                else:
                    checked = e.normal_audit(repo, build, run, record, {n: v["sha256"] for n, v in sealed.items()})
                    diagnostics.extend(checked["fu_windows"])
                    records.append(record)
                all_records.append(record)
            g.require(len(negatives) == 1 and len(records) == 4 and len(diagnostics) == 16, "probe audit run counts")
            for before, after in zip(all_records, all_records[1:]):
                g.require(datetime.fromisoformat(before["finished"]) <= datetime.fromisoformat(after["started"]),
                          "probe execution order/concurrency differs")
            e.audit_recovery(negatives[0], records[0])
            for record in records:
                if record["replay"] == 1:
                    prior = next(r for r in records if r["name"] == record["name"] and r["replay"] == 0)
                    g.require(m.signature(prior) == m.signature(record), "probe archived replay differs")
        g.require(set(sealed) == set(expected_sealed), "probe sealed input closure differs")
        for name, entry in sealed.items():
            g.require(entry["sha256"] == expected_sealed[name], "probe sealed input hash differs")
            if entry["logical"] is None:
                g.require(external.get(name) == entry["sha256"], "probe unarchived non-external input")
            else:
                g.require(e.digest(archive.raw(entry["logical"])) == entry["sha256"], "probe sealed payload differs")
        stats = p.summarize(records)
        cached = archive.json("campaign/results.json")
        g.require(cached["status"] == p.PASS and cached["contract"] == p.CONTRACT and
                  cached["negative"] == negatives[0] and cached["runs"] == records, "probe summary receipts differ")
        for name in ("samples", "rows", "fastest_rvv", "scope"):
            g.require(cached[name] == stats[name], "probe cached statistics differ: " + name)
    return dict(status="R2_STRONG_RVV_PROBE_ARCHITECTURE_COUNTER_TRACE_LAYOUT_PASS", contract=p.CONTRACT,
                archive=archive.bytes_result, layout=layout, normal_runs=4, expected_negative_runs=1,
                formal_windows=32, replay_runs=2, rows=stats["rows"], fastest_rvv=stats["fastest_rvv"],
                fu_window_diagnostics=diagnostics, final_selection_qualified=False,
                new_emu_runs=0, physical_hardware_and_reference_inputs_revalidated=False, architecture_replayed=True,
                scope=stats["scope"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--action", choices=("pack", "audit", "bytes", "index"), required=True)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--support", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        repo, archive_path = args.repo.resolve(), args.archive.resolve()
        index.check_output_path(archive_path, args.output)
        if args.action == "pack":
            g.require(args.run is not None, "probe pack requires --run")
            result = pack(repo, args.run.resolve(), archive_path, [x.resolve() for x in args.support])
        elif args.action == "audit":
            result = audit(repo, archive_path)
        else:
            archive = archive_open(repo, archive_path)
            layout = pair(archive)
            result = dict(status="R2_STRONG_RVV_PROBE_BYTES_AND_LAYOUT_PASS", archive=archive.bytes_result,
                          layout=layout, new_emu_runs=0, architecture_replayed=False)
            if args.action == "index":
                with p.bindings(repo):
                    result["index"] = index.verify(repo, archive_path)
                result["status"] = "R2_STRONG_RVV_PROBE_COMPLETE_GIT_INDEX_AND_LAYOUT_PASS"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        g.save(args.output, result)
        print(e.json_bytes({k: result[k] for k in ("status", "new_emu_runs", "architecture_replayed")}).decode())
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as exc:
        parser.exit(2, "R2_STRONG_RVV_EVIDENCE_REJECTED: " + str(exc) + "\n")
