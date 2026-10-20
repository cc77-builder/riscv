"""O3 GEMV assembly: distinct application contract, shared exact input layout."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = "o3-gemv-s8-r32-v1"
SEED = 0x20261019
SHAPES = ((4, 8), (8, 32), (16, 64), (4, 13))
SCOPES = ("core", "endtoend")

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

oracle = module("o3_independent_model", ROOT / "team/workloads/o3-gemv/model.py")

def inputs(m, k, dataset):
    if dataset not in (0, 1, 2):
        raise ValueError("dataset")
    if dataset == 0:
        x = [-128 if j % 2 == 0 else 127 for j in range(k)]
        a = [[(-128, 127, -1, 0, 1, 63, -64)[(i * 3 + j) % 7] for j in range(k)] for i in range(m)]
    elif dataset == 1:
        x = [((j * 29 + 11) % 255) - 127 for j in range(k)]
        a = [[((i * 61 + j * 17 + 19) % 256) - 128 for j in range(k)] for i in range(m)]
    else:
        rng = random.Random(SEED + m * 1009 + k)
        x = [rng.randrange(-128, 128) for _ in range(k)]
        a = [[rng.randrange(-128, 128) for _ in range(k)] for _ in range(m)]
    return a, x

def stores(m):
    lines = ["mv t6, a3"]
    for row in range(m):
        lines += [f"vs1r.v v{row}, (t6)", "addi t6, t6, 16"]
    return lines

def kernel(m, k, method, software, scope):
    """All A/x loads remain inside both timed scopes; no input packing."""
    if method not in ("vdot", "rvv") or software not in ("basic", "reuse") or scope not in SCOPES:
        raise ValueError("kernel configuration")
    body = []
    if scope == "endtoend":
        body += ["csrwi vstart, 0", "csrwi vcsr, 7", "vsetivli zero, 8, e8, m1, tu, mu"]
    group = 1 if software == "basic" else 4
    width = 8 if method == "vdot" else 16
    chunks = (k // 8) if method == "vdot" else ((k + 15) // 16)
    xbase = 24 if method == "vdot" else 28
    if software == "reuse":
        for block in range(chunks):
            count = 8 if method == "vdot" else min(16, k - 16 * block)
            body += [f"vsetivli zero, {count}, e8, m1, tu, mu",
                     f"addi t6, a2, {m * k + block * width}",
                     f"vle8.v v{xbase + block}, (t6)"]
    for first in range(0, m, group):
        size = min(group, m - first)
        body += [f"li t{i}, 0" for i in range(size)]
        for block in range(chunks):
            count = 8 if method == "vdot" else min(16, k - block * 16)
            xr = xbase + block if software == "reuse" else xbase
            body += [f"vsetivli zero, {count}, e8, m1, tu, mu"]
            if software == "basic":
                body += [f"addi t6, a2, {m * k + block * width}", f"vle8.v v{xr}, (t6)"]
            for lane in range(size):
                offset = (first + lane) * k + block * width
                body += [f"addi t6, a2, {offset}", f"vle8.v v{16 + lane}, (t6)"]
            if method == "vdot":
                for lane in range(size):
                    word = 0x0200000b | (20 + lane) << 7 | (16 + lane) << 15 | xr << 20
                    body += [f".word 0x{word:08x}"]
                body += ["vsetivli zero, 4, e32, m1, tu, mu"]
                for lane in range(size):
                    body += [f"vmv.x.s t6, v{20 + lane}", f"addw t{lane}, t{lane}, t6"]
            else:
                for lane in range(size):
                    body += [f"vwmul.vv v{20 + 2 * lane}, v{16 + lane}, v{xr}"]
                body += ["vsetivli zero, 4, e32, m1, tu, mu"]
                body += [f"vmv.v.i v{16 + lane}, 0" for lane in range(size)]
                body += [f"vsetivli zero, {count}, e16, m2, tu, mu"]
                for lane in range(size):
                    body += [f"vwredsum.vs v{16 + lane}, v{20 + 2 * lane}, v{16 + lane}"]
                body += ["vsetivli zero, 4, e32, m1, tu, mu"]
                for lane in range(size):
                    body += [f"vmv.x.s t6, v{16 + lane}", f"addw t{lane}, t{lane}, t6"]
        if method == "vdot":
            # Current ISA requires VL=8: the non-multiple tail is honest scalar work.
            for j in range(k // 8 * 8, k):
                body += [f"lb t4, {m * k + j}(a2)"]
                for lane in range(size):
                    body += [f"lb t6, {(first + lane) * k + j}(a2)",
                             "mulw t6, t6, t4", f"addw t{lane}, t{lane}, t6"]
        body += ["vsetivli zero, 4, e32, m1, tu, mu"]
        for lane in range(size):
            body += [f"vmv.v.i v{first + lane}, 0", f"vmv.s.x v{first + lane}, t{lane}"]
    body += ["vsetivli zero, 8, e8, m1, tu, mu", f"li t5, {m * k}"]
    if scope == "endtoend":
        body += stores(m)
    return body

def case(m, k, dataset, method, software, scope):
    a, x = inputs(m, k, dataset)
    results = [oracle.result_bytes(v).hex() for v in oracle.gemv(a, x)]
    packed = bytes(v & 255 for row in a for v in row) + bytes(v & 255 for v in x)
    packed += bytes((-len(packed)) % 16)
    before = [bytes((0x35 + 7 * reg + 19 * i) & 255 for i in range(16)).hex() for reg in range(32)]
    expected = before[:]
    expected[:m] = results
    return dict(id=f"gemv-{m}x{k}-{scope}-{software}-{method}",
                scenario=f"gemv-{m}x{k}-{scope}-{software}", method=method,
                n=m * k, dots=m * (k // 8), iterations=m * k,
                operands=[0, 16, 24], vtype=0, scratch=list(range(16, 32)),
                before=before, expected=expected,
                stream=[packed[i:i+16].hex() for i in range(0, len(packed), 16)],
                outputs=results, body=kernel(m, k, method, software, scope),
                m=m, k=k, software=software, scope=scope,
                input_layout="row-major signed int8 A[M][K] immediately followed by x[K]; no row padding",
                output_layout="M signed int32 values, each in a zero-high96 16-byte slot")

def generate(output, suite, dataset, shard=0, shards=1, shared_stream=True, variant="ours"):
    if suite not in ("smoke", "performance") or variant != "ours" or shards != 8 or not 0 <= shard < 8:
        raise ValueError("O3 requires exactly eight shape/scope shards and ours ISA")
    old = module("o3_frozen_assembly_renderer", ROOT / "team/workloads/unified-vdot/generate.py")
    m, k = SHAPES[shard // 2]
    scope = SCOPES[shard % 2]
    rows, plan = [], []
    for software in ("basic", "reuse"):
        for method in ("vdot", "rvv"):
            rows.append(case(m, k, dataset, method, software, scope))
    for repeat in range(2 if suite == "smoke" else 6):
        phase = "functional" if suite == "smoke" else ("first" if repeat == 0 else "warmup" if repeat == 1 else "measured")
        order = (0, 1, 2, 3) if repeat % 2 == 0 else (3, 2, 1, 0)
        for index in order:
            plan.append(dict(index=index, repeat=repeat, phase=phase, seq=len(plan), id=rows[index]["id"]))
    # Reuse only assembly scaffolding/C ABI, not old dot8 cases or expected outputs.
    old.corpus = lambda _suite, _dataset: (rows, plan)
    value = old.generate(output, suite, dataset, 0, 1, True, "ours")
    value.update(contract=CONTRACT, seed=SEED, shard=shard, shards=shards,
                 application="GEMV", m=m, k=k, scope=scope, no_input_packing=True,
                 model_sha256=hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest())
    out = Path(output)
    text = (out / "kernels.S").read_text()
    if scope == "core":
        needle = "  .word 0x51400013\n  fence rw, rw\n"
        if text.count(needle) != len(rows):
            raise ValueError("O3 output-store marker cardinality")
        text = text.replace(needle, needle + "".join("  " + line + "\n" for line in stores(m)))
        (out / "kernels.S").write_text(text)
    header = (out / "cases.h").read_text().replace("#endif", f'#define O3_CONTRACT "{CONTRACT}"\n#endif')
    (out / "cases.h").write_text(header)
    value["files"] = {name:hashlib.sha256((out / name).read_bytes()).hexdigest() for name in ("kernels.S", "cases.h")}
    (out / "manifest.json").write_text(json.dumps(value, indent=2) + "\n")
    return value

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--suite", choices=("smoke", "performance"), default="performance")
    p.add_argument("--dataset", type=int, choices=(0, 1, 2), default=0)
    p.add_argument("--shard", required=True, type=int)
    a = p.parse_args()
    v = generate(a.output, a.suite, a.dataset, a.shard, 8)
    print(json.dumps(dict(rows=len(v["rows"]), windows=len(v["plan"]), m=v["m"], k=v["k"], scope=v["scope"])))
