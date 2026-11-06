"""Generate a separate full-GS32 RVV consumer from the pinned full-Q shell.

Existing generators and public assembly are read only. This module generates
code; it neither selects the performance winner nor changes a stable entry.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused')
PARENT_SHA = 'b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b'
NAME = 'q288_gs32_rvv'
CONTRACT = 'r2-s3-runq-gs32-rvv-screen-v2'
CORE_WORDS = 39


def need(ok, message):
    if not ok:
        raise ValueError(message)


def load_parent(repo):
    path = repo / REL / 'generate.py'
    need(hashlib.sha256(path.read_bytes()).hexdigest() == PARENT_SHA,
         'unchanged full-Q shell generator')
    spec = importlib.util.spec_from_file_location('gs32_pinned_fullq_generator', path)
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    raw = (repo / parent.PUBLIC).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == parent.PUBLIC_SHA,
         'unchanged public RVV baseline assembly')
    return parent, raw.decode()


def integer_core():
    # All products and all 32 input lanes are active. v0 is a common zero
    # reduction seed until row 0 is written last. High tails were cleared at
    # function entry and every reduction preserves them with tu.
    code = '  vsetivli zero, 4, e32, m1, tu, mu\n'
    code += '  vmv.v.i v0, 0\n'
    code += '  vsetvli zero, t4, e8, m2, tu, mu\n'
    code += '  vle8.v v14, (a1)\n'
    for batch, rows in enumerate(((1, 2, 3, 4), (5, 6, 7, 0))):
        if batch:
            code += '  vsetvli zero, t4, e8, m2, tu, mu\n'
        for lane, row in enumerate(rows):
            code += f'  addi t6, a2, {row*32}\n'
            code += '  vle8.v v12, (t6)\n'
            code += f'  vwmul.vv v{16+4*lane}, v12, v14\n'
        code += '  vsetvli zero, t4, e16, m4, tu, mu\n'
        for lane, row in enumerate(rows):
            code += f'  vwredsum.vs v{row}, v{16+4*lane}, v0\n'
    need(len(code.splitlines()) == CORE_WORDS, 'shared-seed core instruction inventory')
    return code


def function(parent, public):
    before = parent.function(public, 'rvv4')
    old_core = parent.integer_core(public, 'rvv4')
    need(before.count(old_core) == 1, 'one explicit old integer-core boundary')
    core = NAME + '_core_begin:\n' + integer_core() + NAME + '_core_end:\n'
    after = before.replace(old_core, core)
    need(after.count('  li t3, 36\n') == 1, 'one scalar AVL initialization point')
    after = after.replace('  li t3, 36\n', '  li t3, 36\n  li t4, 32\n')
    marker = '  vsetivli zero, 8, e32, m2, tu, mu\n.Ltile_rvv4:\n'
    need(after.count(marker) == 1, 'one entry output-tail initialization point')
    clear = ''.join(f'  vmv.v.i v{reg}, 0\n' for reg in (0, 2, 4, 6))
    after = after.replace(marker, marker.split('.Ltile_rvv4:')[0]+clear+'.Ltile_rvv4:\n')
    after = after.replace('q288_fused_rvv4', NAME).replace('.Ltile_rvv4', '.Ltile_gs32').replace('.Lgroup_rvv4', '.Lgroup_gs32')
    return after


def generate(repo, out):
    parent, public = load_parent(repo)
    need(not out.exists(), 'fresh output directory')
    out.mkdir(parents=True)
    baseline = parent.function(public, 'rvv4')
    candidate = function(parent, public)
    source = '.option norvc\n.option norelax\n.text\n' + baseline + candidate
    (out / 'gs32.S').write_text(source)
    result = dict(contract=CONTRACT, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  baseline='q288_fused_rvv4', candidate=NAME,
                  parent_generator_sha256=PARENT_SHA, public_sha256=parent.PUBLIC_SHA,
                  integer_core_source_instructions=len(integer_core().splitlines()),
                  version='shared-zero-seed-v2',
                  standard_rvv_only=True, layout_changed=False,
                  hardware_changed=False, performance_qualified=False)
    (out / 'generation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(generate(args.repo.resolve(), args.output.resolve()), indent=2))
