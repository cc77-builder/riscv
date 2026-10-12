"""Validate actual baseline logs against hashed independent inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re

BASELINE_ID = 'rvv-vdot-s8x8-r32-v1'
CONTRACT = 'vdot-s8x8-r32-v0.1'


def fields(line):
    return dict(re.findall(r'([a-zA-Z0-9_]+)=([^\s]+)', line))


def validate(content, exit_code, data):
    if exit_code != 0 or re.search(r'\bFAIL[: ]|BAD TRAP', content):
        raise ValueError('baseline exit/failure marker')
    if content.count(f'BASELINE_BEGIN contract={CONTRACT} baseline={BASELINE_ID}') != 1:
        raise ValueError('baseline begin marker')
    if content.count('BASELINE_CONTROLS_PASS high96=detected preserved_register=detected csr=detected declared_scratch=allowed') != 1:
        raise ValueError('missing baseline controls')
    manifest = json.loads((data/'manifest.json').read_text())
    baseline = json.loads((data/'baseline-manifest.json').read_text())
    if manifest['contract_id'] != CONTRACT or baseline['contract_id'] != CONTRACT or baseline['baseline_id'] != BASELINE_ID:
        raise ValueError('contract mismatch')
    if hashlib.sha256((data/'manifest.json').read_bytes()).hexdigest() != baseline['data_manifest_sha256']:
        raise ValueError('data manifest hash mismatch')
    for group in (manifest, baseline):
        for name, digest in group['artifacts_sha256'].items():
            if hashlib.sha256((data/name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'artifact hash mismatch: {name}')
    cases = [json.loads(line) for line in (data/'cases.jsonl').read_text().splitlines()][:manifest['smoke_count']]
    expected = {c['id']:c for c in cases}
    records = [fields(line) for line in content.splitlines() if line.startswith('BASELINE_CASE ')]
    ids = [r.get('id') for r in records]
    if len(set(ids)) != len(ids) or set(ids) != set(expected):
        raise ValueError('missing/duplicate/unexpected case IDs')
    summaries = [fields(line) for line in content.splitlines() if line.startswith('BASELINE_SUMMARY ')]
    if len(summaries) != 1:
        raise ValueError('baseline summary count')
    s = summaries[0]
    if s.get('contract') != CONTRACT or s.get('baseline') != BASELINE_ID or baseline['planned'] != len(cases):
        raise ValueError('summary contract/count mismatch')
    if any(int(s.get(k, '-1')) != len(cases) for k in ('planned','executed','passed')) or int(s.get('failed', '-1')) != 0:
        raise ValueError('incomplete baseline coverage')
    for row in records:
        case = expected[row['id']]
        cfg = case['config']
        word = int(case['instruction'], 16)
        scratch = baseline['scratch_by_word'][f'0x{word:08x}']
        if len(set(scratch)) != 4 or set(scratch) & {case['vd'],case['vs1'],case['vs2']}:
            raise ValueError('invalid scratch contract')
        wanted_csrs = (cfg['vtype'],8,0,cfg['vxrm'],cfg['vxsat'],(cfg['vxrm']<<1)|cfg['vxsat'])
        if row.get('result') != 'PASS' or int(row.get('instruction','-1'),0) != word:
            raise ValueError('wrong case result')
        if int(row.get('scratch_mask','-1'),0) != sum(1 << r for r in scratch):
            raise ValueError('scratch mask mismatch')
        for key in ('pre_csr', 'post_csr'):
            if tuple(int(v,0) for v in row[key].split('/')) != wanted_csrs:
                raise ValueError('baseline CSR mismatch')
        for key in ('expected_vd128', 'post_vd128'):
            if int(row[key],0) != int(case['expected_128'],16):
                raise ValueError('baseline disagrees with independent oracle')
        if ((int(row['pre_mstatus'],0)>>9)&3) != cfg['vs'] or ((int(row['raw_mstatus'],0)>>9)&3) != 3:
            raise ValueError('wrong VS state')
        if int(row.get('trap_count','-1')) != 0 or int(row.get('protocol_errors','-1'),0) != 0:
            raise ValueError('unexpected trap')
        if int(row.get('requested_vs','-1'))!=cfg['vs'] or row.get('pre32_checked')!='1':
            raise ValueError('missing exact initial state observation')
        if int(row.get('end_pc','0'),0)-int(row.get('begin_pc','0'),0)!=52:
            raise ValueError('wrong baseline instruction boundary')
        if row.get('all32_except_scratch_checked') != '1' or row.get('guards_ok') != '1':
            raise ValueError('incomplete state observation')
    return dict(status='RVV_BASELINE_PASS', executed=len(cases), baseline_id=BASELINE_ID,
                contract_id=CONTRACT, hardware_performance_measured=False,
                scratch_layout_count=len({tuple(v) for v in baseline['scratch_by_word'].values()}),
                coverage=manifest['coverage'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path)
    parser.add_argument('--exit-code',type=int,required=True)
    parser.add_argument('--data',type=Path,required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.log.read_text(errors='replace'),args.exit_code,args.data),sort_keys=True))
    except (ValueError,KeyError,FileNotFoundError) as error:
        raise SystemExit(f'BASELINE_RUN_REJECTED: {error}')
