"""Host fixtures for the observation entry; these are not CPU execution evidence."""
import unittest

from check_trace import TraceError
from run_trace_core import control_check


class CoreObservationTests(unittest.TestCase):
    def setUp(self):
        self.text = '\n'.join([
            'T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1',
            *[f'T12_GROUP_PASS id={i} checkpoints=32 bytes=16384' for i in range(4)],
            'T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0',
            'HIT GOOD TRAP',
        ])
        self.trace = dict(scope='fullcore', mode=2, overlap=100, rob=dict(committed=2157, accepted_squashed=2, rob_wraps=10),
                          vdot_canceled=2, accepted_by_kind={'0':2160,'1':10,'2':0}, waits=50, vdot_stalls=1)
        self.manifest = dict(groups=[dict(vdot_count=512)]*4, speculation=dict(expected_architectural_vdot=109))

    def test_observation_result_explicitly_keeps_t12_pending(self):
        result = control_check(self.text, self.trace, self.manifest, 0)
        self.assertIn('T12_ACCEPTANCE_PENDING', result['status'])
        self.assertEqual(result['expected_vdot_commits'], 2157)
        self.assertTrue(all(result['coverage'].values()))
        self.assertIn('FTQ', result['missing_observation'][0])

    def test_retirement_must_match_compiled_plan(self):
        self.trace['rob']['committed'] -= 1
        with self.assertRaisesRegex(TraceError, 'retirement count'):
            control_check(self.text, self.trace, self.manifest, 0)

    def test_uart_pass_does_not_override_runtime_failure(self):
        with self.assertRaisesRegex(TraceError, 'runtime failed'):
            control_check(self.text, self.trace, self.manifest, 1)

    def test_missing_duplicate_and_reordered_groups(self):
        lines = self.text.splitlines()
        for changed in (lines[:2] + lines[3:], lines[:2] + [lines[1]] + lines[2:],
                        lines[:1] + [lines[2],lines[1]] + lines[3:]):
            with self.assertRaisesRegex(TraceError, 'groups'):
                control_check('\n'.join(changed), self.trace, self.manifest, 0)

    def test_missing_coverage_is_reported(self):
        self.trace['vdot_stalls'] = 0
        result = control_check(self.text, self.trace, self.manifest, 0)
        self.assertFalse(result['coverage']['vdot_writeback_backpressure'])
        self.assertIn('T12_ACCEPTANCE_PENDING', result['status'])


if __name__ == '__main__':
    unittest.main()
