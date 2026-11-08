#!/usr/bin/env python3
"""Deterministic finite supplementary stimulus. Does not run target tools."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
PHASES = (0, 1, 2, 4)
X = [-128, 127, -1, 1, -7, 11, 64, -64] + [0] * 8
Y = [1, -1, 127, -128, 13, -17, 2, -2] + [0] * 8
SENTINEL = bytes.fromhex('13579bdf2468ace01122334455667788')
DOT = (sum(x*y for x,y in zip(X[:8],Y[:8])) & 0xffffffff).to_bytes(4,'little') + bytes(12)
NUMERATOR = 0x8000000000003039
DIVISOR = 3
QUOTIENT = NUMERATOR // DIVISOR

def word(vd):
    return 0x0200000b | (vd << 7) | (8 << 15) | (9 << 20)

def label(name):
    return f'.global {name}\n{name}:'

def prefix(name):
    return [f'.global {name}', f'.type {name},@function', f'{name}:',
            'csrr a3,vl', 'csrr a4,vtype', 'csrr a5,vstart', 'csrr a6,vcsr', 'csrr a7,fcsr',
            'sd a3,32(a1)', 'sd a4,40(a1)', 'sd a5,48(a1)', 'sd a6,56(a1)', 'sd a7,64(a1)',
            'csrwi vstart,0', 'csrwi vcsr,0', 'csrwi fcsr,0',
            'vsetivli zero,8,e8,m1,tu,mu', 'vl1re8.v v8,(a0)',
            'addi t3,a0,16', 'vl1re8.v v9,(t3)', 'addi t3,a0,32', 'vl1re8.v v17,(t3)']

def suffix(name, guard=False):
    return ['vs1r.v v0,(a1)' if guard else 'vs1r.v v16,(a1)',
            'addi t3,a1,16', 'vs1r.v v17,(t3)',
            'li t3,0' if guard else 'fmv.x.w t3,ft0', 'sd t3,112(a1)',
            'ld t3,24(a2)', 'sd t3,120(a1)',
            'csrwi vstart,0', 'vsetvl zero,a3,a4', 'csrw vstart,a5', 'csrw vcsr,a6', 'csrw fcsr,a7',
            'csrr t3,vl', 'sd t3,72(a1)', 'csrr t3,vtype', 'sd t3,80(a1)',
            'csrr t3,vstart', 'sd t3,88(a1)', 'csrr t3,vcsr', 'sd t3,96(a1)',
            'csrr t3,fcsr', 'sd t3,104(a1)', 'ret', label(name+'_end'), f'.size {name},.-{name}']

asm = ['.section .text', '.balign 4', '.option push', '.option norvc', '.option norelax']
roles = []
functions = []
name = 'o2c_guard'
asm += prefix(name) + [label(name+'_dot'), f'.word 0x{word(0):08x}'] + suffix(name, True)
functions.append({'name':name, 'stage':'prelude', 'phase':None})
roles.append({'symbol':name+'_dot','stage':'prelude','phase':None,'packet':'guard','vd':0,'word':word(0)})
for phase in PHASES:
    for stage in ('S0','S1'):
        name=f'o2c_{stage.lower()}_p{phase}'
        asm += prefix(name)
        asm += ['li t3,0x40e00000','fmv.w.x ft1,t3','li t3,0x40000000','fmv.w.x ft2,t3',
                'fdiv.s ft0,ft1,ft2,rne','vsetivli zero,4,e32,m1,tu,mu',label(name+'_pressure')]
        asm += [f'vfmv.v.f v{v},ft0' for v in range(24,32)]
        asm += ['vsetivli zero,8,e8,m1,tu,mu','fmv.x.w t6,ft0','andi t6,t6,255']
        asm += ['xori t6,t6,1','xori t6,t6,1'] * phase
        asm += ['add t6,a0,t6','vle8.v v8,(t6)']
        if stage=='S1':
            asm += ['sub t4,t6,a0','ld t0,0(a2)','ld t1,8(a2)','ld t2,16(a2)']
        asm += [label(name+'_A'),f'.word 0x{word(16):08x}']
        if stage=='S1':
            asm += ['add t0,t0,t4','divu t0,t0,t1',label(name+'_branch'),f'bne t0,t2,{name}_skip_B']
        asm += [label(name+'_B'),f'.word 0x{word(17):08x}']
        if stage=='S1':
            asm += [label(name+'_skip_B')]
        asm += suffix(name)
        functions.append({'name':name,'stage':stage,'phase':phase})
        for packet,vd in [('A',16),('B',17)]:
            entry={'symbol':name+'_'+packet,'stage':stage,'phase':phase,'packet':packet,'vd':vd,'word':word(vd)}
            if stage=='S1' and packet=='A': entry['eligible_commit_ordinal']=8
            roles.append(entry)
asm += ['.option pop','.section .note.GNU-stack,"",@progbits']
(ROOT/'kernels.S').write_text('\n'.join(asm)+'\n')
plan=[{'seq':0,'kernel':'o2c_guard','stage':'prelude','phase':None,'probe':False,'ordinal':0,'flags':0,'retired_symbols':['o2c_guard_dot']}]
for phase in PHASES:
    name=f'o2c_s0_p{phase}'
    plan.append({'seq':len(plan),'kernel':name,'stage':'S0','phase':phase,'probe':False,'ordinal':0,'flags':len(plan),'retired_symbols':[name+'_A',name+'_B']})
    name=f'o2c_s1_p{phase}'
    for ordinal in range(9):
        probe=ordinal==8
        plan.append({'seq':len(plan),'kernel':name,'stage':'S1','phase':phase,'probe':probe,'ordinal':ordinal,'flags':len(plan),'retired_symbols':[name+'_A']+([] if probe else [name+'_B'])})
headers=['#ifndef O2C_CASES_H','#define O2C_CASES_H','#include "contract.h"']
for f in functions: headers.append(f'extern void {f["name"]}(const uint8_t *, struct o2c_result *, const struct o2c_trial *);')
headers += ['struct o2c_case { o2c_kernel kernel; const char *stage; unsigned phase, probe; struct o2c_trial trial; };', '#define O2C_CALL_COUNT 41', 'static const struct o2c_case o2c_cases[O2C_CALL_COUNT] = {']
for p in plan:
    q=QUOTIENT + int(p['probe'])
    headers.append('  {%s, "%s", %d, %d, {0x%xULL, %d, 0x%xULL, %d}},' % (p['kernel'],p['stage'],p['phase'] or 0,p['probe'],NUMERATOR,DIVISOR,q,p['flags']))
headers += ['};','#endif']
(ROOT/'cases.h').write_text('\n'.join(headers)+'\n')
def array(name,data):
    return f'const uint8_t {name}[{len(data)}] __attribute__((aligned(16))) = {{'+','.join(str(x & 255) for x in data)+'};'
(ROOT/'data.c').write_text('#include "contract.h"\n'+array('o2c_input',X+Y+list(SENTINEL))+'\n'+array('o2c_dot',DOT)+'\n'+array('o2c_sentinel',SENTINEL)+'\n')
base={'schema':'sp1-e-o2-cancel-software-v1','phases':list(PHASES),'functions':functions,'pc_roles':roles,'call_plan':plan,
      'expected_calls':41,'expected_custom_commits':77,'expected_f2v_arch_instructions':320,
      'training_calls_per_phase':8,'probe_calls_per_phase':1,'s0_calls_per_phase':1,
      'input_bytes':bytes(x&255 for x in X+Y).hex(),'expected_dot128':DOT.hex(),'sentinel128':SENTINEL.hex(),
      'vs1_low64':int.from_bytes(bytes(x&255 for x in X[:8]),'little'),'vs2_low64':int.from_bytes(bytes(x&255 for x in Y[:8]),'little'),
      'expected_caller_csrs':{'vl':8,'vtype':0,'vstart':0,'vcsr':7,'fcsr':96},
      'expected_fp_bits':0x40600000,'guard_fp_bits':0,'result_bytes':128,
      'integer_division':{'numerator':NUMERATOR,'divisor':DIVISOR,'quotient':QUOTIENT},
      'target_status':'NOT_RUN','coverage_status':'NOT_TESTED','dynamic_abi_status':'NOT_TESTED',
      'uart_prefix':'OC19_','no_target_execution':True}
assert len(plan)==41 and sum(len(p['retired_symbols']) for p in plan)==77
(ROOT/'manifest.source.json').write_text(json.dumps(base,indent=2)+'\n')
