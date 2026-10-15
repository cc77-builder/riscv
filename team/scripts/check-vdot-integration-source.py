"""Static integration and two-oracle checks; never a claim of RTL execution."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

def check():
    inst = read('src/main/scala/xiangshan/backend/decode/Instructions.scala')
    patterns = re.findall(r'def VDOT_VV = BitPat\("b([01?]+)"\)', inst)
    require(len(patterns) == 1 and len(patterns[0]) == 32, 'unique 32-bit vdot BitPat required')
    pattern = patterns[0]
    match = int(pattern.replace('?', '0'), 2)
    mask = int(''.join('0' if p == '?' else '1' for p in pattern), 2)
    require((match, mask) == (0x0200000b, 0xfe00707f), 'production BitPat disagrees with contract')
    encoding_count = 0
    for vd, vs1, vs2 in itertools.product(range(32), repeat=3):
        word = 0x0200000b | vd << 7 | vs1 << 15 | vs2 << 20
        require(word & mask == match, 'operand field overlaps fixed encoding')
        require(((word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31) ==
                (vd, vs1, vs2), 'encoding field loss')
        encoding_count += 1
    neighbours = 0
    for bit in range(32):
        if mask & (1 << bit):
            require(((0x0284850b ^ (1 << bit)) & mask) != match, 'fixed-bit neighbour accepted')
            neighbours += 1
    package = read('src/main/scala/xiangshan/package.scala').split('object UopSplitType {', 1)[1].split('object ExceptionNO', 1)[0]
    split_types = re.findall(r'def (\w+)\s*= "b([01]{6})"\.U', package)
    values = [bits for _, bits in split_types]
    require(len(values) == len(set(values)), 'split encoding collision')
    splits = dict(split_types)
    require('VEC_VDOT' in splits and int(splits['VEC_VDOT'], 2) & 0x30, 'vdot not on complex split path')
    require('UopSplitType.VEC_VDOT -> 1.U' in read('src/main/scala/xiangshan/backend/decode/UopInfoGen.scala'), 'missing fixed one-uop entry')
    parameters = read('src/main/scala/xiangshan/Parameters.scala')
    require(parameters.count('Seq(VfdivCfg, VidivCfg, VDotCfg)') == 1, 'unexpected VFEX4 binding')
    manifest = json.loads(read('team/patches/nemu/manifest.json'))
    patch = ROOT / 'team/patches/nemu/vdot-s8x8-r32-v0.1.patch'
    require(hashlib.sha256(patch.read_bytes()).hexdigest() == manifest['patch_sha256'], 'imported NEMU patch changed')
    require(manifest['base_rev'] == 'a48a11f208ff81ad765591d83271d1b339fb3861', 'wrong NEMU baseline')
    original = module('vdot_original_oracle', 'team/models/vdot/model.py')
    imported = module('vdot_imported_oracle', 'team/tests/vdot_model.py')
    counts = {}
    for name in ('directed', 'random'):
        count = 0
        for line in read(f'team/models/vdot/data/{name}.jsonl').splitlines():
            case = json.loads(line)
            a, b, expected = (int(case[key], 16) for key in ('vs1', 'vs2', 'expected_vd'))
            require(original.vdot(a, b) == imported.result128(a, b) == expected,
                    f'{name} case {case["id"]}: independent oracle disagreement')
            count += 1
        require(count > 0, 'empty oracle input')
        counts[name] = count
    return dict(status='STATIC_SOURCE_AND_ORACLES_PASS', encoding_combinations=encoding_count,
                fixed_bit_neighbours=neighbours, split_encoding=splits['VEC_VDOT'],
                original_data_counts=counts, nemu_patch_sha256=manifest['patch_sha256'],
                scope='host/static only; Scala compilation and RTL/NEMU/full-core execution NOT_RUN')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
