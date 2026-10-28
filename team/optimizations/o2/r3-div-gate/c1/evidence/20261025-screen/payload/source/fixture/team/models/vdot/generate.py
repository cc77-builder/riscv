#!/usr/bin/env python3
"""Generate reproducible vdot contract vectors; --check never writes files."""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

# In particular, a read-only --check must not create model.__pycache__.
sys.dont_write_bytecode = True
import model


GENERATOR_VERSION = "1.0.0"
DEFAULT_SEED = 0x20261011
DEFAULT_RANDOM_COUNT = 10_000
U128_MASK = (1 << 128) - 1
MASK_VDOT = 0xFE00707F
MATCH_VDOT = 0x0200000B
SOURCE_DIR = Path(__file__).resolve().parent
PRNG_DESCRIPTION = (
    "For index i starting at 0, compute "
    "sha256(f'{seed:08x}:{i}'.encode('ascii')).digest(). "
    "The lowercase hexadecimal seed has minimum width 8 with zero padding; "
    "i is unpadded decimal. Interpret digest[0:16] as unsigned little-endian "
    "vs1 and digest[16:32] as unsigned little-endian vs2. "
    "Each is 128 bits; only its low eight signed int8 lanes participate."
)


def hex128(value: int) -> str:
    return f"0x{value:032x}"


def arithmetic_row(case_id: str, vs1: int, vs2: int) -> dict[str, Any]:
    a = [int.from_bytes(bytes([(vs1 >> (8 * i)) & 255]), "little", signed=True)
         for i in range(8)]
    b = [int.from_bytes(bytes([(vs2 >> (8 * i)) & 255]), "little", signed=True)
         for i in range(8)]
    return {"id": case_id, "vs1": hex128(vs1), "vs2": hex128(vs2),
            "expected_sum": model.dot_s8(a, b),
            "expected_vd": hex128(model.vdot(vs1, vs2))}


def directed_rows() -> list[dict[str, Any]]:
    # D00-D10 are the manually evaluated cases in spec/vdot.md section 7.1.
    cases = [
        ("D00", [0] * 8, [127] * 8, 0),
        ("D01", [1] * 8, [1] * 8, 8),
        ("D02", list(range(1, 9)), list(range(1, 9)), 204),
        ("D03", [-1] * 8, [1] * 8, -8),
        ("D04", [-1] * 8, [-1] * 8, 8),
        ("D05", [127] * 8, [127] * 8, 129032),
        ("D06", [-128] * 8, [127] * 8, -130048),
        ("D07", [-128] * 8, [-128] * 8, 131072),
        ("D08", [1, -2, 3, -4, 5, -6, 7, -8], list(range(8, 0, -1)), 0),
        ("D09", [-128] + [0] * 7, [-1] + [0] * 7, 128),
        ("D10", [0] * 7 + [-128], [0] * 7 + [127], -16256),
    ]
    rows = []
    for case_id, a, b, expected in cases:
        row = arithmetic_row(case_id, model.pack_lanes(a), model.pack_lanes(b))
        if (row["expected_sum"] != expected or
                int(row["expected_vd"], 16) != (expected & 0xFFFFFFFF)):
            raise RuntimeError(f"model disagrees with manual contract case {case_id}")
        rows.append(row)
    for lane in range(8):
        a = [0] * 8
        a[lane] = -3
        rows.append(arithmetic_row(f"L01_{lane}", model.pack_lanes(a),
                                   model.pack_lanes(list(range(1, 9)))))
    patterns = [
        ("L02_random", 0xD840CEF276159BA3, 0x3A6BC82DE940517F),
        ("L02_ff", (1 << 64) - 1, (1 << 64) - 1),
        ("L02_alternating", 0x55AA55AA55AA55AA, 0xAA55AA55AA55AA55),
    ]
    for case_id, high_a, high_b in patterns:
        rows.append(arithmetic_row(case_id, model.pack_lanes(list(range(1, 9)), high_a),
                                   model.pack_lanes(list(range(1, 9)), high_b)))
    return rows


