"""Generate RVV sequences for the same independent T05 legal corpus."""
import argparse
import hashlib
import json
from pathlib import Path

from generate_vdot_cases import generate, SEED
from vdot_model import decode

BASELINE_ID = 'rvv-vdot-s8x8-r32-v1'


def scratch_registers(vd, vs1, vs2):
    operands = {vd, vs1, vs2, 0}
    product = next(p for p in range(2, 32, 2) if not {p, p+1} & operands)
    free = [p for p in range(1, 32) if p not in operands | {product, product+1}]
    return product, product+1, free[0], free[1]


def generate_baseline(output, random_count=1000, smoke_random_count=1000):
    data = generate(output, random_count, SEED, smoke_random_count,'expanded')
    cases = [json.loads(line) for line in (output/'cases.jsonl').read_text().splitlines()][:data['smoke_count']]
    words = sorted({int(c['instruction'], 16) for c in cases})
    asm = ['/* Generated ordinary RVV baseline; no custom instruction. */',
           '#include "layout.h"', '.option norvc', '.text']
    header = ['#ifndef RVV_BASELINE_STUBS_H', '#define RVV_BASELINE_STUBS_H',
              'struct baseline_site { unsigned word, scratch_mask; void (*entry)(void); const char *begin, *end; };']
    sites = []
    scratch = {}
    for word in words:
        vd, vs1, vs2 = decode(word)
        p, high, z, r = scratch_registers(vd, vs1, vs2)
        name = f'baseline_{word:08x}'
        header.append(f'extern void {name}(void);')
        header.append(f'extern const char {name}_begin[], {name}_end[];')
        mask = sum(1 << reg for reg in (p, high, z, r))
        sites.append(f'  {{0x{word:08x}U, 0x{mask:08x}U, {name}, {name}_begin, {name}_end}}')
        scratch[f'0x{word:08x}'] = [p, high, z, r]
        asm.extend([f'.globl {name}', f'.type {name}, @function', f'{name}:',
                    '  csrr t0, mstatus', '  sd t0, REC_PRE_STATUS(s0)',
                    f'.globl {name}_begin', f'{name}_begin:', '  csrr t3, vl', '  csrr t4, vtype',
                    '  vsetivli zero, 4, e32, m1, tu, mu', f'  vmv.v.i v{z}, 0',
                    '  vsetivli zero, 8, e8, m1, tu, mu',
                    f'{name}_multiply:', f'  vwmul.vv v{p}, v{vs1}, v{vs2}',
                    '  vsetivli zero, 8, e16, m2, tu, mu',
                    f'{name}_reduce:', f'  vwredsum.vs v{r}, v{p}, v{z}',
                    '  vsetivli zero, 4, e32, m1, tu, mu', f'  vmv.x.s t2, v{r}',
                    f'  vmv.v.i v{vd}, 0', f'  vmv.s.x v{vd}, t2',
                    '  vsetvl zero, t3, t4', f'.globl {name}_end', f'{name}_end:',
                    '  j vdot_observe', f'.size {name}, .-{name}'])
    header.extend(['static const struct baseline_site baseline_sites[] = {', ',\n'.join(sites), '};',
                   'static const struct baseline_site *find_baseline(unsigned word) {',
                   '  for (unsigned i=0; i<sizeof(baseline_sites)/sizeof(baseline_sites[0]); ++i)',
                   '    if (baseline_sites[i].word==word) return &baseline_sites[i];',
                   '  return 0;', '}', '#endif'])
    (output/'baseline-sites.S').write_bytes(('\n'.join(asm)+'\n').encode())
    (output/'baseline-stubs.h').write_bytes(('\n'.join(header)+'\n').encode())
    manifest = dict(baseline_id=BASELINE_ID, contract_id=data['contract_id'], planned=len(cases),
                    scratch_by_word=scratch, gpr_scratch=['t0', 't2', 't3', 't4'],
                    data_manifest_sha256=hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    artifacts_sha256={name:hashlib.sha256((output/name).read_bytes()).hexdigest()
                                      for name in ('baseline-sites.S', 'baseline-stubs.h')})
    manifest['scratch_layout_count']=len({tuple(values) for values in scratch.values()})
    (output/'baseline-manifest.json').write_bytes((json.dumps(manifest, sort_keys=True, indent=2)+'\n').encode())
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--random-count', type=int, default=1000)
    parser.add_argument('--smoke-random-count', type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(generate_baseline(args.output, args.random_count, args.smoke_random_count), sort_keys=True))
