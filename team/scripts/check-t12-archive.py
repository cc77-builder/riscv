"""Recompute T12 archived acceptance without running the DUT again.

Hashes prove archived byte consistency, not a new binary execution or a signature.
Pass the reviewed build source and binary hashes explicitly.
"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'team/scripts'/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

control = module('archive_t12_control', 'check-vdot-regression.py')
functional = module('archive_t12_functional', 'check-vdot-run.py')

def require(ok, message):
    if not ok: raise ValueError(message)

def read(path):
    return gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()

def load(path):
    return json.loads(read(path))

def decode_log(raw):
    # Match Path.read_text() in the actual suite driver: UART uses CRLF while
    # hardware events use LF. Validate raw hashes before text interpretation.
    with io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8', newline=None) as stream:
        return stream.read()

def validate(root, source, emu, reference, flash):
    root = Path(root).resolve()
    hashes = load(root/'archive-manifest.json')
    require(bool(hashes['files']), 'empty archive')
    for name, wanted in hashes['files'].items():
        path = (root/name).resolve()
        require(path.is_relative_to(root), 'archive path escapes root')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==wanted, 'archive byte mismatch: '+name)
    for name, wanted in hashes['raw_log_sha256'].items():
        require(hashlib.sha256(read(root/name)).hexdigest()==wanted, 'decoded log mismatch: '+name)
    pins = load(root/'suite/hardware-pins.json.gz')
    require(pins['source_commit']==source and pins['emu_sha256']==emu, 'unexpected hardware source/binary pins')
    require(pins['config']=='MinimalConfig' and pins['NUM_CORES']==1 and pins['VDOT_T12_TRACE']=='1', 'wrong configuration')
    expected_names = {'control','hello-vadd','negative-vdot'} | {f'functional-{i}' for i in range(8)}
    suite = load(root/'suite/result.json')
    require(suite['status']=='T12_FULLCORE_SUITE_PASS', 'suite was not accepted')
    require(len(suite['runs'])==11 and {x['name'] for x in suite['runs']}==expected_names, 'incomplete suite')
    results = {}; records = {}
    for name in sorted(expected_names):
        directory = root/'suite'/name
        record = load(directory/'result.json')
        original = load(directory/'runtime.json')
        require(record['status'] not in ('RUNNING','FAILED'), 'failed or unfinished job: '+name)
        require(record['files']==original['files'] and record['command']==original['command'], 'runtime receipt drift')
        command = record['command']
        emulator = next(x for x in command if x.endswith('/build/emu'))
        selected = next(x.split('=',1)[1] for x in command if x.startswith('--diff='))
        selected_flash = next(x.split('=',1)[1] for x in command if x.startswith('--flash='))
        require(record['files'][emulator]==emu, 'wrong runtime EMU')
        require(record['files'][selected_flash]==flash, 'wrong runtime flash')
        normal_refs = [v for p,v in record['files'].items() if p.endswith('/reference/build/riscv64-nemu-interpreter-so')]
        require(normal_refs==[reference], 'wrong normal reference')
        if name!='negative-vdot': require(record['files'][selected]==reference, 'positive run used injected reference')
        require(record.get('log_format')=='separate-streams-v1; derived run.log = stderr.log + stdout.log', 'missing separate raw streams')
        raw = {name:read(directory/(name+'.gz')) for name in ('stdout.log','stderr.log')}
        require(all(hashlib.sha256(value).hexdigest()==record['raw_logs_sha256'][name] for name,value in raw.items()), 'raw stream digest mismatch')
        combined = read(directory/'run.log.gz')
        require(combined==raw['stderr.log']+raw['stdout.log'], 'derived log differs from raw streams')
        text = decode_log(combined)
        exit_code = int((directory/'exit-code.txt').read_text())
        require(exit_code==record['exit_code'], 'exit receipt mismatch')
        require('The reference model is '+selected in text, 'loaded reference differs from receipt')
        require('The first instruction of core 0 has commited. Difftest enabled.' in text, 'DiffTest not enabled')
        events, uart = control.extract_events(text)
        if name=='control':
            result = control.check(text, load(root/'control/manifest.json.gz'), exit_code)
            require(result['status']=='T12_CONTROL_REGRESSION_PASS', 'control coverage incomplete')
        elif name.startswith('functional-'):
            index = int(name.split('-')[1])
            result = functional.validate(uart,'full',exit_code,root/f'matrix/data-{index}',require_diff=True)
        elif name=='hello-vadd':
            require(exit_code==0 and 'HELLO_VADD_PASS' in uart and 'HIT GOOD TRAP' in uart, 'hello/vadd incomplete')
            require(not re.search(r'HIT BAD TRAP|different at pc|Assertion failed',text),'hello/vadd failure')
            result = {'status':'HELLO_VADD_PASS'}
        else:
            injection = re.search(r'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=(\d+) pc=(0x[0-9a-f]+) instruction=(0x[0-9a-f]+)',text)
            require(injection is not None and exit_code==1,'negative fixture did not reject')
            mismatch = re.search(r'v'+injection[1]+r'_high different at pc = (0x[0-9a-fA-F]+), right=\s*(0x[0-9a-fA-F]+), wrong =\s*(0x[0-9a-fA-F]+)',text)
            require(mismatch is not None and int(injection[2],16)==int(mismatch[1],16),'negative PC/register mismatch')
            require(int(mismatch[2],16)^int(mismatch[3],16)==1<<36,'negative bit mismatch')
            require(int(injection[3],16)&0xfe00707f==0x0200000b,'negative instruction is not vdot')
            result = {'status':'EXPECTED_VDOT_HIGHBIT_REJECTION'}
        records[name] = record
        results[name] = result
    negative = records['negative-vdot']; positive = records['functional-0']
    negative_image = negative['command'][negative['command'].index('-i')+1]
    positive_image = positive['command'][positive['command'].index('-i')+1]
    require(negative['files'][negative_image]==positive['files'][positive_image], 'normal recovery changed the image')
    parent = ROOT/'team/evidence/t10-t11-fullcore-20261013/parent'
    expected = [json.loads(x) for x in (parent/'cases.jsonl').read_text().splitlines()]
    expected += load(parent/'exceptions.json')
    by_id = {x['id']:x for x in expected}; seen = {}; total = 0
    for i in range(8):
        data = root/f'matrix/data-{i}'
        cases = [json.loads(x) for x in (data/'cases.jsonl').read_text().splitlines()]+load(data/'exceptions.json')
        for case in cases:
            require(case==by_id.get(case['id']), 'matrix case differs from reviewed parent')
            require(case['id'] not in seen or case['id']=='D00','unexpected duplicate case')
            seen[case['id']] = case; total += 1
    require(set(seen)==set(by_id) and len(seen)==117 and total==124,'matrix incomplete')
    return {'status':'T12_ARCHIVE_RECHECK_PASS','scope':'recheck stored logs and receipts; not a new DUT run',
            'hardware_source':source,'emu_sha256':emu,'reference_sha256':reference,
            'matrix_unique':117,'matrix_executed':124,'results':results}

if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    for name in ('source','emu','reference','flash'):
        parser.add_argument('--expected-'+name,required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.archive,args.expected_source,args.expected_emu,
                              args.expected_reference,args.expected_flash),indent=2))
