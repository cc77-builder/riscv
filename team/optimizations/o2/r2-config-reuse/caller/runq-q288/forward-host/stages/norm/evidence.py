"""Preserve norm raw evidence and re-audit restored bytes with frozen validators.

Offline audit never launches NEMU/EMU or re-certifies a physical runtime. Each
campaign uses a fresh Python process and its own pinned source closure.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import types

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
NORM_REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/norm')
GATES = ('team/optimizations/o2/fullcore/run_suite.py', 'team/optimizations/o1/audit/runtime_gate.py',
         'team/optimizations/o2/fullcore/recheck.py', 'team/optimizations/o2/fullcore/analyze.py')


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory(root):
    found = {}
    for path in sorted(root.rglob('*')):
        need(not path.is_symlink(), 'no evidence symlink')
        if path.is_file():
            found[path.relative_to(root).as_posix()] = dict(size=path.stat().st_size, sha256=sha(path))
    return found


def closure(campaign, repo, destination, builds, extras=None):
    pins = read(campaign / 'runtime-inputs.json')
    for name, value in (extras or {}).items():
        need(name not in pins or pins[name] == value, 'no historical source pin override while sealing')
        pins[name] = value
    selected = {}
    for name, value in pins.items():
        path = Path(name)
        if not path.is_relative_to(repo):
            continue
        rel = path.relative_to(repo)
        candidates = [campaign / 'source' / rel, campaign / 'runtime-source' / rel,
                      *(build / 'source/repo' / rel for build in builds), repo / rel]
        matching = next((candidate for candidate in candidates if candidate.is_file() and sha(candidate) == value), None)
        need(matching is not None, 'exact campaign source is available: ' + str(rel))
        target = destination / 'repo' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(matching, target)
        need(sha(target) == value, 'exact copied campaign source')
        selected[rel.as_posix()] = value
    need(selected and str(NORM_REL / 'build.py') in selected, 'complete norm source root')
    save(destination / 'pins.json', dict(original_repo=str(repo), files=selected,
                                       runtime_inputs_sha256=sha(campaign / 'runtime-inputs.json'),
                                       supplemental_pins=extras or {}))


def closed(path):
    state = read(path / 'state.json')
    need(state.get('finished') and not state.get('active') and state.get('active_pid') is None
         and not state.get('cleanup_unknown'), 'campaign is terminal with no unresolved owned process')
    return state


def seal(args):
    roots = {name: getattr(args, name.replace('-', '_')).resolve() for name in
             ('build', 'reference', 'target-original', 'target-budget2')}
    for name in ('consumer-build', 'consumer-reference', 'api-build', 'api-reference'):
        value = getattr(args, name.replace('-', '_'))
        if value is not None:
            roots[name] = value.resolve()
    need(('consumer-build' in roots) == ('consumer-reference' in roots) and
         ('api-build' in roots) == ('api-reference' in roots), 'complete optional build/campaign pairs')
    need('api-build' not in roots or 'consumer-build' in roots, 'API evidence requires its consumer qualification')
    for text in args.extra:
        label, path = text.split('=', 1)
        need(re.fullmatch('[a-z0-9-]+', label) and label not in roots, 'unique bounded extra label')
        roots[label] = Path(path).resolve()
    repo, output = args.repo.resolve(), args.output.resolve()
    need(not output.exists() and not any(output.is_relative_to(root) for root in [repo, *roots.values()]),
         'fresh archive work directory outside inputs')
    need(closed(roots['target-original'])['status'] == 'FAILED', 'preserve original timeout as failed')
    need(closed(roots['target-budget2'])['status'] == 'NORM_BOUNDARY_DIFFTEST_CAMPAIGN_PASS',
         'new norm target completed before sealing')
    need(closed(roots['reference'])['status'] == 'NORM_REFERENCE_CAMPAIGN_PASS', 'completed norm reference')
    if 'consumer-reference' in roots:
        need(closed(roots['consumer-reference'])['status'] == 'NORM_W2_FORWARD_REFERENCE_CAMPAIGN_PASS',
             'completed new consumer qualification')
    if 'api-reference' in roots:
        need(closed(roots['api-reference'])['status'] == 'NORM_W2_API_REFERENCE_CAMPAIGN_PASS',
             'completed new guarded API qualification')
    output.mkdir(parents=True)
    meta, closures = output / 'metadata', output / 'closures'
    meta.mkdir(); closures.mkdir()
    builds = [roots[name] for name in ('build', 'consumer-build', 'api-build') if name in roots]
    campaigns = [name for name in ('reference', 'target-original', 'target-budget2', 'consumer-reference', 'api-reference') if name in roots]
    profile = roots['target-budget2'].with_name(roots['target-budget2'].name + '.resource-contract.json')
    need(profile.read_bytes() == (roots['target-budget2'] / 'resource-contract.json').read_bytes(),
         'original starting resource receipt equals terminal copy')
    shutil.copyfile(profile, meta / 'original-resource-contract.json')
    for name in campaigns:
        extras = {}
        if name == 'target-budget2':
            record = read(profile)
            extras[record['entry_path']] = record['entry_sha256']
            extras[record['resource_contract_path']] = record['resource_contract_sha256']
        closure(roots[name], repo, closures / name, builds, extras)
    tools = {}
    for source in (Path(__file__).resolve(), STAGES / 'archive.py', STAGES / 'restore.py'):
        rel = source.relative_to(repo)
        dest = meta / 'tool-source' / rel
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, dest)
        tools[rel.as_posix()] = sha(dest)
    for name in ('recovery.json', 'start-parameter-rejection.json'):
        source = roots['target-budget2'].parent / name
        if source.is_file():
            shutil.copyfile(source, meta / name)
    descriptor = dict(format='norm-evidence-v1', roots={name: str(path) for name, path in roots.items()},
                      original_repo=str(repo), campaigns=campaigns, tool_files=tools,
                      new_reference_runs=0, new_emu_runs=0, physical_runtime_identity_rechecked=False)
    save(meta / 'descriptor.json', descriptor)
    archiver = load('norm_evidence_archiver', STAGES / 'archive.py')
    report = archiver.seal([*(name + '=' + str(path) for name, path in roots.items()),
                           'closures=' + str(closures), 'metadata=' + str(meta)], output / 'archive')
    return report


def frozen(root, campaign, module):
    directory = root / 'closures' / campaign
    info = read(directory / 'pins.json'); source = directory / 'repo'
    descriptor = read(root / 'metadata/descriptor.json')
    need(info['original_repo'] == descriptor['original_repo'], 'one original repository identity')
    original = Path(info['original_repo'])
    runtime = read(root / campaign / 'runtime-inputs.json')
    supplemental = info['supplemental_pins']
    if campaign == 'target-budget2':
        profile = read(root / campaign / 'resource-contract.json')
        need(supplemental == {profile['entry_path']: profile['entry_sha256'],
                              profile['resource_contract_path']: profile['resource_contract_sha256']},
             'only the explicit resource profile supplements original source pins')
    else:
        need(not supplemental, 'no unregistered source supplement')
    combined = dict(runtime)
    for name, value in supplemental.items():
        need(name not in combined or combined[name] == value, 'no historical source pin override')
        combined[name] = value
    expected = {Path(name).relative_to(original).as_posix(): value for name, value in combined.items()
                if Path(name).is_relative_to(original)}
    need(info['files'] == expected, 'exact source pin membership and values from historical runtime inputs')
    for rel, expected in info['files'].items():
        need(sha(source / rel) == expected, 'all frozen source bytes')
    need(sha(root / campaign / 'runtime-inputs.json') == info['runtime_inputs_sha256'], 'exact historical runtime registry')
    value = load('frozen_norm_' + campaign.replace('-', '_'), source / NORM_REL / module)
    return value, source, info


def bind_build(root, campaign, label):
    """Bind restored build bytes to the actual historical campaign registry."""
    descriptor = read(root / 'metadata/descriptor.json')
    original = Path(descriptor['roots'][label]); repo = Path(descriptor['original_repo'])
    restored = root / label; record = read(restored / 'result.json')
    runtime = read(root / campaign / 'runtime-inputs.json')
    for name in ('result.json', 'tools.json'):
        need(runtime.get(str(original / name)) == sha(restored / name), 'historically consumed build metadata')
    for group, suffix in (('artifacts', ''), ('fixtures', 'fixture'), ('actual_source_pins', 'source')):
        for name, value in record[group].items():
            need(runtime.get(str(original / suffix / name)) == value == sha(restored / suffix / name),
                 'historically consumed complete build member: ' + name)
    for rel, value in record['source_pins'].items():
        need(runtime.get(str(repo / rel)) == value and
             runtime.get(str(original / 'source/repo' / rel)) == value == sha(restored / 'source/repo' / rel),
             'build source and actual campaign source agree: ' + rel)
    for name, value in record['external_pins'].items():
        need(runtime.get(name) == value, 'same historical external dependency pin')
    # Recheck every historical input that this package actually preserves. We
    # deliberately do not access unarchived physical tool/hardware paths.
    mappings = sorted(((Path(path), root / name) for name, path in descriptor['roots'].items()),
                      key=lambda pair: len(str(pair[0])), reverse=True)
    checked = 0
    for name, value in runtime.items():
        path = Path(name)
        for old, new in mappings:
            if path.is_relative_to(old):
                actual = new / path.relative_to(old)
                need(actual.is_file() and sha(actual) == value, 'all preserved historical input bytes agree')
                checked += 1
                break
    return record, checked


def imports(module, source, info, restored):
    pending, seen, checked = [module], set(), {}
    original = Path(info['original_repo'])
    current = Path(__file__).resolve()
    for part in reversed((NORM_REL / 'evidence.py').parts):
        need(current.name == part, 'offline auditor remains within its published repository-relative path')
        current = current.parent
    current_checkout = current
    while pending:
        current = pending.pop()
        if not isinstance(current, types.ModuleType) or id(current) in seen:
            continue
        seen.add(id(current))
        pending.extend(value for value in vars(current).values() if isinstance(value, types.ModuleType))
        name = getattr(current, '__file__', None)
        if not name:
            continue
        path = Path(name).resolve()
        if path.is_relative_to(source):
            rel = path.relative_to(source).as_posix()
            need(info['files'].get(rel) == sha(path), 'every actual imported team helper is pinned')
            checked[rel] = sha(path)
        else:
            need(not path.is_relative_to(original) and not path.is_relative_to(restored) and
                 not path.is_relative_to(current_checkout),
                 'no other physical checkout or restored source was imported')
    need(checked, 'actual frozen team validator imports inspected')
    return checked


def reference_command(receipt, runtime, dump_plan, original_build, original_dest, max_calls, seconds):
    argv = receipt['command']; cwd = Path(receipt['cwd'])
    need(cwd == original_dest, 'exact historical reference case directory')
    need(len(argv) == 9 and Path(argv[0]).name == 'reference-runner' and argv[0] in runtime and
         runtime.get(argv[1]) == '8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9',
         'exact historical normal NEMU and runner pins')
    need(argv[2:7] == [str(cwd / 'image.bin'), str(cwd), 'builtin', str(max_calls), str(seconds)]
         and argv[7] == str(original_build / 'dump-plan.txt') and argv[8] == '1' and
         runtime.get(argv[7]) == sha(dump_plan), 'exact bounded historical reference command')


def target_command(receipt, cfg, build, original_build, original_dest, runtime, cycles):
    name = 'negative.bin' if receipt['mode'] else 'real-norm.bin'
    argv = receipt['command']
    need(argv == [str(Path(cfg['hardware_source']) / 'build/emu'), '-i', argv[2], '--flash=' + cfg['flash'],
                  '--ram-size=128MB', '--diff=' + cfg['reference'], '--max-cycles=' + str(cycles), '--seed=1'],
         'exact historical target command including resource ceiling')
    need(argv[2] == str(original_build / name) and receipt['cwd'] == str(original_dest / 'cwd') and
         receipt['files'].get(argv[2]) == build['artifacts'][name] == receipt['image_sha256'],
         'original target image path and exact image bytes')
    need(all(receipt['files'].get(path) == value for path, value in runtime.items()),
         'each target receipt contains the exact campaign shared input closure')
    need(receipt['environment_overrides'] == {'XS_NEGATIVE_VECTOR_TARGET': None, 'OMP_NUM_THREADS': '1', 'EMU_THREADS': '1'},
         'same ordinary target environment')


def receipts(root, campaign, labels):
    """Cross-check historical independent processes without querying live PIDs."""
    path = root / campaign; target = campaign.startswith('target-')
    actual_cases = path / 'runs' if target else path
    need({item.parent.name for item in actual_cases.glob('*/result.json')} == set(labels), 'exact saved case membership')
    final = {}
    for label in labels:
        dest = path / 'runs' / label if target else path / label
        record = read(dest / 'result.json')
        need(record['name'] == label and record.get('process_started') is True and
             record.get('direct_child_reaped') is True and record.get('process_group_absent_after_exit') is True and
             not record.get('residual_process_group') and isinstance(record.get('pid'), int) and record['pid'] > 0 and
             record.get('process_group') == record['pid'], 'complete historical owned process receipt')
        if 'validation_sha256' in record:
            need(record['validation_sha256'] == sha(dest / 'validation.json'), 'historical validation receipt SHA')
        final[label] = record
    need(len({record['pid'] for record in final.values()}) == len(labels), 'distinct actual reference/EMU PIDs')
    state = closed(path)
    identities = {
        'reference': ('r2-s3-rmsnorm-output-v1', 'NORM_REFERENCE_CAMPAIGN_PASS'),
        'target-original': ('r2-s3-rmsnorm-output-v1', 'FAILED'),
        'target-budget2': ('r2-s3-rmsnorm-output-v1', 'NORM_BOUNDARY_DIFFTEST_CAMPAIGN_PASS'),
        'consumer-reference': ('r2-s3-forward-consumer-w2-norm-v1', 'NORM_W2_FORWARD_REFERENCE_CAMPAIGN_PASS'),
        'api-reference': ('r2-s3-forward-consumer-w2-norm-api-v1', 'NORM_W2_API_REFERENCE_CAMPAIGN_PASS'),
    }
    need((state['contract'], state['status']) == identities[campaign], 'exact terminal contract and state')
    if target:
        need(state['new_emu_runs'] == len(labels), 'target launch count agrees with complete receipts')
    elif campaign == 'consumer-reference':
        need(state['reference_runs'] == len(labels) == 8 and set(state['completed']) == set(labels),
             'all eight independently completed reference cases')
        ownership = state['launcher_receipts']
        need(len(ownership) == 8 and {item['case'] for item in ownership} == set(labels), 'all eight launcher ownership records')
        for item in ownership:
            need(item['cleanup_verified'] and item['receipt_cleanup_verified'] and
                 item['reference_pid'] == final[item['case']]['pid'] and item['reference_group_present'] is False and
                 item['launcher_group_present'] is False and item['launcher_exit_code'] == 0, 'verified launcher and child ownership')
    aggregates = []
    if 'records' in state:
        aggregates.append((state['records'], True))
    if (path / 'results.json').is_file():
        summary = read(path / 'results.json')
        need(summary['contract'] == state['contract'] and summary['status'] == state['status'], 'same terminal campaign identity')
        if 'records' in summary:
            aggregates.append((summary['records'], True))
    if (path / 'completed-runs.json').is_file():
        aggregates.append((read(path / 'completed-runs.json'), False))
    for items, complete in aggregates:
        need(len({item['name'] for item in items}) == len(items), 'unique aggregate receipt names')
        need({item['name'] for item in items} <= set(labels) and
             (not complete or {item['name'] for item in items} == set(labels)), 'exact aggregate case inventory')
        for item in items:
            actual = final[item['name']]
            # API results are saved before the finally block adds finished.
            # Every field that was actually recorded must still agree.
            need(all(key in actual and actual[key] == value for key, value in item.items()),
                 'aggregate receipt fields agree with terminal case receipt')
    return dict(cases=list(labels), unique_processes=len(final), terminal_status=state['status'],
                pids={label: record['pid'] for label, record in final.items()})


def worker(root, campaign, output):
    need(not output.exists(), 'fresh isolated audit output'); output.mkdir(parents=True)
    began = time.monotonic(); checks = {}; extras = {}
    descriptor = read(root / 'metadata/descriptor.json')
    original_roots = {name: Path(value) for name, value in descriptor['roots'].items()}
    labels = ('api',) if campaign == 'api-reference' else (
        ('negative', 'scalar', 'fr', 'ta', 'fr-cache', 'ta-cache', 'recovery', 'replay')
        if campaign == 'consumer-reference' else ('negative', 'normal', 'replay'))
    extras['historical_process_receipts'] = receipts(root, campaign, labels)
    if campaign == 'reference':
        module, source, info = frozen(root, campaign, 'reference.py')
        need(module.b.REPO == source, 'reference validator uses only its frozen repository')
        build = root / 'build'; record, bound = bind_build(root, campaign, 'build')
        extras['historical_input_files_bound'] = bound
        original = read(root / campaign / 'results.json'); runtime = read(root / campaign / 'runtime-inputs.json')
        for label in ('negative', 'normal', 'replay'):
            dest = root / campaign / label; receipt = read(dest / 'result.json')
            reference_command(receipt, runtime, build / 'dump-plan.txt', original_roots['build'],
                              original_roots[campaign] / label, 100000000, 300)
            actual = module.validate(build, dest, record, receipt, label == 'negative')
            need(actual == original['validations'][label] == read(dest / 'validation.json'), 'recomputed complete norm reference')
            checks[label] = actual
        need(checks['normal'] == checks['replay'], 'complete original norm reference replay')
    elif campaign in ('target-original', 'target-budget2'):
        budget = campaign == 'target-budget2'
        module, source, info = frozen(root, campaign, 'budget.py' if budget else 'run.py')
        owner = module
        if budget:
            profile = read(root / campaign / 'resource-contract.json')
            need((root / campaign / 'resource-contract.json').read_bytes() ==
                 (root / 'metadata/original-resource-contract.json').read_bytes(), 'initial budget receipt remains exact')
            need(profile['resource_contract'] == module.RESOURCE_CONTRACT and profile['validation_contract'] == 'r2-s3-rmsnorm-output-v1'
                 and profile['limits'] == dict(guest_cycles=6000000, host_seconds=7200, raw_file_bytes=536870912, concurrent_emu=2)
                 and profile['original_limits'] == dict(guest_cycles=4000000, host_seconds=3600), 'separate fixed resource contract')
            for path_key, sha_key in (('entry_path', 'entry_sha256'), ('resource_contract_path', 'resource_contract_sha256')):
                relative = Path(profile[path_key]).relative_to(Path(info['original_repo']))
                need(sha(source / relative) == profile[sha_key], 'resource source identity')
            state = read(root / campaign / 'state.json')
            need(state['resource_contract_sha256'] == sha(root / campaign / 'resource-contract.json'), 'starting profile bound to terminal state')
            need(profile['operation_id'] == state['operation_id'] and
                 state['resource_contract'] == profile['resource_contract'] and
                 state['validation_contract'] == profile['validation_contract'], 'same budget campaign identity')
            need(profile['original_runner_sha256'] == module.BASE_RUN_SHA256 and
                 profile['original_contract_sha256'] == module.BASE_CONTRACT_SHA256, 'original frozen contract identities')
            need(all(profile[key] is False for key in ('workload_changed', 'runtime_log_profile_changed',
                 'numerical_or_performance_rules_changed', 'old_failed_campaign_reclassified')), 'no unregistered semantic change')
            need(all(profile['arguments'][key] == str(original_roots[label]) for key, label in
                 (('build', 'build'), ('reference', 'reference'), ('output', 'target-budget2'))),
                 'profile names this exact archived experiment')
            module = module.load_base()
            extras['resource_contract'] = profile
        need(module.REPO == source, 'target validator uses only its frozen repository')
        gates = tuple(load('frozen_norm_gate_' + str(index), source / rel) for index, rel in enumerate(GATES))
        build_dir = root / 'build'; record, bound = bind_build(root, campaign, 'build')
        extras['historical_input_files_bound'] = bound
        cfg = read(root / campaign / 'configuration.json'); state = closed(root / campaign)
        runtime = read(root / campaign / 'runtime-inputs.json')
        need((state['max_cycles'], state['external_timeout_seconds']) == (module.MAX_CYCLES, module.TIMEOUT),
             'historical campaign and frozen validation resource ceilings agree')
        for label in ('negative', 'normal', 'replay'):
            src = root / campaign / 'runs' / label; receipt = read(src / 'result.json')
            target_command(receipt, cfg, record, original_roots['build'],
                           original_roots[campaign] / 'runs' / label, runtime, module.MAX_CYCLES)
            need(receipt['raw_sha256'] == {name: sha(src / name) for name in ('stdout.log', 'stderr.log')},
                 'exact original raw target hashes')
            need(receipt.get('direct_child_reaped') is True and receipt.get('process_group_absent_after_exit') is True
                 and not receipt.get('residual_process_group'), 'owned historical child cleanup closed')
            dest = output / label; dest.mkdir()
            for name in ('stdout.log', 'stderr.log'):
                shutil.copyfile(src / name, dest / name)
            mapped = copy.deepcopy(receipt)
            mapped['command'][2] = str(build_dir / ('negative.bin' if label == 'negative' else 'real-norm.bin'))
            if not budget and label != 'negative':
                need(state['status'] == 'FAILED' and receipt['exit_code'] == -9, 'original timeout remains failed')
                try:
                    module.validate(dest, record, build_dir, 0, mapped, cfg, gates)
                except ValueError as error:
                    need(str(error) == 'complete expected EMU process', 'original failed process is rejected by original gate')
                else:
                    raise ValueError('incomplete original normal must not acquire qualification')
                samples = re.findall(r'^NORM_SAMPLE (\d+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]{16})$',
                                     (src / 'stdout.log').read_text(), re.M)
                scalar = [int(row[2]) for row in samples if row[1] == '0']
                checks[label] = dict(status='ORIGINAL_FAILED_PROCESS_STILL_REJECTED', partial_stdout_samples=samples,
                                     scalar_span_lower_bound=max(scalar) / min(scalar) - 1 if len(scalar) >= 2 else None,
                                     complete_target_qualified=False, timed_out=receipt.get('timed_out', False))
                continue
            actual = module.validate(dest, record, build_dir, int(label == 'negative'), mapped, cfg, gates)
            need(actual == read(src / 'validation.json'), 'complete frozen norm target validator replay')
            for name in ('counter-audit.json', 'protocol.json', 'uart.txt', 'counter-source.txt'):
                need((dest / name).read_bytes() == (src / name).read_bytes(), 'derived target audit bytes exactly replay')
            checks[label] = actual
        if budget:
            results = read(root / campaign / 'results.json')
            need(checks['normal'] == checks['replay'] == results['validation'], 'independent target replay equals complete original summary')
            decision = module.performance(checks['normal'])
            need(decision == read(root / campaign / 'performance.json') == results['performance'],
                 'performance decision recomputed with unchanged original thresholds')
            need(state['performance_qualified'] == results['stage_performance_qualified'] ==
                 decision['candidate_performance_qualified'] and results['full_forward_performance_qualified'] is False,
                 'all reported qualification fields agree with the recomputed decision')
            extras['performance'] = decision
        owner.base_for_import_audit = module
        for index, gate in enumerate(gates):
            setattr(owner, 'gate_for_import_audit_' + str(index), gate)
        module = owner
    elif campaign == 'consumer-reference':
        module, source, info = frozen(root, campaign, 'consumer/run.py')
        need(module.b.REPO == source, 'consumer validator uses only its frozen repository')
        _, bound = bind_build(root, campaign, 'consumer-build')
        extras['historical_input_files_bound'] = bound
        build = root / 'consumer-build'; original = read(root / campaign / 'results.json')
        runtime = read(root / campaign / 'runtime-inputs.json')
        need(original['contract'] == module.b.CONTRACT and original['status'] == module.b.PASS, 'new consumer contract')
        for label, method, negative in module.CASES:
            dest = root / campaign / label; receipt = read(dest / 'result.json')
            reference_command(receipt, runtime, build / 'dump-plan.txt', original_roots['consumer-build'],
                              original_roots[campaign] / label, module.w.MAX_CALLS, 600)
            actual = module.validate(build, dest, method, negative, receipt)
            need(actual == original['validations'][label] == read(dest / 'validation.json'), 'complete new consumer state recheck')
            checks[label] = actual
        need(checks['ta-cache'] == checks['recovery'] == checks['replay'], 'complete new consumer recovery/replay')
        need(all(checks[name]['flags'] == checks['scalar']['flags'] for name in ('fr', 'ta', 'fr-cache', 'ta-cache')),
             'five methods retain scalar flags')
    elif campaign == 'api-reference':
        module, source, info = frozen(root, campaign, 'consumer/api.py')
        need(module.b.REPO == source, 'API validator uses only its frozen repository')
        build = root / 'api-build'; record, bound = bind_build(root, campaign, 'api-build')
        extras['historical_input_files_bound'] = bound
        original = read(root / campaign / 'results.json'); dest = root / campaign / 'api'
        receipt = read(dest / 'result.json'); runtime = read(root / campaign / 'runtime-inputs.json')
        reference_command(receipt, runtime, build / 'dump-plan.txt', original_roots['api-build'],
                          original_roots[campaign] / 'api', module.r.w.MAX_CALLS, 600)
        need(record['qualified_consumer_object_sha256'] == read(root / 'consumer-build/result.json')['artifacts'][module.b.CORE],
             'API uses the same whole qualified object')
        need(record['qualified_campaign'] == descriptor['roots']['consumer-reference'] and
             record['qualified_build'] == descriptor['roots']['consumer-build'], 'original API qualification paths')
        for name in ('results.json', 'state.json', 'runtime-inputs.json'):
            need(runtime.get(str(Path(record['qualified_campaign']) / name)) == sha(root / 'consumer-reference' / name),
                 'same historical parent qualification before in-memory path mapping')
        record = copy.deepcopy(record); record['qualified_campaign'] = str(root / 'consumer-reference')
        actual = module.validate(build, dest, record, receipt)
        need(actual == original['validation'] == read(dest / 'validation.json'), 'complete guarded API recheck')
        _, proof = module.validator()
        need(proof == original['validator_derivation'] == read(root / campaign / 'validator-derivation.json'),
             'exact mechanically derived API identity binding')
        checks['api'] = actual
    else:
        raise ValueError('unknown campaign')
    source_files = imports(module, source, info, root)
    result = dict(status='FROZEN_NORM_EVIDENCE_RECHECK_PASS', campaign=campaign, checks=checks,
                  imported_source_files=source_files, extra=extras, seconds=time.monotonic() - began,
                  new_reference_runs=0, new_emu_runs=0, physical_runtime_identity_rechecked=False)
    save(output / 'result.json', result)
    return result


def recheck(args):
    root, output = args.root.resolve(), args.output.resolve()
    need(not output.exists() and not output.is_relative_to(root), 'fresh audit outside restored originals')
    need(sha(args.manifest) == args.expected_manifest_sha256, 'published exact manifest identity')
    manifest = read(args.manifest)
    expected = {row['path']: dict(size=row['size'], sha256=row['sha256']) for row in manifest['files']}
    before = inventory(root)
    need(before == expected, 'complete restored file membership and byte identity before audit')
    output.mkdir(parents=True); started = time.monotonic()
    descriptor = read(root / 'metadata/descriptor.json'); results = {}
    campaigns = descriptor['campaigns']
    need(len(campaigns) == len(set(campaigns)) and {'reference', 'target-original', 'target-budget2'} <= set(campaigns)
         and set(campaigns) <= {'reference', 'target-original', 'target-budget2', 'consumer-reference', 'api-reference'}
         and ('api-reference' not in campaigns or 'consumer-reference' in campaigns), 'complete explicit campaign inventory')
    for rel, value in descriptor['tool_files'].items():
        need(sha(root / 'metadata/tool-source' / rel) == value, 'published offline tool source identity')
    need(descriptor['tool_files'][str(NORM_REL / 'evidence.py')] == sha(__file__), 'same published offline auditor')
    for campaign in descriptor['campaigns']:
        argv = [sys.executable, '-B', str(Path(__file__).resolve()), 'worker', '--root', str(root),
                '--campaign', campaign, '--output', str(output / campaign)]
        with (output / (campaign + '.stdout.log')).open('wb') as stdout, (output / (campaign + '.stderr.log')).open('wb') as stderr:
            proc = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=900)
        need(proc.returncode == 0, 'fresh frozen-validator audit process: ' + campaign)
        results[campaign] = read(output / campaign / 'result.json')
    need(inventory(root) == before, 'all restored original bytes unchanged after audit')
    report = dict(status='NORM_ARCHIVE_RAW_RECHECK_PASS', manifest_sha256=sha(args.manifest),
                  file_count=len(before), original_bytes=sum(value['size'] for value in before.values()),
                  campaigns={key: dict(status=value['status'], cases=list(value['checks']),
                                       imported_sources=len(value['imported_source_files'])) for key, value in results.items()},
                  original_failed_target_preserved=True, performance=results['target-budget2']['extra']['performance'],
                  seconds=time.monotonic() - started, new_reference_runs=0, new_emu_runs=0,
                  physical_runtime_identity_rechecked=False, full_forward_performance_qualified=False)
    save(output / 'result.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='action', required=True)
    p = commands.add_parser('seal')
    for name in ('repo', 'build', 'reference', 'target-original', 'target-budget2', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('consumer-build', 'consumer-reference', 'api-build', 'api-reference'):
        p.add_argument('--' + name, type=Path)
    p.add_argument('--extra', action='append', default=[])
    p = commands.add_parser('recheck')
    for name in ('root', 'manifest', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--expected-manifest-sha256', required=True)
    p = commands.add_parser('worker')
    for name in ('root', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--campaign', required=True)
    args = parser.parse_args()
    result = seal(args) if args.action == 'seal' else recheck(args) if args.action == 'recheck' else worker(args.root.resolve(), args.campaign, args.output.resolve())
    print(json.dumps({key: result[key] for key in ('status',) if key in result}, indent=2))
