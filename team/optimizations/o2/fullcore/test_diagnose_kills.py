"""Diagnostic mutation tests; synthetic traces do not constitute RTL coverage."""
import hashlib
import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import diagnose_kills
from test_trace import Fixture, basic, killed, change, drop


class KillDiagnosisTests(unittest.TestCase):
    def test_survivor_identity_for_both_slot_orders_and_rob_wrap(self):
        for reverse, wrap in itertools.product((False, True), repeat=2):
            with self.subTest(reverse=reverse, wrap=wrap):
                result = diagnose_kills.diagnose(killed(reverse, False, wrap).text().encode())
                self.assertEqual(result["classifications"], {"partial_kill": 1})
                row = result["windows"][0]
                survivor, victim = (row["p"], row["r"]) if reverse else (row["r"], row["p"])
                self.assertTrue(row["survivor_committed"])
                self.assertFalse(row["victim_committed"])
                self.assertEqual(survivor["rob"], "0:47" if wrap else "0:5")
                self.assertEqual(victim["rob"], "1:0" if wrap else "0:6")
                self.assertEqual(survivor["pc"], "0x80000004" if reverse else "0x80000000")

    def test_both_killed_is_not_partial_coverage(self):
        result = diagnose_kills.diagnose(killed(both=True).text().encode())
        self.assertEqual(result["classifications"], {"both_slots_cancelled": 1})
        self.assertEqual(result["counts"]["PARTIAL_KILL"], 0)
        self.assertFalse(result["windows"][0]["p"]["committed"])
        self.assertFalse(result["windows"][0]["r"]["committed"])

    def test_no_kill_and_exact_crlf_byte_identity(self):
        raw = basic().text().replace("\n", "\r\n").encode()
        result = diagnose_kills.diagnose(raw)
        self.assertEqual(result["raw_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["windows"], [])

    def test_rob_reuse_does_not_borrow_an_earlier_commit_or_pc(self):
        fixture = basic()
        fixture.enqueue("0:5")
        fixture.enqueue("0:6", 8)
        fixture.tick("0:5")
        fixture.tick("0:6")
        fixture.tick(ready=0, flush=("0:5", 0), auto_commit=False)
        fixture.drain()
        row = diagnose_kills.diagnose(fixture.text().encode())["windows"][0]
        self.assertEqual(row["r"]["pc"], "0x80000004")
        self.assertGreater(row["r"]["commit_cycle"], row["r"]["accept_cycle"])
        self.assertFalse(row["p"]["committed"])

    def test_single_occupied_slot_is_not_partial_coverage(self):
        fixture = Fixture()
        fixture.enqueue()
        fixture.tick("0:5")
        fixture.tick(flush=("0:5", 1))
        fixture.drain()
        result = diagnose_kills.diagnose(fixture.text().encode())
        self.assertEqual(result["classifications"], {"one_slot_occupied": 1})
        self.assertIsNone(result["windows"][0]["r"])

    def test_missing_survivor_commit_is_rejected_by_complete_audit(self):
        raw = drop(killed().text(), "O2_COMMIT ").encode()
        with self.assertRaises(ValueError):
            diagnose_kills.diagnose(raw)

    def test_false_slot_kill_cannot_create_a_witness(self):
        raw = change(killed().text(), "O2_STATE cycle=3 ", "killp=1", "killp=0").encode()
        with self.assertRaises(ValueError):
            diagnose_kills.diagnose(raw)

    def test_cli_does_not_overwrite_input_or_previous_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "run.log"
            raw = basic().text().encode()
            log.write_bytes(raw)
            with patch("sys.argv", ["diagnose_kills.py", str(log), "--output", str(log)]):
                with self.assertRaises(FileExistsError):
                    diagnose_kills.main()
            self.assertEqual(log.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
