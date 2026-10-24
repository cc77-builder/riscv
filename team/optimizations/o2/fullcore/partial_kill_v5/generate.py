"""A dependent producer and a co-ready sibling target one admission-cycle gap."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_suite
model = run_suite.load_module('partial_v5_model', Path(__file__).resolve().parents[1]/'workloads/generate.py')
CONTRACT = 'o2-partial-kill-dependency-admission-v5'
TRIALS = 16


def inputs_and_expected():
    initial = model.initial()
    divided = initial[19][:]
    divided[:8] = [255 if b == 0 else a // b for a, b in zip(initial[8][:8], initial[9][:8])]
    low = model.signed(divided[0])
    trials, expected = [], []
    for n in range(TRIALS):
        execute = (hashlib.sha256(f'O2-control-20261019:14:{n}'.encode()).digest()[16] & 1) == 0
        trials.append((low ^ (not execute)) & ((1 << 64) - 1))
        regs = [r[:] for r in initial]
        regs[19] = divided[:]
        regs[17] = model.dot(divided, initial[9])
        regs[18] = model.dot(regs[17], initial[9])
        regs[16] = model.dot(regs[17], initial[9])
        if execute:
            for reg in range(20, 28):
                regs[reg] = model.dot(regs[17], initial[9])
        expected.append(regs)
    return initial, trials, expected


def corpus():
    initial, trials, expected = inputs_and_expected()
    asm = ['.option norvc', '.option norelax', '.text', '.balign 64',
           '.global partial_0', 'partial_0:', 'li t6,16', '.Ltry:',
           'mv t4,a0', 'vsetivli zero,16,e8,m1,tu,mu']
    for reg in range(32):
        asm += [f'vl1re8.v v{reg},(t4)', 'addi t4,t4,16']
    asm += ['vsetivli zero,8,e8,m1,tu,mu', 'ld t3,0(a2)',
            '.global partial_div', 'partial_div:', 'vdivu.vv v19,v8,v9',
            '.global partial_producer', 'partial_producer:', f'.word 0x{model.word(17,19,9):08x}',
            '.global partial_sibling', 'partial_sibling:', f'.word 0x{model.word(18,17,9):08x}',
            '.global partial_old', 'partial_old:', f'.word 0x{model.word(16,17,9):08x}',
            '.global partial_extract', 'partial_extract:', 'vmv.x.s t2,v19',
            '.global partial_branch', 'partial_branch:', 'bne t2,t3,.Lskip',
            '.global partial_young', 'partial_young:']
    asm += [f'.word 0x{model.word(reg,17,9):08x}' for reg in range(20, 28)]
    asm += ['.Lskip:']
    for reg in range(32):
        asm += [f'vs1r.v v{reg},(a1)', 'addi a1,a1,16']
    asm += ['addi a2,a2,8', 'addi t6,t6,-1', 'bnez t6,.Ltry', 'fence rw,rw', 'ret',
            '.global partial_0_end', 'partial_0_end:']
    header = ['#include <stdint.h>', '#define GROUPS 1', f'#define TRIALS {TRIALS}',
              'extern void partial_0(const void*,void*,const void*);',
              'static void (*const entries[GROUPS])(const void*,void*,const void*) = {partial_0};',
              'static const uint8_t input[32][16] = '+model.c_array(initial)+';',
              'static const uint64_t trials[TRIALS] = {'+','.join(f'UINT64_C({x})' for x in trials)+'};',
              'static const uint8_t expected[GROUPS][TRIALS][32][16] = '+model.c_array([expected])+';']
    files = {'kernels.S': '\n'.join(asm)+'\n', 'cases.h': '\n'.join(header)+'\n'}
    low = model.signed(expected[0][19][0]) & ((1 << 64) - 1)
    manifest = dict(schema=5, contract=CONTRACT, groups=1, trials=TRIALS,
                    dependency='vdivu v19 -> {vdot v17 -> co-ready sibling v18 and older/younger vdots, vmv.x.s v19 -> branch}',
                    whole_vector_bytes_checked=TRIALS*512,
                    expected_vdot_commits=3*TRIALS+8*sum(x == low for x in trials),
                    generated_sha256={n: hashlib.sha256(s.encode()).hexdigest() for n,s in files.items()},
                    performance_measured=False, coverage_claim='pending actual strict full-core observations')
    return files, manifest


def emit(out):
    out.mkdir(parents=True, exist_ok=False)
    files, manifest = corpus()
    for name, text in files.items():
        (out/name).write_text(text, encoding='utf-8', newline='\n')
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8', newline='\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(emit(parser.parse_args().output)))
