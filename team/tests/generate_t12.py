"""T12 deterministic directed sequences and paired, full-width RVV kernels.
No DUT-derived expectations. Ordinary RVV scratch is explicitly declared.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

CONTRACT = 'vdot-s8x8-r32-v0.1'
SEED = 0x20261014
REPEATS = 4

def s8(x):
    return x if x < 128 else x - 256

def dot(a, b):
    return sum(s8(a[i]) * s8(b[i]) for i in range(8)).to_bytes(4, 'little', signed=True) + bytes(12)

def word(vd, a, b):
    if not all(0 <= r < 32 for r in (vd, a, b)):
        raise ValueError('register out of range')
    return 0x0200000b | b << 20 | a << 15 | vd << 7

def custom(vd=10, a=8, b=9):
    return f'  .word 0x{word(vd,a,b):08x} /* vdot v{vd}, v{b}, v{a} */'

def general(vd=10, a=8, b=9, known=False):
    # Same widening sequence as the mature T09 baseline. Product EMUL=2.
    lines = [] if known else ['  csrr t3, vl', '  csrr t4, vtype']
    lines += ['  vsetivli zero, 4, e32, m1, tu, mu', '  vmv.v.i v4, 0',
              '  vsetivli zero, 8, e8, m1, tu, mu', f'  vwmul.vv v2, v{a}, v{b}',
              '  vsetivli zero, 8, e16, m2, tu, mu', '  vwredsum.vs v5, v2, v4',
              '  vsetivli zero, 4, e32, m1, tu, mu', '  vmv.x.s t2, v5',
              f'  vmv.v.i v{vd}, 0', f'  vmv.s.x v{vd}, t2']
    lines += ['  vsetivli zero, 8, e8, m1, tu, mu'] if known else ['  vsetvl zero, t3, t4']
    return lines

def batched():
    lines = ['  vsetivli zero, 4, e32, m1, tu, mu', '  vmv.v.i v4, 0',
             '  vsetivli zero, 8, e8, m1, tu, mu']
    lines += [f'  vwmul.vv v{16+2*i}, v8, v9' for i in range(4)]
    lines += ['  vsetivli zero, 8, e16, m2, tu, mu']
    lines += [f'  vwredsum.vs v{24+i}, v{16+2*i}, v4' for i in range(4)]
    lines += ['  vsetivli zero, 4, e32, m1, tu, mu']
    for i in range(4):
        lines += [f'  vmv.x.s t2, v{24+i}', f'  vmv.v.i v{10+i}, 0', f'  vmv.s.x v{10+i}, t2']
    return lines + ['  vsetivli zero, 8, e8, m1, tu, mu']

def fixture(a=None, b=None):
    regs = [bytes((0x51 + r*7 + i*13) & 255 for i in range(16)) for r in range(32)]
    regs[8] = bytes(x & 255 for x in (a or [-128,127,-1,1,2,-2,63,-64])) + bytes([0xa5]*8)
    regs[9] = bytes(x & 255 for x in (b or [127,-128,1,-1,-2,2,-64,63])) + bytes([0x5a]*8)
    return regs

def apply(regs, vd=10, a=8, b=9):
    regs[vd] = dot(regs[a], regs[b])

def loop(body, n, label):
    return [f'  li t6, {n}', f'.L{label}:'] + body + ['  addi t6, t6, -1', f'  bnez t6, .L{label}']

def corpus():
    rows = []
    def add(name, body, operations, *, before=None, scratch=(), fault_vl=None, kind='stress', scenario='', method='', dots=0):
        initial = list(before or fixture())
        expected = list(initial)
        for op in operations:
            if op[0] == 'dot':
                apply(expected, *op[1:])
            elif op[0] == 'div':
                _, d, a, b = op
                out = bytearray(expected[d])
                for i in range(8):
                    x, y = s8(expected[a][i]), s8(expected[b][i])
                    out[i] = (int(abs(x)//abs(y)) * (-1 if (x < 0) != (y < 0) else 1) if y else -1) & 255
                expected[d] = bytes(out)
            else:
                raise ValueError(op)
        rows.append(dict(id=name, body=body, before=[x.hex() for x in initial], expected=[x.hex() for x in expected],
                         scratch=list(scratch), fault_vl=fault_vl, kind=kind, scenario=scenario, method=method, dots=dots))
    add('vl-adjacent', ['  li t1, 8', '  li t2, 0', '  vsetvl zero, t1, t2', custom()], [('dot',10,8,9)])
    add('raw-alias', [custom(10), custom(10,10,9), custom(8,10,8), custom(9,8,9)],
        [('dot',10,8,9),('dot',10,10,9),('dot',8,10,8),('dot',9,8,9)])
    add('waw', [custom(10,8,9),custom(10,8,8),custom(10,9,9)],
        [('dot',10,8,9),('dot',10,8,8),('dot',10,9,9)])
    add('independent-streams', [custom(10+i) for i in range(4)], [('dot',10+i,8,9) for i in range(4)])
    mixed = ['  vdiv.vv v14, v8, v9',custom(10),'  vdiv.vv v15, v9, v8',custom(11,14,15)]
    add('vfex4-div-mix',loop(mixed,32,'mix'), [('div',14,8,9),('dot',10,8,9),('div',15,9,8),('dot',11,14,15)]*32)
    add('raw-long',loop([custom(10,10,9)],256,'raw'), [('dot',10,10,9)]*256)
    branch = ['  li t1, 99991', '  li t2, 97', '  div t3, t1, t2', '  li t4, 1030',
              '  beq t3, t4, 1f', custom(31), '  j 2f', '1:', custom(10,8,8), '2:']
    # 99991 / 97 = 1030 remainder 81: take the dependent branch.
    add('branch-dependent-candidate',loop(branch,128,'branch'), [('dot',10,8,8)]*128)
    wrap = [custom(10),'  andi t1, t6, 1', '  beqz t1, 1f',custom(11),'  j 2f',
            '1:',custom(12),'2:',custom(13)]
    ops=[]
    for i in range(1024,0,-1):
        ops += [('dot',10,8,9),('dot',11 if i&1 else 12,8,9),('dot',13,8,9)]
    add('rob-ftq-wrap-candidate',loop(wrap,1024,'wrap'),ops)
    for vl in (0,1,7,9,16):
        name=f'illegal-vl{vl}-recover'
        body=['  la t0, '+name.replace('-','_')+'_fault', '  sd t0, REC_EXPECTED_PC(s0)',
              '  la t0, '+name.replace('-','_')+'_resume', '  sd t0, REC_RESUME_PC(s0)',
              '  li t0, 2', '  sd t0, REC_EXPECTED_CAUSE(s0)', '  li t0, 1', '  sd t0, REC_ARMED(s0)',
              f'  li t1, {vl}', '  li t2, 0', '  vsetvl zero, t1, t2',
              '.globl '+name.replace('-','_')+'_fault', name.replace('-','_')+'_fault:', custom(16),
              name.replace('-','_')+'_resume:', '  li t1, 8', '  vsetvl zero, t1, t2', custom(10),
              '  la t5, t12_recovery_csrs']
        for i, csr in enumerate(('vtype','vl','vstart','vxrm','vxsat','vcsr')):
            body += [f'  csrr t0, {csr}',f'  sd t0, {i*8}(t5)']
        body += ['  la t5, t12_recovery_status', '  csrr t0, mstatus', '  sd t0, 0(t5)']
        add(name,body,[('dot',10,8,9)],fault_vl=vl)
    boundary=[([0]*8,[127]*8),([1]*8,[1]*8),([-1]*8,[1]*8),([-1]*8,[-1]*8),
              ([127]*8,[127]*8),([-128]*8,[127]*8),([-128]*8,[-128]*8),
              (list(range(1,9)),list(range(1,9))),([1,-2,3,-4,5,-6,7,-8],[8,7,6,5,4,3,2,1]),
              ([-128]+[0]*7,[-1]+[0]*7),([0]*7+[-128],[0]*7+[127])]
    rng=random.Random(SEED)
    inputs=boundary+[( [rng.randrange(-128,128) for _ in range(8)], [rng.randrange(-128,128) for _ in range(8)]) for _ in range(64)]
    for i,(a,b) in enumerate(inputs):
        for method in ('vdot','rvv'):
            add(f'equiv-{i:03d}-{method}',[custom()] if method=='vdot' else general(),[('dot',10,8,9)],
                before=fixture(a,b),scratch=() if method=='vdot' else (2,3,4,5),kind='equivalence',method=method)
    for scenario,n,unroll in (('complete',16,1),('known-config',16,1),('independent-batch',16,4)):
        for method in ('empty','vdot','rvv'):
            if method=='empty':
                body=loop([],n,scenario.replace('-','_')+'_empty'); ops=[]; scratch=()
            elif method=='vdot':
                body=loop([custom(10+i) for i in range(unroll)],n,scenario.replace('-','_')+'_vdot')
                ops=[('dot',10+i,8,9) for _ in range(n) for i in range(unroll)]; scratch=()
            else:
                step=batched() if unroll==4 else general(known=scenario=='known-config')
                body=loop(step,n,scenario.replace('-','_')+'_rvv')
                ops=[('dot',10+i,8,9) for _ in range(n) for i in range(unroll)]
                scratch=(4,*range(16,28)) if unroll==4 else (2,3,4,5)
            # Counts are raw, enclosing the result stores + fence, with no overhead subtraction.
            measured=['  la t5, t12_counts','  fence rw, rw','  csrr a5, cycle','  csrr a6, instret']+body
            measured += ['  la t0, t12_sink']
            for i in range(unroll):
                measured += [f'  vs1r.v v{10+i}, (t0)','  addi t0, t0, 16']
            measured += ['  fence rw, rw','  csrr a7, instret','  csrr t1, cycle',
                         '  sd a5, 0(t5)','  sd t1, 8(t5)','  sd a6, 16(t5)','  sd a7, 24(t5)']
            add(f'perf-{scenario}-{method}',measured,ops,kind='perf',scenario=scenario,method=method,
                scratch=scratch,dots=0 if method=='empty' else n*unroll,
                before=fixture([-128]*8,[127]*8))
    return rows

def cbytes(values):
    return '{'+','.join('{'+','.join('0x'+v[i:i+2] for i in range(0,32,2))+'}' for v in values)+'}'

def schedule(rows):
    result=[dict(id=r['id'],repeat=0) for r in rows if r['kind']!='perf']
    for scenario in ('complete','known-config','independent-batch'):
        result.append(dict(id=f'perf-{scenario}-empty',repeat=0))
        for repeat in range(REPEATS):
            for method in (('vdot','rvv') if repeat%2==0 else ('rvv','vdot')):
                result.append(dict(id=f'perf-{scenario}-{method}',repeat=repeat))
    return result

def generate(output):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    rows=corpus()
    asm=['/* T12 generated; no printing inside instruction sequences. */','#include "layout.h"','.option norvc','.text']
    header=['#ifndef T12_CASES_H','#define T12_CASES_H',
            'struct t12_case { const char *id; void (*entry)(void); const char *fault; unsigned kind, scratch; int fault_vl; const char *scenario, *method; unsigned dots; unsigned char before[32][16], expected[32][16]; };']
    records=[]
    for row in rows:
        name='t12_'+row['id'].replace('-','_')
        header += [f'extern void {name}(void);']
        fault=row['id'].replace('-','_')+'_fault' if row['fault_vl'] is not None else '0'
        if fault!='0': header += [f'extern const char {fault}[];']
        asm += [f'.globl {name}',f'.type {name}, @function',f'{name}:','  csrr t0, mstatus','  sd t0, REC_PRE_STATUS(s0)']
        asm += row['body']+['  j vdot_observe',f'.size {name}, .-{name}']
        mask=sum(1<<r for r in row['scratch'])
        kind={'stress':0,'equivalence':1,'perf':2}[row['kind']]
        vl=-1 if row['fault_vl'] is None else row['fault_vl']
        records.append('{'+f'"{row["id"]}",{name},{fault},{kind},0x{mask:08x}U,{vl},"{row["scenario"]}","{row["method"]}",{row["dots"]},'+cbytes(row['before'])+','+cbytes(row['expected'])+'}')
    plan=schedule(rows)
    indexes={r['id']:i for i,r in enumerate(rows)}
    header += ['static const struct t12_case t12_cases[] = {',',\n'.join(records),'};',f'#define T12_REPEATS {REPEATS}',
               f'#define T12_PLAN_COUNT {len(plan)}',
               'static const struct { unsigned index, repeat; } t12_plan[] = {',
               ','.join('{'+str(indexes[p['id']])+','+str(p['repeat'])+'}' for p in plan),'};', '#endif']
    for name,data in [('t12-sites.S','\n'.join(asm)+'\n'),('cases.h','\n'.join(header)+'\n'),('cases.json',json.dumps(rows,sort_keys=True,indent=2)+'\n'),('cases.jsonl',''.join(json.dumps(row,sort_keys=True)+'\n' for row in rows))]:
        (output/name).write_bytes(data.encode())
    manifest=dict(contract=CONTRACT,seed=SEED,repeats=REPEATS,schedule=plan,
                  generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()})
    (output/'manifest.json').write_bytes((json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode())
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); print(json.dumps(generate(a.output),sort_keys=True))
