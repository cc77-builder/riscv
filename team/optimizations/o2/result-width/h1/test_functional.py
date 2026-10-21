"""Negative tests for the independent read-only H1 evidence checker.

Uses an explicitly supplied existing H1 work root; never mutates its evidence.
"""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import validate_functional as vf

class FunctionalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(os.environ["H1_REPO"])
        cls.work = Path(os.environ["H1_WORK"])
        cls.baseline = Path(os.environ["H1_BASELINE"])
        cls.rows = [vf.fields(line) for line in (cls.work / "parent-01/result.log").read_text().splitlines()
            if line.startswith("O2_PARENT_CYCLE ")]

    def validate(self):
        return vf.validate(self.repo, self.work, self.baseline)

    def mutate_read(self, target, transform):
        original = Path.read_bytes
        target = target.resolve()
        def read(path):
            data = original(path)
            return transform(data) if path.resolve() == target else data
        return patch.object(Path, "read_bytes", read)

    def test_real_parent_replay(self):
        result = vf.validate_cycles(self.rows)
        self.assertEqual(result["cycles"], 34356)
        self.assertEqual(result["accepted"], 13515)
        self.assertEqual(result["frozen_vectors"], 10022)
        self.assertEqual(result["latency_cycles"], 2)

    def test_duplicate_field_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate field"):
            vf.fields("EVENT cycle=0 cycle=1")

    def test_expected_negative_marker(self):
        vf.negative_text("parent", "rob", "identity",
            "O2_PARENT_INJECT rob\nO2_PARENT_FAIL identity\n",
            "O2_PARENT_NEGATIVE_CHECK_PASS rob\n")

    def test_wrong_negative_category_rejected(self):
        with self.assertRaisesRegex(ValueError, "incorrect negative detection"):
            vf.negative_text("parent", "rob", "identity",
                "O2_PARENT_INJECT rob\nO2_PARENT_FAIL high\n",
                "O2_PARENT_NEGATIVE_CHECK_PASS rob\n")

    def test_appended_positive_marker_rejected(self):
        with self.assertRaisesRegex(ValueError, "incorrect negative detection"):
            vf.negative_text("fu", "high", "high",
                "O2_FU_INJECT high\nO2_FU_FAIL high\nO2_FU_PASS\n",
                "O2_FU_NEGATIVE_GATE_PASS high\n")

    def test_cycle_gap_rejected(self):
        rows = list(self.rows)
        rows[100] = dict(rows[100], cycle="101")
        with self.assertRaisesRegex(ValueError, "cycle sequence"):
            vf.validate_cycles(rows)

    def test_prefix_count_tamper_rejected(self):
        rows = list(self.rows)
        rows[100] = dict(rows[100], accepted_total=str(int(rows[100]["accepted_total"]) + 1))
        with self.assertRaisesRegex(ValueError, "prefix conservation"):
            vf.validate_cycles(rows)

    def test_same_count_wrong_response_identity_rejected(self):
        rows = list(self.rows)
        i = next(i for i, row in enumerate(rows) if row["response"] == "1")
        rows[i] = dict(rows[i], response_seq=str(int(rows[i]["response_seq"]) + 1))
        with self.assertRaisesRegex(ValueError, "response identity"):
            vf.validate_cycles(rows)

    def test_checker_source_tamper_rejected(self):
        target = self.repo / "team/optimizations/o2/check_negative_fu.py"
        with self.mutate_read(target, lambda data: data + b"\n# modified\n"):
            with self.assertRaisesRegex(ValueError, "source digest mismatch"):
                self.validate()

    def test_artifact_tamper_rejected(self):
        target = self.work / "fu-01/obj/VVDotElasticFuTestTop"
        with self.mutate_read(target, lambda data: data + b"\x00"):
            with self.assertRaisesRegex(ValueError, "artifact digest mismatch"):
                self.validate()

    def test_negative_exit_zero_rejected(self):
        target = self.work / "fu-01/commands.json"
        def transform(data):
            commands = json.loads(data)
            next(x for x in commands if x["log"] == "inject-high.log")["exit_code"] = 0
            return json.dumps(commands).encode()
        with self.mutate_read(target, transform):
            with self.assertRaisesRegex(ValueError, "command exit code"):
                self.validate()

    def test_missing_negative_command_rejected(self):
        target = self.work / "fu-01/commands.json"
        def transform(data):
            return json.dumps([x for x in json.loads(data) if x["log"] != "check-high.log"]).encode()
        with self.mutate_read(target, transform):
            with self.assertRaisesRegex(ValueError, "command inventory"):
                self.validate()

if __name__ == "__main__":
    unittest.main()
