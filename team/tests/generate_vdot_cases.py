"""Deterministic T05 inputs, full-width expectations and workload headers."""

import argparse
import hashlib
import json
from pathlib import Path

from vdot_model import CONTRACT_ID, MODEL_VERSION, VectorState, dot_s8, encode, execute

GENERATOR_VERSION = "1.3.0"
SEED = 0x20261011
DIRECTED = [
    ("D00", [0]*8, [127]*8, 0),
    ("D01", [1]*8, [1]*8, 8),
    ("D02", list(range(1, 9)), list(range(1, 9)), 204),
    ("D03", [-1]*8, [1]*8, -8),
    ("D04", [-1]*8, [-1]*8, 8),
    ("D05", [127]*8, [127]*8, 129032),
    ("D06", [-128]*8, [127]*8, -130048),
    ("D07", [-128]*8, [-128]*8, 131072),
    ("D08", [1,-2,3,-4,5,-6,7,-8], [8,7,6,5,4,3,2,1], 0),
    ("D09", [-128]+[0]*7, [-1]+[0]*7, 128),
    ("D10", [0]*7+[-128], [0]*7+[127], -16256),
]


def packed(lanes, tail=bytes([0xA5]*8)):
    if len(lanes) != 8 or len(tail) != 8:
        raise ValueError("8 participating bytes and 8 ignored bytes required")
    return int.from_bytes(bytes(x & 255 for x in lanes) + tail, "little")


def case(test_id, a, b, *, vd=10, vs1=8, vs2=9, vtype=0, vxrm=0, vxsat=0, vs=1,
         old=int.from_bytes(bytes([255]*16), "little"), tags=()):
    # Overlapping source registers must refer to one actual pre-instruction value.
    if vs1 == vs2:
        b = a
    regs = [int.from_bytes(bytes([0x55,0xAA]*8), "little")] * 32
    regs[vd] = old
    regs[vs1], regs[vs2] = a, b
    before = VectorState(regs=tuple(regs), vtype=vtype, vxrm=vxrm, vxsat=vxsat, vs=vs)
    outcome = execute(encode(vd, vs1, vs2), before)
    if outcome.cause is not None:
        raise ValueError("legal data generator received illegal state")
    src1, src2 = before.regs[vs1], before.regs[vs2]
    word = encode(vd, vs1, vs2)
    return dict(id=test_id, contract_id=CONTRACT_ID, tags=list(tags),
                vd=vd, vs1=vs1, vs2=vs2, instruction=f"0x{word:08x}",
                instruction_le=word.to_bytes(4,"little").hex(),
                src1_128=f"{src1:032x}", src2_128=f"{src2:032x}",
                old_vd_128=f"{before.regs[vd]:032x}",
                expected_128=f"{outcome.state.regs[vd]:032x}",
                expected_signed=dot_s8(*[[int.from_bytes(bytes([x]),'little',signed=True)
                                        for x in s.to_bytes(16,'little')[:8]]
                                       for s in (src1,src2)]),
                config=dict(vl=8,vtype=vtype,vstart=0,vs=vs,vxrm=vxrm,vxsat=vxsat))


def directed_cases():
    cases = []
    for name, a, b, total in DIRECTED:
        c = case(name, packed(a), packed(b), tags=("directed",))
        if c["expected_signed"] != total:
            raise ValueError(f"independent documented expectation disagrees: {name}")
        cases.append(c)
    for lane in range(8):
        a = [0]*8
        a[lane] = -128 if lane % 2 else 127
        cases.append(case(f"L01-{lane}",packed(a),packed(list(range(1,9))),tags=("lane",)))
    for i, tail in enumerate((bytes(8), bytes([255]*8), bytes([0x55,0xAA]*4))):
        cases.append(case(f"L02-{i}",packed([-1]*8,tail),packed([1]*8,tail),tags=("ignored-high",)))
    for vd, vs1, vs2 in ((8,8,9),(9,8,9),(10,8,8),(8,8,8),
                         (0,8,9),(10,0,9),(10,8,0),(0,0,9),
                         (31,31,31),(31,8,9)):
        cases.append(case(f"L04-{vd}-{vs1}-{vs2}",packed([-1]*8),packed([1]*8),
                          vd=vd,vs1=vs1,vs2=vs2,tags=("alias", "v0" if 0 in (vd,vs1,vs2) else "register")))
    for policy in range(4):
        for old_name, old in (("ff",(1<<128)-1),("aa55",int.from_bytes(bytes([0xAA,0x55]*8),'little'))):
            cases.append(case(f"L05-{policy}-{old_name}",packed([-1]*8),packed([1]*8),
                              vtype=policy<<6,old=old,tags=("policy","full-width")))
    for vxrm in range(4):
        for vxsat in range(2):
            cases.append(case(f"S01-{vxrm}-{vxsat}",packed([-128]*8),packed([-128]*8),
                              vxrm=vxrm,vxsat=vxsat,tags=("csr",)))
    return cases


