"""Host specification tests; passing does NOT validate production RTL."""
import itertools
from pathlib import Path
import random
import unittest
from contract_model import Contract, Request, next_busy

ROOT = Path(__file__).resolve().parents[3]


class ContractTests(unittest.TestCase):
    def test_default_and_t14_intervals(self):
        for latency in (2, 3):
            c = Contract(handoff=False, latency=latency)
            times = []
            for _ in range(100):
                e = c.step(Request(len(times)))
                if e['accepted']: times.append(e['cycle'])
            self.assertEqual(set(b-a for a,b in zip(times,times[1:])), {latency+1})

    def test_o1_interval_and_busy_replacement(self):
        c = Contract(); times=[]
        for _ in range(100):
            e=c.step(Request(len(times)))
            if e['accepted']: times.append(e['cycle'])
            if e['response']:
                self.assertIsNotNone(e['accepted']); self.assertTrue(e['busy_after'])
        self.assertEqual(set(b-a for a,b in zip(times,times[1:])), {2})

    def test_old_metadata_during_handoff(self):
        c=Contract();c.step(Request(1,v0=True));c.step(Request(2,illegal=True))
        e=c.step(Request(2,illegal=True))
        self.assertEqual(e['visible'],dict(serial=1,v0_wen=True,vec_wen=False,illegal=False))
        c.step();e=c.step(Request(3))
        self.assertEqual(e['visible'],dict(serial=2,v0_wen=False,vec_wen=False,illegal=True))

    def test_stall_then_overlap(self):
        c=Contract();c.step(Request(1));c.step(Request(2))
        for i in range(9):
            e=c.step(Request(i+2,v0=True),ready=False)
            self.assertIsNone(e['accepted']);self.assertEqual(e['visible']['serial'],1)
        e=c.step(Request(99,v0=True));self.assertEqual(e['response'].serial,1)
        self.assertEqual(e['accepted'].serial,99)

    def test_cancel_beats_response_and_new_request(self):
        c=Contract();c.step(Request(1));c.step()
        e=c.step(Request(2),redirect=True,cancel=True)
        self.assertIsNone(e['response']);self.assertIsNone(e['accepted']);self.assertFalse(e['busy_after'])

    def test_unrelated_redirect_keeps_old_response(self):
        c=Contract();c.step(Request(1));c.step()
        e=c.step(Request(2),redirect=True)
        self.assertEqual(e['response'].serial,1);self.assertIsNone(e['accepted'])

    def test_reset_beats_handoff(self):
        c=Contract();c.step(Request(1));c.step()
        e=c.step(Request(2),reset=True)
        self.assertIsNone(e['response']);self.assertIsNone(e['accepted']);self.assertEqual(c.reset_dropped,1)

    def test_idle_redirect_and_reset(self):
        for kwargs in ({'redirect':True},{'reset':True}):
            c=Contract();self.assertIsNone(c.step(Request(1),**kwargs)['accepted'])

    def test_div_vdot_switch_not_overlapped(self):
        for old,new in (('div','vdot'),('vdot','div'),('div','div')):
            c=Contract();c.step(Request(0,kind=old));seen=False
            for _ in range(7):
                e=c.step(Request(1,kind=new))
                if e['response']:
                    self.assertIsNone(e['accepted']);seen=True;break
            self.assertTrue(seen)
            self.assertIsNotNone(c.step(Request(1,kind=new))['accepted'])

    def test_no_phantom_request_on_drain(self):
        c=Contract();c.step(Request(1));c.step();e=c.step()
        self.assertIsNotNone(e['response']);self.assertIsNone(e['accepted'])
        for _ in range(6):self.assertIsNone(c.step()['response'])

    def test_parent_busy_exhaustive(self):
        # 64 Boolean assignments. Reset is applied by the register, not this equation.
        for busy,inf,outf,ko,ki,en in itertools.product((False,True),repeat=6):
            got=next_busy(busy=busy,input_fire=inf,output_fire=outf,kill_old=ko,kill_input=ki,enabled=en)
            if (inf and ki) or (busy and ko): expect=False
            elif en: expect=bool(inf or (busy and not outf))
            else: expect=False if outf else bool(busy or inf)
            self.assertEqual(got,expect)

    def test_old_priority_defect_is_distinguishable(self):
        args=dict(busy=True,input_fire=True,output_fire=True,kill_old=False,kill_input=False)
        self.assertTrue(next_busy(**args,enabled=True));self.assertFalse(next_busy(**args,enabled=False))

    def test_random_transaction_conservation(self):
        c=Contract();rng=random.Random(0x20261018);sent=[];finished=set()
        for i in range(10000):
            redirect=rng.randrange(13)==0;cancel=redirect and rng.choice((False,True));reset=rng.randrange(211)==0
            q=Request(i,kind='div' if i%7==0 else 'vdot',v0=bool(i%2),illegal=i%11==0)
            e=c.step(q if rng.randrange(4) else None,ready=bool(rng.randrange(3)),redirect=redirect,cancel=cancel,reset=reset)
            if e['accepted']:sent.append(e['accepted'].serial)
            if e['response']:
                self.assertIn(e['response'].serial,sent);self.assertNotIn(e['response'].serial,finished)
                finished.add(e['response'].serial)
        while c.pending:c.step()
        self.assertEqual(c.accepted,c.responded+c.killed+c.reset_dropped)

    def test_invalid_protocol_inputs(self):
        with self.assertRaises(ValueError):Contract(latency=3)
        with self.assertRaises(ValueError):Contract().step(cancel=True)
        with self.assertRaises(ValueError):Contract().step(Request(0,'unknown'))

    def test_source_legacy_branches_still_present(self):
        v=(ROOT/'src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala').read_text()
        e=(ROOT/'src/main/scala/xiangshan/backend/exu/ExeUnit.scala').read_text()
        for text in ('io.in.ready := state === idle && !io.flush.valid && !reset.asBool',
                     'when(io.out.fire) { state := idle }', 'assert(!io.in.ready)'):
            self.assertIn(text,v)
        self.assertIn('in1ToN.io.in.valid := io.in.valid && !busy',e)
        self.assertIn('io.in.ready := !busy && in1ToN.io.in.ready',e)

    def test_source_registered_writes_and_parent_scope(self):
        v=(ROOT/'src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala').read_text()
        e=(ROOT/'src/main/scala/xiangshan/backend/exu/ExeUnit.scala').read_text()
        self.assertIn('RegEnable(inCtrl.vecWen.get, io.in.fire)',v)
        self.assertIn('RegEnable(inCtrl.v0Wen.get, io.in.fire)',v)
        self.assertIn('busy && activeIsVDot && newIsVDot && vdotFu.io.out.valid && io.out.ready',e)
        self.assertIn('vdotFu.io.in.fire === (io.in.fire && newIsVDot)',e)
        self.assertIn('io.in.ready := Cat(io.out.map(_.ready)).andR',e)

    def test_source_option_and_observer_guards(self):
        s=(ROOT/'src/main/scala/xiangshan/backend/fu/wrapper/VDotHandoff.scala').read_text()
        for text in ('case None | Some("0") => false','case Some("1") => true','VDOT_T14_FUSED_INPUT',
                     'VDOT_T12_TRACE','VDOT_T13_TRACE','def enabled: Boolean'):
            self.assertIn(text,s)


if __name__=='__main__':unittest.main()
