"""Current and historical replay bind complete, immutable checker dependencies."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

import recheck
import run_suite


class ReplayBindings(unittest.TestCase):
    def test_live_git_inventory_rejects_missing_or_substituted_helpers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'core.autocrlf', 'false'], check=True)
            names = recheck.DRIVERS + recheck.LIVE_DEPENDENCIES
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'import live_inputs\n' if name == recheck.DRIVERS[0] else b'# pinned\n')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Replay Test', '-c',
                            'user.email=replay@example.invalid', 'commit', '-qm', 'pin'], check=True)
            revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
            recorded = {str(root/name): recheck.sha(root/name) for name in names}
            self.assertEqual(run_suite.verify_committed_drivers(recorded, root), revision)
            for helper in recheck.LIVE_DEPENDENCIES:
                (root/helper).write_bytes(b'# later checkout bytes\n')
            current = {str(root/name): recheck.sha(root/name) for name in names}
            with self.assertRaisesRegex(ValueError, 'committed source before execution'):
                run_suite.verify_committed_drivers(current, root)
            blobs = recheck.bind_original_drivers(root, revision, recorded)
            self.assertEqual(len(blobs), 10)
            self.assertEqual(blobs[recheck.LIVE_DEPENDENCIES[0]], b'# pinned\n')
            for helper in recheck.LIVE_DEPENDENCIES:
                incomplete = dict(recorded)
                incomplete.pop(str(root/helper))
                with self.assertRaisesRegex(ValueError, 'inventory'):
                    recheck.bind_original_drivers(root, revision, incomplete)
            substituted = dict(recorded)
            substituted[str(root/recheck.LIVE_DEPENDENCIES[0])] = 'f'*64
            with self.assertRaisesRegex(ValueError, 'Git source commit'):
                recheck.bind_original_drivers(root, revision, substituted)

    def test_real_driver_imports_ignore_and_restore_poisoned_module_cache(self):
        root = recheck.ROOT
        blobs = {name: (root/name).read_bytes() for name in recheck.DRIVERS + recheck.LIVE_DEPENDENCIES + recheck.INPUT_DEPENDENCIES}
        missing = object()
        aliases = ('build_recipe', 'build_inputs', 'live_inputs', 'input_contract', 'analyze', 'run_suite')
        original = {name: sys.modules.get(name, missing) for name in aliases}
        poisoned = {name: types.ModuleType(name) for name in aliases}
        old_path = list(sys.path)
        try:
            sys.modules.update(poisoned)
            with recheck.bound_driver_modules(root, blobs) as modules:
                runner = modules[0]
                self.assertIsNot(runner.live_inputs, poisoned['live_inputs'])
                self.assertIsNot(runner.input_contract, poisoned['input_contract'])
                self.assertIs(runner.live_inputs.build_recipe, sys.modules['build_recipe'])
                self.assertIs(sys.modules['run_suite'], runner)
                gate = runner.load_module('replay_test_dynamic_gate', root/recheck.DRIVERS[-1])
                self.assertTrue(callable(gate.validate_negative))
                with self.assertRaisesRegex(ValueError, 'unbound dynamic'):
                    runner.load_module('unsafe', root/'team/unrecorded.py')
                command = runner.runtime_command('/emu', '/image', '/ref', '/flash')
                self.assertNotIn('stdbuf', command)
                self.assertIn('--seed=1', command)
            self.assertEqual(sys.path, old_path)
            for name in aliases:
                self.assertIs(sys.modules[name], poisoned[name])
            self.assertNotIn('replay_test_dynamic_gate', sys.modules)
        finally:
            for name, module in original.items():
                if module is missing:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_current_two_stream_hashes_and_runtime_identity_are_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = {'stdout.log': b'out\n', 'stderr.log': b'err\n', 'run.log': b'err\nout\n'}
            for name, body in raw.items():
                (root/name).write_bytes(body)
            (root/'exit-code.txt').write_bytes(b'0\n')
            command = ['timeout', '120m', '/emu', '-i', '/image', '--seed=1']
            hashes = {name: hashlib.sha256(body).hexdigest() for name, body in raw.items()}
            record = dict(name='dense-batch128', command=command, files={'/image': 'a'*64},
                          single_core=True, emu_threads=1, negative_target=None, exit_code=0,
                          started='2026-10-21T00:00:00+00:00', finished='2026-10-21T00:00:01+00:00',
                          raw_logs_sha256=hashes,
                          raw_sha256={name: hashes[name] for name in ('stdout.log', 'stderr.log')})
            (root/'runtime.json').write_text(json.dumps(record), encoding='utf-8')
            self.assertEqual(recheck.check_raw_job(root, record, command, record['files'], None)[0], 0)
            bad = dict(record, raw_sha256=hashes)
            with self.assertRaisesRegex(ValueError, 'secondary raw'):
                recheck.check_raw_job(root, bad, command, record['files'], None)
            runtime = dict(record, emu_threads=2)
            (root/'runtime.json').write_text(json.dumps(runtime), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'runtime/result'):
                recheck.check_raw_job(root, record, command, record['files'], None)


if __name__ == '__main__':
    unittest.main()
