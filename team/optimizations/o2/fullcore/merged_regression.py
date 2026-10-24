#!/usr/bin/env python3
"""Merged O2 baseline: qualified legacy normals plus a new bit100/recovery pair.

The old fixed-negative contract is preserved. This entry never rebuilds hardware,
changes an old receipt, resumes a partial EMU pair, or measures performance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'r2-safe-tail'))
import merged_screen as m

f, g = m.f, m.g
CONTRACT = 'o2-merged-regression-new-fixture-v1'
PASS = 'O2_MERGED_REGRESSION_NEW_FIXTURE_PASS'
NEGATIVE = '6e8b3488bb4cc516f05a7aa81c40b9d5e66085e275d4fbe27da85f05748b9a5f'
MATRIX0 = 'b8b7e1a7032070bdfdfc2a747ab6453011ea9959ebd5ac52ca21b439d4d113b3'
REUSED = ('hello-vadd',) + tuple('functional-%d' % i for i in range(1, 8)) + ('control', 'dense-batch128')
CORE = set(REUSED) | {'negative-vdot', 'functional-0'}
SUPPLEMENTS = {'o2-diagnostic', 'o2-control-diagnostic'}
CAMPAIGNS = ('core-normal-partial-01', 'core-normal-parallel-02', 'core-normal-parallel-04')
EXTERNAL = {
    'tools-normal-partial/run_normal_partial.py': 'fa96b9f98f49a5b461457b44bbf27961ad70a846930c71c6fc871c8c870388d0',
    'tools-normal-parallel/run_normal_parallel.py': '6b34a8337117ce2dbae80ced5feef098536a5651350c79489e0e3e61cfb7c472',
    'tools-normal-parallel/schedule_resume.py': '0dab48661e1dbde498e99bb21c4a5f353e439c44fa7932b40e7646a592a9df7d',
    'tools-normal-four/run_normal_four.py': '703f76e2bcb3432a76366e4376e92b1d60bdc8503d96dddc8f52f183d74aaf17',
    'tools-normal-four/schedule_four.py': '666801be24eb01e06049eec16f74669711089f450f4fe14f1081c88eb6b483d8',
}
CONFIG_FIELDS = {'hardware_source', 'build_record', 'build_driver', 'reference', 'flash', 'legacy_base', 'fixture_dir'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def instant(value):
    stamp = datetime.fromisoformat(value)
    g.require(stamp.tzinfo is not None and stamp.utcoffset() is not None, 'timestamp lacks UTC offset')
    return stamp.astimezone(timezone.utc)


def unique_rows(rows, expected):
    g.require(isinstance(rows, list) and len(rows) == len(expected), 'wrong selected job count')
    result = {r['name']: r for r in rows}
    g.require(len(result) == len(rows) and set(result) == set(expected), 'missing/duplicate/extra selected job')
    return result


def tree_hashes(directory):
    result = {}
    for p in sorted(Path(directory).rglob('*')):
        g.require(not p.is_symlink(), 'unexpected evidence symlink: ' + str(p))
        if p.is_file():
            result[p.relative_to(directory).as_posix()] = g.sha(p)
    return result


def identical_copy(source, target, expected_result):
    left, right = tree_hashes(source), tree_hashes(target)
    g.require(left and left == right and left.get('result.json') == expected_result,
              'adopted job bytes differ from original: ' + str(target))
    return left


def config(path, repo):
    value = read(path)
    g.require(set(value) == CONFIG_FIELDS, 'unexpected/missing merged regression configuration field')
    for key, name in value.items():
        g.require(isinstance(name, str) and bool(name.strip()), 'invalid configured path: ' + key)
        value[key] = str(Path(name.replace('${REPO}', str(repo))).expanduser().resolve())
    g.require(Path(value['build_record']).parent == Path(value['legacy_base']), 'legacy/build source mismatch')
    return value


def bind(repo, cfg):
    root = Path(cfg['hardware_source'])
    fixed = {
        'merged_screen.py': 'ff75464c5b0f75349fc4321bdd80a7a85985a54ae415ad347c3ce04fdf4bd885',
        'fullcore_screen.py': '5f5c719a9a5b675f4de166ca30a3d89bd52c944c667cee302f66da94fa2779f2',
        'linked_gate.py': '96807465bfd97a483f31ce100e552e2b83c4d0edd59f9bf4d817c66abd80ec1f',
    }
    m.verify_files({str(repo / g.REL / name): digest for name, digest in fixed.items()})
    recheck_path = root / 'team/optimizations/o2/fullcore/recheck.py'
    g.require(g.sha(recheck_path) == '8cebe76129f86747cdddf87f93f54d4379a8606dd3c1a20d55008361f2f95140', 'frozen raw auditor changed')
    r = g.load('merge_bound_recheck', recheck_path)
    names = list(r.DRIVERS) + ['team/optimizations/o2/fullcore/recheck.py',
        'team/optimizations/o2/fullcore/run_supplements.py', 'team/optimizations/o2/fullcore/workloads/check.py']
    blobs = r.git_blobs(root, m.SOURCE, names)
    tools = {}
    for name, raw in blobs.items():
        digest = hashlib.sha256(raw).hexdigest()
        g.require(g.sha(root / name) == digest and g.sha(repo / name) == digest, 'checker differs from pinned Git source: ' + name)
        tools[str(root / name)] = digest
        tools[str(repo / name)] = digest
    load = lambda name, rel: r.load_blob(name, root / rel, blobs[rel])
    runner = load('run_suite', r.DRIVERS[0])
    analyze = load('analyze', r.DRIVERS[1])
    control = load('merge_bound_control', r.DRIVERS[2])
    guard = load('merge_bound_guard', r.DRIVERS[3])
    functional = load('merge_bound_functional', r.DRIVERS[4])
    perf = load('merge_bound_perf', r.DRIVERS[5])
    gate = load('merge_bound_runtime_gate', r.DRIVERS[6])
    supplement = load('merge_bound_supplement', 'team/optimizations/o2/fullcore/run_supplements.py')
    workload = load('merge_bound_workload', 'team/optimizations/o2/fullcore/workloads/check.py')
    tools.update(m.checker_files(repo))
    tools[str(Path(__file__).resolve())] = g.sha(__file__)
    return SimpleNamespace(r=r, runner=runner, analyze=analyze, guard=guard, perf=perf, gate=gate,
                           supplement=supplement, workload=workload,
                           modules=(runner, analyze, control, guard, functional, perf), tools=tools)


def fixture(cfg):
    directory = Path(cfg['fixture_dir'])
    record = read(directory / 'fixture.json')
    binary = directory / 'negative-reference.so'
    g.require(record.get('source_sha256') == m.NEGATIVE_SHA and g.sha(directory / 'negative-fixture.c') == m.NEGATIVE_SHA
              and record.get('normal_reference_sha256') == f.REFERENCE and record.get('negative_sha256') == NEGATIVE
              and g.sha(binary) == NEGATIVE and record.get('binary') == str(binary)
              and record.get('historical_negative_hash_claim') is False, 'new negative fixture identity differs')
    compiler = record['command'][0]
    expected = [compiler, '-shared', '-fPIC', '-O2', '-DREF_SO="' + cfg['reference'] + '"',
                str(directory / 'negative-fixture.c'), '-Wl,--no-as-needed', cfg['reference'], '-ldl', '-o', str(binary)]
    g.require(record['command'] == expected, 'negative build command changed')
    for name in ('compiler', 'compile', 'linkage'):
        step = directory / name
        command = read(step / 'command.json')
        argv = [compiler, '--version'] if name == 'compiler' else expected if name == 'compile' else [command['command'][0], '-d', str(binary)]
        g.require(command.get('process_started') is True and command.get('exit_code') == 0
                  and not command.get('timed_out') and command.get('command') == argv
                  and command.get('raw_sha256') == {n: g.sha(step / n) for n in ('stdout.log', 'stderr.log')},
                  'negative fixture build receipt changed: ' + name)
    g.require('Shared library: [' + cfg['reference'] + ']' in (directory / 'linkage/stdout.log').read_text(), 'negative direct dependency missing')
    return record


def adoption(base, selected, states):
    chains, files = {}, {}
    expected_origin = {name: CAMPAIGNS[2] for name in REUSED}
    expected_origin.update({'hello-vadd': CAMPAIGNS[0], 'functional-1': CAMPAIGNS[1], 'functional-2': CAMPAIGNS[1]})
    for name in REUSED:
        current, seen, chain = selected, set(), []
        while True:
            g.require(current.name in CAMPAIGNS and current not in seen, 'invalid/cyclic adopted source')
            seen.add(current)
            directory = current / name
            hashes = tree_hashes(directory)
            files.update({str(directory / rel): digest for rel, digest in hashes.items()})
            chain.append(dict(campaign=current.name, directory=str(directory), files=hashes))
            mapping = current / 'adopted-jobs.json'
            rows = read(mapping) if mapping.exists() else []
            g.require(len({r['name'] for r in rows}) == len(rows), 'duplicate adoption record')
            matches = [r for r in rows if r['name'] == name]
            if not matches:
                break
            item = matches[0]
            source = Path(item['source'])
            g.require(source.name == name and source.parent.parent == base and
                      item['copied_to'] == str(directory) and item['new_emu_executed'] is False,
                      'adopted source identity differs')
            identical_copy(source, directory, item['result_sha256'])
            files[str(mapping)] = g.sha(mapping)
            current = source.parent
        g.require(current.name == expected_origin[name], 'unexpected original execution campaign: ' + name)
        record = read(current / name / 'result.json')
        state = states[current.name]
        end = state.get('finished')
        if current.name == CAMPAIGNS[0]:
            retired = read(current / 'orchestration-retired.json')
            g.require(retired.get('status') == 'DISPATCHER_RETIRED_AFTER_FUNCTIONAL_0_RESULT'
                      and retired.get('completed_results_preserved') is True
                      and retired.get('terminated_pending_descendants') == [], 'original dispatcher retirement is not qualified')
            end = retired['finished']
        g.require(instant(state['started']) <= instant(record['started']) <= instant(record['finished']) <= instant(end),
                  'original job outside actual campaign lifetime: ' + name)
        chains[name] = chain
    return chains, files


def prepare(repo, cfg, out):
    ctx = bind(repo, cfg)
    hardware_files, profile = m.hardware_profile(repo, cfg)
    ctx.pins = read(Path(cfg['build_record']) / 'hardware-inputs.json')
    ctx.args = SimpleNamespace(preflight_only=False, hardware_pins=Path(cfg['build_record']) / 'hardware-inputs.json',
        emu=Path(cfg['hardware_source']) / 'build/emu', t12_root=ctx.runner.DEFAULT_T12,
        t14_root=ctx.runner.DEFAULT_T14, dense_build=ctx.runner.DEFAULT_DENSE, timeout='120m', jobs=1)
    base = Path(cfg['legacy_base'])
    external = {str(base / name): digest for name, digest in EXTERNAL.items()}
    m.verify_files(external)
    adapted = g.load('merge_verified_normal_four', base / 'tools-normal-four/run_normal_four.py')
    g.require(adapted.ROOT == Path(cfg['hardware_source']), 'adapted driver hardware root differs')
    pins, paths, fresh = adapted.preflight(ctx.args, ctx.guard, ctx.perf)
    g.require(pins == ctx.pins and fresh['status'] == 'PARTIAL_NORMAL_INPUTS_VERIFIED_NEGATIVE_MISSING'
              and fresh['full_frozen_preflight_pass'] is False, 'legacy partial contract changed')
    g.require(str(paths['reference']) == cfg['reference'] and str(paths['flash']) == cfg['flash'], 'configured normal inputs differ from legacy contract')
    states, inputs = {}, dict(hardware_files, **ctx.tools, **external)
    inputs.update(fresh['input_files'])
    canonical = {str(Path(cfg['hardware_source']) / name): g.sha(Path(cfg['hardware_source']) / name)
                 for name in ctx.r.DRIVERS[1:]}
    variants = (('tools-normal-partial/run_normal_partial.py',),
                ('tools-normal-parallel/run_normal_parallel.py', 'tools-normal-parallel/schedule_resume.py'),
                ('tools-normal-four/run_normal_four.py', 'tools-normal-four/schedule_four.py'))
    for name, variant, jobs in zip(CAMPAIGNS, variants, (1, 2, 4)):
        campaign = base / name
        old = read(campaign / 'preflight.json')
        state = read(campaign / 'campaign-state.json'); states[name] = state
        drivers = dict(canonical, **{str(base / p): EXTERNAL[p] for p in variant})
        g.require(old['driver_files'] == drivers and old['input_files'] == fresh['input_files'] and
                  old['hardware_pins_sha256'] == m.META['hardware-inputs.json'] and old['emu_sha256'] == m.EMU
                  and old['hardware_checked'] is True and old['full_frozen_preflight_pass'] is False
                  and old['missing_required_input'] == fresh['missing_required_input']
                  and old['status'] == fresh['status'] and old['matrix_unique'] == 117 and old['matrix_executed'] == 124,
                  'legacy preflight identity differs: ' + name)
        expected_invocation = [str(base / variant[0]), '--output', str(campaign), '--hardware-pins', str(ctx.args.hardware_pins),
                               '--emu', str(ctx.args.emu), '--jobs', str(jobs)]
        g.require(state['source_commit_at_start'] == m.SOURCE and state['build_source_commit'] == m.SOURCE
                  and state['invocation'] == expected_invocation and state['jobs'] == jobs and state['timeout'] == '120m'
                  and state['emu'] == str(ctx.args.emu) and state['output'] == str(campaign), 'legacy campaign identity changed: ' + name)
        for p in campaign.iterdir():
            if p.is_file():
                inputs[str(p)] = g.sha(p)
    selected = base / CAMPAIGNS[2]
    originals = {name: read(selected / name / 'result.json') for name in CORE}
    ctx.r.validate_final_campaign(states[CAMPAIGNS[2]], read(selected / 'preflight.json'), pins,
                                  originals, read(selected / 'result.json'))
    g.require(originals['negative-vdot']['status'] == 'BLOCKED_MISSING_FROZEN_INPUT'
              and originals['negative-vdot']['emulator_executed'] is False, 'old missing negative status changed')
    chains, raw_files = adoption(base, selected, states)
    inputs.update(raw_files)
    ctx.fixture = fixture(cfg)
    inputs.update({str(Path(cfg['fixture_dir']) / p): digest for p, digest in tree_hashes(Path(cfg['fixture_dir'])).items()})
    ctx.paths = dict(paths, negative=Path(ctx.fixture['binary']))
    ctx.jobs = {row[0]: row for row in ctx.r.original_jobs(ctx.args, ctx.paths)}
    ctx.inputs = inputs
    ctx.profile = profile
    ctx.chains = chains
    ctx.selected = selected
    ctx.originals = originals
    g.save(out / 'hardware-profile.json', profile)
    g.save(out / 'hardware-pins.json', pins)
    g.save(out / 'legacy-preflight-recheck.json', fresh)
    g.save(out / 'adoption-provenance.json', chains)
    g.save(out / 'fixture.json', ctx.fixture)
    g.save(out / 'runtime-inputs.json', inputs)
    return ctx


def reuse_audit(ctx, cfg, out):
    directory = out / 'reused-core'; directory.mkdir()
    rows = []
    for name in REUSED:
        _, image, data, reference = ctx.jobs[name]
        row = ctx.r.recheck_job(name, image, data, reference, ctx.originals[name], ctx.selected, directory,
                               ctx.args, ctx.paths, ctx.modules, ctx.gate)
        g.require(row['status'] != 'FAILED', 'reused raw architecture check failed: ' + name + ': ' + row.get('error', ''))
        g.require(row['status'] == ctx.originals[name]['status'] and
                  row['observation_counts'] == ctx.originals[name]['observation_counts'], 'reused verdict changed: ' + name)
        row['provenance'] = ctx.chains[name]
        rows.append(row)
        print('REUSED_RAW_PASS', name, flush=True)
    supplement = Path(cfg['legacy_base']) / 'supplements-01'
    old = read(supplement / 'preflight.json')
    for rel in ('team/optimizations/o2/fullcore/run_suite.py', 'team/optimizations/o2/fullcore/analyze.py',
                'team/scripts/artifact_guard.py', 'team/optimizations/o1/audit/runtime_gate.py'):
        path = str(Path(cfg['hardware_source']) / rel)
        g.require(old['driver_files'].get(path) == ctx.tools[path], 'supplement shared checker mismatch')
    result = ctx.supplement.recheck_campaign(supplement, out / 'supplements', ctx.pins, m.EMU,
                                            analyze=ctx.analyze, workload=ctx.workload)
    ctx.inputs.update({str(supplement / p): digest for p, digest in tree_hashes(supplement).items()})
    ctx.inputs.update(old['input_files'])
    g.save(out / 'runtime-inputs.json', ctx.inputs)
    return rows, result


def pair_relation(negative, normal, image, emu, flash, reference, fixture_path):
    g.require(negative.get('status') == m.NEGATIVE_PASS and normal.get('status') == 'VDOT_MATRIX_SHARD_PASS', 'pair is not qualified')
    for row in (negative, normal):
        g.require(row.get('process_started') is True and type(row.get('pid')) is int and row['pid'] > 0
                  and not row.get('timed_out') and instant(row['started']) <= instant(row['finished']), 'pair process incomplete')
        for path, digest in ((image, MATRIX0),
                             (emu, m.EMU), (flash, f.FLASH), (reference, f.REFERENCE)):
            g.require(row['files'].get(str(path)) == digest, 'pair shared input mismatch')
        g.require(row.get('auxiliary_files') == m.AUX, 'pair auxiliary inputs differ')
    g.require(negative['pid'] != normal['pid'] and instant(normal['started']) >= instant(negative['finished']), 'recovery is not a new subsequent process')
    g.require(negative['files'].get(str(fixture_path)) == NEGATIVE and str(fixture_path) not in normal['files'], 'pair selected reference mismatch')
    g.require(negative['negative_target'] == 'vdot' and normal['negative_target'] is None, 'pair injection environment mismatch')
    g.require(negative.get('environment_overrides') == {'XS_NEGATIVE_VECTOR_TARGET': 'vdot'}
              and normal.get('environment_overrides') == {'XS_NEGATIVE_VECTOR_TARGET': None}, 'pair environment receipt mismatch')
    g.require(negative['command'][:10] + negative['command'][11:] == normal['command'][:10] + normal['command'][11:]
              and negative['command'][10] == '--diff=' + str(fixture_path)
              and normal['command'][10] == '--diff=' + str(reference), 'pair command mismatch')
    return True


def execute_pair(ctx, cfg, out, state, persist):
    runs = out / 'runs'; runs.mkdir()
    audit = out / 'new-core'; audit.mkdir()
    rows, raw_rows = [], []
    for name in ('negative-vdot', 'functional-0'):
        _, image, data, reference = ctx.jobs[name]
        directory = runs / name; directory.mkdir()
        cwd = directory / 'cwd'; cwd.mkdir()
        (cwd / 'build').mkdir()
        for filename, digest in m.AUX.items():
            shutil.copyfile(Path(cfg['hardware_source']) / 'build' / filename, cwd / 'build' / filename)
            g.require(g.sha(cwd / 'build' / filename) == digest, 'new runtime auxiliary mismatch')
        command = ['timeout', ctx.args.timeout, 'stdbuf', '-o0', '-e0', str(ctx.args.emu), '-i', str(image),
                   '--flash=' + cfg['flash'], '--ram-size=128MB', '--diff=' + str(reference), '--max-cycles=5000000']
        record = dict(name=name, status='RUNNING', started=f.now(), command=command, cwd=str(cwd),
                      files={str(p): g.sha(p) for p in (ctx.args.emu, ctx.paths['reference'], reference, ctx.paths['flash'], image)},
                      negative_target='vdot' if name == 'negative-vdot' else None, auxiliary_files=m.AUX,
                      environment_overrides={'XS_NEGATIVE_VECTOR_TARGET': 'vdot' if name == 'negative-vdot' else None},
                      process_started=False, pid_kind='timeout process-group leader', actual_new_execution=True)
        env = m.execution_environment(name == 'negative-vdot')
        record.update(environment_contract=m.ENVIRONMENT_CONTRACT, environment=dict(env))
        state['new_emu_launch_attempts'] += 1
        state.update(active_result=str(directory / 'runtime.json'), active_process_group=None)
        def progress():
            if record.get('process_started') and not record.get('counted_launch'):
                state['new_emu_runs'] += 1
                record['counted_launch'] = True
            g.save(directory / 'runtime.json', record)
            state['active_process_group'] = record.get('pid')
            persist()
        progress()
        m.verify_files(ctx.inputs)
        try:
            with (directory / 'stdout.log').open('wb') as stdout, (directory / 'stderr.log').open('wb') as stderr:
                f.spawn(command, cwd, stdout, stderr, record, progress, env=env, timeout=7210)
        finally:
            record['finished'] = f.now()
            state['active_process_group'] = None
            g.save(directory / 'runtime.json', record)
            persist()
        stdout, stderr = ((directory / n).read_bytes() for n in ('stdout.log', 'stderr.log'))
        (directory / 'run.log').write_bytes(stderr + stdout)
        record['raw_logs_sha256'] = {n: g.sha(directory / n) for n in ctx.r.RAW_NAMES}
        g.require(type(record.get('exit_code')) is int and not record.get('timed_out'), 'EMU did not complete')
        (directory / 'exit-code.txt').write_text(str(record['exit_code']) + '\n', encoding='ascii')
        record['status'] = 'RAW_EMU_EXITED_AWAITING_RECHECK'
        g.save(directory / 'result.json', record)
        m.verify_files(ctx.inputs)
        g.require({n: g.sha(cwd / 'build' / n) for n in m.AUX} == m.AUX, 'runtime auxiliary changed')
        row = ctx.r.recheck_job(name, image, data, reference, record, runs, audit, ctx.args, ctx.paths, ctx.modules, ctx.gate)
        g.require(row['status'] != 'FAILED', 'new raw architecture check failed: ' + name + ': ' + row.get('error', ''))
        if name == 'negative-vdot':
            detail = row['runtime_gate']
            elf = g.ELF((image.parent / 'vdot-exceptions.elf').read_bytes())
            g.require(int.from_bytes(elf.read(int(detail['pc'], 16), 4), 'little') == int(detail['word'], 16), 'negative instruction not in selected ELF')
            g.save(directory / 'negative.json', detail)
        for key in ('status', 'observation_status', 'observation_counts', 'runtime_gate', 'expected_vdot_commits'):
            if key in row:
                record[key] = row[key]
        g.save(directory / 'result.json', record)
        state.update(active_result=None, active_process_group=None)
        persist()
        rows.append(row); raw_rows.append(record)
        print('NEW_PAIR_PASS', name, flush=True)
    pair_relation(*raw_rows, ctx.jobs['functional-0'][1], ctx.args.emu, ctx.paths['flash'], ctx.paths['reference'], ctx.paths['negative'])
    return rows, raw_rows


def aggregate(ctx, core, supplement, raw_pair):
    unique_rows(core, CORE)
    unique_rows(supplement['records'], SUPPLEMENTS)
    pair_relation(*raw_pair, ctx.jobs['functional-0'][1], ctx.args.emu, ctx.paths['flash'], ctx.paths['reference'], ctx.paths['negative'])
    passed, recovery, coverage = ctx.runner.assess_suite(core, ctx.jobs['functional-0'][1])
    combined = ctx.r.combine_g3(passed, core, supplement, ctx.runner)
    g.require(passed and recovery and combined['whole_suite_pass'], 'merged exact-set/coverage/recovery gate failed')
    return dict(status=PASS, contract=CONTRACT, hardware_source=m.SOURCE, emu_sha256=m.EMU,
                negative_sha256=NEGATIVE, merged_baseline_acceptance=True, historical_fixed_negative_acceptance=False,
                historical_b0_h1_acceptance=False, selected_s2_combination_acceptance=False, performance_measured=False,
                core_records=core, supplements=supplement, suite_coverage=combined['suite_coverage'],
                selected_jobs=14, reused_normal_jobs=12, new_emu_runs=2, normal_reference_recovery=True,
                note='New merged-baseline contract only. Old failed/blocked campaign states are preserved.')


def semantic_result(result):
    unique_rows(result['core_records'], CORE)
    unique_rows(result['supplements']['records'], SUPPLEMENTS)
    fields = ('name', 'status', 'started', 'finished', 'files', 'raw_logs_sha256',
              'observation_status', 'observation_counts', 'runtime_gate')
    identity = ('status', 'contract', 'hardware_source', 'emu_sha256', 'negative_sha256',
                'merged_baseline_acceptance', 'historical_fixed_negative_acceptance', 'historical_b0_h1_acceptance',
                'selected_s2_combination_acceptance', 'performance_measured', 'selected_jobs',
                'reused_normal_jobs', 'new_emu_runs', 'normal_reference_recovery')
    return dict(identity={key: result[key] for key in identity}, suite_coverage=result['suite_coverage'],
                core={row['name']: {key: row[key] for key in fields if key in row} for row in result['core_records']},
                supplements=result['supplements'])


def audit(repo, campaign, out):
    """Fresh full raw/physical-input audit; requires the retained Linux inputs."""
    g.require(not out.exists() and not out.is_relative_to(campaign), 'audit output must be new and outside campaign')
    original_state, original_result = read(campaign / 'state.json'), read(campaign / 'result.json')
    g.require(original_state['status'] == original_result['status'] == PASS
              and original_state['new_emu_runs'] == original_state['new_emu_launch_attempts'] == 2
              and original_state['active_process_group'] is None
              and original_state['active_result'] is None and original_state['finished'] == original_result['finished']
              and original_state['controller_sha256'] == original_result['controller_sha256'] == g.sha(__file__),
              'source campaign is not a completed same-controller run')
    cfg = config(campaign / 'local-config.json', repo)
    roots = [repo, campaign] + [Path(cfg[k]) for k in ('hardware_source', 'legacy_base', 'fixture_dir')]
    g.require(not any(out.is_relative_to(p) or p.is_relative_to(out) for p in roots), 'audit output overlaps inputs')
    out.mkdir(parents=True)
    started = f.now()
    m.verify_files(read(campaign / 'runtime-inputs.json'))
    ctx = prepare(repo, cfg, out)
    core, supplement = reuse_audit(ctx, cfg, out)
    g.require(ctx.inputs == read(campaign / 'runtime-inputs.json'), 'audited input inventory differs from run')
    new_out = out / 'new-core'; new_out.mkdir()
    raw_pair = []
    for name in ('negative-vdot', 'functional-0'):
        _, image, data, reference = ctx.jobs[name]
        directory = campaign / 'runs' / name
        raw = read(directory / 'result.json')
        g.require(raw.get('cwd') == str(directory / 'cwd') and
                  {n: g.sha(directory / 'cwd/build' / n) for n in m.AUX} == m.AUX, 'archived new-run cwd/auxiliary mismatch')
        row = ctx.r.recheck_job(name, image, data, reference, raw, campaign / 'runs', new_out,
                               ctx.args, ctx.paths, ctx.modules, ctx.gate)
        g.require(row['status'] != 'FAILED', 'new-pair raw replay failed: ' + name)
        if name == 'negative-vdot':
            detail = row['runtime_gate']
            elf = g.ELF((image.parent / 'vdot-exceptions.elf').read_bytes())
            g.require(int.from_bytes(elf.read(int(detail['pc'], 16), 4), 'little') == int(detail['word'], 16), 'replayed negative ELF binding differs')
        core.append(row); raw_pair.append(raw)
    result = aggregate(ctx, core, supplement, raw_pair)
    g.require(semantic_result(result) == semantic_result(original_result), 'cached architecture/coverage result differs from raw replay')
    m.verify_files(ctx.inputs)
    result.update(status='O2_MERGED_REGRESSION_RAW_AUDIT_PASS', source_campaign=str(campaign),
                  source_result_sha256=g.sha(campaign / 'result.json'), started=started, finished=f.now(),
                  controller_sha256=g.sha(__file__), source_campaign_new_emu_runs=2, new_emu_runs=0,
                  audit_scope='All 14 selected raw records, actual pinned Linux inputs and provenance; no new EMU')
    g.save(out / 'result.json', result)
    print(result['status'], flush=True)
    return 0


def run(repo, cfg, out, operation_id):
    g.require(not out.exists(), 'output already exists; no EMU resume is supported')
    roots = [repo] + [Path(cfg[k]) for k in ('hardware_source', 'legacy_base', 'fixture_dir')]
    g.require(not any(out.is_relative_to(p) or p.is_relative_to(out) for p in roots), 'output overlaps an input root')
    out.mkdir(parents=True)
    g.save(out / 'local-config.json', cfg)
    state = dict(status='PRECHECK_RUNNING', contract=CONTRACT, operation_id=operation_id, started=f.now(),
                 source_base=subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip(),
                 controller_sha256=g.sha(__file__), new_emu_launch_attempts=0, new_emu_runs=0,
                 active_result=None, active_process_group=None, performance_measured=False,
                 historical_fixed_negative_acceptance=False, historical_b0_h1_acceptance=False)
    persist = lambda: g.save(out / 'state.json', state)
    persist()
    try:
        ctx = prepare(repo, cfg, out)
        core, supplement = reuse_audit(ctx, cfg, out)
        state.update(status='REUSED_ARCHITECTURE_PASS_PAIR_RUNNING', reused_normal_jobs=12)
        persist()
        pair, raw_pair = execute_pair(ctx, cfg, out, state, persist)
        g.require(state['new_emu_runs'] == state['new_emu_launch_attempts'] == 2, 'unexpected new execution count')
        m.verify_files(ctx.inputs)
        _, final_profile = m.hardware_profile(repo, cfg)
        g.require(final_profile == ctx.profile, 'post-run hardware profile differs')
        result = aggregate(ctx, core + pair, supplement, raw_pair)
        state.update(status=PASS, finished=f.now(), active_result=None, active_process_group=None)
        g.save(out / 'result.json', dict(result, started=state['started'], finished=state['finished'], controller_sha256=state['controller_sha256']))
        persist()
        print(PASS, flush=True)
        return 0
    except BaseException as exc:
        state.update(status='O2_MERGED_REGRESSION_FAILED', error=repr(exc), finished=f.now())
        persist()
        print(state['status'], repr(exc), file=sys.stderr, flush=True)
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--action', choices=('run', 'audit'), default='run')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--operation-id')
    args = parser.parse_args()
    try:
        repo = args.repo.resolve()
        if args.action == 'audit':
            g.require(args.campaign is not None, '--campaign is required for audit')
            sys.exit(audit(repo, args.campaign.resolve(), args.output.resolve()))
        g.require(args.config is not None and args.operation_id, '--config and --operation-id are required for run')
        sys.exit(run(repo, config(args.config, repo), args.output.resolve(), args.operation_id))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, 'O2_MERGED_REGRESSION_REJECTED: ' + str(exc) + '\n')
