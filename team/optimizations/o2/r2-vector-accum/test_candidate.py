"""Actual GNU instruction/model tests and adversarial build identity checks."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import candidate
import gate
import experiment

ROOT = Path(__file__).resolve().parents[4]
SHAPES = ((4, 8), (8, 32), (16, 64), (4, 13))

@unittest.skipUnless(shutil.which("riscv64-linux-gnu-gcc"), "actual GNU RISC-V assembler required")
class CompiledSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="s1-compiled-tests-")
        cls.root = Path(cls.tmp.name)
        cls.base = candidate.load_base(ROOT)
        cls.cases = {}
        text = [".option norvc", ".text"]
        for m, k in SHAPES:
            for scope in ("core", "endtoend"):
                for software in ("basic", "reuse"):
                    for method in ("vdot", "rvv"):
                        key = (m, k, scope, software, method)
                        name = "test_" + str(len(cls.cases))
                        body = "\n".join(candidate.kernel(cls.base, m, k, method, software, scope, "s1"))
                        cls.cases[key] = (name, body)
                        text += [".global " + name, ".type " + name + ",@function", name + ":", body,
                                 ".size " + name + ", .-" + name]
        source = cls.root / "all.S"
        source.write_text("\n".join(text) + "\n")
        cls.assemble(source, cls.root / "all.o")
        cls.elf = gate.ELF((cls.root / "all.o").read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @staticmethod
    def assemble(source, output, norelax_flag=True):
        flags = ["-mno-relax"] if norelax_flag else []
        subprocess.run(["riscv64-linux-gnu-gcc", "-march=rv64gcv", "-mabi=lp64d", *flags,
                        "-c", str(source), "-o", str(output)], check=True, capture_output=True)

    def check_body(self, key, code, inputs=None):
        m, k, scope, _, _ = key
        matrix, vector = inputs or self.base.inputs(m, k, 0)
        machine = gate.Machine(matrix, vector, poison_seed=41).execute(code)
        machine.check(matrix, vector, stored=scope == "endtoend")

    def altered(self, key, before, after):
        _, body = self.cases[key]
        self.assertIn(before, body)
        source = self.root / "mutant.S"
        source.write_text(".option norvc\n.text\n.global mutant\n.type mutant,@function\nmutant:\n" +
                          body.replace(before, after, 1) + "\n.size mutant, .-mutant\n")
        self.assemble(source, self.root / "mutant.o")
        return gate.ELF((self.root / "mutant.o").read_bytes()).symbol_data("mutant")

    def test_all_kernels_three_datasets(self):
        for key, (name, _) in self.cases.items():
            for dataset in range(3):
                with self.subTest(key=key, dataset=dataset):
                    self.check_body(key, self.elf.symbol_data(name), self.base.inputs(key[0], key[1], dataset))

    def test_signed_extremes(self):
        for key, (name, _) in self.cases.items():
            m, k = key[:2]
            for a in (-128, 127):
                with self.subTest(key=key, a=a):
                    self.check_body(key, self.elf.symbol_data(name), ([[a] * k for _ in range(m)], [-128] * k))

    def test_generated_assembly_has_no_relaxable_padding(self):
        for variant in ("s0", "s1"):
            out = self.root / ("layout-" + variant)
            candidate.generate(ROOT, out, variant, 0, 5, "smoke")
            # Exercise the source directive even on toolchains where the GCC
            # -mno-relax flag would happen to suppress all alignment relocations.
            self.assemble(out / "kernels.S", out / "kernels.o", norelax_flag=False)
            elf = gate.ELF((out / "kernels.o").read_bytes())
            self.assertEqual(elf.named[".text"][5], 4 * 8192)
            self.assertFalse(any(s[1] in (4, 9) and s[5] for s in elf.sections))
            self.assertEqual([elf.symbols[f"t13_kernel_{i}"][0] for i in range(4)],
                             [i * 8192 for i in range(4)])

    def test_missing_accumulator_initialization(self):
        key = (16, 64, "endtoend", "reuse", "vdot")
        code = self.altered(key, "vmv.v.i v0, 0", "")
        with self.assertRaisesRegex(ValueError, "full 128-bit"):
            self.check_body(key, code)

    def test_wrong_accumulation_width(self):
        key = (16, 64, "endtoend", "reuse", "vdot")
        code = self.altered(key, "vsetivli zero, 4, e32, m1, tu, mu\nvadd.vv",
                            "vsetivli zero, 4, e16, m1, tu, mu\nvadd.vv")
        with self.assertRaisesRegex(ValueError, "S1 vadd"):
            self.check_body(key, code)

    def test_masked_accumulation_rejected(self):
        key = (16, 64, "endtoend", "reuse", "vdot")
        words = list(struct.unpack("<" + "I" * (len(self.elf.symbol_data(self.cases[key][0])) // 4),
                                   self.elf.symbol_data(self.cases[key][0])))
        index = next(i for i, word in enumerate(words) if gate.is_vadd(word))
        words[index] ^= 1 << 25
        with self.assertRaisesRegex(ValueError, "unsupported instruction"):
            self.check_body(key, struct.pack("<" + "I" * len(words), *words))

    def test_wrong_accumulator_register(self):
        key = (16, 64, "endtoend", "reuse", "vdot")
        code = self.altered(key, "vadd.vv v0, v0, v20", "vadd.vv v1, v0, v20")
        with self.assertRaisesRegex(ValueError, "accumulator/partial register"):
            self.check_body(key, code)

    def test_wrong_rvv_seed(self):
        key = (16, 64, "endtoend", "reuse", "rvv")
        code = self.altered(key, "vwredsum.vs v0, v20, v0", "vwredsum.vs v0, v20, v15")
        with self.assertRaisesRegex(ValueError, "full 128-bit"):
            self.check_body(key, code)

    def test_tail_agnostic_reduction(self):
        key = (16, 64, "endtoend", "reuse", "rvv")
        code = self.altered(key, "vsetivli zero, 16, e16, m2, tu, mu", "vsetivli zero, 16, e16, m2, ta, mu")
        with self.assertRaisesRegex(ValueError, "full 128-bit"):
            self.check_body(key, code)

    def test_missing_final_csr_restoration(self):
        key = (4, 13, "core", "reuse", "rvv")
        code = self.altered(key, "vsetivli zero, 8, e8, m1, tu, mu\nli t5,", "li t5,")
        with self.assertRaisesRegex(ValueError, "final CSR"):
            self.check_body(key, code)

    def test_nonmultiple_shape_overread(self):
        key = (4, 13, "endtoend", "reuse", "rvv")
        code = self.altered(key, "vsetivli zero, 13, e8, m1, tu, mu", "vsetivli zero, 16, e8, m1, tu, mu")
        with self.assertRaisesRegex(ValueError, "boundary|over-read"):
            self.check_body(key, code)

class IdentityChecks(unittest.TestCase):
    def layout(self):
        ram = 0x80000000
        elf = SimpleNamespace(entry=ram,
            symbols={f"t13_kernel_{i}": (ram + (i + 1) * 8192, 128) for i in range(4)},
            named={".text": (0, 1, 6, ram, 0, 5 * 8192, 0, 0, 8192, 0),
                   ".bss": (0, 8, 3, ram + 0x150000, 0, 64, 0, 0, 16, 0)})
        return elf, bytes(5 * 8192 + 128)

    def test_different_kernel_slots_allowed(self):
        elf, binary = self.layout()
        changed = bytearray(binary)
        for offset in (8192, 2 * 8192, 3 * 8192, 5 * 8192 - 1):
            changed[offset] = 1
        self.assertEqual(gate.paired_layout(elf, elf, binary, bytes(changed))["nonkernel_bytes"],
                         8192 + 128)

    def test_non_kernel_changes_rejected(self):
        elf, binary = self.layout()
        for offset in (0, 8192 - 1, 5 * 8192, len(binary) - 1):
            changed = bytearray(binary); changed[offset] = 1
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, "non-kernel loaded"):
                gate.paired_layout(elf, elf, binary, bytes(changed))

    def test_section_suffix_drift_rejected(self):
        elf, binary = self.layout()
        changed = copy.deepcopy(elf)
        section = list(changed.named[".text"]); section[5] += 4480
        changed.named[".text"] = tuple(section)
        with self.assertRaisesRegex(ValueError, "section suffix"):
            gate.paired_layout(elf, changed, binary, binary)

    def test_bss_layout_drift_rejected(self):
        elf, binary = self.layout()
        changed = copy.deepcopy(elf)
        section = list(changed.named[".bss"]); section[3] += 16
        changed.named[".bss"] = tuple(section)
        with self.assertRaisesRegex(ValueError, "allocated section layout"):
            gate.paired_layout(elf, changed, binary, binary)

    def test_image_extent_drift_rejected(self):
        elf, binary = self.layout()
        with self.assertRaisesRegex(ValueError, "image extent"):
            gate.paired_layout(elf, elf, binary, binary + b"\0")

    def test_s0_is_frozen_body(self):
        base = candidate.load_base(ROOT)
        for m, k in SHAPES:
            for scope in ("core", "endtoend"):
                for software in ("basic", "reuse"):
                    for method in ("vdot", "rvv"):
                        self.assertEqual(candidate.kernel(base, m, k, method, software, scope, "s0"),
                                         base.kernel(m, k, method, software, scope))

    def test_cross_image_identity_drift(self):
        identity = dict(kind="nexus-am-riscv64-xs", source_commit="commit", am_revision="am",
                        external_files={}, toolchain={}, s1_candidate_sha256="s1", snapshot_files={})
        for field in identity:
            changed = copy.deepcopy(identity)
            changed[field] = "different"
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                images = []
                for i, record in enumerate((identity, changed)):
                    path = Path(tmp) / str(i)
                    path.mkdir()
                    (path / "build.json").write_text(json.dumps(record))
                    images.append(dict(name=str(i), path=str(path)))
                with self.assertRaisesRegex(ValueError, "cross-image build identity"):
                    experiment.validate_pairs(images, ROOT)

    def test_changed_library_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            lib = path / "library.a"
            lib.write_bytes(b"changed")
            record = dict(kind="nexus-am-riscv64-xs", source_commit="commit", am_revision="am",
                          external_files={str(lib): "wrong"}, toolchain={},
                          s1_candidate_sha256="s1", snapshot_files={})
            (path / "build.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "AM library changed"):
                experiment.validate_pairs([dict(name="one", path=str(path))], ROOT)

if __name__ == "__main__":
    if not shutil.which("riscv64-linux-gnu-gcc"):
        raise SystemExit("BLOCKED: actual GNU RISC-V assembler is required; no full test PASS")
    unittest.main(verbosity=2)
