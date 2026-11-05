"""One full-Q dot16 candidate beside unchanged dot8 and RVV functions.

The original packed P[t,g,row,k] format and strict FP32 consumer remain intact.
This generator emits new team assembly; it does not modify frozen sources.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import tempfile

PUBLIC = Path('team/optimizations/o2/r2-config-reuse/public/gemv.S')
PUBLIC_SHA = '9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2'
FUSED = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused')
FUSED_GEN_SHA = 'b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b'
TAIL = FUSED / 'phased/tail'
TAIL_GEN_SHA = '3a75e09640fdf789c11cf8a9050cd716ca3fde12732cb500f3f123adb0b50697'
NAME = 'q288_dot16_vdot'
CONTRACT = 'r3-dot16-v0.1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, path, pin):
    raw = path.read_bytes()
    need(sha(raw) == pin, 'fixed source ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    need(sha(path.read_bytes()) == pin, 'source changed during load')
    return module


def core():
    text = '  vsetivli zero, 16, e8, m1, ta, mu\n'
    text += '  vle8.v v16, (a1)\n  addi a1, a1, 16\n  vle8.v v17, (a1)\n'
    for half in range(2):
        for first in (0, 4):
            for slot in range(4):
                row = first + slot
                text += f'  addi t6, a2, {row * 32 + half * 16}\n'
                text += f'  vle8.v v{20 + slot}, (t6)\n'
            for slot in range(4):
                row = first + slot
                destination = row if half == 0 else 24 + row
                word = 0x0e00000b | (destination << 7) | ((20 + slot) << 15) | ((16 + half) << 20)
                text += f'  .word 0x{word:08x}\n'
    text += '  vsetivli zero, 4, e32, m1, tu, mu\n'
    for row in range(8):
        text += f'  vadd.vv v{row}, v{row}, v{24 + row}\n'
    need(len(text.splitlines()) == 61, '61-word integer core')
    return text


def generate(repo, out):
    need(not out.exists(), 'fresh generator output')
    public_raw = (repo / PUBLIC).read_bytes()
    need(sha(public_raw) == PUBLIC_SHA, 'fixed team public source')
    original = load('dot16_fixed_fusion', repo / FUSED / 'generate.py', FUSED_GEN_SHA)
    tail = load('dot16_fixed_tail', repo / TAIL / 'candidate.py', TAIL_GEN_SHA)
    public = public_raw.decode()
    before = original.function(public, 'vdot')
    old_core = original.integer_core(public, 'vdot')
    need(before.count(old_core) == 1 and before.count('  addi a1, a1, 32\n') == 1,
         'unique bounded replacement')
    after = before.replace(old_core, core()).replace('  addi a1, a1, 32\n', '  addi a1, a1, 16\n')
    after = after.replace('q288_fused_vdot', NAME)
    after = after.replace('.Ltile_vdot', '.Ltile_dot16').replace('.Lgroup_vdot', '.Lgroup_dot16')
    with tempfile.TemporaryDirectory(prefix='dot16-unchanged-tail-') as temp:
        generated = Path(temp) / 'source'
        tail.generate(repo, generated)
        fixed_dot8 = (generated / 'tail.S').read_text()
    assembly = fixed_dot8 + original.function(public, 'rvv4') + after
    out.mkdir(parents=True)
    (out / 'dot16.S').write_text(assembly)
    result = dict(contract=CONTRACT, assembly_sha256=sha(assembly.encode()), candidate=NAME,
                  retained=['q288_fused_vdot', 'q288_phased_vdot', 'q288_tail_vdot', 'q288_fused_rvv4'],
                  core_words_expected=61, group_words_expected=82, function_words_expected=121,
                  expected_dynamic_function_instructions=26922, expected_dynamic_dot16=5184,
                  weight_layout_changed=False, target_runtime_qualified=False, performance_qualified=False)
    (out / 'generation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(generate(a.repo.resolve(), a.output.resolve()), indent=2))
