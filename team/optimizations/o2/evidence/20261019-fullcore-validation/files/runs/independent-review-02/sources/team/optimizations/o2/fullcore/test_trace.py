"""Synthetic trace mutation tests. These exercise the checker, not RTL."""
import copy
import itertools
import random
import unittest
import analyze as a
import check_control as control


class Fixture:
    def __init__(self):
        self.header = ('O2_SCHEMA version=1 clock=global latency=2 slots=2 rob_size=48 '
                       'ftq_size=8 vlen=128 vpu_width=195 perf_width=577')
        self.rows, self.entries = [], {}
        self.p = self.r = self.div = self.last_div = None
        self.seq, self.cycle = 0, 1

    def add(self, kind, /, **f):
        self.rows.append('O2_' + kind + ' ' + ' '.join(
            k + '=' + (hex(v) if k in a.HEXES else str(v)) for k, v in f.items()))

    def enqueue(self, rob='0:5', pdest=7, vd=10, ftq='0:1'):
        e = dict(rob=rob, pdest=pdest, vd=vd, ftq=ftq, pc=0x80000000 + len(self.entries)*4)
        self.entries[rob] = e
        self.add('ENQUEUE', cycle=self.cycle - 1, rob=rob, pc=e['pc'], ftq=ftq,
                 word=(0x0294050b & ~(31 << 7)) | (vd << 7))
        return rob

    def request(self, rob, illegal=0, vl=8, vs1=0x807f01ff01020304, vs2=0xfe8001ff02040506):
        e = self.entries[rob]
        return dict(cycle=self.cycle, seq=self.seq, rob=rob, pdest=e['pdest'], vl=vl,
                    illegal=illegal, vecwen=int(e['vd'] != 0), v0wen=int(e['vd'] == 0),
                    vpu=0x123000 + self.seq, perf=0xabc000 + self.seq, vs1=vs1, vs2=vs2)

    def packet(self, kind, t):
        f = {k:t[k] for k in ('seq','rob','pdest','illegal')}
        if kind != 'MOVE':
            f['data'] = 0 if t['illegal'] else a.dot_result(t['vs1'], t['vs2'])
        f.update(vecwen=0 if t['illegal'] else t['vecwen'],
                 v0wen=0 if t['illegal'] else t['v0wen'],
                 exception=4 if t['illegal'] else 0, vpu=t['vpu'], perf=t['perf'])
        self.add(kind, cycle=self.cycle, **f)

    def commit(self, t, cycle=None):
        e = self.entries[t['rob']]
        self.add('COMMIT', cycle=self.cycle + 1 if cycle is None else cycle,
                 rob=t['rob'], pc=e['pc'], ftq=e['ftq'])

    def tick(self, rob=None, *, ready=1, flush=None, wait=None, illegal=0, vl=8,
             div_fu=None, div_done=False, div_tail=False, auto_commit=True):
        c, p, r, d = self.cycle, self.p, self.r, self.div
        kp = bool(p and flush and a.flushed(p['rob'], *flush))
        kr = bool(r and flush and a.flushed(r['rob'], *flush))
        lp, lr = p is not None and not kp, r is not None and not kr
        move, out = bool(lp and (not lr or ready)), bool(lr)
        vready = int((not lp or not lr or ready) and not flush)
        divoccupied = int(d is not None or div_tail)
        accepted = rob is not None
        assert not (accepted and wait)
        request = self.request(rob, illegal, vl) if rob and not div_fu else None
        div_request = dict(cycle=c, seq=self.seq, rob=rob, fu=div_fu,
                           pdest=11) if div_fu else None
        if request or div_request:
            assert not flush and not divoccupied
            if request:
                assert vready
            else:
                assert not p and not r
        occupancy = int(p is not None) + int(r is not None)
        busy = int(bool(occupancy or divoccupied))
        self.add('STATE', cycle=c, pvalid=int(p is not None), pseq=p['seq'] if p else 0,
                 prob=p['rob'] if p else '0:0', ppdest=p['pdest'] if p else 0,
                 rvalid=int(r is not None), rseq=r['seq'] if r else 0,
                 rrob=r['rob'] if r else '0:0', rpdest=r['pdest'] if r else 0,
                 occupancy=occupancy, invalid=int(accepted or wait is not None),
                 inready=int(accepted), vready=vready, outvalid=int(out), outready=ready,
                 move=int(move), killp=int(kp), killr=int(kr),
                 divactive=int(d is not None), divseq=d['seq'] if d else 0,
                 divoccupied=divoccupied, busy=busy)
        if flush:
            origin, self_flush = flush
            self.add('REDIRECT', cycle=c-1, rob=origin, ftq='0:1', self=self_flush)
            self.add('VFEX4_REDIRECT', cycle=c, rob=origin, self=self_flush)
        if accepted:
            t = request or div_request
            self.add('VFEX4_ACCEPT', cycle=c, seq=t['seq'], rob=rob,
                     fu=a.VDOT if request else div_fu, pdest=t['pdest'])
            self.add('ACCEPT' if request else 'DIV_ACCEPT', **t)
            self.seq += 1
        if wait:
            self.add('VFEX4_WAIT', cycle=c, rob=wait, fu=a.VDOT, busy=busy)
        for slot, t, killed in (('P',p,kp),('R',r,kr)):
            if killed:
                self.add('KILL', cycle=c, seq=t['seq'], slot=slot, rob=t['rob'],
                         pdest=t['pdest'], redirect=flush[0], self=flush[1])
        if move:
            self.packet('MOVE', p)
        if out:
            self.packet('RESPONSE' if ready else 'STALL', r)
            if ready and auto_commit and not r['illegal']:
                self.commit(r)
        dk = d and flush and a.flushed(d['rob'], *flush)
        if dk:
            self.add('DIV_KILL', cycle=c, **{k:d[k] for k in ('seq','rob','fu','pdest')},
                     redirect=flush[0], self=flush[1])
            d['cancelled'] = True
            self.div = None
        if div_done or div_tail:
            t = self.last_div
            self.add('DIV_OUTPUT', cycle=c, **{k:t[k] for k in ('seq','rob','fu','pdest')},
                     ready=1, cancelled=int(t.get('cancelled', False)))
            if not t.get('cancelled'):
                self.div = None
        if div_request:
            self.div = self.last_div = div_request
        self.p = request if request else p if lp and not move else None
        self.r = p if move else r if lr and not ready else None
        self.cycle += 1
        return request

    def drain(self):
        while self.p or self.r:
            self.tick()
        self.tick()

    def text(self):
        rows = sorted(self.rows, key=lambda line:int(line.split('cycle=')[1].split()[0]))
        return self.header + '\n' + '\n'.join(rows) + ('\n' if rows else '')


