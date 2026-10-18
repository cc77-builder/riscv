"""Run the preselected O0 baseline matrix, preserving every attempt and stream."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import json
from pathlib import Path
import subprocess
import sys

import matrix_check as check


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, record):
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')


def run(args):
    require = check.require
    output = args.output.resolve()
    images = args.images.resolve()
    require(not output.exists(), 'output already exists')
    require(1 <= args.jobs <= 8, 'jobs must be 1..8')
    require(not output.is_relative_to((check.ROOT/'team/evidence').resolve()), 'run outside sealed evidence')
    receipt = check.inventory(images)
    paths = {role: getattr(args, role).resolve() for role in check.RUNTIME_SHA}
    fixed = {str(p): check.CHECK.sha(p) for p in paths.values()}
    require(all(fixed[str(path)] == check.RUNTIME_SHA[role] for role, path in paths.items()), 'wrong frozen runtime')
    for item in receipt['images']:
        check.verify_build(images/item['image'])
    output.mkdir(parents=True, exist_ok=False)
    tools = [Path(__file__).resolve(), Path(check.__file__).resolve(),
             check.ROOT/'team/optimizations/o0/compile_matrix.py',
             check.ROOT/'team/optimizations/o0/generate_matrix.py',
             check.ROOT/'team/optimizations/o0/replay_archive.py',
             check.ROOT/'team/optimizations/o0/analyze.py',
             check.ROOT/'team/scripts/check-vdot-regression.py',
             check.ROOT/'team/workloads/unified-vdot/check.py',
             check.ROOT/'team/workloads/vdot-perf/check.py']
    source_hashes = {str(p.relative_to(check.ROOT)): check.CHECK.sha(p) for p in tools}
    for path in tools:
        dest = output/'checker-source'/path.relative_to(check.ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    selection = dict(started=now(), hardware_source=check.HARDWARE_SOURCE, build_receipt_sha256=check.BUILD_SHA,
                     runtime_sha256=check.RUNTIME_SHA, host_concurrency=args.jobs, single_core=True, emu_threads=1,
                     checker_sha256=source_hashes, selected_runs=[f"{r['image']}-r{i}" for r in receipt['images'] for i in range(3)],
                     policy='All 18 images, three seed=1 deterministic replays; no cycle-based selection')
    save(output/'selection.json', selection)

    def execute(name, replay):
        build = images/name
        folder = output/f'{name}-r{replay}'
        folder.mkdir()
        binary = build/'vdot-perf.bin'
        command = ['timeout', '120m', str(paths['emu']), '-i', str(binary), '--flash='+str(paths['flash']),
                   '--ram-size=128MB', '--diff='+str(paths['reference']), '--max-cycles=2000000', '--seed=1']
        record = dict(image=name, build=str(build), replay=replay, started=now(), command=command,
                      files=dict(fixed, **{str(binary): check.CHECK.sha(binary)}), single_core=True,
                      emu_threads=1, host_concurrency=args.jobs, hardware_source=check.HARDWARE_SOURCE, fu_latency=3)
        save(folder/'runtime.json', record)
        try:
            require(all(check.CHECK.sha(Path(p)) == h for p, h in record['files'].items()), 'input changed before launch')
            with (folder/'stdout.log').open('wb') as stdout, (folder/'stderr.log').open('wb') as stderr:
                completed = subprocess.run(command, cwd=check.ROOT, stdout=stdout, stderr=stderr)
            record.update(exit_code=completed.returncode, finished=now(),
                          raw_sha256={n: check.CHECK.sha(folder/n) for n in ('stdout.log', 'stderr.log')})
            require(all(check.CHECK.sha(Path(p)) == h for p, h in record['files'].items()), 'input changed during execution')
            save(folder/'result.json', record)
            checked = check.verify(build, folder)
            save(folder/'check.json', checked)
            print(folder.name + ': PASS windows=' + str(len(checked['samples'])), flush=True)
            return dict(run=folder.name, status='PASS', samples=checked['samples'])
        except Exception as error:
            record.update(verification_error=repr(error), finished=now())
            save(folder/'result.json', record)
            print(folder.name + ': REJECTED ' + repr(error), flush=True)
            return dict(run=folder.name, status='REJECTED', error=repr(error))

    results = []
    # First complete one real matrix invocation before scheduling the remaining corpus.
    first = execute('matrix-d0-s00', 0)
    results.append(first)
    save(output/'campaign.json', dict(status='RUNNING', results=results))
    require(first['status'] == 'PASS', 'matrix pilot rejected; remaining runs not started')
    tasks = [(r['image'], i) for r in receipt['images'] for i in range(3) if (r['image'], i) != ('matrix-d0-s00', 0)]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for future in as_completed([pool.submit(execute, name, replay) for name, replay in tasks]):
            results.append(future.result())
            save(output/'campaign.json', dict(status='RUNNING', results=results))
    require(len(results) == 54 and all(r['status'] == 'PASS' for r in results), 'one or more matrix runs rejected')
    for item in receipt['images']:
        replays = [r['samples'] for r in sorted(results, key=lambda r: r['run']) if r['run'].startswith(item['image']+'-r')]
        require(len(replays) == 3 and replays[0] == replays[1] == replays[2], 'deterministic replay disagreement')
    require(source_hashes == {str(p.relative_to(check.ROOT)): check.CHECK.sha(p) for p in tools}, 'checker source changed during campaign')
    save(output/'campaign.json', dict(status='O0_BASELINE_54_RUNS_PASS', finished=now(), results=results,
                                     hardware_source=check.HARDWARE_SOURCE, new_hardware_execution=True,
                                     hardware_rebuilt=False, windows=648, unique_windows=216,
                                     deterministic_replays_equal=True, o0_complete=False,
                                     limits=['Existing frozen d3706f0b8 II4 EMU; not a run of integrated T14/O1 hardware.',
                                             'T14 same-matrix comparison remains pending; repeated seed=1 runs are not independent samples.']))
    print('O0_BASELINE_54_RUNS_PASS', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('images', 'output', 'emu', 'reference', 'flash'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('O0_MATRIX_CAMPAIGN_REJECTED: '+str(error), file=sys.stderr)
        raise SystemExit(2)
