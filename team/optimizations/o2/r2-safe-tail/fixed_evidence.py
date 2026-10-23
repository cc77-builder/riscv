#!/usr/bin/env python3
"""Seal/replay the fixed-layout S2 campaign without changing legacy contracts.

The wrapper adds complete layout and command-origin relationships to the
unchanged architecture/counter/trace replay. It launches no EMU or NEMU.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import fixed_layout as l
import merged_evidence as e
import merged_index as index

g, f, m = l.g, l.f, l.m
ENTRY = g.REL / "fixed_evidence.py"
HELPERS = {
    "merged_evidence.py": "ae648951a8258ea20d239e977ea616f1c03ef00e4e83e0d2f7878354434026be",
    "merged_index.py": "a67a26ece6413d7a3f06466e503a2a42d2d8ed33a287b0c9110c9e7c4aece764",
}


def source_identity(repo):
    repo = repo.resolve()
    g.require(Path(__file__).resolve() == (repo / ENTRY).resolve(), "fixed evidence entry outside repository")
    for module, name in ((e, "merged_evidence.py"), (index, "merged_index.py")):
        g.require(Path(module.__file__).resolve() == (repo / g.REL / name).resolve() and
                  g.sha(repo / g.REL / name) == HELPERS[name], "legacy archive helper drift: " + name)
    return g.sha(repo / ENTRY)


def layout_audit(repo, archive):
    """Derive all 13 pairs from sealed bytes; no access to original paths."""
    g.require(archive.manifest.get("contract") == l.CONTRACT, "wrong fixed-layout archive contract")
    g.require(archive.raw("support/fixed_evidence.py") == (repo / ENTRY).read_bytes(),
              "fixed evidence export/audit source differs")
    state = archive.json("canonical/state.json")
    g.require(state.get("contract") == l.CONTRACT and state.get("status") == l.BUILD_PASS and
              state.get("canonical_elfs") == 26 and state.get("pairs") == 13 and state.get("new_emu_runs") == 0,
              "fixed canonical build state incomplete")
    cfg = archive.json("campaign/configuration.json")
    images = archive.json("canonical/images.json")["images"]
    expected = {f.image_name(item): item for item in f.inventory()}
    g.require(len(images) == 26 and {image["name"] for image in images} == set(expected),
              "fixed archive canonical inventory differs")
    common = archive.json("campaign/runtime-inputs.json")
    suffix = "/" + l.ENTRY.as_posix()
    roots = [name[:-len(suffix)] for name in common if name.endswith(suffix)]
    g.require(len(roots) == 1 and PurePosixPath(roots[0]).is_absolute(), "ambiguous fixed live source root")
    source_root = roots[0]
    by, payloads = {}, {}
    for image in images:
        name = image["name"]
        g.require(all(image[key] == value for key, value in expected[name].items()), "fixed image label differs")
        original = PurePosixPath(cfg["canonical_build"]) / "images" / name
        g.require(image["path"] == str(original), "fixed image original path differs")
        prefix = "canonical/images/" + name + "/"
        receipt = archive.json(prefix + "build.json")
        manifest = archive.json(prefix + "data/manifest.json")
        m.validate_selection(image, manifest, receipt)
        g.require(receipt["source_root"] == source_root and
                  receipt["commands"][0]["command"][2] == str(original / "source"),
                  "build command origin differs from canonical/live identity")
        elf, binary = archive.raw(prefix + "vdot-perf.elf"), archive.raw(prefix + "vdot-perf.bin")
        g.require(e.digest(binary) == image["image_sha256"], "fixed archived image hash differs")
        payloads[name] = g.ELF(elf), manifest, binary
        by[(image["suite"], image["dataset"], image["shard"], image["variant"])] = name
    pairs = []
    for image in images:
        if image["variant"] != "s2":
            continue
        first = by[(image["suite"], image["dataset"], image["shard"], "s0")]
        a, ma, ba = payloads[first]
        b, mb, bb = payloads[image["name"]]
        pairs.append(l.compare_pair(a, b, ma, mb, ba, bb))
    g.require(archive.json("canonical/pair-layout.json") == dict(contract=l.LAYOUT_CONTRACT, pairs=pairs),
              "cached complete layout pairs differ")
    return dict(status="R2_FIXED_ARCHIVE_COMPLETE_LAYOUT_PASS", layout_contract=l.LAYOUT_CONTRACT,
                canonical_elfs=26, complete_layout_pairs=len(pairs), pairs=pairs,
                new_emu_runs=0, architecture_replayed=False,
                scope="Complete loaded-byte and exact metadata pairs plus original command-root relationships")


def pack(repo, run, archive_path, support=()):
    source = source_identity(repo)
    common = m.read_json(run / "runtime-inputs.json")
    suffix = "/" + l.ENTRY.as_posix()
    roots = [name[:-len(suffix)] for name in common if name.endswith(suffix)]
    g.require(roots == [repo.resolve().as_posix()],
              "pack must use the original live repository; relocated checkouts are audit/index only")
    extra = [p.resolve() for p in support if p.resolve() != (repo / ENTRY).resolve()]
    extra.append(repo / ENTRY)
    with l.bindings(repo):
        byte_result = e.pack(repo, run, archive_path, extra)
        layout = layout_audit(repo, e.portable(repo).Archive(archive_path))
    return dict(status="R2_FIXED_ARCHIVE_BYTES_AND_LAYOUT_PASS", contract=l.CONTRACT,
                checker_sha256=source, byte_check=byte_result, layout_check=layout,
                new_emu_runs=0, architecture_replayed=False)


def audit(repo, archive_path):
    source = source_identity(repo)
    with l.bindings(repo):
        layout = layout_audit(repo, e.portable(repo).Archive(archive_path))
        result = e.audit(repo, archive_path)
    result.update(status="R2_FIXED_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_LAYOUT_PASS",
                  checker_sha256=source, layout_check=layout, architecture_replayed=True)
    return result


def verify_index(repo, archive_path):
    source = source_identity(repo)
    with l.bindings(repo):
        layout = layout_audit(repo, e.portable(repo).Archive(archive_path))
        result = index.verify(repo, archive_path)
    result.update(status="R2_FIXED_ARCHIVE_COMPLETE_GIT_INDEX_AND_LAYOUT_PASS", contract=l.CONTRACT,
                  fixed_checker_sha256=source, layout_check=layout)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--action", choices=("pack", "audit", "index"), required=True)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--support", action="append", type=Path, default=[])
    args = parser.parse_args()
    try:
        repo = args.repo.resolve()
        index.check_output_path(args.archive, args.output)
        if args.action == "pack":
            g.require(args.run is not None, "pack requires --run")
            result = pack(repo, args.run, args.archive, args.support)
        elif args.action == "audit":
            result = audit(repo, args.archive)
        else:
            result = verify_index(repo, args.archive)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        g.save(args.output, result)
        print(json.dumps(dict(status=result["status"], contract=l.CONTRACT, output=str(args.output), new_emu_runs=0)))
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as exc:
        parser.exit(2, "R2_FIXED_EVIDENCE_REJECTED: " + str(exc) + "\n")