def random_rows(seed: int, count: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(count):
        digest = hashlib.sha256(f"{seed:08x}:{index}".encode("ascii")).digest()
        rows.append(arithmetic_row(f"R{index:05d}",
                                   int.from_bytes(digest[:16], "little"),
                                   int.from_bytes(digest[16:], "little")))
    return rows


def register_snapshot(vd: int, vs2: int, vs1: int,
                      negative_case: bool = False) -> tuple[int, ...]:
    """Construct one real pre-state, resolving shared registers before execution."""
    registers = [0] * 32
    registers[29] = 0xCAFE000000000000000000000000BEEF
    registers[vd] = U128_MASK
    a = [-1] * 8 if negative_case else list(range(1, 9))
    b = [1] * 8 if negative_case else [8, -7, 6, -5, 4, -3, 2, -1]
    registers[vs1] = model.pack_lanes(a, 0x0123456789ABCDEF)
    # One register cannot simultaneously contain different source snapshots.
    # When both source indices are equal, they both read the value installed above.
    if vs2 != vs1:
        registers[vs2] = model.pack_lanes(b, 0xFEDCBA9876543210)
    return tuple(registers)


def state_row(case_id: str, vd: int = 10, vs2: int = 8, vs1: int = 9,
              config: model.VectorConfig | None = None, word: int | None = None,
              negative_case: bool = False) -> dict[str, Any]:
    config = model.VectorConfig() if config is None else config
    word = model.encode(vd, vs2, vs1) if word is None else word
    registers = register_snapshot(vd, vs2, vs1, negative_case)
    row: dict[str, Any] = {
        "id": case_id,
        "instruction": f"0x{word:08x}",
        "config": asdict(config),
        "registers": {f"v{i}": hex128(value) for i, value in enumerate(registers) if value},
    }
    if (word & MASK_VDOT) != MATCH_VDOT:
        # Some opcode-bit changes name valid *other* instructions (e.g. LB/ADDIW).
        # Rejection by this vdot-only decoder is not an architectural trap claim.
        row["expected"] = {"outcome": "decoder_reject", "reason": "not_vdot",
                           "unchanged": True}
        return row
    try:
        result = model.execute(word, registers, config)
    except model.IllegalInstruction as error:
        row["expected"] = {"outcome": "illegal_instruction", "cause": error.cause,
                           "unchanged": True}
    except model.UnsupportedConfiguration:
        row["expected"] = {"outcome": "unsupported_configuration", "unchanged": True}
    else:
        row["expected"] = {"outcome": "ok", "vd": hex128(result.registers[vd]),
                           "signed_sum": result.signed_sum, "vs_after": result.config.vs}
    return row


def state_rows() -> list[dict[str, Any]]:
    rows = []
    aliases = [
        ("ALIAS_distinct", 10, 8, 9),
        ("ALIAS_vd_vs1", 9, 8, 9),
        ("ALIAS_vd_vs2", 8, 8, 9),
        ("ALIAS_vs1_vs2", 10, 9, 9),
        ("ALIAS_all", 9, 9, 9),
        ("REG_v0_dest_v31_src", 0, 31, 9),
        ("REG_v31_dest_v0_src", 31, 8, 0),
        ("REG_v0_vs2_v31_vs1", 10, 0, 31),
        ("REG_v31_all", 31, 31, 31),
        ("REG_v0_all", 0, 0, 0),
    ]
    rows.extend(state_row(case_id, vd, vs2, vs1) for case_id, vd, vs2, vs1 in aliases)
    rows.append(state_row("L03_prefilled_negative", negative_case=True))
    base = model.VectorConfig()
    for vta in range(2):
        for vma in range(2):
            rows.append(state_row(f"POLICY_vta{vta}_vma{vma}",
                                  config=replace(base, vtype=(vta << 6) | (vma << 7))))
    for vxrm in range(4):
        for vxsat in range(2):
            rows.append(state_row(f"CSR_vxrm{vxrm}_vxsat{vxsat}",
                                  config=replace(base, vxrm=vxrm, vxsat=vxsat)))
    for vs, label in [(1, "initial"), (2, "clean"), (3, "dirty")]:
        rows.append(state_row(f"VS_{label}", config=replace(base, vs=vs)))
    for vl in [0, 1, 7, 9, 16]:
        rows.append(state_row(f"ILLEGAL_vl{vl}", config=replace(base, vl=vl)))
    for vsew in range(1, 8):
        rows.append(state_row(f"ILLEGAL_vsew{vsew}", config=replace(base, vtype=vsew << 3)))
    for vlmul in range(1, 8):
        rows.append(state_row(f"ILLEGAL_vlmul{vlmul}", config=replace(base, vtype=vlmul)))
    rows.extend([
        state_row("ILLEGAL_vstart1", config=replace(base, vstart=1)),
        state_row("ILLEGAL_vill_with_vl0", config=replace(base, vtype=1 << 63, vl=0)),
        state_row("ILLEGAL_vtype_reserved_bit8", config=replace(base, vtype=1 << 8)),
        state_row("ILLEGAL_vs_off", config=replace(base, vs=0)),
        state_row("ILLEGAL_vector_disabled", config=replace(base, vector_enabled=False)),
    ])
    word = model.encode(10, 8, 9)
    rows.append(state_row("REJECT_vm0", word=word ^ (1 << 25)))
    # Include every other fixed bit, covering funct6, funct3 and the main opcode.
    for bit in range(32):
        if bit != 25 and MASK_VDOT & (1 << bit):
            rows.append(state_row(f"REJECT_encoding_bit{bit:02d}", word=word ^ (1 << bit)))
    for vlen_bits in [64, 256]:
        rows.append(state_row(f"UNSUPPORTED_vlen{vlen_bits}",
                              config=replace(base, vlen_bits=vlen_bits)))
    return rows


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
                   + "\n" for row in rows).encode("utf-8")


