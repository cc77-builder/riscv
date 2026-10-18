#!/usr/bin/env python3
"""Authenticate and recompute the frozen campaign; no EMU or reference is run.

Run from this repository using Python 3.12 and a fresh --output directory.
The reviewed checker sources and independent parent corpus must still match.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVES = {
    'validation.tar.gz': 'ebfb0b7302017699c50a106988944be8038a9c4d8cbdb68f67bbfc3889d84a2c',
    'compiler-inputs.tar.gz': 'b324c3ca1ffd460202542e09929b9ce4837287392ab86e891601fbe10f09a64d',
    'review-inputs.tar.gz': '9a0e066da38b5a66b641cd6c29ccb71119e51d186f8bf97e5324e243e04320e9',
}
SOURCE = '7c4d9c4306703ce95a1aa20ac8d070327f7c7a852cb03f279f30c4799f45bb9d'
EMU = 'fd401bcc1538bdfc01c2c1f6c2dde024417af0182f08905d1853736475533811'
REFERENCE = 'e8c9c9be7d798a348a0f8c5ad3a4c601c27511a1967ca3c4cc0af576233f52a1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def extract(name, destination):
    expected = read(HERE/(name+'.json'))
    require(sha(HERE/name) == ARCHIVES[name] == expected['archive_sha256'], 'archive changed: '+name)
    destination.mkdir()
    actual = {}
    total = 0
    with tarfile.open(HERE/name, 'r:gz') as source:
        for member in source:
            path = PurePosixPath(member.name)
            require(member.isfile() and not path.is_absolute() and '..' not in path.parts
                    and str(path) == member.name and '\\' not in member.name
                    and ':' not in member.name and member.name not in actual,
                    'unsafe/duplicate member: '+member.name)
            total += member.size
            require(total < 1024**3, 'archive exceeds extraction bound')
            target = destination/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.extractfile(member).read())
            actual[member.name] = sha(target)
    require(actual == expected['files'], 'archive inventory differs: '+name)
    return actual


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    raw, compiler, review = (output/n for n in ('raw', 'compiler', 'review'))
    counts = {}
    for name, target in zip(ARCHIVES, (raw, compiler, review)):
        counts[name] = len(extract(name, target))
    # Authenticate executable checkers before importing them. These are exactly
    # the sources used for the recorded host tests and actual CPU campaign.
    for name, digest in read(HERE/'review-inputs.tar.gz.json')['files'].items():
        if name.startswith('team/') and name.endswith('.py'):
            require(sha(ROOT/name) == digest, 'reviewed checker changed: '+name)
    build = raw/'core-build'
    for name in ('build.status', 'split-build.status'):
        require((build/name).read_text().strip() == 'exit_code=0', 'failed build status')
    require((build/'launch.status').read_text().strip() == '0', 'failed launch status')
    require('CORE_BASELINE_BUILD_PASS' in (build/'build.log').read_text()
            and 'CORE_SPLIT_BUILD_PASS' in (build/'split-build.log').read_text(), 'build incomplete')
    require((build/'emu.sha256').read_text().split()[0] == EMU, 'wrong EMU')
    binding = read(build/'source-binding.json')
    profile = read(build/'compile-profile.json')
    require(binding == read(compiler/'source-binding.json'), 'compiler binding differs')
    require(sha(HERE/'source-pack.json') == binding['source_pack_sha256']
            == profile['source_pack_sha256'] == SOURCE, 'source pack differs')
    require(len(binding['physical_root_sha256']) == 437 and len(binding['modules']) == 126,
            'compiler input inventory differs')
    require(all(sha(compiler/n) == h for n, h in binding['physical_root_sha256'].items()),
            'physical compiler input differs')
    require(profile['rtl_manifest_sha256'] == sha(build/'rtl.sha256')
            and (profile['config'], profile['num_cores'], profile['emu_threads'])
            == ('MinimalConfig', 1, 1), 'compile profile differs')
    env = (build/'environment.txt').read_text().splitlines()
    require(all(s in env for s in ('VDOT_O1_TRACE=1', 'VDOT_O1_HANDOFF=1',
                'VDOT_T14_FUSED_INPUT=1', 'VDOT_T12_TRACE=0', 'VDOT_T13_TRACE=0')), 'wrong flags')
    rtl = {name: digest for digest, name in
           (line.split() for line in (build/'rtl.sha256').read_text().splitlines())}
    for path in (HERE/'instrumented-rtl').glob('*.sv'):
        require(sha(path) == rtl['build/rtl/'+path.name], 'RTL snapshot differs')
    runs = raw/'runs-01'
    for phase in ('before', 'after'):
        receipt = read(runs/(phase+'-0.log'))
        require(receipt == dict(status='CORE_SOURCE_BINDING_PASS', root_inputs=437,
                               modules=126, source_pack_sha256=SOURCE), 'source verification differs')
        require(read(runs/('reference-'+phase+'.json'))['binary_sha256'] == REFERENCE,
                'reference verification differs')
    pins = read(runs/'inputs.json')
    require([h for p, h in pins.items() if p.endswith('/build/emu')] == [EMU], 'runtime EMU differs')
    for path, digest in pins.items():
        if '/riscv/team/' in path:
            require(sha(ROOT/('team/'+path.split('/riscv/team/', 1)[1])) == digest, 'runtime checker differs')
        elif '/core-build/' in path:
            require(sha(build/path.rsplit('/', 1)[1]) == digest, 'runtime build receipt differs')
    parent = ROOT/'team/evidence/t10-t11-fullcore-20261013/parent'
    require(all(sha(parent/n) == h for n, h in read(runs/'matrix-union.json')['parent'].items()),
            'independent parent corpus differs')
    host = read(raw/'host-tests.json')
    require(host['exit_code'] == 0 and sha(raw/'host-tests.log') == host['log_sha256']
            and 'Ran 72 tests' in (raw/'host-tests.log').read_text(), 'host receipt differs')
    for name, digest in host['files'].items():
        require(sha(ROOT/'team/optimizations/o1'/name) == digest, 'host source differs')
    sys.path.insert(0, str(ROOT/'team/optimizations/o1'))
    from recheck_extended_run import recheck
    from audit_extended_negatives import check
    result = recheck(runs)
    require(result == read(raw/'recheck.json') == read(HERE/'recheck.json'), 'recomputed campaign differs')
    negative = check(runs/'control/stderr.log', runs/'calibration/stderr.log',
                     runs/'images/calibration', output/'negatives-rechecked.json')
    require(negative == read(raw/'negatives.json') == read(HERE/'negatives.json'), 'mutation results differ')
    receipt = dict(status='O1_EXTENDED_ARCHIVE_RECHECK_PASS', archives=ARCHIVES,
                   archive_files=counts, emu_sha256=EMU, source_pack_sha256=SOURCE,
                   archived_cpu_runs=13, new_cpu_runs=0, host_tests=72,
                   real_log_mutations=negative['count'], default_o1=False, performance_ab=False)
    (output/'archive-recheck.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2, sort_keys=True))
