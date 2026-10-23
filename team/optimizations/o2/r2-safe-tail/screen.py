#!/usr/bin/env python3
"""Cross-assemble S0/S2/RVV and run a bounded architectural model, not EMU."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys

import candidate
from machine_model import Machine

ORIGINAL_BODY_SHA = {
    (4, 13, "vdot"): "4c6a81062eb08c211ac6d532e02ed9c9232da3a65843b158ec387731dc33d19e",
    (4, 13, "rvv"): "b92570f57b6b695e413f45eeadc5afc1c67f94ba3bc29e14024c7050467903e9",
    (16, 64, "vdot"): "620f7688b64e45c7e5c925e80e23a4ba3d9c2677003aa797fd56c7a415def4bf",
    (16, 64, "rvv"): "dd229f79c28c356627bd5d90ac35681b3c4ca25f6d72d5d38a715746c6a02cf5",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def audit_module(repo):
    path = Path(repo) / "team/optimizations/o2/r2-kernel-audit/audit.py"
    spec = importlib.util.spec_from_file_location("r2_previous_audit", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def assemble(body, directory, clang, audit):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    source = ".option norvc\n.option norelax\n.text\n.global kernel\n.type kernel,@function\nkernel:\n"
    source += "\n".join("  " + line for line in body) + "\n.size kernel,.-kernel\n"
    (directory / "body.S").write_text(source)
    command = [clang, "--target=riscv64", "-march=rv64gcv", "-mabi=lp64d", "-c", str(directory / "body.S"), "-o", str(directory / "body.o")]
    done = subprocess.run(command, capture_output=True, text=True, timeout=45)
    (directory / "compile.json").write_text(json.dumps(dict(command=command, returncode=done.returncode, stdout=done.stdout, stderr=done.stderr), indent=2) + "\n")
    candidate.require(done.returncode == 0, "assembler failed: " + done.stderr)
    _, code = audit.elf_functions((directory / "body.o").read_bytes())["kernel"]
    candidate.require(len(code) == 4 * len(body), "unexpected pseudo expansion/compression")
    (directory / "body.bin").write_bytes(code)
    objdump = shutil.which("llvm-objdump")
    if objdump:
        listing = subprocess.run([objdump, "-d", "--mattr=+v", str(directory / "body.o")], capture_output=True, text=True, timeout=45)
        candidate.require(listing.returncode == 0, "objdump failed")
        (directory / "llvm-disassembly.txt").write_text(listing.stdout)
    return code

def vectors(base, m, k):
    for d in range(3):
        a, x = base.inputs(m, k, d)
        yield f"original-d{d}", a, x
    for i, (av, xv) in enumerate(((0, 0), (-128, -128), (-128, 127), (127, 127), (1, -1))):
        yield f"edge-{i}", [[av] * k for _ in range(m)], [xv] * k
    for j in range(k):
        x = [0] * k; x[j] = -128
        a = [[0] * k for _ in range(m)]
        for r in range(m):
            a[r][j] = (127, -128, 1, -1)[r % 4]
        yield f"lane-{j}", a, x
    rng = random.Random(0x20261021 + 1009 * m + k)
    for i in range(512 if (m, k) == (4, 13) else 16):
        yield f"random-{i}", [[rng.randrange(-128, 128) for _ in range(k)] for _ in range(m)], [rng.randrange(-128, 128) for _ in range(k)]

def run(repo, output, clang="clang"):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    candidate.require(not output.exists(), "output must be new")
    compiler = shutil.which(clang)
    candidate.require(compiler is not None, "Clang with RISC-V target is required")
    base, audit = candidate.load_base(repo), audit_module(repo)
    output.mkdir(parents=True, exist_ok=False)
    records, executions, originals = [], 0, 0
    for m, k in ((4, 13), (16, 64)):
        cases = list(vectors(base, m, k))
        for software in ("basic", "reuse"):
            for scope in ("core", "endtoend"):
                control = {}
                for variant, method in (("s0", "vdot"), ("s2", "vdot"), ("s0", "rvv")):
                    name = f"{m}x{k}-{software}-{scope}-{variant}-{method}"
                    body = candidate.kernel(base, m, k, method, software, scope, variant)
                    code = assemble(body, output / name, compiler, audit)
                    if software == "reuse" and scope == "endtoend" and variant == "s0":
                        candidate.require(sha(code) == ORIGINAL_BODY_SHA[(m, k, method)], "original ELF body mismatch")
                        originals += 1
                    if method == "rvv":
                        candidate.require(body == candidate.kernel(base, m, k, method, software, scope, "s2"), "RVV was changed")
                    if variant == "s2" and k != 13:
                        candidate.require(code == control["s0-vdot"], "control shape changed")
                    digest = hashlib.sha256()
                    for i, (label, a, x) in enumerate(cases):
                        vm = Machine(a, x, poison_seed=i + 1).execute(code)
                        vm.check(a, x, stored=(scope == "endtoend"))
                        if method == "vdot" and variant == "s2" and k == 13:
                            dots = vm.tail_dot_operands
                            tails = dots[4:] if software == "reuse" else dots[1::2]
                            candidate.require(len(tails) == 4 and all(bytes.fromhex(l)[5:] == bytes(3) and bytes.fromhex(r)[5:] == bytes(3) for l, r in tails), "tail zero proof failed")
                        digest.update(json.dumps([label, a, x], separators=(",", ":")).encode())
                        digest.update(b"".join(bytes(v) for v in vm.v[:m]))
                        executions += 1
                    counts = dict(sorted(vm.counts.items()))
                    source_counts = audit.source_counts(body)
                    candidate.require(counts == source_counts, "machine/source count mismatch")
                    control[variant + "-" + method] = code
                    records.append(dict(id=name, shape=[m, k], software=software, scope=scope,
                                        variant=variant, method=method, instructions=len(code)//4,
                                        body_sha256=sha(code), counts=counts, cases=len(cases),
                                        case_result_digest=digest.hexdigest(), input_read_bytes=sum(n for _, n in vm.reads),
                                        architectural_load_instructions=len(vm.reads), full_128bit_check=True,
                                        protected_registers_check=True, row_bounds_check=True))
    report = dict(status="R2_S2_HOST_MACHINE_MODEL_PASS_NOT_EMU", source_base=candidate.BASE,
                  compiler=subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
                  python=sys.version, assembled_bodies=len(records), model_executions=executions,
                  original_elf_body_matches=originals, baseline_source_git_blobs=candidate.PINS,
                  sources={p.name:sha(p.read_bytes()) for p in Path(__file__).parent.glob("*.py")},
                  new_emu_runs=0, new_rtl_builds=0, performance_measured=False,
                  pending=["complete benchmark ELF build", "B0/H1 NEMU DiffTest", "paired cycle screening"],
                  available_tools={n:shutil.which(n) for n in ("clang", "llvm-objdump", "riscv64-linux-gnu-gcc", "verilator", "mill", "nemu", "emu")},
                  kernels=records)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--clang", default="clang")
    args = p.parse_args()
    try:
        r = run(args.repo, args.output, args.clang)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        p.exit(2, f"R2_SCREEN_REJECTED: {exc}\n")
    print(json.dumps({k:r[k] for k in ("status", "assembled_bodies", "model_executions", "original_elf_body_matches", "new_emu_runs")}))
