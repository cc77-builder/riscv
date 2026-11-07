#!/usr/bin/env python3
"""Bound GNU build or the unchanged five-case reference; never launch an EMU.

The controller/preparer owns source and verdicts. This driver binds only the
existing command/spawn execution boundary and the frozen parent Git context.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
import types

sys.dont_write_bytecode = True
CONTRACT = 'w2-consumer-bounded-stage-v1'
CONTROLLER_CONTRACT = 'r3-dot16-first-forward-w2np-v1'
HELPER_SHA = 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'
FILE_LIMIT = 128 * 1024 * 1024


def need(ok, message):
    if not ok:
        raise ValueError(message)


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.stage-tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bind(function, **dependencies):
    """Keep the original code object; bind dependencies in a private namespace."""
    namespace = dict(function.__globals__)
    namespace.update(dependencies)
    result = types.FunctionType(function.__code__, namespace, function.__name__,
                                function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def run(args):
    cap = 1200 if args.stage == 'build' else 3600
    need(args.cpu == 1 and 1 <= args.budget_seconds <= cap, 'CPU1 and finite stage budget')
    need(re.fullmatch(r'[0-9a-f]{64}', args.binding_sha256) is not None,
         'explicit complete prepared binding SHA256')
    need((args.build is None) == (args.stage == 'build'), '--build only and always for reference')
    controller, output = args.controller.resolve(), args.output.resolve()
    need(args.controller.is_absolute() and controller.is_dir(), 'absolute prepared controller')
    need(args.output.is_absolute() and Path(os.path.abspath(args.output)) == output
         and not output.exists(), 'fresh absolute output without symlink parents')
    need(not output.is_relative_to(controller) and not controller.is_relative_to(output),
         'output and controller are separate')
    source = Path(__file__).resolve()
    need(not source.is_relative_to(output), 'output must not contain the stage driver')
    build = args.build.resolve() if args.build is not None else None
    if build is not None:
        need(args.build.is_absolute() and build.is_dir() and not output.is_relative_to(build)
             and not build.is_relative_to(output), 'reference build is separate existing input')
    os.sched_setaffinity(0, {1})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    deadline = time.monotonic() + args.budget_seconds
    state = dict(contract=CONTRACT, stage=args.stage, status='PREFLIGHT', started=stamp(),
                 controller=str(controller), output=str(output), build=str(build) if build else None,
                 cpu_affinity=sorted(os.sched_getaffinity(0)), nice=os.getpriority(os.PRIO_PROCESS, 0),
                 budget_seconds=args.budget_seconds, max_output_file_bytes=FILE_LIMIT,
                 commands=[], stage_completed=False, reference_qualified=False,
                 target_emu_runs=0, performance_qualified=False, fullcore_qualified=False,
                 controller_sources_modified=False, original_checkers_modified=False)
    old_environment = dict(os.environ)
    old_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
    old_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM)}
    need(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'standalone stage owns its alarm timer')
    pending, critical, closing = [None], [False], [False]
    output_safe = False
    pins, resolved = {}, {}
    helper = None
    failure = None

    def check():
        if pending[0] is not None:
            if pending[0] == signal.SIGALRM:
                raise TimeoutError('total stage deadline exhausted')
            raise InterruptedError('stage signal ' + str(pending[0]))
        if time.monotonic() >= deadline:
            raise TimeoutError('total stage deadline exhausted')

    def interrupted(signum, _frame):
        if pending[0] is None:
            pending[0] = signum
        # Never interrupt the Popen ownership assignment or bounded cleanup.
        if not critical[0] and not closing[0]:
            check()

    def pin(path, expected=None):
        check()
        path = Path(path)
        need(path.is_absolute() and path.is_file(), 'real absolute stage input: ' + str(path))
        value = sha(path)
        need(expected is None or value == expected, 'fixed stage input: ' + str(path))
        need(str(path) not in pins or pins[str(path)] == value, 'no input rebinding')
        need(not path.resolve().is_relative_to(output), 'output contains no stage input')
        pins[str(path)] = value
        resolved[str(path)] = str(path.resolve())
        return path

    def persist():
        # The original stage must create its own fresh output directory.
        if output.is_dir():
            save(output / 'stage-receipt.json', state)
            if not (output / 'stage-input-pins.json').exists():
                save(output / 'stage-input-pins.json', dict(files=pins, resolved_targets=resolved))

    def execute(argv, cwd, stdout, stderr, record, progress, environment, timeout, label):
        check()
        need(not critical[0], 'one owned external process at a time')
        need(output.is_dir(), 'original stage created its isolated output before execution')
        argv = list(map(str, argv))
        environment = {**environment, 'TMPDIR': str(output)}
        allowance = min(float(timeout), deadline - time.monotonic())
        need(allowance > 0, 'remaining command budget')
        until = time.monotonic() + allowance
        entry = dict(label=label, argv=argv, cwd=str(cwd) if cwd is not None else os.getcwd(),
                     stdout=str(stdout.name), stderr=str(stderr.name), started=stamp(),
                     requested_timeout_seconds=timeout, effective_timeout_seconds=allowance,
                     temporary_directory=str(output),
                     process=record)
        state['commands'].append(entry)
        process = None
        record.update(process_started=False, timed_out=False, residual_process_group=False,
                      direct_child_reaped=False, process_group_absent_after_exit=False)
        critical[0] = True
        try:
            check()
            process = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr,
                                       env=environment, start_new_session=True)
            record.update(process_started=True, pid=process.pid, process_id=process.pid,
                          process_group=process.pid)
            progress(); persist()
            while True:
                check()
                left = until - time.monotonic()
                if left <= 0:
                    record['timed_out'] = True
                    raise subprocess.TimeoutExpired(argv, allowance)
                try:
                    record['exit_code'] = process.wait(timeout=min(.25, left))
                    break
                except subprocess.TimeoutExpired:
                    continue
            if helper.group_exists(process.pid):
                record['residual_process_group'] = True
                raise RuntimeError('external command left a residual process group')
        except BaseException as error:
            if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)):
                record['timed_out'] = True
            record['execution_error'] = repr(error)
            raise
        finally:
            cleanup_error = None
            try:
                if process is not None:
                    try:
                        if process.poll() is None or helper.group_exists(process.pid):
                            record['cleanup_attempted'] = True
                            record['cleanup_complete'] = helper.stop_group(process)
                    except BaseException as error:
                        cleanup_error = error
                        record['cleanup_error'] = repr(error)
                    finally:
                        record['exit_code'] = process.poll()
                        record['direct_child_reaped'] = record['exit_code'] is not None
                        record['process_group_absent_after_exit'] = not helper.group_exists(process.pid)
                entry['finished'] = stamp()
                progress(); persist()
            finally:
                critical[0] = False
            if cleanup_error is not None:
                raise cleanup_error
        check()
        need(record['direct_child_reaped'] and record['process_group_absent_after_exit'],
             'closed direct child and complete process group')
        return record['exit_code']

    def command(argv, out, name, expected=0, timeout=180, environment=None):
        """Same signature, cwd, three raw-log names and dictionary return as h.command."""
        check()
        out = Path(out)
        need(out.resolve() == output and out.is_dir(), 'build command belongs to this fresh output')
        argv = list(map(str, argv))
        record = dict(argv=argv, started_at=stamp(), status='started', timeout_seconds=timeout,
                      environment_overrides=environment or {})
        path = out / (name + '.command.json')
        need(not any((out / (name + suffix)).exists() for suffix in
                     ('.command.json', '.stdout.log', '.stderr.log')), 'fresh original command logs')
        progress = lambda: save(path, record)
        progress(); started = time.monotonic()
        try:
            with (out / (name + '.stdout.log')).open('wb') as stdout, \
                 (out / (name + '.stderr.log')).open('wb') as stderr:
                code = execute(argv, None, stdout, stderr, record, progress,
                               {**os.environ, **(environment or {})}, timeout, name)
            record.update(status='exited', exit_code=code)
        except BaseException as error:
            record.update(status='timeout' if record.get('timed_out') else
                          'residual_process_group' if record.get('residual_process_group') else
                          'interrupted' if record.get('process_started') else 'launch_error',
                          interruption_type=type(error).__name__, error=str(error))
            raise
        finally:
            record.update(ended_at=stamp(), elapsed_seconds=time.monotonic() - started)
            progress(); persist()
        need(read(path) == record, 'durable original command receipt readback')
        need(code == expected, name + ' expected exit ' + str(expected) + ', got ' + str(code))
        return record

    def spawn(argv, cwd, stdout, stderr, record, progress, environment, timeout):
        need(args.stage == 'reference' and timeout == 630, 'unchanged630-second reference spawn')
        need(Path(argv[0]).resolve() == Path(cfg['adapter']).resolve() / 'reference-runner',
             'only the original reference adapter, never an EMU')
        execute(argv, cwd, stdout, stderr, record, progress, environment, timeout,
                'reference-' + record['name'])

    try:
        for sig in old_handlers:
            signal.signal(sig, interrupted)
        signal.setitimer(signal.ITIMER_REAL, args.budget_seconds)
        clean = {key: old_environment[key] for key in ('HOME', 'USER', 'LOGNAME') if key in old_environment}
        clean.update(PATH='/usr/bin:/bin', LANG='C', LC_ALL='C', PYTHONDONTWRITEBYTECODE='1',
                     PYTHONNOUSERSITE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                     MKL_NUM_THREADS='1', MAKEFLAGS='-j1', GIT_OPTIONAL_LOCKS='0')
        os.environ.clear(); os.environ.update(clean)
        need(old_limit[1] == resource.RLIM_INFINITY or old_limit[1] >= FILE_LIMIT,
             'complete image/raw files require at least128MiB hard file limit')
        resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_LIMIT, old_limit[1]))
        pin(source)
        contract_path = pin(source.parent / 'RUN_STAGE_CONTRACT.md')
        pin(controller / 'binding.json', args.binding_sha256)
        binding = read(controller / 'binding.json')
        need(binding['contract'] == CONTROLLER_CONTRACT and
             binding['status'] == 'FIRST_FORWARD_W2NP_CONTROLLER_BOUND_NOT_RUNTIME',
             'explicit prepared W2 consumer identity')
        cfg = binding['config']
        need(Path(cfg['identity']).resolve() == Path(cfg['dot16_hardware_result']).resolve(),
             'reference uses the fixed dot16 hardware record, not the obsolete identity')
        # Do not create a failure receipt inside an input tree if a caller
        # accidentally supplied an invalid output; the outer log retains it.
        protected = [controller, source.parent]
        for value in cfg.values():
            if isinstance(value, str) and Path(value).is_absolute():
                path = Path(value).resolve()
                protected.append(path if path.is_dir() else path.parent)
        parent_result = read(Path(cfg['parent_build']) / 'result.json')
        protected.append(Path(parent_result['am_home']).resolve())
        need(all(not output.is_relative_to(root) and not root.is_relative_to(output)
                 for root in protected), 'output is outside all configured input roots and official AM')
        output_safe = True
        for path, value in binding['input_files'].items():
            pin(path, value)
        for name, value in binding['generated_files'].items():
            path = controller / name
            need(not Path(name).is_absolute() and '..' not in Path(name).parts
                 and path.resolve().is_relative_to(controller), 'closed relative controller input')
            pin(path, value)
        helper_path = pin(Path(cfg['w2_source']).resolve().parent / 'inputs/process_helper.py', HELPER_SHA)
        helper = load('w2_stage_process_helper', helper_path)
        if args.stage == 'build':
            b = load('w2_stage_build', controller / 'build.py')
        else:
            ref = load('w2_stage_reference', controller / 'reference.py')
            b = ref.b
        need(b.CONTRACT == CONTROLLER_CONTRACT and b.BINDING == binding, 'same immutable controller binding')
        for path, value in b.SUPPORT_FILES.items():
            pin(path, value)
        state.update(status='RUNNING', binding_sha256=pins[str(controller / 'binding.json')],
                     driver_sha256=pins[str(source)],
                     execution_contract_sha256=pins[str(contract_path)],
                     process_helper=dict(path=str(helper_path), sha256=HELPER_SHA),
                     execution_binding='private function globals; original module objects unchanged')
        check(); persist()
        if args.stage == 'build':
            original_parent_inputs = b.g.parent_inputs
            def parent_inputs(*values, **keywords):
                check()
                with b.support_git_metadata():
                    result = original_parent_inputs(*values, **keywords)
                check()
                return result
            proxy = types.SimpleNamespace(**vars(b.g))
            proxy.parent_inputs = parent_inputs
            execute_stage = bind(b.build, command=command, g=proxy)
            need(execute_stage.__code__ is b.build.__code__, 'unchanged original build code object')
            result = execute_stage(output)
            need(result['status'] == b.STATIC and result['contract'] == CONTROLLER_CONTRACT,
                 'original complete static build result')
        else:
            previous = types.SimpleNamespace(**vars(ref.old.previous))
            previous.spawn = spawn
            old = types.SimpleNamespace(**vars(ref.old))
            old.previous = previous
            execute_stage = bind(ref.run, old=old)
            need(execute_stage.__code__ is ref.run.__code__ and
                 execute_stage.__globals__['validate'] is ref.validate,
                 'unchanged original reference run and complete validation')
            result = execute_stage(build, Path(cfg['adapter']).resolve(),
                                   Path(cfg['dot16_hardware_result']).resolve(), output)
            need(result['status'] == b.REFERENCE_PASS and result['contract'] == CONTROLLER_CONTRACT,
                 'original complete reference campaign result')
        check()
        for path, expected in pins.items():
            check()
            need(sha(path) == expected and str(Path(path).resolve()) == resolved[path],
                 'stage input unchanged: ' + path)
        need(all(row['process'].get('process_started') is True and
                 row['process'].get('direct_child_reaped') is True and
                 row['process'].get('process_group_absent_after_exit') is True and
                 not row['process'].get('residual_process_group') and
                 not row['process'].get('timed_out') for row in state['commands']),
             'all bounded commands completed and closed')
        check()
        state.update(status='W2_' + args.stage.upper() + '_STAGE_COMPLETE', stage_completed=True,
                     original_status=result['status'], inputs_unchanged=True,
                     reference_qualified=args.stage == 'reference')
    except BaseException as error:
        failure = error
        state.update(status='FAILED', error=repr(error), stage_completed=False, reference_qualified=False)
    finally:
        closing[0] = True
        signal.setitimer(signal.ITIMER_REAL, 0)
        if pending[0] is not None:
            state['signal'] = pending[0]
            if failure is None:
                failure = InterruptedError('signal before final receipt: ' + str(pending[0]))
                state.update(status='FAILED', error=repr(failure), stage_completed=False, reference_qualified=False)
        state['all_children_reaped'] = all(
            not row['process'].get('process_started') or
            (row['process'].get('direct_child_reaped') is True and
             row['process'].get('process_group_absent_after_exit') is True)
            for row in state['commands'])
        state['finished'] = stamp()
        try:
            if output_safe:
                if not output.exists():
                    output.mkdir(parents=True)
                save(output / 'stage-input-pins.json', dict(files=pins, resolved_targets=resolved))
                persist()
        finally:
            resource.setrlimit(resource.RLIMIT_FSIZE, old_limit)
            os.environ.clear(); os.environ.update(old_environment)
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
    print(json.dumps({k: v for k, v in state.items() if k != 'commands'}, indent=2), flush=True)
    if failure is not None:
        raise failure
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller', type=Path, required=True)
    parser.add_argument('--binding-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage', choices=('build', 'reference'), required=True)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--cpu', type=int, choices=(1,), default=1)
    parser.add_argument('--cpu1', action='store_const', dest='cpu', const=1)
    parser.add_argument('--budget-seconds', type=int, required=True)
    run(parser.parse_args())
