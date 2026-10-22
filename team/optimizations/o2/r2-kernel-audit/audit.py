#!/usr/bin/env python3
"""Read-only, pinned R2 audit of four archived O3 kernels; no RTL/EMU execution.

Run from a full repository checkout:
  python3 -B team/optimizations/o2/r2-kernel-audit/audit.py \
      --repo . --output /absolute/new/r2-audit

This is a deliberately limited decoder for the pinned straight-line kernels,
not a general RISC-V disassembler. Unknown instructions fail closed.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

BASE = "17bab1d6e51692ccf1cc007e1ec73054ceda168e"
ARCHIVE = Path("team/workloads/o3-gemv/evidence/20261020-application/files/runs/images-02")
GENERATOR = Path("team/workloads/o3-gemv/generate.py")
GENERATOR_BLOB = "9cb0c6b755daa9b05d346b4b48cb80246852d4a8"
INPUTS = {
    "performance-d0-s07": (4, 13, "b6789cb3796ff1ec4cd2245852f086276750f44e"),
    "performance-d0-s05": (16, 64, "93176d5e1fa03022496cd8719b10db5bd9764f1f"),
}
START, STOP, FENCE = 0x51300013, 0x51400013, 0x0330000F
PREFIX = (START, FENCE, 0xC0202773, FENCE, 0xC0002873, FENCE)
SUFFIX = (FENCE, 0xC00028F3, FENCE, 0xC02027F3, FENCE, STOP)
CODE_HASHES = {
    (4, 13, "vdot"): "b8bd0c0754763f79d8b32815407da34448d26cfa282bc169c3a9e5992a4bb25d",
    (4, 13, "rvv"): "6f309d552d904c5c0922923c39faa0202d65cdb65a30a0237d40350fc16c6717",
    (16, 64, "vdot"): "6ae684322e54f6092fcd42b5b556a042ee3cb41e6fff09b576ffaed61d17ba29",
    (16, 64, "rvv"): "e1ba7cd1eb705d2b9793e9559f77b0bb92a4e5d1323dea22d828b8a4bbd09fdf",
}

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def section_table(data: bytes) -> list[tuple]:
    require(len(data) >= 64, "truncated ELF header")
    h = struct.unpack_from("<16sHHIQQQIHHHHHH", data)
    require(h[0][:7] == b"\x7fELF\x02\x01\x01" and h[2] == 243, "expected ELF64 LE RISC-V")
    require(h[-3] == 64 and 0 < h[-2] < 4096, "unsupported section table")
    require(h[6] + 64 * h[-2] <= len(data), "truncated section table")
    return [struct.unpack_from("<IIQQQQIIQQ", data, h[6] + i * 64) for i in range(h[-2])]

def section_bytes(data: bytes, section: tuple) -> bytes:
    start, size = section[4:6]
    require(start + size <= len(data), "truncated section payload")
    return data[start:start + size]

def elf_functions(data: bytes) -> dict[str, tuple[int, bytes]]:
    sections = section_table(data)
    found: dict[str, tuple[int, bytes]] = {}
    for table in sections:
        if table[1] != 2:  # SHT_SYMTAB
            continue
        require(table[9] == 24 and table[5] % 24 == 0, "invalid symbol table")
        require(table[6] < len(sections), "invalid string table link")
        strings = section_bytes(data, sections[table[6]])
        symbols = section_bytes(data, table)
        for pos in range(0, len(symbols), 24):
            nameoff, info, _, index, value, size = struct.unpack_from("<IBBHQQ", symbols, pos)
            if info & 15 != 2 or not size or index == 0 or index >= len(sections):
                continue
            require(nameoff < len(strings), "invalid symbol name")
            end = strings.find(b"\0", nameoff)
            require(end >= nameoff, "unterminated symbol name")
            name = strings[nameoff:end].decode("utf-8")
            section = sections[index]
            if not section[2] & 4:
                continue
            offset = value - section[3]
            require(0 <= offset and offset + size <= section[5], "symbol outside executable section")
            require(name not in found, "duplicate function name")
            found[name] = (value, section_bytes(data, section)[offset:offset + size])
    return found

def decode(word: int) -> tuple[str, str]:
    op, f3, f7, f6 = word & 127, (word >> 12) & 7, word >> 25, word >> 26
    rd, rs1, rs2 = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
    imm = word >> 20
    signed = imm if imm < 2048 else imm - 4096
    if word & 0xFE00707F == 0x0200000B:
        return "vdot.vv", f"v{rd}, v{rs1}, v{rs2}"
    if op == 0x13 and f3 == 0:
        return "addi", f"x{rd}, x{rs1}, {signed}"
    if op == 3 and f3 == 0:
        return "lb", f"x{rd}, {signed}(x{rs1})"
    if op == 0x3B and f3 == 0 and f7 in (0, 1):
        return ("mulw" if f7 else "addw"), f"x{rd}, x{rs1}, x{rs2}"
    if op == 0x73 and f3 == 5 and rd == 0 and imm in (8, 15):
        return "csrwi", f"{hex(imm)}, {rs1}"
    if op == 7 and word & 0xFFF0707F == 0x02000007:
        return "vle8.v", f"v{rd}, (x{rs1})"
    if op == 0x27 and word & 0xFFF0707F == 0x02800027:
        return "vs1r.v", f"v{rd}, (x{rs1})"
    if op == 0x57:
        if f3 == 7 and word >> 30 == 3:
            return "vsetivli", f"x{rd}, {rs1}, vtype={hex((word >> 20) & 0x3ff)}"
        if (f6, f3) == (0x10, 2) and rs1 == 0 and (word >> 25) & 1:
            return "vmv.x.s", f"x{rd}, v{rs2}"
        if (f6, f3) == (0x10, 6) and rs2 == 0 and (word >> 25) & 1:
            return "vmv.s.x", f"v{rd}, x{rs1}"
        if (f6, f3) == (0x17, 3) and rs2 == 0 and (word >> 25) & 1:
            return "vmv.v.i", f"v{rd}, {rs1 if rs1 < 16 else rs1 - 32}"
        if (f6, f3) == (0x3B, 2) and (word >> 25) & 1:
            return "vwmul.vv", f"v{rd}, v{rs2}, v{rs1}"
        if (f6, f3) == (0x31, 0) and (word >> 25) & 1:
            return "vwredsum.vs", f"v{rd}, v{rs2}, v{rs1}"
    raise ValueError(f"unsupported body instruction 0x{word:08x}")

def audit_kernel(code: bytes, address: int) -> dict:
    require(len(code) % 4 == 0, "truncated or compressed function")
    words = struct.unpack("<" + "I" * (len(code) // 4), code)
    require(words.count(START) == words.count(STOP) == 1, "need exactly one start/stop marker")
    a, z = words.index(START), words.index(STOP)
    require(a + 12 <= z + 1, "reversed or empty measurement span")
    require(words[a:a + 6] == PREFIX and words[z - 5:z + 1] == SUFFIX, "measurement wrapper changed")
    body = words[a + 6:z - 5]
    require(body and all(w & 3 == 3 for w in body), "compressed or empty body unsupported")
    rows = []
    for i, w in enumerate(body):
        name, operands = decode(w)
        rows.append({"pc": f"0x{address + (a + 6 + i) * 4:08x}", "word": f"{w:08x}",
                     "mnemonic": name, "operands": operands})
    return {
        "code_sha256": hashlib.sha256(code).hexdigest(),
        "body_sha256": hashlib.sha256(struct.pack("<" + "I" * len(body), *body)).hexdigest(),
        "body_start": rows[0]["pc"], "body_end_exclusive": f"0x{address + (z - 5) * 4:08x}",
        "body_instructions": len(body), "marker_span_instructions": z - a + 1,
        "wrapper_instructions": 12, "counts": dict(sorted(Counter(r["mnemonic"] for r in rows).items())),
        "instructions": rows,
    }

def load_generator(repo: Path):
    data = (repo / GENERATOR).read_bytes()
    require(git_blob(data) == GENERATOR_BLOB, "frozen generator identity mismatch")
    tree = ast.parse(data)
    defs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("kernel", "stores")]
    require({n.name for n in defs} == {"kernel", "stores"}, "generator functions missing")
    namespace = {"SCOPES": ("core", "endtoend")}
    exec(compile(ast.Module(body=defs, type_ignores=[]), str(GENERATOR), "exec"), namespace)
    return namespace["kernel"]

def source_counts(lines: list[str]) -> dict[str, int]:
    names = {"li": "addi", "mv": "addi", ".word": "vdot.vv"}
    return dict(sorted(Counter(names.get(line.split()[0], line.split()[0]) for line in lines).items()))

def run(repo: Path, output: Path) -> dict:
    require(not output.exists(), "output must be a new directory")
    generate = load_generator(repo)
    results = []
    for image, (m, k, blob) in INPUTS.items():
        directory = repo / ARCHIVE / image
        raw = (directory / "vdot-perf.elf").read_bytes()
        require(git_blob(raw) == blob, f"archived ELF identity mismatch: {image}")
        functions = elf_functions(raw)
        archived = {r["id"]: r for r in json.loads((directory / "elf-audit.json").read_text())["kernels"]}
        for index, method in ((2, "vdot"), (3, "rvv")):
            key = f"gemv-{m}x{k}-endtoend-reuse-{method}"
            address, code = functions[f"t13_kernel_{index}"]
            result = audit_kernel(code, address)
            require(result["code_sha256"] == CODE_HASHES[(m, k, method)], "function bytes changed")
            old = archived[key]
            require(result["marker_span_instructions"] == old["machine_instructions"], "archived span mismatch")
            require(result["counts"].get("vdot.vv", 0) == old["custom_instructions"], "archived custom count mismatch")
            require(result["counts"] == source_counts(generate(m, k, method, "reuse", "endtoend")), "source/machine count mismatch")
            result.update(id=key, image=image, elf_git_blob=blob, elf_sha256=hashlib.sha256(raw).hexdigest(),
                          full_elf_identity_verified=True, source_count_check=True, archived_count_check=True)
            results.append(result)
    output.mkdir(parents=True, exist_ok=False)
    for row in results:
        text = "\n".join(f'{x["pc"]}: {x["word"]}  {x["mnemonic"]} {x["operands"]}' for x in row.pop("instructions"))
        (output / (row["id"] + ".disassembly.txt")).write_text(text + "\n")
    result = {"status": "R2_PINNED_KERNEL_AUDIT_PASS", "source_base": BASE, "new_emu_runs": 0,
              "scope": "dataset0, reuse, endtoend, 4x13 and 16x64; not an application regression",
              "warning": "Static instruction counts are not cycle attribution; no new performance claim.",
              "kernels": results}
    (output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.repo.resolve(), args.output.resolve())
    except (ValueError, OSError, KeyError, struct.error) as exc:
        parser.exit(2, f"R2_AUDIT_REJECTED: {exc}\n")
    print(report["status"])
