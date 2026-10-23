"""Independent S1 GEMV candidate; frozen S0/S2 source and golden data stay intact."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

REL = Path("team/optimizations/o2/r2-vector-accum")
CONTRACT = "o2-r2-vector-accum-s1-v2-fixed-layout"
PINS = {
    "team/workloads/o3-gemv/generate.py": "9cb0c6b755daa9b05d346b4b48cb80246852d4a8",
    "team/workloads/o3-gemv/model.py": "0be812d0fc112af863fe5adf3be3794e16c7bdf4",
    "team/workloads/unified-vdot/generate.py": "90cc41079c27ebfe146321d4bf01e2ee0426dae9",
}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def blob(data):
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def load_base(repo):
    repo = Path(repo).resolve()
    for name, digest in PINS.items():
        require(blob((repo / name).read_bytes()) == digest, "frozen source drift: " + name)
    spec = importlib.util.spec_from_file_location("s1_private_o3", repo / "team/workloads/o3-gemv/generate.py")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    return base

def kernel(base, m, k, method, software, scope, variant):
    require(variant in ("s0", "s1"), "variant")
    require((m, k) in base.SHAPES and scope in base.SCOPES, "shape/scope")
    require(method in ("vdot", "rvv") and software in ("basic", "reuse"), "method/software")
    if variant == "s0":
        return base.kernel(m, k, method, software, scope)
    body = []
    if scope == "endtoend":
        body += ["csrwi vstart, 0", "csrwi vcsr, 7", "vsetivli zero, 8, e8, m1, tu, mu"]
    group = 1 if software == "basic" else 4
    width = 8 if method == "vdot" else 16
    chunks = k // 8 if method == "vdot" else (k + 15) // 16
    xbase = 24 if method == "vdot" else 28
    if software == "reuse":
        for block in range(chunks):
            count = 8 if method == "vdot" else min(16, k - block * 16)
            body += [f"vsetivli zero, {count}, e8, m1, tu, mu",
                     f"addi t6, a2, {m * k + block * width}", f"vle8.v v{xbase + block}, (t6)"]
    for first in range(0, m, group):
        size = min(group, m - first)
        # These are already the current group's declared output registers.
        # Initialize all 128 bits INSIDE the measured body, not in the harness.
        body += ["vsetivli zero, 4, e32, m1, tu, mu"]
        body += [f"vmv.v.i v{first + lane}, 0" for lane in range(size)]
        for block in range(chunks):
            count = 8 if method == "vdot" else min(16, k - block * 16)
            xr = xbase + block if software == "reuse" else xbase
            body += [f"vsetivli zero, {count}, e8, m1, tu, mu"]
            if software == "basic":
                body += [f"addi t6, a2, {m * k + block * width}", f"vle8.v v{xr}, (t6)"]
            for lane in range(size):
                body += [f"addi t6, a2, {(first + lane) * k + block * width}",
                         f"vle8.v v{16 + lane}, (t6)"]
            if method == "vdot":
                for lane in range(size):
                    word = 0x0200000b | (20 + lane) << 7 | (16 + lane) << 15 | xr << 20
                    body += [f".word 0x{word:08x}"]
                body += ["vsetivli zero, 4, e32, m1, tu, mu"]
                body += [f"vadd.vv v{first + lane}, v{first + lane}, v{20 + lane}" for lane in range(size)]
            else:
                body += [f"vwmul.vv v{20 + 2 * lane}, v{16 + lane}, v{xr}" for lane in range(size)]
                body += [f"vsetivli zero, {count}, e16, m2, tu, mu"]
                # Scalar seed/destination uses ONE register regardless of LMUL.
                # tu preserves the three previously cleared high INT32 lanes.
                body += [f"vwredsum.vs v{first + lane}, v{20 + 2 * lane}, v{first + lane}"
                         for lane in range(size)]
        if method == "vdot" and k % 8:
            # S1 alone: retain the honest scalar tail; this is NOT S1+S2.
            body += [f"li t{lane}, 0" for lane in range(size)]
            for j in range(k // 8 * 8, k):
                body += [f"lb t4, {m * k + j}(a2)"]
                for lane in range(size):
                    body += [f"lb t6, {(first + lane) * k + j}(a2)",
                             "mulw t6, t6, t4", f"addw t{lane}, t{lane}, t6"]
            body += ["vsetivli zero, 4, e32, m1, tu, mu"]
            for lane in range(size):
                body += [f"vmv.x.s t6, v{first + lane}", f"addw t{lane}, t{lane}, t6",
                         f"vmv.s.x v{first + lane}, t{lane}"]
    body += ["vsetivli zero, 8, e8, m1, tu, mu", f"li t5, {m * k}"]
    if scope == "endtoend":
        body += base.stores(m)
    return body

def generate(repo, output, variant, dataset, shard, suite="performance"):
    require(variant in ("s0", "s1") and type(dataset) is int and dataset in range(3), "selection")
    require(type(shard) is int and shard in range(8) and suite in ("smoke", "performance"), "suite/shard")
    output, repo = Path(output), Path(repo).resolve()
    require(not output.exists(), "new output directory required")
    base = load_base(repo)
    original_case = base.case
    def case(m, k, ds, method, software, scope):
        row = original_case(m, k, ds, method, software, scope)
        row["body"] = kernel(base, m, k, method, software, scope, variant)
        row["dots"] = sum(line.startswith(".word ") for line in row["body"]) if method == "vdot" else row["dots"]
        row["r2_variant"] = variant
        return row
    base.case = case
    base.CONTRACT = CONTRACT
    value = base.generate(output, suite, dataset, shard, 8)
    # Disable assembler relaxation explicitly: GNU can otherwise emit ALIGN
    # relocations despite -mno-relax and leave a size-dependent section suffix.
    # Fixed 8 KiB slots must also leave main/AM and every non-kernel byte fixed.
    # Historical S2 and rejected v1 samples are never reused for this layout.
    assembly = (output / "kernels.S").read_text()
    require(assembly.startswith(".option norvc\n.text\n"), "frozen renderer prefix changed")
    assembly = assembly.replace(".option norvc\n.text\n", ".option norvc\n.option norelax\n.text\n", 1)
    require(assembly.count(".balign 4096") == 8, "frozen renderer alignment changed")
    assembly = assembly.replace(".balign 4096", ".balign 8192")
    (output / "kernels.S").write_text(assembly)
    value["files"] = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                      for name in ("kernels.S", "cases.h")}
    value.update(r2_variant=variant, baseline_git_blobs=PINS,
                 candidate_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 acceptance="generation only; compiled model and live DiffTest are separate",
                 s1_s2_combined=False, kernel_slot_bytes=8192, assembler_relaxation=False)
    (output / "manifest.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return value

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--variant", choices=("s0", "s1"), required=True)
    p.add_argument("--dataset", type=int, choices=range(3), default=0)
    p.add_argument("--shard", type=int, choices=range(8), required=True)
    p.add_argument("--suite", choices=("smoke", "performance"), default="performance")
    a = p.parse_args()
    print(json.dumps({"status": "GENERATED_NOT_EXECUTED", "windows":
        len(generate(a.repo, a.output, a.variant, a.dataset, a.shard, a.suite)["plan"])}))

