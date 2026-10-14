"""Synthetic negative fixtures for the T12 acceptance boundary, never DUT proof."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('t12_checker',ROOT/'team/scripts/check-vdot-regression.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

def fixture():
    lines=['The reference model is /synthetic/ref.so',
           'The first instruction of core 0 has commited. Difftest enabled.']
    lines += ['T12_ENQUEUE cycle=1 rob=0:5 pc=0x80000004 ftq=0:1 word=0x0294050b',
              'T12_ACCEPT cycle=2 rob=0:5 pdest=3 vl=8 illegal=0',
              'T12_REDIRECT cycle=3 rob=0:4 ftq=0:1',
              'T12_KILL cycle=3 rob=0:5 redirect=0:4 state=2',
              'T12_VFEX4_ACCEPT cycle=2 rob=0:5 fu=0x800',
              'T12_VFEX4_ACCEPT cycle=4 rob=0:6 fu=0x400',
              'T12_VFEX4_WAIT cycle=3 rob=0:6 fu=0x400 busy=1']
    for i in range(9):
        cycle=20+i*100;ptr=f'{i%2}:10';ftq=f'{i%2}:2';pc=f'0x{0x80001000+i*4:x}'
        lines += [f'T12_ENQUEUE cycle={cycle} rob={ptr} pc={pc} ftq={ftq} word=0x0294050b',
                  f'T12_ACCEPT cycle={cycle+1} rob={ptr} pdest=7 vl=8 illegal=0',
                  f'T12_STALL cycle={cycle+3} rob={ptr}',
                  f'T12_RESPONSE cycle={cycle+4} rob={ptr} pdest=7 illegal=0 data=0x00000000fffffff8',
                  f'T12_COMMIT cycle={cycle+5} rob={ptr} pc={pc} ftq={ftq}']
    lines += [f'T12_GROUP_PASS id={i} checkpoints=32 bytes=16384' for i in range(4)]
    lines += ['T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0','HIT GOOD TRAP']
    return '\n'.join(lines)+'\n'

class T12AcceptanceTests(unittest.TestCase):
    manifest={'groups':[{'vdot_count':9}],'speculation':{'expected_architectural_vdot':0}}
    def run_check(self, text=None, rc=0):
        return checker.check(fixture() if text is None else text,self.manifest,rc)
    def test_complete_synthetic_fixture(self):
        self.assertEqual(self.run_check()['status'],'T12_CONTROL_REGRESSION_PASS')
    def test_nonzero_exit(self):
        with self.assertRaisesRegex(ValueError,'exit code'): self.run_check(rc=124)
    def test_missing_summary(self):
        with self.assertRaisesRegex(ValueError,'summary'): self.run_check(fixture().replace('T12_SUMMARY','OLD_SUMMARY'))
    def test_missing_good_trap(self):
        with self.assertRaisesRegex(ValueError,'GOOD TRAP'): self.run_check(fixture().replace('HIT GOOD TRAP','TIMEOUT'))
    def test_disabled_difftest(self):
        with self.assertRaisesRegex(ValueError,'DiffTest'): self.run_check(fixture().replace('Difftest enabled.','Difftest disabled.'))
    def test_wrong_high_bits(self):
        with self.assertRaisesRegex(ValueError,'high 96'): self.run_check(fixture().replace('data=0x00000000fffffff8','data=0x100000000fffffff8',1))
    def test_wrong_identity(self):
        with self.assertRaisesRegex(ValueError,'identity changed'): self.run_check(fixture().replace('pdest=7 illegal=0','pdest=8 illegal=0',1))
    def test_cancelled_instruction_commits(self):
        extra='T12_COMMIT cycle=4 rob=0:5 pc=0x80000004 ftq=0:1\n'
        with self.assertRaisesRegex(ValueError,'cancelled'): self.run_check(fixture()+extra)
    def test_missing_writeback_pressure_is_incomplete(self):
        text='\n'.join(x for x in fixture().splitlines() if not x.startswith('T12_STALL'))
        self.assertEqual(self.run_check(text)['status'],'T12_COVERAGE_INCOMPLETE')
    def test_no_fu_acceptance(self):
        with self.assertRaises(ValueError): self.run_check(fixture().replace('T12_ACCEPT cycle=21','REMOVED cycle=21'))
    def test_duplicate_response(self):
        extra=next(x for x in fixture().splitlines() if x.startswith('T12_RESPONSE'))
        with self.assertRaises(ValueError): self.run_check(fixture()+extra+'\n')
    def test_missing_group(self):
        with self.assertRaisesRegex(ValueError,'group'): self.run_check(fixture().replace('T12_GROUP_PASS id=2','IGNORED id=2'))
    def test_uart_interleaving(self):
        text=fixture().replace('T12_GROUP_PASS id=0','T12_GROUP_T12_REDIRECT cycle=2000 rob=0:0 ftq=0:0\nPASS id=0')
        self.assertEqual(self.run_check(text)['status'],'T12_CONTROL_REGRESSION_PASS')

    def test_partial_observer_record_is_rejected(self):
        for bad in ('T12_RESPON', 'T12_', 'T12_STALL cycle=9 rob=0:5'):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'malformed|truncated'):
                self.run_check(fixture()+bad)
    def test_uart_inside_observer_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'malformed'):
            self.run_check(fixture().replace('pdest=7 illegal=0', 'pdest=T12_GROUP_PASS7 illegal=0', 1))
    def test_missing_observer_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'malformed'):
            self.run_check(fixture().replace(' pdest=7 illegal=0', ' illegal=0', 1))
    def test_duplicate_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'malformed'):
            self.run_check(fixture().replace('pdest=7 illegal=0', 'pdest=7 pdest=8 illegal=0', 1))
    def test_out_of_order_printing_is_sorted_by_cycle(self):
        lines=fixture().splitlines()
        observed=[x for x in lines if any(x.startswith('T12_'+k+' ') for k in checker.EVENT_FIELDS)]
        remaining=[x for x in lines if x not in observed]
        self.assertEqual(self.run_check('\n'.join(observed[::-1]+remaining)+'\n')['status'], 'T12_CONTROL_REGRESSION_PASS')

    def test_nonzero_failure_suffix_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'summary'):
            self.run_check(fixture().replace('failures=0', 'failures=01'))
    def test_extra_malformed_summary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'summary'):
            self.run_check(fixture()+'T12_SUMMARY incomplete\n')

if __name__=='__main__': unittest.main()
