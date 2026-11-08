from pathlib import Path
import unittest,json,tempfile,subprocess,sys,importlib.util,copy,struct
import adapter,runner
from fixtures_local import normal,negative
N=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('m4_object',N/'build-review/audit.py');obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
M=json.loads((N/'software/manifest.json').read_text())
class M4(unittest.TestCase):
 def test_actual_manifest_PC_binding(self):
  adapter.validate_pc_binding(adapter.PC,adapter.M)
  for field in ['pc_roles','expected_retired_pc_sequence','call_plan','software_manifest']:
   bad=copy.deepcopy(adapter.PC);bad[field]={} if isinstance(bad[field],dict)else []
   with self.assertRaises(ValueError):adapter.validate_pc_binding(bad,adapter.M)

 def test_regeneration_and_unchanged_numeric_ABI(self):
  with tempfile.TemporaryDirectory()as d:
   d=Path(d);(d/'generate.py').write_bytes((N/'software/generate.py').read_bytes())
   a=subprocess.run([sys.executable,'-B',str(d/'generate.py')],capture_output=True,timeout=30);self.assertEqual(a.returncode,0)
   for name in ['kernels.S','data.c','cases.h','manifest.source.json']:self.assertEqual((d/name).read_bytes(),(N/'software'/name).read_bytes())
  reuse=json.loads((N/'host/REUSE.json').read_text());self.assertTrue(all(r['equal']for r in reuse['unchanged_software']))
  self.assertEqual([M['expected_calls'],M['expected_custom_commits'],M['expected_f2v_arch_instructions']],[41,77,320])
  self.assertEqual(struct.unpack('<I',struct.pack('<f',(7.0/2)*2*2*2*2))[0],0x42600000)
  self.assertEqual(M['expected_dot128'],'ecfdffff000000000000000000000000')
 def test_actual_delay_dependency_and_abi_negatives(self):
  b=N/'build-review/attempt-01';symbols={l.split()[-1]:int(l.split()[0],16)for l in (b/'o2-cancel.elf.nm.stdout').read_text().splitlines()if len(l.split())>=3};ins=obj.parse_disassembly((b/'o2-cancel.elf.objdump.stdout').read_text())
  for f in M['functions']:
   if f['stage']=='prelude':continue
   text=[ins[pc]['mnemonic']+' '+ins[pc]['operands'].split('#')[0].strip()for pc in range(f['start_pc'],f['end_pc'],4)]
   obj.audit_m1_sequence(text,f,symbols,ins)
   for token,replacement in [('fmul.s ft3,ft0,ft2,rne','fmul.s ft3,ft1,ft2,rne'),('fsgnj.s ft3,ft3,ft3','fsgnj.s ft3,ft0,ft0'),('vfmv.v.f v24,ft3','vfmv.v.f v24,ft0'),('vadd.vx v8,v8,t6','vadd.vx v8,v8,t3')]:
    bad=list(text);idx=text.index(token);bad[idx]=replacement
    with self.assertRaises(ValueError):obj.audit_m1_sequence(bad,f,symbols,ins)
   for idx in [i for i,x in enumerate(text)if x=='fmul.s ft3,ft3,ft2,rne']:
    bad=list(text);bad[idx]='fmul.s ft3,ft0,ft2,rne'
    with self.assertRaises(ValueError):obj.audit_m1_sequence(bad,f,symbols,ins)
   self.assertEqual(text.count('fmul.s ft3,ft3,ft2,rne'),3)
   words=[ins[pc]['word']for pc in range(f['start_pc'],f['end_pc'],4)];idx=text.index('fmul.s ft3,ft0,ft2,rne');bad=list(words);bad[idx]=(bad[idx]&~(31<<7))|(8<<7)
   with self.assertRaises(ValueError):obj.audit_kernel_words(bad)
 def test_exact_new_guard_and_complete_pair_fixture(self):
  self.assertEqual(adapter.collect(negative(2,2),'bit100',1)['status'],'NEW_GUARD_BIT100_LOG_PASS')
  a=adapter.collect(normal(),'candidate-normal',0);self.assertEqual(a['status'],'SUPPLEMENT_TRACE_HIT');self.assertTrue(a['witnesses']['S0']);self.assertTrue(a['witnesses']['S1'])
  t=negative();self.assertIn('bit=100 vd=0',t)
  with self.assertRaises(ValueError):adapter.collect(t.replace('bit=100 vd=0','bit=99 vd=0',1),'bit100',1)
 def test_no_false_hit_or_missing_calls(self):
  t=normal()
  with self.assertRaises(ValueError):adapter.collect(t.replace('OC19_PASS seq=40','OC19_PASS seq=39',1),'candidate-normal',0)
  seen=[]
  def run(s):seen.append(s['name']);return None
  def check(s,v):raise ValueError('test-stop')
  with self.assertRaises(ValueError):runner.schedule(run,check)
  self.assertEqual(seen,['bit100'])
if __name__=='__main__':unittest.main(verbosity=2)
