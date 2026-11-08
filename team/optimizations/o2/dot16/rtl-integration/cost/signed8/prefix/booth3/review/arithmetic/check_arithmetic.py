#!/usr/bin/env python3
"""Booth3 incremental integer model; does not run Chisel, SV, or EDA."""
from pathlib import Path
from itertools import product
import hashlib
import json
import random
import time

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT.parent / "prefix-booth-candidate-01/source"
ORIGINAL = ROOT.parent / "prefix-pgroup-candidate-01/base/source"
PINS = {
    "derive_source.py": "37f42bc92375810f046bcb12730c98cec8c4f8318cd46087811fcb6e47f1f37e",
    "source/VDotDatapath.scala": "880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680",
    "source/VDotElastic.scala": "1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238",
    "source/source-derivation.json": "202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876",
}
LIMITS = (28, 19, 13, 9, 6, 4, 3)
BIAS = 1 << 19


def signed(x, width):
    x &= (1 << width) - 1
    return x - (1 << width) if x & (1 << (width - 1)) else x


def partials(a, b):
    # The recoder/constant source block is byte-identical to the already
    # independently exhausted Booth9 source. Its proved row is a*d-neg+256.
    for group in range(4):
        low = 0 if group == 0 else (b >> (2 * group - 1)) & 1
        mid, high = (b >> (2 * group)) & 1, (b >> (2 * group + 1)) & 1
        d = -2 * high + mid + low
        row = signed(a, 8) * d - high + 256
        assert 0 <= row < 512
        yield group, row, high


def p_rows(left, right):
    columns = [[] for _ in range(20)]
    for a, b in zip(left, right):
        for g, row, neg in partials(a, b):
            for bit in range(9):
                columns[2 * g + bit].append((row >> bit) & 1)
            columns[2 * g].append(neg)
    for col in (18, 16, 14, 12, 11):
        columns[col].append(1)
    full = half = 0
    shapes = []
    for limit in LIMITS:
        before = sum(sum(c) << i for i, c in enumerate(columns))
        nxt = [[] for _ in range(20)]
        for col, old in enumerate(columns):
            used = 0
            while len(old) - used + len(nxt[col]) > limit:
                n = 3 if len(old) - used + len(nxt[col]) - limit >= 2 else 2
                assert len(old) - used >= n
                x, y = old[used:used + 2]
                if n == 3:
                    z = old[used + 2]
                    s, c = x ^ y ^ z, (x & y) | ((x ^ y) & z)
                    full += 1
                else:
                    s, c = x ^ y, x & y
                    half += 1
                assert s + 2 * c == sum(old[used:used + n])
                nxt[col].append(s)
                assert col + 1 < 20, "model found a structural high-carry discard"
                nxt[col + 1].append(c)
                used += n
            nxt[col].extend(old[used:])
            assert len(nxt[col]) <= limit
        assert before == sum(sum(c) << i for i, c in enumerate(nxt))
        columns = nxt
        shapes.append([len(c) for c in columns])
    assert all(len(c) <= 3 for c in columns)
    rows = [sum((c[row] if row < len(c) else 0) << bit
                for bit, c in enumerate(columns)) for row in range(3)]
    return rows, dict(full_adders=full, half_adders=half, layers=len(LIMITS), shapes=shapes)


def csa(a, b, c, width):
    mask = (1 << width) - 1
    s = a ^ b ^ c
    carry = (((a & b) | ((a ^ b) & c)) << 1) & mask
    assert (s + carry) & mask == (a + b + c) & mask
    return s, carry


def prefix_pair(x, y, width):
    mask = (1 << width) - 1
    p0 = p = x ^ y
    g = x & y
    for distance in (1, 2, 4, 8, 16):
        low_mask = (1 << distance) - 1
        nxt_p = (p & (p << distance) & mask) | (p & low_mask)
        nxt_g = (g | (p & (g << distance))) & mask
        p, g = nxt_p, nxt_g
    result = p0 ^ ((g << 1) & mask)
    assert result == (x + y) & mask
    return result


def r_finish(rows, width):
    assert (width, len(rows)) in ((19, 3), (20, 6))
    mask = (1 << width) - 1
    rows = [r & mask for r in rows]
    lo_s, lo_c = csa(*rows[:3], width)
    if len(rows) == 6:
        hi_s, hi_c = csa(*rows[3:], width)
        cs0_s, cs0_c = csa(lo_s, lo_c, hi_s, width)
        x, y = csa(cs0_s, cs0_c, hi_c, width)
    else:
        x, y = lo_s, lo_c
    result = prefix_pair(x, y, width)
    assert result == sum(rows) & mask
    return result


