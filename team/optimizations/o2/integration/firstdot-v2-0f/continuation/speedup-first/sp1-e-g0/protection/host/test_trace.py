"""SP1 host-only parser mutation tests, never evidence of RTL correctness."""
import copy
import itertools
import random
import unittest
import analyze as a
from fixtures import Fixture, basic, blocked, killed, stream, change, drop


def field(line,key):
    return next(s.split('=',1)[1] for s in line.split() if s.startswith(key+'='))


def local_text(text):
    return '\n'.join(x for x in text.splitlines() if not x.startswith(('SP1_ENQUEUE ', 'SP1_COMMIT ', 'SP1_REDIRECT ')))+'\n'


class TraceTests(unittest.TestCase):
    def reject(self,*mutants):
        for m in mutants:
            with self.subTest(tail=m[-150:]),self.assertRaises(ValueError):
                a.analyze(m)

    def test_direct_one_cycle_full128(self):
        r=a.analyze(basic().text())
        self.assertEqual(r['status'],'SP1_TRACE_PASS')
        self.assertEqual(r['response_latency_histogram'],{'1':1})
        self.assertEqual((r['counts']['DIRECT_R'],r['counts']['MOVE']),(1,0))

    def test_direct_stream_does_not_use_stale_r_seq(self):
        r=a.analyze(stream().text())
        self.assertEqual(r['observed_accept_gap_histogram'],{'1':3})
        self.assertEqual(r['response_latency_histogram'],{'1':4})
        self.assertEqual([t['seq'] for t in r['transactions']],list(range(4)))

    def test_enqueue_p_and_old_p_priority_on_triple_overlap(self):
        f=Fixture()
        for i in range(5,9): f.enqueue('0:'+str(i),i+2)
        f.tick('0:5');f.tick('0:6',ready=0);f.tick('0:7');f.tick('0:8');f.drain()
        r=a.analyze(f.text())
        self.assertEqual(r['counts']['TRIPLE_OVERLAP'],2)
        self.assertEqual(r['counts']['ENQUEUE_P'],3)
        self.assertEqual([t['route'] for t in r['transactions']],['DIRECT_R']+['ENQUEUE_P']*3)
        self.assertEqual(r['counts']['ACCEPT'],r['counts']['DIRECT_R']+r['counts']['ENQUEUE_P'])

    def test_full_stall_preserves_complete_packet(self):
        r=a.analyze(blocked().text())
        self.assertEqual(r['counts']['FULL_STALL'],2)
        self.assertEqual(r['counts']['STALL'],3)
        self.assertEqual(r['counts']['COMMIT'],2)

    def test_partial_and_both_kills_both_age_orders_and_wrap(self):
        for reverse,both,wrap in itertools.product((False,True),repeat=3):
            with self.subTest(reverse=reverse,both=both,wrap=wrap):
                r=a.analyze(killed(reverse,both,wrap).text())
                self.assertEqual(r['counts']['KILL'],2 if both else 1)
                self.assertEqual(r['counts']['COMMIT'],0 if both else 1)

    def test_all_pointer_pairs_including_half_ring(self):
        for left,right,self_flush in itertools.product(range(96),range(96),(0,1)):
            distance=(left-right)%96
            self.assertEqual(a.flushed(f'{left//48}:{left%48}',f'{right//48}:{right%48}',self_flush),
                             1<=distance<=48 or distance==0 and self_flush==1)

    def test_illegal_zero_and_no_writes_then_cancel(self):
        f=Fixture();f.enqueue();f.tick('0:5',illegal=1,vl=7);f.tick(auto_commit=False)
        f.tick(flush=('0:5',1));f.tick()
        r=a.analyze(f.text())
        self.assertEqual(r['transactions'][0]['expected_data'],0)
        self.assertEqual(r['counts']['ACCEPTED_THEN_SQUASHED'],1)

    def test_div_completion_seq_and_cancelled_tail(self):
        for fu in (1<<22,1<<26):
            for cancelled in (False,True):
                f=Fixture();f.tick('0:6',div_fu=fu)
                if cancelled:
                    f.tick(flush=('0:5',0));f.tick(div_tail=True)
                else: f.tick(div_done=True)
                f.tick();f.enqueue();f.tick('0:5');f.drain()
                r=a.analyze(f.text())
                self.assertEqual(r['transactions'][0]['seq'],1)
                self.assertEqual(r['counts']['DIV_RESPONSE'],int(not cancelled))

    def test_same_cycle_order_independent(self):
        text=blocked().text();wanted=a.analyze(text);wanted.pop('input_sha256')
        for seed in range(20):
            groups={};rng=random.Random(seed)
            for line in text.splitlines()[1:]: groups.setdefault(int(field(line,'cycle')),[]).append(line)
            rows=[text.splitlines()[0]]
            for _,bucket in sorted(groups.items()): rng.shuffle(bucket);rows.extend(bucket)
            actual=a.analyze('\n'.join(rows)+'\n');actual.pop('input_sha256')
            self.assertEqual(actual,wanted)

    def test_inactive_rob_raw_indices(self):
        text=basic().text()
        for index in (0,47,48,63):
            a.analyze(change(text,'SP1_STATE cycle=1 ','prob=0:0','prob=1:'+str(index)))
        for index in (64,127):
            self.reject(change(text,'SP1_STATE cycle=1 ','prob=0:0','prob=1:'+str(index)))

    def test_schema_modes_and_epoch_reject(self):
        text=basic().text()
        self.reject(text.replace('mode=p4_one_cycle','mode=o2'),text.replace('min_latency=1','min_latency=2'),
                    text.replace('slots=2','slots=1'),text.replace('vpu_width=195','vpu_width=0'),
                    text+text.splitlines()[0]+'\n',text+'SP1_RESET cycle=9 pvalid=0 pseq=0 rvalid=0 rseq=0 divactive=0 divseq=0\n',
                    text+'O2_RESPONSE cycle=9\n',text+'O1_RESPONSE cycle=9\n')

    def test_unknown_truncated_duplicate_fields(self):
        text=basic().text()
        self.reject(text+'SP1_UNKNOWN cycle=9\n',text+'SP1_STATE cycle=9',
                    text.replace('slots=2','slots=2 slots=2'),text.replace('clock=global','clock=gated'),
                    text.replace('DIRECT_R','DIRECT_R_X'),text.replace('directr=1','directr=2'))

    def test_each_required_event_cannot_drop(self):
        texts=[basic().text(),blocked().text()]
        for text in texts:
            for event in ('ACCEPT','DIRECT_R','ENQUEUE_P','MOVE','RESPONSE','COMMIT','VFEX4_ACCEPT','STATE'):
                if 'SP1_'+event+' ' in text: self.reject(drop(text,'SP1_'+event+' '))

    def test_duplicate_route_or_response(self):
        text=blocked().text()
        for event in ('ACCEPT','DIRECT_R','ENQUEUE_P','MOVE','RESPONSE','STALL'):
            row=next(x for x in text.splitlines() if x.startswith('SP1_'+event+' '))
            self.reject(text.replace(row,row+'\n'+row))
        self.reject(text.replace('SP1_DIRECT_R ','SP1_ENQUEUE_P ',1))

    def test_route_and_slot_state_mutants(self):
        text=blocked().text()
        self.reject(change(text,'SP1_STATE cycle=1 ','directr=1','directr=0'),
                    change(text,'SP1_STATE cycle=2 ','enqueuep=1','enqueuep=0'),
                    change(text,'SP1_STATE cycle=3 ','occupancy=2','occupancy=1'),
                    change(text,'SP1_STATE cycle=3 ','rseq=0','rseq=1'),
                    change(text,'SP1_STATE cycle=3 ','pseq=1','pseq=0'),
                    change(text,'SP1_STATE cycle=3 ','vready=0','vready=1'),
                    change(text,'SP1_VFEX4_ACCEPT cycle=2 ','seq=1','seq=9'))

    def test_every_packet_field_and_highbit_mutants(self):
        text=blocked().text()
        for event in ('DIRECT_R','ENQUEUE_P','MOVE','STALL','RESPONSE'):
            row=next(x for x in text.splitlines() if x.startswith('SP1_'+event+' '))
            for key in ('seq','pdest','illegal','data','vecwen','v0wen','exception','vpu','perf'):
                old=field(row,key); n=int(old,0)^1
                new=hex(n) if key in a.HEXES else str(n)
                self.reject(change(text,'SP1_'+event+' ',key+'='+old,key+'='+new))
            old=field(row,'data')
            self.reject(change(text,'SP1_'+event+' ','data='+old,'data='+hex(int(old,16)^(1<<100))))
            old=field(row,'rob');new='0:7'
            self.reject(change(text,'SP1_'+event+' ','rob='+old,'rob='+new))

    def test_partial_cannot_complete_or_hide_corruption(self):
        f=Fixture();f.enqueue();f.tick('0:5')
        self.reject(f.text())
        r=a.analyze(f.text(),require_complete=False)
        self.assertEqual(r['status'],'SP1_PARTIAL_TRACE_AUDIT')
        self.assertEqual(r['pending_count'],1)
        with self.assertRaises(ValueError): a.analyze(f.text()+'SP1_STATE cycle=',require_complete=False)

    def test_missing_final_idle(self):
        text=basic().text(); last=max(int(field(x,'cycle')) for x in text.splitlines() if x.startswith('SP1_STATE '))
        self.reject(drop(text,'SP1_STATE cycle='+str(last)+' '))

    def test_kill_identity_phase_and_survivor(self):
        text=killed().text()
        self.reject(drop(text,'SP1_KILL '),change(text,'SP1_KILL ','slot=P','slot=R'),
                    change(text,'SP1_KILL ','self=0','self=1'),
                    change(text,'SP1_KILL ','rob=0:6','rob=0:5'),
                    change(text,'SP1_VFEX4_REDIRECT ','rob=0:5','rob=0:4'),
                    drop(text,'SP1_VFEX4_REDIRECT '),drop(text,'SP1_RESPONSE '))

    def test_div_bad_classification_overlap_or_missing(self):
        f=Fixture();f.tick('0:4',div_fu=1<<22);f.tick(div_done=True);f.tick();text=f.text()
        self.reject(drop(text,'SP1_DIV_ACCEPT '),drop(text,'SP1_DIV_OUTPUT '),
                    change(text,'SP1_DIV_OUTPUT ','cancelled=0','cancelled=1'),
                    change(text,'SP1_DIV_OUTPUT ','seq=0','seq=1'),
                    change(text,'SP1_STATE cycle=2 ','outready=1','outready=0'))
        text=blocked().text()
        self.reject(change(text,'SP1_STATE cycle=3 ','divoccupied=0','divoccupied=1'))

    def test_local_scope_never_fullcore(self):
        text=local_text(blocked().text())
        self.reject(text)
        r=a.analyze(text,local=True)
        self.assertEqual(r['status'],'SP1_LOCAL_TRACE_PASS')
        self.assertEqual(r['qualification'],'LOCAL_FU_PARENT_ONLY')
        self.assertEqual(r['counts']['COMMIT'],0)
        with self.assertRaises(ValueError): a.analyze(basic().text(),local=True)

    def test_local_partial_cancel(self):
        for reverse,both in itertools.product((False,True),repeat=2):
            r=a.analyze(local_text(killed(reverse,both).text()),local=True)
            self.assertEqual(r['counts']['KILL'],2 if both else 1)

    def test_uart_interleaving_old_workload_tags(self):
        text=basic().text();row=next(x for x in text.splitlines(keepends=True) if x.startswith('SP1_STATE '))
        text=text.replace(row,'O2_DI'+row+'AG_BEGIN version=1\n')
        _,uart=a.extract_events_and_uart(text)
        self.assertIn('O2_DIAG_BEGIN',uart)
        a.analyze(text)
        self.reject(text+'O2_DIAG_UNKNOWN x=1\n')

    def test_explicit_mode_dispatch_no_fallback(self):
        import dispatch
        stable=('O2_SCHEMA version=1 clock=global latency=2 slots=2 rob_size=48 '
                'ftq_size=8 vlen=128 vpu_width=195 perf_width=577\n'
                'O2_STATE cycle=0 pvalid=0 pseq=0 prob=0:0 ppdest=0 rvalid=0 rseq=0 rrob=0:0 rpdest=0 '
                'occupancy=0 invalid=0 inready=0 vready=1 outvalid=0 outready=1 move=0 killp=0 killr=0 '
                'divactive=0 divseq=0 divoccupied=0 busy=0\n')
        self.assertEqual(dispatch.analyze_mode('stable-0f',stable)['status'],'O2_TRACE_PASS')
        self.assertEqual(dispatch.analyze_mode('sp1-p4',basic().text())['status'],'SP1_TRACE_PASS')
        for mode,text in [('stable-0f',basic().text()),('sp1-p4',stable),('autodetect',stable)]:
            with self.assertRaises(ValueError):dispatch.analyze_mode(mode,text)

    def test_local_reset_drops_exact_pending_identity(self):
        for two in (False,True):
            f=Fixture();f.enqueue();f.tick('0:5')
            if two: f.enqueue('0:6',8);f.tick('0:6',ready=0)
            reset=f'SP1_RESET cycle={f.cycle} pvalid={int(two)} pseq=1 rvalid=1 rseq=0 divactive=0 divseq=0\n'
            text=local_text(f.text())+reset+local_text(basic().text())
            r=a.analyze_local(text)
            self.assertEqual(r['reset_drops'],2 if two else 1)
            self.assertFalse(r['fullcore_qualified'])
            for mutant in (text.replace('rvalid=1 rseq=0','rvalid=1 rseq=9'),
                           text.replace(reset,reset.replace('rvalid=1','rvalid=0')),
                           text[:text.rfind('SP1_SCHEMA ')]):
                with self.assertRaises(ValueError): a.analyze_local(mutant)
            self.reject(text)

    def test_local_div_reset_identity(self):
        for fu in (1<<22,1<<26):
            f=Fixture();f.tick('0:6',div_fu=fu)
            reset='SP1_RESET cycle=2 pvalid=0 pseq=0 rvalid=0 rseq=0 divactive=1 divseq=0\n'
            text=local_text(f.text())+reset+local_text(basic().text())
            r=a.analyze_local(text)
            self.assertEqual(r['div_reset_drops'],1)
            self.assertEqual(r['reset_drops'],0)
            with self.assertRaisesRegex(ValueError,'reset pending sequence'):
                a.analyze_local(text.replace(reset,reset.replace('divseq=0','divseq=1')))
            with self.assertRaisesRegex(ValueError,'reset pending validity'):
                a.analyze_local(text.replace(reset,reset.replace('divactive=1','divactive=0')))

    def test_oracle_signed_extremes_and_upper_source_ignore(self):
        self.assertEqual(a.dot_result(int('80'*8,16),int('80'*8,16)),131072)
        self.assertEqual(a.dot_result(int('ff'*8,16),int('01'*8,16)),0xfffffff8)
        self.assertEqual(a.dot_result((1<<127)|255,1),0xffffffff)


if __name__=='__main__': unittest.main()
