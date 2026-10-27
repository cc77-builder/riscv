"""Eight full-state references for the new norm consumer, on isolated CPU slots."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import resource
import signal
import struct
import types

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('norm_consumer_build', HERE / 'build.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
w, old = b.w, b.w.old
need, read, save, digest = b.need, b.read, b.save, b.digest
CASES = old.CASES


def verify_inputs(build, adapter, identity_path):
    record = read(build / 'result.json')
    api = record['contract'] == b.API_CONTRACT
    need(record['contract'] == (b.API_CONTRACT if api else b.CONTRACT) and
         record['status'] == (b.API_STATIC if api else b.STATIC), 'explicit new build identity')
    _, identity, checker, files = w.verify_inputs(Path(record['original_w2_build']), adapter, identity_path)
    for path, value in record['external_pins'].items():
        b.pin(files, path, value)
    for rel, value in record['source_pins'].items():
        b.pin(files, b.REPO / rel, value); b.pin(files, build / 'source/repo' / rel, value)
    for group, root in (('artifacts', build), ('fixtures', build / 'fixture'),
                        ('actual_source_pins', build / 'source')):
        for name, value in record[group].items():
            b.pin(files, root / name, value)
    for path in (build / 'result.json', build / 'tools.json', identity_path, *b.module_files(), HERE / 'run.py'):
        b.pin(files, path)
    for tool in read(build / 'tools.json').values():
        b.pin(files, tool['path'], tool['sha256'])
    b.inspect(build, b.API_PREFIX if api else b.PREFIX, record, Path(record['norm_build']))
    need(digest(build / b.CORE) == record['kernel_identity']['consumer_object_sha256'] ==
         record['qualified_consumer_object_sha256'], 'same complete new consumer object')
    checker.verify_files(files)
    return record, files, identity, checker


def image(build, record, method, kind):
    need(kind in ('normal', 'output'), 'only the new eight-case scope')
    raw = bytearray((build / (b.PREFIX + '.bin')).read_bytes())
    offset = record['control_offset']; controls = [method, 3, int(kind == 'output'), 1]
    raw[offset:offset + 16] = struct.pack('<4I', *controls)
    return raw, dict(base_sha256=record['artifacts'][b.PREFIX + '.bin'], offset=offset, controls=controls,
                     w2_pack_fault=False, w2_packed_offset=record['w2_packed_offset'], sha256=b.base.f.h.sha(raw))


def validate(build, dest, method, negative, receipt):
    need(receipt.get('direct_child_reaped') is True, 'direct reference child reaped')
    actual = b.bind(w.validate, image=image)(build, dest, read(build / 'result.json'), method,
                                           'output' if negative else 'normal', receipt)
    actual.update(contract=b.CONTRACT, status='EXPECTED_NORM_W2_FULL_STATE_REJECTION' if negative else
                  'NORM_W2_FORWARD_COMPLETE_REFERENCE_PASS')
    return actual


def one(build, adapter, identity_path, output, case):
    need(not output.exists() and len(os.sched_getaffinity(0)) == 1, 'fresh single-CPU reference case')
    method, negative = {name: (method, negative) for name, method, negative in CASES}[case]
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE); limit = 128 * 1024 * 1024
    need(hard == resource.RLIM_INFINITY or hard >= limit, 'whole reference image and dump budget')
    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, hard))
    record, files, identity, checker = verify_inputs(build, adapter, identity_path)
    need(record['contract'] == b.CONTRACT, 'forward case uses the forward build')
    old.r.parent.outside_inputs(output, [b.REPO, build, adapter, identity_path.parent,
        identity['configuration']['hardware_source'], identity['configuration']['am_home']])
    output.mkdir(parents=True)
    raw, control = image(build, record, method, 'output' if negative else 'normal')
    (output / 'image.bin').write_bytes(raw); save(output / 'image-control.json', control); del raw
    b.pin(files, output / 'image.bin'); b.pin(files, output / 'image-control.json')
    save(output / 'runtime-inputs.json', files)
    argv = [str(adapter / 'reference-runner'), identity['configuration']['reference'], str(output / 'image.bin'),
            str(output), 'builtin', str(w.MAX_CALLS), '600', str(build / 'dump-plan.txt'), '1']
    receipt = dict(contract=b.CONTRACT, name=case, method=method, negative=negative, command=argv,
                   cwd=str(output), started=b.base.f.h.now(), process_started=False, exit_code=None,
                   status='RUNNING', cpu_affinity=sorted(os.sched_getaffinity(0)), max_api_calls=w.MAX_CALLS,
                   wall_limit_seconds=600, external_timeout_seconds=630, max_output_file_bytes=limit)
    progress = lambda: save(output / 'result.json', receipt)
    progress()
    try:
        checker.verify_files(files)
        with (output / 'stdout.log').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
            old.previous.spawn(argv, output, stdout, stderr, receipt, progress, dict(os.environ), 630)
        checked = validate(build, output, method, negative, receipt)
        save(output / 'validation.json', checked)
        checker.verify_files(files)
        receipt.update(status=checked['status'], validation_sha256=digest(output / 'validation.json'))
        print(case, checked['status'], flush=True)
    except BaseException as error:
        receipt.update(status='FAILED', error=repr(error)); raise
    finally:
        receipt['finished'] = b.base.f.h.now(); progress()
    return receipt


def campaign(build, adapter, identity_path, output, cpus):
    need(1 <= len(cpus) <= 2, 'at most two reference slots beside two norm EMUs')
    # The mature scheduler retains all ownership checks, termination handling,
    # negative-first ordering, replay equality and five-method flag gates.
    # HERE redirects its case CLI to this file; b supplies only identity/time.
    scheduler = b.bind(old.campaign, HERE=HERE, verify_inputs=verify_inputs,
                       b=types.SimpleNamespace(CONTRACT=b.CONTRACT, f=b.base.f))
    state = scheduler(build, adapter, identity_path, output, cpus)
    need(state['status'] == 'PURE_FORWARD_REFERENCE_CAMPAIGN_PASS' and not state['active']
         and not state['cleanup_unknown'] and state['reference_runs'] == 8, 'all scheduler gates completed')
    results = read(output / 'results.json')
    need(results['contract'] == b.CONTRACT, 'new identity throughout scheduler output')
    state.update(status=b.PASS, target_emu_runs=0)
    results['status'] = b.PASS
    results['reused_scheduler_sha256'] = digest(Path(old.__file__))
    results['reused_numerical_validator_sha256'] = digest(Path(w.__file__))
    save(output / 'results.json', results); save(output / 'state.json', state)
    return state


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('norm consumer reference signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'adapter', 'identity', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--case', choices=[name for name, _, _ in CASES])
    parser.add_argument('--cpus', default='2,3')
    args = parser.parse_args(); paths = [getattr(args, name).resolve() for name in ('build', 'adapter', 'identity', 'output')]
    result = one(*paths, args.case) if args.case else campaign(*paths, [int(value) for value in args.cpus.split(',')])
    print(json.dumps(dict(contract=b.CONTRACT, status=result['status']), indent=2))
