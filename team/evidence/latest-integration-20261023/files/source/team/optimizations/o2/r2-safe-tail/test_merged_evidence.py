"""Reject forged process receipts before accepting archived runtime evidence."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import merged_evidence as e


def valid_receipt():
    image = dict(name='smoke-s2-d0-s07', suite='smoke', variant='s2', shard=7, dataset=0,
                 path='/experiment/build/images/smoke-s2-d0-s07', image_sha256='image-digest')
    cfg = dict(hardware_source='/hardware', reference='/normal.so', flash='/flash.bin')
    fixture = dict(binary='/experiment/negative.so', negative_sha256='fixture-digest')
    common = {'/hardware/build/emu': e.m.EMU, '/normal.so': e.f.REFERENCE, '/flash.bin': e.f.FLASH}
    files = dict(common)
    files[image['path'] + '/vdot-perf.bin'] = image['image_sha256']
    files.update({'/experiment/run/cwd/build/' + name: sha for name, sha in e.m.AUX.items()})
    sealed = {name: dict(sha256=sha, logical=None) for name, sha in files.items()}
    record = dict(image, contract=e.m.CONTRACT, mode='merged', replay=0, negative=False,
                  process_started=True, pid=123, exit_code=0, status=e.m.NORMAL_PASS,
                  started='2026-10-23T08:00:00+00:00', finished='2026-10-23T08:00:01+00:00',
                  cwd='/experiment/run/cwd', reference=cfg['reference'], files=files,
                  command=['/hardware/build/emu', '-i', image['path'] + '/vdot-perf.bin',
                           '--flash=/flash.bin', '--ram-size=128MB', '--diff=/normal.so',
                           '--max-cycles=2000000', '--seed=1'],
                  environment_overrides={'XS_NEGATIVE_VECTOR_TARGET': None},
                  environment_contract=e.m.ENVIRONMENT_CONTRACT, environment=e.m.execution_environment())
    return record, image, 0, False, cfg, fixture, common, sealed


class ReceiptIdentity(unittest.TestCase):
    def test_old_receipt_does_not_gain_new_environment_claim(self):
        args = list(valid_receipt())
        del args[0]['environment']
        del args[0]['environment_contract']
        with self.assertRaisesRegex(ValueError, 'explicit process environment'):
            e.run_identity(*args)

    def test_loader_override_is_rejected(self):
        args = list(valid_receipt())
        args[0]['environment']['LD_PRELOAD'] = '/unsealed.so'
        with self.assertRaisesRegex(ValueError, 'explicit process environment'):
            e.run_identity(*args)

    def test_fixture_environment_requires_complete_versioned_fields(self):
        for receipt in ({}, {'environment': e.m.execution_environment()},
                        {'environment_contract': 'other', 'environment': e.m.execution_environment()}):
            with self.subTest(receipt=receipt), self.assertRaisesRegex(ValueError, 'explicit process environment'):
                e.audit_environment(receipt)

    def test_complete_linux_receipt(self):
        e.run_identity(*valid_receipt())

    def test_pass_label_without_process_rejected(self):
        args = list(valid_receipt()); args[0]['process_started'] = False
        with self.assertRaisesRegex(ValueError, 'real process'):
            e.run_identity(*args)

    def test_timed_out_process_cannot_claim_pass(self):
        args = list(valid_receipt()); args[0]['timed_out'] = True
        with self.assertRaisesRegex(ValueError, 'real process'):
            e.run_identity(*args)

    def test_changed_loaded_reference_command_rejected(self):
        args = list(valid_receipt()); args[0]['command'][5] = '--diff=/other.so'
        with self.assertRaisesRegex(ValueError, 'command/reference'):
            e.run_identity(*args)

    def test_extra_unsealed_input_rejected(self):
        args = list(valid_receipt()); args[0]['files']['/extra-preload.so'] = 'anything'
        with self.assertRaisesRegex(ValueError, 'input map'):
            e.run_identity(*args)

    def test_recorded_input_and_seal_must_match(self):
        args = list(valid_receipt()); args[-1]['/normal.so']['sha256'] = 'other'
        with self.assertRaisesRegex(ValueError, 'unsealed'):
            e.run_identity(*args)

    def test_timezone_free_timestamp_rejected(self):
        args = list(valid_receipt()); args[0]['started'] = '2026-10-23T08:00:00'
        with self.assertRaisesRegex(ValueError, 'timestamps'):
            e.run_identity(*args)

    def test_negative_environment_cannot_leak_to_normal(self):
        args = list(valid_receipt()); args[0]['environment_overrides']['XS_NEGATIVE_VECTOR_TARGET'] = 'vdot'
        with self.assertRaisesRegex(ValueError, 'environment'):
            e.run_identity(*args)

    def test_timezone_offset_cannot_turn_earlier_normal_into_recovery(self):
        negative = dict(status=e.m.NEGATIVE_PASS, image_sha256='same-image', pid=1,
                        finished='2026-10-23T08:00:00+00:00')
        normal = dict(status=e.m.NORMAL_PASS, image_sha256='same-image', pid=2,
                      started='2026-10-23T09:00:00+02:00')
        with self.assertRaisesRegex(ValueError, 'before negative completion'):
            e.audit_recovery(negative, normal)


class AuditOutputBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / 'archive'
        self.archive.mkdir()
        self.original = self.archive / 'original.txt'
        self.original.write_bytes(b'immutable evidence\n')

    def invoke(self, output):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            e.main(['--repo', str(self.root), '--action', 'audit',
                    '--archive', str(self.archive), '--output', str(output)])

    def reject_before_audit(self, output):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob('*') if p.is_file()}
        with mock.patch.object(e, 'audit') as audit, self.assertRaises(SystemExit) as failure:
            self.invoke(output)
        self.assertEqual(failure.exception.code, 2)
        audit.assert_not_called()
        after = {p.relative_to(self.root): p.read_bytes()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def symlink(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError as exc:
            self.skipTest('symlink creation unavailable: ' + str(exc))

    def test_archive_child_rejected_before_audit_or_directory_creation(self):
        output = self.archive / 'files/new/audit.json'
        self.reject_before_audit(output)
        self.assertFalse(output.parent.exists())

    def test_archive_root_rejected_before_audit(self):
        self.reject_before_audit(self.archive)

    def test_existing_external_receipt_is_preserved(self):
        output = self.root / 'prior.json'
        output.write_bytes(b'prior result\n')
        self.reject_before_audit(output)

    def test_parent_symlink_into_archive_is_rejected(self):
        link = self.root / 'archive-alias'
        self.symlink(link, self.archive, directory=True)
        self.reject_before_audit(link / 'new.json')
        self.assertFalse((self.archive / 'new.json').exists())

    def test_dangling_output_symlink_is_rejected(self):
        output, target = self.root / 'output.json', self.root / 'target.json'
        self.symlink(output, target)
        self.reject_before_audit(output)
        self.assertFalse(target.exists())

    def test_new_external_receipt_preserves_archive(self):
        output = self.root / 'receipts/result.json'
        value = dict(status='test-audit-result', new_emu_runs=0)
        with mock.patch.object(e, 'audit', return_value=value) as audit:
            self.invoke(output)
        audit.assert_called_once_with(self.root, self.archive)
        self.assertEqual(json.loads(output.read_text()), value)
        self.assertEqual(list(self.archive.iterdir()), [self.original])
        self.assertEqual(self.original.read_bytes(), b'immutable evidence\n')

    def test_output_created_during_audit_is_not_overwritten(self):
        output = self.root / 'race.json'
        def create_competing_receipt(*args):
            output.write_bytes(b'another completed audit\n')
            return {'status': 'test-audit-result'}
        with mock.patch.object(e, 'audit', side_effect=create_competing_receipt):
            with self.assertRaises(SystemExit) as failure:
                self.invoke(output)
        self.assertEqual(failure.exception.code, 2)
        self.assertEqual(output.read_bytes(), b'another completed audit\n')


if __name__ == '__main__':
    unittest.main()
