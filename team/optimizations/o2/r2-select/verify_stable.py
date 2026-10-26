"""Verify the stable C aliases/library against qualified T17 source and evidence.

Real GNU builds compare all eight aliases with explicit existing symbols under
default/explicit FORCE_RVV modes. This proves source-level alias/build equivalence; it does
not measure a new application's cycles or execute EMU/NEMU.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

REL = Path("team/optimizations/o2/r2-select")
CONTRACT = "r5-selected-gemv-v1"
SHAPES = ((4, 8), (8, 32), (16, 64), (4, 13))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    Path(path).write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())


def now():
    return datetime.now(timezone.utc).isoformat()


def main(args):
    require(os.name == "posix", "GNU qualification requires Linux/WSL")
    repo, output = args.repo.resolve(), args.output.resolve()
    require(not output.exists() and not output.is_relative_to(repo), "new output must be outside source snapshot")
    require(not any(c.isspace() for c in str(output)) and re.fullmatch(r"[A-Za-z0-9_./-]+", args.cross_prefix),
            "use a whitespace-free output and plain toolchain prefix")
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    manifest_path = repo / REL / "STABLE_MANIFEST.json"
    manifest_sha256 = sha(manifest_path)
    manifest = read(manifest_path)
    require(manifest["contract"] == CONTRACT and manifest["qualified_base_commit"] ==
            "666fc80edebd50f7b3d6fb13cf0eb24d526e02d9", "stable manifest contract/base")
    selected = manifest["selection"]
    require([tuple(row["shape"]) for row in selected] == list(SHAPES), "stable shape inventory")
    pinned = dict(manifest["source_sha256"])
    for entry in manifest["qualification"].values():
        require(entry["path"] not in pinned, "duplicate evidence/source path")
        pinned[entry["path"]] = entry["sha256"]
    for relative, digest in pinned.items():
        path = (repo / relative).resolve()
        require(path.is_relative_to(repo) and not (repo / relative).is_symlink() and sha(path) == digest,
                "stable source/evidence identity: " + relative)
    q = lambda name: read(repo / manifest["qualification"][name]["path"])
    identity, acceptance = q("identity"), q("acceptance")
    matrix, c_audit = q("matrix_audit"), q("c_audit")
    require(acceptance["status"] == "T17_CLEAN_REPRODUCTION_PASS" and
            acceptance["identity_sha256"] == manifest["qualification"]["identity"]["sha256"] and
            acceptance["emu_sha256"] == manifest["hardware"]["emu_sha256"] == identity["hardware_profile"]["emu_sha256"] and
            acceptance["reference_sha256"] == manifest["hardware"]["reference_sha256"] == identity["reference_sha256"] and
            acceptance["source_commit"] == manifest["hardware"]["source_commit"] == identity["source_commit"], "T17 qualification identity")
    require(matrix["software_gate_result"]["status"] == "R4_ENTRY_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS" and
            matrix["software_gate_result"]["archive"]["archive_manifest_sha256"] == acceptance["archives"]["matrix"]["archive_manifest_sha256"] and
            c_audit["software_gate_result"]["status"] == "R4_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS" and
            c_audit["software_gate_result"]["archive"]["archive_manifest_sha256"] == manifest["qualification"]["c_manifest"]["sha256"] ==
            acceptance["archives"]["ordinary_c"]["archive_manifest_sha256"] and
            c_audit["software_gate_result"]["matrix_manifest_sha256"] == acceptance["archives"]["matrix"]["archive_manifest_sha256"],
            "qualified matrix/C evidence")
    require(all(report["identity_sha256"] == manifest["qualification"]["identity"]["sha256"] and
                report["emu_sha256"] == manifest["hardware"]["emu_sha256"] for report in (matrix, c_audit)), "audit hardware identity")
    rows = {tuple(row["shape"]): row for row in matrix["software_gate_result"]["rows"]}
    for item in selected:
        shape = tuple(item["shape"])
        row = rows[shape]
        best = min(row["candidates"], key=lambda v: (v["total"], v["method"] != "rvv"))
        fallback = row["fastest_rvv"]
        stem = "r4_gemv_%dx%d_" % shape
        require(best["variant"] == fallback["variant"] == "s1" and best["software"] == fallback["software"] == "reuse" and
                best["samples"] == fallback["samples"] == 12 and
                item["default_symbol"] == stem + "reuse_" + best["method"] and
                item["rvv_symbol"] == stem + "reuse_rvv" and item["default_cycles"] == best["mean"] and
                item["rvv_cycles"] == fallback["mean"] and item["alias"] == "xs_gemv_%dx%d" % shape,
                "stable choice differs from strongest qualified comparison")
    c_manifest = q("c_manifest")
    reference = manifest["library"]["qualified_reference_object"]
    record = next(r for r in c_manifest["files"] if r["stored"] == reference["stored"])
    require(record["raw_sha256"] == reference["sha256"], "qualified C object identity")
    stored = repo / Path(manifest["qualification"]["c_manifest"]["path"]).parent / record["stored"]
    require(sha(stored) == record["stored_sha256"], "qualified object stored hash")
    body = gzip.decompress(stored.read_bytes()) if record["encoding"] == "gzip" else stored.read_bytes()
    require(hashlib.sha256(body).hexdigest() == reference["sha256"] and len(body) == record["raw_bytes"], "qualified object raw hash")
    output.mkdir(parents=True)
    (output / "qualified-gemv-reference.o").write_bytes(body)
    started = now()
    save(output / "state.json", dict(status="R5_STABLE_BUILD_RUNNING", contract=CONTRACT, started=started, new_emu_runs=0))
    tools = {name: shutil.which(args.cross_prefix + name) for name in ("gcc", "ar", "nm", "objcopy", "ld", "readelf")}
    tools["make"] = shutil.which("make")
    require(all(tools.values()), "missing GNU tools")

    def run(directory, label, command, expect_success=True):
        directory.mkdir(parents=True, exist_ok=True)
        before = now()
        result = subprocess.run(command, cwd=repo, capture_output=True, timeout=180)
        (directory / (label + ".stdout.log")).write_bytes(result.stdout)
        (directory / (label + ".stderr.log")).write_bytes(result.stderr)
        save(directory / (label + ".command.json"), dict(command=command, cwd=str(repo), started=before,
             finished=now(), exit_code=result.returncode, stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
             stderr_sha256=hashlib.sha256(result.stderr).hexdigest()))
        require((result.returncode == 0) == expect_success, "unexpected GNU command outcome: " + label)
        return result.stdout

    versions = {name: dict(path=path, sha256=sha(path), version=run(output / "tools", name, [path, "--version"]).decode().splitlines()[0])
                for name, path in tools.items()}
    public = repo / REL / "public"
    library = output / "library"
    run(output, "make-library", [tools["make"], "-C", str(public), "OUT=" + str(library),
                                 "CROSS_COMPILE=" + args.cross_prefix, "-j1", "all"])
    require((library / "gemv.o").read_bytes() == body,
            "whole library object differs from qualified C02 (including sections/relocations/metadata)")
    require(run(output, "archive-member", [tools["ar"], "p", str(library / "libxs_gemv.a"), "gemv.o"]) ==
            (library / "gemv.o").read_bytes(), "archive member differs from assembled library")
    defined = run(output, "library-symbols", [tools["nm"], "-n", "-S", "-g", "--defined-only", str(library / "gemv.o")])
    qualified = run(output, "qualified-symbols", [tools["nm"], "-n", "-S", "-g", "--defined-only", str(output / "qualified-gemv-reference.o")])
    expected = {"r4_gemv_%dx%d_%s_%s" % (*shape, software, method) for shape in SHAPES
                for software in ("basic", "reuse") for method in ("vdot", "rvv")}
    require({line.split()[-1].decode() for line in defined.splitlines()} == expected and defined == qualified,
            "qualified public symbol inventory/offsets/sizes differ")
    symbol_tables = []
    for name, source in (("library", library / "gemv.o"), ("qualified", output / "qualified-gemv-reference.o")):
        table = run(output, name + "-elf-symbols", [tools["readelf"], "--wide", "--syms", str(source)])
        symbols = {}
        for line in table.decode().splitlines():
            fields = line.split()
            if len(fields) == 8 and fields[-1] in expected:
                require(fields[3:6] == ["FUNC", "GLOBAL", "DEFAULT"], "public function type/binding/visibility")
                symbols[fields[-1]] = fields[1:6]
        require(set(symbols) == expected, "ELF public symbol inventory")
        symbol_tables.append(symbols)
        run(output, name + "-text", [tools["objcopy"], "-O", "binary", "--only-section=.text", str(source),
                                      str(output / (name + ".text.bin"))])
    require(symbol_tables[0] == symbol_tables[1], "qualified ELF function metadata differs")
    require((output / "library.text.bin").read_bytes() == (output / "qualified.text.bin").read_bytes(), "qualified library text differs")

    def mode(force):
        directory = output / ("force-rvv-" + ("default" if force is None else str(force)))
        wanted = set()
        for kind in ("alias", "explicit"):
            target = directory / kind
            target.mkdir(parents=True)
            lines = ['#include "' + ("selected_gemv.h" if kind == "alias" else "gemv.h") + '"']
            for row in selected:
                for fallback in (False, True):
                    symbol = row["rvv_symbol"] if force or fallback else row["default_symbol"]
                    wanted.add(symbol)
                    name = row["alias"] + ("_rvv" if fallback else "") if kind == "alias" else symbol
                    function = "call_%dx%d_%s" % (*row["shape"], "rvv" if fallback else "default")
                    lines.append("void %s(const int8_t *a, void *b) { %s(a, b); }" % (function, name))
            (target / "caller.c").write_text("\n".join(lines) + "\n")
            command = [tools["gcc"], "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-ffreestanding", "-O2",
                 "-g0", "-fno-pic", "-fno-pie", "-fno-asynchronous-unwind-tables", "-fno-tree-vectorize", "-I" + str(public),
                 "-c", str(target / "caller.c"), "-o", str(target / "caller.o")]
            if force is not None:
                command.insert(1, "-DXS_GEMV_FORCE_RVV=" + str(force))
            run(target, "compile", command)
            run(target, "link", [tools["ld"], "-r", "--no-relax", str(target / "caller.o"), str(library / "libxs_gemv.a"),
                                  "-o", str(target / "linked.o")])
            require(not run(target, "linked-undefined", [tools["nm"], "-u", str(target / "linked.o")]).strip(), "unresolved stable link")
        require(all((directory / "alias" / n).read_bytes() == (directory / "explicit" / n).read_bytes()
                    for n in ("caller.o", "linked.o")), "aliases changed code, relocations or linked object")
        undefined = run(directory, "caller-undefined", [tools["nm"], "-u", str(directory / "alias/caller.o")])
        require({line.split()[-1].decode() for line in undefined.splitlines()} == wanted and len(wanted) == (4 if force else 7),
                "caller target inventory")
        return dict(force_rvv=force, aliases_checked=8, unique_targets=sorted(wanted), caller_sha256=sha(directory / "alias/caller.o"),
                    linked_sha256=sha(directory / "alias/linked.o"), whole_objects_identical=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        modes = list(pool.map(mode, (None, 0, 1)))
    require(modes[0]["caller_sha256"] == modes[1]["caller_sha256"] and
            modes[0]["linked_sha256"] == modes[1]["linked_sha256"], "undefined/explicit-zero mode differs")
    invalid = output / "invalid-configurations"
    invalid.mkdir()
    (invalid / "caller.c").write_text('#include "selected_gemv.h"\n')
    rejected = ["2", "-1", "true", "0+1", "true && true", "0||1", "00"]
    for index, value in enumerate(rejected):
        run(invalid, "reject-" + str(index), [tools["gcc"], "-march=rv64gcv", "-mabi=lp64d", "-ffreestanding",
            "-I" + str(public), "-DXS_GEMV_FORCE_RVV=" + value, "-fsyntax-only", str(invalid / "caller.c")], expect_success=False)
    require(sha(manifest_path) == manifest_sha256 and all(sha(repo / path) == digest for path, digest in pinned.items()) and
            sha(stored) == record["stored_sha256"],
            "stable inputs changed during verification")
    result = dict(status="R5_STABLE_SOURCE_ALIAS_BUILD_PASS", contract=CONTRACT, started=started, finished=now(),
                  manifest_sha256=manifest_sha256, verifier_sha256=sha(__file__), input_sha256=pinned,
                  qualified_reference_sha256=reference["sha256"], public_function_count=16,
                  library_object_sha256=sha(library / "gemv.o"), whole_library_object_identical=True,
                  library_text_sha256=sha(output / "library.text.bin"), library_archive_sha256=sha(library / "libxs_gemv.a"),
                  modes=modes, invalid_configurations_rejected=rejected, tools=versions,
                  cpu_affinity=sorted(os.sched_getaffinity(0)), parallel_mode_workers=2,
                  new_emu_runs=0, new_nemu_runs=0, new_application_performance_qualified=False,
                  scope="Compile-time C aliases and default library build only; whole library object equals qualified C02 and alias/explicit caller/link objects are identical.")
    save(output / "result.json", result)
    save(output / "state.json", dict(status=result["status"], started=started, finished=result["finished"], new_emu_runs=0))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cross-prefix", default="riscv64-linux-gnu-")
    print(json.dumps(main(parser.parse_args()), indent=2))
