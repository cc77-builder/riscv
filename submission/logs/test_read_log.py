"""Meaningful checks for archive integrity and non-destructive restoration."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from read_log import History, safe_path


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.here = self.root / 'package'
        self.here.mkdir()
        self.name = 'team/evidence/example/run.log'
        self.data = b'original failed attempt\n'
        archive = self.here / 'part.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr(self.name, self.data)
        self.manifest = {'files': [{'path': self.name, 'storage': 'archive', 'archive': 'part.zip',
                                    'sha256': hashlib.sha256(self.data).hexdigest(), 'size': len(self.data),
                                    'mode': '100644', 'run_log': True}],
                         'archives': [{'path': 'part.zip', 'size': archive.stat().st_size,
                                       'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}]}
        self.save()

    def save(self):
        (self.here / 'manifest.json').write_text(json.dumps(self.manifest))

    def history(self):
        h = History(self.here, self.root)
        self.addCleanup(lambda: [z.close() for z in h.opened.values()])
        return h

    def test_restores_exact_failed_log_and_is_idempotent(self):
        h = self.history()
        dest = self.root / 'restored'
        self.assertEqual(h.restore(dest), {'written': 1, 'already_identical': 0})
        self.assertEqual((dest / self.name).read_bytes(), self.data)
        self.assertEqual(h.restore(dest), {'written': 0, 'already_identical': 1})

    def test_refuses_existing_different_file(self):
        dest = self.root / 'restored'
        p = dest / self.name
        p.parent.mkdir(parents=True)
        p.write_bytes(b'do not overwrite')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            self.history().restore(dest)
        self.assertEqual(p.read_bytes(), b'do not overwrite')

    def test_rejects_archive_corruption(self):
        with (self.here / 'part.zip').open('ab') as f:
            f.write(b'corruption')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.history().read(self.name)

    def test_rejects_member_hash_mismatch(self):
        self.manifest['files'][0]['sha256'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.history().read(self.name)

    def test_rejects_traversal_absolute_and_windows_paths(self):
        for name in ('../outside', '/absolute', 'a/../../outside', 'C:/outside', 'a\\b', './a'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_path(name)

    def test_rejects_duplicate_manifest_path(self):
        self.manifest['files'].append(dict(self.manifest['files'][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.history()

    def test_refuses_destination_symlink_escape(self):
        dest = self.root / 'restored'
        dest.mkdir()
        outside = self.root / 'outside'
        outside.mkdir()
        (dest / 'team').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.history().restore(dest)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
