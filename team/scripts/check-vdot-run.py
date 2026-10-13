"""Check actual workload logs; selftest evidence cannot certify the extension."""
import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path
import re

CONTRACT = 'vdot-s8x8-r32-v0.1'
SELFTEST = {'H00-vadd-control':0x02940557,'H01-ebreak':0x00100073,
            'H02-VS-off':0x00100073,'H03-vstart7':0x00100073,'H04-vill':0x00100073,
            'H05-vadd-initial':0x02940557,'H06-vadd-clean':0x02940557}
LEGAL_CONTROLS={'H00-vadd-control','H05-vadd-initial','H06-vadd-clean'}


def fields(line):
    return dict(re.findall(r'([a-zA-Z0-9_]+)=([^\s]+)',line))


def expand_packed_records(content):
    """Losslessly expand packed-u64-v1 into original verbose records.

    No successful record is inferred: all 34 original numeric fields must be
    present in the payload, and the existing independent checks still run.
    """
    lines=content.splitlines()
    packed=[line for line in lines if line.startswith(('VDOT_PACKED','HARNESS_PACKED'))]
    markers=[line for line in lines if line.startswith('VDOT_LOG_FORMAT')]
    if not markers and not packed:
        return content
    if markers!=['VDOT_LOG_FORMAT packed-u64-v1'] or not packed:
        raise ValueError('missing, duplicate or unsupported packed log format')
    if any(line.startswith(('VDOT_CASE ','HARNESS_NEGATIVE ')) for line in lines):
        raise ValueError('mixed packed and verbose records')
    expanded=[]
    names=('instruction','trap_count','expected_cause','actual_cause','fault_pc','actual_epc',
           'resume_pc','mtval','pre_mstatus','raw_mstatus','capture_phase','protocol_errors','requested_vs')
    decimal={'trap_count','capture_phase','requested_vs','all32_checked','pre32_checked','guards_ok'}
    for line in lines:
        if not line.startswith(('VDOT_PACKED','HARNESS_PACKED')):
            expanded.append(line);continue
        m=re.fullmatch(r'(VDOT_PACKED|HARNESS_PACKED) id=([^\s=]+) result=([A-Z_]+) payload=([A-Za-z0-9+/=]+)',line)
        if not m:raise ValueError('malformed packed record')
        try:payload=base64.b64decode(m[4],validate=True)
        except binascii.Error as e:raise ValueError('invalid packed base64') from e
        if base64.b64encode(payload).decode()!=m[4]:raise ValueError('noncanonical packed base64')
        values=[]; pos=0
        while pos<len(payload) and len(values)<34:
            tag=payload[pos];pos+=1
            if tag<34:
                if tag>=len(values):raise ValueError('invalid packed back-reference')
                values.append(values[tag]);continue
            if tag!=128:raise ValueError('invalid packed literal tag')
            value=0
            for byte_index in range(10):
                if pos>=len(payload):raise ValueError('truncated packed integer')
                byte=payload[pos];pos+=1
                if byte_index==9 and byte>1:raise ValueError('packed integer overflows uint64')
                value|=(byte&127)<<(7*byte_index)
                if byte<128:
                    if byte_index and byte==0:raise ValueError('noncanonical packed integer')
                    break
            else:raise ValueError('unterminated packed integer')
            values.append(value)
        if len(values)!=34 or pos!=len(payload):raise ValueError('wrong packed field count or trailing bytes')
        record={'id':m[2],'result':m[3]}
        record.update({key:(str(v) if key in decimal else hex(v)) for key,v in zip(names,values[:13])})
        record['pre_csr']='/'.join(hex(v) for v in values[13:19])
        record['post_csr']='/'.join(hex(v) for v in values[19:25])
        for key,i in (('pre_vd128',25),('expected_vd128',27),('post_vd128',29)):
            record[key]='0x'+format(values[i]|(values[i+1]<<64),'032x')
        record.update({key:str(values[i]) for key,i in (('all32_checked',31),('pre32_checked',32),('guards_ok',33))})
        prefix='VDOT_CASE' if m[1]=='VDOT_PACKED' else 'HARNESS_NEGATIVE'
        expanded.append(prefix+' '+' '.join(f'{k}={v}' for k,v in record.items()))
    return '\n'.join(expanded)