def random_cases(count, seed=SEED, random_registers=False):
    if not 0 < seed < 1 << 32 or count < 0:
        raise ValueError("nonzero uint32 seed and nonnegative count required")
    state = seed
    def byte():
        nonlocal state
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        state &= 0xFFFFFFFF
        return state & 255
    for i in range(count):
        a, b, old = [int.from_bytes(bytes(byte() for _ in range(16)),"little") for _ in range(3)]
        registers = dict(vd=byte()&31,vs1=byte()&31,vs2=byte()&31,vs=i%3+1) if random_registers else {}
        yield case(f"R{i:05d}",a,b,old=old,vtype=(i%4)<<6,vxrm=i%4,vxsat=i%2,tags=("random",),**registers)


def expanded_cases():
    rows=[]
    a,b=packed([-128,127,-1,1,2,-2,63,-64]),packed([127,-128,1,-1,-2,2,-64,63])
    for reg in range(32):
        other,third=(reg+1)%32,(reg+2)%32
        for index,regs in enumerate(((reg,other,third),(reg,reg,other),(reg,other,reg),
                                     (other,reg,reg),(reg,reg,reg))):
            rows.append(case(f'G{reg:02d}-{index}',a,b,vd=regs[0],vs1=regs[1],vs2=regs[2],
                             tags=('register-layout',),vs=index%3+1))
    for policy in range(4):
        for vxrm in range(4):
            for vxsat in range(2):
                for vs in (1,2,3):
                    rows.append(case(f'C{policy}-{vxrm}-{vxsat}-{vs}',a,b,vtype=policy<<6,
                                     vxrm=vxrm,vxsat=vxsat,vs=vs,tags=('csr-cross','vs-transition')))
    return rows


def jsonl(cases):
    return ''.join(json.dumps(c,sort_keys=True,separators=(',',':'))+'\n' for c in cases).encode()


def c_bytes(value):
    return '{'+','.join(f'0x{x:02x}' for x in int(value,16).to_bytes(16,'little'))+'}'


def exception_cases():
    rows = []
    def add(name, *, vtype=0, vl=8, vstart=0, vxrm=0, vxsat=0, vs_off=0,
            vd=10, vs1=8, vs2=9, flip=0, alternating=0, vs=3):
        rows.append(dict(id=name,vtype=vtype,vl=vl,vstart=vstart,vxrm=vxrm,vxsat=vxsat,
                         vs_off=vs_off,vd=vd,vs1=vs1,vs2=vs2,word=encode(vd,vs1,vs2)^flip,
                         alternating=alternating,vs=vs,expected_cause=2,
                         model_class='not-vdot' if flip else 'illegal-config'))
    add('X01-e16',vtype=8)
    add('X02-m2',vtype=1)
    add('X02-mf2',vtype=7)
    for vl in (0,1,7,9,16): add(f'X03-vl{vl}',vl=vl)
    for vstart in (1,7): add(f'X04-vstart{vstart}',vstart=vstart)
    add('X05-vill',vtype=0x100)
    add('X06-VS-off',vs_off=1)
    add('X07-vm0',flip=1<<25)
    for bit in (26,27,28,29,30,31,12,13,14): add(f'X08-f{bit}',flip=1<<bit)
    for name,regs in (('vd-vs1',(8,8,9)),('vd-vs2',(9,8,9)),('v0',(0,0,9)),
                      ('v31',(31,31,31)),('nonalias',(10,8,9))):
        add('X09-'+name,vl=7,vd=regs[0],vs1=regs[1],vs2=regs[2])
    for vxrm in range(4):
        for vxsat in range(2):
            add(f'X10-{vxrm}-{vxsat}',vl=7,vxrm=vxrm,vxsat=vxsat,alternating=1)
    for vs in (1,2): add(f'X11-VS-{vs}',vl=7,vs=vs)
    return rows


