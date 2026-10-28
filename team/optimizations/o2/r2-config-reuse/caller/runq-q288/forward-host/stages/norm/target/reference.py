"""Qualify the exact first-token image, its guards and genuine BAD trap."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import resource
import shutil
import signal
import struct

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('first_token_build', HERE / 'build.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
c, old = b.c, b.cr.old
need, read, save, digest = b.need, b.read, b.save, b.digest
CASES = [('negative', 4, True), ('fr', 3, False), ('ta', 4, False), ('replay', 4, False)]
MAX_CALLS = 100_000_000


def inputs(build, adapter, identity_path):
    record = read(build / 'result.json')
    need(record['contract'] == b.CONTRACT and record['status'] == b.STATIC, 'new first-token static identity')
    parent, files, identity, checker = b.cr.verify_inputs(Path(record['qualified_build']), adapter, identity_path)
    need(record['qualified_consumer_object_sha256'] == parent['artifacts'][b.CORE], 'same qualified combined object')
    for path, value in record['external_pins'].items(): c.pin(files, path, value)
    for rel, value in record['source_pins'].items():
        c.pin(files, b.REPO / rel, value); c.pin(files, build / 'source/repo' / rel, value)
    for key, root in (('artifacts', build), ('fixtures', build / 'fixture'), ('actual_source_pins', build / 'source')):
        for name, value in record[key].items(): c.pin(files, root / name, value)
    for path in (build / 'result.json', build / 'tools.json', identity_path, HERE / 'reference.py', *c.module_files()):
        c.pin(files, path)
    for tool in read(build / 'tools.json').values(): c.pin(files, tool['path'], tool['sha256'])
    _, inspection = b.inspect(build, record)
    inspection = json.loads(json.dumps(inspection))
    need(all(record[key] == value for key, value in inspection.items()), 'rechecked first-token static inspection')
    checker.verify_files(files)
    return record, files, identity, checker


def image(build, record, method, negative, uart):
    need(method in (3, 4) and type(negative) is bool and uart in (0, 1), 'bounded explicit controls')
    raw = bytearray((build / (b.PREFIX + '.bin')).read_bytes())
    offset = record['control_offset']; controls = [method, int(negative), uart]
    raw[offset:offset + 12] = struct.pack('<3I', *controls)
    return raw, dict(base_sha256=record['artifacts'][b.PREFIX + '.bin'], offset=offset,
                     controls=controls, sha256=c.base.f.h.sha(raw))


def validate(build, dest, record, receipt, method, negative):
    need(receipt.get('process_started') is True and receipt.get('direct_child_reaped') is True and
         receipt.get('process_group_absent_after_exit') is True and not receipt.get('residual_process_group') and
         not receipt.get('timed_out') and receipt['exit_code'] == (2 if negative else 0), 'complete owned reference process')
    result, abi = read(dest / 'reference-result.json'), read(dest / 'abi.json')
    pcs = [int(x, 16) for x in record['failure_traps']] if negative else [int(record['success_trap'], 16)]
    need(result['state'] == 2 and result['reason'] == ('bad_trap' if negative else 'good_trap') and
         result['halt_ret'] == (94 if negative else 0) and result['halt_pc'] in pcs and result['pc'] == result['halt_pc'] + 4 and
         0 < result['retired'] <= result['api_calls'] <= MAX_CALLS and result['memory_dumps'] == len(record['dump_plan']) and
         result['xiangshan_cycles_measured'] is False and all(result[n] == 0 for n in ('mcause', 'mepc', 'mtval')),
         'actual bounded reference terminal state, trap PC and no exception')
    need(abi['register_bytes'] == abi['header_span'] == 1400 and abi['initial_pc'] == 0x10000000 and abi['initial_mode'] == 3,
         'original actual reset/ABI')
    plain = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', (dest / 'stdout.log').read_text())
    need(not (dest / 'stderr.log').read_bytes() and not any(x in plain.lower() for x in
         ('pma check failed', 'critical error', 'reference_adapter_reject', 'abort')), 'no unexplained reference fault')
    trap_lines = [line for line in plain.splitlines() if 'HIT ' in line and ' TRAP' in line]
    need(len(trap_lines) <= 1, 'at most one reference trap transcript')
    for line in trap_lines:
        match = re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT (GOOD|BAD) TRAP at pc = (0x[0-9a-fA-F]+)', line)
        need(match is not None and match[1] == ('BAD' if negative else 'GOOD') and int(match[2], 16) == result['halt_pc'],
             'canonical actual trap transcript')
    sizes = {name: size for name, _, size in record['dump_plan']}
    sizes.update({'initial-registers.bin': 1400, 'final-registers.bin': 1400, 'initial-csrs.bin': 32768, 'final-csrs.bin': 32768})
    need({p.name for p in dest.glob('*.bin')} == set(sizes) | {'image.bin'}, 'exact whole dump inventory')
    for name, size in sizes.items(): need((dest / name).stat().st_size == size, 'complete raw size: ' + name)
    raw_image, control = image(build, record, method, negative, 0)
    need((dest / 'image.bin').read_bytes() == raw_image and read(dest / 'image-control.json') == control, 'only explicit reference controls differ')
    for _, name in c.MODELS:
        need(digest(dest / name.replace('.bin', '-after.bin')) == record['fixtures'][name], 'whole model unchanged: ' + name)
    need(digest(dest / 'gold-after.bin') == record['fixtures']['host-state-p0.bin'], 'whole independent gold unchanged')
    report = struct.unpack('<64Q', (dest / 'report.bin').read_bytes())
    need(report[:10] == (b.MAGIC, 1, method, 94 if negative else 0, 1, int(negative), 0, 1,
                         0 if negative else b.S, 152476 if negative else 0), 'complete report and exact negative location')
    need(report[10] & 0x6000 and report[10] & 0x600 and report[11] == 16 and not any(report[12:16]) and
         report[20] == record['expected_flags'][str(method)] and report[21] == 1 and not any(report[22:]),
         'FS/VS, VLEN128, RNE, qualified flags, guards and reserved report extent')
    need(0 < report[19] - report[16] < 2**32 and 0 < report[18] - report[17] < 2**32, 'bounded complete reference counter window')
    guard = struct.pack('<2Q', b.GUARD, b.GUARD); expected = bytearray((build / 'fixture/host-state-p0.bin').read_bytes())
    if negative: expected[152476] ^= 1
    raw = (dest / 'guarded-state.bin').read_bytes()
    need(raw == guard + expected + guard, 'all state bytes and both entire guards')
    rejection = None
    try: old.compare_normal_states(build, raw[16:-16], 1)
    except ValueError as error: rejection = str(error)
    need(rejection == ('complete_state_mismatch position=0 byte=152476' if negative else None),
         'same complete-state comparator accepts positives and rejects actual negative')
    tls = bytearray(bytes([0x6b]) * 16 + bytes(64) + bytes([0xa7]) * 16)
    offset = 16 + record['tls_errno_offset']; need(16 <= offset <= 76, 'errno wholly inside static TLS')
    tls[offset:offset + 4] = struct.pack('<I', 12345)
    need((dest / 'tls.bin').read_bytes() == tls and (dest / 'control.bin').read_bytes() == struct.pack('<3I', method, int(negative), 0),
         'whole TLS, errno, TLS guards and actual controls')
    return dict(contract=b.CONTRACT, status='EXPECTED_FIRST_TOKEN_REFERENCE_REJECTION' if negative else 'FIRST_TOKEN_COMPLETE_REFERENCE_PASS',
        method=method, negative=negative, report=list(report), halt_pc=result['halt_pc'], api_calls=result['api_calls'], retired=result['retired'],
        normal_comparator_rejection=rejection, raw_sha256={name: digest(dest / name) for name in sizes},
        target_emu_runs=0, performance_qualified=False)


def run(build, adapter, identity_path, output):
    need(not output.exists() and len(os.sched_getaffinity(0)) == 1, 'fresh single-CPU reference campaign')
    record, files, identity, checker = inputs(build, adapter, identity_path)
    old.r.parent.outside_inputs(output, [b.REPO, build, adapter, identity_path.parent,
        Path(identity['configuration']['hardware_source']), Path(record['am_home'])])
    _, hard = resource.getrlimit(resource.RLIMIT_FSIZE); limit = 128 * 1024 * 1024
    need(hard == resource.RLIM_INFINITY or hard >= limit, 'complete raw reference budget')
    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, hard))
    output.mkdir(parents=True); save(output / 'runtime-inputs.json', files); old.snapshot_runtime(output, files)
    shutil.copyfile(identity_path, output / 'parent-identity.json')
    state = dict(contract=b.CONTRACT, status='RUNNING', started=c.base.f.h.now(), records=[], active_pid=None,
                 reference_runs=0, target_emu_runs=0, performance_qualified=False)
    persist = lambda: save(output / 'state.json', state); persist(); validations = {}
    try:
        for label, method, negative in CASES:
            dest = output / label; dest.mkdir(); raw, control = image(build, record, method, negative, 0)
            (dest / 'image.bin').write_bytes(raw); save(dest / 'image-control.json', control); del raw
            casefiles = dict(files); c.pin(casefiles, dest / 'image.bin'); c.pin(casefiles, dest / 'image-control.json')
            save(dest / 'runtime-inputs.json', casefiles); checker.verify_files(casefiles)
            argv = [str(adapter / 'reference-runner'), identity['configuration']['reference'], str(dest / 'image.bin'), str(dest),
                    'builtin', str(MAX_CALLS), '600', str(build / 'dump-plan.txt'), '1']
            rec = dict(contract=b.CONTRACT, name=label, method=method, negative=negative, command=argv, cwd=str(dest),
                started=c.base.f.h.now(), process_started=False, exit_code=None, status='RUNNING',
                cpu_affinity=sorted(os.sched_getaffinity(0)), max_api_calls=MAX_CALLS, wall_limit_seconds=600,
                external_timeout_seconds=630, max_output_file_bytes=limit)
            state['records'].append(rec); state['reference_runs'] += 1
            def progress():
                state['active_pid'] = rec.get('pid') if not rec.get('process_group_absent_after_exit') else None
                save(dest / 'result.json', rec); persist()
            progress()
            try:
                with (dest / 'stdout.log').open('wb') as stdout, (dest / 'stderr.log').open('wb') as stderr:
                    old.previous.spawn(argv, dest, stdout, stderr, rec, progress, dict(os.environ), 630)
                checked = validate(build, dest, record, rec, method, negative); save(dest / 'validation.json', checked)
                checker.verify_files(casefiles); rec.update(status=checked['status'], validation_sha256=digest(dest / 'validation.json'))
                validations[label] = checked
            except BaseException as error:
                rec.update(status='FAILED', error=repr(error)); raise
            finally:
                rec['finished'] = c.base.f.h.now(); progress()
            print(label, rec['status'], flush=True)
        need(validations['ta'] == validations['replay'], 'complete independent reference replay')
        checker.verify_files(files); state['status'] = b.REFERENCE_PASS
        save(output / 'results.json', dict(contract=b.CONTRACT, status=state['status'], records=state['records'],
             validations=validations, reference_runs=4, target_emu_runs=0, performance_qualified=False))
    except BaseException as error:
        state.update(status='FAILED', error=repr(error)); raise
    finally:
        state['finished'] = c.base.f.h.now(); persist()
    return state


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('first-token reference signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'adapter', 'identity', 'output'): parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])
    result = run(*(getattr(args, name).resolve() for name in ('build', 'adapter', 'identity', 'output')))
    print(json.dumps({key: result[key] for key in ('contract', 'status', 'reference_runs', 'performance_qualified')}, indent=2))
