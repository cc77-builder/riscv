"""Ensure trace rechecking rejects plausible but incorrect evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("t15_verify",ROOT/"team/scripts/verify-t15.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def trace():
    common=dict(phase="functional",index="0",reset="0",flush="0",in_valid="0",in_ready="0",
                tag_in="7",out_valid="0",out_ready="1",tag_out="7",result="0000000000000000fffffffffffffff8")
    return [dict(common,cycle="0",in_valid="1",in_ready="1"),
            dict(common,cycle="1"),dict(common,cycle="2",out_valid="1")]


class T15EvidenceTests(unittest.TestCase):
    vectors=[dict(expected_vd="0000000000000000fffffffffffffff8")]

    def test_accept_full_width_trace(self):
        result=module.replay(trace(),self.vectors)
        self.assertEqual(result['counts']['responses'],1)
        self.assertEqual(result['first_valid_ages'],[2])

    def test_high_bit_corruption_rejected(self):
        rows=trace();rows[-1]['result']='8000000000000000fffffffffffffff8'
        with self.assertRaisesRegex(ValueError,'full-128'):module.replay(rows,self.vectors)

    def test_narrow_result_rejected(self):
        rows=trace();rows[-1]['result']='000000000000000000000000fffffff8'
        with self.assertRaisesRegex(ValueError,'full-128'):module.replay(rows,self.vectors)

    def test_wrong_identity_rejected(self):
        rows=trace();rows[-1]['tag_out']='9'
        with self.assertRaisesRegex(ValueError,'identity'):module.replay(rows,self.vectors)

    def test_early_response_rejected(self):
        rows=trace();rows[1]['out_valid']='1'
        with self.assertRaisesRegex(ValueError,'latency'):module.replay(rows,self.vectors)

    def test_cancel_leak_rejected(self):
        rows=trace();rows[-1]['flush']='1'
        with self.assertRaisesRegex(ValueError,'cancellation'):module.replay(rows,self.vectors)

    def test_missing_cycle_rejected(self):
        rows=trace();del rows[1]
        with self.assertRaisesRegex(ValueError,'cycle'):module.replay(rows,self.vectors)

    def test_stall_result_must_remain_bound(self):
        rows=trace();rows[-1]['out_ready']='0'
        rows.append(dict(rows[-1],cycle='3',out_ready='1',result='00000000000000000000000000000000'))
        with self.assertRaisesRegex(ValueError,'full-128'):module.replay(rows,self.vectors)
