#!/usr/bin/env python3
"""Exercise the offline scheduler with synthetic processes, never EMU/NEMU."""
import argparse
import hashlib
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import signal
import sys
import time
import traceback

TOOL = None


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def process_identity(pid):
    path = Path('/proc') / str(pid) / 'stat'
    if not path.exists():
        return None
    fields = path.read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'state': fields[0], 'process_group': int(fields[2]), 'start_ticks': int(fields[19])}


def probe_case(task):
    name, delay, failure, cpu, directory = task
    os.sched_setaffinity(0, {cpu})
    identity = process_identity(os.getpid())
    identity.update(case=name, started=time.time(), cpu_affinity=sorted(os.sched_getaffinity(0)))
    write(Path(directory) / (name + '.json'), identity)
    time.sleep(delay)
    if failure:
        raise ValueError('intentional synthetic case failure: ' + name)
    return {'case': name, 'pid': os.getpid(), 'value': int(name[-1]) ** 2,
            'process_group': os.getpgrp(), 'cpu_affinity': sorted(os.sched_getaffinity(0))}


def run_synthetic_worker(args):
    cpu = min(os.sched_getaffinity(0))
    TOOL._CASE_CONTEXT = {'process_group': os.getpgrp(), 'allowed_cpus': [cpu]}
    TOOL._audit_case = probe_case
    mode = args.worker
    delays = [0.20, 0.50, 0.10, 0.30] if mode == 'normal' else [0.30] * 4 if mode == 'case_failure' else [10.0] * 4
    tasks = [('case' + str(i), delay, mode == 'case_failure' and i == 1, cpu, str(args.output / 'pids'))
             for i, delay in enumerate(delays)]
    result = TOOL._dispatch_cases(tasks, 4, 0.2 if mode == 'inner_timeout' else 20)
    assert [row['case'] for row in result] == ['case' + str(i) for i in range(4)]
    assert [row['value'] for row in result] == [0, 1, 4, 9]
    assert all(row['cpu_affinity'] == [cpu] and row['process_group'] == os.getpgrp() for row in result)
    assert not multiprocessing.active_children()
    write(args.output / 'worker-result.json', {'status': 'SYNTHETIC_CASE_DISPATCH_COMPLETE', 'results': result})


def main():
    global TOOL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', choices=('normal', 'case_failure', 'inner_timeout', 'outer_timeout', 'cancel'))
    args = parser.parse_args()
    TOOL = load('offline_evidence_mechanism_under_test', args.tool)
    signal.signal(signal.SIGTERM, TOOL.interrupted)
    signal.signal(signal.SIGINT, TOOL.interrupted)
    if args.worker:
        run_synthetic_worker(args)
        return
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    reference = load('offline_original_reference_for_owner', args.tool.with_name('reference.py'))
    spawn = reference.old.previous.spawn
    owner_path = Path(spawn.__code__.co_filename)
    assert hashlib.sha256(owner_path.read_bytes()).hexdigest() == 'bee89ca4424110f244560b1ab0529c80fd4e9736dd274c49690026754dbf8475'
    report = {'status': 'RUNNING', 'started': time.time(),
              'tool_sha256': hashlib.sha256(args.tool.read_bytes()).hexdigest(),
              'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'owner_sha256': hashlib.sha256(owner_path.read_bytes()).hexdigest(),
              'synthetic_only': True, 'new_reference_runs': 0, 'new_emu_runs': 0,
              'real_archive_rechecked': False, 'performance_qualified': False,
              'cpu_affinity': sorted(os.sched_getaffinity(0)), 'checks': {}}
    try:
        for mode in ('normal', 'case_failure', 'inner_timeout', 'outer_timeout', 'cancel'):
            directory = args.output / mode
            (directory / 'pids').mkdir(parents=True)
            command = [sys.executable, '-B', str(Path(__file__).resolve()), '--tool', str(args.tool),
                       '--output', str(directory), '--worker', mode]
            interrupted = False
            alarm_started = time.monotonic()
            def cancel_when_workers_exist(signum, frame):
                if len(list((directory / 'pids').glob('*.json'))) >= 2:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    os.kill(os.getpid(), signal.SIGTERM)
                elif time.monotonic() - alarm_started < 5:
                    signal.setitimer(signal.ITIMER_REAL, 0.05)
                else:
                    raise AssertionError('synthetic cancellation workers did not become ready')
            if mode == 'cancel':
                signal.signal(signal.SIGALRM, cancel_when_workers_exist)
                signal.setitimer(signal.ITIMER_REAL, 0.05)
            try:
                TOOL.owned_command(command, directory, directory / 'stdout.log', directory / 'stderr.log',
                                   directory / 'ownership.json', spawn, timeout=1 if mode == 'outer_timeout' else 10)
                assert mode == 'normal', 'intentional fault must not be accepted'
            except BaseException as error:
                interrupted = isinstance(error, InterruptedError)
                if mode == 'normal':
                    raise
                if mode == 'cancel':
                    assert interrupted, 'real SIGTERM must reach the production exception handler'
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            ownership = json.loads((directory / 'ownership.json').read_text())
            assert ownership['process_started'] is True and ownership['direct_child_reaped'] is True
            assert ownership['process_group_absent_after_exit'] is True and ownership['cleanup_unknown'] is False
            assert ownership['status'] == ('OWNED_OFFLINE_WORKER_CLOSED' if mode == 'normal' else 'FAILED')
            if mode == 'outer_timeout':
                assert ownership.get('timed_out') is True
            if mode == 'case_failure':
                assert 'intentional synthetic case failure' in (directory / 'stderr.log').read_text()
                assert not ownership.get('timed_out')
            if mode == 'inner_timeout':
                assert 'TimeoutError' in (directory / 'stderr.log').read_text()
                assert not ownership.get('timed_out')
            if mode == 'normal':
                completed = json.loads((directory / 'worker-result.json').read_text())
                assert completed['status'] == 'SYNTHETIC_CASE_DISPATCH_COMPLETE'
                assert [row['value'] for row in completed['results']] == [0, 1, 4, 9]
            identities = [json.loads(path.read_text()) for path in (directory / 'pids').glob('*.json')]
            assert len(identities) >= 2, 'actual fork descendants participated in the check'
            for old in identities:
                current = process_identity(old['pid'])
                assert current is None or current['start_ticks'] != old['start_ticks'], 'owned descendant generation remains'
            report['checks'][mode] = {'status': 'PASS', 'worker_pid': ownership['pid'],
                                     'observed_descendants': identities, 'group_absent': True,
                                     'real_sigterm_observed': interrupted if mode == 'cancel' else None}
            write(args.output / 'result.json', report)
        report['status'] = 'OFFLINE_PARALLEL_PROCESS_MECHANISMS_PASS'
    except BaseException as error:
        report.update(status='FAILED', error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        report['finished'] = time.time()
        write(args.output / 'result.json', report)
    print(json.dumps({'status': report['status'], 'checks': list(report['checks']), 'real_archive_rechecked': False}))


if __name__ == '__main__':
    main()
