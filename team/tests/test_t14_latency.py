"""Latency contracts keep T12 identity and clock checks strict for both modes."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("t14_observer", ROOT / "team/scripts/check-vdot-regression.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def events(response=12, stall=None):
    text = "T12_VFEX4_ACCEPT cycle=100 rob=0:5 fu=0x800000000\n"
    text += "T12_ACCEPT cycle=10 rob=0:5 pdest=7 vl=8 illegal=0\n"
    if stall is not None:
        text += f"T12_STALL cycle={stall} rob=0:5\n"
    text += f"T12_RESPONSE cycle={response} rob=0:5 pdest=7 illegal=0 data=0x00000000fffffff8\n"
    text += "T12_COMMIT cycle=110 rob=0:5 pc=0x80000004 ftq=0:1\n"
    return checker.extract_events(text)[0]


class T14LatencyTests(unittest.TestCase):
    def test_e2_requires_explicit_candidate_contract(self):
        with self.assertRaisesRegex(ValueError, "precedes E3"):
            checker.normalize_fu_cycles(events())
        mapped = checker.normalize_fu_cycles(events(), min_response_latency=2)
        self.assertEqual(next(e[0] for e in mapped if e[2] == "RESPONSE"), 102)

    def test_candidate_rejects_e1_response(self):
        with self.assertRaisesRegex(ValueError, "precedes E2"):
            checker.normalize_fu_cycles(events(response=11), min_response_latency=2)

    def test_candidate_allows_backpressure_after_e2(self):
        mapped = checker.normalize_fu_cycles(events(response=16, stall=12), min_response_latency=2)
        self.assertEqual(next(e[0] for e in mapped if e[2] == "RESPONSE"), 106)

    def test_e2_does_not_weaken_parent_identity(self):
        trace = events()
        trace[0][3]["rob"] = "0:6"
        with self.assertRaisesRegex(ValueError, "parent/FU acceptance identity"):
            checker.normalize_fu_cycles(trace, min_response_latency=2)

    def test_unsupported_latency_is_rejected(self):
        for value in (0, 1, 4):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "unsupported"):
                checker.normalize_fu_cycles(events(), min_response_latency=value)


if __name__ == "__main__":
    unittest.main()
