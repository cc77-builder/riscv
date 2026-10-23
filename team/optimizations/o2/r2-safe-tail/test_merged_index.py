"""Regressions for archive publication mode and receipt-location failures."""
from pathlib import Path
import tempfile
import unittest

import merged_index as index


class IndexGateTests(unittest.TestCase):
    def entry(self, mode='100644', stage='0', name='archive/raw.log', oid='1' * 40):
        return ('%s %s %s\t%s\0' % (mode, oid, stage, name)).encode('utf-8')

    def test_resolved_ordinary_modes_and_object_ids(self):
        result = index.index_entries(self.entry() + self.entry('100755', name='archive/tool', oid='a' * 64))
        self.assertEqual(result['archive/raw.log'], dict(mode='100644', oid='1' * 40))
        self.assertEqual(result['archive/tool'], dict(mode='100755', oid='a' * 64))

    def test_symlink_same_blob_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-regular'):
            index.index_entries(self.entry(mode='120000'))

    def test_gitlink_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-regular'):
            index.index_entries(self.entry(mode='160000'))

    def test_unmerged_entry_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unmerged'):
            index.index_entries(self.entry(stage='1'))

    def test_duplicate_path_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            index.index_entries(self.entry() + self.entry())

    def test_invalid_oid_and_unterminated_inventory_rejected(self):
        with self.assertRaisesRegex(ValueError, 'object identity'):
            index.index_entries(self.entry(oid='g' * 40))
        with self.assertRaisesRegex(ValueError, 'unterminated'):
            index.index_entries(self.entry()[:-1])

    def test_receipt_inside_archive_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'sealed'
            archive.mkdir()
            output = archive / 'new-receipt.json'
            with self.assertRaisesRegex(ValueError, 'outside the archive'):
                index.check_output_path(archive, output)
            self.assertFalse(output.exists())

    def test_receipt_external_new_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'sealed'
            archive.mkdir()
            output = Path(tmp) / 'receipt.json'
            index.check_output_path(archive, output)
            output.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                index.check_output_path(archive, output)


if __name__ == '__main__':
    unittest.main()
