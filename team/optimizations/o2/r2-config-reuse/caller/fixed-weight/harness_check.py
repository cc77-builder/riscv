"""Check actual C stream wrappers and judge with explicit host-only scalar stubs.

This is a lifecycle/oracle test, not RVV/VDot ISA or timing evidence. The target
main.c has a named, forbidden-in-target-build CSR shim for this test only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import run as e

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)

DRIVER=r'''
#undef main
static unsigned active_d,active_kind,active_mode,active_n,leaf_calls;
static void must(int ok,unsigned line) {
    if(!ok) { fprintf(stderr,"HOST_REJECT line=%u step=%u\n",line,leaf_calls);exit(1); }
}
#define CHECK(x) must((x),__LINE__)
static void scalar_leaf(const int8_t *a,const int8_t *x,struct caller_slot *s,unsigned mode,unsigned kind) {
    CHECK(mode==active_mode && kind==active_kind && leaf_calls<active_n);
    CHECK(s==fixed_slots.value.value+leaf_calls*8);
    CHECK(a==(mode?(int8_t *)fixed_arena.bytes+a_offset:fixed_packed_buffer.value.bytes));
    CHECK(x==(mode?(int8_t *)fixed_arena.bytes+x_offset+32*leaf_calls:fixed_packed_buffer.value.bytes+256));
    for(unsigned i=0;i<256;++i) CHECK(a[i]==fixed_inputs[active_d][i]);
    for(unsigned i=0;i<32;++i) CHECK(x[i]==fixed_inputs[active_d][256+32*leaf_calls+i]);
    int64_t sums[8]={0};
    for(unsigned k=0;k<32;++k) for(unsigned r=0;r<8;++r) sums[r]+=(int64_t)a[r*32+k]*x[k];
    for(unsigned r=0;r<8;++r) {
        CHECK(sums[r]==scalar_golden[active_d][leaf_calls][r]);
        s[r].value=(int32_t)sums[r];
        for(unsigned j=0;j<3;++j)s[r].high[j]=0;
    }
    ++leaf_calls;
}
STUBS
void _putc(char c){(void)c;abort();}
void split_measure(void *c,struct caller_measurement *m,uintptr_t f){(void)c;(void)m;(void)f;abort();}
int main(void) {
    unsigned cases=0,byte_faults=0,csr_faults=0,original_controls=0;
    const unsigned aa[3]={96,97,601},xx[3]={512,513,35};
    prepare_golden();
    for(unsigned d=0;d<7;++d) for(unsigned l=0;l<3;++l) for(unsigned ni=0;ni<2;++ni)
        for(unsigned mode=0;mode<2;++mode) for(unsigned kind=0;kind<6;++kind) {
        unsigned n=ni?4:1;
        initialize(d,kind,n,l);
        CHECK(a_offset==aa[l] && x_offset==xx[l]);
        CHECK(fixed_context.a==(int8_t *)fixed_arena.bytes+aa[l]);
        CHECK(fixed_context.x==(int8_t *)fixed_arena.bytes+xx[l]);
        CHECK(fixed_context.y==fixed_y.value.value && fixed_context.slots==fixed_slots.value.value);
        CHECK(fixed_context.packed==fixed_packed_buffer.value.bytes && fixed_context.count==n);
        CHECK(fixed_context.packed_entry==packed_entries[kind] && fixed_context.split_entry==split_entries[kind]);
        for(unsigned i=0;i<1024;++i) {
            unsigned char want=0xa6;
            if(i>=aa[l] && i<aa[l]+256)want=(unsigned char)fixed_inputs[d][i-aa[l]];
            if(i>=xx[l] && i<xx[l]+128)want=(unsigned char)fixed_inputs[d][256+i-xx[l]];
            CHECK(fixed_arena.bytes[i]==want);
        }
        active_d=d;active_kind=kind;active_mode=mode;active_n=n;leaf_calls=0;
        if(mode)fixed_split(&fixed_context);else fixed_packed(&fixed_context);
        CHECK(leaf_calls==n && judge(d,kind,n,mode)==0);
        if(kind==0) {
            unsigned char *regions[5]={fixed_arena.bytes,(unsigned char *)&fixed_packed_buffer,
                (unsigned char *)&fixed_slots,(unsigned char *)&fixed_y,(unsigned char *)&fixed_context};
            const unsigned sizes[5]={1024,320,544,160,64};
            for(unsigned region=0;region<5;++region)for(unsigned i=0;i<sizes[region];++i) {
                regions[region][i]^=1;CHECK(judge(d,kind,n,mode)!=0);
                regions[region][i]^=1;CHECK(judge(d,kind,n,mode)==0);++byte_faults;
            }
            uint64_t *csr[4]={&host_vl,&host_vt,&host_vs,&host_vc};
            for(unsigned i=0;i<4;++i) {
                *csr[i]^=1;CHECK(judge(d,kind,n,mode)!=0);
                *csr[i]^=1;CHECK(judge(d,kind,n,mode)==0);++csr_faults;
            }
            if(d==0 && l==1 && n==4 && mode==1) {
                original_controls=controls();CHECK(original_controls==8 && judge(d,kind,n,mode)==0);
            }
        }
        memset(&fixed_arena,0x11,sizeof(fixed_arena));
        memset(&fixed_packed_buffer,0x22,sizeof(fixed_packed_buffer));
        memset(&fixed_slots,0x33,sizeof(fixed_slots));
        memset(&fixed_y,0x44,sizeof(fixed_y));
        memset(&fixed_context,0x55,sizeof(fixed_context));
        ++cases;
    }
    printf("FIXED_HOST_PASS cases=%u byte_faults=%u csr_faults=%u controls=%u\n",cases,byte_faults,csr_faults,original_controls);
    return 0;
}
'''

def check(build,out):
    need(not out.exists() and not out.is_relative_to(HERE) and not out.is_relative_to(build),'fresh external output')
    br=json.loads((build/'build.json').read_text());manifest=json.loads((build/'source/manifest.json').read_text())
    valid=e.verification(e.ROOT,build)
    need(br['accepted'] is True and br['exit_code']==0 and br['contract']==e.CONTRACT,'accepted qualified build')
    for n in ('main.c','fixed.c','fixed.h'):
        key='team/optimizations/o2/r2-config-reuse/caller/fixed-weight/'+n
        need(br['software_files'][key]==sha(HERE/n)==sha(build/'source'/n),'actual compiled source: '+n)
    out.mkdir(parents=True)
    inputs=('caller.h','split.h','fixed.h','data.h','main.c','fixed.c')
    for n in inputs:shutil.copyfile(build/'source'/n,out/n)
    stubs=[]
    for row in manifest['rows'][:12]:
        n,kind=row['leaf'],row['algorithm']
        if row['mode']=='packed':stubs.append(f'void {n}(const int8_t *p,void *s){{scalar_leaf(p,p+256,s,0,{kind});}}')
        else:stubs.append(f'void {n}(const int8_t *a,const int8_t *x,struct caller_slot *s){{scalar_leaf(a,x,s,1,{kind});}}')
    prefix='#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#define FIXED_HOST_TEST 1\n#define main fixed_guest_main\n#include "main.c"\n'
    (out/'host.c').write_text(prefix+DRIVER.replace('STUBS','\n'.join(stubs)))
    gcc=shutil.which('gcc');need(gcc is not None,'host GNU gcc')
    flags=['-std=gnu11','-O2','-Wall','-Werror','-Wstrict-aliasing=2','-fstrict-aliasing',
        '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-tree-loop-distribute-patterns']
    result=dict(status='RUNNING',contract=br['contract'],scope='host lifecycle/actual C judge; scalar leaf and CSR shims; no ISA/timing claim',
        checker_sha256=sha(__file__),host_source_sha256=sha(out/'host.c'),inputs={n:sha(out/n) for n in inputs},
        qualified_build_sha256=sha(build/'build.json'),qualified_image_sha256=valid['image_sha256'],
        manifest_sha256=sha(build/'source/manifest.json'),
        compiler=dict(path=gcc,sha256=sha(gcc)),commands=[],new_emu_runs=0)
    def command(label,argv,expected):
        p=subprocess.run(argv,cwd=out,capture_output=True,timeout=60)
        for stream,data in (('stdout',p.stdout),('stderr',p.stderr)):(out/(label+'-'+stream+'.log')).write_bytes(data)
        result['commands'].append(dict(label=label,command=argv,exit_code=p.returncode))
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        need((p.returncode==0)==expected,'unexpected host result: '+label)
        return p
    command('compile',[gcc,*flags,'host.c','fixed.c','-o','harness-check'],True)
    p=command('execute',[str(out/'harness-check')],True)
    need(p.stdout==b'FIXED_HOST_PASS cases=504 byte_faults=177408 csr_faults=336 controls=8\n','complete coverage')
    wrapper=(out/'fixed.c').read_text()
    mutants=[('stale-x','x+step*32','x'),('slot-overwrite','slots+step*8','slots'),
             ('omit-final-step','step<count','step+1<count'),
             ('wrong-step-values','slots[step*8+r].value','slots[r].value')]
    for label,before,after in mutants:
        need(before in wrapper,'mutation location: '+label)
        mutant='mutated-'+label+'.c'
        (out/mutant).write_text(wrapper.replace(before,after))
        command(label+'-compile',[gcc,*flags,'host.c',mutant,'-o',label],True)
        failed=command(label+'-execute',[str(out/label)],False)
        need(b'HOST_REJECT' in failed.stderr,'specific lifecycle rejection: '+label)
    result.update(status='FIXED_C_LIFECYCLE_AND_BYTE_FAULTS_PASS',cases=504,byte_faults=177408,byte_fault_bit=0,
        csr_faults=336,controls=8,lifecycle_mutants=[m[0] for m in mutants],
        fault_scope='84 kind-0 cases, bit0 at each of 2112 bytes; four simulated CSR words; all 504 wrapper cases use scalar stubs',
        artifacts={n:sha(out/n) for n in ('harness-check',*(m[0] for m in mutants),*('mutated-'+m[0]+'.c' for m in mutants))},
        raw_sha256={p.name:sha(p) for p in sorted(out.glob('*.log'))})
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(check(a.build.resolve(),a.output.resolve()),indent=2))