def emit_header(cases, exceptions=None):
    rows = []
    for c in cases:
        cfg = c['config']
        rows.append('  {"%s", %sU, %d, %d, %d, %d, %d, %d, %d, %s, %s, %s, %s}' %
                    (c['id'],c['instruction'],c['vd'],c['vs1'],c['vs2'],cfg['vtype'],cfg['vxrm'],cfg['vxsat'],cfg['vs'],
                     *(c_bytes(c[k]) for k in ('src1_128','src2_128','old_vd_128','expected_128'))))
    exceptions = exception_cases() if exceptions is None else exceptions
    erows = []
    for c in exceptions:
        erows.append('  {"%s", %s}' % (c['id'],', '.join(str(c[k])+('U' if k=='word' else '')
            for k in ('vtype','vl','vstart','vxrm','vxsat','vs_off','word','vd','vs1','vs2','alternating','vs'))))
    return ('/* Generated by generate_vdot_cases.py; do not edit. */\n'
            '#ifndef VDOT_CASES_H\n#define VDOT_CASES_H\n'
            f'#define VDOT_CONTRACT "{CONTRACT_ID}"\n'
            'struct arithmetic_case { const char *id; unsigned word, vd, vs1, vs2, vtype, vxrm, vxsat, vs; '
            'unsigned char a[16], b[16], old[16], expected[16]; };\n'
            'static const struct arithmetic_case arithmetic_cases[] = {\n'+',\n'.join(rows)+'\n};\n'
            '#define ARITHMETIC_COUNT (sizeof(arithmetic_cases)/sizeof(arithmetic_cases[0]))\n'
            'struct exception_case { const char *id; unsigned vtype, vl, vstart, vxrm, vxsat, vs_off, '
            'word, vd, vs1, vs2, alternating, vs; };\n'
            'static const struct exception_case exception_cases_data[] = {\n'+',\n'.join(erows)+'\n};\n'
            '#define EXCEPTION_COUNT (sizeof(exception_cases_data)/sizeof(exception_cases_data[0]))\n#endif\n')


def emit_stubs(cases, exceptions=None):
    exceptions = exception_cases() if exceptions is None else exceptions
    base = encode(10,8,9)
    words = sorted({int(c['instruction'],16) for c in cases} | {c['word'] for c in exceptions} |
                   {base ^ (1<<bit) for bit in (25,26,27,28,29,30,31,12,13,14)} |
                   {0x00100073,0x02940557})
    asm = ['/* Generated fixed 32-bit fault sites. */','#include "layout.h"',
           '.option norvc','.text']
    header = ['/* Generated instruction dispatch. */','#ifndef VDOT_STUBS_H','#define VDOT_STUBS_H']
    for word in words:
        name = f'vdot_word_{word:08x}'
        header.append(f'extern void {name}(void);')
        asm.extend([f'.globl {name}',f'.type {name}, @function',f'{name}:',
                    '  la t0, 1f','  ld t1, CFG_PC_BIAS(s1)','  add t0, t0, t1',
                    '  sd t0, REC_EXPECTED_PC(s0)','  la t0, 2f','  sd t0, REC_RESUME_PC(s0)',
                    '  csrr t0, mstatus','  sd t0, REC_PRE_STATUS(s0)',
                    '  li t0, 1','  sd t0, REC_ARMED(s0)',f'1: .word 0x{word:08x}',
                    '2: j vdot_observe',f'.size {name}, .-{name}'])
    header.append('static void (*find_stub(unsigned word))(void) { switch (word) {')
    header.extend(f'case 0x{word:08x}U: return vdot_word_{word:08x};' for word in words)
    header.extend(['default: return 0; } }','#endif'])
    return '\n'.join(asm)+'\n','\n'.join(header)+'\n'


def write_text(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data.encode('utf-8') if isinstance(data,str) else data)


