"""Acceptance checks for paired identity, sample matching, and replay rejection."""
import copy
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).with_name("compare.py")
spec = importlib.util.spec_from_file_location("paired_compare", path)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def pins():
    common = dict(files={"src/a": "1"}, dependency_files={"dep/a": "2"}, config="MinimalConfig",
                  NUM_CORES=1, EMU_THREADS=1, JVM_XMX="12G", BUILD_JOBS=2,
                  VDOT_T14_FUSED_INPUT="1", VDOT_O1_TRACE="1", VDOT_T12_TRACE="0", VDOT_T13_TRACE="1")
    return copy.deepcopy(dict(common, VDOT_O1_HANDOFF="0")), copy.deepcopy(dict(common, VDOT_O1_HANDOFF="1"))


def samples():
    result = []
    for mode in compare.MODES:
        for scenario in compare.SCENARIOS:
            for dataset in range(3):
                for repeat in range(2, 6):
                    for method in ("vdot", "rvv"):
                        cycle = 200 if method == "rvv" else 80 if mode == "o1" else 100
                        result.append(dict(mode=mode, stage="performance", phase="measured", replay=0,
                                           scenario=scenario, method=method, dataset=dataset, repeat=repeat,
                                           cycles=cycle, dots=128, instructions=10 if method == "vdot" else 20,
                                           n=32, seq=repeat * 2 + (method == "rvv"),
                                           image_sha256=scenario + str(dataset)))
    return result


def replay_rows():
    result = []
    for replay in (0, 1, 2):
        for mode in compare.MODES:
            result.append(dict(mode=mode, image="batch", replay=replay,
                               samples=[dict(seq=0, cycles=100 if mode == "t14" else 80, instructions=10)]))
    return result


class PairIdentity(unittest.TestCase):
    def test_only_handoff_difference_allowed(self):
        self.assertTrue(compare.validate_pair(*pins()))

    def test_equal_handoff_modes_rejected(self):
        a, b = pins()
        b["VDOT_O1_HANDOFF"] = "0"
        with self.assertRaises(ValueError):
            compare.validate_pair(a, b)

    def test_hardware_source_difference_rejected(self):
        a, b = copy.deepcopy(pins())
        b["files"]["src/a"] = "changed"
        with self.assertRaises(ValueError):
            compare.validate_pair(a, b)

    def test_dependency_difference_rejected(self):
        a, b = copy.deepcopy(pins())
        b["dependency_files"]["dep/a"] = "changed"
        with self.assertRaises(ValueError):
            compare.validate_pair(a, b)

    def test_trace_difference_rejected(self):
        a, b = pins()
        b["VDOT_T13_TRACE"] = "0"
        with self.assertRaises(ValueError):
            compare.validate_pair(a, b)

    def test_nonmatching_core_configuration_rejected(self):
        a, b = pins()
        a["NUM_CORES"] = b["NUM_CORES"] = 2
        with self.assertRaises(ValueError):
            compare.validate_pair(a, b)


class Samples(unittest.TestCase):
    def test_ratio_and_reduction_use_each_modes_actual_rvv(self):
        rows = samples()
        for row in rows:
            if row["mode"] == "o1" and row["method"] == "rvv":
                row["cycles"] = 180
        result = compare.summarize(rows)
        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result[0]["custom_cycle_reduction"], 0.2)
        self.assertEqual(result[0]["t14"]["speedup_ratio_of_sums"], 2)
        self.assertEqual(result[0]["o1"]["speedup_ratio_of_sums"], 2.25)
        self.assertAlmostEqual(result[0]["rvv_cycle_reduction"], 0.1)

    def test_missing_window_rejected(self):
        with self.assertRaises(ValueError):
            compare.summarize(samples()[:-1])

    def test_duplicate_key_cannot_replace_missing_pair(self):
        rows = samples()
        rows[1] = dict(rows[0])
        with self.assertRaises(ValueError):
            compare.summarize(rows)

    def test_different_retirement_rejected(self):
        rows = samples()
        rows[-1]["instructions"] += 1
        with self.assertRaises(ValueError):
            compare.summarize(rows)

    def test_different_elf_image_rejected(self):
        rows = samples()
        rows[-1]["image_sha256"] = "foreign"
        with self.assertRaises(ValueError):
            compare.summarize(rows)

    def test_different_work_rejected(self):
        rows = samples()
        rows[-1]["dots"] = 64
        with self.assertRaises(ValueError):
            compare.summarize(rows)

    def test_regression_flag_is_preserved(self):
        rows = samples()
        for row in rows:
            if row["mode"] == "o1" and row["method"] == "vdot":
                row["cycles"] = 103
        self.assertTrue(all(r["investigation_required"] for r in compare.summarize(rows)))

    def test_expected_instruction_count_uses_manifest_plan(self):
        manifest = {"rows": [{"method": "vdot", "dots": 128}, {"method": "rvv", "dots": 128}],
                    "plan": [{"index": 0}, {"index": 1}, {"index": 0}]}
        self.assertEqual(compare.expected_commits(manifest), 256)


class Replay(unittest.TestCase):
    def test_matching_replays_pass(self):
        self.assertEqual(compare.compare_replays(replay_rows()), 4)

    def test_changed_cycle_rejected(self):
        rows = replay_rows()
        rows[-1]["samples"][0]["cycles"] += 1
        with self.assertRaises(ValueError):
            compare.compare_replays(rows)

    def test_replays_cannot_be_statistical_extra_samples(self):
        self.assertEqual(compare.summarize(samples() + [
            dict(samples()[0], replay=1)
        ]), compare.summarize(samples()))



class ReferenceBinding(unittest.TestCase):
    def test_one_reference_banner_passes(self):
        compare.validate_loaded_reference("The reference model is /ref.so\n", "/ref.so", lambda x: x)

    def test_duplicate_across_streams_rejected(self):
        with self.assertRaises(ValueError):
            compare.validate_loaded_reference("The reference model is /ref.so\nThe reference model is /ref.so\n",
                                              "/ref.so", lambda x: x)

    def test_foreign_reference_rejected(self):
        with self.assertRaises(ValueError):
            compare.validate_loaded_reference("The reference model is /foreign.so\n", "/ref.so", lambda x: x)


if __name__ == "__main__":
    unittest.main()
