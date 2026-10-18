"""Prepare the O0 fixed-work corpus; generation is not hardware acceptance.

256 dots per window, 1/2/4 independent destination lanes, shared or distinct
input register pairs. Loop counts differ and MUST be considered in diagnosis.
The established emitter supplies full register snapshots and fenced CSR windows.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EMITTER = ROOT / 'team/workloads/unified-vdot/generate.py'


def emitter():
    spec = importlib.util.spec_from_file_location('o0_unified_emitter', EMITTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def case(g, dataset, lanes, inputs, method):
    if dataset not in (0, 1, 2) or lanes not in (1, 2, 4) or inputs not in ('same', 'different') or method not in ('vdot', 'rvv'):
        raise ValueError('unsupported matrix coordinate')
    a, b = g.dataset_pair(dataset)
    before = g.initial(a, b)
    pairs = []
    for lane in range(lanes):
        left, right = (8, 9) if inputs == 'same' else (8 + 2*lane, 9 + 2*lane)
        if inputs == 'different' and lane:
            # Distinct active bytes even for constant extreme-value datasets.
            before[left] = bytes((x + 17*lane + i*lane) & 255 for i, x in enumerate(a[:8])) + a[8:]
            before[right] = bytes((x - 13*lane - i*lane) & 255 for i, x in enumerate(b[:8])) + b[8:]
        pairs.append((left, right))
    expected = list(before)
    destinations = list(range(24, 24 + lanes))
    for dest, (left, right) in zip(destinations, pairs):
        expected[dest] = g.dot(before[left], before[right])
    if method == 'vdot':
        step = [g.vdot(dest, left, right) for dest, (left, right) in zip(destinations, pairs)]
        scratch = []
    else:
        step = [f'vwmul.vv v{16 + 2*i}, v{left}, v{right}' for i, (left, right) in enumerate(pairs)]
        step += ['vsetivli zero, 8, e16, m1, tu, mu']
        for i, dest in enumerate(destinations):
            step += [f'vmv.v.i v{dest}, 0', f'vwredsum.vs v{dest}, v{16 + 2*i}, v{dest}']
        step += ['vsetivli zero, 8, e8, m1, tu, mu']
        scratch = list(range(16, 16 + 2*lanes))
    iterations = 256 // lanes
    scenario = f'matrix-l{lanes}-{inputs}'
    return dict(id=f'{scenario}-{method}', scenario=scenario, method=method,
                n=iterations, iterations=iterations, dots=256, lanes=lanes, input_mode=inputs,
                lane_operands=[[d, a, b] for d, (a, b) in zip(destinations, pairs)],
                operands=[destinations[0], *pairs[0]], vtype=0, scratch=scratch,
                before=[x.hex() for x in before], expected=[x.hex() for x in expected],
                stream=[], outputs=[], body=[f'li t6, {iterations}', '.Lloop:'] + step +
                ['addi t5, t5, 1', 'addi t6, t6, -1', 'bnez t6, .Lloop'])


def corpus(dataset):
    g = emitter()
    rows, plan = [], []
    for lanes in (1, 2, 4):
        for inputs in ('same', 'different'):
            base = len(rows)
            rows.extend(case(g, dataset, lanes, inputs, method) for method in ('vdot', 'rvv'))
            for repeat in range(6):
                for index in ((base, base+1) if repeat % 2 == 0 else (base+1, base)):
                    plan.append(dict(seq=len(plan), index=index, id=rows[index]['id'], repeat=repeat,
                                     phase='first' if repeat == 0 else 'warmup' if repeat == 1 else 'measured'))
    return rows, plan


def generate(output, dataset, shard=0, shards=1):
    if type(dataset) is not int or dataset not in (0, 1, 2):
        raise ValueError('dataset must be 0, 1 or 2')
    if type(shards) is not int or shards not in (1, 6) or type(shard) is not int or not 0 <= shard < shards:
        raise ValueError('use one complete image or six paired shards')
    rows, plan = corpus(dataset)
    result = emitter().emit(output, rows, plan, 'o0-matrix', dataset, shard, shards, True, 'ours')
    result['diagnostic'] = {
        'schema': 1, 'status': 'GENERATED_NOT_HARDWARE_VALIDATED',
        'work_per_window': 256,
        'lane_definition': 'independent destination registers; no result-to-input RAW dependency',
        'input_definition': 'same shares v8/v9; different uses distinct register pairs and active bytes',
        'one_lane_control': 'same/different operands coincide at one lane by construction',
        'limits': ['Loop counts 256/128/64 and instruction counts differ; lane comparison is not pure hardware II.',
                   'No loads/stores inside the measured loop; stream behavior is covered separately.',
                   'New ELF/source binding, execution, calibration and retirement checks remain required.'],
        'source_sha256': {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (Path(__file__).resolve(), EMITTER)},
    }
    (Path(output) / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', type=int, choices=(0, 1, 2), required=True)
    parser.add_argument('--shard', type=int, default=0)
    parser.add_argument('--shards', type=int, choices=(1, 6), default=1)
    args = parser.parse_args()
    result = generate(args.output, args.dataset, args.shard, args.shards)
    print(json.dumps({'status': result['diagnostic']['status'], 'rows': len(result['rows']), 'windows': len(result['plan'])}))
