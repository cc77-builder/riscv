"""Behavior tests for all seven real-parent negative-control transcript gates."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_negative import check_negative

# Independent of the checker declaration: changing one side must fail a test.
CASES = ("identity", "wen", "high", "cancel", "busy", "route", "clock")


def transcript(fault):
    return f"O1_PARENT_INJECT {fault}\nO1_PARENT_FAIL {fault}\n"


class ParentNegativeGateTests(unittest.TestCase):
    def test_each_intended_detection(self):
        for fault in CASES:
            with self.subTest(fault=fault):
                check_negative(fault, 1, transcript(fault))

    def test_wrong_exit_status_rejected(self):
        for fault in CASES:
            for status in (0, 2, 3, 4, 126, 127, 134, -6, -9):
                with self.subTest(fault=fault, status=status):
                    with self.assertRaises(ValueError):
                        check_negative(fault, status, transcript(fault))

    def test_escape_and_unrelated_failures_rejected(self):
        for fault in CASES:
            for status in (1, 3):
                for failure in (f"O1_PARENT_FAULT_ESCAPED {fault}",
                                "O1_PARENT_FAIL fault escaped", "missing vectors",
                                "Assertion failed", "O1_PARENT_FAIL unrelated"):
                    with self.subTest(fault=fault, status=status, failure=failure):
                        with self.assertRaises(ValueError):
                            check_negative(fault, status, f"O1_PARENT_INJECT {fault}\n{failure}\n")

    def test_other_faults_are_rejected(self):
        for fault in CASES:
            for other in CASES:
                if fault == other:
                    continue
                for value in (transcript(other),
                              f"O1_PARENT_INJECT {fault}\nO1_PARENT_FAIL {other}\n",
                              f"O1_PARENT_INJECT {other}\nO1_PARENT_FAIL {fault}\n"):
                    with self.subTest(fault=fault, other=other, value=value):
                        with self.assertRaises(ValueError):
                            check_negative(fault, 1, value)

    def test_missing_duplicate_reordered_or_extra_lines_rejected(self):
        for fault in CASES:
            inject = f"O1_PARENT_INJECT {fault}"
            fail = f"O1_PARENT_FAIL {fault}"
            bad = (
                "", inject, fail, f"{fail}\n{inject}\n",
                f"{inject}\n{inject}\n{fail}\n", f"{inject}\n{fail}\n{fail}\n",
                f" {inject}\n{fail}\n", f"{inject} extra\n{fail}\n",
                f"{inject}\n{fail} extra\n", f"{inject}\n {fail}\n",
                transcript(fault) + "O1_PARENT_PASS mode=1\n",
                transcript(fault) + f"O1_PARENT_FAULT_ESCAPED {fault}\n",
                transcript(fault) + "unrelated runtime error\n",
            )
            for index, value in enumerate(bad):
                with self.subTest(fault=fault, case=index):
                    with self.assertRaises(ValueError):
                        check_negative(fault, 1, value)

    def test_unknown_fault_rejected(self):
        with self.assertRaises(ValueError):
            check_negative("unknown", 1, transcript("unknown"))

    def test_cli_reads_real_logs_and_returns_status(self):
        script = Path(__file__).with_name("check_negative.py")
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "injection.log"
            for fault in CASES:
                for value, status, expected in (
                    (transcript(fault), 1, 0),
                    (f"O1_PARENT_INJECT {fault}\nO1_PARENT_FAULT_ESCAPED {fault}\n", 3, 1),
                    (transcript(fault) + "error\n", 1, 1),
                    (transcript(fault), 0, 1),
                ):
                    log.write_text(value, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(script), "--fault", fault,
                         "--return-code", str(status), "--log", str(log)],
                        capture_output=True, text=True, check=False,
                    )
                    with self.subTest(fault=fault, value=value, status=status):
                        self.assertEqual(result.returncode, expected, result.stderr)
                        self.assertEqual("O1_PARENT_NEGATIVE_CHECK_PASS" in result.stdout, expected == 0)
            log.unlink()
            result = subprocess.run(
                [sys.executable, "-B", str(script), "--fault", "clock", "--return-code", "1", "--log", str(log)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("O1_PARENT_NEGATIVE_CHECK_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
