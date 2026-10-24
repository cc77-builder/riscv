"""PARTIAL_KILL v2: fixed vector schedule, eight scalar-DIV latency classes.

No changes to the frozen v1 corpus. SRT16 iteration count depends on operand
leading-zero difference; changing divisor width tests branch timing directly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_suite
model=run_suite.load_module('partial_vector_model',Path(__file__).resolve().parents[1]/'workloads/generate.py')
CONTRACT='o2-partial-kill-directed-v2'
WIDTHS=(32,36,40,44,48,52,56,60)
TRIALS=16


def corpus():
    initial=model.initial(); groups=[]; all_trials=[]; expected=[]
    asm=['.option norvc','.option norelax','.text']
    for group,width in enumerate(WIDTHS):
        trials=[]; outputs=[]
        for n in range(TRIALS):
            h=hashlib.sha256(f'O2-control-20261019:14:{n}'.encode()).digest()
            numerator=int.from_bytes(h[:8],'little') | (1<<63)
            divisor=(int.from_bytes(h[8:16],'little') & ((1<<(width-1))-1)) | (1<<(width-1))
            execute=(h[16]&1)==0
            trials.append([numerator,divisor,numerator//divisor ^ (not execute)])
            regs=[r[:] for r in initial]
            regs[28]=list(bytes.fromhex('00006040')*4)
            regs[19][:8]=[255 if y==0 else x//y for x,y in zip(regs[8][:8],regs[9][:8])]
            regs[16]=model.dot(regs[8],regs[9])
            if execute:
                for reg in range(20,28):regs[reg]=model.dot(regs[8],regs[9])
            outputs.append(regs)
        expected.append(outputs); all_trials.extend(trials)
        groups.append(dict(id=group,divisor_bits=width,fp_burst=15,decode_gap=2,trials=TRIALS,
                           expected_commits=TRIALS+8*sum(a//b==c for a,b,c in trials)))
        asm += ['.balign 64',f'.global partial_{group}',f'partial_{group}:',
                'li t6,16','li t5,0',f'.Ltry_{group}:','mv t4,a0','vsetivli zero,16,e8,m1,tu,mu']
        for reg in range(32):asm += [f'vl1re8.v v{reg},(t4)','addi t4,t4,16']
        asm += ['li t0,0x40e00000','fmv.w.x ft0,t0','li t0,0x40000000','fmv.w.x ft2,t0',
                'fdiv.s ft1,ft0,ft2','vsetivli zero,4,e32,m1,tu,mu']
        asm += ['vfmv.v.f v28,ft1']*15
        asm += ['vsetivli zero,8,e8,m1,tu,mu','ld t0,0(a2)','ld t1,8(a2)','ld t3,16(a2)',
                'vdivu.vv v19,v8,v9',f'.word 0x{model.word(16,8,9):08x}',
                'divu t2,t0,t1',f'bne t2,t3,.Lskip_{group}','addi t5,t5,1','addi t5,t5,1']
        asm += [f'.word 0x{model.word(reg,8,9):08x}' for reg in range(20,28)]
        asm += [f'.Lskip_{group}:']
        for reg in range(32):asm += [f'vs1r.v v{reg},(a1)','addi a1,a1,16']
        asm += ['addi a2,a2,24','addi t6,t6,-1',f'bnez t6,.Ltry_{group}','fence rw,rw','ret',
                f'.global partial_{group}_end',f'partial_{group}_end:',f'.space 2048-(.-partial_{group}),0']
    header=['#include <stdint.h>',f'#define GROUPS {len(WIDTHS)}',f'#define TRIALS {TRIALS}']
    header += [f'extern void partial_{g}(const void*,void*,const void*);' for g in range(len(WIDTHS))]
    header += ['static void (*const entries[GROUPS])(const void*,void*,const void*) = {'+
               ','.join(f'partial_{g}' for g in range(len(WIDTHS)))+'};',
               'static const uint8_t input[32][16] = '+model.c_array(initial)+';',
               'static const uint64_t trials[GROUPS*TRIALS][3] = {'+
               ','.join('{'+','.join(f'UINT64_C({x})' for x in row)+'}' for row in all_trials)+'};',
               'static const uint8_t expected[GROUPS][TRIALS][32][16] = '+model.c_array(expected)+';']
    files={'kernels.S':'\n'.join(asm)+'\n','cases.h':'\n'.join(header)+'\n'}
    manifest=dict(schema=2,contract=CONTRACT,groups=groups,trials=len(WIDTHS)*TRIALS,
                  whole_vector_bytes_checked=len(WIDTHS)*TRIALS*512,
                  expected_vdot_commits=sum(g['expected_commits'] for g in groups),
                  generated_sha256={n:hashlib.sha256(s.encode()).hexdigest() for n,s in files.items()},
                  performance_measured=False,coverage_claim='pending actual strict full-core observations')
    return files,manifest


def emit(out):
    out.mkdir(parents=True,exist_ok=False)
    files,manifest=corpus()
    for name,text in files.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(emit(p.parse_args().output)))
