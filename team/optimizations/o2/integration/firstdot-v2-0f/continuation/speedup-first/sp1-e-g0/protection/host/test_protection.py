"""Synthetic contract controls, explicitly not hardware or NEMU executions."""
from pathlib import Path
import copy,importlib.util,json,struct,tempfile,unittest
import protection as p

def fixture():
 m=p.manifest();audit,kernels=p.static_audit();events={x:[] for x in p.windows.FIELDS};rows=[]
 lines=['SP1E_BEGIN version=1 datasets=3 operators=3 windows=54 vl=2 sew=64','SP1E_GUARD lo=0000000000000010 hi=0000000000000000']
 div=[];seq=0
 for plan in m['plan']:
  n=plan['seq'];base=1000+n*300;case=m['cases'][plan['case']];path=p.windows.walk(kernels[plan['op']]);vals=[10000+n*100,base+39,base+149,10015+n*100]
  ci=0
  for i,(pc,word) in enumerate(path):
   cycle=base+i*10;rob=(n*20+i)%48;flag=((n*20+i)//48)%2;data=case['out'][0] if word==p.OPS[plan['op']] else 0
   if word in p.COUNTERS:
    data=vals[ci];events['COUNTER_ENQUEUE'].append(dict(cycle=cycle-2,flag=flag,rob=rob,pc=pc,word=word,empty=1,wait=1,block=1))
    events['CSR_SAMPLE'].append(dict(cycle=cycle-1,addr=word>>20,data=data,wen=0));ci+=1
   e=dict(cycle=cycle,slot=0,flag=flag,rob=rob,pc=pc,word=word,count=1,data=data);events['RETIRE'].append(e)
   if word==p.OPS[plan['op']]:
    f=dict(cycle=cycle-5,seq=seq,rob=f'{flag}:{rob}',fu=p.VIDIV if plan['op']=='vdivu' else p.VFDIV,pdest=10)
    div.append((cycle-5,0,'DIV_ACCEPT',f));div.append((cycle-1,1,'DIV_OUTPUT',dict(f,cycle=cycle-1,ready=1,cancelled=0)));seq+=1
  row=dict(seq=n,d=plan['dataset'],op=plan['opid'],r=plan['repeat'],c=110,i=15,cb=vals[1],ce=vals[2],ib=vals[0],ie=vals[3],lo=case['out'][0],hi=case['out'][1],vl=2,vt=24,vs=0,vc=7,ff=case['fflags'],mc=0);rows.append(row)
  lines.append('SP1E_WINDOW '+' '.join(k+'='+(f'{v:016x}' if k in ('lo','hi') else str(v)) for k,v in row.items()))
 lines.extend(['SP1E_SUMMARY windows=54 div=288 sqrt=144 full128=54 source128=108 csr=324 failures=0','HIT GOOD TRAP'])
 return '\n'.join(lines)+'\n',events,rows,kernels,div

class ProtectionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.fixture=fixture()
 def test_independent_oracle_and_compiled_full128_contract(self):
  a,k=p.static_audit();self.assertEqual(a['oracle']['lanes'],18);self.assertEqual(a['guard']['pc'],'0x80000540')
 def test_oracle_rejects_upperlane_and_exception_mutations(self):
  for case,key,index in [(0,'out',1),(7,'out',0),(8,'out',0)]:
   m=p.manifest();m['cases'][case][key][index]^=1
   with self.assertRaises(ValueError):p.oracle_cases(m)
  m=p.manifest();m['cases'][7]['fflags']=16
  with self.assertRaises(ValueError):p.oracle_cases(m)
 def test_compiled_wrong_opcode_rejected(self):
  raw=bytearray((p.ROOT/'build-01/protection.elf').read_bytes());i=raw.index(struct.pack('<I',p.OPS['vfsqrt']));raw[i]^=0x80
  with tempfile.TemporaryDirectory(dir=p.ROOT) as td:
   elf=Path(td)/'bad.elf';elf.write_bytes(raw)
   with self.assertRaises(ValueError):p.static_audit(elf)
 def test_generation_determinism(self):
  spec=importlib.util.spec_from_file_location('new_generator',p.ROOT/'software/generate.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
  with tempfile.TemporaryDirectory(dir=p.ROOT) as td:
   g.HERE=Path(td);g.generate()
   for name in ('manifest.json','data.h','kernels.S'):self.assertEqual((Path(td)/name).read_bytes(),(p.ROOT/'software'/name).read_bytes())
 def test_all_54_uart_fullwidth_and_csr_positive(self):
  uart,events,rows,kernels,div=self.fixture;self.assertEqual(p.check_uart(uart,p.manifest()),rows)
 def test_uart_fail_closed_mutations(self):
  uart,*_=self.fixture
  mutants=[uart.replace('hi=000000000000008e','hi=000000100000008e',1),uart.replace(' ff=24 ',' ff=16 ',1),uart.replace(' vt=24 ',' vt=0 ',1),uart.replace(' vc=7 ',' vc=0 ',1),uart.replace(' ff=0 ',' ff=32 ',1),uart.replace(' i=15 ',' i=14 ',1),uart.replace(' mc=0',' mc=1',1),uart.replace('SP1E_WINDOW seq=1 ','SP1E_WINDOW seq=2 ',1),uart.replace('HIT GOOD TRAP','HIT BAD TRAP'),uart+'SP1E_FAIL seq=0 reason=mock\n',uart+'SP1E_GUARD lo=0000000000000010 hi=0000000000000000\n']
  for mutant in mutants:
   self.assertNotEqual(mutant,uart)
   with self.subTest(mutant=mutant[-80:]),self.assertRaises(ValueError):p.check_uart(mutant,p.manifest())
 def test_exact_54_window_csr_retirement_and_div_identity_positive(self):
  uart,events,rows,kernels,div=self.fixture;a=p.check_t13(events,p.manifest(),kernels,rows)
  self.assertEqual(len(a['samples']),54);self.assertEqual(p.bind_div_retirement(div,a['operator_retirements'])['count'],432)
 def test_retirement_and_counter_negatives(self):
  _,orig,rows,kernels,_=self.fixture
  for kind,index,field,value in [('RETIRE',6,'word',p.OPS['vfdiv']),('RETIRE',6,'pc',0),('RETIRE',6,'count',2),('COUNTER_ENQUEUE',0,'rob',47),('CSR_SAMPLE',1,'wen',1),('CSR_SAMPLE',1,'data',1),('CSR_SAMPLE',0,'cycle',1)]:
   e=copy.deepcopy(orig);e[kind][index][field]=value
   with self.subTest(kind=kind,field=field),self.assertRaises(ValueError):p.check_t13(e,p.manifest(),kernels,rows)
  e=copy.deepcopy(orig);e['RETIRE'].pop(6)
  with self.assertRaises(ValueError):p.check_t13(e,p.manifest(),kernels,rows)
 def test_div_retirement_ownership_cancel_missing_output_negatives(self):
  _,e,rows,kernels,div=self.fixture;a=p.check_t13(e,p.manifest(),kernels,rows)
  for index,key,value in [(0,'fu',p.VFDIV),(1,'cancelled',1),(1,'pdest',11),(1,'ready',0)]:
   d=copy.deepcopy(div);d[index][3][key]=value
   with self.assertRaises(ValueError):p.bind_div_retirement(d,a['operator_retirements'])
  with self.assertRaises(ValueError):p.bind_div_retirement(div[1:],a['operator_retirements'])
 def test_performance_2percent_and_exact_replay(self):
  uart,e,rows,kernels,div=self.fixture;a=p.check_t13(e,p.manifest(),kernels,rows);a.pop('operator_retirements')
  base=dict(status='PROTECTION_NORMAL_PASS',rows=rows,t13=a,div_binding={'fixture':True},observation_sha256='synthetic',observation_counts={},elf_sha256='same',bin_sha256='same',manifest_sha256='same',reference='same')
  rs=[dict(copy.deepcopy(base),mode=('candidate' if i%2==0 else 'baseline'),run_id='SYNTHETIC-'+str(i)) for i in range(4)]
  self.assertEqual(p.compare(*rs)['status'],'PROTECTION_PERFORMANCE_PASS')
  rs[0]['rows'][6]['c']=200;rs[2]['rows'][6]['c']=200
  self.assertEqual(p.compare(*rs)['status'],'PROTECTION_PERFORMANCE_NO_GO')
  rs[2]['rows'][6]['c']=201
  with self.assertRaises(ValueError):p.compare(*rs)
 def test_raw_negative_bit100_exact_binding(self):
  from fixtures import basic,change
  f=basic().text();f=change(f,'SP1_ENQUEUE ','pc=0x80000000','pc=0x80000540');f=change(f,'SP1_COMMIT ','pc=0x80000000','pc=0x80000540')
  banner='The reference model is /SYNTHETIC/ref.so\nThe first instruction of core 0 has commited. Difftest enabled.\n'
  tail='DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=10 pc=0x80000540 instruction=0x0294050b\nv10_high different at pc = 0x80000540, right=0x0, wrong =0x1000000000\nCore 0: ABORT at pc = 0x80000000\n'
  text=banner+f+tail;self.assertEqual(p.negative_gate(text,1,'/SYNTHETIC/ref.so')['fault']['bit'],100)
  for mutant in [text.replace('bit=100','bit=99'),text.replace('wrong =0x1000000000','wrong =0x1000000001'),text.replace('/SYNTHETIC/ref.so','/wrong/ref'),text.replace('SP1_COMMIT','SP1_XCOMMIT'),text+'HIT GOOD TRAP\n']:
   with self.assertRaises(ValueError):p.negative_gate(mutant,1,'/SYNTHETIC/ref.so')

 def test_full_candidate_normal_pipeline_synthetic_only(self):
  from fixtures import Fixture,change
  uart,t13,rows,kernels,_=self.fixture
  f=Fixture();f.enqueue();original=f.request
  f.request=lambda rob,illegal=0,vl=8: original(rob,illegal,vl,vs1=0xa5a5a5a5a5a5a5a50101010101010101,vs2=0x5a5a5a5a5a5a5a5a0202020202020202)
  f.tick('0:5');f.drain()
  for e in t13['RETIRE']:
   if e['word'] not in p.OPS.values():continue
   f.cycle=e['cycle']-5
   f.tick(f"{e['flag']}:{e['rob']}",div_fu=p.VIDIV if e['word']==p.OPS['vdivu'] else p.VFDIV)
   for _ in range(3):f.tick()
   f.tick(div_done=True);f.tick()
  trace=change(f.text(),'SP1_ENQUEUE ','pc=0x80000000','pc=0x80000540');trace=change(trace,'SP1_COMMIT ','pc=0x80000000','pc=0x80000540')
  lines=[]
  for kind,events in t13.items():
   for e in events:
    if kind=='RETIRE':line=f"T13_RETIRE cycle={e['cycle']} slot={e['slot']} rob={e['flag']}:{e['rob']} pc=0x{e['pc']:x} word=0x{e['word']:x} count={e['count']} data=0x{e['data']:x}"
    elif kind=='COUNTER_ENQUEUE':line=f"T13_COUNTER_ENQUEUE cycle={e['cycle']} rob={e['flag']}:{e['rob']} pc=0x{e['pc']:x} word=0x{e['word']:x} empty=1 wait=1 block=1"
    else:line=f"T13_CSR_SAMPLE cycle={e['cycle']} addr=0x{e['addr']:x} data=0x{e['data']:x} wen=0"
    lines.append((e['cycle'],line))
  banner='The reference model is /SYNTHETIC/ref.so\nThe first instruction of core 0 has commited. Difftest enabled.\n'
  text=banner+trace+'\n'.join(line for _,line in sorted(lines))+'\n'+uart
  a=p.normal_gate(text,0,'/SYNTHETIC/ref.so','candidate');self.assertEqual(a['div_binding']['count'],432)
  for bad in [text+'O2_STATE x=1\n',text.replace('Difftest enabled.','Difftest disabled.'),text.replace('SP1_DIV_OUTPUT','SP1_MISSING_DIV_OUTPUT',1),text.replace('word=0x4e801557','word=0x82849557',1),text.replace('ff=24','ff=0',1)]:
   with self.assertRaises(ValueError):p.normal_gate(bad,0,'/SYNTHETIC/ref.so','candidate')

if __name__=='__main__':unittest.main()
