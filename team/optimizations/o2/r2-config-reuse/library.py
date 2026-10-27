"""Package the qualified config_reuse object; prove all C consumers resolve its bytes."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

import c_api as c
import c_evidence as ce

g, a, e = c.g, c.a, c.evidence
ARTIFACTS = {"gemv.S", "gemv.h", "gemv.o", "libconfig_reuse_gemv.a", "consumer.c", "consumer.o", "consumer-linked.o",
             "member-list/stdout.log", "member-extract/stdout.log"}


def archive_member(raw):
    """Read GNU ar members without executing a tool during offline checking."""
    g.require(raw.startswith(b"!<arch>\n"), "invalid GNU archive")
    offset, members = 8, {}
    while offset < len(raw):
        g.require(offset + 60 <= len(raw), "truncated archive header")
        header = raw[offset:offset + 60]
        g.require(header[-2:] == b"`\n", "archive member terminator")
        name = header[:16].decode("ascii").strip()
        size = int(header[48:58].decode("ascii").strip())
        offset += 60
        g.require(size >= 0 and offset + size <= len(raw), "archive member size")
        data = raw[offset:offset + size]
        offset += size
        if size % 2:
            g.require(raw[offset:offset + 1] == b"\n", "archive member padding")
            offset += 1
        if name == "/":
            continue
        g.require(name.endswith("/") and name[:-1] == "gemv.o" and "gemv.o" not in members, "unexpected archive member")
        members[name[:-1]] = data
    g.require(offset == len(raw) and set(members) == {"gemv.o"}, "archive membership differs")
    return members["gemv.o"]


def consumer(names):
    declarations = ["#include <stdint.h>", '#include "gemv.h"',
        "typedef void (*entry_t)(const int8_t *, void *);",
        "entry_t const config_reuse_all_entries[] = {"]
    declarations.extend("  " + name + "," for name in names)
    declarations += ["};", "void config_reuse_link_all(const int8_t *p, void *q) {",
                     "  for (unsigned i=0; i<16; ++i) config_reuse_all_entries[i](p,q);", "}", ""]
    return "\n".join(declarations)


def consumer_references(elf, names):
    """Prove the linked C table still references each of the sixteen leaves."""
    g.require(elf.kind == 1, "consumer must be a relocatable link")
    address, size, index, _ = elf.symbols["config_reuse_all_entries"]
    start = address - elf.sections[index][3]
    found = {}
    for section in elf.sections:
        if section[1] != 4 or section[7] != index:
            continue
        g.require(section[9] == 24 and section[5] % 24 == 0 and section[6] < len(elf.sections),
                  "consumer relocation section")
        symbols = elf.sections[section[6]]
        g.require(symbols[1] == 2 and symbols[9] == 24 and symbols[6] < len(elf.sections),
                  "consumer relocation symbols")
        strings = elf.section(elf.sections[symbols[6]])
        for pos in range(section[4], section[4] + section[5], 24):
            offset, info, addend = struct.unpack_from("<QQq", elf.raw, pos)
            if not (start <= offset < start + size):
                continue
            number = info >> 32
            g.require(info & 0xffffffff == 2 and addend == 0 and number < symbols[5] // 24 and
                      offset not in found, "consumer entry relocation differs")
            name_offset = struct.unpack_from("<I", elf.raw, symbols[4] + 24 * number)[0]
            found[offset] = elf.string(strings, name_offset)
    g.require(found == {start + 8 * i: name for i, name in enumerate(names)},
              "consumer does not reference all qualified entries in order")
    return len(found)


def byte_check(output):
    receipt = a.read(output / "library.json")
    g.require(receipt["contract"] == c.CONTRACT and receipt["status"] == "S3_LIBRARY_PACKAGED" and
              receipt["new_emu_runs"] == 0 and receipt["stable_default_changed"] is False, "library receipt scope")
    g.require(set(receipt["artifacts"]) == ARTIFACTS, "library artifact inventory differs")
    for name, sha in receipt["artifacts"].items():
        g.require(g.sha(output / name) == sha, "library artifact drift: " + name)
    obj = (output / "gemv.o").read_bytes()
    g.require(e.digest(obj) == receipt["qualified_object_sha256"], "library qualified object identity differs")
    g.require(archive_member((output / "libconfig_reuse_gemv.a").read_bytes()) == obj and
              (output / "member-extract/stdout.log").read_bytes() == obj, "library member differs from qualified object")
    original, linked = g.ELF(obj), g.ELF((output / "consumer-linked.o").read_bytes())
    g.require("config_reuse_link_all" in linked.symbols and linked.symbols["config_reuse_link_all"][1] > 0 and
              "config_reuse_all_entries" in linked.symbols and linked.symbols["config_reuse_all_entries"][1] == 128,
              "linked C consumer or complete entry table missing")
    names = receipt["public_symbols"]
    g.require(len(names) == len(set(names)) == 16 and names == sorted(names) and
              all(n.startswith("config_reuse_gemv_") for n in names), "library public inventory")
    g.require({n for n in original.symbols if n.startswith("config_reuse_gemv_")} == set(names) and
              {n for n in linked.symbols if n.startswith("config_reuse_gemv_")} == set(names) and
              not any(n.startswith(("r4_gemv_", "firstdot_gemv_")) for n in original.symbols | linked.symbols),
              "library namespace collision")
    g.require((output / "consumer.c").read_text() == consumer(names), "library consumer differs")
    references = consumer_references(linked, names)
    functions = []
    for name in names:
        raw = original.symbol_data(name)
        g.require(linked.symbol_data(name) == raw, "consumer did not resolve qualified leaf: " + name)
        functions.append(dict(symbol=name, bytes=len(raw), sha256=e.digest(raw)))
    g.require(functions == receipt["functions"], "library leaf inventory differs")
    return dict(status="S3_LIBRARY_OBJECT_AND_CONSUMER_PASS", archive_sha256=g.sha(output / "libconfig_reuse_gemv.a"),
                object_sha256=e.digest(obj), header_sha256=g.sha(output / "gemv.h"), public_functions=16,
                archive_member_bytes=len(obj), linked_leaf_bytes_identical=True, new_emu_runs=0,
                linked_c_entry_relocations=references,
                performance_remeasured=False, stable_default_changed=False)


def build(repo, identity, build_dir, run, matrix, c_archive, output):
    parent, portable = ce.adapter(repo, identity, matrix)
    proof = parent.audit_archive(repo, c_archive, matrix)
    sealed = portable.Archive(c_archive)
    g.require(sealed.raw("build/gemv-reference.o") == (build_dir / "gemv-reference.o").read_bytes(), "library object differs from audited C archive")
    for name in ("gemv.S", "gemv.h"):
        g.require(sealed.raw("build/source/" + name) == (build_dir / "source" / name).read_bytes(), "library public source differs")
    app = c.adapter(repo, identity)
    app.verify_build(repo, build_dir)
    anchor = c.library_anchor(repo, build_dir, matrix)
    c.validate_qualification(build_dir, run, anchor)
    receipt = a.read(build_dir / "build.json")
    tools = receipt["toolchain"]
    for tool in tools.values():
        g.require(g.sha(tool["path"]) == tool["sha256"], "library toolchain differs from C qualification")
    output.mkdir(parents=True, exist_ok=False)
    for name in ("gemv.S", "gemv.h"):
        shutil.copyfile(build_dir / "source" / name, output / name)
    shutil.copyfile(build_dir / "gemv-reference.o", output / "gemv.o")
    names = sorted(r["api_symbol"] for r in a.read(build_dir / "source/manifest.json")["rows"])
    (output / "consumer.c").write_text(consumer(names))
    gcc, ar, ld = (tools[n]["path"] for n in ("gcc", "ar", "ld"))
    flags = ["-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-ffreestanding", "-O2"]
    commands = [
        ("archive-create", [ar, "rcsD", str(output / "libconfig_reuse_gemv.a"), str(output / "gemv.o")]),
        ("member-list", [ar, "t", str(output / "libconfig_reuse_gemv.a")]),
        ("member-extract", [ar, "p", str(output / "libconfig_reuse_gemv.a"), "gemv.o"]),
        ("consumer-compile", [gcc, *flags, "-I" + str(output), "-c", str(output / "consumer.c"), "-o", str(output / "consumer.o")]),
        ("consumer-link", [ld, "-r", "--no-relax", str(output / "consumer.o"), str(output / "libconfig_reuse_gemv.a"), "-o", str(output / "consumer-linked.o")]),
    ]
    results = [app.a.frozen_f.command(argv, repo, output / label) for label, argv in commands]
    g.require((output / "member-list/stdout.log").read_text() == "gemv.o\n", "GNU ar member list differs")
    obj = g.ELF((output / "gemv.o").read_bytes())
    data = dict(contract=c.CONTRACT, status="S3_LIBRARY_PACKAGED", build_root=str(output),
        source_root=str(repo), source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        library_builder_sha256=g.sha(Path(__file__)), qualified_object_sha256=g.sha(build_dir / "gemv-reference.o"),
        matrix_manifest_sha256=g.sha(matrix / "archive-manifest.json"), c_archive_manifest_sha256=sealed.manifest_sha256,
        c_archive_proof=proof, public_symbols=names, functions=[dict(symbol=n, bytes=len(obj.symbol_data(n)),
        sha256=e.digest(obj.symbol_data(n))) for n in names], artifacts={n: g.sha(output / n) for n in sorted(ARTIFACTS)},
        toolchain=tools, commands=results, new_emu_runs=0, stable_default_changed=False)
    g.save(output / "library.json", data)
    result = byte_check(output)
    g.save(output / "library-check.json", result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--action", choices=("build", "bytes"), required=True)
    p.add_argument("--identity", type=Path)
    p.add_argument("--matrix", type=Path)
    p.add_argument("--c-archive", type=Path)
    p.add_argument("--build", type=Path)
    p.add_argument("--run", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    g.require(repo == a.ROOT, "selected library checkout differs")
    if args.action == "build":
        g.require(all((args.identity, args.matrix, args.c_archive, args.build, args.run)) and not output.exists(), "qualified inputs and fresh library output required")
        identity = a.parent_identity(repo, args.identity.resolve())
        cfg = identity["configuration"]
        a.outside_inputs(output, [repo, args.identity.resolve().parent, args.matrix.resolve(), args.c_archive.resolve(),
            args.build.resolve(), args.run.resolve(), cfg["hardware_source"], cfg["build_record"], cfg["am_home"]])
        if os.name == "posix":
            os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
        result = build(repo, identity, args.build.resolve(), args.run.resolve(), args.matrix.resolve(), args.c_archive.resolve(), output)
    else:
        result = byte_check(output)
        g.require(a.read(output / "library-check.json") == result, "cached library check differs")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
