"""Exercise the actual spawn boundary without launching an EMU or compiler."""
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import merged_screen as m


BASE_ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC'}
POLLUTED = dict(PATH='/untrusted/bin', LD_PRELOAD='/untracked.so',
                LD_LIBRARY_PATH='/untracked/lib', CPATH='/untracked/include',
                PYTHONPATH='/untracked/python', MAKEFILES='/untracked/make',
                XS_NEGATIVE_VECTOR_TARGET='other')


class ExplicitEnvironment(unittest.TestCase):
    def test_fixture_lookup_and_every_spawn_use_recorded_clean_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / m.NEGATIVE_SOURCE
            source.parent.mkdir(parents=True)
            source.write_bytes(b'fixture source for mocked compiler')
            out = root / 'fixture'
            cfg = {'reference': '/verified/normal.so'}
            calls = []

            def popen(argv, **kwargs):
                calls.append((list(argv), dict(kwargs['env'])))
                receipt = m.read_json(Path(kwargs['stdout'].name).parent / 'command.json')
                self.assertEqual(receipt['environment_contract'], m.ENVIRONMENT_CONTRACT)
                self.assertEqual(receipt['environment'], kwargs['env'])
                self.assertEqual(kwargs['env'], BASE_ENV)
                if '-o' in argv:
                    Path(argv[argv.index('-o') + 1]).write_bytes(b'mocked binary')
                if '-d' in argv:
                    kwargs['stdout'].write(b'Shared library: [/verified/normal.so]\n')
                return SimpleNamespace(pid=123, wait=lambda **unused: 0)

            with patch.dict(os.environ, POLLUTED), patch.object(m, 'NEGATIVE_SHA', m.g.sha(source)), \
                    patch.object(m.shutil, 'which', side_effect=lambda name, path: '/usr/bin/' + name) as which, \
                    patch.object(m.f.subprocess, 'Popen', side_effect=popen):
                fixture = m.build_negative(root, cfg, out)
            self.assertEqual(which.call_args_list[0].kwargs, {'path': BASE_ENV['PATH']})
            self.assertEqual(which.call_args_list[1].kwargs, {'path': BASE_ENV['PATH']})
            self.assertEqual(len(calls), 3)
            self.assertEqual(fixture['environment_contract'], m.ENVIRONMENT_CONTRACT)
            self.assertEqual(fixture['environment'], BASE_ENV)
            for step in ('compiler', 'compile', 'linkage'):
                receipt = m.read_json(out / step / 'command.json')
                self.assertTrue(receipt['process_started'])
                self.assertEqual(receipt['exit_code'], 0)
                self.assertEqual(receipt['environment'], BASE_ENV)

    def test_emu_negative_and_normal_spawns_are_isolated_and_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'build').mkdir()
            for name in m.AUX:
                (root / 'build' / name).write_bytes(b'auxiliary fixture')
            image_root = root / 'image'
            (image_root / 'data').mkdir(parents=True)
            (image_root / 'build.json').write_text('{}')
            (image_root / 'data/manifest.json').write_text(json.dumps({'plan': [], 'rows': []}))
            (image_root / 'vdot-perf.bin').write_bytes(b'image fixture')
            image = dict(path=str(image_root), image_sha256=m.g.sha(image_root / 'vdot-perf.bin'),
                         variant='s2', shard=7, suite='smoke', dataset=0)
            cfg = dict(hardware_source=str(root), reference='/normal.so', flash='/flash.bin')
            negative = dict(binary='/negative.so', negative_sha256='fixture-hash')
            captures = []

            def popen(argv, **kwargs):
                expected = dict(BASE_ENV)
                is_negative = '--diff=/negative.so' in argv
                if is_negative:
                    expected['XS_NEGATIVE_VECTOR_TARGET'] = 'vdot'
                self.assertEqual(kwargs['env'], expected)
                receipt = m.read_json(Path(kwargs['stdout'].name).parent / 'result.json')
                self.assertEqual(receipt['environment_contract'], m.ENVIRONMENT_CONTRACT)
                self.assertEqual(receipt['environment'], expected)
                captures.append(dict(kwargs['env']))
                return SimpleNamespace(pid=123 + len(captures), wait=lambda **unused: int(is_negative))

            with patch.dict(os.environ, POLLUTED), \
                    patch.object(m.g, 'verify_build'), patch.object(m, 'validate_selection'), \
                    patch.object(m, 'verify_files'), \
                    patch.object(m.g, 'load', return_value=SimpleNamespace(validate_runtime=lambda *args: None)), \
                    patch.object(m, 'negative_check', return_value={'mocked': True}), \
                    patch.object(m.f, 'verify_runtime', return_value=({'samples': []}, {})), \
                    patch.object(m.f.subprocess, 'Popen', side_effect=popen):
                rejected = m.execute(root, cfg, image, root / 'negative-run', {}, negative=negative)
                recovered = m.execute(root, cfg, image, root / 'normal-run', {})
            self.assertEqual(rejected['status'], m.NEGATIVE_PASS)
            self.assertEqual(recovered['status'], m.NORMAL_PASS)
            self.assertEqual(captures[1], BASE_ENV)
            self.assertNotIn('XS_NEGATIVE_VECTOR_TARGET', recovered['environment'])
            self.assertEqual(rejected['environment'], captures[0])
            self.assertEqual(recovered['environment'], captures[1])

    def test_failed_fixture_spawn_preserves_environment_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict(os.environ, POLLUTED), \
                    patch.object(m.f.subprocess, 'Popen', side_effect=OSError('test launch failure')):
                with self.assertRaisesRegex(OSError, 'launch failure'):
                    m.environment_command(['/usr/bin/gcc', '--version'], root, root / 'command')
            receipt = m.read_json(root / 'command/command.json')
            self.assertFalse(receipt['process_started'])
            self.assertIsNone(receipt['exit_code'])
            self.assertEqual(receipt['environment_contract'], m.ENVIRONMENT_CONTRACT)
            self.assertEqual(receipt['environment'], BASE_ENV)


if __name__ == '__main__':
    unittest.main()
