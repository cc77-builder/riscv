"""Generate a guarded paired-product RVV full-Q candidate.

The fixed parent, public assembly, reference paths, and production hardware
remain read-only. The guard and safe fallback are inside the timed function.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused')
PARENT_SHA = 'b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b'
PUBLIC_SHA = '9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2'
NAME = 'q288_paired16_rvv'
CONTRACT = 'r2-s3-runq-paired16-rvv-screen-v1'
CORE_WORDS = 45


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_parent(repo):
    path = repo / REL / 'generate.py'
    need(sha(path.read_bytes()) == PARENT_SHA, 'unchanged full-Q parent generator')
    spec = importlib.util.spec_from_file_location('paired16_pinned_parent', path)
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    raw = (repo / parent.PUBLIC).read_bytes()
    need(sha(raw) == PUBLIC_SHA, 'unchanged public RVV assembly')
    return parent, raw.decode()


def integer_core():
    # Fixed VLEN128: a whole two-register load reads 32B independently of VL16.
    # v8/v9 remain live FP accumulators; v12/13 and v14/15 are integer scratch.
    text = '  vsetivli zero, 4, e32, m1, tu, mu\n  vmv.v.i v0, 0\n'
    text += '  vsetivli zero, 16, e8, m1, tu, mu\n  vl2re8.v v14, (a1)\n'
    for row in range(8):
        dest = 16 + 2 * row
        text += f'  addi t6, a2, {row*32}\n  vl2re8.v v12, (t6)\n'
        text += f'  vwmul.vv v{dest}, v12, v14\n'
        text += f'  vwmacc.vv v{dest}, v13, v15\n'
    text += '  vsetivli zero, 16, e16, m2, tu, mu\n'
    for row in (*range(1, 8), 0):
        text += f'  vwredsum.vs v{row}, v{16+2*row}, v0\n'
    need(len(text.splitlines()) == CORE_WORDS, '45-instruction paired integer core')
    return text


def body_of(source, name):
    before, sep, body = source.partition(name + ':\n')
    ending = f'.size {name}, .-{name}\n'
    need(sep and before.endswith(f'.type {name}, @function\n') and body.endswith(ending),
         'exact parent function envelope')
    return body[:-len(ending)]


def function(parent, public):
    old = parent.function(public, 'rvv4')
    old_core = parent.integer_core(public, 'rvv4')
    body = body_of(old, 'q288_fused_rvv4')
    need(body.count(old_core) == 1, 'unique fixed integer-core replacement')
    fast = body.replace(old_core, NAME+'_core_begin:\n'+integer_core()+NAME+'_core_end:\n')
    marker = '  vsetivli zero, 8, e32, m2, tu, mu\n.Ltile_rvv4:\n'
    need(fast.count(marker) == 1, 'one entry full-result initialization point')
    clear = ''.join(f'  vmv.v.i v{reg}, 0\n' for reg in (0, 2, 4, 6))
    fast = fast.replace(marker, marker.split('.Ltile_rvv4:')[0]+clear+'.Ltile_rvv4:\n')
    fast = fast.replace('.Ltile_rvv4', '.Ltile_paired16').replace('.Lgroup_rvv4', '.Lgroup_paired16')
    fallback = body.replace(old_core, NAME+'_fallback_core_begin:\n'+old_core+NAME+'_fallback_core_end:\n')
    fallback = fallback.replace('.Ltile_rvv4', '.Ltile_paired16_fallback').replace('.Lgroup_rvv4', '.Lgroup_paired16_fallback')
    # Scan every byte exactly once, even if an earlier chunk contains -128.
    # The exact VL32 uses register AVL because vsetivli cannot encode 32.
    guard = '''  csrwi vstart, 0
  csrwi vcsr, 7
  ld t0, 8(a0)
  li t1, 9
  li t4, 32
  li t5, -127
  vsetvli zero, t4, e8, m2, tu, mu
  li t4, 0
'''
    guard += NAME+'_guard_loop:\n'
    guard += '''  vle8.v v14, (t0)
  vmslt.vx v12, v14, t5
  vcpop.m t6, v12
  addw t4, t4, t6
  addi t0, t0, 32
  addi t1, t1, -1
'''
    guard += f'  bnez t1, {NAME}_guard_loop\n'
    guard += NAME+'_guard_dispatch:\n'
    guard += f'  bnez t4, {NAME}_fallback_begin\n'
    return (f'.balign 64\n.global {NAME}\n.type {NAME}, @function\n{NAME}:\n'
            +guard+NAME+'_fast_begin:\n'+fast+NAME+'_fast_end:\n'
            +NAME+'_fallback_begin:\n'+fallback+NAME+'_fallback_end:\n'
            +f'.size {NAME}, .-{NAME}\n')


def generate(repo, out):
    parent, public = load_parent(repo)
    need(not out.exists(), 'fresh independent generation directory')
    baseline = parent.function(public, 'rvv4')
    candidate = function(parent, public)
    source = '.option norvc\n.option norelax\n.text\n'+baseline+candidate
    out.mkdir(parents=True)
    (out/'paired16.S').write_text(source)
    result = dict(contract=CONTRACT, source_sha256=sha(source.encode()),
                  parent_generator_sha256=PARENT_SHA, public_sha256=PUBLIC_SHA,
                  baseline='q288_fused_rvv4', candidate=NAME,
                  core_words=CORE_WORDS, guard_bytes=288, guard_chunks=9,
                  full_signed_int8_domain=True, layout_changed=False,
                  hardware_changed=False, target_runtime_qualified=False,
                  performance_qualified=False)
    (out/'generation.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.repo.resolve(), args.output.resolve()), indent=2))
