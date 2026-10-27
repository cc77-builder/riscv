"""Fail-closed O2 parent observation-negative verifier tests."""
import unittest
from check_negative import FAULTS, FAULT_CATEGORIES, check_negative, check_positive


class NegativeGateTests(unittest.TestCase):
    def valid(self, fault):
        return f"O2_PARENT_INJECT {fault}\nO2_PARENT_FAIL {FAULT_CATEGORIES[fault]}\n"

    def test_all_exact_categories_are_accepted(self):
        for fault in FAULTS:
            with self.subTest(fault=fault):
                check_negative(fault, 1, self.valid(fault))

    def test_incorrect_failure_category_is_rejected(self):
        for fault in FAULTS:
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                check_negative(fault, 1, f"O2_PARENT_INJECT {fault}\nO2_PARENT_FAIL unrelated\n")

    def test_success_error_escape_signal_exit_codes_rejected(self):
        for rc in (0, 2, 3, -6, 134):
            with self.subTest(rc=rc), self.assertRaises(ValueError):
                check_negative("high", rc, self.valid("high"))

    def test_missing_injection_rejected(self):
        with self.assertRaises(ValueError):
            check_negative("high", 1, "O2_PARENT_FAIL high\n")

    def test_wrong_selected_fault_rejected(self):
        with self.assertRaises(ValueError):
            check_negative("identity", 1, self.valid("high"))

    def test_unknown_fault_rejected(self):
        with self.assertRaises(ValueError):
            check_negative("cancel", 1, "O2_PARENT_INJECT cancel\nO2_PARENT_FAIL cancel\n")

    def test_reordered_or_duplicated_records_rejected(self):
        lines = self.valid("high").splitlines()
        for log in ("\n".join(reversed(lines)), self.valid("high")+lines[-1]):
            with self.subTest(log=log), self.assertRaises(ValueError):
                check_negative("high", 1, log)

    def test_extra_pass_or_assertion_does_not_count_as_rejection(self):
        for extra in ("O2_PARENT_PASS\n", "Assertion failed\n", "O2_PARENT_FAULT_ESCAPED high\n"):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                check_negative("high", 1, self.valid("high")+extra)

    def test_ansi_and_hidden_suffix_not_silently_removed(self):
        for log in ("\x1b[31m"+self.valid("high"), self.valid("high").rstrip()+"\x00\n"):
            with self.subTest(log=log), self.assertRaises(ValueError):
                check_negative("high", 1, log)

    def test_empty_positive_is_not_pass(self):
        with self.assertRaises(ValueError):
            check_positive("")

    def test_negative_transcript_cannot_be_positive(self):
        with self.assertRaises(ValueError):
            check_positive(self.valid("high"))

    def test_positive_duplicate_schema_fields_fail(self):
        with self.assertRaises(ValueError):
            check_positive("O2_PARENT_CYCLE schema=1 schema=1\n")

    def test_positive_entry_also_enforces_strict_idle_clock(self):
        from test_trace import encode, fixture
        rows, fus, final = fixture()
        rows[11]["clocks"] = 2
        fus[1]["clock_edges"] += 1
        with self.assertRaisesRegex(ValueError, "idle FU retained clock"):
            check_positive(encode(rows, fus, final))

    def test_positive_bare_pass_is_not_complete(self):
        with self.assertRaises((ValueError, KeyError)):
            check_positive("O2_PARENT_PASS schema=1\n")


if __name__ == "__main__":
    unittest.main()
