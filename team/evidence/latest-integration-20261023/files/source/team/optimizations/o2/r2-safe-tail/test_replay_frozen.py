"""Protect current inputs when preparing the separate historical context."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import replay_frozen as replay


class FrozenContextBoundary(unittest.TestCase):
    def test_invalid_locations_never_launch_git_or_modify_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo, archive = base / 'repo', base / 'archive'
            repo.mkdir(); archive.mkdir()
            manifest = archive / 'archive-manifest.json'
            manifest.write_bytes(b'fixture manifest')
            existing = base / 'existing'
            existing.mkdir()
            for output in (repo / 'nested', archive / 'nested', existing):
                with self.subTest(output=output), patch.object(replay.sys, 'platform', 'linux'), \
                     patch.object(replay.subprocess, 'check_output') as git:
                    with self.assertRaises(ValueError):
                        replay.run(repo, archive, output, base / 'tools')
                    git.assert_not_called()
                    self.assertEqual(manifest.read_bytes(), b'fixture manifest')
            self.assertFalse((repo / 'nested').exists())
            self.assertFalse((archive / 'nested').exists())

    def test_different_archive_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / 'archive').mkdir()
            (base / 'archive/archive-manifest.json').write_bytes(b'wrong archive')
            with patch.object(replay.sys, 'platform', 'linux'), patch.object(replay.subprocess, 'check_output') as git:
                with self.assertRaisesRegex(ValueError, 'not the fixed'):
                    replay.run(base / 'repo', base / 'archive', base / 'output', base / 'tools')
                git.assert_not_called()
            self.assertFalse((base / 'output').exists())

    def test_missing_tools_are_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); archive = base / 'archive'; archive.mkdir()
            raw = b'fixture manifest'
            (archive / 'archive-manifest.json').write_bytes(raw)
            with patch.object(replay.sys, 'platform', 'linux'), \
                 patch.object(replay, 'MANIFEST_SHA', hashlib.sha256(raw).hexdigest()), \
                 patch.object(replay.shutil, 'which', return_value=None), \
                 patch.object(replay.subprocess, 'check_output') as git:
                with self.assertRaisesRegex(ValueError, 'missing host-test tool'):
                    replay.run(base / 'repo', archive, base / 'output', base / 'tools')
                git.assert_not_called()
            self.assertFalse((base / 'output').exists())


if __name__ == '__main__':
    unittest.main()
