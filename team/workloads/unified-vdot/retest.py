"""Portable fresh measurements for the final O2 EMU (Python 3.10+, Linux).

Uses the existing source-bound workload and strict T13 retirement/CSR checker.
Does not interpret T12 FU events or claim a new O2 queue/STA acceptance result.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys

import campaign
import check
import generate

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AM_REV = '086a238062fdfb3281b745a537b361983d0154b5'
SCENARIOS = ('single', 'chain', 'batch', 'stream')
require = check.require
sha = campaign.digest
save = campaign.save


def inventory(mode):
    items = [('smoke', 0, 0, 1)]
    if mode == 'full':
        items += [('functional', 0, s, 3) for s in range(3)]
        items += [('performance', d, s, 4) for d in range(3) for s in range(4)]
    return [(f'{suite}-d{d}-s{s:02d}', suite, d, s, n) for suite, d, s, n in items]


def fresh(path):
    path = path.resolve()
    require(not path.exists(), 'output exists; use a fresh directory: ' + str(path))
    require(not path.is_relative_to(ROOT) and not ROOT.is_relative_to(path),
            'output must be outside the repository')
    path.mkdir(parents=True)
    return path


def logged(command, log, **kwargs):
    with log.open('wb') as stream:
        subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True, **kwargs)


def build(a):
    am = a.am.resolve()
    revision = subprocess.check_output(['git', '-C', str(am), 'rev-parse', 'HEAD'], text=True).strip()
    require(revision == AM_REV, 'nexus-am revision differs from pinned release')
    subprocess.run(['git', '-C', str(am), 'diff', '--quiet', 'HEAD', '--'], check=True)
    out = fresh(a.output)
    env = dict(os.environ, AM_HOME=str(am), LINUX_GNU_TOOLCHAIN='1')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    images = []
    try:
        for name, suite, dataset, shard, shards in inventory(a.mode):
            folder = out / name
            folder.mkdir()
            generate.generate(folder / 'data', suite, dataset, shard, shards, True, 'ours')
            (folder / 'source').mkdir()
            names = ('generate.py', 'main.c', 'Makefile', 'fixed-layout.ld', 'check.py', 'retest.py')
            for filename in names:
                shutil.copyfile(HERE / filename, folder / 'source' / filename)
            command = ['make', '-C', str(HERE), 'ARCH=riscv64-xs', 'MARCH=rv64gcv',
                       'T13_DATA=' + str(folder / 'data'), 'T13_OBJ_ROOT=' + str(folder / 'objects'),
                       'BINARY=' + str(folder / 'vdot-perf'), '-j1']
            record = dict(source=source, am_revision=revision, command=command,
                          started=campaign.now(), software={n: sha(HERE / n) for n in names})
            save(folder / 'build.json', record)
            logged(command, folder / 'build.log', env=env, timeout=a.timeout)
            record.update(exit_code=0, finished=campaign.now(), artifacts={
                n: sha(folder / n) for n in ('vdot-perf.bin', 'vdot-perf.elf')})
            record['artifacts']['manifest.json'] = sha(folder / 'data/manifest.json')
            save(folder / 'build.json', record)
            manifest = json.loads((folder / 'data/manifest.json').read_text())
            check.verify_generation(folder, manifest)
            check.check_compiled_cases(folder / 'vdot-perf.elf', manifest)
            check.elf_kernels(folder / 'vdot-perf.elf')
            images.append(dict(name=name, suite=suite, dataset=dataset, shard=shard))
            print('RETEST_IMAGE_PASS ' + name, flush=True)
        flash = out / 'boot-flash'
        logged(['riscv64-linux-gnu-gcc', '-c', '-march=rv64gc', '-mabi=lp64d',
                str(ROOT / 'team/workloads/hello-vadd/boot-flash.S'), '-o', str(flash)+'.o'],
               out / 'flash-build.log', timeout=60)
        subprocess.run(['riscv64-linux-gnu-objcopy', '-O', 'binary', '-j', '.text',
                        str(flash)+'.o', str(flash)+'.bin'], check=True, timeout=60)
        save(out / 'images.json', dict(mode=a.mode, images=images, source=source,
             flash_sha256=sha(out / 'boot-flash.bin')))
    except Exception as exc:
        save(out / 'failure.json', dict(error=repr(exc), when=campaign.now()))
        raise


def load_images(folder):
    data = json.loads((folder / 'images.json').read_text())
    require(data['mode'] in ('smoke', 'full'), 'unknown image mode')
    require([r['name'] for r in data['images']] == [r[0] for r in inventory(data['mode'])],
            'missing, reordered or duplicate images')
    for row, (_, suite, dataset, shard, shards) in zip(data['images'], inventory(data['mode'])):
        b = folder / row['name']
        manifest = json.loads((b / 'data/manifest.json').read_text())
        require((manifest['suite'], manifest['dataset'], manifest['shard'], manifest['shards']) ==
                (suite, dataset, shard, shards), 'image identity mismatch')
        require(manifest['variant'] == 'ours' and manifest['shared_stream'], 'wrong workload variant')
        check.verify_generation(b, manifest)
        check.check_compiled_cases(b / 'vdot-perf.elf', manifest)
        check.elf_kernels(b / 'vdot-perf.elf')
    require(sha(folder / 'boot-flash.bin') == data['flash_sha256'], 'flash changed')
    return data


def hardware_identity(record_dir, emu):
    pins = json.loads((record_dir / 'hardware-inputs.json').read_text())
    state = json.loads((record_dir / 'build-state.json').read_text())
    require(state['status'] == 'O2_FULLCORE_BUILD_PASS' and state['build_exit_code'] == 0,
            'EMU build has not passed')
    require(pins['emu_sha256'] == state['emu_sha256'] == sha(emu), 'EMU digest mismatch')
    require(pins['source_commit'] == state['source_commit'], 'EMU source receipts disagree')
    required = dict(VDOT_O2_ELASTIC='1', VDOT_T14_FUSED_INPUT='1', VDOT_O1_HANDOFF='0',
                    VDOT_O2_TRACE='1', VDOT_T12_TRACE='0', VDOT_T13_TRACE='1')
    require(all(pins.get(k) == v for k, v in required.items()), 'need final observe-profile EMU')
    require(pins['config'] == 'MinimalConfig' and pins['NUM_CORES'] == pins['EMU_THREADS'] == 1,
            'need single-core/single-thread MinimalConfig')
    actual_tree = subprocess.check_output(['git', 'rev-parse', pins['source_commit'] + ':src'],
                                          cwd=ROOT, text=True).strip()
    final_tree = subprocess.check_output(['git', 'rev-parse', 'HEAD:src'], cwd=ROOT, text=True).strip()
    require(actual_tree == final_tree, 'EMU production source tree differs from release')
    require('build.sc' in pins['files'] and any(p.startswith('src/') for p in pins['files']),
            'missing hardware source pins')
    for name, digest in pins['files'].items():
        if name.startswith('src/') or name in ('build.sc', 'Makefile', 'Makefile.test'):
            require(sha(ROOT / name) == digest, 'hardware source changed: ' + name)
    return dict(source_commit=pins['source_commit'], src_tree=actual_tree, emu_sha256=pins['emu_sha256'],
                receipt_sha256={n: sha(record_dir / n) for n in ('hardware-inputs.json', 'build-state.json')})


def summarize(samples):
    grouped = defaultdict(dict)
    for s in samples:
        if s['stage'] != 'performance' or s['phase'] != 'measured':
            continue
        key = (s['dataset'], s['repeat'])
        group = grouped[s['scenario'], s['method']]
        require(key not in group, 'duplicate measured window')
        require(s['cycles'] > 0, 'nonpositive cycle count')
        group[key] = s
    require(set(grouped) == {(s, m) for s in SCENARIOS for m in ('vdot', 'rvv')},
            'missing or unexpected scenario/method')
    summary = []
    for scenario in SCENARIOS:
        v, r = grouped[scenario, 'vdot'], grouped[scenario, 'rvv']
        require(set(v) == set(r) == {(d, n) for d in range(3) for n in range(2, 6)},
                'need exactly 3 datasets x 4 measured windows per method')
        require(all((v[k]['n'], v[k]['dots']) == (r[k]['n'], r[k]['dots']) for k in v),
                'paired workloads differ')
        vc, rc = [s['cycles'] for s in v.values()], [s['cycles'] for s in r.values()]
        summary.append(dict(scenario=scenario, windows_per_method=12,
            vdot_mean=statistics.mean(vc), rvv_mean=statistics.mean(rc), speedup=sum(rc)/sum(vc),
            vdot_min=min(vc), vdot_max=max(vc), rvv_min=min(rc), rvv_max=max(rc)))
    return summary


def validate_run(build, run, files, reference):
    receipt = json.loads((run / 'result.json').read_text())
    expected = {**files, str(build / 'vdot-perf.bin'): sha(build / 'vdot-perf.bin')}
    require(receipt['files'] == expected, 'missing or mixed runtime artifacts')
    require(set(receipt.get('raw_sha256', {})) == {'stdout.log', 'stderr.log'}, 'missing raw log pins')
    stderr = check.read_text(run / 'stderr.log')
    require(not re.search(r'Assertion.*failed|different at pc|DIFFTEST FAIL|ABORT|HIT BAD TRAP', stderr),
            'runtime failure in stderr')
    combined = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', check.read_text(run / 'stdout.log') + '\n' + stderr)
    require(re.findall(r'The reference model is ([^\r\n]+)', combined) == [str(reference)],
            'loaded reference mismatch')
    return check.verify(build, run)


def analyze(images, runs, output):
    data = load_images(images)
    state = json.loads((runs / 'state.json').read_text())
    require(state['mode'] == data['mode'] and state['images_sha256'] == sha(images / 'images.json'),
            'campaign/image identity mismatch')
    for name, digest in state['files'].items():
        require(sha(name) == digest, 'runtime input changed: ' + name)
    if data['mode'] == 'full':
        require(state.get('hardware_identity'), 'full campaign requires hardware build receipts')
        identity = hardware_identity(Path(state['emu_record']), Path(state['emu']))
        require(identity == state['hardware_identity'], 'hardware identity changed')
    samples = []
    for row in data['images']:
        run = runs / row['name']
        verdict = validate_run(images / row['name'], run, state['files'], Path(state['reference']))
        for s in verdict['samples']:
            samples.append(dict(s, stage=row['suite'], image=row['name']))
    out = fresh(output)
    result = dict(status='PERFORMANCE_RETEST_PASS' if data['mode'] == 'full' else 'SMOKE_RETEST_PASS',
                  scope='DiffTest, full state, retired instructions and calibrated CSR windows; no O2 queue/STA qualification',
                  hardware_identity=state.get('hardware_identity'), samples=samples,
                  summary=summarize(samples) if data['mode'] == 'full' else [],
                  inputs=state['files'], images_sha256=state['images_sha256'],
                  raw_logs={row['name']: {n: sha(runs / row['name'] / n)
                            for n in ('stdout.log', 'stderr.log', 'result.json')} for row in data['images']})
    save(out / 'result.json', result)
    for name, rows in [('samples.csv', samples), ('summary.csv', result['summary'])]:
        if rows:
            with (out / name).open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
    print(result['status'] + ' ' + str(out), flush=True)
    return result


def run(a):
    images, emu, reference = a.images.resolve(), a.emu.resolve(), a.reference.resolve()
    data = load_images(images)
    require(os.access(emu, os.X_OK), 'EMU is not executable')
    require(a.emu_record is not None or data['mode'] == 'smoke', 'full mode requires --emu-record')
    identity = hardware_identity(a.emu_record.resolve(), emu) if a.emu_record else None
    out = fresh(a.output)
    state = dict(status='PREFLIGHT', mode=data['mode'], started=campaign.now(), emu=str(emu), reference=str(reference),
                 emu_record=str(a.emu_record.resolve()) if a.emu_record else None,
                 hardware_identity=identity, images_sha256=sha(images / 'images.json'))
    flash = images / 'boot-flash.bin'
    state['files'] = {str(p): sha(p) for p in (emu, reference, flash)}
    save(out / 'state.json', state)
    try:
        logged([sys.executable, '-B', str(ROOT / 'team/scripts/artifact_guard.py'), 'nemu-runtime',
                '--repo', str(reference.parent.parent), '--binary', str(reference), '--mode', 'reference'],
               out / 'nemu-check.json', timeout=120)
        def execute(row):
            folder = out / row['name']; folder.mkdir()
            binary = images / row['name'] / 'vdot-perf.bin'
            command = ['timeout', '--signal=TERM', '--kill-after=10s', str(a.timeout)+'s',
                       str(emu), '-i', str(binary), '--flash='+str(flash), '--ram-size=128MB',
                       '--diff='+str(reference), '--max-cycles='+str(a.max_cycles), '--seed=1', '--no-snapshot']
            receipt = dict(command=command, started=campaign.now(),
                           files={**state['files'], str(binary): sha(binary)})
            save(folder / 'runtime.json', receipt)
            with (folder / 'stdout.log').open('wb') as stdout, (folder / 'stderr.log').open('wb') as stderr:
                rc = subprocess.run(command, cwd=folder, stdout=stdout, stderr=stderr).returncode
            receipt.update(exit_code=rc, finished=campaign.now(),
                           raw_sha256={n: sha(folder / n) for n in ('stdout.log', 'stderr.log')})
            save(folder / 'result.json', receipt)
            require(rc == 0, row['name'] + ' EMU exit=' + str(rc))
            verdict = validate_run(images / row['name'], folder, state['files'], reference)
            save(folder / 'check.json', verdict)
            print('RETEST_RUN_PASS ' + row['name'], flush=True)
        for stage in ('smoke', 'functional', 'performance'):
            selected = [r for r in data['images'] if r['suite'] == stage]
            if not selected:
                continue
            state.update(status='RUNNING', stage=stage); save(out / 'state.json', state)
            with ThreadPoolExecutor(max_workers=a.jobs) as pool:
                list(pool.map(execute, selected))
        analyze(images, out, out / 'analysis')
        state.update(status='PASS', finished=campaign.now()); save(out / 'state.json', state)
    except Exception as exc:
        state.update(status='FAILED', error=repr(exc), finished=campaign.now())
        save(out / 'state.json', state)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action', required=True)
    b = subs.add_parser('build'); b.add_argument('--am', type=Path, required=True)
    b.add_argument('--mode', choices=('smoke', 'full'), default='full')
    b.add_argument('--timeout', type=int, default=300); b.add_argument('--output', type=Path, required=True)
    r = subs.add_parser('run')
    for name in ('images', 'emu', 'reference', 'output'):
        r.add_argument('--'+name, type=Path, required=True)
    r.add_argument('--emu-record', type=Path)
    r.add_argument('--timeout', type=int, default=1200)
    r.add_argument('--max-cycles', type=int, default=2000000)
    r.add_argument('--jobs', type=int, choices=(1, 2), default=1)
    c = subs.add_parser('analyze')
    for name in ('images', 'runs', 'output'):
        c.add_argument('--'+name, type=Path, required=True)
    a = parser.parse_args()
    if hasattr(a, 'timeout'):
        require(a.timeout > 0, 'timeout must be positive')
    if a.action == 'build': build(a)
    elif a.action == 'run': run(a)
    else: analyze(a.images.resolve(), a.runs.resolve(), a.output)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('RETEST_FAILED: ' + str(exc), file=sys.stderr)
        sys.exit(1)
