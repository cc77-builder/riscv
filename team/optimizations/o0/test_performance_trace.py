"""Actual archived pilot replay and in-memory checker negatives; not RTL tests."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('o0_performance',HERE/'summarize_performance_trace.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PerformanceTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gate=m.load_gate()
        pins=gate.strict_json((HERE/'pilot-t14-batch128.json').read_bytes())
        cls.replay=gate.replay(m.ROOT,pins,'trace')
        raw,_=gate.pinned_file(m.ROOT,pins['files']['analysis'])
        cls.analysis=gate.strict_json(raw)
        raw,_=gate.pinned_file(m.ROOT,pins['files']['stderr'])
        cls.text=gate.decode_gzip(raw,cls.analysis['raw_sha256']['stderr.log'])
        cls.checker=gate.load_diagnostics(m.ROOT).load_parser()
        cls.diagnosis=cls.replay['replayed_diagnostics']
        cls.result=m.correlate(cls.text,cls.analysis,cls.diagnosis,cls.checker)

    def run_correlate(self,text=None,analysis=None,diagnosis=None):
        return m.correlate(self.text if text is None else text,
            self.analysis if analysis is None else analysis,
            self.diagnosis if diagnosis is None else diagnosis,self.checker)

    def test_strict_original_gate(self):
        self.assertTrue(self.replay['raw_hardware_trace_replayed'])
        self.assertEqual(self.replay['status'],'O0_PILOT_TRACE_REPLAY_PASS_NOT_FULL_O0')

    def test_all_dynamic_lifetimes(self):
        r=self.result
        self.assertEqual(r['accepted_responded_committed'],768)
        self.assertEqual(r['preaccept_cancelled_allocations'],6)
        self.assertEqual(r['suppressed_enqueue_attempts'],6)
        self.assertEqual(len(r['lifetimes']),768)
        self.assertEqual({e['response_cycle']-e['accept_cycle'] for e in r['lifetimes']},{2})
        self.assertEqual(r['raw_csr_samples_checked'],48)

    def test_same_waiter_not_just_coincidence(self):
        r=self.result
        self.assertEqual(r['response_busy_coincidences'],738)
        self.assertEqual(r['same_waiter_accepted_next_cycle'],738)
        self.assertEqual(r['matched_with_redirect_same_cycle'],0)
        self.assertTrue(all(p['next_accept_cycle']==p['response_cycle']+1 for p in r['matched_waiters']))

    def test_separate_first_warmup_measured(self):
        self.assertEqual([(w['seq'],w['cycles'],w['same_waiter_accepted_next_cycle']) for w in self.result['windows'] if w['method']=='vdot'],
                         [(0,480,119),(3,483,119),(4,465,125),(7,464,125),(8,464,125),(11,464,125)])
        self.assertTrue(all(w['accepted']==0 and w['busy_wait_events']==0 for w in self.result['windows'] if w['method']=='rvv'))

    def test_exclude_interwindow_gaps(self):
        self.assertEqual(self.result['inter_window_gaps_excluded'],5)
        self.assertEqual(sum(self.result['within_window_gap_histogram'].values()),6*127)
        self.assertEqual(self.result['within_window_gap_histogram']['3'],744)
        self.assertEqual(max(map(int,self.result['within_window_gap_histogram'])),14)

    def test_missing_csr_rejected(self):
        line=next(s for s in self.text.splitlines(True) if s.startswith('T13_CSR_SAMPLE'))
        with self.assertRaisesRegex(ValueError,'CSR'):self.run_correlate(text=self.text.replace(line,'',1))

    def test_duplicate_csr_rejected(self):
        line=next(s for s in self.text.splitlines(True) if s.startswith('T13_CSR_SAMPLE'))
        with self.assertRaisesRegex(ValueError,'CSR'):self.run_correlate(text=self.text.replace(line,line*2,1))

    def test_changed_u64_sample_rejected(self):
        analysis=copy.deepcopy(self.analysis)
        analysis['samples'][0]['counter_values'][0]+=1
        with self.assertRaisesRegex(ValueError,'CSR'):self.run_correlate(analysis=analysis)

    def test_changed_commit_pc_rejected(self):
        line=next(s for s in self.text.splitlines(True) if s.startswith('T12_COMMIT'))
        wrong=__import__('re').sub(r'pc=0x[0-9a-fA-F]+','pc=0x1234',line)
        with self.assertRaisesRegex(ValueError,'commit PC'):self.run_correlate(text=self.text.replace(line,wrong,1))

    def test_missing_commit_rejected(self):
        line=next(s for s in self.text.splitlines(True) if s.startswith('T12_COMMIT'))
        with self.assertRaises(ValueError):self.run_correlate(text=self.text.replace(line,'',1))

    def test_changed_response_identity_rejected(self):
        line=next(s for s in self.text.splitlines(True) if s.startswith('T12_RESPONSE'))
        wrong=__import__('re').sub(r'pdest=\s*\d+','pdest=999',line)
        with self.assertRaisesRegex(ValueError,'response identity'):self.run_correlate(text=self.text.replace(line,wrong,1))

    def test_wrong_workload_count_rejected(self):
        analysis=copy.deepcopy(self.analysis)
        analysis['samples'][0]['dots']=127
        with self.assertRaisesRegex(ValueError,'workload'):self.run_correlate(analysis=analysis)

    def test_changed_transaction_time_rejected(self):
        diagnosis=copy.deepcopy(self.diagnosis)
        diagnosis['transactions'][0]['end_cycle']+=1
        with self.assertRaisesRegex(ValueError,'response identity'):self.run_correlate(diagnosis=diagnosis)

    def test_source_guard(self):
        with patch.object(m,'GATE_BLOB','0'*40):
            with self.assertRaisesRegex(ValueError,'source changed'):m.load_gate()

    def test_redirect_cycle_enqueue_is_not_an_allocation(self):
        # Print order and pointer age do not change ROB redirect suppression.
        for rob in ('0:1', '0:10', '0:11', '1:0'):
            for reverse in (False, True):
                events = [(2, 0, 'REDIRECT', {'rob': '0:10'}),
                          (2, 1, 'ENQUEUE', {'rob': rob, 'pc': '0x100', 'word': '0x0200000b'})]
                self.assertEqual(m.bind_retirements(events[::-1] if reverse else events, []), ([], 0))

    def test_suppressed_enqueue_cannot_fabricate_a_lifetime(self):
        fields = {'rob': '0:11', 'pc': '0x100', 'word': '0x0200000b'}
        events = [(1, 0, 'ENQUEUE', fields),
                  (2, 1, 'REDIRECT', {'rob': '0:10'}),
                  (2, 2, 'ENQUEUE', fields),
                  (3, 3, 'ACCEPT', {'rob': '0:11', 'pdest': '1'})]
        tx = [{'accept_cycle': 3, 'rob': '0:11', 'pdest': 1, 'index': 0}]
        with self.assertRaisesRegex(ValueError, 'unbound/duplicate accept'):
            m.bind_retirements(events, tx)

    def test_cancelled_rob_reuse_and_same_cycle_retire_reallocate(self):
        fields = {'rob': '0:11', 'pc': '0x100', 'word': '0x0200000b'}
        events = [(1, 0, 'ENQUEUE', fields), (2, 1, 'REDIRECT', {'rob': '0:10'})]
        tx = []
        for index, start in enumerate((3, 7)):
            # Deliberately put the next ENQUEUE before previous COMMIT in print order.
            events += [(start, 0, 'ENQUEUE', fields),
                       (start+1, 1, 'ACCEPT', {'rob': '0:11', 'pdest': str(index+1)}),
                       (start+3, 2, 'RESPONSE', {'rob': '0:11', 'pdest': str(index+1), 'data': '0x1'}),
                       (start+4, 3, 'COMMIT', {'rob': '0:11', 'pc': '0x100'})]
            tx.append(dict(accept_cycle=start+1, end_cycle=start+3, rob='0:11',
                           pdest=index+1, index=index, outcome='response'))
        lifetimes, cancelled = m.bind_retirements(events, tx)
        self.assertEqual(cancelled, 1)
        self.assertEqual([e['pdest'] for e in lifetimes], [1, 2])

    def test_scope_not_overclaimed(self):
        for name in ('o0_full_matrix_complete','o1_rtl_implemented','new_hardware_run'):
            self.assertFalse(self.result[name])
        self.assertNotIn('speedup',self.result)

    def test_cli_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'result'
            cmd=[sys.executable,'-B',str(HERE/'summarize_performance_trace.py'),'--output',str(out)]
            run=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            old=(out/'result.json').read_bytes()
            self.assertEqual(json.loads(old)['same_waiter_accepted_next_cycle'],738)
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
            self.assertEqual((out/'result.json').read_bytes(),old)


if __name__=='__main__':
    unittest.main()
