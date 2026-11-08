import unittest
from sched_trace import audit
S='SCHED_SCHEMA version=1 cycle=0 module=ROB robsize=48\nSCHED_SCHEMA version=1 cycle=0 module=EXU exu=8\nSCHED_SCHEMA version=1 cycle=0 module=WB3\n'
def u(c,r,first=1,fu=3,d=7):return f'SCHED_UOP cycle={c} slot=0 rob={r} alloc={r} first={first} last=1 uop=0 pc=0x80000100 word=0x123 fu={fu} op=5 pdest={d} psrc=0x12 srcType=0x3 vec=1 v0=0\n'
def inp(c,r,fu=3,d=7):return f'SCHED_EXU_IN cycle={c} exu=8 fu={fu} op=5 rob={r} pdest={d} vec=1 v0=0\n'
def out(c,r,fu=3,d=7,ready=1):return f'SCHED_EXU_OUT cycle={c} exu=8 fu={fu} rob={r} pdest={d} vec=1 v0=0 valid=1 ready={ready} fire={ready}\n'
class Tests(unittest.TestCase):
 def test_split_wait_same_cycle(self):
  t=S+u(1,'0:3')+u(2,'0:3',0,4,9)+inp(3,'0:3')+out(3,'0:3',ready=0)+out(4,'0:3')+inp(4,'0:3',4,9)+out(5,'0:3',4,9)
  self.assertEqual(len(audit(t)['responses']),2)
 def test_cancel_and_reuse(self):
  t=S+u(1,'0:3')+inp(2,'0:3')+'SP1_REDIRECT cycle=3 rob=0:2 self=0\n'+u(4,'0:3')+inp(5,'0:3')+out(6,'0:3')
  self.assertEqual(len(audit(t)['responses']),1)
 def test_identity_negative_controls(self):
  t=S+u(1,'0:3')+inp(2,'0:3')+out(3,'0:3')
  for label,bad in [('orphan',t.replace('first=1','first=0')),('wrongdest',t.replace('SCHED_EXU_OUT cycle=3 exu=8 fu=3 rob=0:3 pdest=7','SCHED_EXU_OUT cycle=3 exu=8 fu=3 rob=0:3 pdest=9')),('duplicate',t+out(4,'0:3')),('missing',S+u(1,'0:3')+inp(2,'0:3')),('wrongexu',t.replace('OUT cycle=3 exu=8','OUT cycle=3 exu=9')),('reset',t+S),('stale',S+u(1,'0:3')+inp(2,'0:3')+'SP1_REDIRECT cycle=3 rob=0:2 self=0\n'+out(4,'0:3'))]:
   with self.subTest(label=label),self.assertRaises(ValueError):audit(bad)
 def test_empty_truncated_and_clock(self):
  for t in ['',S,S+u(2,'0:3')+inp(1,'0:3')+out(3,'0:3')]:
   with self.assertRaises(ValueError):audit(t)
 def test_schema_cancel_and_enable_boundaries(self):
  t=S+u(1,'0:3')+inp(2,'0:3')+out(3,'0:3')
  bads=[t.replace('version=1','version=2'),t.replace('robsize=48','robsize=64'),t.replace('module=EXU exu=8','module=EXU exu=9'),t.replace(out(3,'0:3'),out(3,'0:3').replace('vec=1','vec=0')),t+'SCHED_UNKNOWN cycle=4\n',S+u(1,'0:3')+inp(2,'0:3')+'SP1_REDIRECT cycle=3 rob=0:2 self=0\n'+inp(4,'0:3')+out(5,'0:3'),S+u(1,'0:3')+u(2,'0:3',0)+inp(3,'0:3')+out(4,'0:3')]
  for i,bad in enumerate(bads):
   self.assertNotEqual(bad,t)
   with self.subTest(case=i),self.assertRaises(ValueError):audit(bad)
 def test_padding_wrap_and_unrelated_alias(self):
  t=S+u(1,'1:47')+u(2,'1:47',0,4,9)+u(3,'1:47',0,4,9)+inp(4,'1:47')+out(5,'1:47')
  self.assertEqual(len(audit(t.replace('cycle=','cycle=   ').replace('1:47','1: 47'))['responses']),1)
 def test_wb_all_valid_combinations(self):
  for h in [0,1]:
   for l in [0,1]:
    w=f'SCHED_WB3 cycle=1 hv={h} hr=1 lv={l} lr={int(not h or not l)} hrob=0:3 lrob=0:4 hs={h} hvec=1 ls={l} lvec=1 ov={int(bool(h or l))} od={7 if h else 8} hd=7 ld=8\n'
    audit(S+u(1,'0:3')+u(1,'0:4',fu=16,d=8)+inp(1,'0:3')+out(1,'0:3')+w)
    if l:
     with self.assertRaises(ValueError):audit(S+u(1,'0:3')+inp(1,'0:3')+out(1,'0:3')+w)
    if h:
     with self.assertRaises(ValueError):audit(S+u(1,'0:3')+u(1,'0:4',fu=16,d=8)+inp(1,'0:3')+out(1,'0:3')+w.replace('hvec=1','hvec=0'))
if __name__=='__main__':unittest.main(verbosity=2)
