#!/usr/bin/env python3
"""Host-only probes for proposed B6/B7 RVV sequences; not an ISA simulator.

Checks math, storage layout, scratch allocation and the six/seven-instruction
assembly for all 32^3 operand register combinations. No target cycles, VS/trap,
NEMU, RTL or DiffTest evidence is produced. Python 3.10+, standard library only.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import platform
import shutil
import struct
import subprocess
import tempfile
from datetime import datetime, timezone

MASK128 = (1 << 128) - 1
SEED = 0x20261012


def scratch(vd: int, a: int, b: int, variant: str) -> tuple[int, ...]:
    if variant not in ('B6', 'B7'):
        raise ValueError('variant must be B6 or B7')
    if not all(isinstance(r, int) and 0 <= r < 32 for r in (vd, a, b)):
        raise ValueError('vector register indices must be in 0..31')
    blocked = {0, vd, a, b}
    candidates = ((p, p + 1) for p in range(2, 32, 2)) if variant == 'B6' else ((p,) for p in range(1, 32))
    for group in candidates:
        if not blocked.intersection(group):
            return group
    raise ValueError('no nonoverlapping scratch group')


def reference(regs: list[int], a: int, b: int) -> int:
    aa = struct.unpack('<8b', regs[a].to_bytes(16, 'little')[:8])
    bb = struct.unpack('<8b', regs[b].to_bytes(16, 'little')[:8])
    return sum(x * y for x, y in zip(aa, bb)) & 0xffffffff


def step_model(regs: list[int], vd: int, a: int, b: int,
               policy: int, variant: str, agnostic_ones: bool) -> tuple[list[int], int]:
    """Manual RVV-operation model, limited to legal VLEN128/e8m1/vl8 input.

    Saves the ORIGINAL sources before changing a possibly aliased destination.
    Covers policy restoration as integer data only, not actual privileged CSR
    effects. vwmul output upper register in B6 may be tail-preserved/all ones.
    """
    out = regs.copy()
    group = scratch(vd, a, b, variant)
    x, y = regs[a], regs[b]
    product = 0
    for i in range(8):
        u, v = (x >> (8*i)) & 255, (y >> (8*i)) & 255
        u = u - 256 if u & 128 else u
        v = v - 256 if v & 128 else v
        product |= ((u*v) & 65535) << (16*i)
    out[group[0]] = product
    if variant == 'B6' and (policy & 64) and agnostic_ones:
        out[group[1]] = MASK128
    # vsetivli t3,8,e16,m1,tu,mu returns 8, equal to legal entry vl.
    new_vl = min(8, 128 // 16)
    if new_vl != 8:
        raise AssertionError('candidate precondition violated')
    out[vd] = 0  # vmv.v.i at e16,vl8 clears the WHOLE 128-bit destination.
    total = 0
    for i in range(new_vl):
        p = (out[group[0]] >> (16*i)) & 65535
        total += p - 65536 if p & 32768 else p
    out[vd] = total & 0xffffffff  # reduction seed=0; TU retains zero high96.
    restored_vtype = policy  # vsetvl zero,t3,t4; saved t4, not constant policy.
    return out, restored_vtype


def instruction_lines(vd: int, a: int, b: int, variant: str) -> list[str]:
    p = scratch(vd, a, b, variant)[0]
    lines = ['csrr t4, vtype']
    if variant == 'B7':
        lines += ['vsetivli zero, 8, e8, mf2, tu, mu']
    lines += [f'vwmul.vv v{p}, v{b}, v{a}',
              'vsetivli t3, 8, e16, m1, tu, mu',
              f'vmv.v.i v{vd}, 0', f'vwredsum.vs v{vd}, v{p}, v{vd}',
              'vsetvl zero, t3, t4']
    return lines


def text_bytes(path: Path) -> bytes:
    """Read ELF64 LE .text only, avoiding huge generated disassembly logs."""
    data = path.read_bytes()
    if data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('expected ELF64 little-endian')
    shoff = struct.unpack_from('<Q', data, 40)[0]
    entsize, count, strindex = struct.unpack_from('<HHH', data, 58)
    def section(i: int) -> tuple:
        return struct.unpack_from('<IIQQQQIIQQ', data, shoff+i*entsize)
    names = section(strindex)
    table = data[names[4]:names[4]+names[5]]
    for i in range(count):
        s = section(i)
        if table[s[0]:].split(b'\0', 1)[0] == b'.text':
            return data[s[4]:s[4]+s[5]]
    raise ValueError('.text missing')


def check_assembly() -> dict:
    clang = shutil.which('clang')
    if not clang:
        raise RuntimeError('--assemble requested but clang is unavailable')
    version = subprocess.check_output([clang, '--version'], text=True).splitlines()[0]
    result: dict = {'status': 'PASS', 'tool': version, 'variants': {}}
    with tempfile.TemporaryDirectory(prefix='vdot-review-') as d:
        root = Path(d)
        for variant, n in [('B6', 6), ('B7', 7)]:
            src, obj = root / f'{variant}.S', root / f'{variant}.o'
            with src.open('w', encoding='utf-8', newline='\n') as f:
                f.write('.text\n.option norvc\n.p2align 2\n')
                for vd, a, b in itertools.product(range(32), repeat=3):
                    f.write(f'f_{vd}_{a}_{b}:\n')
                    for line in instruction_lines(vd, a, b, variant):
                        f.write('    '+line+'\n')
                    f.write('    ret\n')
            command = [clang, '--target=riscv64', '-march=rv64gcv', '-mabi=lp64d', '-c', str(src), '-o', str(obj)]
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=90)
            text = text_bytes(obj)
            if len(text) != 32768 * (n + 1) * 4:
                raise AssertionError(f'{variant}: unexpected instruction bytes')
            result['variants'][variant] = {
                'register_triples': 32768, 'roi_instructions': n,
                'text_bytes_including_ret': len(text),
                'text_sha256': hashlib.sha256(text).hexdigest(),
                'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
            }
    return result


def run(assemble: bool) -> dict:
    rng = random.Random(SEED)
    corpus = hashlib.sha256()
    counts = {'B6': 0, 'B7': 0}
    # One coherent 32-register state per register triple; eight policy/tail
    # environments each. This is NOT exhaustive over 2^256 source-bit patterns.
    for vd, a, b in itertools.product(range(32), repeat=3):
        regs = [rng.getrandbits(128) for _ in range(32)]
        corpus.update(bytes((vd, a, b)))
        for value in regs:
            corpus.update(value.to_bytes(16, 'little'))
        expect = reference(regs, a, b)
        for variant in counts:
            group = set(scratch(vd, a, b, variant))
            for policy in (0, 64, 128, 192):
                for tail in (False, True):
                    actual, restored = step_model(regs, vd, a, b, policy, variant, tail)
                    if actual[vd] != expect or restored != policy:
                        raise AssertionError((variant, vd, a, b, policy, 'value/config'))
                    for r in range(32):
                        if r != vd and r not in group and actual[r] != regs[r]:
                            raise AssertionError((variant, vd, a, b, r, 'clobber'))
                    counts[variant] += 1
    extrema = [([-128]*8, [-128]*8, 131072),
               ([-128]*8, [127]*8, -130048),
               ([-1]*8, [1]*8, -8), ([127]*8, [127]*8, 129032)]
    for aa, bb, answer in extrema:
        regs = [MASK128]*32
        regs[8] = int.from_bytes(struct.pack('<8b', *aa)+b'\xa5'*8, 'little')
        regs[9] = int.from_bytes(struct.pack('<8b', *bb)+b'\x5a'*8, 'little')
        for variant in counts:
            out, _ = step_model(regs, 10, 8, 9, 192, variant, True)
            if out[10] != answer & 0xffffffff:
                raise AssertionError(('extreme', variant, answer))
    # Observable counterexamples, not RTL fault injection.
    negative = {
        '16bit_accumulator_overflows': (131072 & 65535) != 131072,
        'sign_extending_to128_is_wrong': (MASK128-7) != 0xfffffff8,
        'restoring_constant_policy_loses_ta_ma': 0 != 192,
        'e8_scalar_extract_truncates_131072': (131072 & 255) != 131072,
    }
    if not all(negative.values()):
        raise AssertionError('negative-control design failed')
    return {
        'status': 'PASS', 'scope': 'host_RVV_step_model_and_optional_assembly_only',
        'utc': datetime.now(timezone.utc).isoformat(), 'seed': hex(SEED),
        'python_version': platform.python_version(),
        'random_generator': 'Python random.Random.getrandbits; compare corpus hash across runtimes',
        'random_register_corpus_sha256': corpus.hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'register_triples': 32768, 'policies': 4, 'tail_modes': 2,
        'modeled_cases_per_variant': counts, 'extra_extremes_per_variant': len(extrema),
        'negative_counterexamples': negative,
        'assembly': check_assembly() if assemble else {'status': 'NOT_RUN'},
        'not_verified': ['actual_CPU_execution', 'VS_or_trap_behavior',
                         'NEMU', 'XiangShan_RTL', 'DiffTest', 'cycles', 'PPA'],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assemble', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    def emit(result: dict) -> str:
        rendered = json.dumps(result, ensure_ascii=False, indent=2)+'\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding='utf-8')
        return rendered
    # Invalidate a previous PASS before a new run, including interrupted runs.
    emit({'status': 'RUNNING', 'scope': 'host_probe_only'})
    try:
        result = run(args.assemble)
    except Exception as exc:
        emit({'status': 'FAIL', 'scope': 'host_probe_only',
              'error_type': type(exc).__name__, 'error': str(exc)})
        raise
    print(emit(result), end='')

if __name__ == '__main__':
    main()
