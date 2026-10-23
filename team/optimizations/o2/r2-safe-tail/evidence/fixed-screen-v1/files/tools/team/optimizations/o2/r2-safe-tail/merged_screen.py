#!/usr/bin/env python3
"""Strict S0/S2 software screen on the separately identified merged O2 hardware.

This is NOT the historical B0/H1 campaign or whole-suite hardware acceptance.
Consumes an already successful canonical build; never rebuilds or resumes EMU runs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess

import fullcore_screen as f
import linked_gate as g

CONTRACT = 'r2-s2-merged-software-screen-v1'
SOURCE = '6d2abe403b07c297b8830a7d4f06e370b0a8e070'
EMU = '1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63'
META = {
    'hardware-inputs.json': '2c580afa6095cda5e9d1680b7e91939b6f182b21c47357c77402c2d6b09d0a2c',
    'hardware-inputs-before.json': '92c91fd607448de7d28c3e6d6f294180764ec0b38c77b926a45b66f9705b8698',
    'generated-artifacts.json': '0ed279de2f10071ab763457097bfd9fdf1e304c3f01caee542753d93417f7b28',
    'build-state.json': 'ae84306e2e4bdeaa02b0abc4380032451ba02de3d05e8e5e0a46cf9f5f29305e',
    'dependencies.json': '564b9534ef059f544c564d6a491cca32cd34e8b3ba0f7868c3de401e2bd547d8',
    'build-command.sh': '6bd1b25079c9c15b9afd8c733b4a01949901e2c6c32a7ad008c3d9be7f3167bc',
    'emu-build.log': '9e7b5a1c3b5abb6f024406ef79a0cc7fce1ffc332ab1af20bc41212d4b7c2733',
    'source-status.txt': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'working-tree.patch': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'java-version.log': '5157fc80c2b1904606b0668b959604ac1266f20c8089e3e235d26ab755c73ead',
    'python-version.log': 'f6b75e07f1488db28a89724a522725e3e01af3dc78f6fd365f17eb4059e41056',
    'make-version.log': '8ee498ee2fc27e8dcdf99191b454077df95e3840d841ec94321748b6d7f36819',
    'mill-version.log': 'c62d357a27590ad6c8cfc7f87f5fee65896adf266c4ce221cc39f04ab6a9ea23',
    'firtool-version.log': '314271dc6f68632027c0711da7f96100db18723d94d80a16ad9d82cdd2e0377f',
    'clang-version.log': '8c803e6e30d91b83ca5df33fb58fc74c2021c3845b36ad4c22fb7fd8d94ee919',
    'verilator-version.log': '110d748d8e6eca23b22ad7bf766d1d1fcf69c45731c3260fc80857cdd2d62576',
}
AUX = {
    'constantin.txt': 'a1fd1d4de05919fec0257bacb550a3622c0f4ec2373e5cf230fc4233fb98c1bf',
    'plusArgs': '160d9702d313cbe66be84ae88c2f45c3df9ed7b61b65e3ddeea25133ac6765ff',
}
NEGATIVE_SOURCE = Path('team/evidence/t10-t11-fullcore-20261013/matrix/negative-fixture.c')
NEGATIVE_SHA = '7b39400d0a566229ce018a8251ead8242b92a3afe05a1aee5711b38809056273'
NORMAL_PASS = 'R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS'
NEGATIVE_PASS = 'EXPECTED_VDOT_HIGHBIT_REJECTION'
PASS = 'R2_S2_MERGED_SOFTWARE_SCREEN_PASS'


def read_json(path):
    return json.loads(Path(path).read_text())


def verify_files(files):
    for name, digest in files.items():
        g.require(g.sha(name) == digest, 'input drift: ' + str(name))


def read_config(path, repo):
    cfg = read_json(path)
    fields = {'hardware_source', 'build_record', 'build_driver', 'canonical_build', 'reference', 'flash'}
    g.require(set(cfg) == fields, 'unexpected/missing merged-screen configuration fields')
    for key, value in cfg.items():
        g.require(isinstance(value, str) and value.strip(), 'invalid path: ' + key)
        cfg[key] = str(Path(value.replace('${REPO}', str(repo))).expanduser().resolve())
    return cfg


def hardware_profile(repo, cfg):
    """Verify actual products, dependencies and source, not just receipt labels."""
    root, record = Path(cfg['hardware_source']), Path(cfg['build_record'])
    files = {str(record / name): digest for name, digest in META.items()}
    files.update({str(root / 'build' / name): digest for name, digest in AUX.items()})
    files.update({str(root / 'build/emu'): EMU, cfg['reference']: f.REFERENCE, cfg['flash']: f.FLASH})
    verify_files(files)
    pins, state = read_json(record / 'hardware-inputs.json'), read_json(record / 'build-state.json')
    suite = g.load('r2_merged_suite', repo / 'team/optimizations/o2/fullcore/run_suite.py')
    suite.validate_pin_fields(pins)
    g.require(pins['source_commit'] == SOURCE and pins['emu_sha256'] == EMU, 'wrong merged identity')
    g.require(state['source_commit'] == SOURCE and state['emu_sha256'] == EMU and
              state['status'] == 'O2_FULLCORE_BUILD_PASS' and state['build_exit_code'] == 0,
              'merged build was not completed successfully')
    g.require(len(pins['files']) == 429 and len(pins['dependency_files']) == 21236,
              'incomplete hardware input inventory')
    suite.hardware_guard(pins, root / 'build/emu', root=root)
    profile = g.load('r2_merged_git_sources', repo / f.H1DIR / 'build_profile.py')
    profile.ROOT = root
    profile.verified_git_sources(pins)
    # The actual builder was a recorded, external resource-adapted copy. Keep
    # both identities; the original source file is not that executed copy.
    files[str(root / 'team/optimizations/o2/fullcore/build_fullcore.py')] = \
        '8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0'
    files[cfg['build_driver']] = pins['build_script_sha256']
    verify_files(files)
    generated = read_json(record / 'generated-artifacts.json')
    g.require(len(generated) == 1672 and len({p['path'] for p in generated}) == 1672,
              'incomplete/duplicate generated inventory')
    for item in generated:
        rel = Path(item['path'])
        g.require(not rel.is_absolute() and '..' not in rel.parts, 'unsafe product path')
        path = root / rel
        g.require(path.stat().st_size == item['bytes'] and g.sha(path) == item['sha256'],
                  'generated artifact drift: ' + str(rel))
    provenance = g.load('r2_merged_artifact_guard', repo / 'team/scripts/artifact_guard.py')
    ref = Path(cfg['reference'])
    reference_provenance = provenance.verify_nemu(ref.parents[1], ref, 'reference')
    details = dict(contract=CONTRACT, source_commit=SOURCE, emu_sha256=EMU,
                   pins_sha256=META['hardware-inputs.json'], source_files=429,
                   dependency_files=21236, generated_files=1672,
                   reference_provenance=reference_provenance, build_driver_sha256=pins['build_script_sha256'],
                   historical_b0_h1_acceptance=False, whole_suite_acceptance=False)
    return files, details


def checker_files(repo):
    f.pinned_modules(repo)
    g.verify_sources(repo)
    fixed = {
        'fullcore_screen.py': '5f5c719a9a5b675f4de166ca30a3d89bd52c944c667cee302f66da94fa2779f2',
        'linked_gate.py': '96807465bfd97a483f31ce100e552e2b83c4d0edd59f9bf4d817c66abd80ec1f',
    }
    verify_files({str(repo / g.REL / name): digest for name, digest in fixed.items()})
    paths = set(f.CHECKER_PATHS) | set(g.PINNED) | {
        g.REL / 'fullcore_screen.py', g.REL / 'linked_gate.py', g.REL / 'merged_screen.py',
        Path('team/optimizations/o2/fullcore/run_suite.py'),
        Path('team/optimizations/o2/fullcore/recheck.py'),
        Path('team/scripts/artifact_guard.py'), Path('team/patches/nemu/manifest.json'), NEGATIVE_SOURCE,
    }
    return {str(repo / p): g.sha(repo / p) for p in paths}


def validate_selection(image, manifest, receipt):
    expected = {k: image[k] for k in ('suite', 'dataset', 'shard', 'variant')}
    g.require(receipt['selection'] == expected and receipt.get('accepted') is True,
              'build selection does not match image label')
    actual = {k: manifest['r2_variant' if k == 'variant' else k] for k in expected}
    g.require(actual == expected, 'manifest selection does not match image label')


def canonical_images(repo, cfg):
    base = Path(cfg['canonical_build'])
    g.require(read_json(base / 'state.json')['status'] == 'CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN',
              'input is not a completed canonical build-only result')
    images = read_json(base / 'images.json')['images']
    expected = {f.image_name(item): item for item in f.inventory()}
    g.require(len(images) == 26 and {i['name'] for i in images} == set(expected),
              'canonical image inventory differs')
    for item in images:
        g.require(all(item[k] == v for k, v in expected[item['name']].items()), 'image label differs')
        build = Path(item['path'])
        g.require(build.resolve() == (base / 'images' / item['name']).resolve(), 'image outside canonical build')
        validate_selection(item, read_json(build / 'data/manifest.json'), read_json(build / 'build.json'))
        g.verify_build(build, repo)
        g.require(g.sha(build / 'vdot-perf.bin') == item['image_sha256'], 'image identity changed')
    f.validate_controls(images, repo)
    return images


def build_negative(repo, cfg, out):
    out.mkdir(parents=True, exist_ok=False)
    source = repo / NEGATIVE_SOURCE
    g.require(g.sha(source) == NEGATIVE_SHA, 'negative fixture source changed')
    shutil.copyfile(source, out / 'negative-fixture.c')
    cc, readelf = shutil.which('gcc'), shutil.which('readelf')
    g.require(cc and readelf, 'negative fixture requires gcc and readelf')
    binary = out / 'negative-reference.so'
    argv = [cc, '-shared', '-fPIC', '-O2', '-DREF_SO="' + cfg['reference'] + '"',
            str(out / 'negative-fixture.c'), '-Wl,--no-as-needed', cfg['reference'], '-ldl', '-o', str(binary)]
    f.command([cc, '--version'], out, out / 'compiler')
    f.command(argv, out, out / 'compile')
    f.command([readelf, '-d', str(binary)], out, out / 'linkage')
    linkage = (out / 'linkage/stdout.log').read_text()
    g.require('Shared library: [' + cfg['reference'] + ']' in linkage, 'normal reference not a direct dependency')
    result = dict(source_sha256=NEGATIVE_SHA, normal_reference_sha256=f.REFERENCE,
                  negative_sha256=g.sha(binary), binary=str(binary), command=argv,
                  historical_negative_hash_claim=False)
    g.save(out / 'fixture.json', result)
    return result


def negative_check(repo, build, out, record):
    gate = g.load('r2_merged_negative_gate', repo / 'team/optimizations/o1/audit/runtime_gate.py')
    fatal = g.load('r2_merged_fatal_gate', repo / 'team/optimizations/o2/fullcore/recheck.py')
    observer = g.load('r2_merged_negative_observer', repo / 'team/optimizations/o2/fullcore/analyze.py')
    stdout, stderr = ((out / p).read_text() for p in ('stdout.log', 'stderr.log'))
    for stream in (stdout, stderr):
        fatal.reject_fatal_output(stream)
    detail = gate.validate_negative(stderr + stdout, record['exit_code'])
    plain = gate.normalize_console(stdout)
    mismatch, abort = list(gate.MISMATCH.finditer(plain)), list(gate.ABORT.finditer(plain))
    g.require(len(mismatch) == len(abort) == 1 and mismatch[0].end() < abort[0].start() and
              not plain[mismatch[0].end():abort[0].start()].strip(), 'negative raw stdout chain differs')
    elf = g.ELF((build / 'vdot-perf.elf').read_bytes())
    word = int.from_bytes(elf.read(int(detail['pc'], 16), 4), 'little')
    g.require(word == int(detail['word'], 16), 'injected instruction not in selected ELF')
    analysis = observer.analyze(stderr + stdout, require_complete=False)
    g.require(analysis['status'] == 'O2_PARTIAL_TRACE_AUDIT' and analysis['schema']['slots'] == 2,
              'negative O2 partial trace failed')
    g.save(out / 'negative.json', detail)
    g.save(out / 'observation.json', analysis)
    return detail


def execute(repo, cfg, image, out, files, negative=None, replay=0, progress=None):
    out.mkdir(parents=True, exist_ok=False)
    build, root = Path(image['path']), Path(cfg['hardware_source'])
    cwd = out / 'cwd'
    (cwd / 'build').mkdir(parents=True)
    for name in AUX:
        shutil.copyfile(root / 'build' / name, cwd / 'build' / name)
    reference = negative['binary'] if negative else cfg['reference']
    inputs = dict(files)
    inputs.update({str(cwd / 'build' / name): digest for name, digest in AUX.items()})
    inputs[str(build / 'vdot-perf.bin')] = image['image_sha256']
    if negative:
        inputs[reference] = negative['negative_sha256']
    argv = [str(root / 'build/emu'), '-i', str(build / 'vdot-perf.bin'), '--flash=' + cfg['flash'],
            '--ram-size=128MB', '--diff=' + reference, '--max-cycles=2000000', '--seed=1']
    record = dict(image, contract=CONTRACT, mode='merged', replay=replay,
                  negative=bool(negative), command=argv, cwd=str(cwd), files=inputs,
                  reference=reference, exit_code=None, process_started=False, status='RUNNING', started=f.now())
    def persist():
        g.save(out / 'result.json', record)
        if progress:
            progress(record)
    persist()
    try:
        g.verify_build(build, repo)
        validate_selection(image, read_json(build / 'data/manifest.json'), read_json(build / 'build.json'))
        verify_files(inputs)
        env = dict(os.environ)
        env.pop('XS_NEGATIVE_VECTOR_TARGET', None)
        if negative:
            env['XS_NEGATIVE_VECTOR_TARGET'] = 'vdot'
        record['environment_overrides'] = {'XS_NEGATIVE_VECTOR_TARGET': 'vdot' if negative else None}
        with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
            f.spawn(argv, cwd, stdout, stderr, record, persist, env=env, timeout=7200)
        record['raw_sha256'] = {p: g.sha(out / p) for p in ('stdout.log', 'stderr.log')}
        persist()
        suite = g.load('r2_merged_runtime_banner', repo / 'team/optimizations/o2/fullcore/run_suite.py')
        suite.validate_runtime((out / 'stdout.log').read_text() + (out / 'stderr.log').read_text(), reference)
        if negative:
            record['negative_details'] = negative_check(repo, build, out, record)
            record['status'] = NEGATIVE_PASS
        else:
            g.require(record['exit_code'] == 0 and not record.get('timed_out'), 'EMU incomplete/nonzero exit')
            windows, analysis = f.verify_runtime(repo, build, out)
            manifest = read_json(build / 'data/manifest.json')
            g.require(len(windows['samples']) == len(manifest['plan']), 'sample/plan count differs')
            record['samples'] = []
            for sample, entry in zip(windows['samples'], manifest['plan']):
                row = manifest['rows'][entry['index']]
                record['samples'].append(dict(sample, mode='merged', variant=image['variant'], shard=image['shard'],
                                              software=row['software'], m=row['m'], k=row['k'], scope=row['scope'],
                                              image_sha256=image['image_sha256']))
            g.save(out / 'windows.json', windows)
            g.save(out / 'observation.json', analysis)
            record['status'] = NORMAL_PASS
        verify_files(inputs)
    except BaseException as exc:
        record.update(status='FAILED', error=repr(exc))
        if not isinstance(exc, Exception):
            raise
    finally:
        record['raw_sha256'] = {p: g.sha(out / p) for p in ('stdout.log', 'stderr.log') if (out / p).is_file()}
        record['finished'] = f.now()
        persist()
    g.require(record['status'] == (NEGATIVE_PASS if negative else NORMAL_PASS), 'runtime gate failed: ' + str(out))
    return record


def signature(record):
    return [(s['seq'], s['cycles'], s['instructions']) for s in record['samples']]


def summarize(records):
    """Single hardware; preserve every qualifying RVV and the invariant controls."""
    samples = [s for r in records if r['suite'] == 'performance' and r['replay'] == 0
               for s in r['samples'] if s['phase'] == 'measured']
    expected = {(v, shard, software, method, dataset, repeat)
                for v in ('s0', 's2') for shard in (4, 5, 6, 7) for software in ('basic', 'reuse')
                for method in ('vdot', 'rvv') for dataset in range(3) for repeat in range(2, 6)}
    keys = {}
    for sample in samples:
        key = tuple(sample[k] for k in ('variant', 'shard', 'software', 'method', 'dataset', 'repeat'))
        g.require(key not in keys, 'duplicate measured sample')
        g.require(sample['mode'] == 'merged' and type(sample['cycles']) is int and sample['cycles'] > 0 and
                  type(sample['instructions']) is int and sample['instructions'] > 0, 'invalid measured sample')
        keys[key] = sample
    g.require(set(keys) == expected and len(samples) == 384, 'missing/extra measured sample keys')
    rows = []
    for shard in (4, 5, 6, 7):
        for variant in ('s0', 's2'):
            for software in ('basic', 'reuse'):
                row = dict(shard=shard, variant=variant, software=software)
                for method in ('vdot', 'rvv'):
                    values = []
                    for dataset in range(3):
                        for repeat in range(2, 6):
                            sample = keys[(variant, shard, software, method, dataset, repeat)]
                            if shard in (4, 5):
                                other = keys[('s2' if variant == 's0' else 's0', shard, software, method, dataset, repeat)]
                                g.require(all(sample[k] == other[k] for k in ('image_sha256', 'instructions', 'seq', 'cycles')),
                                          '16x64 invariant control diverged')
                            values.append(sample['cycles'])
                    row[method] = dict(samples=12, total=sum(values), mean=statistics.mean(values),
                                       minimum=min(values), maximum=max(values), pstdev=statistics.pstdev(values))
                row['rvv_over_vdot'] = row['rvv']['total'] / row['vdot']['total']
                rows.append(row)
    comparisons = []
    for shard in (4, 5, 6, 7):
        eligible = [r for r in rows if r['shard'] == shard]
        rvv = min(eligible, key=lambda r: r['rvv']['total'])
        for row in eligible:
            baseline = next(r for r in eligible if r['variant'] == 's0' and r['software'] == row['software'])
            comparisons.append(dict(shard=shard, variant=row['variant'], software=row['software'],
                                    s0_over_variant=baseline['vdot']['total'] / row['vdot']['total'],
                                    fastest_rvv_variant=rvv['variant'], fastest_rvv_software=rvv['software'],
                                    fastest_rvv_over_vdot=rvv['rvv']['total'] / row['vdot']['total']))
    return dict(samples=samples, rows=rows, comparisons=comparisons)


def validate_recovery(negative, normal):
    g.require(negative['status'] == NEGATIVE_PASS and normal['status'] == NORMAL_PASS and
              negative['image_sha256'] == normal['image_sha256'] and normal['started'] >= negative['finished'] and
              negative['pid'] != normal['pid'], 'negative/normal recovery provenance differs')


def run(repo, cfg, out, action):
    repo, out = repo.resolve(), out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status='PREFLIGHT', started=f.now(), new_emu_runs=0,
                 hardware_source_commit=SOURCE, historical_b0_h1_acceptance=False,
                 whole_suite_acceptance=False, performance_measured=False)
    persist = lambda: g.save(out / 'state.json', state)
    persist()
    def launch(image, name, negative=None, replay=0):
        run_out = out / 'runs' / name
        before = state['new_emu_runs']
        def progress(record):
            state['new_emu_runs'] = before + int(record.get('process_started') is True)
            state['active_result'] = str(run_out / 'result.json') if 'finished' not in record else None
            state['active_pid'] = record.get('pid') if 'finished' not in record else None
            persist()
        return execute(repo, cfg, image, run_out, files, negative, replay, progress)
    try:
        g.save(out / 'configuration.json', cfg)
        files = checker_files(repo)
        hardware_files, details = hardware_profile(repo, cfg)
        files.update(hardware_files)
        images = canonical_images(repo, cfg)
        files.update({str(Path(i['path']) / p): g.sha(Path(i['path']) / p)
                      for i in images for p in ('build.json', 'data/manifest.json')})
        files.update({str(Path(cfg['canonical_build']) / p): g.sha(Path(cfg['canonical_build']) / p)
                      for p in ('images.json', 'state.json')})
        g.save(out / 'build-profile.json', details)
        g.save(out / 'runtime-inputs.json', files)
        g.save(out / 'images.json', dict(images=images))
        state.update(status='MERGED_SCREEN_PREFLIGHT_PASS', canonical_elfs=26)
        persist()
        if action == 'preflight':
            return state
        negative_fixture = build_negative(repo, cfg, out / 'negative-fixture')
        smoke_s2 = next(i for i in images if i['suite'] == 'smoke' and i['variant'] == 's2')
        state.update(status='RUNNING', stage='negative-then-recovery')
        persist()
        negative = launch(smoke_s2, 'negative-s2', negative_fixture)
        records = [launch(smoke_s2, smoke_s2['name'] + '-r0')]
        validate_recovery(negative, records[0])
        smoke_s0 = next(i for i in images if i['suite'] == 'smoke' and i['variant'] == 's0')
        records.append(launch(smoke_s0, smoke_s0['name'] + '-r0'))
        state.update(stage='formal', smoke_pass=True, negative_and_recovery_pass=True)
        persist()
        formal = [i for i in images if i['suite'] == 'performance']
        # Reverse S0/S2 pair order for odd datasets to expose host/order effects.
        formal.sort(key=lambda i: (i['shard'], i['dataset'], (i['variant'] == 's0') == (i['dataset'] % 2 == 1)))
        for image in formal:
            records.append(launch(image, image['name'] + '-r0'))
            state['normal_runs_completed'] = len(records)
            persist()
        state['stage'] = 'replay'
        persist()
        for image in [i for i in formal if i['dataset'] == 0 and i['shard'] in (5, 7)]:
            record = launch(image, image['name'] + '-r1', replay=1)
            prior = next(r for r in records if r['name'] == image['name'] and r['replay'] == 0)
            g.require(signature(record) == signature(prior), 'deterministic replay differs')
            records.append(record)
        g.require(len(records) == 30, 'normal campaign inventory incomplete')
        stats = summarize(records)
        hardware_profile(repo, cfg)
        verify_files(files)
        g.save(out / 'results.json', dict(status=PASS, contract=CONTRACT, runs=records, negative=negative, **stats))
        state.update(status=PASS, stage='complete', normal_runs_completed=30,
                     formal_windows=384, performance_measured=True)
    except BaseException as exc:
        state.update(status='BLOCKED_OR_FAILED', error=repr(exc))
        raise
    finally:
        receipts = [read_json(p) for p in (out / 'runs').glob('*/result.json')]
        state['new_emu_runs'] = sum(r.get('process_started') is True for r in receipts)
        state['failed_or_incomplete_emu_runs'] = sum(r.get('process_started') is True and
                                                    r.get('status') not in (NORMAL_PASS, NEGATIVE_PASS) for r in receipts)
        state['finished'] = f.now()
        persist()
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--action', choices=('preflight', 'run'), default='preflight')
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.repo, read_config(args.config, args.repo.resolve()), args.output, args.action)))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, 'R2_MERGED_SCREEN_STOPPED: ' + str(exc) + '\n')
