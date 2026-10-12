#!/usr/bin/env python3
"""Isolated research checks, not an ISA simulator, RTL proof, or PPA model.

Run from any directory: python3 check_arithmetic.py --output result.json
Only the requested result file is written. Python 3.10+, standard library.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

SEED = 0xCD0D2026
WIDTH = 19
MASK = (1 << WIDTH) - 1
PAIR_CORRECTION = -2 * sum(1 << k for k in range(7, 14))


def signed(x: int, width: int) -> int:
    x &= (1 << width) - 1
    return x - (1 << width) if x & (1 << (width - 1)) else x


def pp_rows(a: int, b: int) -> list[int]:
    """Eight rows, complementing ONLY negative-weight partial-product bits.

    For a signed byte, bit 7 has weight -128. Thus exactly one sign
    index gives a negative term. -x*2^k = (1-x)*2^k - 2^k.
    Rows here exclude the shared, data-independent correction.
    """
    if not (0 <= a <= 255 and 0 <= b <= 255):
        raise ValueError("pp_rows needs encoded bytes")
    rows = []
    for j in range(8):
        row = 0
        for i in range(8):
            bit = ((a >> i) & 1) & ((b >> j) & 1)
            if (i == 7) != (j == 7):
                bit ^= 1
            row |= bit << (i + j)
        rows.append(row)
    return rows


def compress(rows: list[int], width: int = WIDTH) -> int:
    """Word-level 3:2 reduction modulo 2**width. NOT gate-delay estimation."""
    mask = (1 << width) - 1
    work = [x & mask for x in rows]
    if not work:
        return 0
    invariant = sum(work) & mask
    while len(work) > 2:
        nxt = []
        for i in range(0, len(work) - 2, 3):
            x, y, z = work[i:i + 3]
            nxt.extend([(x ^ y ^ z) & mask,
                        (((x & y) | (x & z) | (y & z)) << 1) & mask])
        tail = len(work) - len(work) % 3
        nxt.extend(work[tail:])
        if sum(nxt) & mask != invariant:
            raise AssertionError("compression lost a weighted bit")
        work = nxt
    return sum(work) & mask


def dot_reference(a: list[int], b: list[int]) -> int:
    return sum(signed(x, 8) * signed(y, 8) for x, y in zip(a, b))


def dot_tree(a: list[int], b: list[int]) -> int:
    work = [signed(x, 8) * signed(y, 8) for x, y in zip(a, b)]
    while len(work) > 1:
        work = [work[i] + work[i + 1] for i in range(0, len(work), 2)]
    return work[0]


def dot_products_csa(a: list[int], b: list[int]) -> int:
    return signed(compress([signed(x, 8) * signed(y, 8)
                            for x, y in zip(a, b)]), WIDTH)


def dot_fused_pp(a: list[int], b: list[int]) -> int:
    if len(a) != 8 or len(b) != 8:
        raise ValueError("this candidate is exactly eight byte pairs")
    rows = [r for x, y in zip(a, b) for r in pp_rows(x, y)]
    rows.append((8 * PAIR_CORRECTION) & MASK)
    return signed(compress(rows), WIDTH)


def execute_math(src1: int, src2: int) -> int:
    a = [(src1 >> (8 * i)) & 255 for i in range(8)]
    b = [(src2 >> (8 * i)) & 255 for i in range(8)]
    return dot_fused_pp(a, b) & 0xffffffff  # NOT sign-extension to 128 bits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not __debug__:
        raise RuntimeError('Run without -O: assertions are part of the experiment')
    rng = random.Random(SEED)
    corpus = hashlib.sha256()
    pair_cases = 0
    for a in range(256):
        for b in range(256):
            expect = signed(a, 8) * signed(b, 8)
            rows = pp_rows(a, b)
            for width in (16, 19):
                got = signed((sum(rows) + PAIR_CORRECTION), width)
                assert got == expect, (a, b, width, got, expect)
            pair_cases += 1
    # The full-adder identity is exhaustive for all single-bit inputs.
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                assert x + y + z == (x ^ y ^ z) + 2 * ((x & y) | (x & z) | (y & z))
    directed = [([0]*8, [0]*8), ([128]*8, [128]*8),
                ([128]*8, [127]*8), ([127]*8, [127]*8),
                ([128, 127]*4, [127, 128]*4),
                ([255]*8, [1]*8), ([0]*7+[128], [0]*7+[128]),
                ([128]*4+[127]*4, [128]*4+[128]*4)]
    cases = directed + [([rng.randrange(256) for _ in range(8)],
                         [rng.randrange(256) for _ in range(8)]) for _ in range(4096)]
    observed = []
    for a, b in cases:
        expect = dot_reference(a, b)
        corpus.update(bytes(a + b))
        assert dot_tree(a, b) == expect
        assert dot_products_csa(a, b) == expect
        assert dot_fused_pp(a, b) == expect
        assert -130048 <= expect <= 131072
        assert dot_fused_pp(b, a) == expect
        order = list(range(8)); rng.shuffle(order)
        assert dot_fused_pp([a[i] for i in order], [b[i] for i in order]) == expect
        lo1 = int.from_bytes(bytes(a), 'little')
        lo2 = int.from_bytes(bytes(b), 'little')
        full1 = lo1 | (rng.getrandbits(64) << 64)
        full2 = lo2 | (rng.getrandbits(64) << 64)
        assert execute_math(full1, full2) == (expect & 0xffffffff)
        assert execute_math(full1, full2) >> 32 == 0
        observed.append(expect)
    # Named negative controls: each is an intentionally wrong proposed shortcut.
    negative = {
        "18_bit_sum_at_positive_extreme": {"expected": 131072, "wrong": signed(131072, 18)},
        "16_bit_accumulate_two_extreme_products": {"expected": 32768, "wrong": signed(32768, 16)},
        "extract_int32_at_e8": {"expected": 131072, "wrong": signed(131072, 8)},
        "sign_extend_negative_to_full_128": {"expected": (-8) & 0xffffffff,
                                              "wrong": (-8) & ((1 << 128) - 1)},
        "preserve_old_high_destination": {"expected": 8, "wrong": 8 | (1 << 100)},
        "merge_blocks_with_different_scales": {"expected": 32*1 + 32*2, "wrong": (32+32)*1},
        "flush_all_when_only_younger_is_killed": {"expected": [10], "wrong": []},
        "numeric_rob_index_comparison_across_wrap": {"expected": ["kill_young_index_0"], "wrong": []},
    }
    for key, case in negative.items():
        assert case["expected"] != case["wrong"], key
    # Width-safe long dot, distinct from the custom instruction contract.
    long_cases = 0
    for length in (0, 1, 7, 8, 9, 31, 32, 33, 128, 1024):
        for _ in range(16):
            a = [rng.randrange(-128, 128) for _ in range(length)]
            b = [rng.randrange(-128, 128) for _ in range(length)]
            acc = [0]*8
            for off in range(0, length, 8):
                for lane, (x, y) in enumerate(zip(a[off:off+8], b[off:off+8])):
                    acc[lane] += x*y
            assert sum(acc) == sum(x*y for x, y in zip(a, b))
            long_cases += 1
    assert 131071 * 16384 <= 2**31 - 1 < 131072 * 16384
    out = {
        "schema": 1, "scope": "host arithmetic/logic only; not executed RTL or ISA",
        "ran_at_utc": datetime.now(timezone.utc).isoformat(), "seed": SEED,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "pair_input_cases_exhaustive": pair_cases,
        "pair_encoding_widths_checked": [16, 19], "full_adder_truth_cases": 8,
        "eight_pair_cases": len(cases), "eight_pair_candidates": 3,
        "metamorphic_checks_per_case": ["swap_sources", "permute_pairs", "ignore_high64", "zero_high96"],
        "long_dot_cases": long_cases, "rejected_shortcut_counterexamples": negative,
        "minimum_observed": min(observed), "maximum_observed": max(observed),
        "pair_correction": PAIR_CORRECTION, "eight_pair_correction_mod_2pow19": (8*PAIR_CORRECTION) & MASK,
        "eight_pair_corpus_sha256": corpus.hexdigest(), "passed": True,
        "not_proved": ["Chisel implementation", "ISA exception/CSR behavior", "full-core integration",
                       "physical timing/area/power", "performance improvement"]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: out[k] for k in ("passed", "pair_input_cases_exhaustive", "eight_pair_cases", "long_dot_cases")}))


if __name__ == '__main__':
    main()
