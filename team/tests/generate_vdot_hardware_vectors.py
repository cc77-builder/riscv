"""Independent model -> standalone hardware interface vectors, with no RTL oracle."""
import argparse
import hashlib
import json
from pathlib import Path

from generate_vdot_cases import directed_cases, expanded_cases, random_cases, exception_cases, SEED, GENERATOR_VERSION
from vdot_model import encode, decode, execute, NotVdot, VectorState, MODEL_VERSION


def generate(output):
    records = []

    def add(name, word, a, b, vl=8, vtype=0, vstart=0, vs=1):
        try:
            _, s1, s2 = decode(word)
            regs = [0] * 32
            if s1 == s2 and a != b:
                raise ValueError('Aliased sources must be identical')
            regs[s1], regs[s2] = a, b
            outcome = execute(word, VectorState(regs=tuple(regs), vl=vl, vtype=vtype, vstart=vstart, vs=vs))
            illegal = outcome.cause is not None
            expected = 0 if illegal else outcome.state.regs[(word >> 7) & 31]
        except NotVdot:
            # An unsupported request sent to THIS module is rejected. In the
            # processor other encodings still belong to the ordinary decoder.
            illegal, expected = True, 0
        records.append((name, word, a, b, vl, vtype, vstart, vs, len(records), expected, int(illegal)))

    for c in directed_cases() + expanded_cases() + list(random_cases(10000, SEED, random_registers=True)):
        cfg = c['config']
        add(c['id'], int(c['instruction'], 16), int(c['src1_128'], 16), int(c['src2_128'], 16),
            cfg['vl'], cfg['vtype'], cfg['vstart'], cfg['vs'])
    a, b = int('80' * 8 + '7f' * 8, 16), int('7f' * 8 + '80' * 8, 16)
    word = encode(10, 8, 9)
    for c in exception_cases():
        same_source = ((c['word'] >> 15) & 31) == ((c['word'] >> 20) & 31)
        add(c['id'], c['word'], a, a if same_source else b,
            c['vl'], c['vtype'], c['vstart'], 0 if c['vs_off'] else c['vs'])
    for bit in range(64):
        add(f'vtype-bit-{bit}', word, a, b, vtype=1 << bit)
    for vl in range(256):
        add(f'actual-vl-{vl}', word, a, b, vl=vl)
    for bit in range(64):
        add(f'vstart-bit-{bit}', word, a, b, vstart=1 << bit)
    for bit in range(32):
        if (0xFE00707F >> bit) & 1:
            add(f'encoding-bit-{bit}', word ^ (1 << bit), a, b)
    # Exercise every signed input byte against extremal/sign/zero multipliers,
    # rotating all eight lane positions and poisoning the ignored upper half.
    for value in range(-128, 128):
        for multiplier in (-128, -1, 0, 1, 127):
            lane = (value + 128) % 8
            left = bytearray([0] * 8 + [0xA5] * 8)
            right = bytearray([0] * 8 + [0x5A] * 8)
            left[lane], right[lane] = value & 255, multiplier & 255
            add(f'signed-byte-{value}-{multiplier}', word, int.from_bytes(left, 'little'), int.from_bytes(right, 'little'))

    lines = ['# id\tinstruction\tsrc1\tsrc2\tvl\tvtype\tvstart\tvs\ttag\texpected128\tillegal']
    for name, word, a, b, vl, vt, start, vs, tag, expected, illegal in records:
        lines.append(f'{name}\t{word:08x}\t{a:032x}\t{b:032x}\t{vl}\t{vt:016x}\t{start:016x}\t{vs}\t{tag}\t{expected:032x}\t{illegal}')
    output.mkdir(parents=True, exist_ok=True)
    table = output / 'vectors.tsv'
    table.write_bytes(('\n'.join(lines) + '\n').encode())
    source_root = Path(__file__).resolve().parents[2]
    names = ['team/tests/vdot_model.py', 'team/tests/generate_vdot_cases.py',
             'team/tests/generate_vdot_hardware_vectors.py',
             'team/legacy/james-vfex1/src/main/scala/xiangshan/backend/fu/vector/VdotExec.scala',
             'team/hardware/vdot/build.sbt', 'team/hardware/vdot/project/build.properties',
             'team/hardware/vdot/src/main/scala/EmitVdot.scala',
             'team/hardware/vdot/src/test/scala/VdotExecSpec.scala',
             'team/scripts/vdot-hardware-tests.sh']
    metadata = dict(contract_id='vdot-s8x8-r32-v0.1', vectors=len(records),
                    seed=f'0x{SEED:08x}',random_count=10000,
                    model_version=MODEL_VERSION,generator_version=GENERATOR_VERSION,
                    legal=sum(not r[-1] for r in records), illegal=sum(r[-1] for r in records),
                    vectors_sha256=hashlib.sha256(table.read_bytes()).hexdigest(),
                    source_sha256={name:hashlib.sha256((source_root/name).read_bytes()).hexdigest() for name in names})
    (output/'vectors-manifest.json').write_bytes((json.dumps(metadata, sort_keys=True, indent=2)+'\n').encode())
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(generate(parser.parse_args().output), sort_keys=True))
