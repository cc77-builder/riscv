"""Pinned NEMU functional cross-check; never a performance measurement.

ABI setup is adapted from the preserved zufan check_t12_lean_reference.py.
This run uses our accepted reference hash, our 10,022 original vectors, and
fresh generated kernels. No upstream PASS record is counted as our execution.
"""
from check import require
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import generate as g

REFERENCE_SHA256 = {'ours': 'efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4', 'jade': 'af5cd64938e0a1056843898a90e2ecaaf09fa457171cefd916aa0efbcf4d457f', 'shishui': '6117e9f5ec76685efabc4e6d3223a1b685f871e965ba86911608b42badcc2268', 'redoop': '4762f99366fee5bab12559f902c722d1b01eb22a2780df5ce09fa2e00d5d0387'}
LAYOUT=dict(size=1400,mode=512,mstatus=520,pc=656,mcause=584,mepc=536,mtvec=568,vr=800,vstart=1312,vl=1344,vtype=1352,vlenb=1360,vxrm=1328,vxsat=1320,vcsr=1336)
TRIPLES=((10,8,9),(8,8,9),(9,8,9),(10,8,8),(8,8,8),(0,0,9),(31,8,31))


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    require(hashlib.sha256(a.reference.read_bytes()).hexdigest() == REFERENCE_SHA256[a.variant], 'reference variant/hash mismatch')
    g.VARIANT=a.variant
    seqs={}
    for d,x,y in TRIPLES:
        seqs[f'generic_{d}_{x}_{y}']=g.rvv(d,x,y,True)
        seqs[f'vdot_{d}_{x}_{y}']=[g.vdot(d,x,y)]
    seqs['known']=g.rvv(10,8,9);seqs['batch']=g.batch();seqs['custom_batch']=g.custom_batch()
    asm=['.option norvc','.text'];blocks={};offset=0
    for name,seq in seqs.items():
        seq=[line.strip() for item in seq for line in item.splitlines()]
        blocks[name]=(offset,len(seq));asm+=[name+':']+seq;offset+=4*len(seq)
    (out/'kernels.S').write_text('\n'.join(asm)+'\n')
    for tool,args in [('as',['-march=rv64gcv','-mabi=lp64d','-o',str(out/'kernels.o'),str(out/'kernels.S')]),('objcopy',['-j','.text','-O','binary',str(out/'kernels.o'),str(out/'kernels.bin')]),('objdump',['-d',str(out/'kernels.o')])]:
        with (out/(tool+'.log')).open('wb') as f:subprocess.run(['riscv64-linux-gnu-'+tool]+args,stdout=f,stderr=subprocess.STDOUT,check=True)
    code=(out/'kernels.bin').read_bytes();require(len(code)==offset, 'reference validation failed: len(code)==offset')
    lib=C.CDLL(str(a.reference.resolve()));require(C.c_uint.in_dll(lib,'DIFFTEST_REG_SIZE').value==1400, "reference validation failed: C.c_uint.in_dll(lib,'DIFFTEST_REG_SIZE').value==1400")
    for name,types in [('difftest_set_ramsize',[C.c_size_t]),('difftest_init_v2',[C.c_uint]),('difftest_regcpy',[C.c_void_p,C.c_bool]),('difftest_memcpy',[C.c_uint64,C.c_void_p,C.c_size_t,C.c_bool]),('difftest_exec',[C.c_uint64])]:
        f=getattr(lib,name);f.argtypes=types;f.restype=None
    lib.difftest_set_ramsize(16*1024*1024);lib.difftest_init_v2(1400)
    def read():
        b=C.create_string_buffer(1400);lib.difftest_regcpy(b,False);return bytearray(b.raw)
    def get(b,k):return struct.unpack_from('<Q',b,LAYOUT[k])[0]
    def put(b,k,v):struct.pack_into('<Q',b,LAYOUT[k],v)
    initial=read();lib.difftest_memcpy(0x80000000,C.create_string_buffer(code),len(code),True)
    counts=dict(generic_vdot_pairs=0,known=0,batch=0)
    def oracle(x,y):
        total=sum(a*b for a,b in zip(struct.unpack('8b',x[:8]),struct.unpack('8b',y[:8])))
        return struct.pack('<I',total & 0xffffffff)+bytes(12)
    def run(name,regs,policy,rounding,sat,want,scratch):
        b=bytearray(initial)
        for r in range(1,32):struct.pack_into('<Q',b,r*8,0x12340000+r)
        offset,n=blocks[name]
        for k,v in dict(pc=0x80000000+offset,mode=3,mstatus=(get(b,'mstatus')&~(3<<9))|0x200,mtvec=0x80040000,mcause=0,mepc=0,vl=8,vtype=policy,vstart=0,vlenb=16,vxrm=rounding,vxsat=sat,vcsr=2*rounding+sat).items():put(b,k,v)
        b[800:1312]=b''.join(regs);lib.difftest_regcpy(C.create_string_buffer(bytes(b)),True)
        # This accepted DiffTest reference intentionally exposes one-step exec.
        for _ in range(n):lib.difftest_exec(1)
        r=read()
        require(get(r,'pc')==0x80000000+offset+4*n and get(r,'mcause')==0, (name,'trap'))
        for i in range(32):
            if i not in scratch:require(r[800+16*i:816+16*i]==want[i], (name,i,'full128'))
        for k in ('vl','vtype','vstart','vxrm','vxsat','vcsr','vlenb'):require(get(r,k)==get(b,k), (name,k))
        require(((get(r,'mstatus')>>9)&3)==3, "reference validation failed: ((get(r,'mstatus')>>9)&3)==3")
        for i in range(32):
            if not (name.startswith('generic') and i in (28,29)):require(r[i*8:i*8+8]==b[i*8:i*8+8], (name,i,'GPR'))
    data=g.ROOT/'team/models/vdot/data'
    vectors=[json.loads(line) for f in ('directed.jsonl','random.jsonl') for line in (data/f).read_text().splitlines()]
    require(len(vectors)==10022, 'reference validation failed: len(vectors)==10022')
    for i,row in enumerate(vectors):
        x=int(row['vs1'],16).to_bytes(16,'little');y=int(row['vs2'],16).to_bytes(16,'little')
        require(oracle(x,y)==int(row['expected_vd'],16).to_bytes(16,'little'), "reference validation failed: oracle(x,y)==int(row['expected_vd'],16).to_bytes(16,'little')")
        base=g.initial(x,y)
        configurations=[(t,p,q,s) for t in TRIPLES for p in (0,) for q in (3,) for s in (1,)] if i<22 else [(TRIPLES[i%7],0,3,1)]
        for (d,xreg,yreg),policy,rounding,sat in configurations:
            regs=list(base);regs[xreg]=x;regs[yreg]=y
            want=list(regs);want[d]=oracle(regs[xreg],regs[yreg])
            run(f'generic_{d}_{xreg}_{yreg}',regs,policy,rounding,sat,want,{2,3})
            run(f'vdot_{d}_{xreg}_{yreg}',regs,policy,rounding,sat,want,{2} if a.variant=='redoop' else set())
            counts['generic_vdot_pairs']+=1
        want=list(base);want[10]=oracle(base[8],base[9]);run('known',base,0,3,1,want,{2,3});counts['known']+=1
        for d in range(10,14):want[d]=oracle(base[8],base[9])
        run('batch',base,0,3,1,want,set(range(16,24)));counts['batch']+=1
        run('custom_batch',base,0,3,1,want,{16,18,20,22} if a.variant=='redoop' else set())
    result=dict(status='PASS_REFERENCE_ONLY',counts=counts,variant=a.variant,reference_sha256=hashlib.sha256(a.reference.read_bytes()).hexdigest(),layout=LAYOUT,code_sha256=hashlib.sha256(code).hexdigest(),input_sha256={f:hashlib.sha256((data/f).read_bytes()).hexdigest() for f in ('directed.jsonl','random.jsonl')},source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),full_core=False,performance=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--variant',choices=tuple(g.MATCH),required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
