#!/usr/bin/env python3
"""Build and qualify the explicit C8 source/relocatable-link package (no EMU)."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CONTRACT = "current-c8-minimal-package-static-v1"
OBJECT_SHA = "f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3"
LIB = "libxs_gemv_c8.a"
SHAPES = ((4, 8), (8, 32), (16, 64), (4, 13))
NAMES = {f"config_reuse_gemv_{m}x{k}_{s}_{v}" for m, k in SHAPES
         for s in ("basic", "reuse") for v in ("vdot", "rvv")}
FLAGS = ["-std=c11", "-march=rv64gcv", "-mabi=lp64d", "-mno-relax",
         "-ffreestanding", "-O2", "-Werror=implicit-function-declaration"]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def archive_member(raw):
    """Bounded GNU ar parser, adapted from frozen r2-config-reuse/library.py."""
    require(raw.startswith(b"!<arch>\n"), "invalid GNU archive")
    offset, members = 8, {}
    while offset < len(raw):
        require(offset + 60 <= len(raw), "truncated archive header")
        header = raw[offset:offset + 60]
        require(header[-2:] == b"`\n", "archive member terminator")
        name = header[:16].decode("ascii").strip()
        size = int(header[48:58].decode("ascii").strip())
        offset += 60
        require(size >= 0 and offset + size <= len(raw), "archive member size")
        data = raw[offset:offset + size]
        offset += size
        if size % 2:
            require(raw[offset:offset + 1] == b"\n", "archive padding")
            offset += 1
        if name == "/":
            continue
        require(name == "gemv.o/" and not members, "unexpected archive member")
        members["gemv.o"] = data
    require(offset == len(raw) and set(members) == {"gemv.o"}, "archive membership")
    return members["gemv.o"]


def check_archive(path, expected):
    member = archive_member(Path(path).read_bytes())
    require(member == expected and digest(member) == OBJECT_SHA,
            "archive member differs from qualified complete object")
    return {"member": "gemv.o", "bytes": len(member), "sha256": digest(member)}


def expected_names(force):
    return ["config_reuse_gemv_8x32_reuse_" + ("rvv" if force else "vdot"),
            "config_reuse_gemv_8x32_reuse_rvv"]


def caller(force, aliases=True, includes=None, extra=()):
    names = ["xs_c8_gemv_8x32", "xs_c8_gemv_8x32_rvv"] if aliases else expected_names(force)
    lines = includes or ['#include "selected_gemv_c8.h"']
    return "\n".join([*lines, "_Static_assert(XS_C8_GEMV_API_VERSION == 1, \"C8 API\");",
        "typedef void (*entry_t)(const int8_t *, void *);",
        "entry_t const c8_entries[2] = {" + ",".join(names) + "};",
        *[f"void call_{i}(const int8_t *p, void *q) {{ {n}(p,q); }}" for i, n in enumerate(names)],
        *extra, ""])


def semantic_equal(candidate, authority):
    require(Path(candidate).read_bytes() == Path(authority).read_bytes(),
            "semantic caller mismatch against independent direct-callee oracle")


def references(elf, names):
    """Check exact table and real call relocations, including ordered duplicate RVV."""
    require(elf.kind == 1, "expected relocatable object")
    address, size, index, _ = elf.symbols["c8_entries"]
    require(size == 16, "two-entry table size")
    start = address - elf.sections[index][3]
    table, calls = {}, []
    for section in elf.sections:
        if section[1] != 4:
            continue
        require(section[9] == 24 and section[5] % 24 == 0, "RELA layout")
        symtab = elf.sections[section[6]]
        require(symtab[1] == 2 and symtab[9] == 24, "relocation symbol table")
        strings = elf.section(elf.sections[symtab[6]])
        for pos in range(section[4], section[4] + section[5], 24):
            offset, info, addend = struct.unpack_from("<QQq", elf.raw, pos)
            number, typ = info >> 32, info & 0xffffffff
            require(number < symtab[5] // 24, "relocation symbol bounds")
            string_offset = struct.unpack_from("<I", elf.raw, symtab[4] + 24 * number)[0]
            name = elf.string(strings, string_offset)
            if section[7] == index and start <= offset < start + size:
                require(typ == 2 and addend == 0 and offset not in table,
                        "pointer relocation differs")
                table[offset] = name
            if name.startswith("config_reuse_gemv_") and section[7] != index:
                require(typ in (18, 19) and addend == 0, "call relocation differs")
                calls.append(name)
    require(table == {start + 8 * i: n for i, n in enumerate(names)}, "table callee/order differs")
    require(sorted(calls) == sorted(names), "call relocation target/count differs")
    return {"pointer_relocations": 2, "call_relocations": 2, "targets": names}


def main(args):
    repo, identity, matrix, c8, out = [p.resolve() for p in
                                      (args.repo, args.identity, args.matrix, args.c8, args.output)]
    require(not out.exists(), "fresh output required")
    for protected in (repo, identity.parent, matrix, c8):
        require(not out.is_relative_to(protected) and not protected.is_relative_to(out),
                "output overlaps protected inputs")
    os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])
    out.mkdir(parents=True)
    state = {"contract": CONTRACT, "status": "RUNNING", "started": now(),
             "new_emu_runs": 0, "new_nemu_runs": 0, "stable_default_changed": False}
    save(out / "state.json", state)
    commands = []
    env = dict(os.environ)
    for key in ("CFLAGS", "CPPFLAGS", "CXXFLAGS", "ASFLAGS", "LDFLAGS", "CC_OPT",
                "MAKEFLAGS", "MFLAGS", "GCC_EXEC_PREFIX", "COMPILER_PATH", "LIBRARY_PATH",
                "CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "OBJC_INCLUDE_PATH",
                "DEPENDENCIES_OUTPUT", "SUNPRO_DEPENDENCIES"):
        env.pop(key, None)
    env.update(LC_ALL="C", LANG="C")

    def run(folder, label, argv, success=True, cwd=None, timeout=180):
        folder.mkdir(parents=True, exist_ok=True)
        require(not (folder / (label + ".command.json")).exists(), "fresh command receipt required")
        begin = now()
        proc = subprocess.run([str(x) for x in argv], cwd=cwd or out, env=env,
                              capture_output=True, timeout=timeout)
        for stream in ("stdout", "stderr"):
            (folder / (label + "." + stream + ".log")).write_bytes(getattr(proc, stream))
        receipt = {"command": [str(x) for x in argv], "cwd": str(cwd or out),
                   "started": begin, "finished": now(), "exit_code": proc.returncode,
                   "expected_success": success, "stdout_sha256": digest(proc.stdout),
                   "stderr_sha256": digest(proc.stderr)}
        save(folder / (label + ".command.json"), receipt)
        commands.append(str((folder / (label + ".command.json")).relative_to(out)))
        require((proc.returncode == 0) == success, "unexpected command result: " + str(folder / label))
        return proc.stdout

    try:
        import qualification
        run(out / "qualification-command", "audit", [sys.executable, "-B", HERE / "qualification.py",
            "--repo", repo, "--identity", identity, "--matrix", matrix, "--c8", c8,
            "--output", out / "qualification"], timeout=1800)
        binding = json.loads((out / "qualification/qualification.json").read_text())
        # The old parser is used as a parser, not to grant its old runtime qualification.
        sys.path.insert(0, str(repo / "team/optimizations/o2/r2-vector-accum"))
        import firstdot_gate as g
        g.bind(repo)
        source_pins = {str(p): sha(p) for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        for module in list(sys.modules.values()):
            file = getattr(module, "__file__", None)
            if file and Path(file).is_file() and Path(file).resolve().is_relative_to(repo):
                source_pins[str(Path(file).resolve())] = sha(file)
        tools = {n: shutil.which(args.cross_prefix + n) for n in ("gcc", "ld", "ar", "nm", "readelf")}
        tools["make"] = shutil.which("make")
        require(all(tools.values()), "missing GNU tool")
        versions = {}
        for n, file in tools.items():
            selected = Path(file)
            actual = dict(path=str(selected), link_text=os.readlink(selected) if selected.is_symlink() else None,
                          resolved_path=str(selected.resolve()), sha256=sha(selected))
            pinned = {k: v for k, v in binding["toolchain"][n].items() if k != "version"}
            require(actual == pinned, "selected tool differs from qualified toolchain: " + n)
            path = Path(file)
            versions[n] = {"path": str(path), "link": os.readlink(path) if path.is_symlink() else None,
                           "resolved": str(path.resolve()), "sha256": sha(path),
                           "version": run(out / "tools", n, [path, "--version"]).decode().splitlines()[0]}
        save(out / "tools.json", versions)
        sdk, authority = out / "sdk", out / "authority"
        run(out / "make", "build", [tools["make"], "-j1", "-f", HERE / "public/Makefile",
            "SOURCE_DIR=" + str(c8 / "qualified-public"), "OUT=" + str(sdk),
            "CROSS_COMPILE=" + args.cross_prefix])
        run(authority, "assemble", [tools["gcc"], "-march=rv64gcv", "-mabi=lp64d", "-mno-relax",
            "-c", c8 / "qualified-public/gemv.S", "-o", authority / "gemv.o"])
        obj = (authority / "gemv.o").read_bytes()
        require(digest(obj) == OBJECT_SHA and len(obj) == 27160, "independent object identity")
        require(obj == (sdk / "gemv.o").read_bytes() == (c8 / "build-01/gemv-reference.o").read_bytes(),
                "complete object rebuild differs")
        member = check_archive(sdk / LIB, obj)
        require(run(out / "archive", "list", [tools["ar"], "t", sdk / LIB]) == b"gemv.o\n", "ar member list")
        require(run(out / "archive", "extract", [tools["ar"], "p", sdk / LIB, "gemv.o"]) == obj,
                "GNU extracted member differs")
        run(authority, "archive", [tools["ar"], "rcsD", authority / LIB, authority / "gemv.o"])
        require((authority / LIB).read_bytes() == (sdk / LIB).read_bytes(), "archive not deterministic")
        public = g.ELF(obj)
        defined = {n for n, (_, size, index, _) in public.symbols.items() if size > 0 and index > 0}
        require(defined == NAMES, "16 public functions required")
        require(not any(n.startswith("xs_c8_") for n in public.symbols), "runtime C8 symbol")
        require(public.named[".text"][8] == 16, "text alignment")
        require(not any(s[1] in (4, 9) and s[5] for s in public.sections), "qualified object has relocations")
        require((sdk / "include/config_reuse_gemv.h").read_bytes() ==
                (c8 / "qualified-public/gemv.h").read_bytes(), "bottom header changed")
        require((sdk / "include/selected_gemv_c8.h").read_bytes() ==
                (HERE / "public/selected_gemv_c8.h").read_bytes(), "selected header changed")

        def compile_one(folder, source, include, defines=(), success=True, flags=FLAGS):
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "caller.c").write_text(source)
            run(folder, "compile", [tools["gcc"], *flags, *defines, "-I" + str(include),
                "-c", folder / "caller.c", "-o", folder / "caller.o"], success, cwd=folder)
            return folder / "caller.o"

        def undefined(folder, file, label="undefined"):
            text = run(folder, label, [tools["nm"], "-u", file]).decode()
            return {line.split()[-1] for line in text.splitlines() if line.strip()}

        def link_one(folder, file, library):
            linked = folder / "linked.o"
            run(folder, "link", [tools["ld"], "-r", "--no-relax", file, library, "-o", linked])
            require(not undefined(folder, linked, "linked-undefined"), "unresolved symbols after ld-r")
            return linked

        mode_checks = []
        for label, force, definitions in [
            ("default", False, ()), ("zero", False, ("-DXS_C8_GEMV_FORCE_RVV=0",)),
            ("one", True, ("-DXS_C8_GEMV_FORCE_RVV=1",)),
            ("expanded-one", True, ("-DC8_CHOICE=1", "-DXS_C8_GEMV_FORCE_RVV=C8_CHOICE"))]:
            d = out / "modes" / label
            a = compile_one(d / "alias", caller(force), sdk / "include", definitions)
            e = compile_one(d / "explicit", caller(force, False), sdk / "include", definitions)
            semantic_equal(a, e)
            require(undefined(d / "alias", a) == set(expected_names(force)), "unlinked alias targets")
            al = link_one(d / "alias", a, sdk / LIB)
            el = link_one(d / "explicit", e, sdk / LIB)
            semantic_equal(al, el)
            linked = g.ELF(al.read_bytes())
            refs = references(linked, expected_names(force))
            require(all(linked.symbol_data(n) == public.symbol_data(n) for n in NAMES),
                    "linked leaf bytes differ")
            require(not any(n.startswith("xs_c8_") and v[1] > 0 for n, v in linked.symbols.items()),
                    "runtime alias wrapper")
            mode_checks.append({"mode": label, "caller_sha256": sha(a), "linked_sha256": sha(al), **refs})

        negatives = []
        def reject(label, operation, paths=()):
            try:
                operation()
            except ValueError as exc:
                negatives.append({"case": label, "rejected": True, "reason": str(exc),
                    "candidate_rehashed": {str(p.relative_to(out)): sha(p) for p in paths}})
            else:
                raise ValueError("negative control accepted: " + label)

        for i, value in enumerate(("2", "-1", "", "(1)", "1+0", "true", "unknown", "01", "1U", "'1'")):
            compile_one(out / "negative" / ("macro-" + str(i)), caller(False), sdk / "include",
                        ("-DXS_C8_GEMV_FORCE_RVV=" + value,), success=False)
            negatives.append({"case": "invalid-macro-" + repr(value), "compiler_rejected": True})
        header_text = (sdk / "include/selected_gemv_c8.h").read_text()
        default_line = "#define xs_c8_gemv_8x32 config_reuse_gemv_8x32_reuse_vdot"
        rvv_line = "#define xs_c8_gemv_8x32_rvv config_reuse_gemv_8x32_reuse_rvv"
        mutations = [
            ("basic-selection", default_line, default_line.replace("reuse_vdot", "basic_vdot")),
            ("other-shape", default_line, default_line.replace("config_reuse_gemv_8x32", "config_reuse_gemv_4x8")),
            ("wrong-default-rvv", default_line, default_line.replace("reuse_vdot", "reuse_rvv")),
            ("wrong-explicit-rvv", rvv_line, rvv_line.replace("reuse_rvv", "reuse_vdot"))]
        for label, before, after in mutations:
            d = out / "negative" / label
            shutil.copytree(sdk / "include", d / "include")
            require(header_text.count(before) == 1, "mutation anchor missing")
            h = d / "include/selected_gemv_c8.h"
            h.write_text(header_text.replace(before, after))
            a = compile_one(d, caller(False), d / "include")
            reject(label, lambda: semantic_equal(a, out / "modes/default/explicit/caller.o"), (h, a))
        d = out / "negative/wrong-object"
        d.mkdir()
        bad = bytearray(obj)
        bad[public.named[".text"][4] + 8] ^= 1
        (d / "gemv.o").write_bytes(bad)
        run(d, "archive", [tools["ar"], "rcsD", d / LIB, d / "gemv.o"])
        reject("rehash-wrong-object", lambda: check_archive(d / LIB, obj), (d / "gemv.o", d / LIB))
        d = out / "negative/wrong-library"
        d.mkdir()
        run(d, "archive", [tools["ar"], "rcsD", d / "empty.a"])
        reject("wrong-library-unresolved", lambda: link_one(d, out / "modes/default/alias/caller.o", d / "empty.a"),
               (d / "empty.a",))
        d = out / "negative/missing-header"
        (d / "include").mkdir(parents=True)
        shutil.copyfile(sdk / "include/selected_gemv_c8.h", d / "include/selected_gemv_c8.h")
        example = (HERE / "public/example.c").read_text()
        compile_one(d, example, d / "include", success=False)
        negatives.append({"case": "missing-header", "compiler_rejected": True})
        # Coexistence is a compile-only link contract, never an all-shape runtime call.
        coexist = []
        for version in (1, 2):
            old = repo / "team/optimizations/o2/r2-select/public"
            if version == 2:
                old = old / "firstdot"
            dep = "firstdot_gemv.h" if version == 2 else "gemv.h"
            old_inc = out / "coexist-headers" / str(version)
            old_inc.mkdir(parents=True)
            source_pins[str(old / "selected_gemv.h")] = sha(old / "selected_gemv.h")
            shutil.copyfile(old / "selected_gemv.h", old_inc / "selected_gemv.h")
            # Qualified old public declaration bytes (not old code/runtime qualification).
            src = repo / ("team/optimizations/o2/r2-vector-accum/firstdot/public/gemv.h" if version == 2
                          else "team/optimizations/o2/r2-select/public/gemv.h")
            source_pins[str(src)] = sha(src)
            shutil.copyfile(src, old_inc / dep)
            for order in ("old-first", "c8-first"):
                for old_force in (0, 1):
                    for new_force in (0, 1):
                        d = out / "coexist" / f"v{version}-{order}-{old_force}-{new_force}"
                        lines = ['#include "' + str(old_inc / "selected_gemv.h") + '"',
                                 '#include "selected_gemv_c8.h"']
                        if order == "c8-first":
                            lines.reverse()
                        old_target = ("firstdot" if version == 2 else "r4") + "_gemv_8x32_reuse_" + ("rvv" if old_force else "vdot")
                        assertions = [f'_Static_assert(XS_GEMV_STABLE_API_VERSION == {version}, "old version");',
                                      f'_Static_assert(XS_GEMV_FORCE_RVV == {old_force}, "old macro");',
                                      f'_Static_assert(XS_C8_GEMV_FORCE_RVV == {new_force}, "C8 macro");']
                        alias_src = caller(new_force, True, lines, [*assertions,
                            "void old_call(const int8_t *p, void *q) { xs_gemv_8x32(p,q); }"])
                        explicit_src = caller(new_force, False, lines, [*assertions,
                            f"void old_call(const int8_t *p, void *q) {{ {old_target}(p,q); }}"])
                        defines = (f"-DXS_GEMV_FORCE_RVV={old_force}", f"-DXS_C8_GEMV_FORCE_RVV={new_force}")
                        a = compile_one(d / "alias", alias_src, sdk / "include", defines)
                        e = compile_one(d / "explicit", explicit_src, sdk / "include", defines)
                        semantic_equal(a, e)
                        require(undefined(d / "alias", a) == set(expected_names(new_force)) | {old_target},
                                "coexistence changed selection")
                        coexist.append({"case": d.name, "caller_sha256": sha(a)})

        # Move only SDK files outside repository; compile with no repository include/search paths.
        moved = out / "moved SDK"
        shutil.copytree(sdk, moved)
        moved_checks = []
        for force in (0, 1):
            d = out / "moved-example" / str(force)
            a = compile_one(d, (moved / "example.c").read_text(), moved / "include",
                            (f"-DXS_C8_GEMV_FORCE_RVV={force}",),
                            flags=[*FLAGS, "-fno-builtin", "-fno-pic", "-fno-pie", "-fno-stack-protector"])
            linked = link_one(d, a, moved / LIB)
            require(undefined(d, a) == set(expected_names(force)), "moved example target mismatch")
            moved_checks.append({"force_rvv": force, "caller_sha256": sha(a), "linked_sha256": sha(linked),
                                 "runtime": "NOT_TESTED"})

        for file, expected in source_pins.items():
            require(sha(file) == expected, "checker/source changed during validation: " + file)
        for item in versions.values():
            path = Path(item["path"])
            require(sha(path) == item["sha256"] and str(path.resolve()) == item["resolved"] and
                    (os.readlink(path) if path.is_symlink() else None) == item["link"], "toolchain changed")
        manifest = {"contract": CONTRACT, "api_version": 1, "status": "STATIC_PACKAGE_QUALIFIED",
                    "object": member, "files": {str(p.relative_to(sdk)): sha(p) for p in sdk.rglob("*") if p.is_file()},
                    "qualified_runtime_references": ["CONFIG-REUSE-MATRIX-DIVFIX0F-CLEAN02-20261027-01",
                        "CONFIG-REUSE-C8-DIVFIX0F-CLEAN02-20261027-02"],
                    "new_example_runtime": "NOT_TESTED", "new_performance": "NOT_TESTED",
                    "runtime_support": "Explicit current0f, VLEN=128, ordinary RV64/lp64d, VS enabled",
                    "stable_default_changed": False}
        save(sdk / "manifest.json", manifest)
        # Manifest copied only after qualification, compare entire SDK after the final copy.
        shutil.copyfile(sdk / "manifest.json", moved / "manifest.json")
        require({str(p.relative_to(sdk)): sha(p) for p in sdk.rglob("*") if p.is_file()} ==
                {str(p.relative_to(moved)): sha(p) for p in moved.rglob("*") if p.is_file()}, "moved SDK changed")
        save(out / "source-inputs.json", source_pins)
        report = {**state, "status": "CURRENT_C8_MINIMAL_PACKAGE_STATIC_PASS", "finished": now(),
                  "qualification": binding, "independent_object": member, "defined_functions": 16,
                  "runtime_wrapper_symbols": 0, "alias_modes": mode_checks, "coexistence": coexist,
                  "negative_controls": negatives, "moved_examples": moved_checks,
                  "sdk": str(sdk), "sdk_manifest_sha256": sha(sdk / "manifest.json"),
                  "toolchain": versions, "command_receipts": commands,
                  "new_example_runtime": "NOT_TESTED", "new_final_elf": "NOT_TESTED",
                  "new_performance": "NOT_TESTED", "new_ppa": "NOT_TESTED",
                  "scope": "New source aliases, complete archive, tested callers and relocatable links; prior runtime evidence explicitly reused."}
        save(out / "report.json", report)
        state.update(status=report["status"], finished=report["finished"], report_sha256=sha(out / "report.json"))
        save(out / "state.json", state)
        print(json.dumps({"status": report["status"], "commands": len(commands), "negatives": len(negatives),
                          "coexistence_cases": len(coexist), "new_emu_runs": 0}))
        return report
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc), finished=now())
        save(out / "state.json", state)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "identity", "matrix", "c8", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--cross-prefix", default="/usr/bin/riscv64-linux-gnu-")
    main(parser.parse_args())
