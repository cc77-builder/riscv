"""Synthetic observer tests, NOT simulator evidence."""
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('o0_analyze', HERE / 'analyze.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def transaction(core=100, tick=10, rob='0:1', dest=7, stalls=0, latency=2, kill=False, illegal=0):
    lines = [f'T12_VFEX4_ACCEPT cycle={core} rob={rob} fu=0x800000000',
             f'T12_ACCEPT cycle={tick} rob={rob} pdest={dest} vl=8 illegal={illegal}']
    if kill:
        lines += [f'T12_KILL cycle={tick+1} rob={rob} redirect=0:0 state=2']
    else:
        lines += [f'T12_STALL cycle={tick+latency+i} rob={rob}' for i in range(stalls)]
        lines += [f'T12_RESPONSE cycle={tick+latency+stalls} rob={rob} pdest={dest} illegal={illegal} data=0x0']
    return '\n'.join(lines) + '\n'


def run(text, latency=2):
    return a.analyze(text, fu_latency=latency)


class AnalyzerTests(unittest.TestCase):
    def test_dependency_matches_fetched_blob(self):
        self.assertEqual(a.git_blob(a.PARSER.read_bytes()), a.PARSER_BLOB)

    def test_t14_two_requests(self):
        result = run(transaction() + transaction(103, 13, '0:2', 8))
        self.assertEqual(result['observed_accept_gap_histogram'], {'3': 1})
        self.assertEqual(result['release_to_next_accept_histogram'], {'1': 1})
        self.assertEqual(result['counts']['responded'], 2)

    def test_baseline(self):
        result = run(transaction(latency=3) + transaction(104, 14, '0:2', latency=3), 3)
        self.assertEqual(result['response_latency_histogram'], {'3': 2})
        self.assertEqual(result['observed_accept_gap_histogram'], {'4': 1})

    def test_idle_gated_clock_is_not_global(self):
        result = run(transaction() + transaction(1000, 15, '0:2'))
        self.assertEqual(result['observed_accept_gap_histogram'], {'900': 1})
        self.assertEqual(result['transactions'][1]['end_cycle'], 1002)

    def test_large_integer_cycles(self):
        base = 2**54 + 1
        result = run(transaction(base) + transaction(base+3, 13, '0:2'))
        self.assertEqual(result['transactions'][0]['accept_cycle'], base)
        self.assertEqual(result['observed_accept_gap_histogram'], {'3': 1})

    def test_backpressure(self):
        result = run(transaction(stalls=7))
        self.assertEqual(result['response_latency_histogram'], {'9': 1})
        self.assertEqual(result['counts']['writeback_stall_events'], 7)

    def test_kill_and_pointer_reuse(self):
        result = run(transaction(kill=True) + transaction(103, 13))
        self.assertEqual(result['counts']['killed'], 1)
        self.assertEqual(result['counts']['responded'], 1)

    def test_busy_wait_coincidence_is_only_observation(self):
        text = transaction().replace('T12_RESPONSE',
            'T12_VFEX4_WAIT cycle=102 rob=0:2 fu=0x800000000 busy=1\nT12_RESPONSE')
        result = run(text)
        self.assertEqual(result['response_coincident_busy_wait_cycles'], [102])
        self.assertEqual(result['parent_wait_event_counts'], {'vdot_busy': 1})
        self.assertEqual(result['status'], 'O0_DIAGNOSTICS_ONLY')

    def test_wait_not_busy_is_not_assumed_writeback(self):
        text = transaction() + 'T12_VFEX4_WAIT cycle=104 rob=0:3 fu=0x800000000 busy=0\n'
        result = run(text)
        self.assertEqual(result['parent_wait_event_counts'], {'vdot_not_busy': 1})
        self.assertEqual(result['counts']['writeback_stall_events'], 0)

    def test_other_fu_wait(self):
        result = run(transaction() + 'T12_VFEX4_WAIT cycle=104 rob=0:3 fu=0x1 busy=1\n')
        self.assertEqual(result['parent_wait_event_counts'], {'other_busy': 1})

    def test_empty_rejected(self):
        with self.assertRaises(ValueError): run('unrelated output\n')

    def test_partial_record_rejected(self):
        with self.assertRaises(ValueError): run(transaction().rstrip('\n'))

    def test_missing_parent_rejected(self):
        with self.assertRaises(ValueError): run(transaction().split('\n', 1)[1])

    def test_unfinished_rejected(self):
        with self.assertRaises(ValueError): run('\n'.join(transaction().splitlines()[:2])+'\n')

    def test_changed_pdest_rejected(self):
        text = transaction().replace('pdest=7 illegal=0 data=', 'pdest=8 illegal=0 data=')
        with self.assertRaises(ValueError): run(text)

    def test_high_result_bit_rejected(self):
        with self.assertRaises(ValueError): run(transaction().replace('data=0x0', f'data=0x{1<<100:x}'))

    def test_missing_stall_rejected(self):
        with self.assertRaises(ValueError): run(transaction(stalls=1).replace('T12_STALL cycle=12 rob=0:1\n', ''))

    def test_duplicate_rejected(self):
        text = transaction(stalls=1).replace('T12_STALL cycle=12 rob=0:1\n', 'T12_STALL cycle=12 rob=0:1\n'*2)
        with self.assertRaises(ValueError): run(text)

    def test_invalid_busy_rejected(self):
        with self.assertRaises(ValueError): run(transaction()+'T12_VFEX4_WAIT cycle=104 rob=0:2 fu=0x800000000 busy=2\n')

    def test_bad_pointer_rejected(self):
        with self.assertRaises(ValueError): run(transaction(rob='0:48'))

    def test_wrong_latency_rejected(self):
        with self.assertRaises(ValueError): run(transaction(), 3)

    def test_o1_overlap_rejected_not_silently_accepted(self):
        with self.assertRaises(ValueError): run(transaction() + transaction(102, 12, '0:2'))

    def test_illegal_response_is_zero(self):
        self.assertEqual(run(transaction(illegal=1))['transactions'][0]['illegal'], 1)
        with self.assertRaises(ValueError): run(transaction(illegal=1).replace('data=0x0', 'data=0x8'))

    def test_clock_stream_reorder_rejected(self):
        with self.assertRaises(ValueError): run(transaction() + 'T12_VFEX4_WAIT cycle=99 rob=0:2 fu=0x1 busy=1\n')

    def test_cli_gzip_no_overwrite_and_failed_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            err = root/'stderr.log.gz'
            with gzip.open(err, 'wb') as stream: stream.write(transaction().encode())
            out = root/'stdout.log'
            out.write_text('The first instruction of core 0 has commited. Difftest enabled.\n'
                           'The reference model is fixture.so\nHIT GOOD TRAP\n')
            cmd = [sys.executable, '-B', str(HERE/'analyze.py'), '--stderr', str(err), '--stdout', str(out),
                   '--exit-code', '0', '--fu-latency', '2', '--output', str(root/'result')]
            success = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            report = root/'result/diagnosis.json'
            before = report.read_bytes()
            self.assertEqual(json.loads(before)['status'], 'O0_DIAGNOSTICS_ONLY')
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)
            self.assertEqual(report.read_bytes(), before)
            cmd[cmd.index('--exit-code')+1] = '1'
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)

    def test_corrupt_huge_latency_rejected_without_allocating_range(self):
        text = transaction().replace('T12_RESPONSE cycle=12', f'T12_RESPONSE cycle={2**60}')
        with self.assertRaises(ValueError): run(text)

    def test_reader_size_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'data.gz'
            with gzip.open(path, 'wb') as stream: stream.write(b'x'*100)
            with self.assertRaises(ValueError): a.read_stream(path, 10)


if __name__ == '__main__':
    unittest.main()
