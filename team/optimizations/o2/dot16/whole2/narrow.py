#!/usr/bin/env python3
"""Derive whole8 plus exact integer merge/packing; this does not execute a guest."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

CONTRACT = 'r3-dot16-whole8-narrow-source-v1'
WHOLE8_GENERATOR_SHA = 'd02068b6714fb268faa526a751c53f601c7e6c46d20a8f20400334906425e448'
BASE_MACHINE_SHA = 'b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6'
OLD = 'q288_dot16_whole8'
NEW = 'q288_dot16_whole8_narrow'
BEFORE = ('  vsetivli zero, 4, e32, m1, tu, mu\n'
          + ''.join(f'  vadd.vv v{i}, v{i}, v{24+i}\n' for i in range(8))
          + ''.join(f'  vmv.v.v v{10+g}, v{4*g}\n'
                    + ''.join(f'  vslideup.vi v{10+g}, v{4*g+i}, {i}\n' for i in range(1,4))
                    for g in range(2))
          + '  vsetivli zero, 8, e32, m2, tu, mu\n')
AFTER = '''  vsetvli t6, zero, e32, m8, tu, mu
  vadd.vv v0, v0, v24
  vsetivli zero, 16, e32, m4, tu, mu
  vnsrl.wi v16, v0, 0
  vsetivli zero, 8, e32, m2, tu, mu
  vnsrl.wi v10, v16, 0
'''
# Independent RISC-V bit-field encoding, checked separately from GNU output.
PACK_WORDS = (0x01307fd7, 0x020c0057, 0xc1287057,
              0xb2003857, 0xc1147057, 0xb3003557)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_whole8(path):
    need(sha(path.read_bytes()) == WHOLE8_GENERATOR_SHA, 'frozen whole8 generator')
    spec = importlib.util.spec_from_file_location('frozen_whole8', path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def packing_proof():
    # Labels stand for arbitrary 32-bit lane sums, including nonzero upper lanes.
    lanes = [(r, lane) for r in range(8) for lane in range(4)]
    first = lanes[::2]
    second = first[::2]
    old = [(r, 0) for r in range(8)]
    need(second == old, 'same row result for arbitrary upper lanes')
    old_full = {(r, lane): ('add32', r, lane, r+24, lane)
                for r in range(8) for lane in range(4)}
    new_full = {(i//4, i%4): ('add32', i//4, i%4, 24+i//4, i%4)
                for i in range(32)}
    need(old_full == new_full, 'all eight complete 128-bit slot values preserved')
    return dict(vlen_bits=128, first_selected_lanes=list(range(0,32,2)),
                final_selected_lanes=list(range(0,32,4)), upper_lanes_arbitrary=True,
                all_full_slot_additions_identical=True,
                narrowing_shift=0, rounding=False, saturation=False,
                float_sequence_unchanged=True)


def derive(raw, whole8):
    retained, candidate8, report8 = whole8.derive(raw)
    text = candidate8.decode()
    need(text.count(BEFORE) == 1 and AFTER not in text, 'unique exact 18-instruction merge/pack')
    changed = text.replace(BEFORE, AFTER, 1)
    edits = [(BEFORE, AFTER)]
    for before, after, count in ((OLD, NEW, 5),
            ('.Ltile_dot16_whole8', '.Ltile_dot16_whole8_narrow', 2),
            ('.Lgroup_dot16_whole8', '.Lgroup_dot16_whole8_narrow', 2)):
        need(changed.count(before) == count and after not in changed, 'unique rename '+before)
        changed = changed.replace(before, after)
        edits.append((before, after))
    inverse = changed
    for before, after in reversed(edits):
        inverse = inverse.replace(after, before)
    need(inverse == text, 'inverse reconstructs whole8 byte exactly')
    old_inst, new_inst = whole8.instructions(text), whole8.instructions(changed)
    need(len(old_inst) == 90 and len(new_inst) == 78, 'function instruction budget')
    need(sum(x.startswith('.word') for x in new_inst) == 16, 'same sixteen dot16 sites')
    need(text[text.index('  vfcvt.f.x.v'):].replace(OLD,NEW).replace(
            '.Lgroup_dot16_whole8','.Lgroup_dot16_whole8_narrow').replace(
            '.Ltile_dot16_whole8','.Ltile_dot16_whole8_narrow')
         == changed[changed.index('  vfcvt.f.x.v'):], 'unchanged floating/tail sequence')
    # t6 becomes VL, but is dead until its later explicit reload from a3.
    suffix = changed[changed.index('  vfcvt.f.x.v'):]
    need('t6' not in suffix[:suffix.index('  mv t6, a3')], 't6 value dead after packing')
    combined = retained + b'\n' + changed.encode()
    need(combined[:len(retained)] == retained, 'all retained source byte exact')
    report = dict(schema=1, contract=CONTRACT, status='SOURCE_DERIVED_UNBUILT',
        candidate=NEW, base_assembly_sha256=sha(raw), whole8_derivation=report8,
        candidate_source_sha256=sha(changed.encode()), combined_source_sha256=sha(combined),
        source_inverse_byte_exact=True, retained_source_byte_equal=True,
        packing=packing_proof(), pack_expected_words=[f'{w:08x}' for w in PACK_WORDS],
        expected=dict(function_instructions=78, function_machine_bytes=312,
            groups_per_function=324, dynamic_function_instructions=12990,
            reduction_vs_whole2=8100, reduction_vs_whole8=3888,
            dynamic_dot16=5184, dynamic_whole2_loads=324, dynamic_whole8_loads=648),
        gnu_built=False, reference_qualified=False, target_runtime_qualified=False,
        performance_qualified=False, new_emu_runs=0)
    return combined, changed.encode(), report


def branch_offset(word):
    n = ((word>>31&1)<<12 | (word>>7&1)<<11 | (word>>25&63)<<5 | (word>>8&15)<<1)
    return n-8192 if n & 4096 else n


def with_branch_offset(word, offset):
    need(-4096 <= offset < 4096 and offset % 2 == 0, 'B immediate range')
    n = offset & 8191
    return ((word & ~0xfe000f80) | (n>>12&1)<<31 | (n>>11&1)<<7
            | (n>>5&63)<<25 | (n>>1&15)<<8)


def expected_machine(raw):
    """Derive expected bytes from pinned whole2 words, independently of assembly."""
    need(sha(raw) == BASE_MACHINE_SHA and len(raw) == 412, 'frozen whole2 machine bytes')
    words = list(struct.unpack('<103I', raw))
    need(words[50] == PACK_WORDS[1] and words[66] == PACK_WORDS[4], 'old exact merge words')
    rows = []
    i = 0
    while i < len(words):
        if i == 17:
            # VL2 nf=1 -> VL8 nf=7; first base t6 -> a2. All other fields retained.
            need(words[18]>>29 == 1 and words[18]>>15&31 == 31, 'first VL2 encoding')
            rows.append((17, (words[18] & ~((7<<29)|(31<<15))) | (7<<29) | (12<<15)))
            i = 25
        elif i == 33:
            need(words[34]>>29 == 1, 'second VL2 encoding')
            rows.extend(((33, words[33]), (34, (words[34] & ~(7<<29)) | 7<<29)))
            i = 41
        elif i == 49:
            rows.extend((None, word) for word in PACK_WORDS)
            i = 67
        else:
            rows.append((i, words[i]))
            i += 1
    need(len(rows) == 78, 'independent machine instruction count')
    indices = {old: new for new,(old,_) in enumerate(rows) if old is not None}
    result, targets = [], []
    for new,(old,word) in enumerate(rows):
        if word & 127 == 0x63:
            need(old is not None, 'retained branch')
            target = old + branch_offset(word)//4
            need(target in (11,15), 'only retained tile/group branch')
            word = with_branch_offset(word, 4*(indices[target]-new))
            targets.append(target)
        result.append(word)
    need(sorted(targets) == [11,15], 'both local branches reconstructed')
    return struct.pack('<78I', *result)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--whole2-assembly', type=Path, required=True)
    p.add_argument('--whole8-generator', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    need(a.output.is_absolute() and not a.output.exists(), 'fresh absolute output')
    raw=a.whole2_assembly.read_bytes()
    combined,candidate,report=derive(raw,load_whole8(a.whole8_generator))
    a.output.mkdir(parents=True)
    (a.output/'whole8-narrow.S').write_bytes(combined)
    (a.output/'whole8-narrow-only.S').write_bytes(candidate)
    report.update(generated_at=datetime.now(timezone.utc).isoformat(),
                  generator_sha256=sha(Path(__file__).read_bytes()))
    (a.output/'derivation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('contract','status','candidate','candidate_source_sha256')}))


if __name__ == '__main__':
    main()
