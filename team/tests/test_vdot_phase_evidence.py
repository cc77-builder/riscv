"""Counterexamples are synthetic parser tests, never claimed as DUT runs."""
import unittest
from test_vdot_log import checker,fixture
class PhaseEvidenceTests(unittest.TestCase):
    def prefix(self):
        return '\n'.join(x for x in fixture().splitlines() if not x.startswith('VDOT_SUMMARY '))
    def test_complete_seven_selftest_records_are_valid(self):
        checker.validate_selftest_prefix(self.prefix())
    def test_pass_marker_cannot_replace_deleted_selftest_records(self):
        p=self.prefix()
        for name in checker.SELFTEST:
            bad='\n'.join(x for x in p.splitlines() if not x.startswith('VDOT_CASE id='+name+' '))
            with self.subTest(name=name),self.assertRaises(ValueError):checker.validate_selftest_prefix(bad)
        bad='\n'.join(x for x in p.splitlines() if not x.startswith('VDOT_CASE '))
        with self.assertRaises(ValueError):checker.validate_selftest_prefix(bad)
    def test_selftest_result_and_initial_state_are_still_checked(self):
        p=self.prefix()
        for bad in (p.replace('all32_checked=1','all32_checked=0',1),
                    p.replace('pre32_checked=1','pre32_checked=0',1),
                    p.replace('actual_cause=0x3','actual_cause=0x2',1)):
            with self.assertRaises(ValueError):checker.validate_selftest_prefix(bad)
    def test_reordered_or_missing_negative_controls_are_rejected(self):
        lines=self.prefix().splitlines()
        negative=[i for i,x in enumerate(lines) if x.startswith('HARNESS_NEGATIVE ')]
        lines[negative[0]],lines[negative[1]]=lines[negative[1]],lines[negative[0]]
        with self.assertRaises(ValueError):checker.validate_selftest_prefix('\n'.join(lines))
    def test_exception_cannot_precede_declared_legal_control(self):
        expected={'D00':1,'D01':2,'X00':3}
        checker.require_record_order([{'id':k} for k in expected],expected)
        for ids in (('X00','D00','D01'),('D01','D00','X00'),('D00','X00'),('D00','D01','X00','D00')):
            with self.subTest(ids=ids),self.assertRaises(ValueError):
                checker.require_record_order([{'id':k} for k in ids],expected)
if __name__=='__main__':unittest.main()
