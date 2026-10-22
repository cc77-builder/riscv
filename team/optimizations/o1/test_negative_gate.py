"""Exercise acceptance and rejection of real negative-run transcripts."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_negative import check_negative

# Kept independent of the checker's mapping so an accidental mapping change fails.
CASES = (
    ("identity", "old identity"),
    ("wen", "old write enables"),
    ("high", "full128 result"),
    ("cancel", "output valid/kill/latency"),
)


class NegativeGateTests(unittest.TestCase):
    def test_each_intended_detection(self):
        for fault, reason in CASES:
            with self.subTest(fault=fault):
                check_negative(fault, 1, f"O1_INJECT {fault}\nO1_FU_FAIL {reason}\n")

    def test_exit_status_is_bound_to_detection(self):
        for fault, reason in CASES:
            for code in (0, 2, 3, 4, 126, 127, 134, -6, -9):
                with self.subTest(fault=fault, code=code):
                    with self.assertRaises(ValueError):
                        check_negative(fault, code, f"O1_INJECT {fault}\nO1_FU_FAIL {reason}\n")

    def test_escape_cannot_masquerade_as_detection(self):
        for fault, _ in CASES:
            for suffix in ("O1_FU_FAIL fault escaped", f"O1_FU_FAULT_ESCAPED {fault}"):
                for code in (1, 3):
                    with self.subTest(fault=fault, suffix=suffix, code=code):
                        with self.assertRaises(ValueError):
                            check_negative(fault, code, f"O1_INJECT {fault}\n{suffix}\n")

    def test_missing_wrong_duplicate_and_unrelated_markers(self):
        for fault, reason in CASES:
            inject = f"O1_INJECT {fault}"
            fail = f"O1_FU_FAIL {reason}"
            good = f"{inject}\n{fail}\n"
            bad = (
                "", f"{inject}\n", f"{fail}\n",
                f"{fail}\n{inject}\n",  # Failure before injection.
                f"{inject}\n{inject}\n{fail}\n",
                f"{inject}\n{fail}\n{fail}\n",
                f"{inject}\nO1_FU_FAIL missing vectors\n",
                good + "O1_FU_ONLY_PASS accepted=1\n",
                good + "O1_FU_FAIL fault escaped\n",
                good + f"O1_FU_FAULT_ESCAPED {fault}\n",
                good + "unrelated runtime error\n",
                good + "O1_INJECT unknown\n",
                f"O1_INJECT unknown\n{fail}\n",
                f"{inject} extra\n{fail}\n",
                f"{inject}\n{fail} extra\n",
                f" {inject}\n{fail}\n",
            )
            for index, log in enumerate(bad):
                with self.subTest(fault=fault, case=index):
                    with self.assertRaises(ValueError):
                        check_negative(fault, 1, log)

    def test_other_faults_are_not_accepted(self):
        for fault, _ in CASES:
            for other, reason in CASES:
                if other == fault:
                    continue
                for log in (f"O1_INJECT {other}\nO1_FU_FAIL {reason}\n",
                            f"O1_INJECT {fault}\nO1_FU_FAIL {reason}\n"):
                    with self.subTest(fault=fault, other=other, log=log):
                        with self.assertRaises(ValueError):
                            check_negative(fault, 1, log)

    def test_unknown_fault_is_rejected(self):
        with self.assertRaises(ValueError):
            check_negative("unknown", 1, "O1_INJECT unknown\nO1_FU_FAIL old identity\n")

    def test_cli_reads_transcript_and_returns_status(self):
        script = Path(__file__).with_name("check_negative.py")
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "injection.log"
            for fault, reason in CASES:
                for text, status, expected_rc in (
                    (f"O1_INJECT {fault}\nO1_FU_FAIL {reason}\n", 1, 0),
                    (f"O1_INJECT {fault}\nO1_FU_FAIL fault escaped\n", 1, 1),
                    (f"O1_INJECT {fault}\nO1_FU_FAULT_ESCAPED {fault}\n", 3, 1),
                ):
                    log.write_text(text, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(script), "--fault", fault,
                         "--return-code", str(status), "--log", str(log)],
                        capture_output=True, text=True, check=False,
                    )
                    with self.subTest(fault=fault, text=text):
                        self.assertEqual(result.returncode, expected_rc, result.stderr)
                        self.assertEqual("O1_NEGATIVE_CHECK_PASS" in result.stdout, expected_rc == 0)
            log.unlink()
            result = subprocess.run(
                [sys.executable, "-B", str(script), "--fault", "high", "--return-code", "1", "--log", str(log)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("O1_NEGATIVE_CHECK_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
