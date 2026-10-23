"""Exact R4 C-ABI artifacts and a bounded one-call retirement path.

Frozen arithmetic, UART, CSR and O2 checkers are loaded unchanged. Only the new
generation identity and explicitly specified call/return path are adapted.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
S1 = Path("team/optimizations/o2/r2-vector-accum")
ENTRY = Path("team/optimizations/o2/r2-select")
sys.path.append(str(ROOT / "team/optimizations/o2/r2-safe-tail"))
import linked_gate as original
from linked_gate import ELF, require, sha, blob, load, save, O3, REL, BASE, PINNED, verify_sources

S1_GATE_SHA = "ab07b578f5fe2dc7782ef9af64e722e051363d1dfddfcd0f1939efb209346b6d"
require(sha(ROOT / S1 / "gate.py") == S1_GATE_SHA, "frozen S1 gate drift")
s1 = load("r4_frozen_s1_gate", ROOT / S1 / "gate.py")
candidate = load("r4_entry_candidate", ROOT / ENTRY / "entry_candidate.py")
START, STOP = 0x51300013, 0x51400013
COUNTERS = [0xc0202773, 0xc0002873, 0xc00028f3, 0xc02027f3]
SOURCES = set(PINNED) | {str(S1 / "candidate.py")} | {
    str(ENTRY / name) for name in ("entry_candidate.py", "entry_gate.py", "entry_experiment.py")}
ARTIFACTS = {"vdot-perf.elf", "vdot-perf.bin", "kernels-reference.o", "gemv-reference.o", "data/manifest.json"}
PUBLIC_C_ARTIFACTS = {"api-c-smoke.c", "api-c-smoke.o", "api-c-linked.o"}


def signed(value, width):
    return value - (1 << width) if value & (1 << (width - 1)) else value


def jal_target(pc, word):
    imm = ((word >> 31) << 20) | (((word >> 21) & 1023) << 1) | \
          (((word >> 20) & 1) << 11) | (word & 0xff000)
    return pc + signed(imm, 21)


def walk(words):
    """Accept exactly one direct jal ra and its ret, with no other branches."""
    starts = [p for p, w in words.items() if w == START]
    stops = [p for p, w in words.items() if w == STOP]
    require(len(starts) == len(stops) == 1 and starts[0] < stops[0], "unique ordered R4 markers")
    pc, stop = starts[0], stops[0]
    link, calls, returns, result, visited = None, 0, 0, [], set()
    while True:
        require(pc in words and pc not in visited and len(result) < 20000, "escaped/repeated R4 path")
        visited.add(pc)
        word = words[pc]
        require(word & 3 == 3, "compressed R4 path")
        result.append((pc, word))
        if pc == stop:
            require(link is None and calls == returns == 1, "R4 call/return cardinality")
            break
        op, rd = word & 127, (word >> 7) & 31
        require(op != 0x63, "branch in R4 leaf path")
        if op == 0x6f:
            require(rd == 1 and calls == 0 and link is None, "unexpected or nested R4 call")
            target = jal_target(pc, word)
            require(target > stop and target in words and target % 4 == 0, "R4 call target")
            link, calls, pc = pc + 4, 1, target
        elif op == 0x67:
            require(word == 0x00008067 and link is not None and returns == 0, "unexpected R4 return")
            pc, link, returns = link, None, 1
        else:
            # All scalar destination forms used by the frozen body. Vector
            # rd fields are vector registers and must not be treated as x1.
            require(not (rd == 1 and (op in (0x03, 0x13, 0x1b, 0x17, 0x33, 0x37, 0x3b, 0x73)
                                         or (op == 0x57 and (word >> 12) & 7 == 7))),
                    "link register overwritten inside measured path")
            pc += 4
    require([w for _, w in result if w in COUNTERS] == COUNTERS, "R4 counter order")
    return result


def counter_adapter(repo):
    check = load("r4_private_counter_checker", Path(repo) / O3 / "check.py")
    check.base.walk = walk
    frozen_trace = check.base.trace_windows

    def trace(events, manifest, kernels):
        paths = [walk(kernels[p["index"]]) for p in manifest["plan"]]
        window, pos, active = -1, 0, False
        for event in events["RETIRE"]:
            if event["word"] == START:
                require(not active, "nested R4 trace marker")
                window, pos, active = window + 1, 0, True
            if active:
                require(window < len(paths), "extra R4 trace window")
                covered = paths[window][pos:pos + event["count"]]
                if event["count"] > 1:
                    require(all(w & 127 not in (0x63, 0x6f, 0x67) for _, w in covered),
                            "call/return in compressed retirement")
                pos += event["count"]
            if event["word"] == STOP:
                active = False
        return frozen_trace(events, manifest, kernels)

    check.base.trace_windows = trace
    return check


def regenerate(build):
    build = Path(build)
    manifest = json.loads((build / "data/manifest.json").read_text())
    receipt = json.loads((build / "build.json").read_text())
    snapshot = build / "source/repo"
    verify_sources(snapshot)
    require(set(receipt["snapshot_files"]) == SOURCES, "R4 source snapshot inventory")
    for rel, digest in receipt["snapshot_files"].items():
        require(sha(snapshot / rel) == digest, "R4 source snapshot drift: " + rel)
    generator = load("r4_exact_regenerator", snapshot / ENTRY / "entry_candidate.py")
    with tempfile.TemporaryDirectory(prefix="r4-entry-regenerate-") as temp:
        out = Path(temp) / "data"
        fresh = generator.generate(snapshot, out, manifest["r2_variant"], manifest["dataset"],
                                   manifest["shard"], manifest["suite"])
        require(fresh == manifest, "R4 exact manifest regeneration differs")
        for name in candidate.FILES:
            require((out / name).read_bytes() == (build / "data" / name).read_bytes(),
                    "R4 generated bytes changed: " + name)
    for name in ("main.c", "Makefile", "fixed-layout.ld"):
        require((build / "source" / name).read_bytes() == (snapshot / O3 / name).read_bytes(),
                "frozen harness/build source changed")
    return manifest


def semantic_check(code, row, repo):
    base = candidate.source(repo).load_base(repo)
    m, k = row["m"], row["k"]
    inputs = [base.inputs(m, k, d) for d in range(3)]
    inputs += [([[-128] * k for _ in range(m)], [-128] * k),
               ([[127] * k for _ in range(m)], [-128] * k)]
    rng = random.Random(0x5234 + 1009 * m + k)
    inputs += [([[rng.randrange(-128, 128) for _ in range(k)] for _ in range(m)],
                [rng.randrange(-128, 128) for _ in range(k)]) for _ in range(4)]
    for trial, (matrix, vector) in enumerate(inputs):
        machine = s1.Machine(matrix, vector, poison_seed=0x5234 + trial).execute(code)
        machine.check(matrix, vector, stored=True)
        require(machine.counts.get("vdot.vv", 0) == (row["dots"] if row["method"] == "vdot" else 0),
                "R4 model custom count")
    return dict(trials=len(inputs), full128=True, bounded_reads=True, poisoned_initial_registers=True)


def inspect(build, manifest, repo):
    build = Path(build)
    elf = ELF((build / "vdot-perf.elf").read_bytes())
    elf.executable()
    require(elf.binary() == (build / "vdot-perf.bin").read_bytes(), "R4 ELF/BIN mismatch")
    original.compiled_cases(elf, manifest)
    obj, public = [ELF((build / p).read_bytes()) for p in ("kernels-reference.o", "gemv-reference.o")]
    for ref in (obj, public):
        require(ref.kind == 1 and not any(s[1] in (4, 9) and s[5] for s in ref.sections),
                "R4 independent GNU object has relocations")
    require(obj.named[".text"][5] == 32768 and elf.named[".text"][5] == 40960,
            "R4 fixed complete text extent")
    audit = s1.auditor(repo)
    reports = []
    for i, row in enumerate(manifest["rows"]):
        name, api = f"t13_kernel_{i}", row["api_symbol"]
        address, length = elf.symbols[name][:2]
        code = elf.symbol_data(name)
        require(address == original.RAM + (i + 1) * 8192 and 0 < length <= 8192,
                "R4 fixed slot layout")
        require(code == obj.symbol_data(name), "R4 linked wrapper/reference differs")
        leaf = elf.symbol_data(api)
        require(leaf == obj.symbol_data(api) == public.symbol_data(api), "public callable bytes differ")
        require(leaf[:8] == struct.pack("<II", 0x00050613, 0x00058693) and
                leaf[-4:] == struct.pack("<I", 0x00008067), "public leaf ABI prologue/return")
        core = leaf[8:-4]
        counts = dict(sorted(Counter(audit.decode(w)[0] for w, in struct.iter_unpack("<I", core)).items()))
        require(counts == audit.source_counts(row["body"]), "R4 compiled/source body counts")
        words = {address + 4 * n: w for n, (w,) in enumerate(struct.iter_unpack("<I", code))}
        path = walk(words)
        start = next(n for n, (_, w) in enumerate(path) if w == COUNTERS[1])
        stop = next(n for n, (_, w) in enumerate(path) if w == COUNTERS[2])
        body_path = path[start + 2:stop - 1]
        require(len(body_path) == len(core) // 4 + 7, "R4 complete invocation instruction count")
        calls = [(p, w) for p, w in path if w & 127 == 0x6f]
        require(jal_target(*calls[0]) == elf.symbols[api][0], "call not bound to public symbol")
        require(sum(w & manifest["custom_mask"] == manifest["custom_match"] for _, w in path) ==
                (row["dots"] if row["method"] == "vdot" else 0), "R4 actual path custom count")
        reports.append(dict(id=row["id"], api_symbol=api, api_pc=elf.symbols[api][0],
                            api_sha256=hashlib.sha256(leaf).hexdigest(),
                            body_instructions=len(core) // 4, invocation_instructions=len(body_path),
                            entry_overhead_instructions=7, counts=counts,
                            semantics=semantic_check(core, row, repo)))
    return dict(status="R4_LINKED_CALLABLE_AND_COMPILED_MODEL_PASS_NOT_DIFFTEST", kernels=reports,
                elf_sha256=sha(build / "vdot-perf.elf"), image_sha256=sha(build / "vdot-perf.bin"))


def verify_build(build, repo):
    build, repo = Path(build), Path(repo)
    require(Path(__file__).resolve() == (repo / ENTRY / "entry_gate.py").resolve(),
            "loaded R4 gate from another checkout")
    for module, rel in ((candidate, ENTRY / "entry_candidate.py"), (s1, S1 / "gate.py"),
                        (original, REL / "linked_gate.py")):
        require(Path(module.__file__).resolve() == (repo / rel).resolve(), "loaded R4 module from another checkout")
    verify_sources(repo)
    receipt = json.loads((build / "build.json").read_text())
    require(receipt.get("kind") == "nexus-am-riscv64-xs" and receipt.get("exit_code") == 0,
            "no successful real R4 AM build")
    require(receipt.get("contract") == candidate.CONTRACT and set(receipt["artifacts"]) == ARTIFACTS,
            "R4 build contract/artifacts")
    for rel in SOURCES:
        require(receipt["snapshot_files"].get(rel) == sha(repo / rel), "R4 selected source drift: " + rel)
    for name, digest in receipt["artifacts"].items():
        require(sha(build / name) == digest, "R4 artifact drift: " + name)
    require(set(receipt.get("public_c_link_test", {})) == PUBLIC_C_ARTIFACTS, "C caller artifact inventory")
    for name, digest in receipt["public_c_link_test"].items():
        require(sha(build / name) == digest, "C caller artifact drift: " + name)
    manifest = regenerate(build)
    require(receipt["selection"] == {k: manifest["r2_variant" if k == "variant" else k]
                                     for k in ("suite", "dataset", "shard", "variant")}, "R4 selection drift")
    return inspect(build, manifest, repo)


def paired_layout(left, right):
    left, right = Path(left), Path(right)
    e0, e1 = [ELF((p / "vdot-perf.elf").read_bytes()) for p in (left, right)]
    result = s1.paired_layout(e0, e1, (left / "vdot-perf.bin").read_bytes(),
                             (right / "vdot-perf.bin").read_bytes())
    m0, m1 = [json.loads((p / "data/manifest.json").read_text()) for p in (left, right)]
    require(m0["plan"] == m1["plan"], "R4 paired invocation order")
    for r0, r1 in zip(m0["rows"], m1["rows"]):
        require({k: v for k, v in r0.items() if k not in ("body", "r2_variant")} ==
                {k: v for k, v in r1.items() if k not in ("body", "r2_variant")}, "R4 fair input/state")
        require(e0.symbols[r0["api_symbol"]][0] == e1.symbols[r1["api_symbol"]][0],
                "R4 paired public entry address")
    return result
