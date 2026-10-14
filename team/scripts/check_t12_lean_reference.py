"""Pinned reference-only validation of shorter RVV kernels; not full-core evidence.
The 1400-byte ABI is for the recorded NEMU 1.1.0 build, with no lightqs.
"""
import argparse,ctypes as C,hashlib,importlib.util,json,os,struct,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--toolchain',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
refhash=hashlib.sha256(a.reference.read_bytes()).hexdigest();assert refhash=='e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae'
spec=importlib.util.spec_from_file_location('g',Path(__file__).resolve().parents[1]/'tests/generate_t12.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
layout=dict(size=1400,mode=512,mstatus=520,pc=656,mcause=584,mepc=536,mtvec=568,vr=800,vstart=1312,vl=1344,vtype=1352,vlenb=1360,vxrm=1328,vxsat=1320,vcsr=1336)
triples=((10,8,9),(8,8,9),(9,8,9),(10,8,8),(8,8,8),(0,0,9),(31,8,31))
seqs={}
for vd,x,y in triples:
 seqs[f'lean_{vd}_{x}_{y}']=g.general(vd,x,y,lean=True)
 seqs[f'vdot_{vd}_{x}_{y}']=[g.custom(vd,x,y)]
seqs['known']=g.general(known=True,lean=True);seqs['batch']=g.batched(lean=True)
asm=['.option norvc','.text'];blocks={};offset=0
for name,seq in seqs.items():
 blocks[name]=(offset,4*len(seq));asm+=['.globl '+name,name+':']+seq;offset+=4*len(seq)
(out/'kernels.S').write_text('\n'.join(asm)+'\n');env=dict(os.environ,LD_LIBRARY_PATH=str(a.toolchain.resolve()/'usr/lib/x86_64-linux-gnu'));commands=[]
for name,argv in [('as',['as','-march=rv64gcv','-mabi=lp64d','-o',str(out/'kernels.o'),str(out/'kernels.S')]),('objcopy',['objcopy','-j','.text','-O','binary',str(out/'kernels.o'),str(out/'kernels.bin')]),('objdump',['objdump','-d',str(out/'kernels.o')])]:
 argv[0]=str(a.toolchain.resolve()/'usr/bin'/('riscv64-linux-gnu-'+argv[0]));t=time.time()
 with (out/(name+'.log')).open('wb') as f:r=subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60)
 commands.append(dict(argv=argv,exit_code=r.returncode,started_epoch=t,elapsed_seconds=time.time()-t));assert r.returncode==0
(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
code=(out/'kernels.bin').read_bytes();assert len(code)==offset
lib=C.CDLL(str(a.reference.resolve()));assert C.c_uint.in_dll(lib,'DIFFTEST_REG_SIZE').value==layout['size']
for name,types in [('difftest_set_ramsize',[C.c_size_t]),('difftest_init_v2',[C.c_uint]),('difftest_regcpy',[C.c_void_p,C.c_bool]),('difftest_memcpy',[C.c_uint64,C.c_void_p,C.c_size_t,C.c_bool]),('difftest_exec',[C.c_uint64])]:
 f=getattr(lib,name);f.argtypes=types;f.restype=None
lib.difftest_set_ramsize(16*1024*1024);lib.difftest_init_v2(layout['size'])
def read():
 b=C.create_string_buffer(layout['size']);lib.difftest_regcpy(b,False);return bytearray(b.raw)
def get(b,k):return struct.unpack_from('<Q',b,layout[k])[0]
def put(b,k,v):struct.pack_into('<Q',b,layout[k],v)
initial=read();lib.difftest_memcpy(0x80000000,C.create_string_buffer(code),len(code),True)
def run(name,regs,policy,vxrm,vxsat,want,scratch):
 b=bytearray(initial)
 for i in range(1,32):struct.pack_into('<Q',b,8*i,0x12340000+i)
 offset,n=blocks[name]
 for k,v in dict(pc=0x80000000+offset,mode=3,mstatus=(get(b,'mstatus')&~(3<<9))|0x200,mtvec=0x80040000,mcause=0,mepc=0,vl=8,vtype=policy,vstart=0,vlenb=16,vxrm=vxrm,vxsat=vxsat,vcsr=2*vxrm+vxsat).items():put(b,k,v)
 b[800:1312]=b''.join(regs);lib.difftest_regcpy(C.create_string_buffer(bytes(b)),True)
 for i in range(n//4):lib.difftest_exec(1)
 result=read();assert get(result,'pc')==0x80000000+offset+n and get(result,'mcause')==0,(name,'trap')
 for r in range(32):
  if r not in scratch:assert result[800+r*16:816+r*16]==want[r],(name,r,'vector')
 for k in ('vl','vtype','vstart','vxrm','vxsat','vcsr','vlenb'):assert get(result,k)==get(b,k),(name,k)
 assert ((get(result,'mstatus')>>9)&3)==3
 scalar_scratch={28,29} if name.startswith('lean_') else set()
 for r in range(32):
  if r not in scalar_scratch:assert result[8*r:8*r+8]==b[8*r:8*r+8],(name,r,'gpr')
 return result
inputs=[r for r in g.corpus() if r['kind']=='equivalence' and r['method']=='vdot'];counts=dict(dual_general=0,known=0,batch=0)
for row in inputs:
 base=[bytes.fromhex(x) for x in row['before']]
 for vd,x,y in triples:
  regs=list(base);regs[x]=base[8];regs[y]=base[9]
  want=list(regs);want[vd]=g.dot(regs[x],regs[y])
  for policy in (0,64,128,192):
   for vxrm in range(4):
    for vxsat in range(2):
     run(f'lean_{vd}_{x}_{y}',regs,policy,vxrm,vxsat,want,{2,3})
     run(f'vdot_{vd}_{x}_{y}',regs,policy,vxrm,vxsat,want,set());counts['dual_general']+=1
 want=list(base);want[10]=g.dot(base[8],base[9]);run('known',base,0,3,1,want,{2,3});counts['known']+=1
 for vd in range(10,14):want[vd]=g.dot(base[8],base[9])
 run('batch',base,0,3,1,want,set(range(16,24)));counts['batch']+=1
result=dict(status='PASS_REFERENCE_ONLY',counts=counts,baseline='lean',instruction_counts={k:len(v) for k,v in seqs.items()},reference_sha256=refhash,generator_sha256=hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),code_sha256=hashlib.sha256(code).hexdigest(),layout=layout,full_core=False)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
