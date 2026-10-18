"""Recheck the sealed unified ours archive, then diagnose its four scenarios.

No archived command is executed. The fixed manifest authenticates runtime hashes
passed to the current software checker. This is historical replay, not new RTL.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

import replay_archive as sealed

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = Path('team/evidence/unified-vdot-20261017/archive')
MANIFEST_SHA = '611c0410c48fbbafdd37cd730e19463998ecc012df26b0a70acb470b70ab2a1d'
IMAGES_SHA = 'd84c130d4e049d773524dda7503e9697f89d25a4d1f1fcd405d1b1932bea93b5'
EMU_SHA = '60521f406816846f8724de13021906a3ebbffa7044f35e6ee93c28bed7bf96b5'
SCENARIOS = {'single': 1, 'chain': 256, 'batch': 128, 'stream': 64}
require = sealed.require


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authenticate(archive):
    raw = (archive / '文件校验.json').read_bytes()
    require(sealed.sha256(raw) == MANIFEST_SHA, 'sealed manifest changed')
    manifest = sealed.strict_json(raw)
    require(manifest['algorithm'] == 'sha256', 'unexpected digest algorithm')
    files = manifest['files']
    require(len(files) == 439, 'archive inventory changed')
    for name, expected in files.items():
        path = sealed.contained(archive, name)
        require(sealed.sha256(path.read_bytes()) == expected, 'stored bytes changed: ' + name)
    require(sealed.sha256((archive / '测试镜像与构建快照.tar.gz').read_bytes()) == IMAGES_SHA,
            'image bundle changed')
    return len(files)


def extract_images(bundle, target):
    """Only ordinary files/directories, checked before writing (also on Windows)."""
    with tarfile.open(bundle) as archive:
        members = archive.getmembers()
        names = set()
        total = 0
        for member in members:
            name = member.name
            parts = PurePosixPath(name).parts
            require(parts and not name.startswith('/') and '\\' not in name
                    and ':' not in name and '..' not in parts, 'unsafe tar path')
            require(member.isfile() or member.isdir(), 'tar links/special files rejected')
            canonical = '/'.join(parts).casefold()
            require(canonical not in names, 'duplicate tar path')
            names.add(canonical)
            total += member.size
        require(total <= 128 * 1024 * 1024, 'image bundle too large')
        target.mkdir(parents=True, exist_ok=False)
        for member in members:
            if PurePosixPath(member.name).parts[0] != 'ours':
                continue
            dest = sealed.contained(target, member.name)
            if member.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, dest.open('xb') as sink:
                    sink.write(source.read())


def histogram(values):
    return dict(sorted(Counter(map(str, values)).items(), key=lambda pair: int(pair[0])))


def observe(sample, diagnosis, events):
    start, end = sample['sample_ticks'][1:3]
    accepted = [t for t in diagnosis['transactions'] if start <= t['accept_cycle'] < end]
    # Window-internal pairs only: never count setup/teardown between invocations.
    pairs = list(zip(accepted, accepted[1:]))
    waits = Counter()
    for cycle, _, kind, fields in events:
        if start <= cycle < end and kind == 'VFEX4_WAIT':
            key = ('vdot' if int(fields['fu'], 16) == 0x800000000 else 'other')
            key += '_busy' if fields['busy'] == '1' else '_not_busy'
            waits[key] += 1
    return {
        **{k: sample[k] for k in ('seq', 'scenario', 'dataset', 'method', 'phase', 'repeat', 'dots', 'cycles', 'instructions')},
        'start_inclusive': start, 'end_exclusive': end,
        'FU_accepts_including_speculation': len(accepted),
        'accepted_here_ended_outside_window': sum(t['end_cycle'] >= end for t in accepted),
        'accept_gap_histogram': histogram(b['accept_cycle'] - a['accept_cycle'] for a, b in pairs),
        'release_gap_histogram': histogram(b['accept_cycle'] - a['end_cycle'] for a, b in pairs),
        'response_coincident_busy_wait_events': sum(start <= c < end for c in diagnosis['response_coincident_busy_wait_cycles']),
        'parent_wait_event_counts': dict(sorted(waits.items())),
    }


def summarize(windows):
    rows = []
    for scenario, dots in SCENARIOS.items():
        for method in ('vdot', 'rvv'):
            selected = [w for w in windows if w['scenario'] == scenario and w['method'] == method and w['phase'] == 'measured']
            require(len(selected) == 12 and all(w['dots'] == dots for w in selected), 'incomplete measured inventory')
            row = dict(scenario=scenario, method=method, dots_per_window=dots, measured_windows=len(selected),
                       cycles=[w['cycles'] for w in selected],
                       mean_cycles=sum(w['cycles'] for w in selected) / len(selected),
                       FU_accepts_including_speculation=sum(w['FU_accepts_including_speculation'] for w in selected),
                       response_coincident_busy_wait_events=sum(w['response_coincident_busy_wait_events'] for w in selected))
            for field in ('accept_gap_histogram', 'release_gap_histogram', 'parent_wait_event_counts'):
                counts = Counter()
                for window in selected:
                    counts.update(window[field])
                row[field] = dict(sorted(counts.items()))
            rows.append(row)
    return rows


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def replay(root, output):
    require(not output.exists(), 'output already exists')
    require(not output.resolve().is_relative_to((root / 'team/evidence').resolve()), 'use a fresh work directory outside sealed evidence')
    archive = root / ARCHIVE
    stored = authenticate(archive)
    analyzer = sealed.load_diagnostics(root)
    checker = load('o0_unified_checker', root / 'team/workloads/unified-vdot/check.py')
    # run-suite imports sibling check by name; avoid depending on sys.path state.
    previous = {name: sys.modules.get(name) for name in ('check', 'campaign')}
    sys.modules['check'] = checker
    try:
        sys.modules['campaign'] = load('o0_unified_campaign', root / 'team/workloads/unified-vdot/campaign.py')
        suite = load('o0_unified_suite', root / 'team/workloads/unified-vdot/run-suite.py')
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    output.mkdir(parents=True, exist_ok=False)
    images = output / 'images'
    extract_images(archive / '测试镜像与构建快照.tar.gz', images)
    items = []
    for build in sorted((images / 'ours').iterdir()):
        manifest = sealed.strict_json((build / 'data/manifest.json').read_bytes())
        items.append(dict(name=build.name, path=str(build), suite=manifest['suite'],
                          dataset=manifest['dataset'], shard=manifest['shard'], replays=1))
    suite.validate_inventory(items, 'ours')
    all_samples, windows, runs = [], [], []
    event_parser = analyzer.load_parser()
    for item in items:
        run = archive / '验证证据/ours' / item['name']
        receipt = sealed.strict_json((run / 'result.json').read_bytes())
        roles = checker.runtime_roles(receipt['command'])
        require(receipt['files'][roles['emu']] == EMU_SHA, 'not the frozen fused-input EMU')
        checked = checker.verify(Path(item['path']), run, receipt['files'])
        require(checked == sealed.strict_json((run / 'check.json').read_bytes()), 'current checker disagrees: ' + item['name'])
        all_samples.extend(dict(s, variant='ours', stage=item['suite']) for s in checked['samples'])
        if item['suite'] != 'performance':
            continue
        stderr = sealed.decode_gzip((run / 'stderr.log.gz').read_bytes(), receipt['raw_sha256']['stderr.log'])
        diagnosis = analyzer.analyze(stderr, fu_latency=2)
        events, _ = event_parser.extract_events(stderr)
        observations = [observe(s, diagnosis, events) for s in checked['samples']]
        windows.extend(observations)
        dest = output / item['name']
        dest.mkdir()
        write_json(dest / 'diagnosis.json', diagnosis)
        write_json(dest / 'windows.json', {'windows': observations})
        with (dest / 'timeline.csv').open('x', encoding='utf-8', newline='') as stream:
            fields = list(dict.fromkeys(k for t in diagnosis['transactions'] for k in t))
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(diagnosis['transactions'])
        runs.append(dict(image=item['name'], raw_sha256=receipt['raw_sha256'],
                         image_sha256=checked['image_sha256'], counts=diagnosis['counts'],
                         response_latency_histogram=diagnosis['response_latency_histogram'],
                         parent_wait_event_counts=diagnosis['parent_wait_event_counts']))
        print(item['name'] + ': checked and diagnosed', flush=True)
    saved = sealed.strict_json((archive / '验证证据/ours/result.json').read_bytes())
    def canonical(samples):
        return sorted(json.dumps({k: v for k, v in s.items() if k != 'run'}, sort_keys=True) for s in samples)
    require(canonical(all_samples) == canonical(saved['samples']), 'suite inventory differs')
    require(len(all_samples) == 215 and len(windows) == 144 and len(runs) == 12, 'coverage incomplete')
    sources = ['team/optimizations/o0/replay_scenarios.py', 'team/optimizations/o0/replay_archive.py',
               'team/optimizations/o0/analyze.py', 'team/scripts/check-vdot-regression.py',
               'team/workloads/unified-vdot/check.py', 'team/workloads/unified-vdot/run-suite.py',
               'team/workloads/unified-vdot/campaign.py',
               'team/workloads/vdot-perf/check.py']
    result = dict(schema=1, status='O0_FOUR_SCENARIO_ARCHIVE_REPLAY_PASS',
                  archive_manifest_sha256=MANIFEST_SHA, images_sha256=IMAGES_SHA,
                  emu_sha256=EMU_SHA, stored_files_checked=stored, images_checked=16,
                  correctness_windows_checked=215, performance_windows_diagnosed=144,
                  measured_windows=96, raw_hardware_trace_replayed=True, new_hardware_run=False,
                  o0_complete=False, o1_implemented=False, runs=runs, summary=summarize(windows),
                  tool_sha256={name: sealed.sha256((root / name).read_bytes()) for name in sources},
                  limits=diagnosis['limits'] + [
                      'Four scenarios use different workloads (1/256/128/64 dots); no cross-scenario speedup inference.',
                      'Three datasets, one historical execution per image; no new independent repetitions.',
                      'Fixed 256-dot 1/2/4-lane same/different-input hardware matrix remains pending.'])
    write_json(output / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = replay(ROOT, args.output.resolve())
        print(result['status'])
        return 0
    except (ValueError, OSError, EOFError, KeyError, TypeError, tarfile.TarError) as exc:
        print('O0_SCENARIO_REPLAY_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
