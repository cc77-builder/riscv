#!/usr/bin/env python3
"""Execute actual pinned NEMU instructions via its checked public reference ABI.
This is NEMU reference-level validation, not RTL/NEMU DiffTest.
"""
import ctypes as C, hashlib, json, pathlib, struct, subprocess, sys, time
from datetime import datetime
base=pathlib.Path('/home/lizufan/xiangshan-t10-t11-supervisor-20261013')
job=base/'runs/closure-tval-fix'; repo=base/'closure-tval-repo'; ref=base/'nemu-xs-tval/reference'
layout=json.loads((base/'runs/reference-api-probe/layout.json').read_text())
so=ref/'build/riscv64-nemu-interpreter-so'
subprocess.run([sys.executable,'-B',str(repo/'team/scripts/artifact_guard.py'),'nemu-runtime','--repo',str(ref),'--binary',str(so),'--mode','reference'],check=True,stdout=(job/'provenance-before.json').open('w'))
assert not layout['lightqs'] and layout['vector_bytes']==512
lib=C.CDLL(str(so))
assert C.c_uint.in_dll(lib,'DIFFTEST_REG_SIZE').value==layout['size']
lib.difftest_set_ramsize.argtypes=[C.c_size_t]; lib.difftest_set_ramsize.restype=None
lib.difftest_init_v2.argtypes=[C.c_uint]; lib.difftest_init_v2.restype=None
lib.difftest_regcpy.argtypes=[C.c_void_p,C.c_bool]; lib.difftest_regcpy.restype=None
lib.difftest_memcpy.argtypes=[C.c_uint64,C.c_void_p,C.c_size_t,C.c_bool]; lib.difftest_memcpy.restype=None
lib.difftest_exec.argtypes=[C.c_uint64]; lib.difftest_exec.restype=None
lib.difftest_set_ramsize(128*1024*1024); lib.difftest_init_v2(layout['size'])
lib.difftest_csrcpy.argtypes=[C.c_void_p,C.c_bool];lib.difftest_csrcpy.restype=None
csrs=(C.c_uint64*4096)();lib.difftest_csrcpy(csrs,False)
assert csrs[0x744]&8, 'reference NMIE reset must match pinned XS'
assert not (csrs[0x300]&(1<<42)), 'reference MDT reset must match pinned XS'
print('TARGET_RESET_MATCH NMIE=1 MDT=0',flush=True)
def read():
 b=C.create_string_buffer(layout['size']); lib.difftest_regcpy(b,False); return bytearray(b.raw)
def put(b):
 buf=C.create_string_buffer(bytes(b)); lib.difftest_regcpy(buf,True)
def get(b,key): return struct.unpack_from('<Q',b,layout[key])[0]
def setv(b,key,value): struct.pack_into('<Q',b,layout[key],value)
def vset(b,reg,value):
 o=layout['vr']+16*reg; b[o:o+16]=value.to_bytes(16,'little')
