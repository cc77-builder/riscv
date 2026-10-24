"""Focused archive-adapter rejection tests using actual sealed evidence bytes."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import fixed_evidence as fixed

l, e = fixed.l, fixed.e
ROOT = Path(__file__).resolve().parents[4]


class Overlay:
    """Read-only base archive with deliberate in-memory corruption for tests."""
    def __init__(self, base):
        self.base = base
        self.manifest = copy.deepcopy(base.manifest)
        self.overrides = {}

    def raw(self, name):
        return self.overrides.get(name, self.base.raw(name))

    def json(self, name):
        return json.loads(self.raw(name))

    def put_json(self, name, value):
        self.overrides[name] = e.json_bytes(value)


class FixedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = os.environ.get("R2_FIXED_TEST_ARCHIVE")
        if not source:
            raise unittest.SkipTest("set R2_FIXED_TEST_ARCHIVE to actual completed fixed archive")
        cls.path = Path(source)
        cls.archive = e.portable(ROOT).Archive(cls.path)
        cls.first = cls.archive.json("canonical/images.json")["images"][0]["name"]
        cls.receipt = "canonical/images/" + cls.first + "/build.json"
        fixed.source_identity(ROOT)

    def reject(self, archive, message):
        with self.assertRaisesRegex(ValueError, message):
            fixed.layout_audit(ROOT, archive)

    def test_actual_complete_sealed_pairs(self):
        report = fixed.layout_audit(ROOT, self.archive)
        self.assertEqual(report["complete_layout_pairs"], 13)
        self.assertEqual(sum(p["whole_image_identical"] for p in report["pairs"]), 6)
        self.assertEqual(report["new_emu_runs"], 0)
        self.assertFalse(report["architecture_replayed"])

    def test_export_auditor_source_drift(self):
        archive = Overlay(self.archive)
        archive.overrides["support/fixed_evidence.py"] = archive.raw("support/fixed_evidence.py") + b"\n# drift\n"
        self.reject(archive, "export/audit source differs")

    def test_self_consistent_wrong_source_root(self):
        archive = Overlay(self.archive)
        receipt = archive.json(self.receipt)
        receipt["source_root"] = "/different-checkout"
        for command in receipt["commands"]:
            command["cwd"] = receipt["source_root"]
        archive.put_json(self.receipt, receipt)
        self.reject(archive, "origin differs")

    def test_wrong_make_build_root(self):
        archive = Overlay(self.archive)
        receipt = archive.json(self.receipt)
        receipt["commands"][0]["command"][2] = "/different-build/source"
        archive.put_json(self.receipt, receipt)
        self.reject(archive, "origin differs")

    def test_wrong_original_image_location(self):
        archive = Overlay(self.archive)
        images = archive.json("canonical/images.json")
        images["images"][0]["path"] = "/different-build/images/" + self.first
        archive.put_json("canonical/images.json", images)
        self.reject(archive, "original path differs")

    def test_pair_cache_changed_or_missing(self):
        for mode in ("value", "missing"):
            archive = Overlay(self.archive)
            pairs = archive.json("canonical/pair-layout.json")
            if mode == "value":
                pairs["pairs"][0]["main"] = "0x8000b000"
            else:
                pairs["pairs"].pop()
            archive.put_json("canonical/pair-layout.json", pairs)
            self.reject(archive, "cached complete layout pairs differ")

    def test_incomplete_canonical_state(self):
        archive = Overlay(self.archive)
        state = archive.json("canonical/state.json")
        state["status"] = "BUILDING"
        archive.put_json("canonical/state.json", state)
        self.reject(archive, "canonical build state incomplete")

    def test_legacy_auditor_rejects_new_contract(self):
        self.assertNotEqual(e.m.CONTRACT, l.CONTRACT)
        with self.assertRaisesRegex(ValueError, "wrong archived contract"):
            e.audit(ROOT, self.path)

    def test_pack_relocated_source_rejected_before_output(self):
        common = self.archive.json("campaign/runtime-inputs.json")
        suffix = "/" + l.ENTRY.as_posix()
        original = next(name for name in common if name.endswith(suffix))
        common["/different-live-root" + suffix] = common.pop(original)
        with tempfile.TemporaryDirectory() as temp:
            run, output = Path(temp) / "run", Path(temp) / "archive"
            run.mkdir()
            (run / "runtime-inputs.json").write_bytes(e.json_bytes(common))
            with self.assertRaisesRegex(ValueError, "original live repository"):
                fixed.pack(ROOT, run, output)
            self.assertFalse(output.exists())

    def test_fixed_auditor_rejects_real_legacy_archive(self):
        legacy = e.portable(ROOT).Archive(ROOT / l.g.REL / "evidence/merged-screen-v1")
        self.reject(legacy, "wrong fixed-layout archive contract")


if __name__ == "__main__":
    unittest.main()