def validate(content, mode, exit_code, data, *, expect_unextended=False, require_diff=False):
    content = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',content)
    content = expand_packed_records(content)
    if f'VDOT_BEGIN contract={CONTRACT} mode={mode}' not in content:
        raise ValueError('missing matching mode/contract begin marker')
    if 'HARNESS_SELFTEST_PASS cases=7 negative_controls=3' not in content:
        raise ValueError('harness selftest did not complete')
    negative = [fields(line) for line in content.splitlines() if line.startswith('HARNESS_NEGATIVE ')]
    if len(negative)!=3 or {n.get('id') for n in negative}!={'N01-wrong-pc','N02-wrong-high-byte','N03-wrong-vs'}:
        raise ValueError('missing or duplicate negative controls')
    by_id={n['id']:n for n in negative}
    if (by_id['N01-wrong-pc'].get('result')!='TRAP_PROTOCOL' or
        int(by_id['N01-wrong-pc'].get('protocol_errors','0'),0)!=2 or
        by_id['N02-wrong-high-byte'].get('result')!='VECTOR_CHANGED' or
        by_id['N03-wrong-vs'].get('result')!='VS_CHANGED'):
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
        wanted_cause=(0 if name in legal_by_id else 2) if mode=='full' else (0 if name in LEGAL_CONTROLS else 3)
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
            wanted_vector=0xFFFFFFFFFFFFFFFF0000000000000000 if name in LEGAL_CONTROLS else (1<<128)-1
            if int(r['post_vd128'],0)!=wanted_vector:
                raise ValueError(f'{name}: selftest destination disagrees with known expectation')
        if int(r['resume_pc'],0)!=int(r['fault_pc'],0)+4:
            raise ValueError(f'{name}: wrong 32-bit resume site')
        if mode=='full':
            cfg=legal_by_id[name]['config'] if name in legal_by_id else exceptions_by_id[name]
        else:
            cfg=dict(vtype=0x100 if name=='H04-vill' else 0,vl=8,
                     vstart=7 if name=='H03-vstart7' else 0,vxrm=3,vxsat=1,
                     vs_off=int(name=='H02-VS-off'),vs=1 if name=='H05-vadd-initial' else 2 if name=='H06-vadd-clean' else 3)
        csr_type=(1<<63) if cfg['vtype']&0x100 else cfg['vtype']
        csr_vl=0 if cfg['vtype']&0x100 else cfg['vl']
        wanted_csrs=(csr_type,csr_vl,cfg['vstart'],cfg['vxrm'],cfg['vxsat'],(cfg['vxrm']<<1)|cfg['vxsat'])
        if tuple(int(x,0) for x in r['pre_csr'].split('/'))!=wanted_csrs:
            raise ValueError(f'{name}: initial vector state not reached')
        off=cfg.get('vs_off',0)
        before_vs=(int(r['pre_mstatus'],0)>>9)&3
        after_vs=(int(r['raw_mstatus'],0)>>9)&3
        if int(r.get('capture_phase','-1'))!=(2 if off else 1) or before_vs!=(0 if off else cfg['vs']):
            raise ValueError(f'{name}: VS/capture phase mismatch')
        if (off and after_vs!=0) or (cause==0 and after_vs!=3) or \
           (cause!=0 and not off and after_vs not in (before_vs,3)):
            raise ValueError(f'{name}: wrong vector status')
        if int(r.get('requested_vs','-1'))!=(0 if off else cfg['vs']) or int(r.get('pre32_checked','0'))!=1:
            raise ValueError(f'{name}: missing exact initial state observation')
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
