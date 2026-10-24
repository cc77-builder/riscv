#!/usr/bin/env python3
"""Seal MERGE-REG evidence and replay its raw architecture checks without EMU.

The frozen controller retains the original Linux physical-input audit. This
entry preserves its bytes and never redirects or relaxes that audit. Offline
replay uses sealed inputs and explicitly does not revalidate build trees.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile

import merged_regression as m
import portable
import recheck as rawcheck
import run_suite as suite
import run_supplements as supplements
import analyze
import check_control

g = m.g
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONTROLLER = 'b082d34f9e7eed5d56296aacf4a707358cab3c370ae301bf9a4a82174af122a5'
AUDIT_PASS = 'O2_MERGED_REGRESSION_RAW_AUDIT_PASS'
ARCHIVE_PASS = 'O2_MERGED_ARCHIVE_ARCHITECTURE_TRACE_PASS'
PORTABLE_SHA = '7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b'
HELPERS = {
    'merged_screen.py': 'ff75464c5b0f75349fc4321bdd80a7a85985a54ae415ad347c3ce04fdf4bd885',
    'fullcore_screen.py': '5f5c719a9a5b675f4de166ca30a3d89bd52c944c667cee302f66da94fa2779f2',
    'linked_gate.py': '96807465bfd97a483f31ce100e552e2b83c4d0edd59f9bf4d817c66abd80ec1f',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bind():
    require(g.sha(HERE / 'merged_regression.py') == CONTROLLER, 'frozen controller changed')
    require(g.sha(HERE / 'portable.py') == PORTABLE_SHA, 'archive decoder changed')
    for name, sha in HELPERS.items():
        require(g.sha(ROOT / g.REL / name) == sha, 'frozen helper changed: ' + name)


def closed_result(state, result, audit):
    require(state['status'] == result['status'] == m.PASS and audit['status'] == AUDIT_PASS,
            'campaign or physical audit is incomplete')
    require(state['controller_sha256'] == result['controller_sha256'] == audit['controller_sha256'] == CONTROLLER,
            'controller identity differs')
    require(state['new_emu_launch_attempts'] == state['new_emu_runs'] == result['new_emu_runs'] == 2
            and audit['new_emu_runs'] == 0 and audit['source_campaign_new_emu_runs'] == 2,
            'execution count differs')
    require(state['active_result'] is None and state['active_process_group'] is None
            and state['finished'] == result['finished'], 'campaign has active or incoherent state')
    left, right = m.semantic_result(result), m.semantic_result(audit)
    for name in ('status', 'new_emu_runs'):
        left['identity'].pop(name)
        right['identity'].pop(name)
    require(left == right, 'physical audit and campaign semantic results differ')
    require(result['contract'] == m.CONTRACT and result['hardware_source'] == m.m.SOURCE
            and result['emu_sha256'] == m.m.EMU and result['negative_sha256'] == m.NEGATIVE
            and result['selected_jobs'] == 14 and result['reused_normal_jobs'] == 12
            and result['merged_baseline_acceptance'] is True and result['normal_reference_recovery'] is True
            and all(result[k] is False for k in ('historical_fixed_negative_acceptance',
                'historical_b0_h1_acceptance', 'selected_s2_combination_acceptance', 'performance_measured')),
            'contract identity or acceptance scope differs')


def retained_roots(campaign, audit):
    cfg = m.read(campaign / 'local-config.json')
    inputs = m.read(campaign / 'runtime-inputs.json')
    suffix = '/team/optimizations/o2/fullcore/merged_regression.py'
    roots = [p[:-len(suffix)] for p in inputs if p.endswith(suffix)]
    require(len(roots) == 1, 'ambiguous original software root')
    return [campaign, audit, Path(roots[0])] + [Path(cfg[k]) for k in
            ('hardware_source', 'legacy_base', 'fixture_dir')]


def pack(campaign, audit, output, support=()):
    bind()
    campaign, audit, output = (p.resolve() for p in (campaign, audit, output))
    cfg = m.read(campaign / 'local-config.json')
    state, result, audited = (m.read(p) for p in (campaign / 'state.json', campaign / 'result.json', audit / 'result.json'))
    closed_result(state, result, audited)
    require(audited['source_campaign'] == str(campaign)
            and audited['source_result_sha256'] == g.sha(campaign / 'result.json'), 'physical audit source differs')
    inputs = m.read(campaign / 'runtime-inputs.json')
    suffix = '/team/optimizations/o2/fullcore/merged_regression.py'
    source_roots = [p[:-len(suffix)] for p in inputs if p.endswith(suffix)]
    require(len(source_roots) == 1, 'ambiguous original software root')
    protected = retained_roots(campaign, audit)
    require(not output.exists() and not output.is_symlink(), 'archive output already exists')
    require(not any(output.is_relative_to(p) or p.is_relative_to(output) for p in protected),
            'archive output overlaps retained inputs')
    for item in support:
        require(item.is_file() and not item.is_symlink(), 'support must be an existing ordinary file')
        require(not item.resolve().is_relative_to(output), 'support overlaps archive output')
    m.m.verify_files(inputs)
    external = {str(PurePosixPath(cfg['hardware_source']) / 'build/emu'): m.m.EMU}
    require(all(inputs.get(k) == v for k, v in external.items()), 'missing EMU input identity')
    output.mkdir(parents=True)
    entries, originals = [], {}

    def add(raw, logical, original):
        portable.safe_relative(logical)
        if original in originals:
            require(originals[original][1] == digest(raw), 'same input changed while sealing')
            return
        target_rel = Path('files') / logical
        encoded, encoding = raw, 'identity'
        if len(raw) >= 16384 and target_rel.suffix in ('.log', '.json', '.jsonl', '.txt', '.S', '.h', '.patch'):
            target_rel = target_rel.with_name(target_rel.name + '.gz')
            encoded, encoding = gzip.compress(raw, compresslevel=6, mtime=0), 'gzip'
        target = output / target_rel
        require(not target.exists(), 'duplicate stored path')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encoded)
        entries.append(dict(original=original, stored=target_rel.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=digest(raw),
                            stored_bytes=len(encoded), stored_sha256=digest(encoded)))
        originals[original] = (logical, digest(raw))

    def add_file(path, logical):
        require(path.is_file() and not path.is_symlink(), 'missing or symbolic input: ' + str(path))
        add(path.read_bytes(), logical, str(path))

    for source, prefix in ((campaign, 'campaign'), (audit, 'physical-audit')):
        for path in sorted(source.rglob('*')):
            require(not path.is_symlink(), 'symbolic evidence input')
            if path.is_file():
                add_file(path, prefix + '/' + path.relative_to(source).as_posix())
    for number, (name, expected) in enumerate(sorted(inputs.items())):
        if name in external:
            continue
        path = Path(name)
        require(g.sha(path) == expected, 'input changed during archive export')
        add_file(path, 'inputs/%04d/%s' % (number, path.name))
    for number, path in enumerate(support):
        add_file(path.resolve(), 'support/%04d/%s' % (number, path.name))
    add_file(Path(__file__), 'exporter/merged_regression_evidence.py')
    info = dict(contract=m.CONTRACT, campaign=str(campaign), physical_audit=str(audit),
                original_software_root=source_roots[0], external_inputs=external,
                physical_audit_result_sha256=g.sha(audit / 'result.json'),
                export_tool_sha256=g.sha(__file__),
                excluded_scope='Only EMU is omitted from the recorded direct input set. Hardware dependency trees, generated RTL, NEMU source/build and system headers remain external physical provenance, not a portable rebuild closure.')
    add(json_bytes(info), 'evidence-map.json', 'generated:evidence-map')
    manifest = dict(version=1, contract=m.CONTRACT, created_utc=datetime.now(timezone.utc).isoformat(), files=entries)
    body = json_bytes(manifest)
    (output / 'archive-manifest.json').write_bytes(body)
    (output / 'archive-manifest.sha256').write_bytes((digest(body) + '  archive-manifest.json\n').encode('ascii'))
    m.m.verify_files(inputs)
    archive = portable.Archive(output)
    return dict(status='O2_MERGED_ARCHIVE_BYTES_PASS', **archive.bytes_result,
                physical_inputs_revalidated=False, architecture_replayed=False, new_emu_runs=0)


class Evidence:
    def __init__(self, path):
        self.archive = portable.Archive(path)
        require(self.archive.manifest.get('contract') == m.CONTRACT, 'wrong archive contract')
        require({p.name for p in Path(path).iterdir()} == {'files', 'archive-manifest.json', 'archive-manifest.sha256'},
                'unexpected archive root content')
        self.originals = {}
        for logical, record in self.archive.records.items():
            original = record['original']
            require(original not in self.originals, 'duplicate original identity')
            self.originals[original] = logical
        self.info = self.archive.json('evidence-map.json')
        require(digest(self.archive.raw('exporter/merged_regression_evidence.py')) == self.info['export_tool_sha256'],
                'export tool identity differs')
        self.cfg = self.archive.json('campaign/local-config.json')
        self.inputs = self.archive.json('campaign/runtime-inputs.json')
        self.external = {str(PurePosixPath(self.cfg['hardware_source']) / 'build/emu'): m.m.EMU}
        require(self.info['external_inputs'] == self.external, 'unexpected omitted physical input')
        for original, expected in self.inputs.items():
            require(self.external.get(original) == expected if original in self.external else digest(self.raw(original)) == expected,
                    'input identity missing from archive: ' + original)

    def raw(self, original):
        require(original in self.originals, 'unsealed input: ' + original)
        return self.archive.raw(self.originals[original])

    def json(self, original):
        return json.loads(self.raw(original))

    def extract(self, original, output):
        """Materialize a bounded sealed subtree in a new temporary directory."""
        prefix = original.rstrip('/') + '/'
        found = 0
        for name in self.originals:
            if not name.startswith(prefix):
                continue
            relative = name[len(prefix):]
            portable.safe_relative(relative)
            target = output / relative
            require(not target.exists(), 'duplicate extraction path')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.raw(name))
            found += 1
        require(found > 0, 'empty sealed subtree: ' + original)
        return output


def audit_provenance(e):
    chains = e.archive.json('campaign/adoption-provenance.json')
    require(set(chains) == set(m.REUSED), 'adoption selected jobs differ')
    base = PurePosixPath(e.cfg['legacy_base'])
    for name, chain in chains.items():
        expected = [m.CAMPAIGNS[2], m.CAMPAIGNS[1], m.CAMPAIGNS[0]] if name == 'hello-vadd' else (
            [m.CAMPAIGNS[2], m.CAMPAIGNS[1]] if name in ('functional-1', 'functional-2') else [m.CAMPAIGNS[2]])
        require([row['campaign'] for row in chain] == expected, 'unexpected adoption chain')
        for index, row in enumerate(chain):
            directory = str(base / row['campaign'] / name)
            require(row['directory'] == directory, 'adoption directory differs')
            files = {p[len(directory)+1:]: digest(e.raw(p)) for p in e.originals if p.startswith(directory + '/')}
            require(files == row['files'] and files, 'adoption byte inventory differs')
            if index + 1 < len(chain):
                mapping = e.json(str(base / row['campaign'] / 'adopted-jobs.json'))
                require(len({r['name'] for r in mapping}) == len(mapping), 'duplicate adoption declaration')
                item = [r for r in mapping if r['name'] == name]
                require(len(item) == 1 and item[0]['source'] == chain[index+1]['directory']
                        and item[0]['copied_to'] == directory and item[0]['new_emu_executed'] is False
                        and item[0]['result_sha256'] == files['result.json']
                        and files == chain[index+1]['files'], 'adoption link differs')
        origin = base / chain[-1]['campaign']
        state, job = e.json(str(origin / 'campaign-state.json')), e.json(str(origin / name / 'result.json'))
        if chain[-1]['campaign'] == m.CAMPAIGNS[0]:
            retired = e.json(str(origin / 'orchestration-retired.json'))
            require(retired['status'] == 'DISPATCHER_RETIRED_AFTER_FUNCTIONAL_0_RESULT'
                    and retired['completed_results_preserved'] is True
                    and retired['terminated_pending_descendants'] == [], 'retirement receipt differs')
            end = retired['finished']
        else:
            end = state['finished']
        require(m.instant(state['started']) <= m.instant(job['started']) <= m.instant(job['finished']) <= m.instant(end),
                'job outside original campaign lifetime')


def recheck_supplement(directory, e, workload):
    """Preserve POSIX reference identities on every host; frozen pure gates run unchanged."""
    record, runtime = (m.read(directory / name) for name in ('result.json', 'runtime.json'))
    spec = supplements.JOBS[record['name']]
    require(record['kind'] == spec['kind'], 'supplement kind differs')
    for key in ('kind', 'hardware_pins_sha256', 'build_source_commit', 'input_manifest_sha256',
                'archived_manifest_sha256', 'expected_vdot_commits'):
        require(record[key] == runtime[key], 'supplement runtime differs: ' + key)
    command = record['command']
    expected = ['timeout', '120m', 'stdbuf', '-o0', '-e0',
                str(PurePosixPath(e.cfg['hardware_source']) / 'build/emu'), '-i', command[7],
                '--flash=' + e.cfg['flash'], '--ram-size=128MB', '--diff=' + e.cfg['reference'], '--max-cycles=5000000']
    files = {p: e.external[p] if p in e.external else digest(e.raw(p))
             for p in (expected[5], command[7], e.cfg['flash'], e.cfg['reference'])}
    require(files[command[7]] == spec['image_sha256'], 'supplement image differs')
    rc, text = rawcheck.check_raw_job(directory, record, expected, files, None)
    manifest = m.read(directory / 'input-manifest.json')
    require(g.sha(directory / 'input-manifest.json') == record['archived_manifest_sha256'] == record['input_manifest_sha256'],
            'supplement manifest differs')
    build = m.read(directory / 'build-receipt.json')
    require(build['kind'] == spec['kind'] and build['images_sha256'][spec['image']] == spec['image_sha256'],
            'supplement build identity differs')
    observation, _, result = supplements.evaluate(text, rc, spec['kind'], manifest, e.cfg['reference'], analyze, workload)
    require(record['status'] == 'O2_SUPPLEMENT_PASS' and record['observation_status'] == observation['status']
            and record['observation_counts'] == observation['counts'] and record['workload_status'] == result['status'],
            'supplement cached verdict differs from raw replay')
    return dict(observation_status=observation['status'], observation_counts=observation['counts'],
                workload_status=result['status'], checked_register_bytes=result['checked_register_bytes'])


def audit_fixture(e):
    root = e.cfg['fixture_dir']
    record = e.json(root + '/fixture.json')
    binary, source = root + '/negative-reference.so', root + '/negative-fixture.c'
    require(record['source_sha256'] == m.m.NEGATIVE_SHA == digest(e.raw(source))
            and record['normal_reference_sha256'] == m.f.REFERENCE == digest(e.raw(e.cfg['reference']))
            and record['negative_sha256'] == m.NEGATIVE == digest(e.raw(binary))
            and record['binary'] == binary and record['historical_negative_hash_claim'] is False,
            'new fixture identity differs')
    compiler = record['command'][0]
    expected = [compiler, '-shared', '-fPIC', '-O2', '-DREF_SO="' + e.cfg['reference'] + '"',
                source, '-Wl,--no-as-needed', e.cfg['reference'], '-ldl', '-o', binary]
    require(record['command'] == expected, 'fixture compilation command differs')
    for name in ('compiler', 'compile', 'linkage'):
        step = root + '/' + name
        command = e.json(step + '/command.json')
        argv = [compiler, '--version'] if name == 'compiler' else expected if name == 'compile' else [command['command'][0], '-d', binary]
        require(command['process_started'] is True and command['exit_code'] == 0
                and not command['timed_out'] and command['command'] == argv
                and command['raw_sha256'] == {n: digest(e.raw(step + '/' + n)) for n in ('stdout.log', 'stderr.log')},
                'fixture build receipt differs: ' + name)
    require('Shared library: [' + e.cfg['reference'] + ']' in e.raw(root + '/linkage/stdout.log').decode(),
            'fixture direct dependency missing')


def audit(archive_path):
    bind()
    e = Evidence(archive_path)
    state, result, physical = (e.archive.json(n) for n in ('campaign/state.json', 'campaign/result.json', 'physical-audit/result.json'))
    closed_result(state, result, physical)
    require(physical['source_campaign'] == e.info['campaign']
            and physical['source_result_sha256'] == digest(e.archive.raw('campaign/result.json'))
            and digest(e.archive.raw('physical-audit/result.json')) == e.info['physical_audit_result_sha256'],
            'physical audit does not bind this campaign')
    pins = e.archive.json('campaign/hardware-pins.json')
    require(digest(e.archive.raw('campaign/hardware-pins.json')) == m.m.META['hardware-inputs.json']
            and pins['source_commit'] == m.m.SOURCE and pins['emu_sha256'] == m.m.EMU, 'hardware pins differ')
    # Execute only the existing checked-out team checkers, after comparison with
    # the exact live source bytes. Archived third-party code is not an input API.
    required = set(rawcheck.DRIVERS) | {'team/optimizations/o2/fullcore/recheck.py',
        'team/optimizations/o2/fullcore/run_supplements.py', 'team/optimizations/o2/fullcore/workloads/check.py',
        'team/optimizations/o2/fullcore/merged_regression.py'}
    required |= {(g.REL / name).as_posix() for name in HELPERS}
    for rel in sorted(required):
        name = e.info['original_software_root'] + '/' + rel
        require(g.sha(ROOT / rel) == e.inputs[name] == digest(e.raw(name)), 'checker changed: ' + rel)
    functional = g.load('merged_evidence_functional', ROOT / rawcheck.DRIVERS[4])
    perf = g.load('merged_evidence_perf', ROOT / rawcheck.DRIVERS[5])
    gate = g.load('merged_evidence_gate', ROOT / rawcheck.DRIVERS[6])
    workload = g.load('merged_evidence_workload', HERE / 'workloads/check.py')
    audit_provenance(e)
    audit_fixture(e)
    expected_core = m.unique_rows(result['core_records'], m.CORE)
    expected_supplements = m.unique_rows(result['supplements']['records'], m.SUPPLEMENTS)
    core, extra, raw_pair = [], [], []
    with tempfile.TemporaryDirectory(prefix='merge-reg-archive-') as temp:
        temp = Path(temp)
        for name in list(m.REUSED) + ['negative-vdot', 'functional-0']:
            original_dir = str(PurePosixPath(e.cfg['legacy_base']) / m.CAMPAIGNS[2] / name) if name in m.REUSED else e.info['campaign'] + '/runs/' + name
            directory = e.extract(original_dir, temp / 'runs' / name)
            record, expected = m.read(directory / 'result.json'), expected_core[name]
            command = record['command']
            require(len(command) == 12 and command[:5] == ['timeout', '120m', 'stdbuf', '-o0', '-e0']
                    and command[5] == str(PurePosixPath(e.cfg['hardware_source']) / 'build/emu')
                    and command[6] == '-i' and command[8:] == ['--flash=' + e.cfg['flash'], '--ram-size=128MB',
                        '--diff=' + (str(PurePosixPath(e.cfg['fixture_dir']) / 'negative-reference.so') if name == 'negative-vdot' else e.cfg['reference']),
                        '--max-cycles=5000000'], 'run command differs')
            image, reference = command[7], command[10][7:]
            files = {p: e.external[p] if p in e.external else digest(e.raw(p))
                     for p in (command[5], e.cfg['reference'], reference, e.cfg['flash'], image)}
            require(files == expected['files'], 'selected inputs differ from physical audit')
            rc, text = rawcheck.check_raw_job(directory, record, command, files, 'vdot' if name == 'negative-vdot' else None)
            rawcheck.reject_fatal_output(text)
            suite.validate_runtime(text, reference)
            negative = name == 'negative-vdot'
            row = dict(name=name, started=record['started'], finished=record['finished'], files=files, exit_code=rc)
            if negative:
                detail = gate.validate_negative(text, rc)
                stdout = gate.normalize_console((directory / 'stdout.log').read_bytes().decode())
                mismatches, aborts = list(gate.MISMATCH.finditer(stdout)), list(gate.ABORT.finditer(stdout))
                require(len(mismatches) == len(aborts) == 1 and mismatches[0].end() < aborts[0].start()
                        and not stdout[mismatches[0].end():aborts[0].start()].strip(), 'negative stdout chain differs')
                elf = g.ELF(e.raw(str(PurePosixPath(image).with_suffix('.elf'))))
                require(int.from_bytes(elf.read(int(detail['pc'], 16), 4), 'little') == int(detail['word'], 16),
                        'negative PC is not the selected ELF instruction')
                row.update(status=m.m.NEGATIVE_PASS, runtime_gate=detail)
            else:
                require(rc == 0, 'normal execution failed')
                gate.validate_failure_markers(text)
            observation = analyze.analyze(text, require_complete=not negative)
            suite.validate_observation(observation, negative=negative)
            require(observation['schema']['slots'] == 2, 'wrong O2 slot count')
            _, uart = analyze.extract_events_and_uart(text)
            if name.startswith('functional-'):
                data = str(PurePosixPath(image).parent.parent / ('data-' + name.split('-')[1]))
                extracted = e.extract(data, temp / name / 'data')
                count = m.read(extracted / 'manifest.json')['smoke_count']
                require(observation['counts'].get('COMMIT') == count and observation['counts'].get('ACCEPT', 0) >= count > 0,
                        'functional commit count differs')
                functional.validate(uart, 'full', rc, extracted, require_diff=True)
                row.update(status='VDOT_MATRIX_SHARD_PASS', expected_vdot_commits=count)
            elif name == 'control':
                manifest = e.json(str(PurePosixPath(image).parent / 'data/manifest.json'))
                row.update(suite.classify_control(check_control.check(text, manifest, rc, analysis=observation)))
            elif name == 'dense-batch128':
                build = e.extract(str(PurePosixPath(image).parent), temp / 'dense-build')
                windows = perf.verify(build, directory, external=e.inputs)
                count = sum(s['dots'] for s in windows['samples'] if s['method'] == 'vdot')
                require(windows['status'] == 'PASS' and len(windows['samples']) == 12
                        and observation['counts'].get('COMMIT') == count
                        and observation['counts'].get('ACCEPT', 0) >= count > 0
                        and all(observation['counts'].get(k, 0) > 0 for k in ('MULTI_INFLIGHT', 'TRIPLE_OVERLAP')),
                        'dense windows or overlap gate differs')
                row.update(status='O2_DENSE_ELASTIC_AND_WINDOWS_PASS', expected_vdot_commits=count)
            elif name == 'hello-vadd':
                require(observation['counts'].get('ACCEPT') == observation['counts'].get('COMMIT') == 0
                        and 'HELLO_VADD_PASS' in uart and 'HIT GOOD TRAP' in uart, 'hello/vadd failed')
                row['status'] = 'HELLO_VADD_PASS'
            row.update(observation_status=observation['status'], observation_counts=observation['counts'])
            for key in ('status', 'observation_status', 'observation_counts', 'runtime_gate', 'expected_vdot_commits'):
                require(row.get(key) == expected.get(key), 'raw replay differs: ' + name + '/' + key)
            if name in ('negative-vdot', 'functional-0'):
                require({n: g.sha(directory / 'cwd/build' / n) for n in m.m.AUX} == m.m.AUX, 'new pair auxiliary input differs')
                raw_pair.append(record)
            core.append(row)
        for name in sorted(m.SUPPLEMENTS):
            original = str(PurePosixPath(e.cfg['legacy_base']) / 'supplements-01' / name)
            directory = e.extract(original, temp / name)
            replay = recheck_supplement(directory, e, workload)
            record = m.read(directory / 'result.json')
            require(record['files'].get(record['command'][5]) == m.m.EMU
                    and record['hardware_pins_sha256'] == m.m.META['hardware-inputs.json']
                    and record['build_source_commit'] == m.m.SOURCE, 'supplement hardware differs')
            for field in ('observation_counts', 'observation_status', 'workload_status', 'checked_register_bytes'):
                require(replay[field] == expected_supplements[name][field], 'supplement raw replay differs')
            require(record['files'] == expected_supplements[name]['files'], 'supplement input identity differs')
            for path, sha in record['files'].items():
                require(e.external.get(path) == sha if path in e.external else digest(e.raw(path)) == sha,
                        'supplement input not sealed')
            extra.append(dict(record, checked_register_bytes=replay['checked_register_bytes']))
    normal = raw_pair[1]
    m.pair_relation(*raw_pair, normal['command'][7], normal['command'][5], e.cfg['flash'],
                    e.cfg['reference'], str(PurePosixPath(e.cfg['fixture_dir']) / 'negative-reference.so'))
    passed, recovery, _ = suite.assess_suite(core, normal['command'][7])
    combined = rawcheck.combine_g3(passed, core, dict(status='O2_SUPPLEMENT_OFFLINE_RECHECK_PASS', records=extra), suite)
    require(passed and recovery and combined['whole_suite_pass'] and combined['suite_coverage'] == result['suite_coverage'],
            'exact set, recovery or coverage differs')
    return dict(status=ARCHIVE_PASS, contract=m.CONTRACT, archive=e.archive.bytes_result,
                audit_tool_sha256=g.sha(__file__),
                core_jobs=len(core), supplemental_jobs=len(extra), complete_normal_traces=13,
                expected_negative_traces=1, source_campaign_new_emu_runs=2, new_emu_runs=0, new_nemu_runs=0,
                physical_inputs_revalidated=False, independent_clean_build=False, performance_measured=False,
                historical_fixed_negative_acceptance=False, historical_b0_h1_acceptance=False,
                selected_s2_combination_acceptance=False, suite_coverage=combined['suite_coverage'],
                scope='Sealed raw streams, full functional/control/dense/supplement checks, O2 trace coverage, adopted byte chains and same-image negative/recovery. Original Linux physical audit is retained separately.')


def verify_index(archive_path):
    """Reuse the existing index parser; require every payload blob, not only names."""
    bind()
    archive_path = archive_path.resolve()
    require(archive_path.is_relative_to(ROOT), 'archive must be inside this repository')
    e = Evidence(archive_path)
    index = g.load('merged_regression_index_helpers', ROOT / g.REL / 'merged_index.py')
    relative = archive_path.relative_to(ROOT).as_posix()
    expected = {relative + '/' + r['stored'] for r in e.archive.records.values()}
    expected |= {relative + '/' + n for n in ('archive-manifest.json', 'archive-manifest.sha256')}
    entries = index.index_entries(index.git(ROOT, 'ls-files', '--stage', '-z', '--', relative))
    require(set(entries) == expected, 'Git index misses or adds archive files')
    names = sorted(entries)
    stream = io.BytesIO(index.git(ROOT, 'cat-file', '--batch', data=''.join(entries[n]['oid'] + '\n' for n in names).encode()))
    for name in names:
        header = stream.readline().split()
        require(len(header) == 3 and header[0].decode() == entries[name]['oid'] and header[1] == b'blob', 'wrong staged object')
        raw = stream.read(int(header[2]))
        require(stream.read(1) == b'\n' and raw == (ROOT / name).read_bytes(), 'staged bytes differ: ' + name)
    require(not stream.read(), 'unexpected Git blob output')
    return dict(status='O2_MERGED_ARCHIVE_COMPLETE_INDEX_PASS', files=len(names), new_emu_runs=0,
                archive=e.archive.bytes_result, architecture_replayed=False)


def output_guard(path, archive, protected=()):
    require(not path.exists() and not path.is_symlink(), 'report already exists')
    require(not path.resolve().is_relative_to(archive.resolve()), 'report must be outside sealed archive')
    require(not any(path.resolve().is_relative_to(p.resolve()) for p in protected),
            'report overlaps retained input')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('pack', 'audit', 'verify-index'))
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--physical-audit', type=Path)
    parser.add_argument('--support', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'pack':
            require(args.campaign is not None and args.physical_audit is not None, 'pack requires campaign and physical audit')
            output_guard(args.output, args.archive, retained_roots(args.campaign.resolve(), args.physical_audit.resolve()))
            value = pack(args.campaign, args.physical_audit, args.archive, args.support)
        else:
            output_guard(args.output, args.archive)
            value = audit(args.archive) if args.action == 'audit' else verify_index(args.archive)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(json_bytes(value))
        print(json.dumps(value, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        parser.exit(2, 'O2_MERGED_EVIDENCE_REJECTED: ' + str(exc) + '\n')
