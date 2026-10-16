"""Negative controls against real archived receipts; never new DUT evidence."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import check as c
import campaign
import generate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE = ROOT / 'team/evidence/t13-performance-20261015'


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.build = root / 'build'
        self.run = root / 'run'
        shutil.copytree(ARCHIVE / 'images-v3/performance-d0-s00', self.build)
        shutil.copytree(ARCHIVE / 'campaign-v3/performance-d0-s00-r0', self.run)
        self.external = json.loads((ARCHIVE / 'external-artifacts.json').read_text())

    def edit(self, folder, name, action):
        path = folder / name
        value = json.loads(path.read_text())
        action(value)
        path.write_text(json.dumps(value))

    def test_original_receipt(self):
        self.assertEqual(c.verify(self.build, self.run, self.external)['status'], 'PASS')

    def test_incomplete_or_inconsistent_receipts(self):
        mutations = [
            ('run', 'result.json', lambda r: r.update(files={})),
            ('run', 'result.json', lambda r: r.update(command=['other-emu', '--no-diff'])),
            ('run', 'result.json', lambda r: r.pop('raw_sha256')),
            ('run', 'result.json', lambda r: r['command'].append('--no-diff')),
            ('run', 'result.json', lambda r: r['command'].append('--diff=/wrong.so')),
            ('run', 'result.json', lambda r: r['command'].remove('--seed=1')),
            ('run', 'result.json', lambda r: r.update(emu_threads=2)),
            ('build', 'build.json', lambda r: r.update(exit_code=1)),
            ('build', 'build.json', lambda r: r.pop('artifacts')),
            ('build', 'build.json', lambda r: r.update(am_revision='0'*40)),
        ]
        for folder, name, action in mutations:
            path = getattr(self, folder) / name
            original = path.read_bytes()
            with self.subTest(folder=folder, action=action):
                self.edit(getattr(self, folder), name, action)
                try:
                    with self.assertRaises((ValueError, KeyError)):
                        c.verify(self.build, self.run, self.external)
                finally:
                    path.write_bytes(original)


class OptimizedPythonTests(unittest.TestCase):
    def test_failed_reference_pin_and_judge_remain_failures(self):
        programs = [
            "import reference as m; ref=out/'wrong.so'; ref.write_bytes(b'wrong'); "
            "m.main(SimpleNamespace(output=out/'result', reference=ref))",
            "import host_judge as m; "
            "m.g.generate=lambda *a,**k: {'rows': []}; "
            "m.subprocess.run=lambda *a,**k: SimpleNamespace(returncode=17,stdout='FAILED',stderr=''); "
            "m.main(SimpleNamespace(output=out/'result'))",
        ]
        for optimize in ('0', '1', '2'):
            for program in programs:
                with self.subTest(optimize=optimize, program=program), tempfile.TemporaryDirectory() as temp:
                    script = ('from pathlib import Path\nfrom types import SimpleNamespace\n'
                              'import sys\nsys.path.insert(0,sys.argv[1])\nout=Path(sys.argv[2])\n'
                              'try:\n ' + program + '\nexcept ValueError:\n print("EXPECTED_REJECTION")\n'
                              'else:\n raise RuntimeError("invalid evidence was accepted")\n')
                    p = subprocess.run([sys.executable, '-B', '-c', script, str(HERE), temp],
                                       env=dict(os.environ, PYTHONOPTIMIZE=optimize, PYTHONUTF8='1'), capture_output=True, text=True)
                    self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
                    self.assertIn('EXPECTED_REJECTION', p.stdout)


class BuildWorkflowTests(unittest.TestCase):
    def test_fresh_build_snapshots_and_source_drift(self):
        for drift in (False, True):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source_dir = root/'team/workloads/vdot-perf'
                shutil.copytree(HERE, source_dir)
                out = root/'out'
                def child(command, **kwargs):
                    if command[0] == 'python3':
                        args = command[3:]
                        value = lambda key: args[args.index(key)+1]
                        generate.generate(Path(value('--output')), value('--suite'), int(value('--dataset')),
                                          int(value('--shard')), int(value('--shards')), '--shared-stream' in args)
                    else:
                        # Only compiler execution is simulated. Source freezing,
                        # generation and receipt validation run unchanged.
                        image = next(p.parent for p in out.glob('*/data/manifest.json')
                                     if not (p.parents[1]/'vdot-perf.bin').exists()).parent
                        (image/'vdot-perf.bin').write_bytes(b'compiler fixture')
                        (image/'vdot-perf.elf').write_bytes(b'ELF fixture; not a DUT artifact')
                        if drift:
                            with (source_dir/'main.c').open('ab') as f:
                                f.write(b'\n/* concurrent edit */\n')
                    return SimpleNamespace(returncode=0)
                def git(command, **kwargs):
                    return '' if 'status' in command else 'a'*40+'\n'
                with patch.object(campaign, 'ROOT', root), patch.object(campaign, 'am_inputs', return_value={'pinned': 'AM'}), \
                     patch.object(campaign.subprocess, 'check_output', side_effect=git), \
                     patch.object(campaign.subprocess, 'run', side_effect=child):
                    args = SimpleNamespace(output=out, am=root/'am', stream_only=True)
                    if drift:
                        with self.assertRaisesRegex(ValueError, 'software changed'):
                            campaign.build(args)
                        self.assertFalse((out/'images.json').exists())
                    else:
                        campaign.build(args)
                        images = json.loads((out/'images.json').read_text())['images']
                        self.assertEqual(len(images), 9)
                        for image in images:
                            build = Path(image['path'])
                            c.verify_generation(build, json.loads((build/'data/manifest.json').read_text()))
                            for name in ('generate.py', 'main.c', 'Makefile'):
                                self.assertEqual((build/'source'/name).read_bytes(), (source_dir/name).read_bytes())

    def test_runtime_mutation_is_recorded_and_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root/'image'
            shutil.copytree(ARCHIVE/'images-v3/performance-d0-s00', build)
            inventory = root/'images'
            inventory.mkdir()
            (inventory/'images.json').write_text(json.dumps({'images': [dict(
                name='fixture', path=str(build), replays=1)]}))
            assets = [root/name for name in ('emu', 'reference', 'flash')]
            for p in assets:
                p.write_bytes(b'fixed')
            def execute(*args, **kwargs):
                assets[0].write_bytes(b'changed during run')
                return SimpleNamespace(returncode=0)
            args = SimpleNamespace(output=root/'runs', images=inventory, jobs=1,
                                   emu=assets[0], reference=assets[1], flash=assets[2])
            with patch.object(campaign.subprocess, 'run', side_effect=execute):
                with self.assertRaisesRegex(ValueError, 'runtime input changed'):
                    campaign.run(args)
            receipt = json.loads((root/'runs/fixture-r0/result.json').read_text())
            self.assertEqual(receipt['exit_code'], 0)
            self.assertIn('verification_error', receipt)
            self.assertFalse((root/'runs/campaign.json').exists())


if __name__ == '__main__':
    unittest.main()
