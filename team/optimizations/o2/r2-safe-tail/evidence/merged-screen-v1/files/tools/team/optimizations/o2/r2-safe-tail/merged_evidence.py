#!/usr/bin/env python3
"""Seal and independently replay a completed merged S2 software screen.

Offline audit replays architectural/counter/trace checks from archived bytes.
It does not launch EMU or revalidate absent hardware and NEMU build trees.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile

import merged_screen as m

g, f = m.g, m.f
PORTABLE = Path('team/optimizations/o2/fullcore/portable.py')
PORTABLE_SHA = '7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def portable(repo):
    g.require(g.sha(repo / PORTABLE) == PORTABLE_SHA, 'portable archive checker changed')
    return g.load('r2_merged_portable_archive', repo / PORTABLE)


def bind_modules(repo):
    for module, name in ((m, 'merged_screen.py'), (f, 'fullcore_screen.py'), (g, 'linked_gate.py')):
        g.require(Path(module.__file__).resolve() == (repo / g.REL / name).resolve(),
                  'executed module is outside the declared repository: ' + name)
    g.require(Path(__file__).resolve() == (repo / g.REL / 'merged_evidence.py').resolve(),
              'executed evidence entry differs from declared repository')


def pack(repo, run, output, support=()):
    repo, run, output = repo.resolve(), run.resolve(), output.resolve()
    bind_modules(repo)
    state = m.read_json(run / 'state.json')
    g.require(state['status'] == m.PASS and state['new_emu_runs'] == 31, 'campaign incomplete')
    g.require(not output.exists() and not output.is_relative_to(run), 'archive output must be new/outside run')
    cfg, inputs = m.read_json(run / 'configuration.json'), m.read_json(run / 'runtime-inputs.json')
    m.verify_files(inputs)
    canonical, hardware = Path(cfg['canonical_build']), Path(cfg['build_record'])
    g.require(not output.is_relative_to(canonical.resolve()), 'archive output must be outside canonical inputs')
    for item in support:
        g.require(not item.is_dir() or not output.is_relative_to(item.resolve()), 'archive output must be outside support inputs')
    output.mkdir(parents=True)
    entries, originals = [], {}
    archive_tools = portable(repo)

    def add(raw, logical, original):
        archive_tools.safe_relative(logical)
        g.require(original not in originals, 'duplicate archive original: ' + original)
        path = Path('files') / logical
        data, encoding = raw, 'identity'
        if len(raw) >= 16384 and path.suffix in ('.log', '.json', '.txt', '.S', '.h', '.patch'):
            path = path.with_name(path.name + '.gz')
            data, encoding = gzip.compress(raw, compresslevel=9, mtime=0), 'gzip'
        target = output / path
        g.require(not target.exists(), 'duplicate archive path: ' + logical)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append(dict(original=original, stored=path.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=digest(raw),
                            stored_bytes=len(data), stored_sha256=digest(data)))
        originals[original] = logical

    def add_file(path, logical):
        g.require(path.is_file() and not path.is_symlink(), 'missing/symlink evidence: ' + str(path))
        add(path.read_bytes(), logical, str(path))

    for directory, prefix in ((run, 'campaign'), (canonical, 'canonical')):
        for path in sorted(directory.rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(directory)
            if set(rel.parts) & {'objects', '__pycache__'}:
                continue
            # Runtime cwd may contain incidental simulator output. Only the two
            # actual auxiliary inputs belong to this archived contract.
            if 'cwd' in rel.parts and not (path.name in m.AUX and path.parent.name == 'build'):
                continue
            add_file(path, prefix + '/' + rel.as_posix())
    for name in m.META:
        add_file(hardware / name, 'hardware/' + name)
    add_file(Path(cfg['build_driver']), 'hardware/build-driver.py')
    add_file(Path(cfg['hardware_source']) / 'team/optimizations/o2/fullcore/build_fullcore.py',
             'hardware/original-build-driver.py')
    for name in m.AUX:
        add_file(Path(cfg['hardware_source']) / 'build' / name, 'hardware/' + name)
    for name in sorted(inputs):
        path = Path(name)
        if path.is_relative_to(repo):
            add_file(path, 'tools/' + path.relative_to(repo).as_posix())
    # These are export/audit tools, not retroactive identities of the live run.
    for rel in (g.REL / 'merged_evidence.py', PORTABLE):
        if str(repo / rel) not in originals:
            add_file(repo / rel, 'tools/' + rel.as_posix())
    for item in support:
        path = item.resolve()
        if path.is_dir():
            for child in sorted(path.rglob('*')):
                if child.is_file():
                    add_file(child, 'support/' + path.name + '/' + child.relative_to(path).as_posix())
        else:
            add_file(path, 'support/' + path.name)
    all_inputs = dict(inputs)
    for path in (run / 'runs').glob('*/result.json'):
        record = m.read_json(path)
        for name, sha in record['files'].items():
            g.require(name not in all_inputs or all_inputs[name] == sha, 'mixed input identities')
            all_inputs[name] = sha
    for image in m.read_json(canonical / 'images.json')['images']:
        receipt = m.read_json(Path(image['path']) / 'build.json')
        for name, sha in receipt['external_files'].items():
            g.require(name not in all_inputs or all_inputs[name] == sha, 'mixed AM library identities')
            all_inputs[name] = sha
    m.verify_files(all_inputs)
    sealed = {name: dict(sha256=sha, logical=originals.get(name)) for name, sha in sorted(all_inputs.items())}
    add(json_bytes(sealed), 'sealed-inputs.json', 'generated:sealed-inputs')
    git_identity = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
                        status=subprocess.check_output(['git', 'status', '--short'], cwd=repo, text=True))
    add(json_bytes(git_identity), 'export-source.json', 'generated:export-source')
    manifest = dict(version=1, contract=m.CONTRACT, created_utc=f.now(), source_commit_at_export=git_identity['head'],
                    work_root=str(run), files=entries,
                    exclusions=['EMU, normal NEMU and flash binaries', 'hardware/dependency trees and generated RTL',
                                'AM library binaries', 'canonical intermediate objects', 'incidental simulator cwd output'],
                    scope='original evidence bytes; external input hashes retained, physical artifacts not claimed portable')
    raw = json_bytes(manifest)
    (output / 'archive-manifest.json').write_bytes(raw)
    (output / 'archive-manifest.sha256').write_text(digest(raw) + '  archive-manifest.json\n')
    archive = portable(repo).Archive(output)
    result = dict(status='R2_MERGED_ARCHIVE_BYTES_PASS', **archive.bytes_result)
    g.save(output / 'archive-check.json', result)
    return result


def expected_jobs(images):
    jobs = {i['name'] + '-r0': (i, 0, False) for i in images}
    for image in images:
        if image['suite'] == 'performance' and image['dataset'] == 0 and image['shard'] in (5, 7):
            jobs[image['name'] + '-r1'] = image, 1, False
    jobs['negative-s2'] = next(i for i in images if i['suite'] == 'smoke' and i['variant'] == 's2'), 0, True
    g.require(len(jobs) == 31, 'wrong expected run inventory')
    return jobs


def run_identity(record, image, replay, negative, cfg, fixture, common, sealed):
    g.require(record.get('contract') == m.CONTRACT and record.get('mode') == 'merged' and
              record.get('replay') == replay and record.get('negative') is negative,
              'run contract/mode/replay differs')
    g.require(all(record[k] == v for k, v in image.items()), 'run/image identity differs')
    g.require(record.get('process_started') is True and type(record.get('pid')) is int and record['pid'] > 0 and
              not record.get('timed_out'), 'not a completed real process')
    g.require(record['status'] == (m.NEGATIVE_PASS if negative else m.NORMAL_PASS) and
              type(record['exit_code']) is int and record['exit_code'] == (1 if negative else 0), 'wrong run verdict/exit')
    start, finish = (datetime.fromisoformat(record[k]) for k in ('started', 'finished'))
    g.require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish,
              'invalid run timestamps')
    reference = fixture['binary'] if negative else cfg['reference']
    # These are recorded Linux argv strings, including during Windows replay.
    image_bin = str(PurePosixPath(image['path']) / 'vdot-perf.bin')
    expected_command = [str(PurePosixPath(cfg['hardware_source']) / 'build/emu'), '-i', image_bin,
                        '--flash=' + cfg['flash'], '--ram-size=128MB', '--diff=' + reference,
                        '--max-cycles=2000000', '--seed=1']
    g.require(record['command'] == expected_command and record['reference'] == reference, 'run command/reference differs')
    expected = dict(common)
    expected[image_bin] = image['image_sha256']
    expected.update({str(PurePosixPath(record['cwd']) / 'build' / name): sha for name, sha in m.AUX.items()})
    if negative:
        expected[reference] = fixture['negative_sha256']
    g.require(record['files'] == expected, 'run input map differs')
    for name, sha in expected.items():
        g.require(sealed.get(name, {}).get('sha256') == sha, 'unsealed run input')
    g.require(record.get('environment_overrides') == {'XS_NEGATIVE_VECTOR_TARGET': 'vdot' if negative else None},
              'negative-control environment differs')


def audit_recovery(negative, normal):
    m.validate_recovery(negative, normal)
    # Live f.now() uses one UTC representation. An archive audit also rejects
    # an offset-bearing receipt whose lexical order hides reversed real time.
    g.require(datetime.fromisoformat(normal['started']) >= datetime.fromisoformat(negative['finished']),
              'recovery ran before negative completion')


def normal_audit(repo, build, run, record, external):
    g.verify_build(build, repo)
    check = g.load('r2_merged_offline_counter_adapter', repo / g.O3 / 'check.py')
    def generation(directory, manifest):
        g.require(g.regenerate(directory) == manifest, 'offline regenerated manifest differs')
    check.base.verify_generation = generation
    windows = check.verify(build, run, external=external)
    gate = g.load('r2_merged_offline_failure', repo / 'team/optimizations/o1/audit/runtime_gate.py')
    fatal = g.load('r2_merged_offline_fatal', repo / 'team/optimizations/o2/fullcore/workloads/check.py')
    observer = g.load('r2_merged_offline_observer', repo / 'team/optimizations/o2/fullcore/analyze.py')
    stdout, stderr = ((run / name).read_text() for name in ('stdout.log', 'stderr.log'))
    for stream in (stdout, stderr):
        gate.validate_failure_markers(stream)
        fatal.reject_fatal_output(stream)
    analysis = observer.analyze(stderr + stdout)
    manifest = m.read_json(build / 'data/manifest.json')
    dots = sum(manifest['rows'][p['index']]['dots'] for p in manifest['plan']
               if manifest['rows'][p['index']]['method'] == 'vdot')
    g.require(analysis['status'] == 'O2_TRACE_PASS' and analysis['schema']['slots'] == 2 and
              all(analysis.get(k) == 0 for k in ('pending_count', 'pending_div_count', 'unfinished_rob_count')) and
              analysis['counts'].get('COMMIT') == dots, 'normal O2 transaction check failed')
    samples = []
    g.require(len(windows['samples']) == len(manifest['plan']), 'sample/plan length differs')
    for sample, entry in zip(windows['samples'], manifest['plan']):
        row = manifest['rows'][entry['index']]
        samples.append(dict(sample, mode='merged', variant=record['variant'], shard=record['shard'],
                            software=row['software'], m=row['m'], k=row['k'], scope=row['scope'],
                            image_sha256=record['image_sha256']))
    g.require(samples == record['samples'], 'recorded samples differ from raw recomputation')
    g.require(m.read_json(run / 'windows.json') == windows, 'cached windows differ')
    g.require(m.read_json(run / 'observation.json') == json.loads(json.dumps(analysis)), 'cached observation differs')
    # Diagnostic observations, not attribution of the whole window to the FU.
    # Speculative accepts need not equal the architecturally committed dot count.
    fu_windows = []
    if record['suite'] == 'performance' and record['replay'] == 0:
        for sample in samples:
            if sample['phase'] != 'measured' or sample['method'] != 'vdot':
                continue
            start, stop = sample['sample_ticks'][1:3]
            tx = [t for t in analysis['transactions'] if start <= t['accept_cycle'] < stop]
            accepts = sorted(t['accept_cycle'] for t in tx)
            responses = [t for t in tx if t.get('outcome') == 'response']
            details = {k: sample[k] for k in ('variant', 'shard', 'software', 'dataset', 'repeat', 'seq',
                                             'cycles', 'instructions', 'dots')}
            details.update(accepted_in_cycle_interval=len(tx),
                           response_latency_histogram=observer.histogram(t['elapsed_cycles'] for t in responses),
                           writeback_stall_events=sum(t['writeback_stall_events'] for t in tx),
                           accept_gap_histogram=observer.histogram(b - a for a, b in zip(accepts, accepts[1:])),
                           accept_span_cycles=accepts[-1] - accepts[0] if accepts else None,
                           first_accept_after_start=accepts[0] - start if accepts else None,
                           last_response_before_stop=stop - max(t['end_cycle'] for t in responses) if responses else None)
            fu_windows.append(details)
    return dict(samples=samples, fu_windows=fu_windows)


def audit(repo, archive_path):
    repo = repo.resolve()
    bind_modules(repo)
    archive = portable(repo).Archive(archive_path)
    g.require(archive.manifest.get('contract') == m.CONTRACT, 'wrong archived contract')
    common, sealed = archive.json('campaign/runtime-inputs.json'), archive.json('sealed-inputs.json')
    cfg = archive.json('campaign/configuration.json')
    state = archive.json('campaign/state.json')
    g.require(state['status'] == m.PASS and state['new_emu_runs'] == 31 and
              state['failed_or_incomplete_emu_runs'] == 0 and state['formal_windows'] == 384 and
              state['historical_b0_h1_acceptance'] is False and state['whole_suite_acceptance'] is False,
              'campaign state incomplete or wrong scope')
    for name, entry in sealed.items():
        if entry['logical'] is not None:
            g.require(digest(archive.raw(entry['logical'])) == entry['sha256'], 'sealed input bytes differ: ' + name)
    for name, sha in common.items():
        g.require(sealed.get(name, {}).get('sha256') == sha, 'common input not sealed')
    for name, sha in m.META.items():
        g.require(digest(archive.raw('hardware/' + name)) == sha, 'hardware metadata differs')
    pins = archive.json('hardware/hardware-inputs.json')
    g.require(pins['source_commit'] == m.SOURCE and pins['emu_sha256'] == m.EMU and
              len(pins['files']) == 429 and len(pins['dependency_files']) == 21236, 'wrong hardware profile')
    g.require(digest(archive.raw('hardware/build-driver.py')) == pins['build_script_sha256'], 'wrong actual build driver')
    g.require(common.get(str(PurePosixPath(cfg['hardware_source']) / 'build/emu')) == m.EMU and
              common.get(cfg['reference']) == f.REFERENCE and common.get(cfg['flash']) == f.FLASH,
              'runtime hardware/reference/flash mismatch')
    # The offline auditor executes the checked-out tools only after they match
    # the sealed live versions. No executable content is obtained from the web.
    for logical in sorted(archive.records):
        if logical.startswith('tools/team/') and logical.endswith('.py') and not logical.endswith('/merged_evidence.py'):
            relative = Path(logical).relative_to('tools')
            g.require(g.sha(repo / relative) == digest(archive.raw(logical)), 'offline tool differs from live source: ' + str(relative))
    f.pinned_modules(repo)
    g.verify_sources(repo)
    images = archive.json('canonical/images.json')['images']
    expected_images = {f.image_name(i): i for i in f.inventory()}
    g.require(len(images) == 26 and {i['name'] for i in images} == set(expected_images), 'wrong archived ELF inventory')
    for image in images:
        g.require(all(image[k] == v for k, v in expected_images[image['name']].items()), 'archived image label differs')
    jobs = expected_jobs(images)
    found = {p.split('/')[2] for p in archive.records
             if p.startswith('campaign/runs/') and p.endswith('/result.json') and len(p.split('/')) == 4}
    g.require(found == set(jobs), 'missing/extra archived run')
    fixture = archive.json('campaign/negative-fixture/fixture.json')
    g.require(fixture['source_sha256'] == m.NEGATIVE_SHA and fixture['normal_reference_sha256'] == f.REFERENCE and
              fixture['historical_negative_hash_claim'] is False and
              digest(archive.raw('campaign/negative-fixture/negative-fixture.c')) == m.NEGATIVE_SHA and
              digest(archive.raw('campaign/negative-fixture/negative-reference.so')) == fixture['negative_sha256'],
              'negative fixture identity differs')
    compiler = fixture['command'][0]
    fixture_root = PurePosixPath(fixture['binary']).parent
    expected_compile = [compiler, '-shared', '-fPIC', '-O2', '-DREF_SO="' + cfg['reference'] + '"',
                        str(fixture_root / 'negative-fixture.c'), '-Wl,--no-as-needed', cfg['reference'],
                        '-ldl', '-o', fixture['binary']]
    g.require(fixture['command'] == expected_compile, 'negative fixture compilation differs')
    for step in ('compiler', 'compile', 'linkage'):
        prefix = 'campaign/negative-fixture/' + step
        receipt = archive.json(prefix + '/command.json')
        g.require(receipt.get('process_started') is True and receipt.get('exit_code') == 0 and
                  not receipt.get('timed_out') and receipt.get('raw_sha256') ==
                  {name: digest(archive.raw(prefix + '/' + name)) for name in ('stdout.log', 'stderr.log')},
                  'incomplete/changed negative fixture build receipt: ' + step)
        expected_command = ([compiler, '--version'] if step == 'compiler' else expected_compile if step == 'compile'
                            else [receipt['command'][0], '-d', fixture['binary']])
        g.require(receipt['command'] == expected_command, 'negative fixture tool command differs')
    g.require('Shared library: [' + cfg['reference'] + ']' in
              archive.raw('campaign/negative-fixture/linkage/stdout.log').decode(), 'negative direct dependency missing')
    # The historical Linux path prefix is taken only from its unique entry;
    # every relative checker and all other common-input keys are then derived.
    suffix = '/' + (g.REL / 'merged_screen.py').as_posix()
    roots = [name[:-len(suffix)] for name in common if name.endswith(suffix)]
    g.require(len(roots) == 1, 'ambiguous live checker root')
    expected_common = {roots[0] + '/' + Path(name).relative_to(repo).as_posix(): sha
                       for name, sha in m.checker_files(repo).items()}
    expected_common.update({str(PurePosixPath(cfg['build_record']) / name): sha for name, sha in m.META.items()})
    expected_common.update({str(PurePosixPath(cfg['hardware_source']) / 'build' / name): sha for name, sha in m.AUX.items()})
    expected_common.update({str(PurePosixPath(cfg['hardware_source']) / 'build/emu'): m.EMU,
                            cfg['reference']: f.REFERENCE, cfg['flash']: f.FLASH,
                            cfg['build_driver']: pins['build_script_sha256'],
                            str(PurePosixPath(cfg['hardware_source']) / 'team/optimizations/o2/fullcore/build_fullcore.py'):
                            '8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0'})
    for name in ('images.json', 'state.json'):
        expected_common[str(PurePosixPath(cfg['canonical_build']) / name)] = digest(archive.raw('canonical/' + name))
    for image in images:
        for name in ('build.json', 'data/manifest.json'):
            expected_common[str(PurePosixPath(image['path']) / name)] = digest(archive.raw('canonical/images/' + image['name'] + '/' + name))
    g.require(common == expected_common, 'common runtime input inventory differs')
    external = {str(PurePosixPath(cfg['hardware_source']) / 'build/emu'): m.EMU,
                cfg['reference']: f.REFERENCE, cfg['flash']: f.FLASH}
    first_build = archive.json('canonical/images/' + images[0]['name'] + '/build.json')
    libraries = first_build['external_files']
    g.require(first_build['am_revision'] == f.AM_COMMIT and len(libraries) == 2 and
              sum(name.endswith('/am/build/am-riscv64-xs.a') for name in libraries) == 1 and
              sum(name.endswith('/libs/klib/build/klib-riscv64-xs.a') for name in libraries) == 1,
              'unexpected AM source/library inventory')
    external.update(libraries)
    for name, entry in sealed.items():
        if entry['logical'] is None:
            g.require(external.get(name) == entry['sha256'], 'unarchived non-external input: ' + name)
    records, negative, fu_windows = [], None, []
    with tempfile.TemporaryDirectory(prefix='r2-s2-audit-') as tmp:
        extracted = Path(tmp)
        for logical in archive.records:
            if logical.startswith(('canonical/', 'campaign/')):
                target = extracted / logical
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.raw(logical))
        image_builds = {}
        baseline_identity = None
        for image in images:
            build = extracted / 'canonical/images' / image['name']
            manifest, receipt = m.read_json(build / 'data/manifest.json'), m.read_json(build / 'build.json')
            m.validate_selection(image, manifest, receipt)
            g.verify_build(build, repo)
            g.require(g.sha(build / 'vdot-perf.bin') == image['image_sha256'], 'archived image bytes differ')
            identity = {k: receipt[k] for k in ('kind', 'source_base', 'source_commit', 'am_revision', 'external_files', 'toolchain')}
            if baseline_identity is None:
                baseline_identity = identity
            g.require(identity == baseline_identity, 'mixed canonical build environments')
            for name, sha in receipt['external_files'].items():
                g.require(sealed.get(name, {}).get('sha256') == sha, 'AM library identity not sealed')
            image_builds[image['name']] = build
        pairs = {(i['suite'], i['dataset'], i['shard'], i['variant']): i for i in images}
        for image in images:
            if image['variant'] != 's2':
                continue
            other = pairs[(image['suite'], image['dataset'], image['shard'], 's0')]
            a, b = image_builds[other['name']], image_builds[image['name']]
            ea, eb = (g.ELF((p / 'vdot-perf.elf').read_bytes()) for p in (a, b))
            for index in (1, 3):
                name = 't13_kernel_' + str(index)
                g.require(ea.symbols[name][0] == eb.symbols[name][0] and ea.symbol_data(name) == eb.symbol_data(name),
                          'RVV code/address differs')
            if image['shard'] in (4, 5):
                g.require((a / 'vdot-perf.bin').read_bytes() == (b / 'vdot-perf.bin').read_bytes(), 'control image differs')
        suite = g.load('r2_merged_offline_banner', repo / 'team/optimizations/o2/fullcore/run_suite.py')
        for name, (image, replay, is_negative) in jobs.items():
            run = extracted / 'campaign/runs' / name
            record = m.read_json(run / 'result.json')
            run_identity(record, image, replay, is_negative, cfg, fixture, common, sealed)
            g.require(record['raw_sha256'] == {p: g.sha(run / p) for p in ('stdout.log', 'stderr.log')}, 'raw transcript receipt differs')
            suite.validate_runtime((run / 'stdout.log').read_text() + (run / 'stderr.log').read_text(), record['reference'])
            build = image_builds[image['name']]
            if is_negative:
                prior_details, prior_observation = m.read_json(run / 'negative.json'), m.read_json(run / 'observation.json')
                details = m.negative_check(repo, build, run, record)
                g.require(details == prior_details == record['negative_details'] and
                          m.read_json(run / 'observation.json') == prior_observation, 'negative cached result differs')
                negative = record
            else:
                checked = normal_audit(repo, build, run, record, {p: v['sha256'] for p, v in sealed.items()})
                fu_windows.extend(checked['fu_windows'])
                records.append(record)
        recovery = next(r for r in records if r['suite'] == 'smoke' and r['variant'] == 's2')
        audit_recovery(negative, recovery)
        chronological = sorted(records + [negative], key=lambda r: datetime.fromisoformat(r['started']))
        for before, after in zip(chronological, chronological[1:]):
            g.require(datetime.fromisoformat(before['finished']) <= datetime.fromisoformat(after['started']), 'unexpected concurrent runs')
        for record in records:
            if record['replay'] == 1:
                original = next(r for r in records if r['name'] == record['name'] and r['replay'] == 0)
                g.require(m.signature(original) == m.signature(record), 'replay cycles/instructions differ')
    stats = m.summarize(records)
    cached = archive.json('campaign/results.json')
    g.require(cached['status'] == m.PASS and cached['contract'] == m.CONTRACT and cached['negative'] == negative,
              'summary scope/negative differs')
    g.require({(r['name'], r['replay']): r for r in cached['runs']} == {(r['name'], r['replay']): r for r in records}
              and len(cached['runs']) == 30, 'summary run receipts differ')
    for key in ('rows', 'comparisons'):
        g.require(cached[key] == stats[key], 'cached statistics differ: ' + key)
    sample_key = lambda s: (s['variant'], s['shard'], s['software'], s['method'], s['dataset'], s['repeat'])
    g.require(sorted(cached['samples'], key=sample_key) == sorted(stats['samples'], key=sample_key), 'cached formal samples differ')
    g.require(len(fu_windows) == 192, 'missing formal vdot diagnostic windows')
    return dict(status='R2_MERGED_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS', contract=m.CONTRACT,
                archive=archive.bytes_result, normal_runs=30, expected_negative_runs=1,
                formal_windows=384, replay_runs=4, new_emu_runs=0, new_nemu_runs=0,
                physical_hardware_and_reference_inputs_revalidated=False, historical_b0_h1_acceptance=False,
                whole_suite_acceptance=False, rows=stats['rows'], comparisons=stats['comparisons'],
                fu_window_diagnostics=fu_windows,
                fu_diagnostic_scope='Observed accepts/responses inside calibrated cycle intervals; not per-instruction latency attribution or an additional performance sample set',
                scope='Sealed ELF/golden/CSR/exact retirement/O2 trace/negative/recovery and statistics replay; external runtime artifacts represented by recorded hashes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--action', choices=('pack', 'audit'), required=True)
    parser.add_argument('--run', type=Path)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--support', action='append', default=[], type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'pack':
            g.require(args.run is not None, '--run required for pack')
            value = pack(args.repo, args.run, args.archive, args.support)
        else:
            g.require(args.output is not None and not args.output.exists(), 'audit requires a new --output file')
            value = audit(args.repo, args.archive)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            g.save(args.output, value)
        print(json.dumps(value, ensure_ascii=False))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, 'R2_MERGED_EVIDENCE_REJECTED: ' + str(exc) + '\n')
