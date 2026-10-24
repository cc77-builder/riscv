"""Real AM probe checks; the source change is confined to qualified RVV slots."""
from __future__ import annotations
import copy
import os
from pathlib import Path
import tempfile
import unittest
import rvv_probe as p
from machine_model import Machine
import test_fixed_layout as layout_tests

ROOT = Path(__file__).resolve().parents[4]


class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = os.environ.get("R2_RVV_PROBE_TEST_CONFIG")
        if not config:
            raise unittest.SkipTest("set R2_RVV_PROBE_TEST_CONFIG for real AM probe tests")
        cls.temp = tempfile.TemporaryDirectory(prefix="strong-rvv-probe-tests-")
        cls.root = Path(cls.temp.name)
        cls.cfg = p.fixed.read_config(config, ROOT)
        cls.build = cls.root / "build"
        p.build(ROOT, cls.cfg, cls.build)
        cls.paths = [cls.build / "images" / p.f.image_name(i) for i in p.inventory()]
        cls.elfs = [p.g.ELF((b / "vdot-perf.elf").read_bytes()) for b in cls.paths]
        cls.manifests = [p.m.read_json(b / "data/manifest.json") for b in cls.paths]
        cls.audit = p.g.load("probe_test_audit", ROOT / "team/optimizations/o2/r2-kernel-audit/audit.py")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def compare(self, a=None, b=None, ma=None, mb=None):
        a, b = a or self.elfs[0], b or self.elfs[1]
        return p.compare(a, b, ma or self.manifests[0], mb or self.manifests[1], a.binary(), b.binary())

    def test_actual_complete_pair(self):
        result = self.compare()
        self.assertEqual(result["metadata_exceptions"], 0)
        self.assertEqual(result["main"], "0x8000a000")

    def test_actual_compiled_full128_bounds_and_csr(self):
        base = p.g.load("probe_test_s2", ROOT / p.g.REL / "candidate.py").load_base(ROOT)
        vectors = [base.inputs(4, 13, d) for d in range(3)]
        vectors += [([[a] * 13 for _ in range(4)], [b] * 13)
                    for a, b in ((-128, -128), (-128, 127), (127, 127), (0, 127))]
        checks = 0
        for elf, manifest in zip(self.elfs, self.manifests):
            for i, row in enumerate(manifest["rows"]):
                name = "t13_kernel_" + str(i)
                report = self.audit.audit_kernel(elf.symbol_data(name), elf.symbols[name][0])
                code = b"".join(int(x["word"], 16).to_bytes(4, "little") for x in report["instructions"])
                for n, (matrix, vector) in enumerate(vectors):
                    machine = Machine(matrix, vector, 0x2400 + n).execute(code)
                    self.assertTrue(machine.check(matrix, vector, stored=True))
                    self.assertEqual(machine.counts.get("vdot.vv", 0), row["dots"])
                    checks += 1
        self.assertEqual(checks, 56)

    def test_control_bin_is_exact_fixed_s2(self):
        out = self.root / "independent-fixed-s2"
        item = dict(suite="performance", dataset=0, shard=7, variant="s2")
        with p.l.bindings(ROOT):
            tools = p.fixed.build_tools(ROOT, self.cfg)
            p.l.build_one(ROOT, self.cfg, out, item, tools)
        self.assertEqual((out / "vdot-perf.bin").read_bytes(), (self.paths[0] / "vdot-perf.bin").read_bytes())

    def test_vdot_body_or_padding_change_rejected(self):
        for index in (0, 2):
            addr, size = self.elfs[1].symbols[f"t13_kernel_{index}"][:2]
            for location in (addr + 96, addr + size + 16):
                changed = layout_tests.FixedLayoutTests.write_loaded(self.elfs[1], location,
                    bytes([self.elfs[1].read(location, 1)[0] ^ 1]))
                with self.assertRaisesRegex(ValueError, "vdot slot changed"):
                    self.compare(b=changed)

    def test_main_byte_change_rejected(self):
        addr = self.elfs[1].symbols["main"][0]
        changed = layout_tests.FixedLayoutTests.write_loaded(self.elfs[1], addr, bytes([self.elfs[1].read(addr, 1)[0] ^ 1]))
        with self.assertRaisesRegex(ValueError, "main differs"):
            self.compare(b=changed)

    def test_no_dot_metadata_exception(self):
        addr = self.elfs[1].symbols["cases"][0] + p.l.DOTS_OFFSET
        changed = layout_tests.FixedLayoutTests.write_loaded(self.elfs[1], addr, (4).to_bytes(4, "little"))
        with self.assertRaises(ValueError):
            self.compare(b=changed)

    def test_unchanged_manifest_input_required(self):
        manifest = copy.deepcopy(self.manifests[1])
        manifest["rows"][0]["body"] = manifest["rows"][0]["body"] + ["addi zero, zero, 0"]
        with self.assertRaisesRegex(ValueError, "vdot slot changed"):
            self.compare(mb=manifest)

    def test_scope_and_variant_cannot_expand_silently(self):
        for v, d, s in (("s2", 0, 7), ("rvv1", 1, 7), ("rvv1", 0, 6)):
            with self.assertRaisesRegex(ValueError, "bounded probe selection"):
                p.generate(ROOT, self.root / "forbidden", v, d, s)
        self.assertFalse((self.root / "forbidden").exists())

    def test_binding_restores_original_exact_objects(self):
        original = p.g.PINNED, p.l.generate, p.m.CONTRACT
        with p.bindings(ROOT):
            self.assertEqual(p.m.CONTRACT, p.CONTRACT)
            self.assertTrue(set(original[0]) < set(p.g.PINNED))
            with self.assertRaisesRegex(ValueError, "nested probe binding"):
                with p.bindings(ROOT):
                    pass
        self.assertIs(p.g.PINNED, original[0])
        self.assertIs(p.l.generate, original[1])
        self.assertEqual(p.m.CONTRACT, original[2])


if __name__ == "__main__":
    unittest.main()
