"""Regression tests for the pinned XiangShan/NEMU trap-reset compatibility gate."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('reset_artifact_guard',Path(__file__).resolve().parents[1]/'scripts/artifact_guard.py')
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
class ResetPolicyTests(unittest.TestCase):
    def test_target_compatible(self):
        guard.check_xiangshan_reset_config(['CONFIG_NMIE_INIT=y','# CONFIG_MDT_INIT is not set'])
    def test_initial_nmi_disabled_rejected(self):
        with self.assertRaises(ValueError):
            guard.check_xiangshan_reset_config(['# CONFIG_NMIE_INIT is not set','# CONFIG_MDT_INIT is not set'])
    def test_initial_double_trap_enabled_rejected(self):
        with self.assertRaises(ValueError):
            guard.check_xiangshan_reset_config(['CONFIG_NMIE_INIT=y','CONFIG_MDT_INIT=y'])
    def test_missing_policy_rejected(self):
        with self.assertRaises(ValueError):
            guard.check_xiangshan_reset_config([])
    def test_contradictory_policy_rejected(self):
        with self.assertRaises(ValueError):
            guard.check_xiangshan_reset_config(['CONFIG_NMIE_INIT=y','# CONFIG_MDT_INIT is not set','CONFIG_MDT_INIT=y'])
    def test_contradictory_nmie_rejected(self):
        with self.assertRaises(ValueError):
            guard.check_xiangshan_reset_config(['CONFIG_NMIE_INIT=y','# CONFIG_NMIE_INIT is not set','# CONFIG_MDT_INIT is not set'])
if __name__=='__main__':unittest.main()
