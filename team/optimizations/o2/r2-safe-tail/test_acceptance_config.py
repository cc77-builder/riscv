"""Read-only checks for relocatable R2 acceptance paths and frozen checker identity.

These tests do not need a compiler, an emulator, or real historical receipts.
"""
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import fullcore_screen as r2
import linked_gate as gate

ROOT = Path(__file__).resolve().parents[4]
PROFILE = ROOT / "team/optimizations/o2/result-width/h1/performance/build_profile.py"
TEMPLATE = ROOT / "team/optimizations/o2/r2-safe-tail/runtime.example.json"


class RelocatedAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.example = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def configure(self, change):
        item = dict(self.example)
        item.update(change)
        path = self.base / "config.json"
        path.write_text(json.dumps(item), encoding="utf-8")
        return r2.read_config(path, ROOT)

    def test_example_config_has_two_explicit_receipt_locations(self):
        self.assertIn("b0_acceptance", self.example)
        self.assertIn("h1_acceptance", self.example)
        self.assertEqual(set(r2.acceptance_paths(self.configure({}))), {"b0", "h1"})

    def test_remapped_paths_are_preserved_in_preflight_contract(self):
        a = str(self.base / "copied-B0.json")
        b = str(self.base / "copied-H1.json")
        conf = self.configure({"b0_acceptance": a, "h1_acceptance": b})
        paths = r2.acceptance_paths(conf)
        self.assertEqual(paths, {"b0": Path(a), "h1": Path(b)})
        # Probe only the relevant new paths: other hardware inputs intentionally absent.
        with patch.object(gate, "verify_sources", return_value=None):
            report = r2.preflight(ROOT, conf)
        self.assertFalse(report["runtime_ready"])
        for path in paths.values():
            self.assertTrue(any(str(path) in message for message in report["runtime_errors"]))

    def test_legacy_config_still_uses_frozen_original_locations(self):
        item = {k: v for k, v in self.example.items() if k not in {"b0_acceptance", "h1_acceptance"}}
        path = self.base / "old.json"
        path.write_text(json.dumps(item), encoding="utf-8")
        config = r2.read_config(path, ROOT)
        self.assertEqual(r2.acceptance_paths(config), r2.DEFAULT_ACCEPTANCE)

    def test_partial_override_and_unknown_option_rejected(self):
        path = self.base / "bad.json"
        for change in ({"b0_acceptance": "only-one"}, {"disable_difftest": True}):
            item = {k: v for k, v in self.example.items() if k not in {"b0_acceptance", "h1_acceptance"}}
            item.update(change)
            path.write_text(json.dumps(item), encoding="utf-8")
            with self.assertRaises(ValueError):
                r2.read_config(path, ROOT)

    def test_migrated_checker_pin_is_not_implicitly_disabled(self):
        body = PROFILE.read_bytes().replace(b"\r\n", b"\n")
        import hashlib
        self.assertEqual(hashlib.sha256(body).hexdigest(), r2.MIGRATED_PROFILE_SHA256)
        r2.pinned_modules(ROOT)

    def test_semantic_receipts_accept_identical_content_at_new_paths(self):
        profile = gate.load("unit_acceptance_profile", PROFILE)
        b0 = self.base / "B0.json"
        h1 = self.base / "H1.json"
        good_b0 = {
            "status": "O2_G3_OFFLINE_RECHECK_PASS", "g3_complete": True,
            "hardware_pins_sha256": profile.PIN_SHA["b0"], "emu_sha256": profile.EMU_SHA["b0"],
        }
        good_h1 = {
            "status": "H1_FULLCORE_VALIDATION_PASS",
            "input_receipts": {"build-01/hardware-inputs.json": profile.PIN_SHA["h1"]},
            "emu_sha256": profile.EMU_SHA["h1"],
        }
        b0.write_text(json.dumps(good_b0), encoding="utf-8")
        h1.write_text(json.dumps(good_h1), encoding="utf-8")
        self.assertEqual(profile.verify_accepted_receipts({"b0": b0, "h1": h1}),
                         {"b0": b0, "h1": h1})
        good_h1["input_receipts"]["build-01/hardware-inputs.json"] = "0" * 64
        h1.write_text(json.dumps(good_h1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "H1 acceptance mismatch"):
            profile.verify_accepted_receipts({"b0": b0, "h1": h1})


if __name__ == "__main__":
    unittest.main()
