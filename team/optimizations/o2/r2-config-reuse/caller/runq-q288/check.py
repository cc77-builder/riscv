"""Independent native-C numerical checks and actual-ELF rejection controls."""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
gen=load('runq_check_generator',HERE/'generate.py')
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()

SHIM = r'''
#include "q288.h"
#include <math.h>
void host_leaf(const int8_t *a,const int8_t *x,struct caller_slot *s) {
    for(unsigned r=0;r<8;++r) {
        int32_t total=0;
        for(unsigned k=0;k<32;++k) total+=(int32_t)a[r*32+k]*x[k];
        s[r].value=total;
        for(unsigned j=0;j<3;++j) s[r].high[j]=0;
    }
}
uint32_t host_fma_witness(void) {
    volatile uint32_t raw[4]={0x3d000000,0x3d000000,0x3d000001,0x3cfffffe};
    union { uint32_t u;float f; } a,b,c,d,result;
    a.u=raw[0];b.u=raw[1];c.u=raw[2];d.u=raw[3];
    float first=(-1.0f*a.f)*b.f;
    result.f=fmaf(c.f,d.f,first);
    return result.u;
}
'''

class Context(C.Structure):
    _fields_=[(n,C.c_void_p) for n in ('packed','x','weight_scale','input_scale','y','slots','entry')]
class Pack(C.Structure):
    _fields_=[('weight',C.c_void_p),('packed',C.c_void_p)]

def guarded(n,offset=0):
    block=C.create_string_buffer(n+96)
    base=(C.addressof(block)+15)&~15
    ptr=base+32+offset
    C.memset(ptr-16,0xd1,n+32)
    return block,ptr
def guards(ptr,n):
    return C.string_at(ptr-16,16)==b'\xd1'*16 and C.string_at(ptr+n,16)==b'\xd1'*16