def generate(output, count, seed, smoke_random_count=32, coverage_profile='legacy', shard_index=0, shard_count=1):
    if smoke_random_count < 0:
        raise ValueError('nonnegative smoke random count required')
    if coverage_profile not in ('legacy','expanded'):
        raise ValueError('unsupported coverage profile')
    directed = directed_cases() + (expanded_cases() if coverage_profile=='expanded' else [])
    random = list(random_cases(count, seed,random_registers=coverage_profile=='expanded'))
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError('shard_count must be positive and shard_index within range')
    full_smoke = directed+random[:smoke_random_count]
    all_exceptions = exception_cases()
    if shard_count > len(all_exceptions):
        raise ValueError('each shard must contain at least one exception case')
    smoke = full_smoke
    exceptions = all_exceptions
    corpus = directed+random
    shard = None
    if shard_count != 1:
        # Every shard proves at least one legitimate vdot before any illegal
        # instruction claims. Apart from D00, partition rather than duplicate.
        if full_smoke[0]['id'] != 'D00':
            raise ValueError('missing legal D00 control')
        smoke = [full_smoke[0]]+[c for i,c in enumerate(full_smoke)
                                if i % shard_count == shard_index and c['id'] != 'D00']
        exceptions = [c for i,c in enumerate(all_exceptions) if i % shard_count == shard_index]
        corpus = smoke
        plan = json.dumps(dict(legal=full_smoke,exceptions=all_exceptions),
                          sort_keys=True,separators=(',',':')).encode()
        shard = dict(index=shard_index,count=shard_count,legal_control='D00',
                     requested_random_count=count,requested_smoke_random_count=smoke_random_count,
                     parent_legal_count=len(full_smoke),parent_exception_count=len(all_exceptions),
                     parent_plan_sha256=hashlib.sha256(plan).hexdigest())
    data = jsonl(corpus)
    write_text(output/'cases.jsonl',data)
    write_text(output/'cases.h',emit_header(smoke,exceptions))
    asm,header = emit_stubs(smoke,exceptions)
    write_text(output/'word-sites.S',asm)
    write_text(output/'stubs.h',header)
    write_text(output/'exceptions.json',json.dumps(exceptions,sort_keys=True,indent=2)+'\n')
    sources = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (Path(__file__),Path(__file__).with_name('vdot_model.py'))}
    manifest = dict(contract_id=CONTRACT_ID,model_version=MODEL_VERSION,generator_version=GENERATOR_VERSION,
                    prng='xorshift32-v1-low-byte',seed=f'0x{seed:08x}',random_count=count,
                    directed_count=len(directed),total=len(directed)+count,smoke_count=len(smoke),
                    byte_order='little',register_hex_order='most-significant-byte-first',source_sha256=sources,
                    cases_sha256=hashlib.sha256(data).hexdigest(),exception_count=len(exceptions))
    if shard:
        manifest['shard']=shard
        manifest['random_count']=sum('random' in c['tags'] for c in corpus)
        manifest['directed_count']=len(corpus)-manifest['random_count']
        manifest['total']=len(corpus)
    manifest['coverage_profile']=coverage_profile
    manifest['coverage'] = dict(operand_registers=sorted({c[k] for c in smoke for k in ('vd','vs1','vs2')}),
        operand_tuple_count=len({(c['vd'],c['vs1'],c['vs2']) for c in smoke}),
        policy_vxrm_vxsat_vs_count=len({(c['config']['vtype'],c['config']['vxrm'],c['config']['vxsat'],c['config']['vs']) for c in smoke}),
        initial_vs=sorted({c['config']['vs'] for c in smoke}))
    manifest['artifacts_sha256'] = {name:hashlib.sha256((output/name).read_bytes()).hexdigest()
                                  for name in ('cases.jsonl','cases.h','word-sites.S','stubs.h','exceptions.json')}
    write_text(output/'manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'out/t05')
    parser.add_argument('--random-count',type=int,default=10000)
    parser.add_argument('--seed',type=lambda s:int(s,0),default=SEED)
    parser.add_argument('--smoke-random-count',type=int,default=32)
    parser.add_argument('--coverage-profile',choices=('legacy','expanded'),default='legacy')
    parser.add_argument('--shard-index',type=int,default=0)
    parser.add_argument('--shard-count',type=int,default=1)
    args = parser.parse_args()
    print(json.dumps(generate(args.output,args.random_count,args.seed,args.smoke_random_count,args.coverage_profile,args.shard_index,args.shard_count),sort_keys=True))
