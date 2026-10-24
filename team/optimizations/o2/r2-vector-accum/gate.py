"""S1 strict artifact adapter; preserve the frozen ELF, CSR and retirement gates."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
S1 = Path("team/optimizations/o2/r2-vector-accum")
sys.path.append(str(ROOT / "team/optimizations/o2/r2-safe-tail"))
import linked_gate as original
from linked_gate import ELF, require, sha, blob, load, save, O3, REL, BASE, PINNED, verify_sources

MODEL = ROOT / REL / "machine_model.py"
MODEL_SHA = "8fb2ac208d8db9083464fb839c06b46ec365234d72b819822563830dad90171e"
require(hashlib.sha256(MODEL.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == MODEL_SHA,
        "frozen machine-model drift")
old_model = load("s1_private_machine_model", MODEL)

def is_vadd(word):
    # funct6=000000, vm=1, funct3=000, opcode=1010111.
    return word & 0xfe00707f == 0x02000057

class Machine(old_model.Machine):
    """Only add full-width INT32 vadd support; delegate every old instruction."""
    def execute(self, code):
        require(len(code) > 0 and len(code) % 4 == 0, "fixed-width body required")
        for word, in struct.iter_unpack("<I", code):
            if is_vadd(word):
                require((self.vl, self.sew, self.lmul, self.ta, self.ma, self.vstart) ==
                        (4, 32, 1, 0, 0, 0), "S1 vadd must use e32/VL4/m1/tu/mu/vstart0")
                rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
                require(rd < self.m and b == rd and 20 <= a < 24, "S1 accumulator/partial register")
                left = struct.unpack("<4I", self.get(a, 16))
                right = struct.unpack("<4I", self.get(b, 16))
                self.put(rd, struct.pack("<4I", *((x + y) & 0xffffffff for x, y in zip(left, right))), 16)
                self.counts["vadd.vv"] += 1
            else:
                super().execute(struct.pack("<I", word))
        return self

def auditor(repo):
    value = load("s1_private_instruction_auditor", Path(repo) / "team/optimizations/o2/r2-kernel-audit/audit.py")
    old_decode = value.decode
    def decode(word):
        if is_vadd(word):
            rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
            return "vadd.vv", f"v{rd}, v{b}, v{a}"
        return old_decode(word)
    value.decode = decode
    return value

def body_bytes(code, audit):
    words = list(struct.unpack("<" + "I" * (len(code) // 4), code))
    start, stop = words.index(audit.START), words.index(audit.STOP)
    return struct.pack("<" + "I" * (stop - start - 11), *words[start + 6:stop - 5])

def semantic_check(elf, manifest, repo, random_trials=4):
    candidate = load("s1_semantic_source", Path(repo) / S1 / "candidate.py")
    base = candidate.load_base(repo)
    audit = auditor(repo)
    reports = []
    for i, row in enumerate(manifest["rows"]):
        require(row["scratch"] == list(range(16, 32)), "scratch budget changed")
        code = body_bytes(elf.symbol_data(f"t13_kernel_{i}"), audit)
        m, k = row["m"], row["k"]
        vectors = [base.inputs(m, k, d) for d in range(3)]
        vectors += [([[-128] * k for _ in range(m)], [-128] * k),
                    ([[127] * k for _ in range(m)], [-128] * k)]
        rng = random.Random(0x5331 + m * 1009 + k)
        vectors += [([[rng.randrange(-128, 128) for _ in range(k)] for _ in range(m)],
                     [rng.randrange(-128, 128) for _ in range(k)]) for _ in range(random_trials)]
        counts = None
        for trial, (matrix, vector) in enumerate(vectors):
            machine = Machine(matrix, vector, poison_seed=trial + 0x5331).execute(code)
            machine.check(matrix, vector, stored=row["scope"] == "endtoend")
            require(machine.counts.get("vdot.vv", 0) == (row["dots"] if row["method"] == "vdot" else 0),
                    "model custom count")
            counts = dict(sorted(machine.counts.items()))
        reports.append(dict(id=row["id"], trials=len(vectors), rows_checked=m * len(vectors),
                            full128=True, row_bounded_reads=True, poisoned_initial_registers=True,
                            counts=counts))
    return reports

def regenerate(build):
    build = Path(build)
    manifest = json.loads((build / "data/manifest.json").read_text())
    receipt = json.loads((build / "build.json").read_text())
    snapshot = build / "source/repo"
    verify_sources(snapshot)
    require(set(receipt["snapshot_files"]) == set(PINNED) | {str(S1 / "candidate.py")},
            "source snapshot inventory")
    for name, digest in receipt["snapshot_files"].items():
        require(sha(snapshot / name) == digest, "source snapshot drift: " + name)
    candidate = load("s1_exact_regenerator", snapshot / S1 / "candidate.py")
    with tempfile.TemporaryDirectory(prefix="s1-regenerate-") as tmp:
        out = Path(tmp) / "data"
        fresh = candidate.generate(snapshot, out, manifest["r2_variant"], manifest["dataset"],
                                   manifest["shard"], manifest["suite"])
        require(fresh == manifest, "S1 manifest differs from exact regeneration")
        for name in ("kernels.S", "cases.h"):
            require((out / name).read_bytes() == (build / "data" / name).read_bytes(),
                    "generated bytes changed: " + name)
    for name in ("main.c", "Makefile", "fixed-layout.ld"):
        require((build / "source" / name).read_bytes() == (snapshot / O3 / name).read_bytes(),
                "original harness/build source changed")
    return manifest

def paired_layout(e0, e1, binary0, binary1):
    """The loaded image may differ ONLY inside the four fixed kernel slots."""
    ram, slot = original.RAM, 8192
    entries = [ram + (i + 1) * slot for i in range(4)]
    for elf in (e0, e1):
        require([elf.symbols[f"t13_kernel_{i}"][0] for i in range(4)] == entries,
                "paired kernel addresses are not the fixed arena")
        require(elf.named[".text"][3] == ram and elf.named[".text"][5] == 5 * slot,
                "size-dependent kernel section suffix")
    def allocated(elf):
        return {name: [s[i] for i in (1, 2, 3, 5, 8)]
                for name, s in sorted(elf.named.items()) if s[2] & 2}
    require(e0.entry == e1.entry and allocated(e0) == allocated(e1),
            "paired allocated section layout differs")
    require(len(binary0) == len(binary1) and len(binary0) >= 5 * slot,
            "paired loaded image extent differs")
    outside0 = binary0[:slot] + binary0[5 * slot:]
    outside1 = binary1[:slot] + binary1[5 * slot:]
    require(outside0 == outside1, "paired non-kernel loaded bytes differ")
    return dict(kernel_entries=entries, kernel_slot_bytes=slot,
                nonkernel_bytes=len(outside0), nonkernel_sha256=hashlib.sha256(outside0).hexdigest(),
                allocated_sections=allocated(e0), loaded_bytes=len(binary0))

def verify_build(build, repo):
    build, repo = Path(build), Path(repo)
    verify_sources(repo)
    receipt = json.loads((build / "build.json").read_text())
    require(receipt.get("kind") == "nexus-am-riscv64-xs" and receipt.get("exit_code") == 0,
            "no successful real AM build")
    require(receipt.get("s1_candidate_sha256") == sha(repo / S1 / "candidate.py"),
            "candidate identity differs from selected S1 source")
    require(receipt["snapshot_files"][str(S1 / "candidate.py")] == receipt["s1_candidate_sha256"],
            "snapshot candidate identity")
    require(set(receipt["artifacts"]) ==
            {"vdot-perf.elf", "vdot-perf.bin", "kernels-reference.o", "data/manifest.json"},
            "build artifact inventory")
    for name, digest in receipt["artifacts"].items():
        require(sha(build / name) == digest, "build artifact drift: " + name)
    manifest = regenerate(build)
    selection = {k: manifest["r2_variant" if k == "variant" else k] for k in ("suite", "dataset", "shard", "variant")}
    require(selection == receipt["selection"], "build selection drift")
    result = original.inspect(build / "vdot-perf.elf", build / "vdot-perf.bin",
                              build / "kernels-reference.o", manifest, auditor(repo))
    elf = ELF((build / "vdot-perf.elf").read_bytes())
    reference = ELF((build / "kernels-reference.o").read_bytes())
    require(reference.named[".text"][5] == 4 * 8192 and
            not any(s[1] in (4, 9) and s[5] for s in reference.sections),
            "kernel reference must have four exact slots and no relocations")
    entries = [elf.symbols[f"t13_kernel_{i}"][:2] for i in range(4)]
    require(manifest["kernel_slot_bytes"] == 8192 and manifest["assembler_relaxation"] is False and
            [p[0] for p in entries] == [original.RAM + (i + 1) * 8192 for i in range(4)] and
            elf.named[".text"][5] == 5 * 8192 and
            all(address % 8192 == 0 and 0 < length <= 8192 for address, length in entries) and
            all(entries[i][0] - entries[0][0] == i * 8192 for i in range(4)),
            "kernel exceeds fixed equal slot layout")
    result["kernel_entries"] = [address for address, _ in entries]
    result["semantics"] = semantic_check(elf, manifest, repo)
    result.update(status="S1_LINKED_ELF_AND_COMPILED_MODEL_PASS_NOT_DIFFTEST",
                  manifest_sha256=sha(build / "data/manifest.json"))
    return result

