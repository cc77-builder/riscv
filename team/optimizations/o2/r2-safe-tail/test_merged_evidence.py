"""Reject forged process receipts before accepting archived runtime evidence."""
import copy
import unittest

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
                  environment_overrides={'XS_NEGATIVE_VECTOR_TARGET': None})
    return record, image, 0, False, cfg, fixture, common, sealed


class ReceiptIdentity(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
