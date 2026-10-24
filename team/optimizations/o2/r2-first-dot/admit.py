"""Admit the existing 8x32 first-dot ELF pair to a new, bounded runtime contract.

Reuse the authenticated static probe; never rebuild it or launch a simulator.
The archive, exact generation, loaded bytes and decoded negative target are
checked independently of the probe's cached PASS. Linux LF sources required.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "team/optimizations/o2/r2-vector-accum"))
import first_dot_probe as probe

g = probe.g
CONTRACT = "r2-first-dot-8x32-admission-v1"
ARCHIVE = Path("team/optimizations/o2/r2-vector-accum/evidence/merged-v2")
MANIFEST_SHA = "a1af4314c83b29d97b58b7ae9fe65dbc96bb3d050530d2fe7378c022b9415d73"
PROBE_SHA = "0bb3de513d8a542829be8ca11f19b55b477ca3dff63949469fefe6978f1042d8"
PREFIX = "files/support/first-dot-probe-02/"


def read(path):
    return json.loads(Path(path).read_bytes())


def safe_relative(name):
    path = PurePosixPath(name)
    g.require(bool(path.parts) and not path.is_absolute() and
              all(p not in (".", "..") and ":" not in p and "\\" not in p for p in path.parts),
              "unsafe archive path")
    return Path(*path.parts)


def archive_bytes(archive, entry):
    relative = safe_relative(entry["stored"])
    path = archive / relative
    g.require(path.resolve().is_relative_to(archive.resolve()) and not path.is_symlink(),
              "archive payload escaped root")
    body = path.read_bytes()
    g.require(len(body) == entry["stored_bytes"] and hashlib.sha256(body).hexdigest() == entry["stored_sha256"],
              "archive stored bytes differ")
    g.require(entry["encoding"] in ("gzip", "identity"), "unknown archive encoding")
    raw = gzip.decompress(body) if entry["encoding"] == "gzip" else body
    g.require(len(raw) == entry["raw_bytes"] and hashlib.sha256(raw).hexdigest() == entry["raw_sha256"],
              "archive raw bytes differ")
    return raw


def extract(archive, output):
    g.require(g.sha(archive / "archive-manifest.json") == MANIFEST_SHA, "frozen archive identity")
    output.mkdir(parents=True, exist_ok=False)
    records = read(archive / "archive-manifest.json")["files"]
    selected = [r for r in records if any(r["stored"].startswith(PREFIX + "s03-" + v + "/")
                                        for v in ("s1", "firstdot"))]
    g.require(len(selected) == 66, "bounded two-image archive inventory")
    inventory = {}
    for record in selected:
        name = record["stored"][len(PREFIX):]
        if record["encoding"] == "gzip":
            g.require(name.endswith(".gz"), "compressed archive suffix")
            name = name[:-3]
        g.require(name not in inventory, "duplicate extracted path")
        target = output / safe_relative(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive_bytes(archive, record))
        inventory[name] = record["raw_sha256"]
    canonical = [r for r in records if r["stored"] ==
                 "files/canonical/images/performance-s1-d0-s03/vdot-perf.bin.gz"]
    g.require(len(canonical) == 1, "canonical S1 image inventory")
    g.require((output / "s03-s1/vdot-perf.bin").read_bytes() == archive_bytes(archive, canonical[0]),
              "probe control differs from qualified canonical S1 image")
    return inventory


def verify_sources():
    g.verify_sources(ROOT)
    for name, digest in (("candidate.py", probe.PARENT_SHA), ("gate.py", probe.GATE_SHA),
                         ("experiment.py", probe.EXPERIMENT_SHA), ("first_dot_probe.py", PROBE_SHA)):
        g.require(g.sha(ROOT / probe.c.REL / name) == digest, "frozen first-dot source: " + name)
    g.require(Path(probe.c.__file__).resolve() == ROOT / probe.c.REL / "candidate.py" and
              Path(g.__file__).resolve() == ROOT / probe.c.REL / "gate.py" and
              Path(probe.__file__).resolve() == ROOT / probe.c.REL / "first_dot_probe.py", "module roots")


def verify_image(build, variant):
    g.require(variant in ("s1", "firstdot"), "candidate variant")
    manifest, receipt = read(build / "data/manifest.json"), read(build / "build.json")
    g.require(receipt["contract"] == probe.CONTRACT and receipt["variant"] == variant and
              receipt["shard"] == 3, "probe build identity")
    expected_sources = set(g.PINNED) | {str(probe.c.REL / n) for n in
                                      ("candidate.py", "gate.py", "experiment.py", "first_dot_probe.py")}
    g.require(set(receipt["source_sha256"]) == expected_sources and set(receipt["artifacts"]) ==
              {"vdot-perf.elf", "vdot-perf.bin", "kernels-reference.o", "data/manifest.json"},
              "probe receipt inventory")
    g.require(len(receipt["commands"]) == 2, "probe command inventory")
    for label, command in zip(("make-command", "reference-command"), receipt["commands"]):
        g.require(command == read(build / label / "command.json") and command["exit_code"] == 0 and
                  command.get("process_started") is True and not command.get("timed_out", False),
                  "incomplete or inconsistent original build command")
        g.require(set(command["raw_sha256"]) == {"stdout.log", "stderr.log"}, "command log inventory")
        for name, digest in command["raw_sha256"].items():
            g.require(g.sha(build / label / name) == digest, "original build command log changed")
    for name, digest in receipt["source_sha256"].items():
        relative = safe_relative(name)
        g.require(g.sha(build / "source/repo" / relative) == digest and g.sha(ROOT / relative) == digest,
                  "source snapshot differs: " + name)
    for name, digest in receipt["artifacts"].items():
        g.require(g.sha(build / safe_relative(name)) == digest, "probe artifact changed: " + name)
    with tempfile.TemporaryDirectory(prefix="firstdot-regenerate-") as temporary:
        fresh = Path(temporary) / "data"
        regenerated = probe.generate(ROOT, fresh, variant, 3)
        g.require(regenerated == manifest, "manifest differs from exact first-dot regeneration")
        for name in ("kernels.S", "cases.h"):
            g.require((fresh / name).read_bytes() == (build / "data" / name).read_bytes(),
                      "generated source differs: " + name)
    for name in ("main.c", "Makefile", "fixed-layout.ld"):
        g.require((build / "source" / name).read_bytes() == (ROOT / g.O3 / name).read_bytes(),
                  "benchmark harness changed")
    checked = g.original.inspect(build / "vdot-perf.elf", build / "vdot-perf.bin",
                                 build / "kernels-reference.o", manifest, g.auditor(ROOT))
    elf = g.ELF((build / "vdot-perf.elf").read_bytes())
    reference = g.ELF((build / "kernels-reference.o").read_bytes())
    g.require(reference.named[".text"][5] == 32768 and
              not any(s[1] in (4, 9) and s[5] for s in reference.sections), "reference layout/relocations")
    checked["finite_model"] = g.semantic_check(elf, manifest, ROOT)
    checked["first_custom_target"] = negative_target(elf, manifest, variant)
    return checked


def negative_target(elf, manifest, variant):
    g.require(variant in ("s1", "firstdot"), "negative target variant")
    g.require(manifest["plan"][0]["index"] == 0 and manifest["rows"][0]["method"] == "vdot",
              "first runtime kernel must be the basic VDOT kernel")
    address = elf.symbols["t13_kernel_0"][0]
    hits = [(address + i * 4, word) for i, (word,) in
            enumerate(struct.iter_unpack("<I", elf.symbol_data("t13_kernel_0")))
            if word & 0xfe00707f == 0x0200000b]
    g.require(len(hits) == 32, "8x32 custom instruction count")
    pc, word = hits[0]
    rd = (word >> 7) & 31
    g.require(rd == (0 if variant == "firstdot" else 20) and
              (word >> 15) & 31 == 16 and (word >> 20) & 31 == 24, "first custom operand identity")
    return dict(pc=hex(pc), word=hex(word), rd=rd, corruption_bit=64,
                xor_mask="0x00000000000000010000000000000000", low32_unchanged=True,
                negative_executed=False, recovery_executed=False)


def verify_pair(inputs):
    paths = [inputs / ("s03-" + v) for v in ("s1", "firstdot")]
    elfs = [g.ELF((p / "vdot-perf.elf").read_bytes()) for p in paths]
    binaries = [(p / "vdot-perf.bin").read_bytes() for p in paths]
    result = g.paired_layout(*elfs, *binaries)
    for slot in (1, 3):
        g.require(binaries[0][8192 * (slot + 1):8192 * (slot + 2)] ==
                  binaries[1][8192 * (slot + 1):8192 * (slot + 2)], "paired RVV slot changed")
    g.require((paths[0] / "data/cases.h").read_bytes() == (paths[1] / "data/cases.h").read_bytes(),
              "paired cases changed")
    result["removed_body_instructions"] = {}
    decoder = g.auditor(ROOT)
    for index, software, expected in ((0, "basic", 32), (2, "reuse", 20)):
        sizes = [len(g.body_bytes(e.symbol_data(f"t13_kernel_{index}"), decoder)) // 4 for e in elfs]
        g.require(sizes[0] - sizes[1] == expected, "unexpected first-dot instruction reduction")
        result["removed_body_instructions"][software] = expected
    result.update(rvv_slots_identical=True, cases_identical=True)
    return result


def main(archive, output):
    g.require(os.name == "posix", "use Linux LF sources")
    archive, output = archive.resolve(), output.absolute()
    g.require(not output.exists() and not output.is_symlink() and
              not output.resolve().is_relative_to(ROOT) and not ROOT.is_relative_to(output.resolve()) and
              not output.resolve().is_relative_to(archive) and not archive.is_relative_to(output.resolve()),
              "new output must not overlap source or archive")
    verify_sources()
    output.mkdir(parents=True)
    result = dict(contract=CONTRACT, status="RUNNING", started=datetime.now(timezone.utc).isoformat(),
                  source_sha256=g.sha(__file__), archive_manifest_sha256=MANIFEST_SHA,
                  new_emu_runs=0, new_nemu_runs=0, new_builds=0,
                  runtime_qualified=False, performance_qualified=False)
    checker_paths = {Path(m.__file__).resolve() for m in
                     (probe, probe.c, probe.a, g, g.original, g.old_model, probe.a.legacy_f, probe.a.legacy_m)}
    checker_paths.update((Path(__file__).resolve(), ROOT / "team/optimizations/o2/r2-kernel-audit/audit.py"))
    result["checker_sha256"] = {str(p.relative_to(ROOT)): g.sha(p) for p in sorted(checker_paths)}
    g.save(output / "state.json", result)
    try:
        result["input_sha256"] = extract(archive, output / "inputs")
        result["images"] = {v: verify_image(output / "inputs" / ("s03-" + v), v)
                            for v in ("s1", "firstdot")}
        result["pair"] = verify_pair(output / "inputs")
        verify_sources()
        for name, digest in result["checker_sha256"].items():
            g.require(g.sha(ROOT / name) == digest, "admission checker changed")
        for name, digest in result["input_sha256"].items():
            g.require(g.sha(output / "inputs" / name) == digest, "admitted input changed")
        result["status"] = "FIRST_DOT_8X32_STATIC_ADMISSION_PASS_NOT_EXECUTED"
    except BaseException as exc:
        result.update(status="FAILED", error=repr(exc))
        raise
    finally:
        result["finished"] = datetime.now(timezone.utc).isoformat()
        g.save(output / "state.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / ARCHIVE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(main(args.archive, args.output), indent=2))
