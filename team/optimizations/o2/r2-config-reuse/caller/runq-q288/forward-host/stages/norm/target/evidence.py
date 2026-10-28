"""Seal and recheck first-token evidence using its historical source closures."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

e = load('norm_evidence_primitives', HERE.parent / 'evidence.py')
t = load('first_token_streaming_transport', HERE / 'transport.py')
need, read, save, sha = e.need, e.read, e.save, e.sha
REL = e.NORM_REL / 'target'
CONTRACT = 'r2-s3-w2-norm-first-token-v1'
PASS = 'NORM_W2_FIRST_TOKEN_TARGET_CAMPAIGN_PASS'
CASES = [('negative', 4, True), ('fr', 3, False), ('ta', 4, False), ('replay', 4, False)]


def tool_identity(root, descriptor):
    checkout = Path(__file__).resolve()
    for part in reversed((REL / 'evidence.py').parts):
        need(checkout.name == part, 'offline tools retain their complete published repository-relative paths')
        checkout = checkout.parent
    for path in (Path(__file__).resolve(), Path(e.__file__).resolve(), Path(t.__file__).resolve(), Path(t.old.__file__).resolve()):
        need(path.is_relative_to(checkout), 'all actually loaded offline helpers use this published tool tree')
        rel = path.relative_to(checkout).as_posix()
        need(descriptor['tool_files'].get(rel) == sha(path) == sha(root / 'metadata/tool-source' / rel),
             'actual offline helper equals its sealed source: ' + rel)


def bind_norm_baseline(root, campaign):
    """Bind the indirect norm baseline without inventing direct snapshot inputs."""
    descriptor = read(root / 'metadata/descriptor.json')
    original = Path(descriptor['roots']['norm-build']); repo = Path(descriptor['original_repo'])
    restored = root / 'norm-build'; record = read(restored / 'result.json')
    runtime = read(root / campaign / 'runtime-inputs.json'); count = 0
    for name in ('result.json', 'tools.json'):
        need(runtime.get(str(original / name)) == sha(restored / name), 'historical norm baseline metadata')
        count += 1
    for group, suffix in (('artifacts', ''), ('fixtures', 'fixture'), ('actual_source_pins', 'source')):
        for name, value in record[group].items():
            need(runtime.get(str(original / suffix / name)) == value == sha(restored / suffix / name),
                 'historically consumed norm baseline member: ' + name)
            count += 1
    for rel, value in record['source_pins'].items():
        need(runtime.get(str(repo / rel)) == value == sha(restored / 'source/repo' / rel) ==
             sha(root / 'closures' / campaign / 'repo' / rel), 'same frozen norm source and baseline snapshot: ' + rel)
        count += 1
    for name, value in record['external_pins'].items():
        need(runtime.get(name) == value, 'same historical norm external dependency')
        count += 1
    return count


def parent_qualification(record, parent):
    """Connect this harness to the exact eight-case qualification already audited."""
    files = {row['path']: row['sha256'] for row in parent['files']}
    pairs = [('consumer-build/result.json', str(Path(record['qualified_build']) / 'result.json'))]
    pairs += [('consumer-reference/' + name, str(Path(record['qualified_campaign']) / name))
              for name in ('results.json', 'state.json', 'runtime-inputs.json')]
    for archived, original in pairs:
        need(record['external_pins'].get(original) == files[archived], 'same sealed parent qualification input: ' + archived)


def profile_identity(roots, originals, original_repo):
    """Bind the optional reference diagnostic without changing target qualification."""
    if 'profile' not in roots:
        return {}
    profile = roots['profile']; state, summary = e.closed(profile), read(profile / 'results.json')
    need(state['contract'] == summary['contract'] == 'r2-s3-first-token-reference-pc-profile-v1' and
         state['status'] == summary['status'] == 'FIRST_TOKEN_REFERENCE_PROFILE_PASS' and
         state['reference_runs'] == summary['reference_runs'] == 2 and
         state['new_emu_runs'] == summary['new_emu_runs'] == 0 and
         state['performance_qualified'] is False and summary['performance_qualified'] is False,
         'closed two-case reference-only diagnostic')
    for name in ('build', 'reference', 'profile'):
        need(state['original_' + name] == str(originals[name]), 'same original diagnostic root: ' + name)
    need(state['configuration'] == read(roots['reference'] / 'parent-identity.json')['configuration'] and
         read(roots['build'] / 'result.json')['norm_build'] == str(originals['norm-build']),
         'same qualified reference configuration and indirect norm baseline')
    runtime = read(profile / 'runtime-inputs.json'); prior = read(roots['reference'] / 'runtime-inputs.json')
    need(all(runtime.get(path) == value for path, value in prior.items()), 'same complete historical reference shared inputs')
    pins = read(profile / 'closure/pins.json'); source = profile / 'closure/repo'
    expected = {Path(path).relative_to(original_repo).as_posix(): value for path, value in runtime.items()
                if Path(path).is_relative_to(original_repo)}
    need(pins['original_repo'] == str(original_repo) and pins['files'] == expected and
         not pins['supplemental_pins'] and pins['runtime_inputs_sha256'] == sha(profile / 'runtime-inputs.json'),
         'exact diagnostic historical source closure membership')
    for rel, value in expected.items():
        need(sha(source / rel) == value, 'every diagnostic helper matches before executing its frozen entry')
    for name, key in (('profile.py', 'source_sha256'), ('reference.py', 'reference_validator_sha256')):
        rel = (REL / name).as_posix()
        need(summary[key] == expected[rel] == sha(source / rel), 'same frozen diagnostic entry or reference validator')
    need(summary['reference_validator_sha256'] == prior[str(original_repo / REL / 'reference.py')],
         'diagnostic uses the independently audited original reference validator')
    return dict(contract=state['contract'], status=state['status'], source_sha256=summary['source_sha256'],
        reference_validator_sha256=summary['reference_validator_sha256'], historical_reference_runs=2,
        new_reference_runs=0, new_emu_runs=0, performance_qualified=False)


def seal(args):
    repo, output = args.repo.resolve(), args.output.resolve()
    roots = {name: getattr(args, name.replace('-', '_')).resolve() for name in ('build', 'norm-build', 'reference', 'target')}
    for value in args.extra:
        label, path = value.split('=', 1); t.safe(label)
        need('/' not in label and label not in roots and label not in ('metadata', 'closures'), 'unique extra evidence root')
        roots[label] = Path(path).resolve()
    need(not output.exists() and not any(output.is_relative_to(p) for p in (repo, *roots.values())), 'fresh archive work outside all inputs')
    refstate, targetstate = e.closed(roots['reference']), e.closed(roots['target'])
    need(refstate['contract'] == CONTRACT and refstate['status'] == 'NORM_W2_FIRST_TOKEN_REFERENCE_CAMPAIGN_PASS', 'closed exact reference qualification')
    need(targetstate['contract'] == CONTRACT and targetstate['status'] in (PASS, 'FAILED_OR_PARTIAL') and
         not targetstate.get('launch_state_unknown'), 'closed target ownership; failure remains failure')
    diagnostic = profile_identity(roots, roots, repo)
    output.mkdir(parents=True); meta, closures = output / 'metadata', output / 'closures'; meta.mkdir(); closures.mkdir()
    for campaign in ('reference', 'target'):
        e.closure(roots[campaign], repo, closures / campaign, [roots['build'], roots['norm-build']])
    profile = read(roots['target'] / 'resource-contract.json'); runtime = read(roots['target'] / 'runtime-inputs.json')
    extra = set(runtime) - set(profile['input_files'])
    need(len(extra) == 1 and all(runtime[name] == value for name, value in profile['input_files'].items()), 'only original profile supplements frozen inputs')
    profile_path = Path(next(iter(extra)))
    need(sha(profile_path) == runtime[str(profile_path)] == sha(roots['target'] / 'resource-contract.json'), 'unchanged original profile and run copy')
    shutil.copyfile(profile_path, meta / 'original-resource-contract.json')
    parent = args.parent_evidence.resolve()
    parent_manifest = read(parent / 'archive/manifest.json'); parent_audit = read(parent / 'audit/result.json')
    parent_transport = read(parent / 'archive/verification.json')
    need(parent_audit['status'] == 'NORM_ARCHIVE_RAW_RECHECK_PASS' and parent_audit['manifest_sha256'] == sha(parent / 'archive/manifest.json') and
         parent_transport['status'] == 'ARCHIVE_BYTES_PASS' and parent_transport['archive_sha256'] == sha(parent / 'archive/payload.zip'),
         'actual sealed and raw-rechecked parent evidence')
    core = next(row for row in parent_manifest['files'] if row['path'] == 'consumer-build/consumer-w2-norm.o')
    need(core['sha256'] == sha(roots['build'] / 'consumer-w2-norm.o'), 'same actual parent-qualified core bytes')
    parent_qualification(read(roots['build'] / 'result.json'), parent_manifest)
    for name, source in (('parent-manifest.json', parent / 'archive/manifest.json'),
                         ('parent-transport.json', parent / 'archive/verification.json'),
                         ('parent-raw-recheck.json', parent / 'audit/result.json')):
        shutil.copyfile(source, meta / name)
    tools = {}
    for source in (Path(__file__).resolve(), HERE / 'transport.py', HERE.parent / 'evidence.py',
                   HERE.parents[1] / 'archive.py', HERE.parents[1] / 'restore.py'):
        rel = source.relative_to(repo); dest = meta / 'tool-source' / rel; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest); tools[rel.as_posix()] = sha(dest)
    save(meta / 'descriptor.json', dict(format='first-token-evidence-v1', original_repo=str(repo),
        roots={name: str(path) for name, path in roots.items()}, campaigns=['reference', 'target'], tool_files=tools,
        diagnostics={'profile': diagnostic} if diagnostic else {},
        original_profile_path=str(profile_path), target_status=targetstate['status'], parent_archive_sha256=parent_transport['archive_sha256'],
        parent_manifest_sha256=sha(parent / 'archive/manifest.json'), parent_core_sha256=core['sha256'],
        new_reference_runs=0, new_emu_runs=0, performance_qualified=False))
    return t.seal([*(name + '=' + str(path) for name, path in roots.items()), 'metadata=' + str(meta), 'closures=' + str(closures)], output / 'archive')


def receipts(root, campaign):
    path = root / campaign; state = e.closed(path); target = campaign == 'target'
    need(not state.get('launch_state_unknown') and state['contract'] == CONTRACT, 'complete unambiguous historical campaign')
    need({p.parent.name for p in path.glob('*/result.json')} == {name for name, _, _ in CASES}, 'exact case inventory')
    records = {}
    for name, method, negative in CASES:
        rec = read(path / name / 'result.json')
        need(rec['contract'] == CONTRACT and rec['name'] == name and rec['method'] == method and rec['negative'] == negative and
             rec.get('process_started') is True and rec.get('direct_child_reaped') is True and
             rec.get('process_group_absent_after_exit') is True and not rec.get('residual_process_group') and
             type(rec.get('pid')) is int and rec['pid'] > 0 and rec['process_group'] == rec['pid'] and rec.get('finished'),
             'complete exact historical owned process')
        records[name] = rec
        if (path / name / 'validation.json').is_file():
            if rec.get('validation_sha256') is not None or rec['status'] != 'FAILED_OR_PARTIAL':
                need(rec.get('validation_sha256') == sha(path / name / 'validation.json'), 'case validation receipt bound')
            # A failed case may have written a derived validation before the
            # final immutable-input check failed. Preserve it without adopting it.
    need(len({r['pid'] for r in records.values()}) == 4, 'four independent historical processes')
    need(state.get('new_emu_runs' if target else 'reference_runs') == 4, 'complete actual process count')
    aggregates = [state['records']]
    if (path / 'results.json').is_file():
        summary = read(path / 'results.json')
        need(summary['contract'] == CONTRACT and summary['status'] == state['status'], 'same terminal campaign summary')
        aggregates.append(summary['records'])
    for group in aggregates:
        need(len({r['name'] for r in group}) == len(group) and {r['name'] for r in group} <= set(records), 'unique known aggregate receipts')
        if not target or state['status'] == PASS: need(len(group) == 4, 'complete successful aggregate inventory')
        for rec in group: need(rec == records[rec['name']], 'aggregate equals final actual case receipt')
    if target:
        for owner in state['launcher_receipts']:
            rec = records[owner['case']]
            need(owner['cleanup_verified'] and owner['reference_pid'] == rec['pid'] and owner['reference_group'] == rec['pid'] and
                 owner['reference_group_present'] is False and owner['launcher_group_present'] is False and owner['receipt_cleanup_verified'],
                 'launcher exit is backed by actual EMU group closure')
        if state['status'] == PASS:
            need(state['completed'] and set(state['completed']) == set(records) and len(state['launcher_receipts']) == 4 and
                 {x['case'] for x in state['launcher_receipts']} == set(records) and all(x['launcher_exit_code'] == 0 for x in state['launcher_receipts']),
                 'all four successful launcher audits completed')
    return state, records


def bind_case(root, campaign, name, runtime, original):
    dest, old_dest = root / campaign / name, original / name
    files = read(dest / 'runtime-inputs.json'); expected = dict(runtime)
    for filename in ('image.bin', 'image-control.json'): expected[str(old_dest / filename)] = sha(dest / filename)
    if campaign == 'target':
        cfg = read(dest / 'configuration.json')
        auxiliaries = dest / 'cwd/build'
        need({p.name for p in auxiliaries.iterdir()} == {'constantin.txt', 'plusArgs'}, 'exact isolated original runtime auxiliary files')
        for path in auxiliaries.iterdir():
            value = sha(path); need(runtime[str(Path(cfg['hardware_source']) / 'build' / path.name)] == value, 'exact original runtime auxiliary bytes')
            expected[str(old_dest / 'cwd/build' / path.name)] = value
    need(files == expected, 'each case has exact shared inputs plus only its declared image/control/auxiliary files')
    return files


def worker(root, campaign, output):
    need(not output.exists() and campaign in ('reference', 'target'), 'fresh selected offline worker output')
    output.mkdir(parents=True); started = time.monotonic()
    descriptor = read(root / 'metadata/descriptor.json'); originals = {k: Path(v) for k, v in descriptor['roots'].items()}
    tool_identity(root, descriptor)
    module, source, info = e.frozen(root, campaign, 'target/reference.py' if campaign == 'reference' else 'target/run.py')
    b = module.b; need(b.REPO == source, 'all actual validator modules rooted in historical source closure')
    record, bound = e.bind_build(root, campaign, 'build')
    norm_bound = bind_norm_baseline(root, campaign)
    patched = copy.deepcopy(record); patched['norm_build'] = str(root / 'norm-build')
    _, inspection = b.inspect(root / 'build', patched); inspection = json.loads(json.dumps(inspection))
    need(all(record[key] == value for key, value in inspection.items()), 'actual restored final ELF/static/TLS/trap/kernel/norm inspection')
    need(record['qualified_consumer_object_sha256'] == sha(root / 'build' / b.CORE) == descriptor['parent_core_sha256'] and
         record.get('exact_flags_guard') == 1, 'same complete qualified object and precise flags gate')
    state, cases = receipts(root, campaign); runtime = read(root / campaign / 'runtime-inputs.json')
    checks = {}; failed = {}; shared = read(root / campaign / 'results.json') if (root / campaign / 'results.json').is_file() else None
    profile = None
    if campaign == 'reference':
        need(state['status'] == b.REFERENCE_PASS, 'exact reference campaign qualification')
    else:
        profile = read(root / 'target/resource-contract.json')
        need(profile == read(root / 'metadata/original-resource-contract.json') and
             runtime == {**profile['input_files'], descriptor['original_profile_path']: sha(root / 'target/resource-contract.json')},
             'original resource receipt and exact shared input closure')
        need(profile['contract'] == module.PROFILE and profile['workload_contract'] == CONTRACT and
             profile['max_cycles'] == module.MAX_CYCLES == 40000000 and
             profile['external_timeout_seconds'] == module.TIMEOUT == 28800 and
             profile['max_output_file_bytes'] == module.RAW_LIMIT == 4294967296 and
             profile['cases'] == [list(case) for case in CASES] and profile['automatic_budget_extension'] is False and
             profile['performance_qualified'] is False, 'one explicit unchanged resource/workload contract')
        need(profile['paths']['build'] == str(originals['build']) and profile['paths']['reference'] == str(originals['reference']) and
             profile['paths']['output'] == str(originals['target']) and state['operation_id'] == profile['operation_id'], 'profile names these exact original roots')
    for name, method, negative in CASES:
        dest = root / campaign / name; rec = cases[name]; old_dest = originals[campaign] / name
        files = bind_case(root, campaign, name, runtime, originals[campaign])
        if campaign == 'reference':
            e.reference_command(rec, runtime, root / 'build/dump-plan.txt', originals['build'], old_dest, 100000000, 600)
            actual = module.validate(root / 'build', dest, record, rec, method, negative)
        else:
            cfg = read(dest / 'configuration.json')
            need(cfg == profile['configuration'] and read(dest / 'hardware-profile.json') == profile['hardware_profile'] and
                 read(dest / 'parent-identity.json') == profile['physical_identity'], 'saved exact actual runtime identity')
            need(rec['cwd'] == str(old_dest / 'cwd') and rec['command'] == [str(Path(cfg['hardware_source']) / 'build/emu'), '-i',
                str(old_dest / 'image.bin'), '--flash=' + cfg['flash'], '--ram-size=128MB', '--diff=' + cfg['reference'],
                '--max-cycles=40000000', '--seed=1', '--log-end=0'] and files[rec['command'][2]] == rec['image_sha256'], 'exact historical target invocation')
            need(len(rec['cpu_affinity']) == 1 and rec['cpu_affinity'][0] in profile['cpu_slots'], 'actual declared single CPU')
            # Validate the historical command first. Only redirect the actual
            # image access in an in-memory receipt copy; archived bytes stay fixed.
            mapped = copy.deepcopy(rec); mapped['command'][2] = str(dest / 'image.bin')
            if rec['status'] not in ('EXPECTED_FIRST_TOKEN_TARGET_REJECTION', 'FIRST_TOKEN_TARGET_DIFFTEST_PASS'):
                need(state['status'] == 'FAILED_OR_PARTIAL' and rec['status'] == 'FAILED_OR_PARTIAL', 'failed process remains failed')
                logs = [dest / n for n in ('stdout.log', 'stderr.log')]
                need(rec['raw_sha256'] == {p.name: sha(p) for p in logs} and rec['raw_bytes'] == {p.name: p.stat().st_size for p in logs},
                     'all raw failed bytes retained without qualification')
                failed[name] = dict(status=rec['status'], error=rec.get('error'), exit_code=rec['exit_code'],
                    raw_bytes=rec['raw_bytes'], raw_sha256=rec['raw_sha256'], target_correctness_qualified=False)
                continue
            actual = module.a.validate(dest, root / 'build', record, mapped, cfg, profile, output / name)
            need(e.inventory(output / name) == e.inventory(dest / 'audit'), 'every raw-derived audit artifact recomputed exactly')
        need(actual == read(dest / 'validation.json') and rec['status'] == actual['status'], 'actual raw validation equals bound receipt')
        if shared is not None: need(actual == shared['validations'][name], 'same campaign aggregate validation')
        checks[name] = actual
    replay_equal = checks.get('ta') == checks.get('replay') if 'ta' in checks and 'replay' in checks else None
    qualified = state['status'] == (PASS if campaign == 'target' else b.REFERENCE_PASS)
    if qualified: need(not failed and replay_equal is True, 'independent complete raw architecture/counter/protocol replay')
    else: need(campaign == 'target' and state['status'] == 'FAILED_OR_PARTIAL', 'failed campaign remains unqualified')
    imported = e.imports(module, source, info, root)
    if campaign == 'target':
        for gate in module.a.gates(): imported.update(e.imports(gate, source, info, root))
    report = dict(status='FIRST_TOKEN_FROZEN_RAW_RECHECK_PASS' if qualified else 'FIRST_TOKEN_CLOSED_PARTIAL_EVIDENCE_PRESERVED',
        campaign=campaign, checks=checks, failed_cases=failed, historical_status=state['status'], imported_source_files=imported,
        historical_error=state.get('error'), replay_equal=replay_equal,
        historically_bound_files=bound + norm_bound, elapsed_seconds=time.monotonic() - started,
        new_reference_runs=0, new_emu_runs=0, physical_runtime_identity_rechecked=False, performance_qualified=False)
    save(output / 'result.json', report)
    return report


def recheck(args):
    root, output = args.root.resolve(), args.output.resolve()
    need(not output.exists() and not output.is_relative_to(root), 'fresh audit output outside restored originals')
    need(sha(args.manifest) == args.expected_manifest_sha256, 'published exact manifest identity')
    manifest = read(args.manifest); expected = {row['path']: dict(size=row['size'], sha256=row['sha256']) for row in manifest['files']}
    before = e.inventory(root); need(before == expected, 'all restored bytes and complete membership before raw audit')
    descriptor = read(root / 'metadata/descriptor.json')
    need(descriptor['format'] == 'first-token-evidence-v1' and descriptor['campaigns'] == ['reference', 'target'], 'exact new evidence schema')
    for rel, value in descriptor['tool_files'].items(): need(sha(root / 'metadata/tool-source' / rel) == value, 'all published offline tools exact')
    tool_identity(root, descriptor)
    parent = read(root / 'metadata/parent-manifest.json'); parent_audit = read(root / 'metadata/parent-raw-recheck.json')
    parent_qualification(read(root / 'build/result.json'), parent)
    need(sha(root / 'metadata/parent-manifest.json') == descriptor['parent_manifest_sha256'] == parent_audit['manifest_sha256'] and
         parent_audit['status'] == 'NORM_ARCHIVE_RAW_RECHECK_PASS' and
         read(root / 'metadata/parent-transport.json')['archive_sha256'] == descriptor['parent_archive_sha256'] and
         next(row['sha256'] for row in parent['files'] if row['path'] == 'consumer-build/consumer-w2-norm.o') == descriptor['parent_core_sha256'],
         'explicit sealed parent provenance and exact shared core; parent raw not rerun here')
    output.mkdir(parents=True); began = time.monotonic(); reports = {}
    for campaign in ('reference', 'target'):
        argv = [sys.executable, '-B', str(Path(__file__).resolve()), 'worker', '--root', str(root), '--campaign', campaign, '--output', str(output / campaign)]
        with (output / (campaign + '.stdout.log')).open('wb') as stdout, (output / (campaign + '.stderr.log')).open('wb') as stderr:
            proc = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=7200)
        need(proc.returncode == 0, 'fresh historical-validator process: ' + campaign)
        reports[campaign] = read(output / campaign / 'result.json')
    diagnostics = {}; originals = {name: Path(path) for name, path in descriptor['roots'].items()}
    roots = {name: root / name for name in originals}
    diagnostic = profile_identity(roots, originals, Path(descriptor['original_repo']))
    need(descriptor.get('diagnostics', {}) == ({'profile': diagnostic} if diagnostic else {}),
         'all declared diagnostics exactly match their historical qualification')
    if diagnostic:
        _, bound = e.bind_build(root, 'profile', 'build')
        entry = root / 'profile/closure/repo' / REL / 'profile.py'
        argv = [sys.executable, '-B', str(entry), 'recheck', '--build', str(root / 'build'),
                '--reference', str(root / 'reference'), '--profile', str(root / 'profile'), '--output', str(output / 'profile')]
        with (output / 'profile.stdout.log').open('wb') as stdout, (output / 'profile.stderr.log').open('wb') as stderr:
            proc = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=7200)
        need(proc.returncode == 0, 'fresh historical reference-profile raw recheck')
        checked = read(output / 'profile/result.json')
        need(checked['status'] == 'FROZEN_REFERENCE_PROFILE_RECHECK_PASS' and
             checked['new_reference_runs'] == checked['new_emu_runs'] == 0 and checked['performance_qualified'] is False,
             'complete raw reference diagnostic remains reference-only')
        diagnostics['profile'] = dict(status=checked['status'], historically_bound_files=bound,
            cases=list(checked['checks']), performance_qualified=False)
    need(e.inventory(root) == before, 'every restored original file unchanged after raw audit')
    qualified = reports['target']['historical_status'] == PASS and not reports['target']['failed_cases']
    report = dict(status='FIRST_TOKEN_ARCHIVE_RAW_RECHECK_PASS' if qualified else 'FIRST_TOKEN_PARTIAL_ARCHIVE_PRESERVED',
        manifest_sha256=sha(args.manifest), file_count=len(before), original_bytes=sum(r['size'] for r in before.values()),
        campaigns={name: dict(status=v['status'], cases=list(v['checks']), failed_cases=list(v['failed_cases'])) for name, v in reports.items()},
        diagnostics=diagnostics,
        target_correctness_qualified=qualified, parent_archive_sha256=descriptor['parent_archive_sha256'],
        parent_raw_rechecked_in_this_package=False, seconds=time.monotonic() - began,
        new_reference_runs=0, new_emu_runs=0, physical_runtime_identity_rechecked=False,
        performance_qualified=False, full_retirement_window_audited=False)
    save(output / 'result.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('seal')
    for name in ('repo', 'build', 'norm-build', 'reference', 'target', 'parent-evidence', 'output'): p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--extra', action='append', default=[])
    p = sub.add_parser('recheck')
    for name in ('root', 'manifest', 'output'): p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--expected-manifest-sha256', required=True)
    p = sub.add_parser('worker')
    for name in ('root', 'output'): p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--campaign', choices=('reference', 'target'), required=True)
    args = parser.parse_args()
    result = seal(args) if args.action == 'seal' else recheck(args) if args.action == 'recheck' else worker(args.root.resolve(), args.campaign, args.output.resolve())
    print(json.dumps({k: result[k] for k in ('status', 'target_correctness_qualified') if k in result}, indent=2))
