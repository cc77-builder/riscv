"""Host-only bit-0 fault at every byte of the actual v2 C buffers.

Three RISC-V assembly statements are replaced explicitly in a temporary C copy.
No leaf or timer executes here. This checks the changed C harness, not the ISA,
cycle counts, or the real CSR implementation; those require the full campaign.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)

DRIVER=r'''
#undef main
static void must(int ok,unsigned line) {
    if(!ok) { fprintf(stderr,"HARNESS_REJECT line=%u\n",line); exit(1); }
}
#define CHECK(x) must((x),__LINE__)
int main(void) {
    unsigned cases=0,byte_faults=0,csr_faults=0,original_controls=0;
    const unsigned aa[3]={96,97,39},xx[3]={32,35,427};
    for(unsigned d=0;d<7;++d) for(unsigned r=0;r<8;++r) scalar_golden[d][r]=expected(d,r);
    for(unsigned d=0;d<7;++d) for(unsigned l=0;l<3;++l) for(unsigned mode=0;mode<2;++mode) {
        initialize(d,mode?6:0,l);
        CHECK(a_offset==aa[l] && x_offset==xx[l]);
        CHECK(caller_context.a==(int8_t *)split_arena.bytes+aa[l] && caller_context.x==(int8_t *)split_arena.bytes+xx[l]);
        CHECK(caller_context.workspace==&caller_workspace.value && split_context.slots==caller_workspace.value.slots);
        CHECK(split_context.a==caller_context.a && split_context.x==caller_context.x);
        CHECK(caller_context.y==caller_y.value && split_context.y==caller_y.value);
        CHECK(caller_context.entry==packed_entries[0] && split_context.entry==split_entries[0]);
        for(unsigned i=0;i<768;++i) {
            unsigned char want=0xa6;
            if(i>=aa[l] && i<aa[l]+256) want=(unsigned char)split_inputs[d][i-aa[l]];
            if(i>=xx[l] && i<xx[l]+32) want=(unsigned char)split_inputs[d][256+i-xx[l]];
            CHECK(split_arena.bytes[i]==want);
        }
        for(unsigned i=0;i<464;++i) {
            unsigned char want=0xa6;
            if(i<16 || (i>=304 && i<320) || i>=448) want=((const unsigned char *)&guard)[i%8];
            CHECK(((unsigned char *)&caller_workspace)[i]==want);
        }
        for(unsigned i=0;i<64;++i) {
            unsigned char want=(i<16 || i>=48)?((const unsigned char *)&guard)[i%8]:0xa6;
            CHECK(((unsigned char *)&caller_y)[i]==want);
        }
        /* Populate a correct result independently; no candidate implementation
         * is run or substituted for a claimed ISA/functional result. */
        for(unsigned r=0;r<8;++r) {
            int64_t sum=0;
            for(unsigned k=0;k<32;++k) sum+=(int64_t)split_inputs[d][r*32+k]*(int64_t)split_inputs[d][256+k];
            CHECK(scalar_golden[d][r]==sum);
            caller_y.value[r]=caller_workspace.value.slots[r].value=(int32_t)sum;
            for(unsigned k=0;k<3;++k) caller_workspace.value.slots[r].high[k]=0;
        }
        if(!mode) for(unsigned i=0;i<288;++i) caller_workspace.value.packed[i]=split_inputs[d][i];
        CHECK(judge(d,mode)==0);
        unsigned char *regions[3]={split_arena.bytes,(unsigned char *)&caller_workspace,(unsigned char *)&caller_y};
        const unsigned sizes[3]={768,464,64};
        for(unsigned region=0;region<3;++region) for(unsigned i=0;i<sizes[region];++i) {
            regions[region][i]^=1; CHECK(judge(d,mode)!=0);
            regions[region][i]^=1; CHECK(judge(d,mode)==0); ++byte_faults;
        }
        for(unsigned i=0;i<4;++i) {
            host_csr[i]^=1; CHECK(judge(d,mode)!=0);
            host_csr[i]^=1; CHECK(judge(d,mode)==0); ++csr_faults;
        }
        if(d==0 && l==1 && mode==1) { original_controls=controls(); CHECK(original_controls==6 && judge(d,mode)==0); }
        /* The next initialize must restore the real buffers even on a cache
         * hit for the same dataset/layout. References are never corrupted. */
        memset(&split_arena,0x11,sizeof(split_arena));
        memset(&caller_workspace,0x22,sizeof(caller_workspace));
        memset(&caller_y,0x33,sizeof(caller_y));
        ++cases;
    }
    printf("HARNESS_BYTES_PASS cases=%u byte_faults=%u csr_faults=%u controls=%u\n",cases,byte_faults,csr_faults,original_controls);
    return 0;
}
'''

def check(build,out):
    need(not out.exists() and not out.is_relative_to(HERE) and not out.is_relative_to(build),'fresh external output')
    br=json.loads((build/'build.json').read_text())
    main=HERE/'main.c';key='team/optimizations/o2/r2-config-reuse/caller/split/main.c'
    need(br['software_files'][key]==sha(main)==sha(build/'source/main.c'),'actual compiled harness source')
    out.mkdir(parents=True)
    for name in ('caller.h','split.h','data.h'):shutil.copyfile(build/'source'/name,out/name)
    source=main.read_text()
    edits=[
        ('__asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x600):"memory");','(void)0;'),
        ('__asm__ volatile("csrwi vstart,0; csrwi vcsr,7; vsetivli zero,8,e8,m1,tu,mu":::"memory");',
         'host_csr[0]=8; host_csr[1]=0; host_csr[2]=0; host_csr[3]=7;'),
        ('__asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr"\n        :"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));',
         'vl=host_csr[0]; vt=host_csr[1]; vs=host_csr[2]; vc=host_csr[3];'),
    ]
    for before,after in edits:
        need(source.count(before)==1,'unique ISA substitution');source=source.replace(before,after)
    need('__asm__' not in source,'unmapped assembly')
    prefix='#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\nstatic uint64_t host_csr[4];\n#define main split_guest_main\n'
    data=(out/'data.h').read_text();header=(out/'split.h').read_text()
    old=re.findall(r'extern void (\w+)\(const int8_t \*, void \*\);',data)
    new=re.findall(r'void (split_gemv_8x32_\w+)\(const int8_t \*, const int8_t \*, struct caller_slot \*\);',header)
    need(len(old)==len(new)==6,'six stub identities')
    stubs=['void '+n+'(const int8_t *a,void *b){(void)a;(void)b;abort();}' for n in old]
    stubs+=['void '+n+'(const int8_t *a,const int8_t *x,struct caller_slot *s){(void)a;(void)x;(void)s;abort();}' for n in new]
    stubs+=['void _putc(char c){(void)c;abort();}',
        'void split_measure(void *c,struct caller_measurement *m,uintptr_t f){(void)c;(void)m;(void)f;abort();}',
        'void caller_full(struct caller_context *c){(void)c;abort();}',
        'void split_full(struct split_context *c){(void)c;abort();}']
    (out/'host.c').write_text(prefix+source+'\n'+'\n'.join(stubs)+'\n'+DRIVER)
    gcc=shutil.which('gcc');need(gcc is not None,'host GNU gcc required')
    argv=[gcc,'-std=gnu11','-O2','-Wall','-Werror','-Wstrict-aliasing=2','-fstrict-aliasing',
          '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-tree-loop-distribute-patterns','host.c','-o','harness-check']
    result=dict(contract=br['contract'],scope='host C harness only; three ISA statements replaced; no leaf/timer execution',
        source_sha256=sha(main),checker_sha256=sha(__file__),host_source_sha256=sha(out/'host.c'),
        inputs={n:sha(out/n) for n in ('caller.h','split.h','data.h')},command=argv,compiler_sha256=sha(gcc),new_emu_runs=0)
    for label,cmd in [('compile',argv),('execute',[str(out/'harness-check')])]:
        proc=subprocess.run(cmd,cwd=out,capture_output=True,timeout=60)
        for name,value in [('stdout',proc.stdout),('stderr',proc.stderr)]: (out/(label+'-'+name+'.log')).write_bytes(value)
        result[label]=dict(exit_code=proc.returncode,command=cmd)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        need(proc.returncode==0,'host '+label+' failed')
    need((out/'execute-stdout.log').read_text()=='HARNESS_BYTES_PASS cases=42 byte_faults=54432 csr_faults=168 controls=6\n','complete byte fault coverage')
    result.update(status='SPLIT_C_HARNESS_BYTE_FAULTS_PASS',cases=42,byte_faults=54432,byte_fault_bit=0,
        cache_hit_reset_cases=21,csr_faults=168,controls=6,
        compiler_version=subprocess.check_output([gcc,'--version'],text=True).splitlines()[0])
    result['raw_sha256']={p.name:sha(p) for p in sorted(out.glob('*.log'))}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(check(a.build.resolve(),a.output.resolve()),indent=2))