def vget(b,reg): return int.from_bytes(b[layout['vr']+16*reg:layout['vr']+16*(reg+1)],'little')
initial=read(); started=datetime.now().astimezone().isoformat(); index=0; legal=0; illegal=0
fields=['vstart','vl','vtype','vlenb','vxrm','vxsat','vcsr']
def execute(name,a,b,expected,vd,vs1,vs2,policy=0,bad=None,wordxor=0):
 global index,legal,illegal
 state=bytearray(initial); pc=0x80000000+index*8; index+=1
 setv(state,'pc',pc); setv(state,'mode',3); setv(state,'mstatus',(get(state,'mstatus')&~(3<<9))|(1<<9))
 setv(state,'mcause',0); setv(state,'mepc',0); setv(state,'mtvec',0x80040000)
 for k,v in {'vl':8,'vtype':policy,'vstart':0,'vlenb':16,'vxrm':3,'vxsat':1,'vcsr':7}.items():setv(state,k,v)
 for n in range(32):vset(state,n,((1<<128)-1) ^ (n*0x01010101010101010101010101010101))
 vset(state,vs1,a); vset(state,vs2,b)
 if vs1==vs2:
  vals=[((b>>(8*i))&255) for i in range(8)]; vals=[v-256 if v&128 else v for v in vals]
  expected=sum(v*v for v in vals)&0xffffffff
 if bad:
  for k,v in bad.items():setv(state,k,v)
 word=(0x0200000b|(vs2<<20)|(vs1<<15)|(vd<<7))^wordxor
 code=C.create_string_buffer(struct.pack('<I',word)); lib.difftest_memcpy(pc,code,4,True)
 put(state); before=read(); lib.difftest_exec(1); after=read()
 reject=bool(bad or wordxor)
 try:
  if reject:
   lib.difftest_csrcpy(csrs,False)
   # The only non-decode illegal condition of this profile is runtime VL.
   enable=((get(before,'mstatus')>>9)&3)!=0
   only_vl=enable and get(before,'vtype') in (0,64,128,192) and get(before,'vstart')==0 and get(before,'vl')!=8 and not wordxor
   expected_tval=0 if only_vl else word
   assert csrs[0x343]==expected_tval, ('mtval',hex(csrs[0x343]),hex(expected_tval))
   assert get(after,'mcause')==2 and get(after,'mepc')==pc, ('trap',get(after,'mcause'),get(after,'mepc'))
   assert after[layout['vr']:layout['vr']+512]==before[layout['vr']:layout['vr']+512], 'partial vector write'
   assert all(get(after,k)==get(before,k) for k in fields), 'illegal vector CSR side effect'
   illegal+=1
  else:
   assert get(after,'pc')==pc+4, ('pc',hex(get(after,'pc')))
   assert vget(after,vd)==expected, ('full128',hex(vget(after,vd)),hex(expected))
   assert all(vget(after,n)==vget(before,n) for n in range(32) if n!=vd), 'non-destination changed'
   assert after[:256]==before[:256], 'integer RF changed'
   assert all(get(after,k)==get(before,k) for k in fields), 'vector CSR side effect'
   assert (get(after,'mstatus')>>9)&3==3, 'VS not dirty'
   legal+=1
 except AssertionError as err:
  (job/'first-failure.json').write_text(json.dumps({'name':name,'index':index,'pc':hex(pc),'word':hex(word),'vd':vd,'vs1':vs1,'vs2':vs2,'a':hex(a),'b':hex(b),'expected':hex(expected),'actual':hex(vget(after,vd)),'error':str(err)},indent=2)+'\n')
  raise
for filename in ('directed.jsonl','random.jsonl'):
 rows=[json.loads(x) for x in (repo/'team/models/vdot/data'/filename).read_text().splitlines() if x]
 for i,row in enumerate(rows):
  execute(row['id'],int(row['vs1'],16),int(row['vs2'],16),int(row['expected_vd'],16),i%32,9,8,(i%4)<<6)
assert legal==10022
for n in range(32):
 execute('all-equal-'+str(n),0x8080808080808080,0x8080808080808080,131072,n,n,n,(n%4)<<6)
for name,bad in [('vl9',{'vl':9}),('e16',{'vtype':8}),('m2',{'vtype':1}),('vstart1',{'vstart':1}),('vill-vl0',{'vtype':1<<63,'vl':0}),('VS-Off',{'mstatus':get(initial,'mstatus')&~(3<<9)})]:
 execute(name,0x0101010101010101,0x0202020202020202,16,10,9,8,bad=bad)
for bit in range(32):
 if (0xfe00707f>>bit)&1:
  # Only neighboring custom-0 funct/vm patterns must be illegal here; opcode bit changes may map to other legal ISA instructions.
  if bit>=12:execute('fixed-neighbor-'+str(bit),1,1,1,10,9,8,wordxor=1<<bit)
for name,bad in [('vl9-and-vstart',{'vl':9,'vstart':1}),('vl9-and-sew',{'vl':9,'vtype':8}),('vl9-and-vsOff',{'vl':9,'mstatus':get(initial,'mstatus')&~(3<<9)}),('vl1',{'vl':1}),('vl7',{'vl':7}),('vl16',{'vl':16})]:
 execute(name,1,1,1,10,9,8,bad=bad)
assert legal==10054 and illegal==22
subprocess.run([sys.executable,'-B',str(repo/'team/scripts/artifact_guard.py'),'nemu-runtime','--repo',str(ref),'--binary',str(so),'--mode','reference'],check=True,stdout=(job/'provenance-after.json').open('w'))
report={'status':'PASS','scope':'real NEMU reference API execution; NOT full-core DiffTest','started_at':started,'finished_at':datetime.now().astimezone().isoformat(),'legal':legal,'illegal':illegal,'source':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'nemu_binary_sha256':hashlib.sha256(so.read_bytes()).hexdigest(),'abi':layout,'golden_files':{f:hashlib.sha256((repo/'team/models/vdot/data'/f).read_bytes()).hexdigest() for f in ('directed.jsonl','random.jsonl')},'config_state_method':'public regcpy state injection; does not prove program-level CSR reachability/order'}
(job/'result.json').write_text(json.dumps(report,indent=2)+'\n'); print('NEMU_REFERENCE_EXECUTION_PASS '+json.dumps(report),flush=True)
