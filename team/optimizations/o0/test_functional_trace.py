"""Offline replay regressions and in-memory corruptions, NOT new DUT tests."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('functional_replay', HERE / 'replay_functional_trace.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class FunctionalTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {role: r.read_verified(r.ROOT / rel, sha) for role, (rel, sha) in r.FILES.items()}
        cls.original_run = json.loads(cls.data['result'])
        cls.original_analysis = json.loads(cls.data['analysis'])
        cls.stderr = r.unpack(cls.data['stderr'], cls.original_run['raw_sha256']['stderr.log'])
        cls.stdout = r.unpack(cls.data['stdout'], cls.original_run['raw_sha256']['stdout.log'])

    def setUp(self):
        self.run = copy.deepcopy(self.original_run)
        self.analysis = copy.deepcopy(self.original_analysis)

    def call(self, stderr=None, stdout=None):
        return r.review(self.stderr if stderr is None else stderr, self.stdout if stdout is None else stdout, self.analysis, self.run)

    def test_real_replay_and_scope(self):
        result = self.call()
        self.assertEqual(result['matched_vdot_lifetimes'], 6)
        self.assertEqual(result['matched_CSR_sample_events'], 48)
        self.assertEqual(result['diagnosis']['counts']['responded'], 6)
        self.assertEqual(result['diagnosis']['parent_wait_event_counts'], {})
        self.assertTrue(result['raw_hardware_trace_replayed'])
        self.assertFalse(result['o0_complete'])
        self.assertFalse(result['o1_implemented'])

    def test_gated_ticks_not_global_II(self):
        rows = self.call()['lifetime_table']
        self.assertEqual([x['raw_accept_tick'] for x in rows], [0,3,6,9,12,15])
        self.assertEqual(rows[1]['accept_cycle']-rows[0]['accept_cycle'],72153)
        self.assertTrue(all(x['accept_to_response'] == 2 and x['accept_to_commit'] == 4 for x in rows))

    def test_functional_cannot_be_performance_file(self):
        path = r.ROOT / r.FILES['stderr'][0]
        with self.assertRaisesRegex(ValueError, 'wrong file identity'):
            r.read_verified(path, r.EXPECTED_PERFORMANCE_BLOB)

    def test_unknown_uploaded_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'stderr.log.gz'
            path.write_bytes(self.data['stderr']+b'x')
            with self.assertRaises(ValueError): r.read_verified(path, r.FILES['stderr'][1])

    def test_raw_digest_mismatch(self):
        with self.assertRaises(ValueError): r.unpack(self.data['stderr'], '0'*64)

    def test_failed_exit(self):
        self.run['exit_code']=1
        with self.assertRaises(ValueError): self.call()

    def test_wrong_run(self):
        self.run['image']='performance-d0-s06'
        with self.assertRaises(ValueError): self.call()

    def test_wrong_scope(self):
        self.analysis['samples'][0]['phase']='measured'
        with self.assertRaises(ValueError): self.call()

    def test_bad_trap_marker(self):
        with self.assertRaises(ValueError): self.call(stdout=self.stdout+'\nHIT BAD TRAP\n')

    def test_wrong_csr_sample(self):
        text=self.stderr.replace('data=0xcd2e1879d1561b2f wen=0','data=0xcd2e1879d1561b2e wen=0',1)
        self.assertNotEqual(text,self.stderr)
        with self.assertRaisesRegex(ValueError,'hardware/UART counter mismatch'): self.call(stderr=text)

    def test_uart_destination_mismatch(self):
        text=self.stdout.replace('dest=000000000000000000000000fffe0400','dest=000000000000000000000000fffe0401',1)
        with self.assertRaises(ValueError): self.call(stdout=text)

    def test_high_result_bit_mismatch(self):
        text=re.sub(r'(T12_RESPONSE[^\n]*data=)0x[0-9a-f]+',r'\g<1>0x10000000000000000000000000',self.stderr,count=1)
        self.assertNotEqual(text,self.stderr)
        with self.assertRaises(ValueError): self.call(stderr=text)

    def test_missing_parent(self):
        text=re.sub(r'^T12_VFEX4_ACCEPT[^\n]*\n','',self.stderr,count=1,flags=re.M)
        with self.assertRaises(ValueError): self.call(stderr=text)

    def test_response_identity_mismatch(self):
        text=re.sub(r'(T12_RESPONSE[^\n]*pdest=)\s*110',r'\g<1>111',self.stderr,count=1)
        self.assertNotEqual(text,self.stderr)
        with self.assertRaises(ValueError): self.call(stderr=text)

    def test_commit_pc_mismatch(self):
        text=re.sub(r'(T12_COMMIT[^\n]*pc=)0x[0-9a-f]+',r'\g<1>0x1',self.stderr,count=1)
        with self.assertRaisesRegex(ValueError,'enqueue/commit PC mismatch'): self.call(stderr=text)

    def test_summary_not_completion(self):
        with self.assertRaises(ValueError): self.call(stdout=self.stdout.replace('HIT GOOD TRAP','NO TRAP'))

    def test_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'result.json'
            cmd=[sys.executable,'-B',str(HERE/'replay_functional_trace.py'),'--output',str(out)]
            first=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            before=out.read_bytes()
            second=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(second.returncode,2)
            self.assertEqual(out.read_bytes(),before)

    def test_cli_wrong_input_no_success_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'result.json'; wrong=Path(tmp)/'wrong.gz';wrong.write_bytes(b'wrong')
            cmd=[sys.executable,'-B',str(HERE/'replay_functional_trace.py'),'--stderr',str(wrong),'--output',str(out)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
