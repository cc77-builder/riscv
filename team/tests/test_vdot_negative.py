"""Commit-group binding for the bit100 rejection, using DiffTest's ring format."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('negative',Path(__file__).resolve().parents[1]/'scripts/check-vdot-negative.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

def fixture():
    return '''The reference model is /fixture.so
The first instruction of core 0 has commited. Difftest enabled.
DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=10 pc=0x80001c4c instruction=0x0294050b
the first commit instr pc of DUT is 0x0000000080001c40
the first commit instr pc of REF is 0x0000000080001c40
commit group [02]: pc 0080001c40 cmtcnt 3 <--
[30] commit pc 0000000080001c40 inst 0c543423 wen 0 dst 08 data 0000000000000000 idx 002
[31] commit pc 0000000080001c4c inst 0294050b wen 1 dst 10 data 0000000000000000 idx 005
[00] commit pc 000000008000178c inst 02043283 wen 1 dst 05 data 0000000000000000 idx 007 <--
v10_high different at pc = 0x0080001c40, right=0x0000001000000000, wrong =0x0000000000000000
'''

class NegativeTests(unittest.TestCase):
    def test_injected_instruction_inside_wrapped_group(self):
        result=checker.check(fixture(),1)
        self.assertEqual(result['status'],'EXPECTED_VDOT_HIGHBIT_REJECTION')
        self.assertEqual(result['group_pc'],'0x80001c40')
    def test_reject_mutations(self):
        mutations=[('bit=100','bit=99'),('vd=10','vd=11'),('instruction=0x0294050b','instruction=0x0294058b'),
                   ('inst 0294050b','inst 0294058b'),('wen 1 dst 10','wen 0 dst 10'),
                   ('pc = 0x0080001c40','pc = 0x0080001c44'),('cmtcnt 3','cmtcnt 1'),
                   ('cmtcnt 3','cmtcnt 33'),('right=0x0000001000000000','right=0x0000002000000000'),
                   ('[31] commit','[29] commit'),('Difftest enabled.','Difftest disabled.'),
                   ('REF is 0x0000000080001c40','REF is 0x0000000080001c44')]
        for old,new in mutations:
            with self.subTest(old=old),self.assertRaises(ValueError):checker.check(fixture().replace(old,new),1)
    def test_exit_and_duplicate_records(self):
        for rc in (0,-6,124):
            with self.subTest(rc=rc),self.assertRaises(ValueError):checker.check(fixture(),rc)
        for line in fixture().splitlines():
            if any(tag in line for tag in ('INJECTED','different at pc','cmtcnt','[31]')):
                with self.subTest(line=line),self.assertRaises(ValueError):checker.check(fixture()+line+'\n',1)
