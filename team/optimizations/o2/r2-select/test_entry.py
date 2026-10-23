"""Control-flow negative cases and real compiled R4 artifacts."""
import copy
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

import entry_gate as g
import entry_candidate as c


class CallPath(unittest.TestCase):
    def setUp(self):
        self.words = {0: g.START, 4: g.COUNTERS[0], 8: g.COUNTERS[1],
                      12: c.encode_jal(28), 16: g.COUNTERS[2], 20: g.COUNTERS[3],
                      24: g.STOP, 40: 0x00000013, 44: 0x00008067}

    def test_real_order_visits_callee_then_returns(self):
        self.assertEqual([p for p, _ in g.walk(self.words)], [0, 4, 8, 12, 40, 44, 16, 20, 24])

    def test_jal_signed_roundtrip(self):
        for delta in (-1048576, -4, 0, 4, 1048574):
            self.assertEqual(g.jal_target(0x80002000, c.encode_jal(delta)), 0x80002000 + delta)
        for delta in (-1048578, 1048576, 3):
            with self.assertRaises(ValueError):
                c.encode_jal(delta)

    def test_reject_other_control_flow_and_ra_clobber(self):
        for pc, word in [(12, c.encode_jal(100)), (12, c.encode_jal(4)),
                         (12, c.encode_jal(28) & ~(31 << 7)), (40, c.encode_jal(4)),
                         (40, 0x00000063), (40, 0x00000093), (44, 0x00408067),
                         (44, 0x00000013), (40, g.START), (40, g.STOP)]:
            with self.subTest(pc=pc, word=hex(word)):
                words = dict(self.words, **{})
                words[pc] = word
                with self.assertRaises(ValueError):
                    g.walk(words)

    def test_reject_missing_marker_or_counter(self):
        for pc in (0, 4, 8, 16, 20, 24):
            words = dict(self.words)
            words[pc] = 0x00000013
            with self.assertRaises(ValueError):
                g.walk(words)

    def test_compressed_retirement_cannot_cover_call(self):
        check = g.counter_adapter(g.ROOT)
        path = g.walk(self.words)
        events = {"RETIRE": [dict(word=w, count=2 if pc == 12 else 1) for pc, w in path]}
        with self.assertRaisesRegex(ValueError, "call/return in compressed"):
            check.base.trace_windows(events, {"plan": [{"index": 0}]}, {0: self.words})


class ActualBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get("R4_ENTRY_BUILD")
        if not value:
            raise RuntimeError("R4_ENTRY_BUILD must identify the actual canonical two-image probe")
        cls.root = Path(value)
        cls.images = json.loads((cls.root / "images.json").read_text())["images"]
        if len(cls.images) != 2:
            raise RuntimeError("expected exactly two probe images")

    def test_actual_public_api_and_independent_model(self):
        for image in self.images:
            report = g.verify_build(Path(image["path"]), g.ROOT)
            self.assertEqual(len(report["kernels"]), 4)
            for row in report["kernels"]:
                self.assertEqual(row["entry_overhead_instructions"], 7)
                self.assertEqual(row["semantics"]["trials"], 9)

    def test_complete_layout_and_call_entry_addresses(self):
        pair = sorted(self.images, key=lambda x: x["variant"])
        result = g.paired_layout(pair[0]["path"], pair[1]["path"])
        self.assertEqual(result["kernel_slot_bytes"], 8192)

    def test_tampered_public_reference_and_manifest_rejected(self):
        with tempfile.TemporaryDirectory(prefix="r4-negative-build-") as temp:
            dst = Path(temp) / "build"
            shutil.copytree(self.images[0]["path"], dst)
            target = dst / "gemv-reference.o"
            raw = target.read_bytes()
            changed = bytearray(raw)
            changed[-1] ^= 1
            target.write_bytes(changed)
            with self.assertRaisesRegex(ValueError, "artifact drift"):
                g.verify_build(dst, g.ROOT)
            target.write_bytes(raw)
            manifest = dst / "data/manifest.json"
            value = json.loads(manifest.read_text())
            value["entry_candidate_sha256"] = "0" * 64
            manifest.write_text(json.dumps(value))
            receipt = json.loads((dst / "build.json").read_text())
            receipt["artifacts"]["data/manifest.json"] = g.sha(manifest)
            (dst / "build.json").write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "exact manifest"):
                g.verify_build(dst, g.ROOT)

    def test_tampered_snapshot_cannot_be_relabelled(self):
        with tempfile.TemporaryDirectory(prefix="r4-negative-source-") as temp:
            dst = Path(temp) / "build"
            shutil.copytree(self.images[0]["path"], dst)
            source = dst / "source/repo" / g.ENTRY / "entry_candidate.py"
            source.write_bytes(source.read_bytes() + b"\n# changed\n")
            with self.assertRaisesRegex(ValueError, "snapshot drift"):
                g.verify_build(dst, g.ROOT)

    def test_c_compilation_product_is_rechecked(self):
        with tempfile.TemporaryDirectory(prefix="r4-negative-c-link-") as temp:
            dst = Path(temp) / "build"
            shutil.copytree(self.images[0]["path"], dst)
            (dst / "api-c-linked.o").write_bytes(b"not the compiled caller")
            with self.assertRaisesRegex(ValueError, "C caller artifact drift"):
                g.verify_build(dst, g.ROOT)

    def test_foreign_checkout_cannot_supply_runtime_gate(self):
        with tempfile.TemporaryDirectory(prefix="r4-foreign-repo-") as temp:
            with self.assertRaisesRegex(ValueError, "another checkout"):
                g.verify_build(self.images[0]["path"], Path(temp))


if __name__ == "__main__":
    unittest.main()
