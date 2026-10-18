"""Synthetic boundary/negative checks; not hardware results."""
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import replay_scenarios as replay


class WindowTests(unittest.TestCase):
    def test_half_open_windows_exclude_cross_invocation_gaps(self):
        sample = dict(seq=0, scenario='batch', dataset=0, method='vdot', phase='measured',
                      repeat=2, dots=128, cycles=10, instructions=8, sample_ticks=[5, 10, 20, 25])
        diagnosis = dict(transactions=[dict(accept_cycle=c, end_cycle=c+2) for c in (7, 10, 13, 19, 20)],
                         response_coincident_busy_wait_cycles=[9, 10, 19, 20])
        events = [(c, 0, 'VFEX4_WAIT', {'fu': '0x800000000', 'busy': '1'}) for c in (9, 10, 19, 20)]
        window = replay.observe(sample, diagnosis, events)
        self.assertEqual(window['FU_accepts_including_speculation'], 3)
        self.assertEqual(window['accepted_here_ended_outside_window'], 1)
        self.assertEqual(window['accept_gap_histogram'], {'3': 1, '6': 1})
        self.assertEqual(window['release_gap_histogram'], {'1': 1, '4': 1})
        self.assertEqual(window['parent_wait_event_counts'], {'vdot_busy': 2})
        self.assertEqual(window['response_coincident_busy_wait_events'], 2)

    def test_incomplete_inventory_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'incomplete measured inventory'):
            replay.summarize([])

    def test_existing_output_rejected_before_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'output already exists'):
                replay.replay(Path(temp), Path(temp))

    def test_unpinned_manifest_cannot_authenticate_its_own_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '文件校验.json').write_text(json.dumps({'algorithm': 'sha256', 'files': {}}))
            with self.assertRaisesRegex(ValueError, 'sealed manifest changed'):
                replay.authenticate(root)

    def test_unsafe_archive_members_rejected_before_writing(self):
        for name, kind in [('ours/../../escape', tarfile.REGTYPE), ('/escape', tarfile.REGTYPE),
                           ('ours\\escape', tarfile.REGTYPE), ('ours/C:escape', tarfile.REGTYPE),
                           ('ours/link', tarfile.SYMTYPE), ('ours/link', tarfile.LNKTYPE)]:
            with self.subTest(name=name, kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                with tarfile.open(root/'bad.tar', 'w') as archive:
                    entry = tarfile.TarInfo(name)
                    entry.type = kind
                    entry.linkname = '../elsewhere'
                    archive.addfile(entry, io.BytesIO())
                with self.assertRaises(ValueError):
                    replay.extract_images(root/'bad.tar', root/'images')
                self.assertFalse((root/'images').exists())

    def test_case_colliding_archive_names_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with tarfile.open(root/'bad.tar', 'w') as archive:
                for name in ('ours/x', 'ours/X'):
                    archive.addfile(tarfile.TarInfo(name), io.BytesIO())
            with self.assertRaisesRegex(ValueError, 'duplicate tar path'):
                replay.extract_images(root/'bad.tar', root/'images')


if __name__ == '__main__':
    unittest.main()
