"""Fail-closed checks for the independent single-hardware screen (no EMU)."""
import copy
import tempfile
from pathlib import Path
import unittest

import merged_screen as m


def records():
    result = []
    for shard in (4, 5, 6, 7):
        for dataset in range(3):
            for variant in ('s0', 's2'):
                samples = []
                for software in ('basic', 'reuse'):
                    for method in ('vdot', 'rvv'):
                        for repeat in range(2, 6):
                            cycles = 100 if method == 'vdot' else (80 if software == 'reuse' else 120)
                            if shard in (6, 7) and variant == 's2' and method == 'vdot':
                                cycles = 50
                            samples.append(dict(mode='merged', phase='measured', variant=variant, shard=shard,
                                                dataset=dataset, software=software, method=method, repeat=repeat,
                                                cycles=cycles, instructions=40, seq=repeat, image_sha256=str(shard)))
                result.append(dict(suite='performance', replay=0, samples=samples))
    return result


class ScreenStatistics(unittest.TestCase):
    def test_complete_matrix_and_fastest_rvv(self):
        value = m.summarize(records())
        self.assertEqual(len(value['samples']), 384)
        self.assertEqual(len(value['rows']), 16)
        row = next(r for r in value['comparisons'] if r['shard'] == 7 and r['variant'] == 's2' and r['software'] == 'basic')
        self.assertEqual(row['s0_over_variant'], 2)
        self.assertEqual(row['fastest_rvv_software'], 'reuse')
        self.assertEqual(row['fastest_rvv_over_vdot'], 1.6)

    def test_missing_sample_rejected(self):
        value = records()
        value[-1]['samples'].pop()
        with self.assertRaisesRegex(ValueError, 'missing/extra'):
            m.summarize(value)

    def test_duplicate_sample_rejected_even_with_correct_count(self):
        value = records()
        value[-1]['samples'][-1] = copy.deepcopy(value[-1]['samples'][-2])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            m.summarize(value)

    def test_unexpected_dataset_rejected(self):
        value = records()
        value[-1]['samples'][-1]['dataset'] = 3
        with self.assertRaisesRegex(ValueError, 'missing/extra'):
            m.summarize(value)

    def test_wrong_hardware_label_rejected(self):
        value = records()
        value[-1]['samples'][-1]['mode'] = 'h1'
        with self.assertRaisesRegex(ValueError, 'invalid'):
            m.summarize(value)

    def test_bool_cycle_is_not_measurement(self):
        value = records()
        value[-1]['samples'][-1]['cycles'] = True
        with self.assertRaisesRegex(ValueError, 'invalid'):
            m.summarize(value)

    def test_control_cycle_drift_rejected(self):
        value = records()
        value[1]['samples'][0]['cycles'] += 1
        with self.assertRaisesRegex(ValueError, '16x64 invariant'):
            m.summarize(value)

    def test_control_image_drift_rejected(self):
        value = records()
        value[1]['samples'][0]['image_sha256'] = 'different'
        with self.assertRaisesRegex(ValueError, '16x64 invariant'):
            m.summarize(value)

    def test_smoke_warmup_and_replay_not_counted(self):
        value = records()
        smoke = copy.deepcopy(value[0]); smoke['suite'] = 'smoke'
        replay = copy.deepcopy(value[0]); replay['replay'] = 1
        warmup = copy.deepcopy(value[0]['samples'][0]); warmup['phase'] = 'warmup'
        value[0]['samples'].append(warmup)
        self.assertEqual(len(m.summarize(value + [smoke, replay])['samples']), 384)


class Provenance(unittest.TestCase):
    def test_s0_manifest_cannot_masquerade_as_s2(self):
        image = dict(suite='smoke', dataset=0, shard=7, variant='s2')
        receipt = dict(selection=dict(image), accepted=True)
        manifest = dict(suite='smoke', dataset=0, shard=7, r2_variant='s0')
        with self.assertRaisesRegex(ValueError, 'manifest selection'):
            m.validate_selection(image, manifest, receipt)

    def test_wrong_build_selection_rejected(self):
        image = dict(suite='smoke', dataset=0, shard=7, variant='s2')
        receipt = dict(selection=dict(image, dataset=1), accepted=True)
        manifest = dict(suite='smoke', dataset=0, shard=7, r2_variant='s2')
        with self.assertRaisesRegex(ValueError, 'build selection'):
            m.validate_selection(image, manifest, receipt)

    def recovery(self):
        negative = dict(status=m.NEGATIVE_PASS, image_sha256='same', pid=11,
                        finished='2026-10-23T08:00:01+00:00')
        normal = dict(status=m.NORMAL_PASS, image_sha256='same', pid=12,
                      started='2026-10-23T08:00:02+00:00')
        return negative, normal

    def test_recovery_is_later_independent_normal_process(self):
        m.validate_recovery(*self.recovery())

    def test_preceding_normal_is_not_recovery(self):
        negative, normal = self.recovery()
        normal['started'] = '2026-10-23T08:00:00+00:00'
        with self.assertRaises(ValueError):
            m.validate_recovery(negative, normal)

    def test_other_image_is_not_recovery(self):
        negative, normal = self.recovery()
        normal['image_sha256'] = 'other'
        with self.assertRaises(ValueError):
            m.validate_recovery(negative, normal)

    def test_input_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_bytes(b'original')
            files = {str(path): m.g.sha(path)}
            m.verify_files(files)
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'input drift'):
                m.verify_files(files)


if __name__ == '__main__':
    unittest.main()
