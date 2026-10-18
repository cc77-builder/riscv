"""Build regeneration and immutable runtime pins, exercised with optimization on."""
import copy
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import matrix_check as check


class RuntimeGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        evidence = check.ROOT/'team/evidence/o0-progress-20261017'
        bundle = evidence/'matrix-images.tar.gz'
        if hashlib.sha256(bundle.read_bytes()).hexdigest() != '9a15c18502ac745aec60a6c29ddcfe7e6bced58d6026156c2034294add5398de':
            raise ValueError('compiled test fixture changed')
        with tarfile.open(bundle) as archive:
            for entry in archive.getmembers():
                if entry.isfile() and entry.name.startswith(('source/', 'matrix-d0-s00/')):
                    dest = cls.root/entry.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(archive.extractfile(entry).read())
        (cls.root/'result.json').write_bytes((evidence/'matrix-build.json').read_bytes())
        cls.build = cls.root/'matrix-d0-s00'

    def receipt(self):
        roles = {'emu': '/fixture/emu', 'reference': '/fixture/ref', 'flash': '/fixture/flash',
                 'image': '/fixture/build/vdot-perf.bin'}
        return dict(exit_code=0, single_core=True, emu_threads=1, image=self.build.name, replay=0,
                    hardware_source=check.HARDWARE_SOURCE, fu_latency=3, build='/fixture/build',
                    command=['timeout', '120m', roles['emu'], '-i', roles['image'], '--diff='+roles['reference'],
                             '--flash='+roles['flash'], '--max-cycles=2000000', '--ram-size=128MB', '--seed=1'],
                    files={name: check.CHECK.sha(self.build/'vdot-perf.bin') if role == 'image' else check.RUNTIME_SHA[role]
                           for role, name in roles.items()},
                    raw_sha256={'stdout.log': 'a'*64, 'stderr.log': 'b'*64})

    def test_actual_frozen_build_regenerates(self):
        result = check.verify_build(self.build)
        self.assertEqual(result['suite'], 'o0-matrix')
        self.assertEqual(len(result['plan']), 12)

    def test_correct_runtime_binding(self):
        self.assertEqual(set(check.validate_runtime(self.receipt(), self.build, True)), {'emu', 'reference', 'flash', 'image'})

    def test_wrong_binary_cannot_supply_its_own_runtime_hash(self):
        for role in ('emu', 'reference', 'flash', 'image'):
            with self.subTest(role=role):
                receipt = self.receipt()
                path = check.CHECK.runtime_roles(receipt['command'])[role]
                receipt['files'][path] = '0'*64
                with self.assertRaisesRegex(ValueError, 'runtime digest mismatch'):
                    check.validate_runtime(receipt, self.build, True)

    def test_bad_runtime_identity_or_failure(self):
        for field, value in [('exit_code', True), ('exit_code', 1), ('single_core', False), ('emu_threads', True),
                             ('image', 'matrix-d0-s01'), ('replay', True), ('replay', 3), ('fu_latency', 2),
                             ('hardware_source', '0'*40), ('verification_error', 'changed')]:
            with self.subTest(field=field, value=value):
                receipt = self.receipt()
                receipt[field] = value
                with self.assertRaises(ValueError):
                    check.validate_runtime(receipt, self.build, True)

    def test_seed_limit_and_duplicate_options(self):
        for before, after in [('--seed=1', '--seed=2'), ('--max-cycles=2000000', '--max-cycles=1'),
                              ('--ram-size=128MB', '--ram-size=256MB')]:
            with self.subTest(after=after):
                receipt = self.receipt()
                receipt['command'][receipt['command'].index(before)] = after
                with self.assertRaises(ValueError):
                    check.validate_runtime(receipt, self.build, True)
        receipt = self.receipt()
        receipt['command'].append('--seed=1')
        with self.assertRaises(ValueError):
            check.validate_runtime(receipt, self.build, True)

    def test_missing_runtime_or_raw_binding(self):
        for field in ('files', 'raw_sha256'):
            receipt = self.receipt()
            receipt[field].pop(next(iter(receipt[field])))
            with self.subTest(field=field), self.assertRaises(ValueError):
                check.validate_runtime(receipt, self.build, True)

    def test_mutated_source_is_rejected_before_regeneration(self):
        source = self.root/'source/team/optimizations/o0/generate_matrix.py'
        original = source.read_bytes()
        try:
            source.write_bytes(original+b'\n# drift\n')
            with self.assertRaisesRegex(ValueError, 'build source changed'):
                check.verify_build(self.build)
        finally:
            source.write_bytes(original)

    def test_rewritten_build_summary_is_not_trusted(self):
        path = self.root/'result.json'
        original = path.read_bytes()
        receipt = copy.deepcopy(json.loads(original))
        receipt['images'] = receipt['images'][:-1]
        try:
            path.write_text(json.dumps(receipt), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'unrecognized matrix build receipt'):
                check.inventory(self.root)
        finally:
            path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