def native(out, wrapper_source=None):
    out.mkdir(parents=True,exist_ok=False)
    for n in ('q288.c','q288.h','oracle.c'):
        source=Path(wrapper_source) if n=='q288.c' and wrapper_source is not None else HERE/n
        shutil.copyfile(source,out/n)
    shutil.copyfile(HERE.parent/'caller.h',out/'caller.h')
    shutil.copyfile(HERE.parent/'split/split.h',out/'split.h')
    (out/'host-shim.c').write_text(SHIM)
    compiler=shutil.which('gcc');need(compiler,'native GNU C compiler')
    cmd=[compiler,'-std=gnu11','-O2','-fPIC','-shared','-ffp-contract=off','-fno-fast-math',
         '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-lto','-fno-ipa-cp','-fno-ipa-icf',
         '-fno-optimize-sibling-calls','-Wall','-Wextra','-Werror','q288.c','oracle.c','host-shim.c','-lm','-o','consumer.so']
    proc=subprocess.run(cmd,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for name,value in (('stdout.log',proc.stdout),('stderr.log',proc.stderr)):(out/name).write_bytes(value)
    (out/'command.json').write_text(json.dumps(dict(command=cmd,cwd=str(out),exit_code=proc.returncode,
        compiler_sha256=sha(Path(compiler).read_bytes())),indent=2))
    need(proc.returncode==0,'actual native C compilation')
    lib=C.CDLL(str(out/'consumer.so'))
    lib.q288_pack.argtypes=[C.POINTER(Pack)];lib.q288_pack.restype=None
    lib.q288_full.argtypes=[C.POINTER(Context)];lib.q288_full.restype=None
    lib.q288_oracle.argtypes=[C.c_void_p]*5;lib.q288_oracle.restype=None
    lib.host_fma_witness.restype=C.c_uint32
    need(lib.host_fma_witness()==0xa3800000,'real fused witness differs from strict +0')
    fixture=gen.fixtures();cases=[]
    primary=[(f'x{d}',fixture['weight'],fixture['inputs'][d],fixture['input_scale'][d],fixture['golden'][d]) for d in (0,1,0,2)]
    extreme=[('min-min',[-128]*82944,[-128]*288,fixture['input_scale'][0],None),
             ('max-max',[127]*82944,[127]*288,fixture['input_scale'][1],None),
             ('min-max',[-128]*82944,[127]*288,fixture['input_scale'][0],None),
             ('zero-weight',[0]*82944,fixture['inputs'][0],fixture['input_scale'][0],None)]
    for index,(name,w,x,xs,golden) in enumerate(primary+extreme):
        # The first four calls genuinely share the same packed W allocation.
        if index==0 or index>=4:
            weight=C.create_string_buffer(gen.bytes8(w)); scales=C.create_string_buffer(gen.bytes32(fixture['weight_scale']))
            hold_p,p=guarded(82944,0)
            lib.q288_pack(C.byref(Pack(C.addressof(weight),p)))
            expected=gen.bytes8([w[(8*t+r)*288+32*g+k] for t in range(36) for g in range(9) for r in range(8) for k in range(32)])
            need(C.string_at(p,82944)==expected and guards(p,82944),'every packed byte and guards')
        input_bytes=C.create_string_buffer(gen.bytes8(x));input_scales=C.create_string_buffer(gen.bytes32(xs))
        hold_y,y=guarded(1152);hold_slots,slots=guarded(128)
        C.memmove(y,struct.pack('<288I',*([0x7fc00bad]*288)),1152);C.memset(slots,0xa6,128)
        ctx=Context(p,C.addressof(input_bytes),C.addressof(scales),C.addressof(input_scales),y,slots,C.cast(lib.host_leaf,C.c_void_p).value)
        before_ctx=bytes(ctx)
        lib.q288_full(C.byref(ctx))
        output=struct.unpack('<288I',C.string_at(y,1152))
        oracle=C.create_string_buffer(1152)
        lib.q288_oracle(C.addressof(oracle),C.addressof(input_bytes),C.addressof(input_scales),C.addressof(weight),C.addressof(scales))
        need(C.string_at(oracle,1152)==C.string_at(y,1152),'native row-major vs packed wrapper bitwise')
        if golden is not None:need(list(output)==golden,'native C vs independently rounded Python golden')
        else:
            want=[]
            for r in range(288):
                acc=0.0
                for g in range(9):
                    integer=sum(w[r*288+32*g+k]*x[32*g+k] for k in range(32))
                    a=gen.f32(float(integer)*gen.from_bits(fixture['weight_scale'][r*9+g]))
                    acc=gen.f32(acc+gen.f32(a*gen.from_bits(xs[g])))
                want.append(gen.bits(acc))
            need(list(output)==want,'extreme signed-int8 arithmetic and strict rounding')
        need(guards(p,82944) and guards(y,1152) and guards(slots,128),'native complete guards')
        need(bytes(ctx)==before_ctx and C.string_at(p,82944)==expected,'context/packed input preserved')
        need(C.string_at(C.addressof(weight),82944)==gen.bytes8(w) and
             C.string_at(C.addressof(scales),10368)==gen.bytes32(fixture['weight_scale']) and
             C.string_at(C.addressof(input_bytes),288)==gen.bytes8(x) and
             C.string_at(C.addressof(input_scales),36)==gen.bytes32(xs),'all original inputs preserved')
        words=struct.unpack('<32I',C.string_at(slots,128))
        need(all(words[4*r+j]==0 for r in range(8) for j in (1,2,3)),'full high 96 bits')
        cases.append(dict(name=name,output_sha256=sha(C.string_at(y,1152)),all_288_bits=True,full_packed_bytes=True))
    result=dict(status='RUNQ_NATIVE_C_ORACLE_PASS',cases=cases,fma_witness=dict(strict=0,fused=0xa3800000),
                library_sha256=sha((out/'consumer.so').read_bytes()),native_leaf='scalar test stub; not an RTL claim')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

def elf_controls(repo,build,out,engine=None):
    run=engine or load('runq_control_engine',HERE/'run.py')
    blob=(build/'vdot-perf.elf').read_bytes();elf=run.g.ELF(blob)
    fixture=gen.fixtures();manifest=json.loads((build/'source/manifest.json').read_text());row=manifest['rows'][0]
    _,detail=run.traced.path(elf,row,fixture)
    body=elf.symbol_data('q288_full');file_offset=blob.find(body)
    need(file_offset>=0 and blob.find(body,file_offset+1)<0,'unique actual wrapper bytes')
    instructions=list(struct.iter_unpack('<I',body));tests=[]
    fcvt=next(i*4 for i,(w,) in enumerate(instructions) if w&127==0x53 and w>>25==0x68)
    mul=next(i*4 for i,(w,) in enumerate(instructions) if w&127==0x53 and w>>25==0x08)
    scale=detail['weight_scale_load_sites'][0]-elf.symbols['q288_full'][0]
    step=next(i*4 for i,(w,) in enumerate(instructions) if w&127==0x13 and (w>>12)&7==0 and (w>>20)==256)
    cases=[('signed-conversion',fcvt,lambda w:w|(1<<20),'signed fcvt.s.w'),
           ('multiply-to-add',mul,lambda w:w&~(0x08<<25),'strict FP operation cardinality'),
           ('wrong-scale-index',scale,lambda w:(w&0x000fffff)|((((w>>20)+4)&4095)<<20),'exact weight scale index'),
           ('wrong-panel-step',step,lambda w:(w&0x000fffff)|(264<<20),'exact tile/group leaf arguments')]
    for name,offset,change,expected in cases:
        original=struct.unpack_from('<I',body,offset)[0];mutated=change(original)
        candidate=bytearray(blob);struct.pack_into('<I',candidate,file_offset+offset,mutated)
        try:run.traced.path(run.g.ELF(bytes(candidate)),row,fixture)
        except ValueError as error:
            need(expected is None or expected in str(error),'specific rejection: '+name)
            tests.append(dict(name=name,offset=file_offset+offset,pc=elf.symbols['q288_full'][0]+offset,
                original_word=hex(original),mutated_word=hex(mutated),mutated_elf_sha256=sha(candidate),error=str(error)))
        else:raise ValueError('mutated ELF accepted: '+name)
    result=dict(status='RUNQ_ACTUAL_ELF_REJECTION_PASS',base_elf_sha256=sha(blob),controls=tests)
    out.mkdir(parents=True,exist_ok=False);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--action',choices=('host','elf'),required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--build',type=Path)
    a=p.parse_args();out=a.output.resolve();need(not out.exists(),'fresh output required')
    result=native(out) if a.action=='host' else elf_controls(HERE.parents[5],a.build.resolve(),out)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
