import unittest,re,tempfile
from pathlib import Path
import adapter,diagnostic,runner
N=Path(__file__).resolve().parent.parent
OLD=N.parent/'sp1-e-o2-cancel-m1-r4-r1-host-20261107/target-01'
def raw(role):return ''.join((OLD/role/name).read_text()for name in ['stdout.log','stderr.log'])
class Diagnostic(unittest.TestCase):
 def test_normal_and_negative_reuse(self):
  self.assertEqual(adapter.collect(raw('01-bit100'),'bit100',1)['status'],'NEW_GUARD_BIT100_LOG_PASS')
  a=adapter.collect(raw('02-candidate-normal'),'candidate-normal',0)
  self.assertEqual(a['custom_commits'],77);self.assertEqual(a['uart_rows'],84);self.assertEqual(a['status'],'SUPPLEMENT_TRACE_NOT_HIT')
 def test_complete128_and_uart_rejection(self):
  t=raw('02-candidate-normal');line=next(x for x in t.splitlines()if x.startswith('SP1_RESPONSE '));m=re.search(r'data=0x([0-9a-f]+)',line);bad=line[:m.start(1)]+format(int(m[1],16)^(1<<100),'032x')+line[m.end(1):]
  with self.assertRaises(ValueError):adapter.collect(t.replace(line,bad,1),'candidate-normal',0)
  with self.assertRaises(ValueError):adapter.collect(t.replace('HIT GOOD TRAP','REMOVED',1),'candidate-normal',0)
  with self.assertRaises(ValueError):adapter.collect(raw('01-bit100'),'bit100',0)
 def test_stream_projection_is_byte_exact(self):
  with tempfile.TemporaryDirectory()as d:
   d=Path(d);t=b'SP1_STATE preserve\r\nSCHED_UOP dropped\nT13_KEEP exact\n';(d/'in').write_bytes(t)
   a=diagnostic.project([d/'in'],d/'out');self.assertEqual((d/'out').read_bytes(),b'SP1_STATE preserve\r\nT13_KEEP exact\n');self.assertEqual(a['sideband_lines'],1)
   with self.assertRaises(ValueError):diagnostic.project([d/'in'],d/'overflow',cap=1)
 def test_role_plan_and_failstop(self):
  seen=[]
  def run(s):seen.append(s['name']);return s
  def check(s,v):raise ValueError('synthetic failure')
  with self.assertRaises(ValueError):runner.schedule(run,check)
  self.assertEqual(seen,['bit100'])
  for role in runner.ROLES:
   argv,env,cwd=runner.plan(role['name']);self.assertIn('--max-cycles='+str(role['guest_cycles']-16),argv);self.assertEqual(('SP1_CHAIN_BIT100'in env),role['name']=='bit100')
if __name__=='__main__':unittest.main(verbosity=2)