def basic():
    f=Fixture()
    f.enqueue()
    f.tick('0:5')
    f.drain()
    return f


def stream():
    f=Fixture()
    for i in range(5,9):
        f.enqueue(f'0:{i}', pdest=i+2, vd=0 if i == 6 else 10)
    for i in range(5,9):
        f.tick(f'0:{i}')
    f.drain()
    return f


def blocked():
    f=Fixture()
    f.enqueue(); f.enqueue('0:6',8)
    f.tick('0:5'); f.tick('0:6')
    f.tick(ready=0,wait='0:7'); f.tick(ready=0,wait='0:7')
    f.drain()
    return f


def killed(reverse=False, both=False, wrap=False):
    f=Fixture()
    older,newer=('0:47','1:0') if wrap else ('0:5','0:6')
    first,second=(newer,older) if reverse else (older,newer)
    f.enqueue(first); f.enqueue(second,8)
    f.tick(first); f.tick(second)
    f.tick(ready=0,flush=(older,int(both)),auto_commit=False)
    f.drain()
    return f


def change(text, prefix, old, new):
    rows=text.splitlines(keepends=True)
    for i,row in enumerate(rows):
        if row.startswith(prefix):
            assert old in row,(row,old)
            rows[i]=row.replace(old,new,1)
            return ''.join(rows)
    raise AssertionError(prefix)


def drop(text,prefix):
    rows=text.splitlines(keepends=True)
    for i,row in enumerate(rows):
        if row.startswith(prefix):
            return ''.join(rows[:i]+rows[i+1:])
    raise AssertionError(prefix)


