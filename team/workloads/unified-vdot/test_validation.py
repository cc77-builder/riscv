"""Mutation tests for acceptance gates; archived runs are not new DUT runs."""
import ast
import copy
import ctypes
import importlib.util
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import check
import reference

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE = ROOT/'team/evidence/unified-vdot-20261017/archive'
spec = importlib.util.spec_from_file_location('unified_suite', HERE/'run-suite.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


class ProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        with tarfile.open(ARCHIVE/'测试镜像与构建快照.tar.gz') as archive:
            for member in archive:
                if member.name.startswith('ours/performance-d0-s00/') and member.isfile():
                    target = cls.root/member.name
                    if not target.resolve().is_relative_to(cls.root.resolve()):
                        raise ValueError('unsafe archive path')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
        cls.build = cls.root/'ours/performance-d0-s00'
        cls.run_dir = ARCHIVE/'验证证据/ours/performance-d0-s00'
        cls.receipt = json.loads((cls.run_dir/'result.json').read_text())
        cls.build_record = json.loads((cls.build/'build.json').read_text())

    def verdict(self, receipt=None, record=None):
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path == self.run_dir/'result.json' and receipt is not None:
                return json.dumps(receipt)
            if path == self.build/'build.json' and record is not None:
                return json.dumps(record)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            return check.verify(self.build, self.run_dir, self.receipt['files'])

    def test_real_archive_positive(self):
        self.assertEqual(self.verdict()['status'], 'PASS')

    def test_missing_or_invalid_runtime_binding(self):
        for key, value in [('files', {}), ('raw_sha256', {}),
                           ('command', ['not-an-emu']), ('single_core', False),
                           ('emu_threads', 999), ('verification_error', 'changed')]:
            with self.subTest(key=key):
                receipt = dict(self.receipt, **{key: value})
                with self.assertRaises(ValueError):
                    self.verdict(receipt=receipt)

    def test_seed_and_duplicate_roles(self):
        for args in [[], ['--seed=2'], ['--seed=1', '--diff=/another']]:
            receipt = copy.deepcopy(self.receipt)
            receipt['command'] = [x for x in receipt['command'] if not x.startswith('--seed=')] + args
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.verdict(receipt=receipt)

    def test_incomplete_or_failed_build(self):
        for key, value in [('artifacts', {}), ('exit_code', 1), ('source', 'wrong'),
                           ('am_revision', 'wrong'), ('verification_error', 'changed')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verdict(record=dict(self.build_record, **{key: value}))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.images = []
        for stage, dataset, shards in [('smoke', 0, 1), ('functional', 0, 3)] + [('performance', i, 4) for i in range(3)]:
            for shard in range(shards):
                name = f'{stage}-d{dataset}-s{shard:02d}'
                path = self.root/name
                (path/'data').mkdir(parents=True)
                manifest = dict(suite=stage, dataset=dataset, shard=shard, shards=shards,
                                variant='ours', shared_stream=True)
                (path/'data/manifest.json').write_text(json.dumps(manifest))
                self.images.append(dict(name=name, suite=stage, dataset=dataset, shard=shard,
                                        path=str(path), replays=1))

    def test_complete(self):
        suite.validate_inventory(self.images, 'ours')

    def test_missing_functional_shards(self):
        with self.assertRaisesRegex(ValueError, 'inventory'):
            suite.validate_inventory(self.images[:2]+self.images[4:], 'ours')

    def test_duplicate_and_replay(self):
        bad = copy.deepcopy(self.images)
        bad[2] = bad[1]
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            suite.validate_inventory(bad, 'ours')
        bad = copy.deepcopy(self.images)
        bad[1]['replays'] = 0
        with self.assertRaisesRegex(ValueError, 'replay'):
            suite.validate_inventory(bad, 'ours')

    def test_manifest_identity(self):
        path = Path(self.images[1]['path'])/'data/manifest.json'
        for key, value in [('variant', 'jade'), ('shards', 1), ('shard', 2), ('shared_stream', False)]:
            original = json.loads(path.read_text())
            path.write_text(json.dumps(dict(original, **{key: value})))
            with self.subTest(key=key), self.assertRaises(ValueError):
                suite.validate_inventory(self.images, 'ours')
            path.write_text(json.dumps(original))


class OptimizedReferenceTests(unittest.TestCase):
    def run_state_check(self, fault=None):
        # Execute the actual nested checker compiled with optimize=2, using a
        # small ABI fake. This exercises state validation without claiming NEMU.
        tree = ast.parse((HERE/'reference.py').read_text())
        run = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'run')
        layout = reference.LAYOUT
        def get(b, k): return struct.unpack_from('<Q', b, layout[k])[0]
        def put(b, k, v): struct.pack_into('<Q', b, layout[k], v)
        class Native:
            def difftest_regcpy(self, buf, direction):
                self.state = bytearray(ctypes.string_at(buf, 1400))
            def difftest_exec(self, count):
                put(self.state, 'pc', get(self.state, 'pc')+4)
                put(self.state, 'mstatus', 0x600)
        native = Native()
        def read():
            state = bytearray(native.state)
            if fault == 'trap': put(state, 'mcause', 2)
            if fault == 'full128': state[815] ^= 0x80
            if fault == 'csr': put(state, 'vl', 7)
            if fault == 'gpr': state[8] ^= 1
            if fault == 'status': put(state, 'mstatus', 0)
            return state
        env = dict(initial=bytes(1400), struct=struct, C=ctypes, lib=native, read=read,
                   get=get, put=put, blocks={'known': (0, 1)}, require=check.require)
        exec(compile(ast.Module(body=[run], type_ignores=[]), 'actual-reference-check', 'exec', optimize=2), env)
        env['run']('known', [bytes(16)]*32, 0, 3, 1, [bytes(16)]*32, set())

    def test_valid_state(self):
        self.run_state_check()

    def test_wrong_state_rejected_under_oo(self):
        for fault in ('trap', 'full128', 'csr', 'gpr', 'status'):
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                self.run_state_check(fault)


if __name__ == '__main__':
    unittest.main()
