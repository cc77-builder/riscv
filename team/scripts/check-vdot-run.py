"""Check actual workload logs; selftest evidence cannot certify the extension."""
import argparse
import hashlib
import json
from pathlib import Path
import re

CONTRACT = 'vdot-s8x8-r32-v0.1'
SELFTEST = {'H00-vadd-control':0x02940557,'H01-ebreak':0x00100073,
            'H02-VS-off':0x00100073,'H03-vstart7':0x00100073,'H04-vill':0x00100073}


def fields(line):
    return dict(re.findall(r'([a-zA-Z0-9_]+)=([^\s]+)',line))


def validate(content, mode, exit_code, data, *, expect_unextended=False, require_diff=False):
    content = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',content)
    if f'VDOT_BEGIN contract={CONTRACT} mode={mode}' not in content:
        raise ValueError('missing matching mode/contract begin marker')
    if 'HARNESS_SELFTEST_PASS cases=5 negative_controls=2' not in content:
        raise ValueError('harness selftest did not complete')
    negative = [fields(line) for line in content.splitlines() if line.startswith('HARNESS_NEGATIVE ')]
    if len(negative)!=2 or {n.get('id') for n in negative}!={'N01-wrong-pc','N02-wrong-high-byte'}:
        raise ValueError('missing or duplicate negative controls')
    by_id={n['id']:n for n in negative}
    if (by_id['N01-wrong-pc'].get('result')!='TRAP_PROTOCOL' or
        int(by_id['N01-wrong-pc'].get('protocol_errors','0'),0)!=2 or
        by_id['N02-wrong-high-byte'].get('result')!='VECTOR_CHANGED'):
        raise ValueError('negative controls failed to detect errors')
    manifest = json.loads((data/'manifest.json').read_text())
    raw_cases = (data/'cases.jsonl').read_bytes()
    if manifest['contract_id']!=CONTRACT or hashlib.sha256(raw_cases).hexdigest()!=manifest['cases_sha256']:
        raise ValueError('test data contract/hash mismatch')
    for name,digest in manifest['artifacts_sha256'].items():
        if hashlib.sha256((data/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'generated artifact hash mismatch: {name}')
    fixture = [json.loads(line) for line in raw_cases.splitlines()]
    smoke = fixture[:manifest['smoke_count']]
    exceptions = json.loads((data/'exceptions.json').read_text())
    if len(exceptions)!=manifest['exception_count']:
        raise ValueError('exception manifest count mismatch')
    expected = dict(SELFTEST) if mode=='selftest' else {
        **{c['id']:int(c['instruction'],0) for c in smoke}, **{c['id']:c['word'] for c in exceptions}}
    scope = content
    if mode=='full':
        if content.count('VDOT_EXTENSION_BEGIN')!=1:
            raise ValueError('missing or duplicate extension phase')
        scope=content.split('VDOT_EXTENSION_BEGIN',1)[1]
    records = [fields(line) for line in scope.splitlines() if line.startswith('VDOT_CASE ')]
    summaries = [fields(line) for line in scope.splitlines() if line.startswith('VDOT_SUMMARY ')]
    if len(summaries)!=1:
        raise ValueError('missing or duplicate summary')
    summary=summaries[0]
    if summary.get('mode')!=mode or summary.get('contract')!=CONTRACT:
        raise ValueError('summary mode/contract mismatch')
    if expect_unextended:
        if (mode!='full' or exit_code!=3 or len(records)!=1 or records[0].get('id')!='D00' or
            records[0].get('result')!='TRAP_PROTOCOL' or int(records[0].get('actual_cause','0'),0)!=2 or
            int(records[0].get('protocol_errors','0'),0)!=4 or
            int(summary.get('failed','0'))!=1):
            raise ValueError('expected legal-vdot rejection not observed')
        return dict(status='UNEXTENDED_REJECTION_CONFIRMED',extension_pass=False)
    if exit_code!=0:
        raise ValueError(f'program exit code {exit_code}')
    if re.search(r'\bFAIL[: ]|BAD TRAP',content):
        raise ValueError('failure marker in output')
    if require_diff and ('Difftest enabled' not in content or 'HIT GOOD TRAP' not in content):
        raise ValueError('missing real DiffTest/GOOD TRAP evidence')
    ids=[r.get('id') for r in records]
    if len(set(ids))!=len(ids) or set(ids)!=set(expected):
        raise ValueError('missing, unexpected or duplicate test IDs')
    if any(int(summary.get(k,'-1'))!=len(expected) for k in ('planned','executed','passed')) or \
       any(int(summary.get(k,'-1'))!=0 for k in ('failed','unreachable')):
        raise ValueError('summary counts do not prove complete coverage')
    legal_by_id={c['id']:c for c in smoke}
    exceptions_by_id={c['id']:c for c in exceptions}
    for r in records:
        name=r['id']
        if r.get('result')!='PASS' or int(r.get('instruction','-1'),0)!=expected[name]:
            raise ValueError(f'{name}: wrong result or instruction')
        for key in ('fault_pc','actual_epc','resume_pc','mtval','pre_mstatus','raw_mstatus',
                    'pre_vd128','expected_vd128','post_vd128','pre_csr','post_csr'):
            if key not in r: raise ValueError(f'{name}: missing {key}')
        cause=int(r.get('expected_cause','-1'),0)
        wanted_cause=(0 if name in legal_by_id else 2) if mode=='full' else (0 if name=='H00-vadd-control' else 3)
        if cause!=wanted_cause:
            raise ValueError(f'{name}: wrong expected cause')
        if int(r.get('trap_count','-1'))!=(1 if cause else 0):
            raise ValueError(f'{name}: trap count')
        if cause and (int(r['actual_cause'],0)!=cause or r['actual_epc']!=r['fault_pc']):
            raise ValueError(f'{name}: imprecise trap')
        if r['post_vd128']!=r['expected_vd128'] or r['pre_csr']!=r['post_csr']:
            raise ValueError(f'{name}: vector/CSR state mismatch')
        if cause and r['expected_vd128']!=r['pre_vd128']:
            raise ValueError(f'{name}: exception must preserve the pre-instruction destination')
        if mode=='selftest':
            wanted_vector=0xFFFFFFFFFFFFFFFF0000000000000000 if name=='H00-vadd-control' else (1<<128)-1
            if int(r['post_vd128'],0)!=wanted_vector:
                raise ValueError(f'{name}: selftest destination disagrees with known expectation')
        if int(r['resume_pc'],0)!=int(r['fault_pc'],0)+4:
            raise ValueError(f'{name}: wrong 32-bit resume site')
        if mode=='full':
            cfg=legal_by_id[name]['config'] if name in legal_by_id else exceptions_by_id[name]
        else:
            cfg=dict(vtype=0x100 if name=='H04-vill' else 0,vl=8,
                     vstart=7 if name=='H03-vstart7' else 0,vxrm=3,vxsat=1,
                     vs_off=int(name=='H02-VS-off'))
        csr_type=(1<<63) if cfg['vtype']&0x100 else cfg['vtype']
        csr_vl=0 if cfg['vtype']&0x100 else cfg['vl']
        wanted_csrs=(csr_type,csr_vl,cfg['vstart'],cfg['vxrm'],cfg['vxsat'],(cfg['vxrm']<<1)|cfg['vxsat'])
        if tuple(int(x,0) for x in r['pre_csr'].split('/'))!=wanted_csrs:
            raise ValueError(f'{name}: initial vector state not reached')
        off=cfg.get('vs_off',0)
        if int(r.get('capture_phase','-1'))!=(2 if off else 1) or \
           (((int(r['pre_mstatus'],0)>>9)&3)==0)!=bool(off):
            raise ValueError(f'{name}: VS/capture phase mismatch')
        if (off and ((int(r['raw_mstatus'],0)>>9)&3)!=0) or \
           (cause==0 and ((int(r['raw_mstatus'],0)>>9)&3)!=3):
            raise ValueError(f'{name}: wrong vector status')
        if int(r.get('all32_checked','0'))!=1 or int(r.get('guards_ok','0'))!=1 or \
           int(r.get('protocol_errors','-1'),0)!=0:
            raise ValueError(f'{name}: incomplete state check')
        if name in legal_by_id and int(r['post_vd128'],0)!=int(legal_by_id[name]['expected_128'],16):
            raise ValueError(f'{name}: disagrees with independent oracle')
    return dict(status='HARNESS_SELFTEST_PASS' if mode=='selftest' else 'VDOT_WORKLOAD_PASS',
                mode=mode,executed=len(records),extension_pass=mode=='full',difftest=require_diff)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path)
    parser.add_argument('--mode',choices=('selftest','full'),required=True)
    parser.add_argument('--exit-code',type=int,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--require-diff',action='store_true')
    parser.add_argument('--expect-unextended-rejection',action='store_true')
    args=parser.parse_args()
    try:
        result=validate(args.log.read_text(errors='replace'),args.mode,args.exit_code,args.data,
                        expect_unextended=args.expect_unextended_rejection,require_diff=args.require_diff)
    except (ValueError,KeyError,FileNotFoundError) as error:
        raise SystemExit(f'VDOT_RUN_REJECTED: {error}')
    print(json.dumps(result,sort_keys=True))
