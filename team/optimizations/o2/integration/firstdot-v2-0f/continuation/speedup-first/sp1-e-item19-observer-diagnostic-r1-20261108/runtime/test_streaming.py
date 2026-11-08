import unittest,io,tempfile,json,importlib.util
from pathlib import Path
import sched_trace as stream
from test_sched import S,u,inp,out
N=Path(__file__).resolve().parent.parent
OLD=N.parent/'sp1-e-item19-observer-impl-20261107/host/sched_trace.py'
spec=importlib.util.spec_from_file_location('frozen_original_sideband',OLD);original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
class Streaming(unittest.TestCase):
 def test_same_semantics(self):
  for t in [S+u(1,'0:3')+inp(2,'0:3')+out(3,'0:3'),S+u(1,'0:3')+inp(2,'0:3')+out(3,'0:3',ready=0)+out(4,'0:3')]:
   self.assertEqual(stream.audit(t)['responses'],original.audit(t)['responses'])
 def test_prefix_abort_does_not_claim_drain(self):
  t=S+u(1,'0:3')+inp(2,'0:3')
  self.assertEqual(stream.audit_stream(io.StringIO(t),require_complete=False)['pending_at_end'],1)
  with self.assertRaisesRegex(ValueError,'incomplete lifecycle'):stream.audit(t)
 def test_response_sink_and_bounds(self):
  result=[];t=S+u(1,'0:3')+inp(2,'0:3')+out(3,'0:3')
  a=stream.audit_stream(io.StringIO(t),response_sink=result.append)
  self.assertEqual(a['responses'],[]);self.assertEqual(a['response_count'],1);self.assertEqual(len(result),1)
  for bad in [t+'SCHED_UNKNOWN cycle=4\n',S+u(1,'0:3')*65,S+'SCHED_UOP '+'x'*4100]:
   with self.assertRaises(ValueError):stream.audit(bad)
if __name__=='__main__':unittest.main(verbosity=2)
