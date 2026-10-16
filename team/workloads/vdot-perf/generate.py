"""Generate T13 source-bound equivalence tests and paired performance plans.

The lean RVV sequence derives from zufan f090665's generate_t12.py. This
generator independently computes every expected byte and declares scratch.
No observed cycle count or DUT output contributes to the expected results.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = 'vdot-s8x8-r32-v0.1'
SEED = 0x20261015
START = 0x51300013
STOP = 0x51400013


def dot(a, b):
    def signed(x):
        return x if x < 128 else x - 256
    total = sum(signed(x) * signed(y) for x, y in zip(a[:8], b[:8]))
    return (total & 0xffffffff).to_bytes(4, 'little') + bytes(12)


def vdot(d, a, b):
    return f'.word 0x{0x0200000b | d << 7 | a << 15 | b << 20:08x}'


def rvv(d, a, b, generic=False):
    if {2, 3} & {d, a, b}:
        raise ValueError('reserved RVV scratch overlaps operands')
    result = ['csrr t3, vl', 'csrr t4, vtype'] if generic else []
    result += [f'vwmul.vv v2, v{a}, v{b}',
               'vsetivli zero, 8, e16, m1, tu, mu',
               f'vmv.v.i v{d}, 0', f'vwredsum.vs v{d}, v2, v{d}']
    return result + (['vsetvl zero, t3, t4'] if generic else
                     ['vsetivli zero, 8, e8, m1, tu, mu'])


def batch():
    result = [f'vwmul.vv v{16+2*i}, v8, v9' for i in range(4)]
    result += ['vsetivli zero, 8, e16, m1, tu, mu']
    for i in range(4):
        result += [f'vmv.v.i v{10+i}, 0',
                   f'vwredsum.vs v{10+i}, v{16+2*i}, v{10+i}']
    return result + ['vsetivli zero, 8, e8, m1, tu, mu']


def initial(a, b):
    regs = [bytes((0x35 + 7*r + 19*i) & 255 for i in range(16))
            for r in range(32)]
    regs[8], regs[9] = a, b
    return regs


def dataset_pair(dataset):
    values = [([-128]*8, [-128]*8), ([-128]*8, [127]*8),
              ([1, -2, 3, -4, 5, -6, 7, -8], [8, 7, 6, 5, 4, 3, 2, 1])]
    a, b = values[dataset]
    return bytes(x & 255 for x in a) + bytes([0xa5]*8), \
        bytes(x & 255 for x in b) + bytes([0x5a]*8)


def case(name, scenario, method, n, a, b, *, operands=(10, 8, 9), vtype=0):
    d, s1, s2 = operands
    regs = initial(a, b)
    before = list(regs)
    body = []
    scratch = []
    stream = []
    outputs = []
    if scenario == 'calibration-nop':
        body = ['addi t2, t2, 1'] * n
        iterations = 0
    elif scenario == 'calibration-div':
        body = ['li t1, 7', 'li t2, 99991'] + ['div t2, t2, t1'] * n
        iterations = 0
    else:
        iterations = n
        if scenario == 'batch':
            step = [vdot(10+i, 8, 9) for i in range(4)] if method == 'vdot' else batch()
            if method == 'rvv':
                scratch = list(range(16, 24))
            for i in range(4):
                regs[10+i] = dot(regs[8], regs[9])
        else:
            if scenario == 'chain':
                s1 = d
            step = [vdot(d, s1, s2)] if method == 'vdot' else rvv(d, s1, s2, scenario in ('generic', 'equivalence'))
            if method == 'rvv':
                scratch = [2, 3]
            if scenario == 'stream':
                rng = random.Random(SEED + n + int.from_bytes(a[:2], 'little'))
                for i in range(n):
                    x, y = (a, b) if i % 8 == 0 else (rng.randbytes(16), rng.randbytes(16))
                    stream.extend([x, y])
                    outputs.append(dot(x, y))
                step = ['vl1re8.v v8, (a2)', 'addi a2, a2, 16',
                        'vl1re8.v v9, (a2)', 'addi a2, a2, 16'] + step + \
                       ['vs1r.v v10, (a3)', 'addi a3, a3, 16']
                regs[8], regs[9], regs[10] = stream[-2], stream[-1], outputs[-1]
            else:
                for _ in range(n):
                    regs[d] = dot(regs[s1], regs[s2])
        body = [f'li t6, {n}', '.Lloop:'] + step + \
               ['addi t5, t5, 1', 'addi t6, t6, -1', 'bnez t6, .Lloop']
    dots = 0 if scenario.startswith('calibration') else n*(4 if scenario == 'batch' else 1)
    return dict(id=name, scenario=scenario, method=method, n=n, iterations=iterations,
                dots=dots, operands=list(operands), vtype=vtype, scratch=scratch,
                before=[x.hex() for x in before], expected=[x.hex() for x in regs],
                stream=[x.hex() for x in stream], outputs=[x.hex() for x in outputs], body=body)


def corpus(suite, dataset):
    rows = []
    plan = []
    a, b = dataset_pair(dataset)

    def pair(scenario, n, x=a, y=b, tag='', operands=(10, 8, 9), vtype=0, rounds=1):
        indexes = {}
        for method in ('vdot', 'rvv'):
            name = f'{scenario}-{n}-{tag}-{method}'.replace('--', '-')
            indexes[method] = len(rows)
            rows.append(case(name, scenario, method, n, x, y, operands=operands, vtype=vtype))
        for repeat in range(rounds):
            phase = 'functional' if suite == 'functional' else (
                'first' if repeat == 0 else 'warmup' if repeat == 1 else 'measured')
            for method in (('vdot', 'rvv') if repeat % 2 == 0 else ('rvv', 'vdot')):
                plan.append(dict(index=indexes[method], repeat=repeat, phase=phase))

    if suite == 'smoke':
        for name, count in [('calibration-nop', 0), ('calibration-nop', 8), ('calibration-div', 32)]:
            plan.append(dict(index=len(rows), repeat=0, phase='calibration'))
            rows.append(case(f'{name}-{count}', name, 'control', count, a, b))
        for scenario in ('single', 'chain', 'batch', 'stream', 'generic'):
            pair(scenario, 1 if scenario == 'single' else 4, vtype=192 if scenario == 'generic' else 0)
    elif suite == 'functional':
        data = ROOT/'team/models/vdot/data'
        vectors = [json.loads(line) for line in (data/'directed.jsonl').read_text().splitlines()]
        vectors += [json.loads(line) for line in (data/'random.jsonl').read_text().splitlines()[:32]]
        aliases = [(10,8,9), (8,8,9), (9,8,9), (10,8,8), (8,8,8), (0,8,9), (31,8,9)]
        for i, vector in enumerate(vectors):
            x = int(vector['vs1'], 16).to_bytes(16, 'little')
            y = int(vector['vs2'], 16).to_bytes(16, 'little')
            pair('equivalence', 1, x, y, tag=vector['id'], operands=aliases[i % len(aliases)], vtype=(i%4)*64)
    elif suite == 'performance':
        for scenario, sizes in [('single', (1,)), ('chain', (16,64,256)),
                                ('batch', (1,8,32)), ('stream', (1,16,64)),
                                ('generic', (1,16,64))]:
            for n in sizes:
                pair(scenario, n, vtype=192 if scenario == 'generic' else 0, rounds=6)
    else:
        raise ValueError('unknown suite')
    for seq, item in enumerate(plan):
        item.update(seq=seq, id=rows[item['index']]['id'])
    return rows, plan


def array(values):
    return '{' + ','.join('{'+','.join('0x'+v[i:i+2] for i in range(0,32,2))+'}' for v in values) + '}'


def generate(output, suite, dataset, shard=0, shards=1, shared_stream=False):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    rows, plan = corpus(suite, dataset)
    # Keep paired methods and all repeat phases together in the same shard.
    if not 0 <= shard < shards:
        raise ValueError('invalid shard')
    selected = [p for p in plan if (p['index']//2) % shards == shard] if shards > 1 else plan
    used = sorted({p['index'] for p in selected})
    rows = [rows[i] for i in used]
    plan = [dict(p, index=used.index(p['index']), source_seq=p['seq'], seq=i)
            for i, p in enumerate(selected)]
    if not plan:
        raise ValueError('empty shard')
    asm = ['.option norvc', '.text']
    header = ['#ifndef T13_CASES_H', '#define T13_CASES_H',
              'typedef void (*entry_t)(const void *, void *, const void *, void *);',
              'struct t13_case { const char *id, *scenario, *method; entry_t entry; unsigned iterations, dots, scratch, vtype, stream_count, dest; const unsigned char (*stream)[16], (*outputs)[16]; _Alignas(16) unsigned char before[32][16], expected[32][16]; };']
    records = []
    stream_names = {}
    for index, row in enumerate(rows):
        name = f't13_kernel_{index}'
        header.append(f'extern void {name}(const void *, void *, const void *, void *);')
        stream_key = tuple(row['stream']) if shared_stream else (index,)
        if stream_key not in stream_names:
            stream_names[stream_key] = f'stream_{index}'
            alignment = '_Alignas(64) ' if shared_stream else ''
            header.append(f'{alignment}static const unsigned char stream_{index}[][16] = '+array(row['stream'] or ['00'*16])+';')
        stream_name = stream_names[stream_key]
        header.append(f'static const unsigned char outputs_{index}[][16] = '+array(row['outputs'] or ['00'*16])+';')
        pre = ['li t0, 0x6600', 'csrs mstatus, t0', 'csrwi vstart, 0', 'csrwi vcsr, 7',
               'vsetivli zero, 16, e8, m1, tu, mu']
        pre += ['mv t0, a0']
        for reg in range(32):
            pre += [f'vl1re8.v v{reg}, (t0)', 'addi t0, t0, 16']
        pre += ['li t1, 8', f'li t2, {row["vtype"]}', 'vsetvl zero, t1, t2',
                'li t5, 0', 'fence rw, rw', f'.word 0x{START:08x}',
                'fence rw, rw', 'csrr a4, instret', 'fence rw, rw',
                'csrr a6, cycle', 'fence rw, rw']
        body = [line.replace('.Lloop', f'.Lloop_{index}') for line in row['body']]
        post = ['fence rw, rw', 'csrr a7, cycle', 'fence rw, rw',
                'csrr a5, instret', 'fence rw, rw',
                f'.word 0x{STOP:08x}', 'fence rw, rw',
                'sd a6, 0(a1)', 'sd a7, 8(a1)', 'sd a4, 16(a1)', 'sd a5, 24(a1)', 'sd t5, 32(a1)']
        for i, csr in enumerate(('vtype','vl','vstart','vxrm','vxsat','vcsr','mcountinhibit')):
            post += [f'csrr t0, {csr}', f'sd t0, {40+8*i}(a1)']
        post += ['addi t0, a1, 128']
        for reg in range(32):
            post += [f'vs1r.v v{reg}, (t0)', 'addi t0, t0, 16']
        post += ['ret']
        asm += ['.balign 64', f'.global {name}', f'.type {name}, @function', name+':']
        asm += ['  '+line for line in pre+body+post]
        asm += [f'.size {name}, .-{name}']
        mask = sum(1 << i for i in row['scratch'])
        records.append('{'+f'"{row["id"]}","{row["scenario"]}","{row["method"]}",{name},'+
                       f'{row["iterations"]},{row["dots"]},{mask}U,{row["vtype"]},{len(row["outputs"])},{row["operands"][0]},{stream_name},outputs_{index},'+
                       array(row['before'])+','+array(row['expected'])+'}')
    header += ['static const struct t13_case cases[] = {', ',\n'.join(records), '};',
               'static const struct { unsigned index, repeat; const char *phase; } plan[] = {',
               ',\n'.join('{'+f'{p["index"]},{p["repeat"]},"{p["phase"]}"'+'}' for p in plan), '};',
               f'#define T13_PLAN_COUNT {len(plan)}', f'#define T13_SUITE "{suite}"',
               f'#define T13_DATASET {dataset}',
               f'#define T13_COMPACT {int(suite == "performance")}', '#endif']
    (out/'kernels.S').write_bytes(('\n'.join(asm)+'\n').encode())
    (out/'cases.h').write_bytes(('\n'.join(header)+'\n').encode())
    manifest = dict(contract=CONTRACT, seed=SEED, suite=suite, dataset=dataset,
                    baseline_source='f090665130107282be0990a7664aebf26e491b87',
                    shard=shard, shards=shards, compact=suite == 'performance',
                    boundary='pinned-XiangShan-fence-serialized-v2',
                    shared_stream=shared_stream,
                    rows=rows, plan=plan, files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()})
    (out/'manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode())
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--suite', choices=('smoke','functional','performance'), required=True)
    parser.add_argument('--dataset', type=int, choices=(0,1,2), default=0)
    parser.add_argument('--shard', type=int, default=0)
    parser.add_argument('--shards', type=int, default=1)
    parser.add_argument('--shared-stream', action='store_true')
    args = parser.parse_args()
    result = generate(args.output, args.suite, args.dataset, args.shard, args.shards, args.shared_stream)
    print(json.dumps({'suite':args.suite, 'dataset':args.dataset, 'rows':len(result['rows']), 'plan':len(result['plan'])}))
