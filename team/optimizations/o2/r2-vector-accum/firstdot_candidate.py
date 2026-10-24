"""First-block initialization in the frozen R4 C-ABI harness.

Each generation owns its renderer modules. The payload keeps the R4 harness
banner so the baseline BIN can be compared byte-for-byte to T17; the manifest,
build and run use the independent firstdot contract. No stable library changes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REL = Path("team/optimizations/o2/r2-vector-accum")
ENTRY = Path("team/optimizations/o2/r2-select")
CONTRACT = "r2-s1-firstdot-c-abi-v1"
HARNESS = "r4-gemv-c-abi-entry-v1"
FILES = ("kernels.S", "cases.h", "gemv.S", "gemv.h")
PINS = {
    str(ENTRY / "entry_candidate.py"): "a19224bb3b659615e3a1ca5c7db1bcb0e6af90649b098f8b39e3af6021d42edf",
    str(REL / "candidate.py"): "0270736b5c09e160626eb7b32d8e760faa193bf05761fea824a979108c3717b9",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def first_dot(body, m, k, method, software):
    """Promote only each group's first dot result; retain later e32 adds/tail.

    This pure transformation is the checked first_dot_probe-v1 algorithm,
    separated from that probe's global renderer mutation and build-only entry.
    Host validation compares all 16 outputs against the frozen probe function.
    """
    original = list(body)
    require(method in ("vdot", "rvv") and software in ("basic", "reuse"), "method/software")
    require((m, k) in ((4, 8), (8, 32), (16, 64), (4, 13)), "supported shape")
    if method == "rvv":
        return original
    group = 1 if software == "basic" else 4
    groups, chunks = m // group, k // 8
    positions = [i for i, line in enumerate(original) if line.startswith(".word ")]
    require(len(positions) == m * chunks, "original dot count")
    removed, replacements = set(), {}
    for ordinal, first in enumerate(range(0, m, group)):
        clear = ["vsetivli zero, 4, e32, m1, tu, mu"]
        clear += [f"vmv.v.i v{first + lane}, 0" for lane in range(group)]
        locations = [i for i in range(len(original) - len(clear) + 1)
                     if original[i:i + len(clear)] == clear]
        require(len(locations) == 1, "unique original group initialization")
        start = locations[0]
        removed.update(range(start, start + len(clear)))
        dots = positions[ordinal * group * chunks:ordinal * group * chunks + group]
        require(dots == list(range(dots[0], dots[0] + group)) and start + len(clear) < dots[0],
                "first block instruction grouping")
        for lane, index in enumerate(dots):
            word = int(original[index].split()[1], 0)
            expected = 0x0200000b | (20 + lane) << 7 | (16 + lane) << 15 | 24 << 20
            require(word == expected, "first dot register assignment changed")
            replacements[index] = f".word 0x{((word & ~(31 << 7)) | ((first + lane) << 7)):08x}"
        add = ["vsetivli zero, 4, e32, m1, tu, mu"]
        add += [f"vadd.vv v{first + lane}, v{first + lane}, v{20 + lane}" for lane in range(group)]
        after = dots[-1] + 1
        require(original[after:after + len(add)] == add, "first block accumulation changed")
        removed.update(range(after, after + len(add)))
    require(len(removed) == 2 * m + 2 * groups and not (set(replacements) & removed),
            "unexpected transformation size")
    value = [replacements.get(i, line) for i, line in enumerate(original) if i not in removed]
    require(sum(line.startswith(".word ") for line in value) == m * chunks, "changed dot count")
    return value


def generate(repo, output, variant, dataset, shard, suite="performance"):
    repo, output = Path(repo).resolve(), Path(output)
    require(variant in ("s1", "firstdot"), "firstdot variant")
    require(suite == "performance" and shard in (1, 3, 5, 7) and dataset in range(3), "firstdot cohort")
    require(Path(__file__).resolve() == repo / REL / "firstdot_candidate.py", "generator checkout")
    for path, digest in PINS.items():
        require(sha(repo / path) == digest, "frozen generator changed: " + path)
    entry = module("firstdot_private_entry", repo / ENTRY / "entry_candidate.py")
    old_source = entry.source

    def source(root):
        s1 = old_source(root)
        original_kernel = s1.kernel
        def kernel(base, m, k, method, software, scope, selected):
            require(selected == "s1", "firstdot parent must be S1")
            body = original_kernel(base, m, k, method, software, scope, selected)
            return first_dot(body, m, k, method, software) if variant == "firstdot" else body
        s1.kernel = kernel
        return s1

    entry.source = source
    manifest = entry.generate(repo, output, "s1", dataset, shard, suite)
    require(manifest["contract"] == HARNESS, "frozen harness banner changed")
    manifest.update(firstdot_contract=CONTRACT, r2_variant=variant,
                    firstdot_candidate_sha256=sha(Path(__file__)), parent_variant="s1",
                    runtime_qualified=False, stable_default_changed=False)
    for row in manifest["rows"]:
        row["r2_variant"] = variant
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
