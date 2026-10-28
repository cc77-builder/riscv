"""Reject wrong acceptance identities when relocated before/after builds are used."""
import json
from pathlib import Path
import tempfile
import unittest
from build_profile import verify_accepted_receipts,PIN_SHA,EMU_SHA

class AcceptedIdentities(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.paths={n:root/n/"final-validation.json" for n in ("before","after")}
        for p in self.paths.values():p.parent.mkdir()
        (root/"after/recheck-01").mkdir()
        self.before=dict(status="H1_FULLCORE_VALIDATION_PASS",
            input_receipts={"build-01/hardware-inputs.json":PIN_SHA["before"]},emu_sha256=EMU_SHA["before"])
        self.after=dict(status="R3_DIV_GATE_FULLCORE_PASS",emu_sha256=EMU_SHA["after"])
        self.checked=dict(status="O2_G3_OFFLINE_RECHECK_PASS",g3_complete=True,hardware_pins_sha256=PIN_SHA["after"])
    def run_check(self):
        self.paths["before"].write_text(json.dumps(self.before))
        self.paths["after"].write_text(json.dumps(self.after))
        (self.paths["after"].parent/"recheck-01/result.json").write_text(json.dumps(self.checked))
        return verify_accepted_receipts(self.paths)
    def test_original_receipt_formats_accepted(self):self.assertEqual(len(self.run_check()),3)
    def test_wrong_before_emu_rejected(self):
        self.before["emu_sha256"]=EMU_SHA["after"]
        with self.assertRaises(ValueError):self.run_check()
    def test_wrong_after_emu_rejected(self):
        self.after["emu_sha256"]=EMU_SHA["before"]
        with self.assertRaises(ValueError):self.run_check()
    def test_incomplete_recheck_rejected(self):
        self.checked["g3_complete"]=False
        with self.assertRaises(ValueError):self.run_check()
    def test_wrong_recheck_pins_rejected(self):
        self.checked["hardware_pins_sha256"]=PIN_SHA["before"]
        with self.assertRaises(ValueError):self.run_check()
    def test_failed_after_receipt_rejected(self):
        self.after["status"]="FAILED"
        with self.assertRaises(ValueError):self.run_check()

if __name__=="__main__":unittest.main()
