"""R4 callable GEMV functions; retain frozen S0/S1 arithmetic and data."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

REL = Path("team/optimizations/o2/r2-select")
S1 = Path("team/optimizations/o2/r2-vector-accum")
CONTRACT = "r4-gemv-c-abi-entry-v1"
S1_SHA = "0270736b5c09e160626eb7b32d8e760faa193bf05761fea824a979108c3717b9"
FILES = ("kernels.S", "cases.h", "gemv.S", "gemv.h")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source(repo):
    path = Path(repo) / S1 / "candidate.py"
    require(hashlib.sha256(path.read_bytes()).hexdigest() == S1_SHA, "S1 source drift")
    spec = importlib.util.spec_from_file_location("r4_frozen_s1_candidate", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def api_name(row):
    return f"r4_gemv_{row['m']}x{row['k']}_{row['software']}_{row['method']}"


def encode_jal(offset):
    require(type(offset) is int and offset % 2 == 0 and -(1 << 20) <= offset < 1 << 20,
            "JAL displacement")
    return ((offset & 0x100000) << 11) | ((offset & 0x7fe) << 20) | \
        ((offset & 0x800) << 9) | (offset & 0xff000) | 0xef


def generate(repo, output, variant, dataset, shard, suite="performance"):
    require(shard in (1, 3, 5, 7), "callable API includes endtoend work only")
    out = Path(output)
    original = source(repo)
    manifest = original.generate(repo, out, variant, dataset, shard, suite)
    text = (out / "kernels.S").read_text()
    standalone = [".option norvc", ".option norelax", ".text"]
    header = ["#ifndef R4_GEMV_H", "#define R4_GEMV_H", "#include <stdint.h>",
              "/* VLEN128; VS enabled; disjoint packed A||x and M zero-high96 output slots.",
              " * All input loads, state setup and output stores are inside each leaf.",
              " * Vector configuration is caller-clobbered. See ENTRY_CONTRACT.md. */"]
    for i, row in enumerate(manifest["rows"]):
        name, symbol = f"t13_kernel_{i}", api_name(row)
        start = text.index(name + ":\n")
        end = text.index(f".size {name}, .-{name}", start)
        block = text[start:end]
        body = "".join("  " + line + "\n" for line in row["body"])
        require(block.count(body) == 1 and block.endswith("  ret\n"), "renderer body boundary")
        # The measured wrapper saves its own return/result registers before the
        # start marker. The public leaf uses the ordinary two-pointer C ABI.
        block = block.replace(name + ":\n", name + ":\n" +
            "  addi sp, sp, -16\n  sd ra, 0(sp)\n  sd s0, 8(sp)\n  mv s0, a1\n", 1)
        call, target = f".Lr4_call_{i}", f".Lr4_api_{i}"
        delta = f"({target} - {call})"
        # A same-section label difference is absolute: GNU emits the complete
        # JAL word without a linker relocation or relaxation opportunity.
        word = f"(({delta} & 0x100000) << 11) | (({delta} & 0x7fe) << 20) | " + \
               f"(({delta} & 0x800) << 9) | ({delta} & 0xff000) | 0xef"
        measured = f"  mv a0, a2\n  mv a1, a3\n{call}:\n  .word {word}\n  mv a1, s0\n"
        block = block.replace(body, measured, 1)
        leaf = "  mv a2, a0\n  mv a3, a1\n" + body + "  ret\n"
        block = block[:-len("  ret\n")] + "  ld ra, 0(sp)\n  ld s0, 8(sp)\n  addi sp, sp, 16\n  ret\n"
        block += f".global {symbol}\n.type {symbol}, @function\n{symbol}:\n{target}:\n" + leaf
        block += f".size {symbol}, .-{symbol}\n"
        text = text[:start] + block + text[end:]
        standalone += [".balign 16", f".global {symbol}", f".type {symbol}, @function",
                       symbol + ":", leaf.rstrip(), f".size {symbol}, .-{symbol}"]
        header += [f"void {symbol}(const int8_t *packed_ax, void *output_slots);"]
        row["api_symbol"] = symbol
        row["entry_overhead_instructions"] = 7
    header += ["#endif", ""]
    (out / "kernels.S").write_text(text, encoding="utf-8")
    (out / "gemv.S").write_text("\n".join(standalone) + "\n", encoding="utf-8")
    (out / "gemv.h").write_text("\n".join(header), encoding="utf-8")
    cases = (out / "cases.h").read_text().replace(original.CONTRACT, CONTRACT)
    (out / "cases.h").write_text(cases, encoding="utf-8")
    manifest.update(contract=CONTRACT, callable_abi="rv64-lp64d-two-pointer-leaf",
                    dispatcher=False, includes_call_and_return=True,
                    entry_candidate_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    frozen_s1_candidate_sha256=S1_SHA,
                    files={p: hashlib.sha256((out / p).read_bytes()).hexdigest() for p in FILES})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--variant", choices=("s0", "s1"), required=True)
    p.add_argument("--dataset", type=int, choices=range(3), default=0)
    p.add_argument("--shard", type=int, choices=(1, 3, 5, 7), default=3)
    a = p.parse_args()
    generate(a.repo, a.output, a.variant, a.dataset, a.shard)
