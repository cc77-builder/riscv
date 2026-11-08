import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import retest


class RetestTests(unittest.TestCase):
    def samples(self):
        return [dict(stage='performance', phase='measured', scenario=s, method=m,
                     dataset=d, repeat=r, cycles=10 if m == 'vdot' else 30, n=1, dots=1)
                for s in retest.SCENARIOS for m in ('vdot', 'rvv')
                for d in range(3) for r in range(2, 6)]

    def test_real_generator_plan_matches_summary_contract(self):
        rows = []
        with tempfile.TemporaryDirectory() as temp:
            for dataset in range(3):
                manifest = retest.generate.generate(Path(temp) / str(dataset), 'performance', dataset,
                                                   0, 1, True, 'ours')
                for entry in manifest['plan']:
                    row = manifest['rows'][entry['index']]
                    rows.append(dict(stage='performance', phase=entry['phase'], repeat=entry['repeat'],
                                     dataset=dataset, scenario=row['scenario'], method=row['method'],
                                     n=row['n'], dots=row['dots'], cycles=100))
        self.assertEqual([r['speedup'] for r in retest.summarize(rows)], [1, 1, 1, 1])

    def test_exact_paired_windows(self):
        rows = retest.summarize(self.samples())
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r['speedup'] == 3 and r['windows_per_method'] == 12 for r in rows))

    def test_warmup_is_not_measured(self):
        rows = self.samples()
        rows.append(dict(rows[0], phase='warmup', cycles=999))
        self.assertEqual(retest.summarize(rows)[0]['vdot_mean'], 10)

    def test_missing_window_rejected(self):
        with self.assertRaises(ValueError): retest.summarize(self.samples()[1:])

    def test_duplicate_window_rejected(self):
        rows = self.samples()
        with self.assertRaises(ValueError): retest.summarize(rows + [rows[0]])

    def test_wrong_dataset_rejected(self):
        rows = self.samples(); rows[0]['dataset'] = 4
        with self.assertRaises(ValueError): retest.summarize(rows)

    def test_unequal_work_rejected(self):
        rows = self.samples(); rows[0]['dots'] = 2
        with self.assertRaises(ValueError): retest.summarize(rows)

    def test_nonpositive_cycles_rejected(self):
        rows = self.samples(); rows[0]['cycles'] = 0
        with self.assertRaises(ValueError): retest.summarize(rows)

    def test_new_source_commit_supported_but_receipts_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); emu = root / 'emu'; emu.write_bytes(b'new-build')
            (root / 'src').mkdir(); (root / 'src/rtl').write_bytes(b'rtl')
            (root / 'build.sc').write_bytes(b'build')
            pins = dict(source_commit='new-release-commit', emu_sha256=retest.sha(emu),
                        config='MinimalConfig', NUM_CORES=1, EMU_THREADS=1,
                        VDOT_O2_ELASTIC='1', VDOT_T14_FUSED_INPUT='1', VDOT_O1_HANDOFF='0',
                        VDOT_O2_TRACE='1', VDOT_T12_TRACE='0', VDOT_T13_TRACE='1',
                        files={p: retest.sha(root / p) for p in ('build.sc', 'src/rtl')})
            state = dict(source_commit=pins['source_commit'], emu_sha256=pins['emu_sha256'],
                         status='O2_FULLCORE_BUILD_PASS', build_exit_code=0)
            retest.save(root / 'build-state.json', state)
            def run(p):
                retest.save(root / 'hardware-inputs.json', p)
                return retest.hardware_identity(root, emu)
            with patch.object(retest, 'ROOT', root), patch.object(retest.subprocess, 'check_output', return_value='same-tree\n'):
                self.assertEqual(run(pins)['source_commit'], 'new-release-commit')
                for key, value in [('emu_sha256', 'wrong'), ('VDOT_T13_TRACE', '0'),
                                   ('VDOT_O2_ELASTIC', '0'), ('EMU_THREADS', 2)]:
                    bad = copy.deepcopy(pins); bad[key] = value
                    with self.subTest(key=key), self.assertRaises(ValueError): run(bad)
                (root / 'src/rtl').write_bytes(b'changed')
                with self.assertRaises(ValueError): run(pins)

    def test_fresh_output_preserves_existing_results(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); marker = p / 'marker'; marker.write_text('keep')
            with self.assertRaises(ValueError): retest.fresh(p)
            self.assertEqual(marker.read_text(), 'keep')


if __name__ == '__main__': unittest.main()
