"""Fail-closed acceptance for the frozen 18-image O0 corpus and II4 baseline.

Build hashes are pinned outside the mutable run receipt. The existing T13 checker
still verifies the exact retirement path, all CSR boundaries and program guards.
"""
import importlib.util
import json
from pathlib import Path
import re
import tempfile

import compile_matrix
import replay_archive as sealed

ROOT = Path(__file__).resolve().parents[3]
BUILD_SHA = '1122b8a1a7762fbcddc44e20d5f6007da4201313eb8a30f71389ef891c63e82d'
RUNTIME_SHA = {
    'emu': '3e41b191bc82c17bfed5dbcc1df7a69f19bc9f94b56489e085035a19e77d96d1',
    'reference': 'e8c9c9be7d798a348a0f8c5ad3a4c601c27511a1967ca3c4cc0af576233f52a1',
    'flash': 'a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994',
}
HARDWARE_SOURCE = 'd3706f0b86ecfdfbb24cb34cbcf2c18a0314f7f9'
require = sealed.require


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load('o0_matrix_shared_checker', ROOT/'team/workloads/unified-vdot/check.py')


def inventory(images):
    raw = (images/'result.json').read_bytes()
    require(sealed.sha256(raw) == BUILD_SHA, 'unrecognized matrix build receipt')
    receipt = sealed.strict_json(raw)
    names = [row['image'] for row in receipt['images']]
    require(sorted(names) == [f'matrix-d{d}-s{s:02d}' for d in range(3) for s in range(6)], 'matrix inventory mismatch')
    for name, digest in receipt['source_sha256'].items():
        require(CHECK.sha(sealed.contained(images/'source', name)) == digest, 'build source changed: '+name)
    return receipt


def verify_build(build):
    receipt = inventory(build.parent)
    candidates = [r for r in receipt['images'] if r['image'] == build.name]
    require(len(candidates) == 1, 'unexpected matrix image')
    expected = candidates[0]
    require(sealed.strict_json((build/'build.json').read_bytes()) == expected, 'image build receipt changed')
    for name, digest in expected['sha256'].items():
        require(CHECK.sha(sealed.contained(build, name)) == digest, 'compiled artifact changed: '+name)
    manifest = sealed.strict_json((build/'data/manifest.json').read_bytes())
    generator = load('o0_frozen_matrix_generator', build.parent/'source/team/optimizations/o0/generate_matrix.py')
    with tempfile.TemporaryDirectory(prefix='o0-matrix-regenerate-') as temp:
        fresh = generator.generate(Path(temp)/'data', manifest['dataset'], manifest['shard'], manifest['shards'])
        require(fresh == manifest, 'matrix source regeneration mismatch')
        for name, digest in manifest['files'].items():
            require(CHECK.sha(build/'data'/name) == digest, 'generated matrix file changed')
    require(compile_matrix.check_elf(CHECK, build/'vdot-perf.elf', manifest) == expected['static_kernel_checks'],
            'static kernel check differs')
    return manifest


def validate_runtime(receipt, build, external=False):
    require(type(receipt['exit_code']) is int and receipt['exit_code'] == 0, 'runtime failure')
    require(not receipt.get('verification_error'), 'runtime inputs changed')
    require(receipt['single_core'] is True and type(receipt['emu_threads']) is int and receipt['emu_threads'] == 1,
            'core/thread configuration mismatch')
    require(receipt['image'] == build.name and type(receipt['replay']) is int and 0 <= receipt['replay'] < 3,
            'wrong image/replay identity')
    require(receipt['hardware_source'] == HARDWARE_SOURCE and receipt['fu_latency'] == 3, 'wrong baseline binding')
    roles = CHECK.runtime_roles(receipt['command'])
    require(receipt['command'][:2] == ['timeout', '120m'], 'runner prefix mismatch')
    require(sealed.option(receipt['command'], '--max-cycles') == '2000000', 'cycle limit mismatch')
    require(roles['image'] == receipt['build'] + '/vdot-perf.bin', 'runtime build/image mismatch')
    require(set(receipt['files']) == set(roles.values()), 'incomplete runtime binding')
    for role, name in roles.items():
        digest = CHECK.sha(build/'vdot-perf.bin') if role == 'image' else RUNTIME_SHA[role]
        require(receipt['files'][name] == digest, 'runtime digest mismatch: '+role)
        if not external:
            require(CHECK.sha(Path(name)) == digest, 'live runtime input changed: '+role)
    require(set(receipt['raw_sha256']) == {'stdout.log', 'stderr.log'}, 'incomplete raw streams')
    return roles


def verify(build, run, *, external=False):
    manifest = verify_build(build)
    receipt = sealed.strict_json((run/'result.json').read_bytes())
    roles = validate_runtime(receipt, build, external)
    for name, digest in receipt['raw_sha256'].items():
        require(CHECK.sha(run/name) == digest, 'raw stream changed: '+name)
    stdout, stderr = CHECK.read_text(run/'stdout.log'), CHECK.read_text(run/'stderr.log')
    for banner in ('The first instruction of core 0 has commited. Difftest enabled.',
                   'The reference model is '+roles['reference'], 'The image is '+roles['image']):
        require(banner in stdout, 'missing runtime banner: '+banner)
    require(not re.search(r'Assertion.*failed|different at pc|DIFFTEST FAIL|HIT BAD TRAP|T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)',
                          stdout + stderr), 'runtime failure marker')
    results = CHECK.trace_windows(CHECK.parse_events(stderr), manifest, CHECK.elf_kernels(build/'vdot-perf.elf'))
    CHECK.check_uart(stdout, manifest, results)
    analyzer = sealed.load_diagnostics(ROOT)
    diagnosis = analyzer.analyze(stderr, fu_latency=3)
    return dict(status='O0_MATRIX_BASELINE_RUN_PASS', hardware_source=HARDWARE_SOURCE,
                build_receipt_sha256=BUILD_SHA, raw_sha256=receipt['raw_sha256'],
                samples=results, diagnosis=diagnosis,
                scope='Frozen II4 baseline, exact full-state guards, complete 256-dot retirement and fenced CSR windows')
