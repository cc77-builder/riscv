"""New directed selector controls; all input traces are explicitly synthetic."""
import unittest
from copy import deepcopy
from o2_cancel_fixtures import Fixture, change, drop
from o2_cancel_selector import select, base
A0, B0, A1, B1 = 0x80001000, 0x80001004, 0x80002000, 0x80002004
L, R = 0x807f01ff01020304, 0xfe8001ff02040506

def at(f, rob, pc, vd):
    f.enqueue(rob, pdest=(vd+3), vd=vd)
    f.entries[rob]['pc'] = pc
    f.rows[-1] = f.rows[-1].split(' pc=')[0] + ' pc='+hex(pc)+' ftq=0:1 word='+hex((0x0294050b & ~(31<<7)) | (vd<<7))

def source(wrap=False, self_flush=0, same_cycle=False, training_only_hit=False, s0_b_cancelled=False):
    f = Fixture()
    at(f, '0:1', A0, 16);at(f, '0:2', B0, 17)
    f.tick('0:1');f.tick('0:2', ready=0)
    if s0_b_cancelled:
        f.tick();f.tick(auto_commit=False);f.tick(flush=('0:1',0));f.drain()
    else:
        f.drain()
    if training_only_hit:
        at(f, '0:10', A1, 16);at(f, '0:12', B1, 17)
        f.tick('0:10');f.tick('0:12', ready=0);f.tick(ready=0,flush=('0:11',0));f.drain()
        at(f, '0:13', B1, 17);f.tick('0:13');f.drain()
        at(f, '0:15', A1, 16);f.tick('0:15');f.drain()
        ordinal=1
    else:
        a, branch, b = ('0:47','1:0','1:1') if wrap else ('0:10','0:11','0:12')
        at(f,a,A1,16);at(f,b,B1,17)
        f.tick(a);f.tick(b,ready=0)
        f.tick(ready=int(same_cycle),flush=(branch,self_flush));f.drain();ordinal=0
    pc_roles={str(pc):dict(word=(0x0294050b & ~(31<<7)) | (vd<<7),stage=stage,phase=0,packet=packet,vs1_low64=L,vs2_low64=R) for pc,vd,stage,packet in [(A0,16,'S0','A'),(B0,17,'S0','B'),(A1,16,'S1','A'),(B1,17,'S1','B')]}
    pc_roles[str(A1)]['eligible_commit_ordinal']=ordinal
    order=[A0,B0,A1,B1,A1] if training_only_hit else [A0,B0,A1]
    if s0_b_cancelled:order.remove(B0)
    return f.text(),dict(pc_roles=pc_roles,expected_commits=len(order),expected_retired_pc_sequence=order)

class Delta(unittest.TestCase):
    def reject(self, text, c):
        with self.assertRaises(ValueError):select(text,c)
    def test_positive_exact_pair_wrap_self_and_same_cycle(self):
        for wrap in [False,True]:
            for self_flush in [0,1]:
                for same in [False,True]:
                    t,c=source(wrap,self_flush,same);r=select(t,c)
                    self.assertEqual(r['status'],'SUPPLEMENT_TRACE_HIT')
                    self.assertFalse(r['target_run_qualified'])
                    self.assertEqual(r['custom_commits'],3)
                    w=r['witnesses']['S1'][0]
                    self.assertGreaterEqual(w['survivor_response_cycle'],w['kill_cycle'])
    def test_no_training_only_hit_substitution(self):
        t,c=source(training_only_hit=True)
        self.assertEqual(base.analyze(t)['status'],'SP1_TRACE_PASS')
        self.reject(t,c)
        c['pc_roles'][str(A1)]['eligible_commit_ordinal']=0
        self.assertEqual(select(t,c)['status'],'SUPPLEMENT_TRACE_HIT')
    def test_unknown_pc_wrong_word_inputs_and_call_order(self):
        t,c=source()
        for mutate in [lambda x:x['pc_roles'].pop(str(A0)),lambda x:x['pc_roles'][str(A0)].update(word=0xdeadbeef),lambda x:x['pc_roles'][str(A0)].update(vs1_low64=L^1),lambda x:x.update(expected_commits=4),lambda x:x.update(expected_retired_pc_sequence=[B0,A0,A1])]:
            z=deepcopy(c);mutate(z);self.reject(t,z)
    def test_wrong_pair_phase_and_probe_ordinal(self):
        t,c=source()
        for pc,field,value in [(B0,'phase',1),(B1,'packet','A'),(A1,'eligible_commit_ordinal',1)]:
            z=deepcopy(c);z['pc_roles'][str(pc)][field]=value;self.reject(t,z)
    def test_high128_corruption_and_identity_cancel_mutations(self):
        t,c=source();data=hex(base.dot_result(L,R))
        self.reject(change(t,'SP1_RESPONSE ','data='+data,'data='+hex(base.dot_result(L,R)^(1<<100))),c)
        self.reject(drop(t,'SP1_KILL '),c)
        self.reject(change(t,'SP1_KILL ','slot=P','slot=R'),c)
        self.reject(change(t,'SP1_VFEX4_REDIRECT ','rob=0:11','rob=0:12'),c)
        self.reject(drop(t,'SP1_RESPONSE '),c)
    def test_no_uncommitted_S0_response_credit(self):
        t,c=source(s0_b_cancelled=True)
        self.assertEqual(base.analyze(t)['status'],'SP1_TRACE_PASS')
        self.reject(t,c)
    def test_vtype_vm_vstart_mutation(self):
        t,c=source()
        for bit in [187,178,170]:
            bad=t.replace('vpu='+hex(1<<178),'vpu='+hex((1<<178)^(1<<bit)))
            self.assertEqual(base.analyze(bad)['status'],'SP1_TRACE_PASS')
            self.reject(bad,c)
    def test_no_partial_or_local_scope_and_not_hit_result(self):
        t,c=source();self.reject(t[:-30],c)
        self.reject('\n'.join(x for x in t.splitlines() if not x.startswith(('SP1_ENQUEUE ','SP1_COMMIT ','SP1_REDIRECT ')))+'\n',c)
        z=deepcopy(c);z['pc_roles'][str(B1)]['phase']=1
        self.assertEqual(select(t,z,require_hit=False)['status'],'SUPPLEMENT_TRACE_NOT_HIT')

if __name__=='__main__':unittest.main(verbosity=2)