class Tests(unittest.TestCase):
    def test_single_full128_oracle(self):
        r=a.analyze(basic().text())
        self.assertEqual(r['status'],'O2_TRACE_PASS')
        self.assertEqual(r['response_latency_histogram'],{'2':1})
        self.assertEqual(r['counts']['COMMIT'],1)

    def test_sustained_pipeline_accept_gap_and_v0(self):
        r=a.analyze(stream().text())
        self.assertEqual(r['counts']['TRIPLE_OVERLAP'],2)
        self.assertEqual(r['counts']['MULTI_INFLIGHT'],3)
        self.assertEqual(r['observed_accept_gap_histogram'],{'1':3})
        self.assertEqual(r['response_latency_histogram'],{'2':4})

    def test_two_slot_backpressure_preserves_packets(self):
        r=a.analyze(blocked().text())
        self.assertEqual(r['counts']['FULL_STALL'],2)
        self.assertEqual(r['counts']['STALL'],2)
        self.assertEqual(r['response_latency_histogram'],{'4':2})

    def test_partial_and_full_kills_both_accept_age_orders_and_wrap(self):
        for reverse,both,wrap in itertools.product((False,True),repeat=3):
            with self.subTest(reverse=reverse,both=both,wrap=wrap):
                r=a.analyze(killed(reverse,both,wrap).text())
                self.assertEqual(r['counts']['KILL'],2 if both else 1)
                self.assertEqual(r['counts']['PARTIAL_KILL'],0 if both else 1)
                self.assertEqual(r['counts']['COMMIT'],0 if both else 1)
                if not both:
                    self.assertEqual(r['counts']['KILL_R' if reverse else 'KILL_P'],1)

    def test_all_pointer_pairs_including_distance48(self):
        for left,right,self_flush in itertools.product(range(96),range(96),(0,1)):
            distance=(left-right)%96
            self.assertEqual(a.flushed(f'{left//48}:{left%48}',f'{right//48}:{right%48}',self_flush),
                             1<=distance<=48 or distance==0 and self_flush==1)

    def test_illegal_packet_zero_and_no_writes_then_rob_cancel(self):
        f=Fixture(); f.enqueue(); f.tick('0:5',illegal=1,vl=7); f.tick(); f.tick(auto_commit=False)
        f.tick(flush=('0:5',1)); f.tick()
        r=a.analyze(f.text())
        self.assertEqual(r['counts']['COMMIT'],0)
        self.assertEqual(r['counts']['ACCEPTED_THEN_SQUASHED'],1)

    def test_div_seq_gap_completion(self):
        f=Fixture(); f.tick('0:4',div_fu=1<<22); f.tick(); f.tick(div_done=True); f.tick()
        f.enqueue(); f.tick('0:5'); f.drain()
        r=a.analyze(f.text())
        self.assertEqual(r['counts']['DIV_RESPONSE'],1)
        self.assertEqual(r['transactions'][0]['seq'],1)

    def test_div_cancel_then_physical_tail(self):
        f=Fixture(); f.tick('0:6',div_fu=1<<26); f.tick(flush=('0:5',0))
        f.tick(div_tail=True); f.tick()
        f.enqueue(); f.tick('0:5'); f.drain()
        r=a.analyze(f.text())
        self.assertEqual(r['counts']['DIV_KILL'],1)
        self.assertEqual(r['counts']['DIV_RESPONSE'],0)

    def test_cancelled_div_physical_tail_keeps_parent_occupied(self):
        f=Fixture(); f.tick('0:6',div_fu=1<<26); f.tick(flush=('0:5',0))
        f.tick(div_tail=True); f.tick()
        text=change(f.text(),'O2_STATE cycle=3 ','divoccupied=1','divoccupied=0')
        text=change(text,'O2_STATE cycle=3 ','busy=1','busy=0')
        with self.assertRaisesRegex(ValueError,'physical DIV output'):
            a.analyze(text)

    def test_div_ready_matches_real_shared_output_ready(self):
        f=Fixture(); f.tick('0:4',div_fu=1<<22); f.tick(div_done=True); f.tick()
        text=change(f.text(),'O2_STATE cycle=2 ','outready=1','outready=0')
        with self.assertRaisesRegex(ValueError,'shared parent ready'):
            a.analyze(text)

    def test_same_cycle_commit_wrap_is_printf_order_independent(self):
        f=Fixture(); f.enqueue('0:47',7,ftq='0:7'); f.enqueue('1:0',8,ftq='1:0')
        first=f.tick('0:47'); second=f.tick('1:0')
        f.tick(auto_commit=False); f.tick(auto_commit=False); f.tick()
        f.commit(first,cycle=6); f.commit(second,cycle=6)
        text=f.text()
        rows=[row for row in text.splitlines() if row.startswith('O2_COMMIT ')]
        wanted=a.analyze(text); wanted.pop('input_sha256')
        self.assertEqual(wanted['counts']['ROB_WRAP'],1)
        self.assertEqual(wanted['counts']['FTQ_WRAP'],1)
        prefix='\n'.join(row for row in text.splitlines() if not row.startswith('O2_COMMIT '))+'\n'
        for permutation in itertools.permutations(rows):
            result=a.analyze(prefix+'\n'.join(permutation)+'\n'); result.pop('input_sha256')
            self.assertEqual(result,wanted)

    def test_same_cycle_print_order_irrelevant(self):
        text=stream().text()
        wanted=a.analyze(text); wanted.pop('input_sha256')
        lines=text.splitlines()
        for seed in range(20):
            rng=random.Random(seed)
            groups={}
            for line in lines[1:]:
                groups.setdefault(int(line.split('cycle=')[1].split()[0]),[]).append(line)
            shuffled=[lines[0]]
            for cycle,rows in sorted(groups.items()):
                rng.shuffle(rows); shuffled.extend(rows)
            result=a.analyze('\n'.join(shuffled)+'\n'); result.pop('input_sha256')
            self.assertEqual(result,wanted)

    def test_partial_is_explicit_and_not_coverage_pass(self):
        f=Fixture(); f.enqueue(); f.tick('0:5')
        with self.assertRaisesRegex(ValueError,'unfinished|inactive'):
            a.analyze(f.text())
        r=a.analyze(f.text(),require_complete=False)
        self.assertEqual(r['status'],'O2_PARTIAL_TRACE_AUDIT')
        self.assertEqual(r['pending_count'],1)

    def test_partial_does_not_hide_malformed_or_cross_identity(self):
        text=basic().text()
        for mutant in (text+'O2_STATE cycle=',change(text,'O2_ACCEPT ','pdest=7','pdest=8')):
            with self.assertRaises(ValueError):
                a.analyze(mutant,require_complete=False)

    def test_uart_interleaving_and_t13_records(self):
        f=Fixture()
        text=f.header+'\nT12_GROUP_O2_STATE cycle=1 pvalid=0 pseq=0 prob=0:0 ppdest=0 rvalid=0 rseq=0 rrob=0:0 rpdest=0 occupancy=0 invalid=0 inready=0 vready=1 outvalid=0 outready=1 move=0 killp=0 killr=0 divactive=0 divseq=0 divoccupied=0 busy=0\nPASS id=0\nT13_CSR_SAMPLE cycle=1 addr=0xc00 data=0x2 wen=0\n'
        events,uart=a.extract_events_and_uart(text)
        self.assertEqual(uart,'T12_GROUP_PASS id=0\n')
        self.assertEqual(len(events),2)

    def test_parse_rejects_wrong_schema_unknown_truncated_and_legacy(self):
        text=basic().text()
        mutants=[text.replace('slots=2','slots=1'),text.replace('vpu_width=195','vpu_width=0'),
                 text.replace('prob=0:0','prob=0:48',1),text.replace('pvalid=0','pvalid=2',1),
                 text+'O2_UNKNOWN cycle=99\n',text+'O2_STATE cycle=99',
                 text+'O1_RESPONSE cycle=99\n',text.replace('O2_MOVE','O2_MOVE_X'),
                 text+text.splitlines()[0]+'\n',text.replace('clock=global','clock=gated')]
        for mutant in mutants:
            with self.subTest(mutant=mutant[-100:]),self.assertRaises(ValueError):
                a.analyze(mutant)

    def test_duplicate_dropped_or_impossible_events(self):
        text=stream().text()
        mutants=[drop(text,'O2_ACCEPT '),drop(text,'O2_MOVE '),drop(text,'O2_RESPONSE '),
                 drop(text,'O2_STATE cycle=2 '),drop(text,'O2_COMMIT '),
                 change(text,'O2_STATE cycle=3 ','occupancy=2','occupancy=1'),
                 change(text,'O2_STATE cycle=3 ','move=1','move=0'),
                 change(text,'O2_STATE cycle=3 ','vready=1','vready=0'),
                 change(text,'O2_STATE cycle=3 ','outvalid=1','outvalid=0'),
                 change(text,'O2_STATE cycle=3 ','busy=1','busy=0'),
                 change(text,'O2_VFEX4_ACCEPT cycle=2 ','seq=1','seq=9')]
        response=next(row for row in text.splitlines() if row.startswith('O2_RESPONSE '))
        mutants.append(text.replace(response,response+'\n'+response))
        for mutant in mutants:
            with self.subTest(mutant=mutant[-100:]),self.assertRaises(ValueError):
                a.analyze(mutant)

    def test_packet_metadata_cross_slot_and_high_bit_faults(self):
        text=stream().text()
        response=next(row for row in text.splitlines() if row.startswith('O2_RESPONSE '))
        old_data=re_field(response,'data')
        mutants=[
            change(text,'O2_RESPONSE ','pdest=7','pdest=8'),
            change(text,'O2_RESPONSE ','rob=0:5','rob=0:6'),
            change(text,'O2_RESPONSE ','seq=0','seq=1'),
            change(text,'O2_RESPONSE ','vecwen=1','vecwen=0'),
            change(text,'O2_RESPONSE ','exception=0x0','exception=0x4'),
            change(text,'O2_RESPONSE ','vpu=0x123000','vpu=0x123001'),
            change(text,'O2_RESPONSE ','perf=0xabc000','perf=0xabc001'),
            change(text,'O2_RESPONSE ','data='+old_data,'data='+hex(int(old_data,16)^(1<<100))),
            change(text,'O2_MOVE ','pdest=7','pdest=8'),
            change(text,'O2_STATE cycle=3 ','rseq=0','rseq=1'),
        ]
        for mutant in mutants:
            with self.subTest(mutant=mutant[-100:]),self.assertRaises(ValueError):
                a.analyze(mutant)

    def test_stall_mutation_or_missing_history_rejected(self):
        text=blocked().text()
        old=re_field(next(x for x in text.splitlines() if x.startswith('O2_STALL ')),'data')
        for mutant in (drop(text,'O2_STALL '),change(text,'O2_STALL ','data='+old,'data=0x0'),
                       change(text,'O2_STALL ','perf=0xabc000','perf=0xabc001')):
            with self.assertRaises(ValueError):
                a.analyze(mutant)

    def test_kill_wrong_slot_missed_survivor_wrong_phase(self):
        text=killed().text()
        for mutant in (drop(text,'O2_KILL '),
                       change(text,'O2_KILL ','slot=P','slot=R'),
                       change(text,'O2_KILL ','rob=0:6','rob=0:5'),
                       change(text,'O2_KILL ','self=0','self=1'),
                       change(text,'O2_VFEX4_REDIRECT ','rob=0:5','rob=0:4'),
                       change(text,'O2_STATE cycle=3 ','killp=1','killp=0'),
                       drop(text,'O2_VFEX4_REDIRECT ')):
            with self.assertRaises(ValueError):
                a.analyze(mutant)

    def test_runtime_reset_is_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError,'runtime reset'):
            a.analyze(Fixture().header+'\nO2_RESET cycle=3 pvalid=0 pseq=0 rvalid=0 rseq=0 divactive=0 divseq=0\n')

    def test_div_overlap_or_missing_completion_rejected(self):
        f=Fixture(); f.tick('0:4',div_fu=1<<22); f.tick(div_done=True); f.tick()
        text=f.text()
        for mutant in (drop(text,'O2_DIV_ACCEPT '),drop(text,'O2_DIV_OUTPUT '),
                       change(text,'O2_DIV_OUTPUT ','cancelled=0','cancelled=1'),
                       change(text,'O2_DIV_OUTPUT ','seq=0','seq=1')):
            with self.assertRaises(ValueError):
                a.analyze(mutant)
        text=stream().text()
        with self.assertRaisesRegex(ValueError,'overlap'):
            a.analyze(change(text,'O2_STATE cycle=3 ','divoccupied=0','divoccupied=1'))

    def test_control_missing_coverage_reports_incomplete_not_pass(self):
        text=basic().text()
        text=('The reference model is synthetic\n'
              'The first instruction of core 0 has commited. Difftest enabled.\n'+text+
              'T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1\n'+
              ''.join(f'T12_GROUP_PASS id={i} checkpoints=32 bytes=16384\n' for i in range(4))+
              'T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0\nHIT GOOD TRAP\n')
        manifest={'groups':[{'vdot_count':1}],'speculation':{'expected_architectural_vdot':0}}
        result=control.check(text,manifest,0)
        self.assertEqual(result['status'],'O2_COVERAGE_INCOMPLETE')
        self.assertFalse(result['legacy_coverage_complete'])
        self.assertFalse(result['o2_coverage_complete'])
        self.assertEqual(tuple(result['o2_coverage']),a.REQUIRED_O2_COVERAGE)
        for bad in (text.replace('failures=0','failures=1'),text+'HIT GOOD TRAP\n'):
            with self.assertRaises(ValueError):
                control.check(bad,manifest,0)
        with self.assertRaises(ValueError):
            control.check(text,manifest,1)
        with self.assertRaisesRegex(ValueError,'different raw trace'):
            control.check(text,manifest,0,analysis=a.analyze(basic().text()))


    def test_o2_uart_prefix_interruption_and_exact_allowlist(self):
        text=basic().text()
        observer=next(row for row in text.splitlines(keepends=True) if row.startswith('O2_STATE cycle=1 '))
        text=text.replace(observer,'O2_DI'+observer+'AG_BEGIN version=1\n')
        _,uart=a.extract_events_and_uart(text)
        self.assertIn('O2_DIAG_BEGIN version=1\n',uart)
        for tag in a.O2_UART_TAGS:
            _,uart=a.extract_events_and_uart(basic().text()+'O2_'+tag+' arbitrary_uart_payload\n')
            self.assertIn('O2_'+tag,uart)
        for tag in ('DIAG_UNKNOWN','CONTROL_X','STATE',''):
            with self.assertRaises(ValueError):
                a.extract_events_and_uart(basic().text()+'O2_'+tag+' arbitrary_uart_payload\n')

    def test_control_all_fixed_coverage_targets(self):
        f=Fixture()
        for i in range(5,8):
            f.enqueue(f'0:{i}',i+2)
        f.tick('0:5'); f.tick('0:6'); f.tick('0:7')
        f.tick(ready=0,wait='0:8')
        f.drain()
        for reverse in (False,True):
            older,newer='0:10','0:11'
            f.enqueue(older,7); f.enqueue(newer,8)
            f.tick(newer if reverse else older)
            f.tick(older if reverse else newer)
            f.tick(ready=0,flush=(older,0),auto_commit=False)
            f.drain()
        f.tick('0:12',div_fu=1<<22); f.tick(div_done=True); f.tick()
        for i in range(9):
            rob=f'{i%2}:20'
            f.enqueue(rob,7,ftq=f'{i%2}:1'); f.tick(rob); f.drain()
        text=('The reference model is synthetic\n'
              'The first instruction of core 0 has commited. Difftest enabled.\n'+f.text()+
              'T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1\n'+
              ''.join(f'T12_GROUP_PASS id={i} checkpoints=32 bytes=16384\n' for i in range(4))+
              'T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0\nHIT GOOD TRAP\n')
        manifest={'groups':[{'vdot_count':14}],'speculation':{'expected_architectural_vdot':0}}
        result=control.check(text,manifest,0)
        self.assertEqual(result['status'],'O2_CONTROL_REGRESSION_PASS')
        self.assertTrue(all(result['coverage'].values()))

    def test_source_oracle_signed_boundaries_and_high_input_bytes(self):
        self.assertEqual(a.dot_result(int('80'*8,16),int('80'*8,16)),131072)
        self.assertEqual(a.dot_result(int('ff'*8,16),int('01'*8,16)),0xfffffff8)
        self.assertEqual(a.dot_result((1<<127)|0xff,1),0xffffffff)


def re_field(line,key):
    return next(s.split('=',1)[1] for s in line.split() if s.startswith(key+'='))


if __name__=='__main__':
    unittest.main()
