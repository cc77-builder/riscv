"""Apply current reviewed gates to the sealed matrix without rewriting old evidence.

The original verify.py remains an exact-source historical replay. This entry
authenticates its archives first, rechecks each run with current code, and records
both source identities instead of pretending the checkers have not changed.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import matrix_check as check

ROOT = check.ROOT
EVIDENCE = ROOT/'team/evidence/o0-baseline-20261018'


def recheck(output):
    require = check.require
    output = output.resolve()
    require(not output.exists(), 'output already exists')
    require(not output.is_relative_to((ROOT/'team/evidence').resolve()), 'use a fresh work directory')
    spec = importlib.util.spec_from_file_location('sealed_matrix_verifier', EVIDENCE/'verify.py')
    sealed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sealed)
    require(sealed.sha(EVIDENCE/'artifacts.json') == sealed.ARTIFACTS_SHA, 'sealed manifest changed')
    for name, record in check.sealed.strict_json((EVIDENCE/'artifacts.json').read_bytes()).items():
        path = check.sealed.contained(EVIDENCE, name)
        require(path.stat().st_size == record['bytes'] and sealed.sha(path) == record['sha256'], 'artifact changed: '+name)
    builds = EVIDENCE.parent/'o0-progress-20261017'
    require(sealed.sha(builds/'matrix-images.tar.gz') == sealed.BUILD_ARCHIVE_SHA, 'build archive changed')
    require(sealed.sha(builds/'matrix-build.json') == check.BUILD_SHA, 'build receipt changed')
    sealed.extract(builds/'matrix-images.tar.gz', output/'images')
    (output/'images/result.json').write_bytes((builds/'matrix-build.json').read_bytes())
    sealed.extract(EVIDENCE/'runs.tar.gz', output/'runs')
    selection = check.sealed.strict_json((output/'runs/selection.json').read_bytes())
    campaign = check.sealed.strict_json((output/'runs/campaign.json').read_bytes())
    # Archive authentication above binds these original source bytes and results.
    historical = selection['checker_sha256']
    for name, digest in historical.items():
        require(sealed.sha(output/'runs/checker-source'/name) == digest, 'historical checker changed')
    tools = sorted(set(historical) | {
        'team/optimizations/o0/recheck_matrix.py', 'team/optimizations/o0/replay_scenarios.py',
        'team/evidence/o0-baseline-20261018/verify.py'})
    current = {name: sealed.sha(ROOT/name) for name in tools}
    expected = [f"{r['image']}-r{i}" for r in check.inventory(output/'images')['images'] for i in range(3)]
    require(selection['selected_runs'] == expected and len(expected) == 54, 'unexpected selected runs')
    require(campaign['status'] == 'O0_BASELINE_54_RUNS_PASS', 'historical campaign incomplete')
    rows = []
    for name in expected:
        image, replay = name.rsplit('-r', 1)
        folder = output/'runs'/name
        result = check.verify(output/'images'/image, folder, external=True)
        require(result == check.sealed.strict_json((folder/'check.json').read_bytes()), 'acceptance changed: '+name)
        saved = [r for r in campaign['results'] if r['run'] == name]
        require(len(saved) == 1 and saved[0]['status'] == 'PASS' and saved[0]['samples'] == result['samples'], 'campaign result changed')
        rows.append(dict(run=name, windows=len(result['samples']), replay=int(replay)))
    require(sum(r['windows'] for r in rows) == 648, 'wrong window count')
    require(current == {name: sealed.sha(ROOT/name) for name in tools}, 'current checker changed during recheck')
    record = dict(status='O0_CURRENT_CHECKER_54_RUNS_PASS', runs=rows, checked_windows=648,
                  historical_checker_sha256=historical, current_checker_sha256=current,
                  all_per_run_results_identical=True, new_hardware_execution=False,
                  hardware_source=check.HARDWARE_SOURCE, o0_complete=False, o1_accepted=False)
    (output/'result.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8', newline='\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(recheck(args.output)['status'])
