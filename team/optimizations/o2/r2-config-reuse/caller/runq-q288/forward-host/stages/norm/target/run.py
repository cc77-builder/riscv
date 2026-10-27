"""Freeze and run four isolated complete first-token correctness cases."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import time
import types

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('first_token_raw_audit', HERE / 'audit.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
ref, b, c, old = a.ref, a.b, a.c, a.ref.old
need, read, save, sha = a.need, a.read, a.save, a.sha
MAX_CYCLES = 40_000_000
TIMEOUT = 28_800
RAW_LIMIT = 4 * 1024 * 1024 * 1024
PROFILE = 'r2-s3-w2-norm-first-token-resources-v1'
PASS = 'NORM_W2_FIRST_TOKEN_TARGET_CAMPAIGN_PASS'


def qualified(build, reference, adapter, identity_path):
    record, files, initial, checker = ref.inputs(build, adapter, identity_path)
    need(record.get('exact_flags_guard') == 1, 'new exact flags gate before all positive/negative counter UART')
    summary, state, runtime = read(reference / 'results.json'), read(reference / 'state.json'), read(reference / 'runtime-inputs.json')
    need(summary['contract'] == b.CONTRACT and summary['status'] == state['status'] == b.REFERENCE_PASS and
         state['active_pid'] is None and state['reference_runs'] == 4 and state.get('finished'), 'closed exact first-token reference qualification')
    need(set(summary['validations']) == {x[0] for x in ref.CASES}, 'exact four qualified cases')
    for key, root in (('artifacts', build), ('fixtures', build / 'fixture'), ('actual_source_pins', build / 'source')):
        for name, value in record[key].items(): need(runtime[str(root / name)] == value, 'reference consumed exact target input')
    actual = {}
    for label, method, negative in ref.CASES:
        dest = reference / label; receipt = read(dest / 'result.json')
        checked = ref.validate(build, dest, record, receipt, method, negative)
        need(checked == summary['validations'][label] == read(dest / 'validation.json') and
             receipt['validation_sha256'] == sha(dest / 'validation.json'), 're-audited actual first-token qualification')
        actual[label] = checked
        for filename in ('result.json', 'validation.json', 'reference-result.json', 'abi.json', 'image.bin',
                         'image-control.json', 'runtime-inputs.json', 'stdout.log', 'stderr.log', *checked['raw_sha256']):
            c.pin(files, dest / filename, checked['raw_sha256'].get(filename))
    need(actual['ta'] == actual['replay'], 'actual independent reference replay')
    for name in ('results.json', 'state.json', 'runtime-inputs.json', 'parent-identity.json'):
        c.pin(files, reference / name)
    identity, hardware, hardware_profile = old.r.parent.parent_identity(b.REPO, identity_path, physical=True)
    need(identity == initial, 'same original physical runtime identity')
    for path, value in hardware.items(): c.pin(files, path, value)
    cfg = identity['configuration']
    for rel in ('difftest/src/test/csrc/verilator/emu.cpp', 'difftest/verilator.mk',
                'difftest/src/main/scala/Difftest.scala', 'src/main/scala/xiangshan/backend/exu/ExeUnit.scala',
                'src/main/scala/xiangshan/backend/rob/Rob.scala', 'build/rtl/ExeUnit_17.sv'):
        c.pin(files, Path(cfg['hardware_source']) / rel)
    gate_modules = list(a.gates()); seen = set()
    while gate_modules:
        module = gate_modules.pop()
        if not isinstance(module, types.ModuleType) or id(module) in seen: continue
        seen.add(id(module)); gate_modules.extend(v for v in vars(module).values() if isinstance(v, types.ModuleType))
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(b.REPO) and path.is_file(): c.pin(files, path)
    for path in (*c.module_files(), HERE / 'run.py', HERE / 'audit.py', HERE / 'BUDGET.md'):
        c.pin(files, path)
    checker.verify_files(files)
    return record, files, identity, hardware, hardware_profile, checker


def freeze(build, reference, adapter, identity_path, output, profile_path, cpus, operation):
    need(not output.exists() and not profile_path.exists() and 1 <= len(cpus) <= 4 and len(set(cpus)) == len(cpus) and
         set(cpus) <= os.sched_getaffinity(0), 'fresh output/profile and at most four unique assigned CPUs')
    record, files, identity, hardware, hardware_profile, checker = qualified(build, reference, adapter, identity_path)
    old.r.parent.outside_inputs(output, [b.REPO, build, reference, adapter, identity_path.parent,
        Path(identity['configuration']['hardware_source']), Path(record['am_home'])])
    old.r.parent.outside_inputs(profile_path, [b.REPO, build, reference, adapter, identity_path.parent,
        Path(identity['configuration']['hardware_source']), Path(record['am_home'])])
    need(not profile_path.is_relative_to(output), 'profile exists independently before campaign creation')
    profile = dict(contract=PROFILE, workload_contract=b.CONTRACT, status='FROZEN_BEFORE_EMU', created=c.base.f.h.now(),
        operation_id=operation, max_cycles=MAX_CYCLES, external_timeout_seconds=TIMEOUT, max_output_file_bytes=RAW_LIMIT,
        cpu_slots=cpus, cases=[list(case) for case in ref.CASES], schedule='four_independent_after_exact_negative_reference_pass',
        paths=dict(build=str(build), reference=str(reference), adapter=str(adapter), identity=str(identity_path), output=str(output)),
        configuration=identity['configuration'], physical_identity=identity, hardware_pins=hardware, hardware_profile=hardware_profile,
        input_files=files, environment_overrides={'XS_NEGATIVE_VECTOR_TARGET': None, 'OMP_NUM_THREADS': '1', 'EMU_THREADS': '1'},
        log_profile='log-end=0; original bare O2/T13 printf retained; original DiffTest/UART enabled',
        automatic_budget_extension=False, performance_qualified=False, full_retirement_window_audited=False)
    save(profile_path, profile); checker.verify_files(files)
    return profile


def profile_inputs(profile_path, build, reference, adapter, identity_path, campaign_output):
    profile = read(profile_path)
    need(profile['contract'] == PROFILE and profile['workload_contract'] == b.CONTRACT and profile['status'] == 'FROZEN_BEFORE_EMU' and
         profile['max_cycles'] == MAX_CYCLES and profile['external_timeout_seconds'] == TIMEOUT and profile['max_output_file_bytes'] == RAW_LIMIT and
         profile['automatic_budget_extension'] is False and profile['performance_qualified'] is False and
         profile['cases'] == [list(case) for case in ref.CASES], 'exact predeclared one-attempt resource profile')
    need(profile['paths'] == dict(build=str(build), reference=str(reference), adapter=str(adapter), identity=str(identity_path),
                                  output=str(campaign_output)), 'exact pre-frozen campaign roots')
    identity, hardware, hardware_profile = old.r.parent.parent_identity(b.REPO, identity_path, physical=True)
    need((identity, hardware, hardware_profile) == (profile['physical_identity'], profile['hardware_pins'], profile['hardware_profile']),
         'physical original inputs equal frozen profile')
    _, checker = old.r.parent.runtime(b.REPO, identity)
    files = dict(profile['input_files']); c.pin(files, profile_path)
    checker.verify_files(files)
    return profile, files, identity, checker


def one(build, reference, adapter, identity_path, output, profile_path, case):
    need(not output.exists() and len(os.sched_getaffinity(0)) == 1, 'fresh single-CPU isolated target case')
    method, negative = {name: (method, negative) for name, method, negative in ref.CASES}[case]
    profile, files, identity, checker = profile_inputs(profile_path, build, reference, adapter, identity_path, output.parent)
    need(output == Path(profile['paths']['output']) / case, 'one exact declared case directory')
    need(set(os.sched_getaffinity(0)) <= set(profile['cpu_slots']), 'one declared CPU slot')
    cfg = identity['configuration']; record = read(build / 'result.json')
    need(record['contract'] == b.CONTRACT and record['status'] == b.STATIC, 'exact first-token static record')
    output.mkdir(parents=True); cwd = output / 'cwd'; (cwd / 'build').mkdir(parents=True)
    for name, value in checker.AUX.items():
        path = cwd / 'build' / name; shutil.copyfile(Path(cfg['hardware_source']) / 'build' / name, path); c.pin(files, path, value)
    raw, control = ref.image(build, record, method, negative, 1)
    (output / 'image.bin').write_bytes(raw); save(output / 'image-control.json', control); del raw
    c.pin(files, output / 'image.bin'); c.pin(files, output / 'image-control.json')
    save(output / 'runtime-inputs.json', files); save(output / 'configuration.json', cfg)
    save(output / 'hardware-profile.json', profile['hardware_profile']); shutil.copyfile(identity_path, output / 'parent-identity.json')
    _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    need(hard == resource.RLIM_INFINITY or hard >= RAW_LIMIT, 'declared whole raw stream budget')
    resource.setrlimit(resource.RLIMIT_FSIZE, (RAW_LIMIT, hard))
    argv = [str(Path(cfg['hardware_source']) / 'build/emu'), '-i', str(output / 'image.bin'), '--flash=' + cfg['flash'],
            '--ram-size=128MB', '--diff=' + cfg['reference'], '--max-cycles=' + str(MAX_CYCLES), '--seed=1', '--log-end=0']
    env = dict(os.environ); env.pop('XS_NEGATIVE_VECTOR_TARGET', None); env.update(OMP_NUM_THREADS='1', EMU_THREADS='1')
    rec = dict(contract=b.CONTRACT, operation_id=profile['operation_id'], status='RUNNING', name=case, method=method, negative=negative,
        command=argv, cwd=str(cwd), started=c.base.f.h.now(), process_started=False, exit_code=None, cpu_affinity=sorted(os.sched_getaffinity(0)),
        max_cycles=MAX_CYCLES, external_timeout_seconds=TIMEOUT, max_output_file_bytes=RAW_LIMIT,
        image_sha256=control['sha256'], profile_sha256=sha(profile_path), environment_overrides=profile['environment_overrides'],
        log_profile=profile['log_profile'], target_correctness_qualified=False, performance_qualified=False)
    persist = lambda: save(output / 'result.json', rec); persist(); begin = time.monotonic()
    def raw_record():
        paths = [output / name for name in ('stdout.log', 'stderr.log') if (output / name).exists()]
        rec.update(raw_sha256={p.name: sha(p) for p in paths}, raw_bytes={p.name: p.stat().st_size for p in paths})
    try:
        checker.verify_files(files)
        with (output / 'stdout.log').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
            old.previous.spawn(argv, cwd, stdout, stderr, rec, persist, env, TIMEOUT)
        raw_record(); rec['status'] = 'PROCESS_CLOSED_RAW_AUDIT_REQUIRED'; persist()
        checker.verify_files(files)
        actual = old.r.parent.parent_identity(b.REPO, identity_path, physical=True)
        need(actual == (profile['physical_identity'], profile['hardware_pins'], profile['hardware_profile']), 'physical runtime unchanged after EMU')
        checked = a.validate(output, build, record, rec, cfg, profile, output / 'audit')
        save(output / 'validation.json', checked)
        checker.verify_files(files)
        rec.update(status=checked['status'], validation_sha256=sha(output / 'validation.json'),
                   target_correctness_qualified=checked['target_correctness_qualified'])
        print(case, rec['status'], flush=True)
    except BaseException as error:
        rec.update(status='FAILED_OR_PARTIAL', error=repr(error)); raise
    finally:
        final_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        try:
            if 'raw_sha256' not in rec:
                try: raw_record()
                except BaseException as error:
                    rec.update(status='FAILED_OR_PARTIAL', raw_record_error=repr(error), target_correctness_qualified=False)
            rec.update(finished=c.base.f.h.now(), observed_elapsed_seconds=time.monotonic() - begin,
                       child_maxrss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
            persist()
        finally: signal.pthread_sigmask(signal.SIG_SETMASK, final_mask)
    return rec


def campaign(build, reference, adapter, identity_path, output, profile_path):
    need(not output.exists(), 'fresh campaign without implicit resume or rerun')
    profile, files, identity, checker = profile_inputs(profile_path, build, reference, adapter, identity_path, output)
    cpus = profile['cpu_slots']
    need(1 <= len(cpus) <= 4 and len(set(cpus)) == len(cpus) and set(cpus) <= os.sched_getaffinity(0), 'all unique declared slots available')
    os.sched_setaffinity(0, cpus)
    output.mkdir(parents=True); save(output / 'runtime-inputs.json', files); old.snapshot_runtime(output, files)
    shutil.copyfile(profile_path, output / 'resource-contract.json'); shutil.copyfile(identity_path, output / 'parent-identity.json')
    state = dict(contract=b.CONTRACT, resource_contract=PROFILE, operation_id=profile['operation_id'], status='RUNNING',
        started=c.base.f.h.now(), active=[], completed=[], records=[], launcher_receipts=[], launched_cases=[], cpu_slots=cpus,
        new_emu_runs=0, schedule=profile['schedule'], target_correctness_qualified=False, performance_qualified=False)
    persist = lambda: save(output / 'state.json', state); persist(); active = {}; queue = [x[0] for x in ref.CASES]
    try:
        while queue or active:
            for cpu in [n for n in cpus if n not in active]:
                if not queue: break
                label = queue.pop(0)
                argv = ['taskset', '-c', str(cpu), sys.executable, '-B', str(HERE / 'run.py'), '--build', str(build),
                    '--reference', str(reference), '--adapter', str(adapter), '--identity', str(identity_path),
                    '--output', str(output / label), '--profile', str(profile_path), '--case', label]
                logfile = (output / (label + '.launcher.log')).open('wb')
                oldmask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
                try:
                    proc = subprocess.Popen(argv, stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True,
                        preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, oldmask))
                    active[cpu] = (proc, label, logfile)
                    state['launched_cases'].append(label)
                    state['active'] = [dict(pid=v[0].pid, case=v[1], cpu=k) for k, v in active.items()]; persist()
                finally: signal.pthread_sigmask(signal.SIG_SETMASK, oldmask)
            for cpu, (proc, label, logfile) in list(active.items()):
                if proc.poll() is None: continue
                code = proc.wait(); logfile.close()
                ownership, rec = old.case_ownership(output, label, proc)
                state['launcher_receipts'].append(ownership); persist()
                need(ownership['cleanup_verified'], 'case ownership unresolved: ' + label)
                del active[cpu]
                state['active'] = [dict(pid=v[0].pid, case=v[1], cpu=k) for k, v in active.items()]; persist()
                need(code == 0, 'complete case raw audit succeeded: ' + label)
                state['records'].append(rec); state['completed'].append(label)
                state['new_emu_runs'] += int(rec['process_started']); persist()
            if active: time.sleep(0.1)
        validations = {name: read(output / name / 'validation.json') for name, _, _ in ref.CASES}
        need(validations['negative']['status'] == 'EXPECTED_FIRST_TOKEN_TARGET_REJECTION' and
             all(validations[name]['status'] == 'FIRST_TOKEN_TARGET_DIFFTEST_PASS' for name in ('fr', 'ta', 'replay')),
             'actual negative plus all complete positive cases')
        need(validations['ta'] == validations['replay'], 'independent exact architecture/counter/protocol replay')
        need(len({r['pid'] for r in state['records']}) == state['new_emu_runs'] == 4, 'four independent original EMUs')
        checker.verify_files(files); state.update(status=PASS, target_correctness_qualified=True)
        save(output / 'results.json', dict(contract=b.CONTRACT, resource_contract=PROFILE, status=PASS,
            records=state['records'], validations=validations, new_emu_runs=4, target_correctness_qualified=True,
            performance_qualified=False, full_retirement_window_audited=False))
    except BaseException as error:
        state.update(status='FAILED_OR_PARTIAL', error=repr(error)); raise
    finally:
        cleanup_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        try:
            unresolved = []; cleanup_errors = []
            # Notify every owned launcher before waiting for any one of them.
            # Each launcher uses the existing spawn() to reap its own EMU group.
            for cpu, (proc, label, logfile) in active.items():
                if proc.poll() is None:
                    try: os.killpg(proc.pid, signal.SIGTERM)
                    except ProcessLookupError: pass
                    except BaseException as error: cleanup_errors.append(dict(case=label, phase='signal', error=repr(error)))
            for cpu, (proc, label, logfile) in active.items():
                try:
                    if proc.poll() is None: proc.wait(timeout=15)
                except BaseException as error: cleanup_errors.append(dict(case=label, phase='wait', error=repr(error)))
                try: logfile.close()
                except BaseException as error: cleanup_errors.append(dict(case=label, phase='close', error=repr(error)))
                try: ownership, _ = old.case_ownership(output, label, proc)
                except BaseException as error:
                    ownership = dict(case=label, launcher_pid=proc.pid, result_path=str(output / label / 'result.json'),
                                     cleanup_verified=False, receipt_error=repr(error))
                ownership['cpu'] = cpu; state['launcher_receipts'].append(ownership)
                if not ownership['cleanup_verified']: unresolved.append(ownership)
            state['cleanup_unknown'] = unresolved; state['cleanup_errors'] = cleanup_errors
            known_started = 0; unreadable = []
            for name in state['launched_cases']:
                try:
                    receipt = read(output / name / 'result.json')
                    need(type(receipt.get('process_started')) is bool, 'explicit launch state in receipt')
                    known_started += int(receipt['process_started'])
                except BaseException as error:
                    unreadable.append(dict(case=name, receipt_error=repr(error), process_started_unknown=True))
            state['new_emu_runs'] = None if unreadable else known_started
            state['known_started_emu_runs'] = known_started; state['launch_state_unknown'] = unreadable
            state['active'] = [dict(pid=v['launcher_pid'], case=v['case'], cpu=v['cpu'], result_path=v['result_path'], ownership_unresolved=True) for v in unresolved]
            state['finished'] = c.base.f.h.now(); persist()
        finally: signal.pthread_sigmask(signal.SIG_SETMASK, cleanup_mask)
    return state


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('first-token target signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'reference', 'adapter', 'identity', 'output', 'profile'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--freeze', action='store_true'); parser.add_argument('--cpus', default='0,1,2,3')
    parser.add_argument('--operation-id'); parser.add_argument('--case', choices=[x[0] for x in ref.CASES])
    args = parser.parse_args(); paths = [getattr(args, n).resolve() for n in ('build', 'reference', 'adapter', 'identity', 'output', 'profile')]
    if args.freeze:
        need(args.operation_id and not args.case, 'explicit operation identity for profile freeze')
        result = freeze(*paths, [int(x) for x in args.cpus.split(',')], args.operation_id)
    elif args.case: result = one(*paths, args.case)
    else: result = campaign(*paths)
    print(json.dumps({k: result[k] for k in ('contract', 'status', 'performance_qualified')}, indent=2))
