"""T12 sequence corpus. Does not rewrite any T05/T11 golden data."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("original_vdot", ROOT / "team/models/vdot/model.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
SEED = 0x20261014

def initial(group):
    return [list(hashlib.sha256(f"T12:{SEED}:{group}:{i}".encode()).digest()[:16]) for i in range(32)]

def emit(output):
    output.mkdir(parents=True, exist_ok=True)
    asm = ['.option norvc', '.text']
    header = ['#include <stdint.h>']
    manifest = {'schema': 1, 'seed': SEED, 'contract': 'vdot-s8x8-r32-v0.1', 'groups': []}
    for g, name in enumerate(['raw-waw-v0', 'vl-csr-adjacent', 'vfex4-mixed', 'rob-ftq-wrap']):
        regs = initial(g)
        start = [r[:] for r in regs]
        snapshots = []
        operations = []
        asm += [f'.globl t12_group{g}', f't12_group{g}:', 'mv t4, a0',
                'vsetivli zero,16,e8,m1,tu,mu']
        for reg in range(32):
            asm += [f'vle8.v v{reg},(t4)', 'addi t4,t4,16']
        asm += ['vsetivli zero,8,e8,m1,tu,mu']
        def dot(d, a, b):
            word = 0x0200000b | d << 7 | a << 15 | b << 20
            value = model.vdot(int.from_bytes(bytes(regs[a]), 'little'), int.from_bytes(bytes(regs[b]), 'little'))
            regs[d] = list(value.to_bytes(16, 'little'))
            asm.append(f'.word 0x{word:08x}')
            operations.append({'op': 'vdot', 'vd': d, 'vs1': a, 'vs2': b})
        def add(d, a, b):
            regs[d][:8] = [(x+y)&255 for x,y in zip(regs[a][:8],regs[b][:8])]
            asm.append(f'vadd.vv v{d},v{a},v{b}')
            operations.append({'op':'vadd','vd':d,'a':a,'b':b})
        def divide(d, a, b):
            regs[d][:8] = [255 if y==0 else x//y for x,y in zip(regs[a][:8],regs[b][:8])]
            asm.append(f'vdivu.vv v{d},v{a},v{b}')
            operations.append({'op':'vdivu','vd':d,'a':a,'b':b})
        for block in range(32):
            for j in range(16):
                if g==0:
                    d = [0,8,9,10,10,31,1,2][j%8]
                    a = [8,0,8,9,10,10,31,1][j%8]
                    b = [9,9,0,8,9,8,9,31][j%8]
                    if j%4==0: add(a,a,3)
                    dot(d,a,b)
                elif g==1:
                    # Replace a previous VL=16 with VL=8 immediately before vdot.
                    # CSR readback is saved after the sequence, without using it as an oracle.
                    asm += ['vsetivli zero,16,e8,m1,tu,mu',
                            f'csrwi vcsr,{(block+j)%8}',
                            'vsetivli zero,8,e8,m1,tu,mu']
                    dot(10,8,9)
                    asm += ['csrr t0,vcsr','sd t0,0(a2)','addi a2,a2,8']
                elif g==2:
                    # F2v uses the higher-priority shared VF write port. A delayed
                    # scalar FP result lets that producer overlap the vdot stream.
                    if j%4==0:
                        asm += ['li t0,0x40e00000','fmv.w.x ft0,t0',
                                'li t0,0x40000000','fmv.w.x ft2,t0',
                                'fdiv.s ft1,ft0,ft2',
                                'vsetivli zero,4,e32,m1,tu,mu','vfmv.v.f v28,ft1',
                                'vsetivli zero,8,e8,m1,tu,mu']
                        regs[28] = list(bytes.fromhex('00006040')*4)  # exactly 3.5f
                        operations.append({'op':'fdiv-s-vfmv','expected_f32':'40600000'})
                    divide(16+(j%4),8,9)
                    dot(10+(j%4),8,9)
                    add(24+(j%4),8,9)
                else:
                    dot(10+(j%4),8,9)
                    asm += [f'jal zero,.Lg{g}_{block}_{j}', '.word 0x00000000',
                            f'.Lg{g}_{block}_{j}:']
            # Whole-register stores observe all 128 bits without changing VL.
            for reg in range(32):
                asm += [f'vs1r.v v{reg},(a1)', 'addi a1,a1,16']
            snapshots.append([r[:] for r in regs])
        asm += ['ret']
        header += [f'extern void t12_group{g}(const void *,void *,void *);',
                   f'static const uint8_t input{g}[32][16] = '+json.dumps(start).replace('[','{').replace(']','}')+';',
                   f'static const uint8_t expected{g}[32][32][16] = '+json.dumps(snapshots).replace('[','{').replace(']','}')+';']
        manifest['groups'].append({'id':g,'name':name,'checkpoints':32,'vdot_count':512,
                                   'operations':operations})
    # A delayed scalar branch overlaps younger vector operations. Every iteration
    # has a complete 128-bit architectural observation; the RTL observer must
    # establish that an accepted younger instruction was really cancelled.
    asm += ['.globl t12_speculate','t12_speculate:',
            'vsetivli zero,16,e8,m1,tu,mu','vle8.v v8,(a0)','addi t0,a0,16','vle8.v v9,(t0)',
            'vsetivli zero,8,e8,m1,tu,mu','li t4,256','.Lt12_try:',
            'addi t0,a0,32','vl1re8.v v20,(t0)',
            'ld t0,0(a2)','ld t1,8(a2)','ld t3,16(a2)',
            'vdivu.vv v19,v8,v9','divu t2,t0,t1',
            'bne t2,t3,.Lt12_skip', '.word 0x02940a0b',
            '.Lt12_skip:', 'vs1r.v v20,(a1)','addi a1,a1,16','addi a2,a2,24',
            'addi t4,t4,-1','bnez t4,.Lt12_try','ret']
    src = initial(4)[:3]
    trials=[];expected=[]
    for i in range(256):
        h=hashlib.sha256(f'T12-branch:{SEED}:{i}'.encode()).digest()
        n=int.from_bytes(h[:8],'little')|1<<63
        d=int.from_bytes(h[8:16],'little')%(1<<31)+3
        execute=(h[16]&1)==0
        trials.append([n,d,n//d if execute else (n//d)^1])
        expected.append(list(model.vdot(int.from_bytes(bytes(src[0]),'little'),int.from_bytes(bytes(src[1]),'little')).to_bytes(16,'little')) if execute else src[2])
    header += ['extern void t12_speculate(const void *,void *,void *);',
               'static const uint8_t spec_input[3][16] = '+json.dumps(src).replace('[','{').replace(']','}')+';',
               'static const uint64_t spec_trials[256][3] = {'+','.join('{'+','.join(f'UINT64_C({x})' for x in row)+'}' for row in trials)+'};',
               'static const uint8_t spec_expected[256][16] = '+json.dumps(expected).replace('[','{').replace(']','}')+';']
    manifest['speculation']={'attempts':256,'expected_architectural_vdot':sum(x[0]//x[1]==x[2] for x in trials),
                             'acceptance':'requires observed issue then cancellation; GOOD TRAP alone insufficient'}
    (output/'sequences.S').write_text('\n'.join(asm)+'\n')
    (output/'sequences.h').write_text('\n'.join(header)+'\n')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    digest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.name in ['sequences.S','sequences.h','manifest.json']}
    print(json.dumps(digest,sort_keys=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    emit(parser.parse_args().output)
