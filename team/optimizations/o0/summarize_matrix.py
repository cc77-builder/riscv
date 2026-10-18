"""Independently recheck all 54 matrix runs and aggregate unique replay-0 windows."""
import argparse
from collections import Counter
import json
from pathlib import Path

import matrix_check as check
import replay_scenarios as scenarios


def summarize(images, runs, *, offline=False):
    require = check.require
    inventory = check.inventory(images)
    selection = check.sealed.strict_json((runs/'selection.json').read_bytes())
    campaign = check.sealed.strict_json((runs/'campaign.json').read_bytes())
    expected = [f"{row['image']}-r{replay}" for row in inventory['images'] for replay in range(3)]
    require(selection['selected_runs'] == expected, 'preselected inventory differs')
    require(selection['runtime_sha256'] == check.RUNTIME_SHA and selection['hardware_source'] == check.HARDWARE_SOURCE,
            'campaign runtime binding differs')
    require(selection['build_receipt_sha256'] == check.BUILD_SHA, 'campaign build binding differs')
    require(campaign['status'] == 'O0_BASELINE_54_RUNS_PASS', 'campaign did not complete')
    require(sorted(r['run'] for r in campaign['results']) == sorted(expected), 'campaign missing/duplicate runs')
    require(sorted(p.name for p in runs.glob('matrix-*') if p.is_dir()) == sorted(expected), 'run directory inventory differs')
    for name, digest in selection['checker_sha256'].items():
        require(check.CHECK.sha(check.ROOT/name) == digest, 'current checker differs; use the frozen source: '+name)
        require(check.CHECK.sha(runs/'checker-source'/name) == digest, 'archived checker changed')
    windows, records, samples_by_image = [], [], {}
    event_parser = check.sealed.load_diagnostics(check.ROOT).load_parser()
    for name in expected:
        run = runs/name
        image, replay = name.rsplit('-r', 1)
        build = images/image
        raw = check.sealed.strict_json((run/'result.json').read_bytes())
        require(raw['replay'] == int(replay) and raw['image'] == image, 'run directory/receipt identity differs')
        result = check.verify(build, run, external=offline)
        require(result == check.sealed.strict_json((run/'check.json').read_bytes()), 'run acceptance changed: '+name)
        saved = next(r for r in campaign['results'] if r['run'] == name)
        require(saved['status'] == 'PASS' and saved['samples'] == result['samples'], 'campaign sample drift')
        samples_by_image.setdefault(image, []).append(result['samples'])
        records.append(dict(run=name, raw_sha256=raw['raw_sha256'], counts=result['diagnosis']['counts']))
        if replay != '0':
            continue
        manifest = check.sealed.strict_json((build/'data/manifest.json').read_bytes())
        events, _ = event_parser.extract_events(check.CHECK.read_text(run/'stderr.log'))
        for sample in result['samples']:
            observation = scenarios.observe(sample, result['diagnosis'], events)
            row = manifest['rows'][manifest['plan'][sample['seq']]['index']]
            observation.update(lanes=row['lanes'], input_mode=row['input_mode'], image=image)
            windows.append(observation)
    for image, samples in samples_by_image.items():
        require(len(samples) == 3 and samples[0] == samples[1] == samples[2], 'determinism mismatch: '+image)
    require(len(windows) == 216, 'unique window inventory differs')
    groups = []
    for lanes in (1, 2, 4):
        for inputs in ('same', 'different'):
            for method in ('vdot', 'rvv'):
                chosen = [w for w in windows if w['lanes'] == lanes and w['input_mode'] == inputs
                          and w['method'] == method and w['phase'] == 'measured']
                require(len(chosen) == 12 and all(w['dots'] == 256 for w in chosen), 'measured group incomplete')
                group = dict(lanes=lanes, input_mode=inputs, method=method, dots_per_window=256,
                             measured_windows=12, cycles=[w['cycles'] for w in chosen],
                             mean_cycles=sum(w['cycles'] for w in chosen)/12,
                             instructions=sorted(set(w['instructions'] for w in chosen)),
                             FU_accepts_including_speculation=sum(w['FU_accepts_including_speculation'] for w in chosen),
                             response_coincident_busy_wait_events=sum(w['response_coincident_busy_wait_events'] for w in chosen))
                for field in ('accept_gap_histogram', 'release_gap_histogram', 'parent_wait_event_counts'):
                    counts = Counter()
                    for window in chosen:
                        counts.update(window[field])
                    group[field] = dict(sorted(counts.items()))
                groups.append(group)
    return dict(status='O0_BASELINE_54_RUNS_INDEPENDENT_RECHECK_PASS', hardware_source=check.HARDWARE_SOURCE,
                runtime_sha256=check.RUNTIME_SHA, build_receipt_sha256=check.BUILD_SHA, runs=records,
                actual_runs=54, checked_windows=648, unique_windows=216, unique_measured_windows=144,
                deterministic_replays_equal=True, summary=groups, windows=windows,
                source_sha256=check.CHECK.sha(Path(__file__)),
                hardware_execution_rechecked=True, new_hardware_execution=False,
                hardware_rebuilt=False, o0_complete=False, o1_implemented=False,
                limits=['Fixed d3706f0b8 II4 baseline only. T14 same-matrix runs remain pending.',
                        'Summary uses replay 0 only; repeated seed=1 samples are not independent.',
                        'Fixed arithmetic work does not fix loop/instruction count. Gaps are not intrinsic hardware II.',
                        'Busy/response coincidence does not prove handoff legality or predict O1 speedup.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', type=Path, required=True)
    parser.add_argument('--runs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offline', action='store_true', help='use fixed runtime hashes instead of requiring the original executables')
    args = parser.parse_args()
    check.require(not args.output.exists(), 'output already exists')
    result = summarize(args.images, args.runs, offline=args.offline)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(result['status'])
