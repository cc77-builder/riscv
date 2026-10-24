"""Reject substitution, stale recovery, and unverified adoption in the new contract."""
import copy
from pathlib import Path
import tempfile
import unittest

import merged_regression as m


class MergedRegressionTests(unittest.TestCase):
    def pair(self):
        command = ['timeout', '120m', 'stdbuf', '-o0', '-e0', '/emu', '-i', '/matrix0',
                   '--flash=/flash', '--ram-size=128MB', '--diff=/normal', '--max-cycles=5000000']
        files = {'/matrix0': m.MATRIX0, '/emu': m.m.EMU, '/flash': m.f.FLASH, '/normal': m.f.REFERENCE}
        normal = dict(status='VDOT_MATRIX_SHARD_PASS', process_started=True, pid=2, started='2026-10-23T10:00:02+00:00',
                      finished='2026-10-23T10:00:03+00:00', files=files, auxiliary_files=dict(m.m.AUX),
                      negative_target=None, command=command, environment_overrides={'XS_NEGATIVE_VECTOR_TARGET': None})
        negative = copy.deepcopy(normal)
        negative.update(status=m.m.NEGATIVE_PASS, pid=1, started='2026-10-23T18:00:00+08:00',
                        finished='2026-10-23T18:00:01+08:00', negative_target='vdot')
        negative['files']['/negative'] = m.NEGATIVE
        negative['environment_overrides']['XS_NEGATIVE_VECTOR_TARGET'] = 'vdot'
        negative['command'][10] = '--diff=/negative'
        return negative, normal

    def check(self, negative, normal):
        return m.pair_relation(negative, normal, '/matrix0', '/emu', '/flash', '/normal', '/negative')

    def test_cross_offset_actual_time_recovery_passes(self):
        self.assertTrue(self.check(*self.pair()))

    def test_earlier_old_normal_cannot_recover(self):
        negative, normal = self.pair()
        normal['started'] = '2026-10-23T09:59:59+00:00'
        with self.assertRaisesRegex(ValueError, 'subsequent'):
            self.check(negative, normal)

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, 'UTC offset'):
            m.instant('2026-10-23T10:00:00')

    def test_same_pid_rejected(self):
        negative, normal = self.pair(); normal['pid'] = negative['pid']
        with self.assertRaisesRegex(ValueError, 'new subsequent'):
            self.check(negative, normal)

    def test_unstarted_or_timed_out_process_rejected(self):
        for key, value in [('process_started', False), ('timed_out', True)]:
            negative, normal = self.pair(); normal[key] = value
            with self.assertRaisesRegex(ValueError, 'process incomplete'):
                self.check(negative, normal)

    def test_other_image_cannot_replace_matrix0(self):
        negative, normal = self.pair(); normal['files']['/matrix0'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'shared input'):
            self.check(negative, normal)

    def test_old_fixture_not_accepted(self):
        negative, normal = self.pair(); negative['files']['/negative'] = '9b3' + '0' * 61
        with self.assertRaisesRegex(ValueError, 'selected reference'):
            self.check(negative, normal)

    def test_modified_command_or_auxiliary_rejected(self):
        negative, normal = self.pair(); normal['command'][-1] = '--max-cycles=1'
        with self.assertRaisesRegex(ValueError, 'command mismatch'):
            self.check(negative, normal)
        negative, normal = self.pair(); normal['auxiliary_files']['plusArgs'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'auxiliary'):
            self.check(negative, normal)

    def test_exact_set_rejects_duplicate_and_extra(self):
        self.assertEqual(set(m.unique_rows([dict(name='a'), dict(name='b')], {'a', 'b'})), {'a', 'b'})
        for rows in [[dict(name='a'), dict(name='a')], [dict(name='a'), dict(name='b'), dict(name='c')]]:
            with self.assertRaises(ValueError):
                m.unique_rows(rows, {'a', 'b'})

    def test_adoption_requires_all_raw_bytes_and_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            left, right = (Path(tmp) / name for name in ('source', 'copy'))
            for p in (left, right):
                p.mkdir(); (p / 'result.json').write_bytes(b'{}\n'); (p / 'stdout.log').write_bytes(b'raw\n')
            digest = m.g.sha(left / 'result.json')
            m.identical_copy(left, right, digest)
            (right / 'stdout.log').write_bytes(b'changed\n')
            with self.assertRaisesRegex(ValueError, 'adopted job bytes'):
                m.identical_copy(left, right, digest)
            (right / 'stdout.log').write_bytes(b'raw\n'); (right / 'extra.log').write_bytes(b'')
            with self.assertRaisesRegex(ValueError, 'adopted job bytes'):
                m.identical_copy(left, right, digest)


if __name__ == '__main__':
    unittest.main()