def build_files(seed: int = DEFAULT_SEED,
                random_count: int = DEFAULT_RANDOM_COUNT) -> dict[str, bytes]:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if isinstance(random_count, bool) or not isinstance(random_count, int) or random_count < 0:
        raise ValueError("random_count must be a nonnegative integer")
    directed = directed_rows()
    random = random_rows(seed, random_count)
    datasets = {"directed.jsonl": directed, "random.jsonl": random,
                "smoke.jsonl": directed + random[:32], "state.jsonl": state_rows()}
    files = {name: jsonl_bytes(rows) for name, rows in datasets.items()}
    manifest = {
        "schema_version": 1,
        "contract": model.CONTRACT_ID,
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "random_count": random_count,
        "prng": PRNG_DESCRIPTION,
        "serialization": "UTF-8, LF, lowercase hex with 0x prefix; JSONL sorted keys and compact separators",
        "state_registers": "Sparse pre-instruction snapshot; omitted v0..v31 are zero. Source aliases are resolved before expectation calculation.",
        "state_configuration_scope": "Direct model-adapter inputs. Some illegal raw vtype/vl combinations are synthetic and cannot be reproduced verbatim with standard vset instructions. A future whole-core harness must construct reachable states and record actual CSRs.",
        "state_decoder_reject": "Nonmatching words only test that the vdot decoder rejects them. unchanged applies to the vdot-only model entry. A full CPU may execute another existing instruction, e.g. LB or ADDIW; no architectural cause is predicted for decoder_reject.",
        "scope": "Model test vectors only; smoke.jsonl is data for a future whole-core harness, not an executable RTL/NEMU test.",
        "files": {name: {"count": len(datasets[name]),
                          "sha256": hashlib.sha256(payload).hexdigest()}
                  for name, payload in files.items()},
        "source_sha256": {name: hashlib.sha256((SOURCE_DIR / name).read_bytes()).hexdigest()
                          for name in ["model.py", "generate.py"]},
    }
    files["manifest.json"] = (json.dumps(manifest, ensure_ascii=True, sort_keys=True,
                                         indent=2) + "\n").encode("utf-8")
    return files


def check_files(output: Path, files: dict[str, bytes]) -> list[str]:
    """Compare regenerated bytes in memory. No mkdir, writes or replacements."""
    errors = []
    for name, expected in files.items():
        path = output / name
        try:
            actual = path.read_bytes()
        except OSError as error:
            errors.append(f"{path}: {error}")
            continue
        if actual != expected:
            errors.append(f"{path}: byte mismatch (expected sha256 "
                          f"{hashlib.sha256(expected).hexdigest()}, got "
                          f"{hashlib.sha256(actual).hexdigest()})")
    return errors


def parse_int(text: str) -> int:
    try:
        value = int(text, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected an integer such as 123 or 0x20261011") from error
    if value < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=SOURCE_DIR / "data")
    parser.add_argument("--seed", type=parse_int, default=DEFAULT_SEED)
    parser.add_argument("--random-count", type=parse_int, default=DEFAULT_RANDOM_COUNT)
    parser.add_argument("--check", action="store_true", help="compare exact regenerated bytes without writing")
    args = parser.parse_args(argv)
    try:
        files = build_files(args.seed, args.random_count)
        if args.check:
            errors = check_files(args.output, files)
            if errors:
                for message in errors:
                    print(message, file=sys.stderr)
                return 1
            print(f"OK: {len(files)} files match regenerated bytes in {args.output}")
            return 0
        args.output.mkdir(parents=True, exist_ok=True)
        for name, payload in files.items():
            (args.output / name).write_bytes(payload)
        print(f"Wrote {len(files)} files to {args.output}; model vectors only")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
