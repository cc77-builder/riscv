#!/usr/bin/env python3
"""Opt-in S2: replace only the scalar 4x13 tail; keep frozen O3 untouched."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = "a89648d78bc954d9e27a78b987d3fef63cc1ab93"
PINS = {
    "team/workloads/o3-gemv/generate.py": "9cb0c6b755daa9b05d346b4b48cb80246852d4a8",
    "team/workloads/o3-gemv/model.py": "0be812d0fc112af863fe5adf3be3794e16c7bdf4",
    "team/workloads/unified-vdot/generate.py": "90cc41079c27ebfe146321d4bf01e2ee0426dae9",
}
CONTRACT = "o2-r2-safe-tail-s2-v1"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def blob(data):
    # Accept normal Windows checkout CRLF conversion, not other source changes.
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def load_base(repo):
    repo = Path(repo).resolve()
    for path in list(PINS)[:2]:
        require(blob((repo / path).read_bytes()) == PINS[path], "baseline drift: " + path)
    path = repo / "team/workloads/o3-gemv/generate.py"
    spec = importlib.util.spec_from_file_location("r2_frozen_o3", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def scalar_tail(first, size):
    lines = []
    for j in range(8, 13):
        lines += [f"lb t4, {52 + j}(a2)"]
        for lane in range(size):
            lines += [f"lb t6, {(first + lane) * 13 + j}(a2)",
                      "mulw t6, t6, t4", f"addw t{lane}, t{lane}, t6"]
    return lines

def safe_tail(first, size):
    require(size in (1, 4) and 0 <= first and first + size <= 4, "tail group")
    # All reused operands are dead after their full-block partial sums are in t0..t3.
    lines = ["vsetivli zero, 8, e8, m1, tu, mu", "vmv.v.i v24, 0"]
    lines += [f"vmv.v.i v{16 + lane}, 0" for lane in range(size)]
    lines += ["vsetivli zero, 5, e8, m1, tu, mu",
              "addi t6, a2, 60", "vle8.v v24, (t6)"]
    for lane in range(size):
        lines += [f"addi t6, a2, {(first + lane) * 13 + 8}",
                  f"vle8.v v{16 + lane}, (t6)"]
    # tu preserves the explicit zeros in lanes 5..7. Custom dot8 still requires VL=8.
    lines += ["vsetivli zero, 8, e8, m1, tu, mu"]
    for lane in range(size):
        word = 0x0200000b | (20 + lane) << 7 | (16 + lane) << 15 | 24 << 20
        lines += [f".word 0x{word:08x}"]
    lines += ["vsetivli zero, 4, e32, m1, tu, mu"]
    for lane in range(size):
        lines += [f"vmv.x.s t6, v{20 + lane}", f"addw t{lane}, t{lane}, t6"]
    return lines

def kernel(base, m, k, method, software, scope, variant="s2"):
    require(variant in ("s0", "s2"), "variant must be s0 or s2")
    require((m, k) in base.SHAPES, "shape outside frozen O3 contract")
    body = base.kernel(m, k, method, software, scope)
    if variant == "s0" or method != "vdot" or (m, k) != (4, 13):
        return body
    group = 1 if software == "basic" else 4
    for first in range(0, 4, group):
        old = scalar_tail(first, group)
        matches = [i for i in range(len(body) - len(old) + 1) if body[i:i + len(old)] == old]
        require(len(matches) == 1, "scalar tail changed or ambiguous")
        i = matches[0]
        body[i:i + len(old)] = safe_tail(first, group)
    require(not any(line.startswith(("lb ", "mulw ")) for line in body), "scalar tail remains")
    return body

def make_case(base, m, k, dataset, method, software, scope, variant):
    row = base.case(m, k, dataset, method, software, scope)
    row["body"] = kernel(base, m, k, method, software, scope, variant)
    if method == "vdot":
        row["dots"] = sum(line.startswith(".word ") for line in row["body"])
    row["r2_variant"] = variant
    return row

def generate(repo, output, variant, dataset, shard, suite="smoke"):
    """Emit the original four-case C ABI/markers, never run an EMU implicitly."""
    require(variant in ("s0", "s2"), "variant")
    require(shard in (4, 5, 6, 7), "screen only 16x64 and 4x13, core/endtoend")
    require(suite in ("smoke", "performance"), "suite")
    require(not Path(output).exists(), "output directory must not exist")
    repo = Path(repo).resolve()
    renderer = "team/workloads/unified-vdot/generate.py"
    require(blob((repo / renderer).read_bytes()) == PINS[renderer], "renderer drift")
    base = load_base(repo)
    original_case = base.case
    # A fresh private module for each call avoids mutating any shared module or source.
    def case(m, k, ds, method, software, scope):
        row = original_case(m, k, ds, method, software, scope)
        row["body"] = kernel(base, m, k, method, software, scope, variant)
        if method == "vdot":
            row["dots"] = sum(s.startswith(".word ") for s in row["body"])
        row["r2_variant"] = variant
        return row
    base.case = case
    base.CONTRACT = CONTRACT
    value = base.generate(output, suite, dataset, shard, 8)
    value.update(r2_variant=variant, source_base=BASE, baseline_git_blobs=PINS,
                 acceptance="generated-only; NEMU/EMU and cycle screening pending",
                 candidate_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (Path(output) / "manifest.json").write_text(json.dumps(value, indent=2) + "\n")
    return value

def s1_register_plan(method, first=0, k=64):
    """Design-only allocation: accumulators are the current group's legal outputs."""
    require(method in ("vdot", "rvv") and first in (0, 4, 8, 12) and k in (8, 32, 64), "S1 plan domain")
    slots = {
        "output_accumulators": set(range(first, first + 4)),
        "a_loads": set(range(16, 20)),
        "partials": set(range(20, 24 if method == "vdot" else 28)),
        "x_blocks": set(range(24, 24 + k // 8)) if method == "vdot"
                    else set(range(28, 28 + (k + 15) // 16)),
    }
    occupied = set()
    for regs in slots.values():
        require(not occupied & regs and all(0 <= r < 32 for r in regs), "overlap")
        occupied |= regs
    require(set.union(*(v for n, v in slots.items() if n != "output_accumulators")) <= set(range(16, 32)), "scratch budget")
    return {name: sorted(regs) for name, regs in slots.items()}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--variant", choices=("s0", "s2"), required=True)
    p.add_argument("--dataset", type=int, choices=(0, 1, 2), default=0)
    p.add_argument("--shard", type=int, choices=(4, 5, 6, 7), required=True)
    p.add_argument("--suite", choices=("smoke", "performance"), default="smoke")
    a = p.parse_args()
    try:
        result = generate(a.repo, a.output, a.variant, a.dataset, a.shard, a.suite)
    except (ValueError, OSError) as exc:
        p.exit(2, f"R2_GENERATION_REJECTED: {exc}\n")
    print(json.dumps({"status": "R2_SOURCES_GENERATED_NOT_EXECUTED", "variant": a.variant,
                      "rows": len(result["rows"]), "windows": len(result["plan"])}))
