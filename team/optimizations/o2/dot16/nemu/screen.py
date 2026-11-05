#!/usr/bin/env python3
"""Bounded, single-CPU host validation; never builds NEMU or its real API.

Copies exactly five manifest-pinned base files into a fresh partial tree, applies
the frozen legacy patch then the candidate, and compiles the actual helper text.
Every invocation preserves a new run directory, including any failed run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

BASE_FILES = {
    "src/isa/riscv64/Kconfig",
    "src/isa/riscv64/include/isa-all-instr.h",
    "src/isa/riscv64/instr/decode.c",
    "src/isa/riscv64/instr/rvv/exec.h",
    "src/isa/riscv64/system/intr.c",
}
OLD_HELPERS = {
    "src/isa/riscv64/instr/rvv/vdot.h",
    "src/isa/riscv64/local-include/vdot_tval.h",
}
NEW_HELPERS = {
    "src/isa/riscv64/instr/rvv/vdot16.h",
    "src/isa/riscv64/local-include/vdot16_tval.h",
}
NOT_TESTED = [
    "Real NEMU ABI, CSR union layout, reference API, or shared-library loading",
    "Actual NEMU instruction dispatch, Kconfig-generated build, or interpreter execution",
    "Real trap entry and its normal exception CSR / privilege / PC effects",
    "Whole-core XiangShan RTL, DiffTest, performance, or synthesis/timing",
    "Candidate xTVAL policy against a new hardware decode/FU/TrapInstMod path",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_tree(tree: Path, expected: dict[str, str]) -> dict[str, str]:
    actual = {}
    for rel, digest in sorted(expected.items()):
        require(not Path(rel).is_absolute() and ".." not in Path(rel).parts,
                f"unsafe manifest path: {rel}")
        actual[rel] = sha(tree / rel)
        require(actual[rel] == digest, f"source SHA mismatch: {rel}")
    return actual


def command(argv: list[str], cwd: Path, run: Path, name: str,
            records: list[dict], expect_success: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    env["GIT_CEILING_DIRECTORIES"] = str(cwd.parent)
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    start = time.monotonic()
    done = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=45, check=False)
    (run / f"{name}.stdout.log").write_text(done.stdout)
    (run / f"{name}.stderr.log").write_text(done.stderr)
    records.append({"name": name, "argv": argv, "cwd": str(cwd),
                    "returncode": done.returncode,
                    "seconds": round(time.monotonic() - start, 6)})
    if expect_success:
        require(done.returncode == 0, f"{name} failed; preserved stdout/stderr logs")
    return done


def decoder_screen(path: Path) -> dict:
    source = path.read_text()
    found = re.findall(r'def_INSTR_IDTAB\(\s*"([01? ]+)"\s*,\s*R\s*,\s*(vdot16|vdot)\s*\)', source)
    require(len(found) == 2, "expected exactly one dot8 and one dot16 exact R pattern")
    result = {}
    for text, name in found:
        bits = text.replace(" ", "")
        require(len(bits) == 32, f"bad decoder pattern width: {name}")
        mask = int("".join("0" if c == "?" else "1" for c in bits), 2)
        match = int(bits.replace("?", "0"), 2)
        expected = 0x0200000B if name == "vdot" else 0x0E00000B
        require((match, mask) == (expected, 0xFE00707F), f"wrong exact decode: {name}")
        for vd in range(32):
            for vs1 in range(32):
                for vs2 in range(32):
                    word = match | (vd << 7) | (vs1 << 15) | (vs2 << 20)
                    require(word & mask == match, f"operand bits alter match: {name}")
        neighbors = []
        for bit in range(32):
            if mask & (1 << bit):
                neighbor = match ^ (1 << bit)
                require(neighbor & mask != match, f"fixed-bit neighbor accepted: {name}/{bit}")
                neighbors.append({"bit": bit, "word": f"0x{neighbor:08x}"})
        result[name] = {"pattern": text, "match": f"0x{match:08x}",
                        "mask": f"0x{mask:08x}", "operand_assignments": 32768,
                        "fixed_bit_neighbors_rejected_by_this_pattern": neighbors}
    require(0x0200000B & 0xFE00707F != 0x0E00000B, "opcodes overlap")
    result["scope"] = "Static actual-pattern matching only; neighbors may decode as other instructions."
    return result


def config_screen(tree: Path, run: Path, commands: list[dict]) -> dict:
    source = (tree / "src/isa/riscv64/Kconfig").read_text()
    blocks = {}
    for name in ("CUSTOM_VDOT", "CUSTOM_VDOT_XS_TVAL", "CUSTOM_VDOT16", "CUSTOM_VDOT16_XS_TVAL"):
        match = re.search(r"(?m)^config " + name + r"\n(.*?)(?=^config |\Z)", source, re.S | re.M)
        require(match is not None, f"missing Kconfig option {name}")
        text = match.group(1)
        require(re.search(r"(?m)^\s+default n\s*$", text) is not None,
                f"option is not default-off: {name}")
        blocks[name] = {"default": "n", "depends": re.findall(r"(?m)^\s+depends on (.+)$", text)}
    require(blocks["CUSTOM_VDOT16"]["depends"] == ["RVV && CUSTOM_VDOT"],
            "unexpected dot16 dependency")
    require(blocks["CUSTOM_VDOT16_XS_TVAL"]["depends"] == ["CUSTOM_VDOT16"],
            "unexpected dot16 platform dependency")

    # Preprocess only actual custom-pattern lines and surrounding preprocessor
    # directives. This checks feature guards without claiming a decoder build.
    decode_lines = (tree / "src/isa/riscv64/instr/decode.c").read_text().splitlines()
    slice_lines = []
    for line in decode_lines:
        if re.match(r"\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b", line):
            slice_lines.append(line)
        elif re.search(r",\s*vdot(?:16)?\s*\);", line):
            slice_lines.append(line)
    probe = run / "decode_guards.c"
    probe.write_text("\n".join(slice_lines) + "\n")
    modes = {
        "rvv_off": (["CONFIG_CUSTOM_VDOT", "CONFIG_CUSTOM_VDOT16"], set()),
        "custom_off": (["CONFIG_RVV"], set()),
        "dot8_only": (["CONFIG_RVV", "CONFIG_CUSTOM_VDOT"], {"vdot"}),
        "both": (["CONFIG_RVV", "CONFIG_CUSTOM_VDOT", "CONFIG_CUSTOM_VDOT16"], {"vdot", "vdot16"}),
    }
    guard_results = {}
    for mode, (defines, expected) in modes.items():
        done = command(["gcc", "-E", "-P", "-x", "c", *["-D" + d for d in defines], str(probe)],
                       run, run, f"decode-guards-{mode}", commands)
        present = set(re.findall(r",\s*(vdot16|vdot)\s*\);", done.stdout))
        require(present == expected, f"wrong actual decoder guards in {mode}")
        guard_results[mode] = sorted(present)
    return {"kconfig": blocks, "actual_decode_guard_slice": guard_results,
            "scope": "Configuration text and preprocessor stubs; not a Kconfig-generated NEMU build."}


def build_probe(tree: Path, host_source: Path, run: Path, name: str,
                defines: list[str], commands: list[dict], override: Path | None = None) -> Path:
    exe = run / name
    includes = (["-I", str(override)] if override is not None else [])
    flags = ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
             "-fsanitize=undefined", "-fno-sanitize-recover=undefined", "-fno-omit-frame-pointer"]
    command(["gcc", *flags, *["-D" + d for d in defines], *includes,
             "-I", str(tree / "src/isa/riscv64/instr/rvv"), str(host_source), "-o", str(exe)],
            run, run, name + "-compile", commands)
    return exe


def write_results(run: Path, result: dict) -> None:
    (run / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    lines = ["# dot16 NEMU host auxiliary screen", "", f"Status: **{result['status']}**", "",
             "This is a single-CPU host stub screen of actual patched helper text, not NEMU execution.", "",
             f"Started: {result['started_utc']}; ended: {result['ended_utc']}.",
             f"Elapsed: {result['elapsed_seconds']:.3f} seconds.", ""]
    if "error" in result:
        lines.extend(["## Failure", "", result["error"], ""])
    if "host_probes" in result:
        lines.extend(["## Executed host cases", "", "| Configuration | dot8 legal / illegal | dot16 legal / illegal |", "| --- | ---: | ---: |"])
        for name, data in result["host_probes"].items():
            a, b = data["dot8"], data["dot16"]
            lines.append(f"| {name} | {a['legal']} / {a['illegal']} | {b['legal']} / {b['illegal']} |")
        lines.extend(["", "Each enabled instruction covers 32³ register assignments × four vta/vma policies.",
                      "The oracle uses int8_t byte snapshots and an int64_t scalar accumulation.", ""])
    if "negative_controls" in result:
        lines.extend(["## Temporary negative controls", ""])
        for name, data in result["negative_controls"].items():
            lines.append(f"- {name}: rejected at `{data['case']}` ({data['reason']}).")
        lines.append("")
    lines.extend(["## NOT_TESTED", "", *["- " + item for item in NOT_TESTED], "",
                  "The exception stub checks helper effects only: it does not model the valid trap-entry CSR updates.",
                  "Fixed-bit neighbors fail their target pattern; this is not a claim that every neighbor traps in a whole core.", "",
                  "Identity checks, exact commands, per-process logs, partial patched tree, and mutated copies remain beside this report.", ""])
    (run / "SUMMARY.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-source", required=True, type=Path)
    parser.add_argument("--legacy-patch", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    base, legacy, out = args.base_source.resolve(), args.legacy_patch.resolve(), args.out.resolve()
    candidate = Path(__file__).resolve().parent
    input_roots = (base, candidate, legacy.parent)
    require(all(not (out.is_relative_to(root) or root.is_relative_to(out))
                for root in input_roots),
            "output must not contain or be contained in any input root")
    out.mkdir(parents=True, exist_ok=True)
    number = 1
    while True:
        run = out / f"run-{number:03d}"
        try:
            run.mkdir()
            break
        except FileExistsError:
            number += 1
    start = time.monotonic()
    result = {"status": "FAIL", "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "run_dir": str(run), "commands": [], "not_tested": NOT_TESTED,
              "platform": platform.platform()}
    try:
        require(hasattr(os, "sched_getaffinity") and hasattr(os, "sched_setaffinity"),
                "this screen requires Linux CPU affinity for its one-CPU budget")
        selected_cpu = min(os.sched_getaffinity(0))
        os.sched_setaffinity(0, {selected_cpu})
        result["cpu_affinity"] = sorted(os.sched_getaffinity(0))
        commands = result["commands"]
        manifest_path = candidate / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        patch = candidate / manifest["patch_file"]
        host_source = candidate / "host_probe.c"
        require(set(manifest["base_source_sha256"]) == BASE_FILES, "manifest must pin exactly five base files")
        require(set(manifest["legacy_patched_source_sha256"]) == BASE_FILES | OLD_HELPERS,
                "manifest must pin exactly seven legacy-stage files")
        require(set(manifest["patched_source_sha256"]) == BASE_FILES | OLD_HELPERS | NEW_HELPERS,
                "manifest must pin exactly nine candidate-stage files")
        require(set(manifest["unchanged_legacy_helpers"]) == OLD_HELPERS,
                "both old helpers must be explicitly preserved")
        require(sha(legacy) == manifest["required_legacy_patch_sha256"], "legacy patch SHA mismatch")
        require(sha(patch) == manifest["patch_sha256"], "candidate patch SHA mismatch")
        legacy_manifest_path = legacy.parent / "manifest.json"
        old_manifest = json.loads(legacy_manifest_path.read_text())
        require(old_manifest["patch_sha256"] == manifest["required_legacy_patch_sha256"] and
                old_manifest["patch_version"] == manifest["required_legacy_patch_version"] and
                old_manifest["base_rev"] == manifest["base_rev"] and
                old_manifest["patched_source_sha256"] == manifest["legacy_patched_source_sha256"],
                "legacy manifest does not agree with candidate prerequisites")
        result["identities"] = {"base_rev_declared_not_git_object_verified": manifest["base_rev"],
                                "legacy_patch_sha256": sha(legacy), "patch_sha256": sha(patch),
                                "manifest_sha256": sha(manifest_path), "host_probe_sha256": sha(host_source),
                                "screen_sha256": sha(Path(__file__)),
                                "legacy_manifest_sha256": sha(legacy_manifest_path)}
        snapshots = run / "input-snapshots"
        snapshots.mkdir()
        for original, name in ((manifest_path, "manifest.json"), (patch, "candidate.patch"),
                               (legacy, "legacy.patch"), (legacy_manifest_path, "legacy-manifest.json")):
            shutil.copyfile(original, snapshots / name)
        validation_sources = run / "validation-sources"
        validation_sources.mkdir()
        for original in (host_source, Path(__file__).resolve()):
            shutil.copyfile(original, validation_sources / original.name)
        host_source = validation_sources / "host_probe.c"
        result["base_source_sha256"] = verify_tree(base, manifest["base_source_sha256"])
        tree = run / "partial-source"
        tree.mkdir()
        for rel in sorted(BASE_FILES):
            target = tree / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(base / rel, target)
        for name, current_patch in (("legacy", legacy), ("candidate", patch)):
            command(["git", "apply", "--check", "--whitespace=error", str(current_patch)],
                    tree, run, name + "-apply-check", commands)
            command(["git", "apply", "--whitespace=error", str(current_patch)],
                    tree, run, name + "-apply", commands)
            if name == "legacy":
                result["legacy_source_sha256"] = verify_tree(tree, manifest["legacy_patched_source_sha256"])
                legacy_helper_bytes = {rel: (tree / rel).read_bytes() for rel in OLD_HELPERS}
            else:
                result["candidate_source_sha256"] = verify_tree(tree, manifest["patched_source_sha256"])
                require(all((tree / rel).read_bytes() == blob for rel, blob in legacy_helper_bytes.items()),
                        "candidate changed a frozen legacy helper")
                result["legacy_helpers_byte_identical"] = sorted(OLD_HELPERS)
        require({str(p.relative_to(tree)) for p in tree.rglob("*") if p.is_file()} ==
                BASE_FILES | OLD_HELPERS | NEW_HELPERS, "unexpected file in partial tree")
        result["decode"] = decoder_screen(tree / "src/isa/riscv64/instr/decode.c")
        result["configuration"] = config_screen(tree, run, commands)
        version = command(["gcc", "--version"], run, run, "gcc-version", commands)
        result["compiler"] = version.stdout.splitlines()[0]
        result["host_probes"] = {}
        modes = {"both_off": [], "dot8_only": ["CONFIG_CUSTOM_VDOT"],
                 "both_enabled": ["CONFIG_CUSTOM_VDOT", "CONFIG_CUSTOM_VDOT16"]}
        for name, defines in modes.items():
            exe = build_probe(tree, host_source, run, "host-" + name, defines, commands)
            done = command([str(exe)], run, run, "host-" + name + "-run", commands)
            data = json.loads(done.stdout)
            require(data["status"] == "PASS", f"host probe rejected {name}")
            for kind, enabled in (("dot8", "CONFIG_CUSTOM_VDOT" in defines),
                                  ("dot16", "CONFIG_CUSTOM_VDOT16" in defines)):
                require(data[kind]["aliases"] == (32768 * 4 if enabled else 0),
                        f"alias matrix incomplete: {name}/{kind}")
                require(data[kind]["illegal"] == (1408 if enabled else 0),
                        f"illegal matrix incomplete: {name}/{kind}")
            result["host_probes"][name] = data
        header = tree / "src/isa/riscv64/instr/rvv/vdot16.h"
        original = header.read_text()
        mutants = {
            "drop_high_half": ("i < 16", "i < 8", "single_lane"),
            "wrong_negative_sign_extension": ("cpu.vr[vd]._64[0] = (uint32_t)sum;",
                                                "cpu.vr[vd]._64[0] = (int64_t)sum;", "single_lane"),
            "omit_VL_check": ("vl->val != 16 || ", "", "illegal_VL"),
        }
        result["negative_controls"] = {}
        for name, (needle, replacement, expected_case) in mutants.items():
            require(original.count(needle) == 1, f"negative-control edit anchor is not unique: {name}")
            mutant_dir = run / "negative-controls" / name
            mutant_dir.mkdir(parents=True)
            mutated = mutant_dir / "vdot16.h"
            mutated.write_text(original.replace(needle, replacement))
            exe = build_probe(tree, host_source, run, "mutant-" + name,
                              modes["both_enabled"], commands, override=mutant_dir)
            done = command([str(exe)], run, run, "mutant-" + name + "-run", commands, expect_success=False)
            require(done.returncode == 1, f"negative control was not rejected by assertions: {name}")
            data = json.loads(done.stdout)
            require(data["status"] == "FAIL" and data["lanes"] == 16 and data["case"] == expected_case,
                    f"negative control rejected for an unexpected reason: {name}")
            data["mutated_header_sha256"] = sha(mutated)
            result["negative_controls"][name] = data
        verify_tree(base, manifest["base_source_sha256"])
        verify_tree(tree, manifest["patched_source_sha256"])
        require(sha(legacy) == result["identities"]["legacy_patch_sha256"] and
                sha(patch) == result["identities"]["patch_sha256"] and
                sha(manifest_path) == result["identities"]["manifest_sha256"] and
                sha(legacy_manifest_path) == result["identities"]["legacy_manifest_sha256"],
                "an input changed during the screen")
        result["status"] = "PASS"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["ended_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        result["elapsed_seconds"] = round(time.monotonic() - start, 6)
        write_results(run, result)
    print(json.dumps({"status": result["status"], "run_dir": str(run),
                      "elapsed_seconds": result["elapsed_seconds"], "error": result.get("error")},
                     ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