def main():
    start = time.monotonic()
    for name, expected in PINS.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    d = json.loads((ROOT / "source/source-derivation.json").read_bytes())
    names = ("VDotDatapath.scala", "VDotElastic.scala")
    texts = {n: (ROOT / "source" / n).read_text() for n in names}
    restored = texts.copy()
    assert d["new_edits"] == 11 and len(d["edits"]) == 16
    for e in reversed(d["edits"][-11:]):
        assert restored[e["file"]].count(e["after"]) == 1
        restored[e["file"]] = restored[e["file"]].replace(e["after"], e["before"], 1)
    assert all(restored[n].encode() == (PARENT / n).read_bytes() for n in names)
    for e in reversed(d["edits"][:-11]):
        assert restored[e["file"]].count(e["after"]) == 1
        restored[e["file"]] = restored[e["file"]].replace(e["after"], e["before"], 1)
    assert all(restored[n].encode() == (ORIGINAL / n).read_bytes() for n in names)
    old_dp = (PARENT / "VDotDatapath.scala").read_text()
    new_dp = texts["VDotDatapath.scala"]
    def recoder(t):
        return t[t.index("    var columns = Vector.fill(width)"):t.index("    for ((limit, level)")]
    assert recoder(old_dp) == recoder(new_dp)
    marker = '    wire("p0", "x ^ y")'
    assert old_dp[old_dp.index(marker):] == new_dp[new_dp.index(marker):]
    assert d["old_prefix_finish_source_retained"] is False
    assert d["fresh_three_six_row_unconstrained_proofs_required"] is True

    rng = random.Random(0xB003)
    vectors = [([a] * 8, [b] * 8) for a in (0, 1, 127, 128, 129, 254, 255)
               for b in (0, 1, 127, 128, 129, 254, 255)]
    for i in range(8):
        a, b = [0] * 8, [0] * 8
        a[i] = b[i] = 128
        vectors.append((a, b))
    vectors.extend(([rng.randrange(256) for _ in range(8)], [rng.randrange(256) for _ in range(8)])
                   for _ in range(1024))
    full_rows = []
    shapes = []
    for a, b in vectors:
        rows, shape = p_rows(a, b)
        exact = sum(signed(x, 8) * signed(y, 8) for x, y in zip(a, b))
        assert sum(rows) == exact + BIAS
        assert signed(r_finish(rows, 19), 19) == exact
        assert signed(r_finish(rows + [BIAS, 0, 0], 20), 20) == exact
        full_rows.append((rows, exact))
        shapes.append(shape)
    assert all(s == shapes[0] for s in shapes)
    assert (shapes[0]["full_adders"], shapes[0]["half_adders"], shapes[0]["layers"]) == (272, 19, 7)
    for (lo, a), (hi, b) in zip(full_rows, reversed(full_rows)):
        assert signed(r_finish(lo + hi, 20), 20) == a + b
    extremes = {}
    for name, a, b in (("positive", 128, 128), ("negative", 128, 127)):
        rows, _ = p_rows([a] * 8, [b] * 8)
        exact = 16 * signed(a, 8) * signed(b, 8)
        assert signed(r_finish(rows + rows, 20), 20) == exact
        extremes[name] = exact

    r_counts = {}
    for width, count in ((19, 3), (20, 6)):
        mask = (1 << width) - 1
        cases = list(product((0, 1, mask), repeat=count))
        for lane in range(count):
            for bit in range(width):
                row = [0] * count
                row[lane] = 1 << bit
                cases.append(row)
        cases.extend([rng.randrange(mask + 1) for _ in range(count)] for _ in range(2048))
        for rows in cases:
            r_finish(rows, width)
        r_counts[f"width{width}_rows{count}"] = len(cases)
    result = dict(status="BOOTH3_INCREMENTAL_INTEGER_MODEL_PASS", source_pins=PINS,
                  exact_inverse_to_booth9=True, exact_inverse_to_prefix=True,
                  booth_recoder_and_bias_source_unchanged=True, prefix_suffix_source_unchanged=True,
                  whole_finish_source_unchanged=False, old_finish_sat_reused=False,
                  p_shape=shapes[0], p_rows_per_half=3,
                  p_declared_bits={"feature0": 57, "feature1": 120},
                  p_to_r_dot8_feature0_vectors=len(vectors),
                  p_to_r_dot8_feature1_vectors=len(vectors),
                  p_to_r_dot16_vectors=len(vectors) + 2,
                  arbitrary_row_finite_tests=r_counts, dot16_extremes=extremes,
                  actual_chisel_generated=False, actual_sv_verified=False,
                  actual_fu_simulated=False, fresh_sat_executed=False,
                  asic_ppa_verified=False, elapsed_seconds=time.monotonic()-start)
    out = Path(__file__).with_name("arithmetic-result.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("source_pins", "p_shape")}, indent=2))
    print("P_SHAPE", {k: v for k, v in shapes[0].items() if k != "shapes"})
    print("RESULT_SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
