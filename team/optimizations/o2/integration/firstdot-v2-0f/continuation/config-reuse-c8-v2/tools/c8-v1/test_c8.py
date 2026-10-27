import copy,json,struct,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
import c8

class CaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ex=c8.CurrentC()
  cls.tmp=tempfile.TemporaryDirectory(prefix="current-c8-host-")
  cls.root=Path(cls.tmp.name)
  cls.orig=cls.root/"original"
  cls.original=cls.ex.c.generate(c8.SOURCE,cls.orig)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_target_first_and_exact_multiset(self):
  old=self.original["cases"];new=c8.ordered_cases(old)
  self.assertEqual(new[0]["api_symbol"],c8.TARGET);self.assertEqual(new[0]["dataset"],0)
  self.assertTrue(all((c["m"],c["k"])==(8,32) for c in new[:12]))
  self.assertEqual(sorted(map(c8.case_key,old)),sorted(map(c8.case_key,new)))
 def test_missing_case_rejected(self):
  with self.assertRaises(ValueError):c8.ordered_cases(self.original["cases"][:-1])
 def test_duplicate_case_rejected(self):
  cases=copy.deepcopy(self.original["cases"]);cases[-1]=cases[0]
  with self.assertRaises(ValueError):c8.ordered_cases(cases)
 def test_missing_target_dataset_rejected(self):
  cases=copy.deepcopy(self.original["cases"])
  for c in cases:
   if (c["m"],c["k"])==(8,32) and c["dataset"]==2:c["dataset"]=3
  with self.assertRaises(ValueError):c8.ordered_cases(cases)
 def test_target_name_absent_rejected(self):
  cases=copy.deepcopy(self.original["cases"])
  for c in cases:
   if c["api_symbol"]==c8.TARGET:c["api_symbol"]="wrong_target"
  with self.assertRaises(ValueError):c8.ordered_cases(cases)
 def test_generated_only_table_manifest_changed(self):
  out=self.root/"generated";self.ex.generate(c8.SOURCE,out)
  for name in ["gemv.S","gemv.h","main.c","Makefile"]:
   self.assertEqual((out/name).read_bytes(),(self.orig/name).read_bytes())
  m=c8.read(out/"manifest.json")
  for key in self.original:
   if key!="cases":self.assertEqual(m[key],self.original[key])
  self.assertEqual(m["cases"],c8.ordered_cases(self.original["cases"]))
  self.assertEqual((out/"main.c").read_text(),self.ex.app.MAIN)
  self.assertEqual((out/"Makefile").read_text(),self.ex.app.MAKEFILE)
  second=self.root/"generated-again";self.ex.generate(c8.SOURCE,second)
  for name in self.ex.app.FILES:self.assertEqual((out/name).read_bytes(),(second/name).read_bytes())
 def test_corrupt_case_table_rejected(self):
  out=self.root/"corrupt";self.ex.c.generate(c8.SOURCE,out)
  p=out/"cases.h";p.write_text(p.read_text().replace("UINT64_C(4)","UINT64_C(5)",1))
  with self.assertRaises(ValueError):c8.reorder_generated(out)
 def test_real_gnu_build_and_48_anchors(self):
  build=c8.HERE.parent/"c8-preflight-01/host-build-01"
  result,anchor=self.ex.build(build)
  self.assertEqual(result["cases"],48);self.assertEqual(result["public_functions"],16)
  self.assertEqual(anchor["comparisons_count"],48);self.assertEqual(anchor["target_comparisons"],12)
  m=c8.read(build/"source/manifest.json")
  elf=self.ex.c.g.ELF((build/"vdot-perf.elf").read_bytes())
  table=elf.symbol_data("r4_c_cases")
  self.assertEqual(struct.unpack_from("<Q",table)[0],elf.symbols[c8.TARGET][0])
  self.assertEqual(m["cases"][0]["api_symbol"],c8.TARGET)
  first_pc=int(anchor["negative_expected_pc"],16)
  start,size,*_=elf.symbols[c8.TARGET]
  self.assertTrue(start<=first_pc<start+size)
  self.assertEqual(sum(x["dots"] for x in m["cases"][:12]),192)
  c8.save(build/"host-test-check.json",dict(status="CURRENT_C8_GNU_ANCHOR_HOST_PASS",anchor=anchor,
   actual_first_case=c8.TARGET,main_unchanged=True,new_emu_runs=0))
 def test_changed_outer_input_rejected(self):
  f=self.root/"pinned";f.write_text("ok");pins={str(f):c8.sha(f)}
  c8.verify(pins);f.write_text("bad")
  with self.assertRaises(ValueError):c8.verify(pins)
 def test_mixed_outer_identity_rejected(self):
  with self.assertRaises(ValueError):c8.add_files({"x":"a"},{"x":"b"})

class TimingTests(unittest.TestCase):
 def rows(self):
  return [dict(negative=i==0,replay=int(i==2),pid=i+101,current_c_monotonic=dict(
   boot_id="boot",pid=i+101,start_ns=i*20+1,end_ns=i*20+10,scope="popen_wait_bracket")) for i in range(3)]
 def test_serial_proof(self):self.assertTrue(c8.timing_proof(self.rows(),"boot")["serial"])
 def test_missing_record(self):
  with self.assertRaises(ValueError):c8.timing_proof(self.rows()[:2],"boot")
 def test_clock_domain(self):
  rows=self.rows();rows[1]["current_c_monotonic"]["boot_id"]="other"
  with self.assertRaises(ValueError):c8.timing_proof(rows,"boot")
 def test_overlap(self):
  rows=self.rows();rows[1]["current_c_monotonic"]["start_ns"]=2
  with self.assertRaises(ValueError):c8.timing_proof(rows,"boot")
 def test_duplicate_pid(self):
  rows=self.rows();rows[1]["pid"]=101;rows[1]["current_c_monotonic"]["pid"]=101
  with self.assertRaises(ValueError):c8.timing_proof(rows,"boot")
 def test_boolean_time(self):
  rows=self.rows();rows[0]["current_c_monotonic"]["start_ns"]=True
  with self.assertRaises(ValueError):c8.timing_proof(rows,"boot")
 def test_wrong_replay_order(self):
  rows=self.rows();rows[1]["replay"]=1
  with self.assertRaises(ValueError):c8.timing_proof(rows,"boot")

if __name__=="__main__":unittest.main(verbosity=2)
