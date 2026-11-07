#!/usr/bin/env python3
"""Exact eight-word state comparison prototype, outside the forward window.

Derivation never changes an old input. The finite host screen checks the old and
new C bodies, guarded logical ends and first-byte rejection. It is not EMU/PPA.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

CONTRACT = 'r3-first-forward-compare-batch8-prototype-v1'
MAIN_SHA = '339f00055b30cd1b033f10617a43eb55a0c5006e0e78c58c726a7620167ec116'
BODY_SHA = '15b26a473323dcb6c53887fbcaebfa535da067c25f9804998cc2f2ecb5a51e10'
STATE_BYTES = 3691424
ORIGINAL = '''static void complete_compare(void) {
    _Static_assert(R2_CONSUMER_STATE_BYTES%8==0,"complete word comparison");
    const alias_word *actual=(const alias_word*)&target_state,*gold=(const alias_word*)fixture_gold;
    for(unsigned i=0;i<R2_CONSUMER_STATE_BYTES/8;++i)if(actual[i]!=gold[i]) {
        const unsigned char *a=(const unsigned char*)&target_state;
        for(unsigned j=i*8;j<i*8+8;++j)if(a[j]!=fixture_gold[j])reject(94,j);
        reject(95,i*8);
    }
    target_report[8]=R2_CONSUMER_STATE_BYTES;
}
'''


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def candidate():
    need(sha(ORIGINAL.encode()) == BODY_SHA, 'exact original comparator body')
    old = '    for(unsigned i=0;i<R2_CONSUMER_STATE_BYTES/8;++i)if(actual[i]!=gold[i]) {'
    new = '''    const unsigned words=R2_CONSUMER_STATE_BYTES/8;
    unsigned i=0,suspect=words;
    for(;i+8<=words;i+=8) {
        alias_word difference=(actual[i]^gold[i])|(actual[i+1]^gold[i+1])|
            (actual[i+2]^gold[i+2])|(actual[i+3]^gold[i+3])|
            (actual[i+4]^gold[i+4])|(actual[i+5]^gold[i+5])|
            (actual[i+6]^gold[i+6])|(actual[i+7]^gold[i+7]);
        if(difference) {suspect=i;break;}
    }
    for(;i<words;++i)if(actual[i]!=gold[i]) {'''
    result=ORIGINAL.replace(old,new)
    marker='    target_report[8]=R2_CONSUMER_STATE_BYTES;'
    guard='    if(suspect!=words)reject(95,suspect*8);\n'
    result=result.replace(marker,guard+marker)
    need(result.replace(guard,'',1).replace(new,old,1)==ORIGINAL,'exact inverse body')
    return result


def derive(a):
    raw=a.input.read_bytes()
    need(sha(raw)==MAIN_SHA and raw.count(ORIGINAL.encode())==1,'fixed actual main input')
    new=candidate().encode()
    changed=raw.replace(ORIGINAL.encode(),new,1)
    need(changed.replace(new,ORIGINAL.encode(),1)==raw,'entire main byte inverse')
    need(a.output.is_absolute() and not a.output.exists(),'fresh absolute output')
    a.output.mkdir(parents=True)
    (a.output/'main.c').write_bytes(changed)
    (a.output/'original-compare.c').write_bytes(ORIGINAL.encode())
    (a.output/'candidate-compare.c').write_bytes(new)
    report=dict(contract=CONTRACT,status='SOURCE_DERIVED_UNBUILT',
        original_main_sha256=sha(raw),main_sha256=sha(changed),
        original_body_sha256=BODY_SHA,candidate_body_sha256=sha(new),
        source_inverse_byte_exact=True,only_complete_compare_changed=True,
        state_bytes=STATE_BYTES,full_batches=STATE_BYTES//64,tail_bytes=STATE_BYTES%64,
        first_difference_code=94,internal_inconsistency_code=95,
        inconsistency_without_scalar_difference_location='first suspect batch start',
        application_window_change=False,application_performance_qualified=False,
        target_runtime_qualified=False,new_emu_runs=0,
        generator_sha256=sha(Path(__file__).read_bytes()))
    (a.output/'derivation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


HEADER = r'''#define _GNU_SOURCE
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <setjmp.h>
#include <sys/mman.h>
#include <unistd.h>
typedef uint64_t alias_word __attribute__((may_alias));
static unsigned char *actual_base,*fixture_gold;
#define target_state (*actual_base)
static volatile uint64_t target_report[64];
static volatile unsigned trap_code,trap_byte;
static jmp_buf trap;
__attribute__((noreturn,noinline,noclone)) static void reject(unsigned c,unsigned b) {
    trap_code=c;trap_byte=b;longjmp(trap,1);
}
'''

TEST = r'''
static unsigned long cases;
struct region {void *mapping;size_t bytes;unsigned char *data;};
static struct region guarded(unsigned n) {
    size_t page=(size_t)sysconf(_SC_PAGESIZE),rounded=(n+page-1)/page*page,total=rounded+page;
    void *p=mmap(NULL,total,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(p==MAP_FAILED || mprotect((char*)p+rounded,page,PROT_NONE))exit(10);
    struct region r={p,total,(unsigned char*)p+rounded-n};return r;
}
static void one(void (*f)(void),unsigned n,unsigned expected) {
    trap_code=trap_byte=0;target_report[8]=0;
    if(setjmp(trap)==0)f();
    if(expected==n) {
        if(trap_code || target_report[8]!=n) {fprintf(stderr,"false_reject %u %u\n",trap_code,trap_byte);exit(11);}
    } else if(trap_code!=94 || trap_byte!=expected || target_report[8]) {
        fprintf(stderr,"bad_reject expected=%u got=%u/%u reported=%llu\n",expected,trap_code,trap_byte,(unsigned long long)target_report[8]);exit(12);
    }
}
static void pair(void (*old)(void),void (*newer)(void),unsigned n) {
    unsigned first=0;while(first<n && actual_base[first]==fixture_gold[first])++first;
    one(old,n,first);one(newer,n,first);++cases;
}
static uint32_t random_word=0x6b1d2947;
static uint32_t random32(void) {uint32_t x=random_word;x^=x<<13;x^=x>>17;x^=x<<5;return random_word=x;}
static void exercise(unsigned n,void (*old)(void),void (*newer)(void),int exhaustive) {
    struct region a=guarded(n),g=guarded(n);actual_base=a.data;fixture_gold=g.data;
    for(unsigned i=0;i<n;++i)actual_base[i]=fixture_gold[i]=(unsigned char)random32();
    pair(old,newer,n);
    if(exhaustive)for(unsigned b=0;b<n;++b)for(unsigned bit=0;bit<8;++bit) {
        actual_base[b]^=(unsigned char)(1u<<bit);pair(old,newer,n);actual_base[b]^=(unsigned char)(1u<<bit);
    }
    unsigned boundary[]={0,7,8,15,16,31,32,55,56,63,64,65,127,128,n-65,n-64,n-33,n-32,n-31,n-8,n-7,n-1};
    for(unsigned i=0;i<sizeof boundary/sizeof boundary[0];++i) {
        unsigned b=boundary[i];if(b>=n)continue;
        actual_base[b]^=0x80;pair(old,newer,n);actual_base[b]^=0x80;
    }
    /* Same XOR masks must not cancel; include the high half of every word. */
    for(unsigned slot=1;slot<8;++slot) {
        actual_base[7]^=0x80;actual_base[slot*8+7]^=0x80;
        pair(old,newer,n);actual_base[7]^=0x80;actual_base[slot*8+7]^=0x80;
    }
    for(unsigned b=n-32;b<n;++b) {
        actual_base[b]^=1;pair(old,newer,n);actual_base[b]^=1;
    }
    if(n>152476) {actual_base[152476]^=1;pair(old,newer,n);actual_base[152476]^=1;}
    for(unsigned k=0;k<128;++k) {
        unsigned b=random32()%n,c=random32()%n;if(b==c)c=(c+1)%n;
        actual_base[b]^=0x42;actual_base[c]^=0x81;
        pair(old,newer,n);actual_base[b]^=0x42;actual_base[c]^=0x81;
    }
    if(munmap(a.mapping,a.bytes)||munmap(g.mapping,g.bytes))exit(13);
}
int main(void) {
    exercise(160,old_small,new_small,1);
    exercise(3691424,old_full,new_full,0);
    printf("{\"status\":\"COMPARE_BATCH8_HOST_C_PASS\",\"cases\":%lu,\"state_bytes\":3691424,\"small_bytes\":160,\"guard_page_at_logical_end\":true}\n",cases);
    return 0;
}
'''


def host_source():
    text=HEADER
    for label,size in (('small',160),('full',STATE_BYTES)):
        text+='\n#define R2_CONSUMER_STATE_BYTES '+str(size)+'u\n'
        for name,body in (('old',ORIGINAL),('new',candidate())):
            body=body.replace('static void complete_compare(void)',
                '__attribute__((noinline,noclone)) static void '+name+'_'+label+'(void)')
            text+=body
        text+='\n#undef R2_CONSUMER_STATE_BYTES\n'
    return text+TEST


def screen(a):
    need(a.output.is_absolute() and not a.output.exists(),'fresh absolute screen output')
    cc=shutil.which(a.cc);need(cc,'available C compiler')
    a.output.mkdir(parents=True)
    source=a.output/'screen.c';binary=a.output/'screen'
    source.write_text(host_source())
    argv=[cc,'-std=gnu11','-O2','-fno-tree-vectorize','-fno-tree-slp-vectorize',
          '-fno-ipa-icf','-fno-builtin','-Wall','-Wextra','-Werror',
          '-fsanitize=address,undefined',str(source),'-o',str(binary)]
    started=time.monotonic()
    logs=[]
    # The managed host uses ptrace; LeakSanitizer cannot operate there.
    # Address/undefined-behavior checks and explicit guard pages remain enabled.
    env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1'}
    for label,command in (('compile',argv),('run',[str(binary)])):
        with (a.output/(label+'-stdout.log')).open('wb') as out,(a.output/(label+'-stderr.log')).open('wb') as err:
            proc=subprocess.run(command,cwd=a.output,stdout=out,stderr=err,timeout=60,env=env)
        logs.append(dict(label=label,argv=command,exit_code=proc.returncode))
        (a.output/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
        need(proc.returncode==0,'host '+label+' failed; raw evidence retained')
        if label=='run':
            need(not (a.output/'run-stderr.log').read_bytes(),'host diagnostics must be empty')
    result=json.loads((a.output/'run-stdout.log').read_bytes())
    result.update(contract=CONTRACT,elapsed_seconds=time.monotonic()-started,
        compiler=cc,compiler_sha256=sha(Path(cc).read_bytes()),source_sha256=sha(source.read_bytes()),
        candidate_body_sha256=sha(candidate().encode()),original_body_sha256=BODY_SHA,
        generator_sha256=sha(Path(__file__).read_bytes()),
        address_sanitizer=True,undefined_behavior_sanitizer=True,leak_sanitizer=False,
        qualification='host C semantics and guarded ends only; no RISC-V or EMU execution',
        target_runtime_qualified=False,application_performance_qualified=False)
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='mode',required=True)
    q=sub.add_parser('derive');q.add_argument('--input',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('screen');q.add_argument('--cc',default='gcc');q.add_argument('--output',type=Path,required=True)
    a=p.parse_args();(derive if a.mode=='derive' else screen)(a)
