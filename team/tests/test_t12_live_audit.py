"""Counter and receipt parser counterexamples; synthetic host fixtures, not DUT."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('t12_live_auditor',Path(__file__).resolve().parents[1]/'scripts/audit_t12_live.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class IndependentAuditTests(unittest.TestCase):
    def test_valid_minimum(self):
        a.check_counter_window(10,20,100,116,16)
    def test_empty_window(self):
        a.check_counter_window(10,20,100,101,0)
    def test_impossible_instret(self):
        with self.assertRaises(ValueError):a.check_counter_window(10,20,100,101,16)
    def test_uint64_boundaries(self):
        a.check_counter_window(a.U64_MAX-1,a.U64_MAX,a.U64_MAX-16,a.U64_MAX,16)
        for bad in (-1,1<<64,True,0.5,'1',None):
            with self.subTest(value=bad),self.assertRaises(ValueError):
                a.check_counter_window(0,bad,0,16,16)
    def test_nonpositive_and_wrapped(self):
        for values in ((20,10,0,20,16),(10,10,0,20,16),(10,20,1,1,0),(10,20,20,10,0)):
            with self.subTest(values=values),self.assertRaises(ValueError):a.check_counter_window(*values)
    def test_duplicate_json_fields(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{"exit_code":1,"exit_code":0}')
            with self.assertRaises(ValueError):a.read_json(p)
    def test_exact_command_option(self):
        self.assertEqual(a.option(['emu','--diff','ref'],'--diff'),'ref')
        for argv in ([],['emu','--diff'],['emu','--diff','a','--diff','b'],['emu','--diff',None]):
            with self.subTest(argv=argv),self.assertRaises(ValueError):a.option(argv,'--diff')
    def test_completed_process(self):
        a.check_recorded_process(dict(exit_code=0,timed_out=False,pid=5,started_at='2026-10-14T12:00:00+00:00',finished_at='2026-10-14T12:00:01+00:00'))
    def test_failed_timeout_and_boolean_exit(self):
        p=dict(exit_code=0,timed_out=False,pid=5,started_at='2026-10-14T12:00:00+00:00',finished_at='2026-10-14T12:00:01+00:00')
        for field,value in [('exit_code',124),('exit_code',False),('timed_out',True),('timed_out',None),('pid',0),('pid',True),('finished_at','2026-10-14T11:00:00+00:00'),('started_at','2026-10-14T12:00:00')]:
            with self.subTest(field=field,value=value),self.assertRaises((ValueError,TypeError)):
                a.check_recorded_process(dict(p,**{field:value}))

if __name__=='__main__':unittest.main()
