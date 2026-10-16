"""A/B pairing must keep slower and first samples and reject changed programs."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("t14_compare", ROOT / "team/scripts/compare-t14.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def sample():
    return dict(image="performance-d0-s00", replay=0, seq=0, suite="performance",
                method="vdot", scenario="single", n=1, dataset=0, repeat=0,
                phase="first", dots=1, instructions=11, cycles=100)


class T14PairingTests(unittest.TestCase):
    def test_slower_first_sample_is_preserved(self):
        a = sample()
        b = dict(a, cycles=125)
        row = compare.paired_rows([a], [b])[0]
        self.assertEqual(row["phase"], "first")
        self.assertEqual(row["cycles_saved"], -25)
        self.assertEqual(row["hardware_speedup"], 0.8)

    def test_candidate_cannot_drop_an_input(self):
        with self.assertRaisesRegex(ValueError, "missing or extra"):
            compare.paired_rows([sample()], [])

    def test_duplicate_replay_is_rejected(self):
        a = sample()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare.paired_rows([a, a], [a])

    def test_retirement_count_must_match(self):
        a = sample()
        with self.assertRaisesRegex(ValueError, "instructions"):
            compare.paired_rows([a], [dict(a, instructions=10)])

    def test_relabeling_phase_is_rejected(self):
        a = sample()
        with self.assertRaisesRegex(ValueError, "phase"):
            compare.paired_rows([a], [dict(a, phase="measured")])

    def test_changed_dot_count_is_rejected(self):
        a = sample()
        with self.assertRaisesRegex(ValueError, "dots"):
            compare.paired_rows([a], [dict(a, dots=2)])


if __name__ == "__main__":
    unittest.main()
