"""Run an immutable T12 control image, eight T11 shards and DiffTest controls.

Build images and the traced EMU first; this driver never rewrites a build.
Each job keeps its real exit code, raw log, hashes and failure result.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'team/scripts'/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

guard = module('artifact_guard_t12', 'artifact_guard.py')
control = module('control_check_t12', 'check-vdot-regression.py')
functional = module('functional_check_t12', 'check-vdot-run.py')
negative = module('negative_check_t12', 'check-vdot-negative.py')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def stamp():
    return datetime.now().astimezone().isoformat()

def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def run(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    pins = json.loads(args.hardware_pins.read_text())
    require(pins['VDOT_T12_TRACE']=='1' and pins['config']=='MinimalConfig' and pins['NUM_CORES']==1,
            'wrong observer/configuration pins')
    require(args.fu_latency==(2 if pins.get('VDOT_T14_FUSED_INPUT')=='1' else 3),
            'FU latency does not match the elaboration variant')
    require(pins['emu_sha256']==sha(args.emu), 'EMU does not match finished build pins')
    def hardware_guard():
        for name, value in pins['files'].items():
            require(sha(ROOT/name)==value, 'hardware source drift: '+name)
        for name, value in pins.get('dependency_files', {}).items():
            require(sha(ROOT/name)==value, 'dependency source drift: '+name)
        require(sha(args.emu)==pins['emu_sha256'], 'EMU changed')
    hardware_guard()
    ref = args.reference_root/'build/riscv64-nemu-interpreter-so'
    reference = guard.verify_nemu(args.reference_root, ref, 'reference')
    save(out/'reference-provenance.json', reference)
    save(out/'hardware-pins.json', pins)
    guard.verify_sums(args.control/'inputs.sha256')
    jobs = [('control', args.control/'vdot-regression.bin', None, ref),
            ('hello-vadd', args.hello, None, ref),
            ('negative-vdot', args.matrix/'build-0/vdot-exceptions.bin', None, args.negative_reference)]
    for i in range(8):
        data = args.matrix/f'data-{i}'
        image = args.matrix/f'build-{i}/vdot-exceptions.bin'
        provenance = guard.verify_build(args.matrix/f'build-{i}', image, data, 'vdot', 'full')
        save(out/f'functional-{i}-build.json', provenance)
        jobs.append((f'functional-{i}', image, data, ref))
    # Freeze the exact eight inputs against the previously accepted parent corpus.
    parent = ROOT/'team/evidence/t10-t11-fullcore-20261013/parent'
    expected = [json.loads(x) for x in (parent/'cases.jsonl').read_text().splitlines()]
    expected += json.loads((parent/'exceptions.json').read_text())
    by_id = {x['id']: x for x in expected}
    seen = {}; total = 0
    for i in range(8):
        data = args.matrix/f'data-{i}'
        cases = [json.loads(x) for x in (data/'cases.jsonl').read_text().splitlines()]
        cases += json.loads((data/'exceptions.json').read_text())
        for case in cases:
            require(case==by_id.get(case['id']), 'matrix differs from frozen parent: '+case['id'])
            require(case['id'] not in seen or case['id']=='D00', 'unexpected duplicate matrix case')
            seen[case['id']] = case
            total += 1
    require(set(seen)==set(by_id) and len(seen)==117 and total==124, 'incomplete fixed matrix')
    save(out/'matrix-union.json', {'unique':117, 'executed':124, 'repeated_control':'D00',
                                 'parent_files':{x:sha(parent/x) for x in ('cases.jsonl','exceptions.json')}})
    def job(name, image, data, selected_ref):
        directory = out/name
        directory.mkdir()
        command = ['timeout', args.timeout, 'stdbuf', '-o0', '-e0', str(args.emu), '-i', str(image),
                   '--flash='+str(args.flash), '--ram-size=128MB', '--diff='+str(selected_ref),
                   '--max-cycles=5000000']
        record = {'name':name, 'status':'RUNNING', 'started':stamp(), 'command':command,
                  'files':{str(p):sha(p) for p in (args.emu, ref, selected_ref, args.flash, image)}}
        save(directory/'runtime.json', record)
        env = os.environ.copy()
        env.pop('XS_NEGATIVE_VECTOR_TARGET', None)
        if name=='negative-vdot': env['XS_NEGATIVE_VECTOR_TARGET']='vdot'
        try:
            # Separate descriptors: the simulator/reference can reconfigure C stdio
            # buffering after stdbuf. Never merge UART bytes with SV printf bytes.
            with (directory/'stdout.log').open('wb') as stdout, (directory/'stderr.log').open('wb') as stderr:
                rc = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr).returncode
            (directory/'run.log').write_bytes((directory/'stderr.log').read_bytes()+(directory/'stdout.log').read_bytes())
            record['log_format'] = 'separate-streams-v1; derived run.log = stderr.log + stdout.log'
            record['raw_logs_sha256'] = {n:sha(directory/n) for n in ('stdout.log','stderr.log')}
            (directory/'exit-code.txt').write_text(str(rc)+'\n')
            record['exit_code'] = rc
            text = (directory/'run.log').read_text(errors='strict')
            events, uart = control.extract_events(text)
            (directory/'uart.log').write_text(uart)
            require(all(sha(p)==h for p,h in record['files'].items()), 'runtime artifact drift')
            require('The first instruction of core 0 has commited. Difftest enabled.' in text,
                    'missing DiffTest runtime banner')
            require('The reference model is '+str(selected_ref) in text, 'wrong loaded reference path')
            if name=='control':
                result = control.check(text, json.loads((args.control/'data/manifest.json').read_text()), rc, fu_latency=args.fu_latency)
                save(directory/'control-result.json', result)
                require(result['status']=='T12_CONTROL_REGRESSION_PASS', 'control coverage incomplete')
                record['status'] = result['status']
            elif name=='negative-vdot':
                record.update(negative.check(text,rc))
            elif data:
                result = functional.validate(uart, 'full', rc, data, require_diff=True)
                save(directory/'functional-result.json', result)
                record['status'] = 'VDOT_MATRIX_SHARD_PASS'
            else:
                require(rc==0 and 'HELLO_VADD_PASS' in uart and 'HIT GOOD TRAP' in uart,
                        'hello/vadd did not pass')
                require(not re.search(r'HIT BAD TRAP|different at pc|Assertion failed',text),'hello/vadd failure')
                record['status'] = 'HELLO_VADD_PASS'
        except Exception as exc:
            record.update(status='FAILED', error=repr(exc))
        record['finished'] = stamp()
        save(directory/'result.json', record)
        print(name, record['status'], record.get('error',''), flush=True)
        return record
    records = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(job, *item) for item in jobs]
        for future in as_completed(futures):
            records.append(future.result())
            save(out/'progress.json', records)
    hardware_guard()
    guard.verify_nemu(args.reference_root, ref, 'reference')
    guard.verify_sums(args.control/'inputs.sha256')
    for i in range(8):
        guard.verify_build(args.matrix/f'build-{i}', args.matrix/f'build-{i}/vdot-exceptions.bin',
                           args.matrix/f'data-{i}', 'vdot', 'full')
    negative_record = next(x for x in records if x['name']=='negative-vdot')
    normal = next(x for x in records if x['name']=='functional-0')
    image = str(args.matrix/'build-0/vdot-exceptions.bin')
    require(negative_record['files'][image]==normal['files'][image], 'negative recovery image mismatch')
    passed = len(records)==11 and all(x['status']!='FAILED' for x in records)
    result = {'status':'T12_FULLCORE_SUITE_PASS' if passed else 'T12_FULLCORE_SUITE_FAILED',
              'finished':stamp(), 'matrix_unique':117, 'matrix_executed':124, 'runs':records}
    save(out/'result.json',result)
    print(result['status'], flush=True)
    return 0 if passed else 1

if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output','hardware-pins','emu','reference-root','negative-reference','flash','hello','control','matrix'):
        parser.add_argument('--'+name, type=lambda x:Path(x).resolve(), required=True)
    parser.add_argument('--jobs', type=int, choices=(1,2,4,8), default=2)
    parser.add_argument('--timeout', default='120m')
    parser.add_argument('--fu-latency', type=int, choices=(2,3), default=3)
    raise SystemExit(run(parser.parse_args()))
