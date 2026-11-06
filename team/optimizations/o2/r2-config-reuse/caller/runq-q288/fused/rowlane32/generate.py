"""Independent W8 row-lane full-Q candidate; no default or hardware change.

The new function has an explicit transposed-weight layout. The original full-Q
RVV function and all existing generators remain read-only.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused')
PARENT_SHA = 'b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b'
NAME = 'q288_rowlane32_i8'
CONTRACT = 'r2-s3-runq-rowlane32-screen-v1'
CORE_WORDS = 165


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_parent(repo):
    path = repo / REL / 'generate.py'
    need(digest(path.read_bytes()) == PARENT_SHA, 'unchanged full-Q shell generator')
    spec = importlib.util.spec_from_file_location('rowlane32_pinned_parent', path)
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    raw = (repo / parent.PUBLIC).read_bytes()
    need(digest(raw) == parent.PUBLIC_SHA, 'unchanged public baseline assembly')
    return parent, raw.decode()


def pack_q288(weight):
    """Fixture/format conversion, not a timed target implementation.

    Input is exactly 288x288 row-major signed integers. Output is the same byte
    count in [tile32, group32, k, output-lane] order, without scale conversion.
    """
    need(len(weight) == 288 * 288 and all(-128 <= x <= 127 for x in weight),
         'full signed-byte row-major Q288 input')
    return bytes(weight[(32*t+r)*288+32*g+k] & 255
                 for t in range(9) for g in range(9)
                 for k in range(32) for r in range(32))


def function():
    prologue = [
        'ld a2, 0(a0)', 'ld a7, 8(a0)', 'ld a4, 16(a0)', 'ld t0, 24(a0)',
        'ld a6, 32(a0)', 'ld a3, 40(a0)', 'csrwi vstart, 0', 'csrwi vcsr, 7',
        'li t2, 9', 'li t3, 36', 'li t4, 32',
        'vsetvli zero, t4, e32, m8, tu, mu',
    ]
    tile = ['vmv.v.i v16, 0', 'mv a1, a7', 'mv a5, t0', 'li t1, 9']
    core = ['vmv.v.i v0, 0', 'vmv.v.i v8, 0',
            'vsetvli zero, t4, e16, m4, ta, mu']
    for k in range(32):
        core.extend((f'lb t5, {k}(a1)', 'vle8.v v24, (a2)',
                     'vsext.vf2 v28, v24',
                     f'vwmacc.vx v{8*(k % 2)}, t5, v28',
                     'addi a2, a2, 32'))
    core.extend(('vsetvli zero, t4, e32, m8, tu, mu', 'vadd.vv v0, v0, v8'))
    need(len(core) == CORE_WORDS, 'complete integer block source inventory')
    # Preserve v0-v7: v6-v7 contain the final eight signed group sums. The
    # integer second accumulator and the weight temporaries are now dead.
    consume = [
        'vfcvt.f.x.v v8, v0', 'vlse32.v v24, (a4), t3',
        'vfmul.vv v8, v8, v24', 'flw ft0, 0(a5)',
        'vfmul.vf v8, v8, ft0', 'vfadd.vv v16, v16, v8',
        'addi a1, a1, 32', 'addi a4, a4, 4', 'addi a5, a5, 4',
        'addi t1, t1, -1', f'bnez t1, .Lgroup_{NAME}',
    ]
    tile_tail = ['vse32.v v16, (a6)', 'addi a6, a6, 128',
                 'addi a4, a4, 1116', 'addi t2, t2, -1',
                 f'bnez t2, .Ltile_{NAME}']
    # Each of the 128 observable slot bytes is written exactly once. Stores
    # use only the final group's last eight integer sums, not FP conversions.
    epilogue = [
        'vsetivli zero, 8, e32, m2, tu, mu', 'li t6, 16',
        'vsse32.v v6, (a3), t6', 'vmv.v.i v8, 0',
        'addi a3, a3, 4', 'vsse32.v v8, (a3), t6',
        'addi a3, a3, 4', 'vsse32.v v8, (a3), t6',
        'addi a3, a3, 4', 'vsse32.v v8, (a3), t6',
        'vsetivli zero, 8, e8, m1, tu, mu', 'ret',
    ]
    emit = lambda seq: ''.join('  ' + line + '\n' for line in seq)
    return (f'.balign 64\n.global {NAME}\n.type {NAME}, @function\n{NAME}:\n'
            + emit(prologue) + f'.Ltile_{NAME}:\n' + emit(tile)
            + f'.Lgroup_{NAME}:\n{NAME}_core_begin:\n' + emit(core)
            + f'{NAME}_core_end:\n' + emit(consume + tile_tail + epilogue)
            + f'.size {NAME}, .-{NAME}\n')


def generate(repo, out):
    repo, out = Path(repo).resolve(), Path(out).resolve()
    need(not out.exists() and not out.is_relative_to(repo),
         'fresh generated output outside repository')
    parent, public = load_parent(repo)
    baseline = parent.function(public, 'rvv4')
    candidate = function()
    assembly = '.option norvc\n.option norelax\n.text\n' + baseline + candidate
    out.mkdir(parents=True)
    (out / 'rowlane32.S').write_text(assembly)
    result = dict(contract=CONTRACT, source_sha256=digest(assembly.encode()),
                  candidate=NAME, baseline='q288_fused_rvv4',
                  candidate_source_sha256=digest(candidate.encode()),
                  integer_core_source_instructions=CORE_WORDS,
                  full_function_source_instruction_projection=14361,
                  parent_generator_sha256=PARENT_SHA, public_sha256=parent.PUBLIC_SHA,
                  layout='W8[tile32][group32][k][output_lane]',
                  shape=[288, 288], group_size=32, vlen=128,
                  standard_rvv_only=True, hardware_changed=False,
                  target_runtime_qualified=False, performance_qualified=False)
    (out / 'generation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.repo, args.output), indent=2))
