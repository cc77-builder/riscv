"""Real GNU/AM linkage and focused fixed-layout negative tests; zero EMU."""
from __future__ import annotations
import copy
import os
from pathlib import Path
import random
import shutil
import struct
import tempfile
import unittest

import fixed_layout as l
import fixed_screen as s
import candidate
from machine_model import Machine

ROOT = Path(__file__).resolve().parents[4]
g, f, m = l.g, l.f, l.m


class FixedLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = os.environ.get("R2_FIXED_TEST_CONFIG")
        if not config:
            raise unittest.SkipTest("set R2_FIXED_TEST_CONFIG for real AM tests")
        output = os.environ.get("R2_FIXED_TEST_OUTPUT")
        if output:
            cls.output = Path(output)
            cls.output.mkdir(parents=True, exist_ok=False)
            cls.temporary = None
        else:
            cls.temporary = tempfile.TemporaryDirectory(prefix="r2-fixed-tests-")
            cls.output = Path(cls.temporary.name)
        cls.cfg = s.read_config(config, ROOT)
        cls.tools = s.build_tools(ROOT, cls.cfg)
        cls.images = {}
        for shard in (4, 5, 6, 7):
            for variant in ("s0", "s2"):
                item = dict(suite="performance", dataset=0, shard=shard, variant=variant)
                path = cls.output / f.image_name(item)
                l.build_one(ROOT, cls.cfg, path, item, cls.tools)
                cls.images[(shard, variant)] = path
        cls.base = candidate.load_base(ROOT)
        cls.audit = g.load("fixed_test_audit", ROOT / "team/optimizations/o2/r2-kernel-audit/audit.py")

    @classmethod
    def tearDownClass(cls):
        if cls.temporary:
            cls.temporary.cleanup()

    def pair(self, shard=7):
        paths = [self.images[(shard, v)] for v in ("s0", "s2")]
        a, b = [g.ELF((p / "vdot-perf.elf").read_bytes()) for p in paths]
        ma, mb = [m.read_json(p / "data/manifest.json") for p in paths]
        return a, b, ma, mb

    @staticmethod
    def write_loaded(elf, address, data):
        raw = bytearray(elf.raw)
        section = next(x for x in elf.sections if x[2] & 2 and x[1] != 8 and
                       x[3] <= address and address + len(data) <= x[3] + x[5])
        pos = section[4] + address - section[3]
        raw[pos:pos + len(data)] = data
        return g.ELF(bytes(raw))

    def reject(self, a, b, ma, mb):
        with self.assertRaises(ValueError):
            l.compare_pair(a, b, ma, mb, a.binary(), b.binary())

    def test_complete_layout_actual_four_scope_pairs(self):
        for shard in (4, 5, 6, 7):
            result = l.pair_paths(self.images[(shard, "s0")], self.images[(shard, "s2")])
            self.assertEqual(result["main"], "0x8000a000")
            self.assertEqual(result["whole_image_identical"], shard in (4, 5))
            self.assertEqual([x["binary_offset"] for x in result["exact_metadata_differences"]],
                             [] if shard in (4, 5) else ["0x120024", "0x1208c4"])

    def test_real_linked_bodies_poison_bounds_extremes(self):
        checks = 0
        for (shard, variant), path in self.images.items():
            elf = g.ELF((path / "vdot-perf.elf").read_bytes())
            manifest = m.read_json(path / "data/manifest.json")
            for index, row in enumerate(manifest["rows"]):
                name = f"t13_kernel_{index}"
                report = self.audit.audit_kernel(elf.symbol_data(name), elf.symbols[name][0])
                code = b"".join(int(x["word"], 16).to_bytes(4, "little") for x in report["instructions"])
                inputs = [self.base.inputs(row["m"], row["k"], ds) for ds in range(3)]
                inputs += [([[a] * row["k"] for _ in range(row["m"])], [b] * row["k"])
                           for a, b in ((-128, -128), (-128, 127), (127, 127), (0, 127))]
                rng = random.Random(0x2400 + shard)
                inputs += [([[rng.randrange(-128, 128) for _ in range(row["k"])] for _ in range(row["m"])],
                            [rng.randrange(-128, 128) for _ in range(row["k"])]) for _ in range(2)]
                for seed, (a, x) in enumerate(inputs):
                    self.assertTrue(Machine(a, x, seed + 73).execute(code).check(a, x, row["scope"] == "endtoend"))
                    checks += 1
        self.assertEqual(checks, 288)

    def test_main_byte_change_rejected(self):
        a, b, ma, mb = self.pair()
        addr = b.symbols["main"][0]
        b = self.write_loaded(b, addr, bytes([b.read(addr, 1)[0] ^ 1]))
        self.reject(a, b, ma, mb)

    def test_rvv_padding_change_rejected(self):
        a, b, ma, mb = self.pair()
        addr, size = b.symbols["t13_kernel_1"][:2]
        pos = addr + size + 16
        b = self.write_loaded(b, pos, bytes([b.read(pos, 1)[0] ^ 1]))
        self.reject(a, b, ma, mb)

    def test_non_kernel_gap_byte_rejected(self):
        a, b, ma, mb = self.pair()
        # Existing loaded text padding before the first fixed slot.
        pos = g.RAM + l.SLOT - 4
        b = self.write_loaded(b, pos, bytes([b.read(pos, 1)[0] ^ 1]))
        self.reject(a, b, ma, mb)

    def test_dot9_even_with_matching_manifest_rejected(self):
        a, b, ma, mb = self.pair()
        mb["rows"][0]["dots"] = 9
        b = self.write_loaded(b, b.symbols["cases"][0] + l.DOTS_OFFSET, struct.pack("<I", 9))
        self.reject(a, b, ma, mb)

    def test_dot_high_byte_rejected(self):
        a, b, ma, mb = self.pair()
        mb["rows"][0]["dots"] = 0x108
        b = self.write_loaded(b, b.symbols["cases"][0] + l.DOTS_OFFSET, struct.pack("<I", 0x108))
        self.reject(a, b, ma, mb)

    def test_other_case_field_even_with_matching_manifest_rejected(self):
        a, b, ma, mb = self.pair()
        mb["rows"][0]["iterations"] += 1
        b = self.write_loaded(b, b.symbols["cases"][0] + 32, struct.pack("<I", mb["rows"][0]["iterations"]))
        self.reject(a, b, ma, mb)

    def test_rvv_dot_field_not_exempt(self):
        a, b, ma, mb = self.pair()
        mb["rows"][1]["dots"] = 8
        b = self.write_loaded(b, b.symbols["cases"][0] + l.CASE_BYTES + l.DOTS_OFFSET, struct.pack("<I", 8))
        self.reject(a, b, ma, mb)

    def test_control_has_no_metadata_exemption(self):
        a, b, ma, mb = self.pair(5)
        mb["rows"][0]["dots"] += 1
        b = self.write_loaded(b, b.symbols["cases"][0] + l.DOTS_OFFSET, struct.pack("<I", mb["rows"][0]["dots"]))
        self.reject(a, b, ma, mb)

    def test_program_memsz_drift_with_same_bin_rejected(self):
        a, b, ma, mb = self.pair()
        raw = bytearray(b.raw)
        header = struct.unpack_from("<16sHHIQQQIHHHHHH", raw)
        loads = [i for i, seg in enumerate(b.segments) if seg[0] == 1]
        index = loads[-1]
        struct.pack_into("<Q", raw, header[5] + index * 56 + 40, b.segments[index][6] + 16)
        changed = g.ELF(bytes(raw))
        self.assertEqual(changed.binary(), b.binary())
        self.reject(a, changed, ma, mb)

    def test_alloc_alignment_drift_rejected(self):
        a, b, ma, mb = self.pair()
        b.named[".benchmark_inputs"] = tuple(list(b.named[".benchmark_inputs"][:8]) + [32, b.named[".benchmark_inputs"][9]])
        self.reject(a, b, ma, mb)

    def test_unexpected_shape_or_row_order_rejected(self):
        for edit in ("shape", "order"):
            a, b, ma, mb = self.pair()
            if edit == "shape":
                ma["m"] = mb["m"] = 5
            else:
                mb["rows"][0], mb["rows"][1] = mb["rows"][1], mb["rows"][0]
            self.reject(a, b, ma, mb)

    def test_object_relocation_rejected(self):
        obj = g.ELF((self.images[(7, "s2")] / "kernels-reference.o").read_bytes())
        obj.sections.append((0, 4, 0, 0, 0, 24, 0, 0, 8, 24))
        with self.assertRaisesRegex(ValueError, "relocations"):
            l.object_layout(obj)

    def test_binding_restored_and_nested_rejected(self):
        old = (g.regenerate, g.verify_build, f.validate_controls, m.canonical_images, m.CONTRACT, m.PASS)
        with self.assertRaisesRegex(RuntimeError, "sentinel"):
            with l.bindings(ROOT):
                self.assertEqual(m.CONTRACT, l.CONTRACT)
                with self.assertRaisesRegex(ValueError, "nested"):
                    with l.bindings(ROOT):
                        pass
                raise RuntimeError("sentinel")
        self.assertEqual(old, (g.regenerate, g.verify_build, f.validate_controls, m.canonical_images, m.CONTRACT, m.PASS))

    def test_adapter_snapshot_drift_rejected(self):
        source = self.images[(7, "s2")]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "copy"
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("objects"))
            with (target / "source/repo" / l.ADAPTER).open("a") as out:
                out.write("\n# unexpected source drift\n")
            with self.assertRaisesRegex(ValueError, "snapshot differs"):
                l.verify_build(target, ROOT)

    def test_generated_layout_drift_rejected_even_after_rehash(self):
        source = self.images[(7, "s2")]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "copy"
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("objects"))
            asm = target / "data/kernels.S"
            asm.write_text(asm.read_text().replace(".option norelax\n", ""))
            manifest = m.read_json(target / "data/manifest.json")
            manifest["files"]["kernels.S"] = g.sha(asm)
            g.save(target / "data/manifest.json", manifest)
            receipt = m.read_json(target / "build.json")
            receipt["artifacts"]["data/manifest.json"] = g.sha(target / "data/manifest.json")
            g.save(target / "build.json", receipt)
            with self.assertRaisesRegex(ValueError, "regeneration differs"):
                l.verify_build(target, ROOT)

    def test_old_build_contract_rejected_before_images(self):
        with tempfile.TemporaryDirectory() as temp:
            g.save(Path(temp) / "state.json", dict(status="CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN"))
            with self.assertRaisesRegex(ValueError, "fixed-layout build"):
                l.canonical_images(ROOT, dict(canonical_build=temp))

    def test_build_command_option_drift_rejected(self):
        source = self.images[(7, "s2")]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "copy"
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("objects"))
            receipt = m.read_json(target / "build.json")
            receipt["commands"][1]["command"][3] = "-mrelax"
            g.save(target / "reference-command/command.json", receipt["commands"][1])
            g.save(target / "build.json", receipt)
            with self.assertRaisesRegex(ValueError, "changed build command"):
                l.verify_build(target, ROOT)

    def test_build_raw_log_drift_rejected(self):
        source = self.images[(7, "s2")]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "copy"
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("objects"))
            with (target / "make-command/stdout.log").open("a") as out:
                out.write("unexpected\n")
            with self.assertRaisesRegex(ValueError, "raw logs differ"):
                l.verify_build(target, ROOT)


if __name__ == "__main__":
    unittest.main()
