"""Versioned native replay of the bc9/e66 campaign plus dependency-admission v5.

Only archived bytes and newly replayed results qualify. Never launches an EMU.
The original fourteen-job INCOMPLETE verdict and all inputs remain immutable.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

HARDWARE = 'bc9e5ae469137a64b82744231acae9f9e3fe0359'
SOFTWARE = 'a51a7593bd742384f3aedef9dc2bf2358a612c62'
EMU = 'e66a8900eb09dc7f35acfe944c38386046fc8ef481e91792b2501f5cbd9679f5'
PINS = '76bf0fb7dfc86f6cf65885f5c43021f1a0ceab46e26bd5cbbf125b8888e06f5a'
INPUTS = '507e98c135d2533cd69fc9fb742093a5aea7501c2dc823e7a5f1b7db448acc61'
CAPSULES = {
    'core': ('merge-reg-20261023/campaign', 'c010608bea542cf5d59fe3a3884ac75960e0773174abf0f95a7f076bb768eb3a'),
    'partial': ('partial-dependency-admission-20261024', 'adcc339633b5aa311990552d60d8beb8692b69e06971974a6233426894a345d4'),
}
TARGETS = ('MULTI_INFLIGHT', 'TRIPLE_OVERLAP', 'FULL_STALL', 'KILL_P', 'KILL_R', 'PARTIAL_KILL')
JOBS = {'hello-vadd': 'HELLO_VADD_PASS', 'negative-vdot': 'EXPECTED_VDOT_HIGHBIT_REJECTION',
        **{f'functional-{i}': 'VDOT_MATRIX_SHARD_PASS' for i in range(8)},
        'control': 'O2_CONTROL_LEGACY_PASS', 'dense-batch128': 'O2_DENSE_ELASTIC_AND_WINDOWS_PASS'}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


class Capsule:
    """Verified, closed content store; paths are never extracted or executed."""
    def __init__(self, evidence, key):
        relative, identity = CAPSULES[key]
        self.base = Path(evidence) / relative
        raw = (self.base / 'manifest.json').read_bytes()
        require(digest(raw) == identity, 'unrecognized ' + key + ' manifest')
        self.manifest = json.loads(raw)
        m = self.manifest
        payloads = m.get('payloads') or [dict(path=p, **r) for p, r in m['files'].items()]
        for row in payloads:
            body = (self.base / row['path']).read_bytes()
            require(len(body) == row['bytes'] and digest(body) == row['sha256'], 'payload drift: ' + row['path'])
        shared = m.get('shared_archive') or m['shared_input_archive']
        require(sha(self.base / shared['path']) == shared['sha256'], 'shared archive drift')
        archive = 'files.zip' if key == 'partial' else 'campaign-files.zip'
        self.bodies = {}
        with ExitStack() as stack:
            stores = {name: stack.enter_context(zipfile.ZipFile(self.base / name))
                      for name in (archive, shared['path'])}
            original = json.loads(stores[archive].read('inventory.json'))
            rows = original if isinstance(original, list) else [dict(path=p, **r) for p, r in original.items()]
            require(len(rows) == m.get('capsule_paths', m.get('archived_paths')), 'inventory length differs')
            self.rows = {row['path']: row for row in rows}
            require(len(self.rows) == len(rows), 'duplicate inventory path')
            for row in rows:
                require(row['blob_archive'] in stores, 'unexpected blob archive')
                identity = (row['blob_archive'], row['blob'])
                if identity not in self.bodies:
                    self.bodies[identity] = stores[identity[0]].read(identity[1])
                body = self.bodies[identity]
                require(len(body) == row['bytes'] and digest(body) == row['sha256'], 'blob drift: ' + row['path'])

    def body(self, name):
        row = self.rows[name]
        return self.bodies[row['blob_archive'], row['blob']]

    def json(self, name):
        return json.loads(self.body(name))

    def native(self, prefixes):
        count = 0
        for name, row in self.rows.items():
            if any(name.startswith(prefix) for prefix in prefixes):
                require(sha(row['source']) == row['sha256'], 'native/archive mismatch: ' + name)
                count += 1
        require(count > 0, 'no native evidence bound')
        return count


def combine(core, partial):
    """Policy layer; callers must first authenticate and replay both inputs."""
    require(core.get('status') == 'O2_G3_OFFLINE_RECHECK_INCOMPLETE' and
            core.get('core_regression_pass') is True and core.get('supplements_pass') is True and
            core.get('normal_reference_recovery') is True and core.get('completed_only') is False and
            core.get('original_evidence_unchanged') is True and core.get('missing_jobs') == [] and
            core.get('missing_components') == [], 'core regression/recovery incomplete')
    require(core.get('build_source_commit') == HARDWARE and core.get('emu_sha256') == EMU and
            core.get('hardware_pins_sha256') == PINS, 'core hardware mismatch')
    rows = core.get('runs', [])
    require(len(rows) == len(JOBS) and {r['name']: r['status'] for r in rows} == JOBS,
            'missing, duplicate or failed core job')
    extra = core.get('supplement_audit', {})
    require(extra.get('status') == 'O2_SUPPLEMENT_OFFLINE_RECHECK_PASS' and
            extra.get('emu_sha256') == EMU and extra.get('hardware_pins_sha256') == PINS,
            'unqualified original supplements')
    records = extra.get('records', [])
    require(len(records) == 2 and {r['name'] for r in records} ==
            {'o2-diagnostic', 'o2-control-diagnostic'}, 'missing/duplicate original supplements')
    require(all(r.get('status') == 'O2_SUPPLEMENT_PASS' and r.get('observation_status') == 'O2_TRACE_PASS'
                and type(r.get('exit_code')) is int and r['exit_code'] == 0 for r in records),
            'original supplement failed')
    require(partial.get('status') == 'PARTIAL_V5_TARGET_PASS' and partial.get('architectural_pass') is True
            and partial.get('target_covered') is True and type(partial.get('target_windows')) is int
            and partial['target_windows'] > 0 and partial.get('checked_register_bytes') == 8192
            and partial.get('campaign_acceptance') is False, 'directed target/architecture incomplete')
    sources = {key: [] for key in TARGETS}
    for row in rows + records:
        if row['name'] == 'negative-vdot':
            continue  # Fault-injection partial traces never contribute coverage.
        require(row.get('observation_status') == 'O2_TRACE_PASS', 'unqualified normal trace')
        for key in TARGETS:
            value = row.get('observation_counts', {}).get(key, 0)
            require(type(value) is int and value >= 0, 'invalid original count')
            if value:
                sources[key].append(dict(name=row['name'], count=value, campaign='core+original-supplements'))
    original = core['suite_coverage']
    expected = {k: [dict(name=r['name'], count=r['count']) for r in v] for k, v in sources.items()}
    require(original == dict(required=list(TARGETS), sources=expected, complete=False, missing=['PARTIAL_KILL']),
            'original coverage disagrees with qualified records')
    # v5 supplies only the missing obligation, not additional counts for all targets.
    require(type(partial.get('counts', {}).get('PARTIAL_KILL')) is int and
            partial['counts']['PARTIAL_KILL'] == partial['target_windows'] and
            partial['counts'].get('COMMIT') == 112, 'directed coverage/retirement mismatch')
    sources['PARTIAL_KILL'].append(dict(name='partial-v5', count=partial['target_windows'], campaign='directed-v5'))
    return dict(status='O2_G3_SUPPLEMENTED_RECHECK_PASS', contract='bc9-e66-g3-plus-partial-v5-v1',
                g3_complete=True, original_verdict=core['status'], coverage_sources=sources,
                required=list(TARGETS), missing=[], reused_hardware_runs=15, new_emu_runs=0,
                performance_measured=False, defaults_changed=False, t17_complete=False)


def output_guard(output, protected):
    require(output.is_absolute() and not output.exists() and not output.is_symlink(), 'output must be absolute and new')
    resolved = output.resolve()
    require(all(not resolved.is_relative_to(p.resolve()) and not p.resolve().is_relative_to(resolved)
                for p in protected), 'output overlaps protected input')


def audit(evidence, output):
    require(sys.platform == 'linux', 'native Linux required for original bound replays')
    core = Capsule(evidence, 'core')
    partial = Capsule(evidence, 'partial')
    receipt = partial.json('run/receipt.json')
    old = json.loads((core.base / 'recheck-result.json').read_bytes())
    campaign = Path(old['campaign'])
    hardware_root = Path(receipt['emu']).parents[1]
    run = Path(partial.rows['run/receipt.json']['source']).parent
    driver = next(Path(p) for p in receipt['files'] if p.endswith('/partial_kill_v5/run.py'))
    software_root = driver.parents[5]
    original_auditor = hardware_root / 'team/optimizations/o2/fullcore/recheck.py'
    output_guard(output, [Path(evidence), Path(__file__).resolve().parents[5], hardware_root.parent, run.parent])
    output.mkdir(parents=True)
    stable = {str(Path(__file__).resolve()): sha(__file__)}
    save(output / 'audit-source.json', dict(source=str(Path(__file__).resolve()), sha256=sha(__file__)))
    (output / 'audit.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='O2_G3_SUPPLEMENTED_RECHECK_FAILED', g3_complete=False, new_emu_runs=0)
    try:
        require(core.manifest['source_commit'] == HARDWARE and partial.manifest['hardware_source'] == HARDWARE
                and receipt['source_commit'] == SOFTWARE and partial.manifest['source_commit'] == SOFTWARE
                and core.manifest['emu_sha256'] == partial.manifest['emu_sha256'] == EMU,
                'capsule hardware/software identity mismatch')
        preflight = core.json('runs/core-01/preflight.json')
        require(preflight['emu_sha256'] == EMU and preflight['hardware_pins_sha256'] == PINS and
                preflight['input_contract_sha256'] == INPUTS, 'core identity mismatch')
        require(receipt['files'][receipt['emu']] == EMU and
                receipt['files'][str(hardware_root.parent / 'build-01/hardware-inputs.json')] == PINS and
                receipt['files'][str(hardware_root.parent / 'inputs/input-contract-v1.json')] == INPUTS,
                'directed identity mismatch')
        for name in (receipt['reference'], receipt['flash']):
            require(receipt['files'][name] == preflight['input_files'][name], 'normal reference/flash mismatch')
        for root, revision in ((hardware_root, HARDWARE), (software_root, SOFTWARE)):
            require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == revision,
                    'native source revision mismatch')
        stable.update(preflight['driver_files'])
        stable.update(old['new_checker_files'])
        stable.update(receipt['files'])
        require(str(original_auditor) in stable, 'unbound original auditor')
        for name, expected in stable.items():
            require(sha(name) == expected, 'native checker/input drift: ' + name)
        before = dict(core_paths=core.native(('runs/core-01/', 'runs/supplements-01/')),
                      directed_paths=partial.native(('run/',)))
        save(output / 'bindings.json', dict(capsules=CAPSULES, hardware=HARDWARE, emu=EMU,
                                           native=before, checker_and_input_files=stable))
        tool_bin = receipt['commands'][0]['environment']['PATH'].split(':')[0]
        env = dict(PATH=tool_bin + ':/usr/bin:/bin', LANG='C.UTF-8', LC_ALL='C.UTF-8', TZ='UTC',
                   TEAM_XS_ENV_ROOT=str(hardware_root.parent / 'inputs/xs-env'))
        steps = [
            ('core', ['/usr/bin/python3', '-B', str(original_auditor), '--campaign', str(campaign),
                      '--supplements', str(campaign.parent / 'supplements-01'), '--output', str(output / 'core-replay')], hardware_root),
            ('partial', ['/usr/bin/python3', '-B', str(driver), '--action', 'check', '--output', str(run)], software_root),
        ]
        for name, command, cwd in steps:
            started = datetime.now(timezone.utc).isoformat()
            with (output / (name + '.stdout')).open('xb') as stdout, (output / (name + '.stderr')).open('xb') as stderr:
                completed = subprocess.run(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=1800)
            save(output / (name + '-command.json'), dict(command=command, cwd=str(cwd), environment=env,
                 started=started, finished=datetime.now(timezone.utc).isoformat(), exit_code=completed.returncode))
            require(completed.returncode == (1 if name == 'core' else 0), 'unexpected replay exit: ' + name)
        replay = json.loads((output / 'core-replay/result.json').read_bytes())
        directed = json.loads((output / 'partial.stdout').read_bytes())
        require(directed == {k: v for k, v in partial.json('run/result.json').items() if k != 'diagnosis'},
                'directed replay differs from sealed result')
        for name, expected in stable.items():
            require(sha(name) == expected, 'input changed during replay: ' + name)
        require(before == dict(core_paths=core.native(('runs/core-01/', 'runs/supplements-01/')),
                               directed_paths=partial.native(('run/',))), 'source set changed')
        result = combine(replay, directed)
        result.update(hardware_source=HARDWARE, emu_sha256=EMU, directed_source=SOFTWARE,
                      original_evidence_unchanged=True, native_inputs_verified=True)
    except Exception as exc:
        result['error'] = repr(exc)
    result['finished'] = datetime.now(timezone.utc).isoformat()
    save(output / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = audit(args.evidence.resolve(), args.output)
    print(json.dumps(value))
    raise SystemExit(0 if value['g3_complete'] else 1)
