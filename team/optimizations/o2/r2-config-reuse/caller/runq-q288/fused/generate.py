"""Generate separate full-Q implementations with strict lane-wise FP32 consumption.

The pinned team integer cores supply their arithmetic. Existing public assembly
is only read. New symbols inline its tile/group arithmetic and retain each
row's original group order; no source or instruction in the public library is
patched. This generator does not run an EMU or choose a performance winner.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

PUBLIC = Path('team/optimizations/o2/r2-config-reuse/public/gemv.S')
PUBLIC_SHA = '9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2'
FUNCTIONS = {'vdot':'q288_fused_vdot', 'rvv4':'q288_fused_rvv4'}


def need(ok, message):
    if not ok: raise ValueError(message)


def integer_core(public, kind):
    original = 'config_reuse_gemv_8x32_reuse_'+('vdot' if kind == 'vdot' else 'rvv')
    matches = re.findall(r'^'+original+r':\n(.*?)^\.size '+original+r',', public, re.M|re.S)
    need(len(matches) == 1, 'unique pinned source core')
    body = matches[0]
    head = '  mv a2, a0\n  mv a3, a1\n  csrwi vstart, 0\n  csrwi vcsr, 7\n'
    tail = '  vsetivli zero, 8, e8, m1, tu, mu\n  li t5, 256\n  mv t6, a3\n'
    tail += ''.join(f'  vs1r.v v{i}, (t6)\n  addi t6, t6, 16\n' for i in range(8))+'  ret\n'
    need(body.startswith(head) and body.endswith(tail), 'exact removed ABI/CSR/store sections')
    core = body[len(head):-len(tail)]
    if kind == 'rvv4':
        prefix = '  vsetivli zero, 8, e8, m1, tu, mu\n  vsetivli zero, 16, e8, m1, tu, mu\n'
        need(core.startswith(prefix), 'explicit redundant RVV setup')
        core = core[len(prefix.splitlines(True)[0]):]
    hits = []
    def x_address(match):
        offset = int(match[1]); need(offset in (256,264,272,280), 'qualified x offset')
        hits.append(offset)
        return '  addi t6, a1, '+str(offset-256)
    core = re.sub(r'  addi t6, a2, (2[5-8][0-9])(?=\n)', x_address, core)
    need(len(hits) == (4 if kind == 'vdot' else 2), 'all separated x addresses')
    need(not re.search(r'\b(?:v[89]|v1[0-5])\b', core), 'FP accumulator/scratch groups reserved')
    return core


def function(public, kind):
    name = FUNCTIONS[kind]
    code = f'.balign 64\n.global {name}\n.type {name}, @function\n{name}:\n'
    code += '''  ld a2, 0(a0)
  ld a7, 8(a0)
  ld a4, 16(a0)
  ld t0, 24(a0)
  ld a6, 32(a0)
  ld a3, 40(a0)
  csrwi vstart, 0
  csrwi vcsr, 7
  li t2, 36
  li t3, 36
  vsetivli zero, 8, e32, m2, tu, mu
'''
    code += f'.Ltile_{kind}:\n'
    code += '''  vmv.v.i v8, 0
  mv a1, a7
  mv a5, t0
  li t1, 9
'''
    code += f'.Lgroup_{kind}:\n'+integer_core(public, kind)
    if kind == 'rvv4': code += '  vsetivli zero, 4, e32, m1, tu, mu\n'
    for dst, first in ((10,0),(11,4)):
        code += f'  vmv.v.v v{dst}, v{first}\n'
        code += ''.join(f'  vslideup.vi v{dst}, v{first+i}, {i}\n' for i in (1,2,3))
    code += '''  vsetivli zero, 8, e32, m2, tu, mu
  vfcvt.f.x.v v10, v10
  vlse32.v v12, (a4), t3
  vfmul.vv v10, v10, v12
  flw ft0, 0(a5)
  vfmul.vf v10, v10, ft0
  vfadd.vv v8, v8, v10
  addi a2, a2, 256
  addi a1, a1, 32
  addi a4, a4, 4
  addi a5, a5, 4
  addi t1, t1, -1
'''
    code += f'  bnez t1, .Lgroup_{kind}\n'
    code += '''  vse32.v v8, (a6)
  addi a6, a6, 32
  addi a4, a4, 252
  addi t2, t2, -1
'''
    code += f'  bnez t2, .Ltile_{kind}\n'
    code += '  vsetivli zero, 8, e8, m1, tu, mu\n  mv t6, a3\n'
    code += ''.join(f'  vs1r.v v{i}, (t6)\n  addi t6, t6, 16\n' for i in range(8))
    code += f'  ret\n.size {name}, .-{name}\n'
    return code


def generate_text(public):
    return '.option norvc\n.option norelax\n.text\n'+''.join(function(public, kind) for kind in FUNCTIONS)


def generate(repo, out):
    raw = (repo/PUBLIC).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PUBLIC_SHA, 'immutable team source pin')
    out.mkdir(parents=True, exist_ok=False)
    source = generate_text(raw.decode())
    (out/'fused.S').write_text(source)
    result = dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  public_source_sha256=PUBLIC_SHA, functions=FUNCTIONS,
                  full_q=True, intermediate_slot_stores=0, final_slot_stores=8,
                  hardware_changed=False, performance_qualified=False)
    (out/'generation.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(generate(args.repo.resolve(), args.output.resolve()), indent=2))
