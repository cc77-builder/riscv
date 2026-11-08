"""Legacy-image adapter controls. Synthesized SP1 traces are not target evidence."""
from pathlib import Path
import copy,json,unittest
import protection as p
import legacy_adapter as a
from fixtures import Fixture

class LegacyAdapterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cases=json.loads((p.ROOT/'LEGACY_CASES.json').read_text())
 def test_candidate_diagnostic_modes_with_synthetic_protocol(self):
  for case in self.cases[1:]:
   m=json.loads(Path(case['manifest']['path']).read_text());f=Fixture()
   for n in range(m['expected_vdot_commits']):
    rob=f'{(n//48)%2}:{n%48}';f.enqueue(rob,pdest=7,vd=10);f.tick(rob)
   f.drain()
   raw=Path(case['raw_logs']['run.log']['path']).read_text();_,uart=p.o2.extract_events_and_uart(p.failure.normalize_console(raw))
   ref='/home/riscv/riscv-lab/t12-regression-20261013/nemu/reference/build/riscv64-nemu-interpreter-so'
   text=f.text()+uart
   r=a.check(text,m,0,'candidate',case['kind'],ref)
   self.assertEqual(r['observation_status'],'SP1_TRACE_PASS');self.assertFalse(r['performance_2_percent_qualified'])
   for wrong in [text.replace('failures=0','failures=1',1),text.replace('HIT GOOD TRAP','HIT BAD TRAP'),text+'O2_STATE x=1\n']:
    with self.assertRaises(ValueError):a.check(wrong,m,0,'candidate',case['kind'],ref)
   with self.assertRaises(ValueError):a.check(text,m,0,'baseline',case['kind'],ref)
 def test_no_performance_upgrade_from_legacy_history(self):
  for c in self.cases:
   self.assertTrue(c['performance_2percent'].startswith('NOT_QUALIFIED'))
   self.assertEqual(c['candidate_functionality'],'NOT_TESTED')

if __name__=='__main__':unittest.main()
