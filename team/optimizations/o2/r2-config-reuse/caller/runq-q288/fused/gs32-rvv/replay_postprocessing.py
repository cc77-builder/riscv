"""Exercise run_one's real postprocessing with completed raw-log fixtures.

No EMU is launched. Only the runner's subprocess handle is replaced; the real
checker, its source pins, and the runner's shared lock remain in use. Both normal
checker requests rendezvous before acquisition, so the worker threads contend
for the same lock. Compare each result with that log's prior serial raw audit.
All fixture process receipts are explicitly marked as simulated and are written
under fixture-runtime.json, never as a new real runtime.json.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier, Lock
from types import SimpleNamespace
import argparse
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def replay(controller, repo, build, campaign, serial, out):
    need(not out.exists() and all(not out.is_relative_to(p) for p in
         (controller, repo, build, campaign, serial)), 'fresh isolated regression output')
    need(read(campaign/'state.json').get('finished'), 'original campaign terminated')
    audit = read(serial/'result.json')
    need(audit['status'] == 'GS32_TARGET_SERIAL_RAW_RECHECK_PASS', 'completed serial raw audit')
    inputs = read(campaign/'inputs.json')
    pins = {build/name:inputs[str(build/name)] for name in ('gs32-target.elf', 'gs32-target.bin')}
    pins[build/'source/manifest.json'] = sha(build/'source/manifest.json')
    controller_names = ('CONTRACT.md', 'generate.py', 'screen.py', 'target.py',
                        'check_target.py', 'run_target.py')
    for name in controller_names:
        pins[controller/name] = sha(controller/name)
        if name != 'run_target.py':
            need(sha(controller/name) == sha(campaign/'controller'/name), 'unchanged checker '+name)
    for path in (campaign/'inputs.json', campaign/'state.json', serial/'result.json'):
        pins[path] = sha(path)
    originals = {}
    for name in ('negative', 'recovery', 'replay'):
        source = campaign/'runs'/name
        receipt = read(source/'runtime.json')
        originals[name] = receipt
        need(receipt['process_started'] and receipt.get('finished') and not receipt['timed_out'],
             'completed original process '+name)
        pins[source/'runtime.json'] = sha(source/'runtime.json')
        for raw, pin in receipt['raw_sha256'].items():
            need(sha(source/raw) == pin, 'unchanged original raw '+name+'/'+raw)
            pins[source/raw] = pin
        pins[serial/(name+'.json')] = audit['reports_sha256'][name]
    need(all(name not in sys.modules for name in ('generate', 'screen', 'target', 'check_target', 'run_target')),
         'fresh interpreter for controller')
    sys.path.insert(0, str(controller))
    runtime = importlib.import_module('run_target')
    for rel, pin in runtime.check.HELPER_PINS.items():
        pins[repo/rel] = pin
    runtime.verify_files(pins)
    out.mkdir(parents=True)
    save(out/'inputs.json', {str(p):v for p,v in pins.items()})
    state = dict(status='RUNNING', started=now(), new_emu_runs=0,
        scope='runner_postprocessing_only', source_campaign=str(campaign),
        source_serial_audit=str(serial), controller=str(controller), support_repo=str(repo),
        cpu_affinity=sorted(os.sched_getaffinity(0)), regression_sha256=sha(Path(__file__)))
    save(out/'state.json', state)
    rendezvous = Barrier(2)
    bookkeeping = Lock()
    events, waiting, active, peak_waiting, peak_active = [], 0, 0, 0, 0
    normal_phase = False
    real_lock = runtime._CHECKER_LOCK
    real_save = runtime.save

    class ObservedLock:
        def __enter__(self):
            nonlocal waiting, active, peak_waiting, peak_active
            with bookkeeping:
                waiting += 1
                peak_waiting = max(peak_waiting, waiting)
                events.append(dict(event='checker_requested', at=now()))
            if normal_phase:
                rendezvous.wait(timeout=30)
            real_lock.acquire()
            with bookkeeping:
                active += 1
                peak_active = max(peak_active, active)
                events.append(dict(event='checker_entered', at=now()))
            return self

        def __exit__(self, *_):
            nonlocal waiting, active
            with bookkeeping:
                active -= 1
                waiting -= 1
                events.append(dict(event='checker_left', at=now()))
            real_lock.release()

    class RawFixture:
        def __init__(self, command, *, cwd, env, stdout, stderr, start_new_session):
            self.name = Path(cwd).parent.name
            source = campaign/'runs'/self.name
            original = originals[self.name]
            need(command == original['command'] and start_new_session, 'same requested fixture command')
            need(env.get('XS_NEGATIVE_VECTOR_TARGET') == ('vdot' if self.name == 'negative' else None),
                 'same fixture negative selector')
            for stream, raw in ((stdout, 'stdout.log'), (stderr, 'stderr.log')):
                with (source/raw).open('rb') as src:
                    shutil.copyfileobj(src, stream)
            self.pid = -1  # An unmistakable fixture marker; no OS process exists.
            self.returncode = original['exit_code']
            with bookkeeping:
                events.append(dict(event='fixture_opened', name=self.name, at=now()))

        def wait(self, timeout=None):
            need(timeout == 5400, 'unchanged runner wait timeout')
            with bookkeeping:
                events.append(dict(event='fixture_wait_returned', name=self.name, at=now()))
            return self.returncode

    def fixture_save(path, value):
        if path.name == 'runtime.json':
            path = path.with_name('fixture-runtime.json')
            value = dict(value, evidence_kind='SIMULATED_HANDLE_FOR_RAW_LOG_REGRESSION',
                         new_emu_runs=0, fixture_branch_process_started=value['process_started'],
                         process_started=False, fixture_pid=value.get('pid'), pid=None)
        real_save(path, value)

    runtime._CHECKER_LOCK = ObservedLock()
    runtime.save = fixture_save
    # Do not monkeypatch the global subprocess module used by real checkers.
    runtime.subprocess = SimpleNamespace(Popen=RawFixture, TimeoutExpired=subprocess.TimeoutExpired)
    try:
        records = [runtime.run_one(repo, build, out, 'negative', 0, pins, negative=True)]
        normal_phase = True
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(runtime.run_one, repo, build, out, name, core, pins)
                    for name, core in (('recovery', 0), ('replay', 1))]
            records.extend(job.result() for job in jobs)
        for record in records:
            name = record['name']
            expected = read(serial/(name+'.json'))
            if name == 'negative':
                expected['reference_unchanged'] = True
            need(record['result'] == expected, 'exact prior serial analysis '+name)
            need(not (out/'runs'/name/'runtime.json').exists(), 'no real runtime receipt fabricated')
        need(peak_waiting == 2 and peak_active == 1 and active == waiting == 0,
             'two requests contend, only one checker active, all locks released')
        runtime.verify_files(pins)
        result = dict(status='GS32_POSTPROCESSING_CONCURRENCY_REGRESSION_PASS',
            scope=state['scope'], new_emu_runs=0, new_target_or_performance_qualification=False,
            source_emu_runs=3, source_campaign=str(campaign), source_serial_audit=str(serial),
            runner_sha256=sha(controller/'run_target.py'), original_runner_sha256=sha(campaign/'controller/run_target.py'),
            checker_sha256=sha(controller/'check_target.py'), simultaneous_checker_requests=peak_waiting,
            max_active_checkers=peak_active, negative_and_two_normal_analyses_equal_prior_serial_audit=True,
            analyses_sha256={r['name']:sha(out/'runs'/r['name']/'analysis.json') for r in records},
            original_raw_sha256={n:r['raw_sha256'] for n,r in originals.items()},
            events=events)
        save(out/'result.json', result)
        state.update(status=result['status'], result_sha256=sha(out/'result.json'))
    except BaseException as error:
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        state['finished'] = now()
        save(out/'state.json', state)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('controller', 'repo', 'build', 'campaign', 'serial', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    result = replay(*(getattr(args, n).resolve() for n in
                      ('controller', 'repo', 'build', 'campaign', 'serial', 'output')))
    print(json.dumps(result, indent=2))
