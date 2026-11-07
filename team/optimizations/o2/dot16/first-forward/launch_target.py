"""Launch one reviewed four-arm TRACE0 profile with the unchanged P/PQ owner.

This entry does not build, freeze a profile or run a preflight guest. The source
and profile SHA values, source owner, paths and all owner budgets are explicit.
The original owned_campaign() and case_closure() functions are imported intact.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import signal
import sys
import time

CONTRACT = 'r3-dot16-first-forward-v1'
OWNER_SHA = '25758520f36b83d3ca5feb25ece444b963d1e673f7a375096ffe3f60a5f3eafd'
CASES = (('paired16', 0x50313631, False), ('paired16_quantize', 0x50535131, False),
         ('dot16', 0x44313631, False), ('dot16_quantize', 0x44313651, False))
CHECK_PATH = 'target-support/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/check.py'
CHECK_SHA = '0c81b6620b2c417ef73a251899bbe3af0ec4749832dd76ad2631b3e6fbd1386f'
GENERATE_SHA = 'cac40ad6f5fc66d5c793683bf54fb3e411f7490c25468bc24c7bfc8be406e1e7'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args):
    begin = time.monotonic()
    need(sys.dont_write_bytecode, '-B required; frozen inputs stay read-only')
    need(digest(__file__) == args.source_sha256, 'reviewed launcher source')
    paths = [args.controller, args.profile, args.owner_source, args.phase_output, args.export_output]
    need(all(path.is_absolute() and path == path.resolve() for path in paths),
         'explicit canonical absolute paths')
    controller, profile_path, owner_source, phase, export = paths
    need(digest(profile_path) == args.profile_sha256 and digest(owner_source) == OWNER_SHA,
         'reviewed actual profile and unchanged original process owner')
    profile = read(profile_path)
    need(profile['contract'] == 'r3-dot16-first-forward-resources-v1'
         and profile['workload_contract'] == CONTRACT and profile['status'] == 'FROZEN_BEFORE_EMU'
         and profile['cases'] == [list(case) for case in CASES]
         and profile['automatic_budget_extension'] is False
         and profile['performance_qualified'] is False
         and profile['full_retirement_window_audited'] is False,
         'exact four-arm frozen profile')
    cpus = profile['cpu_slots']
    need(1 <= len(cpus) <= 4 and len(set(cpus)) == len(cpus)
         and os.sched_getaffinity(0) == set(cpus), 'exact assigned CPU slots; no implicit fallback')
    roots = profile['paths']
    need(set(roots) == {'build', 'reference', 'adapter', 'identity', 'output'}
         and all(Path(path).is_absolute() and Path(path) == Path(path).resolve() for path in roots.values()),
         'canonical roots from the reviewed profile')
    output = Path(roots['output'])
    need(not any(path.exists() for path in (phase, export, output)), 'fresh launch, export and campaign outputs')
    inputs = [Path(path) for path in profile['input_files']]
    inputs += [controller, profile_path, owner_source, Path(__file__).resolve()]
    # Existing directories and individual files may not contain or be contained
    # by a new output. The separate phase/export/campaign roots cannot overlap.
    for dest in (phase, export, output):
        need(not any(dest.is_relative_to(path) or path.is_relative_to(dest) for path in inputs),
             'output disjoint from every frozen input')
    need(all(not a.is_relative_to(b) and not b.is_relative_to(a)
             for i, a in enumerate((phase, export, output)) for b in (phase, export, output)[i + 1:]),
         'separate phase, export and campaign outputs')
    work, grace, hard, external = (args.work_seconds, args.term_grace_seconds,
                                   args.hard_seconds, args.external_seconds)
    waves = (len(CASES) + len(cpus) - 1) // len(cpus)
    need(0 < work < work + grace < hard < external
         and work > waves * profile['external_timeout_seconds'],
         'explicit owner limits covering the declared case waves and cleanup')
    helper = controller / CHECK_PATH
    need(digest(helper) == CHECK_SHA and digest(helper.parent / 'generate.py') == GENERATE_SHA,
         'unchanged source helper for receipts and time')
    # Authenticate the complete frozen runtime closure before any runtime import.
    # The existing profile_inputs() below still rechecks its physical and budget bindings.
    for path, pin in profile['input_files'].items():
        need(digest(path) == pin, 'reviewed frozen input before import: ' + path)
    need(all(str(controller / name) in profile['input_files']
             for name in ('binding.json', 'run.py', 'audit.py')), 'controller belongs to the reviewed profile')
    owner = load('dot16_original_campaign_owner', owner_source)
    h = load('dot16_target_receipt_helper', helper)
    runtime = load('dot16_reviewed_target_runtime', controller / 'run.py')
    need(runtime.b.CONTRACT == CONTRACT and runtime.TARGET_CASES == CASES,
         'actual runtime four-arm domain')
    actual, files, identity, checker = runtime.profile_inputs(profile_path,
        *(Path(roots[name]) for name in ('build', 'reference', 'adapter', 'identity', 'output')))
    need(actual == profile, 'actual target profile validation unchanged')
    protected_roots = [runtime.b.REPO, controller, owner_source.parent, Path(__file__).resolve().parent,
        *(Path(roots[name]) for name in ('build', 'reference', 'adapter')),
        Path(roots['identity']).parent, Path(identity['configuration']['hardware_source']),
        Path(read(Path(roots['build']) / 'result.json')['am_home'])]
    for dest in (phase, export, output):
        runtime.old.r.parent.outside_inputs(dest, protected_roots)
    need(all(str(controller / name) in files and digest(controller / name) == files[str(controller / name)]
             for name in ('binding.json', 'run.py', 'audit.py')), 'actual controller source in frozen profile')
    fixed = {str(path): digest(path) for path in
             (Path(__file__).resolve(), profile_path, owner_source, helper,
              controller / 'binding.json', controller / 'run.py', controller / 'audit.py')}
    need(fixed[str(profile_path)] == args.profile_sha256
         and fixed[str(Path(__file__).resolve())] == args.source_sha256, 'reviewed inputs still exact')
    argv = [sys.executable, '-B', str(controller / 'run.py')]
    for name in ('build', 'reference', 'adapter', 'identity', 'output'):
        argv += ['--' + name, roots[name]]
    argv += ['--profile', str(profile_path)]
    phase.mkdir(parents=True)
    state = dict(contract=CONTRACT, status='REVIEWED_PROFILE_READY', operation_id=profile['operation_id'],
        started=h.now(), source_sha256=args.source_sha256, original_owner_sha256=OWNER_SHA,
        profile_path=str(profile_path), profile_sha256=args.profile_sha256, campaign_output=str(output),
        cpu_slots=cpus, target_cases=[list(case) for case in CASES], expected_case_waves=waves,
        owner_pid=os.getpid(), owner_process_group=os.getpgrp(), campaign_invoked=False,
        limits=dict(campaign_work_seconds=work, campaign_term_grace_seconds=grace,
                    campaign_hard_seconds=hard, external_owner_seconds=external),
        external_limit_enforcement='must equal the enclosing tool request; not implemented by this script',
        target_correctness_qualified=False, performance_qualified=False,
        full_retirement_window_audited=False, cpu_release_verified=False)
    h.save(phase / 'state.json', state)
    h.save(phase / 'owner-inputs.json', fixed)
    h.save(phase / 'planned-commands.json', dict(campaign=argv, owner_limits=state['limits'],
        profile_sha256=args.profile_sha256, frozen_run_sha256=fixed[str(controller / 'run.py')]))
    export.mkdir(parents=True)
    owner.export_small(profile_path, export / 'resource-contract.json')
    owner.export_small(phase / 'planned-commands.json', export / 'planned-commands.json')
    def interrupted(signum, frame):
        raise InterruptedError('dot16 target owner signal ' + str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupted)
    changed = []
    try:
        preparation_seconds = time.monotonic() - begin
        need(preparation_seconds + hard < external, 'declared external limit leaves the full inner hard budget')
        state.update(status='ENTERING_CAMPAIGN', preparation_seconds=preparation_seconds,
                     external_headroom_after_inner_hard_seconds=external - preparation_seconds - hard,
                     campaign_invoked=True)
        h.save(phase / 'state.json', state)
        owner.owned_campaign(argv, phase, h, runtime.old.group_present,
            work_seconds=work, grace_seconds=grace, hard_seconds=hard)
        actual_state = read(output / 'state.json')
        need(actual_state['status'] == runtime.PASS and actual_state['new_emu_runs'] == len(CASES)
             and not any(actual_state[name] for name in
                         ('active', 'cleanup_unknown', 'cleanup_errors', 'launch_state_unknown')),
             'complete original campaign terminal receipt')
        need(len(actual_state['records']) == len(CASES)
             and {(row['name'], row['method'], row['negative']) for row in actual_state['records']} == set(CASES)
             and all(len(row['cpu_affinity']) == 1 and row['cpu_affinity'][0] in cpus
                     for row in actual_state['records']), 'four actual independent single-slot cases')
        need(owner.case_closure(runtime, output, profile['operation_id'])['cleanup_verified'],
             'original actual launcher/EMU ownership closure')
        checker.verify_files(files)
        state.update(status=actual_state['status'], target_correctness_qualified=True,
                     campaign_state_sha256=digest(output / 'state.json'),
                     results_sha256=digest(output / 'results.json'))
    except BaseException as error:
        state.update(status='FAILED_OR_PARTIAL', error=repr(error))
        raise
    finally:
        final_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        try:
            closure = owner.case_closure(runtime, output, profile['operation_id']) if output.exists() else dict(
                cleanup_verified=False, unknown=['campaign output absent; no case closure claimed'])
            state['case_cleanup'] = closure
            campaign_closed = False
            try:
                receipt = read(phase / 'campaign.command.json')
                pid = receipt.get('process_id')
                campaign_closed = (receipt.get('direct_child_reaped') is True
                    and receipt.get('process_group_absent_after_exit') is True
                    and not receipt.get('cleanup_errors') and type(pid) is int and pid > 0
                    and runtime.old.group_present(pid) is False)
                state['campaign_command_sha256'] = digest(phase / 'campaign.command.json')
            except (OSError, ValueError, TypeError) as error:
                state['campaign_owner_receipt_error'] = repr(error)
            state['cpu_release_verified'] = closure['cleanup_verified'] and campaign_closed
            changed = [path for path, pin in fixed.items() if not Path(path).is_file() or digest(path) != pin]
            state.update(finished=h.now(), elapsed_seconds=time.monotonic() - begin, changed_inputs=changed)
            if changed or not state['cpu_release_verified']:
                state.update(status='FAILED_OR_PARTIAL', target_correctness_qualified=False)
            h.save(phase / 'state.json', state)
            for path in phase.iterdir():
                if path.is_file() and not (export / path.name).exists():
                    owner.export_small(path, export / path.name)
            for name in ('state.json', 'results.json'):
                owner.export_small(output / name, export / ('campaign-' + name))
            print(json.dumps(state), flush=True)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, final_mask)
    need(not changed and state['cpu_release_verified'], 'unchanged inputs and complete resource closure')
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('controller', 'profile', 'owner-source', 'phase-output', 'export-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('source-sha256', 'profile-sha256'):
        parser.add_argument('--' + name, required=True)
    for name in ('work-seconds', 'term-grace-seconds', 'hard-seconds', 'external-seconds'):
        parser.add_argument('--' + name, type=int, required=True)
    run(parser.parse_args())
