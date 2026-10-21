"""Acceptance checks for paired identity, sample matching, and replay rejection."""
import copy
import importlib.util
from pathlib import Path
import unittest
import tempfile
import shlex
from unittest.mock import patch

path = Path(__file__).with_name("compare.py")
spec = importlib.util.spec_from_file_location("paired_compare", path)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)
builder_spec = importlib.util.spec_from_file_location("paired_build_t14", path.with_name("build_t14.py"))
builder = importlib.util.module_from_spec(builder_spec)
builder_spec.loader.exec_module(builder)


def contract():
    return dict(schema=2, make_args=list(compare.build_recipe.MAKE_ARGS), environment_sha256="f" * 64,
                mill_launch=["/tools with spaces/sh", "/tools with spaces/mill"],
                launch_metadata={".mill-version": dict(sha256="c" * 64, value="0.12.3")},
                recipe_sha256="a" * 64, compilers={role: dict(path="/tools with spaces/" + role,
                sha256="b" * 64, version="test version") for role in
                ("cxx", "cc", "java", "bash", "sh", "time", "mill", "verilator", "verilator_bin", "firtool")})


def pins():
    common = dict(files={"src/a": "1"}, dependency_files={"dep/a": "2"}, config="MinimalConfig",
                  NUM_CORES=1, EMU_THREADS=1, JVM_XMX="12G", BUILD_JOBS=2,
                  VDOT_O1_TRACE_PROFILE="events", VDOT_T14_FUSED_INPUT="1", VDOT_O1_TRACE="1", VDOT_T12_TRACE="0", VDOT_T13_TRACE="1",
                  native_build_contract=contract())
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
    def test_missing_or_different_compiler_contract_rejected(self):
        for mutate in (lambda p: p.pop("native_build_contract"),
                       lambda p: p["native_build_contract"]["compilers"]["cxx"].update(sha256="c" * 64),
                       lambda p: p["native_build_contract"].update(environment_sha256="e" * 64)):
            a, b = pins()
            mutate(b)
            with self.assertRaises(ValueError):
                compare.validate_pair(a, b)

    def test_profile_must_be_explicit_events_on_both_modes(self):
        for value in (None, 'frames', 'event', 1):
            a, b = pins()
            for item in (a, b):
                if value is None:
                    item.pop('VDOT_O1_TRACE_PROFILE')
                else:
                    item['VDOT_O1_TRACE_PROFILE'] = value
            with self.assertRaisesRegex(ValueError, 'explicit events'):
                compare.validate_pair(a, b)

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
        for value in (2, True):
            a, b = pins()
            a["NUM_CORES"] = b["NUM_CORES"] = value
            with self.assertRaises(ValueError):
                compare.validate_pair(a, b)


class CurrentReference(unittest.TestCase):
    def test_unbound_hardware_and_compiler_injection_is_not_inherited(self):
        injected = dict(L2_CACHE_SIZE="512", NO_DIFF="1", CPATH="/injected", PGO_CFLAGS="-O0",
                        COMMON_EXTRA_ARGS="--disable-all", VEXTRA_FLAGS="--no-assert",
                        BASH_ENV="/injected.sh", LD_PRELOAD="/injected.so", MAKEFLAGS="-e")
        original = compare.build_recipe.environment()
        with patch.dict(compare.build_recipe.os.environ, injected):
            self.assertEqual(compare.build_recipe.environment(), original)
            self.assertFalse(set(injected) & compare.build_recipe.environment().keys())

    def reference(self):
        _, p = pins()
        p.update(emu_sha256="d" * 64, source_commit="a" * 40)
        state = dict(status="O1_FULLCORE_BUILD_PASS", build_exit_code=0, emu_sha256="d" * 64,
                     source_commit="a" * 40)
        return p, state

    def validate(self, p, state):
        builder.validate_reference(p, state, {"src/a": "1"}, {"dep/a": "2"}, contract(), "d" * 64)

    def test_current_completed_reference_accepted(self):
        self.validate(*self.reference())

    def test_failed_build_or_wrong_binary_rejected(self):
        for key, value in (("status", "FAILED"), ("build_exit_code", 1), ("build_exit_code", False), ("emu_sha256", "e" * 64),
                           ("source_commit", "b" * 40)):
            p, state = self.reference()
            state[key] = value
            with self.assertRaises(ValueError):
                self.validate(p, state)

    def test_reference_must_match_sources_and_mode(self):
        for key, value in (("files", {"src/foreign": "1"}), ("dependency_files", {}),
                           ("VDOT_O1_HANDOFF", "0"), ("VDOT_O1_TRACE_PROFILE", "frames"),
                           ("NUM_CORES", True), ("native_build_contract", None)):
            p, state = self.reference()
            p[key] = value
            with self.assertRaises(ValueError):
                self.validate(p, state)

    def test_make_command_quotes_paths_and_selects_actual_compilers(self):
        command = compare.build_recipe.make_command(contract(), "/new output/$(touch unexpected)")
        args = shlex.split(command)
        self.assertIn("CXX=/tools with spaces/cxx", args)
        self.assertIn("CC=/tools with spaces/cc", args)
        self.assertIn("SHELL=/tools with spaces/bash", args)
        self.assertIn("BUILD_DIR=/new output/$(touch unexpected)", args)
        self.assertEqual(args[:2], ["make", "emu"])

    def test_recipe_drift_rejected_before_reuse(self):
        changed = contract()
        changed["compilers"]["firtool"]["sha256"] = "e" * 64
        with patch.object(compare.build_recipe, "capture", return_value=changed):
            with self.assertRaisesRegex(ValueError, "contract changed"):
                compare.build_recipe.verify(Path("."), contract())


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



class GeneratedInputScope(unittest.TestCase):
    def module(self):
        return compare.load_module("resume_scope_test", Path(__file__).with_name("resume_t14.py"))

    def test_only_root_host_timing_log_is_excluded(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            products = Path(temp)
            (products / "time.log").write_text("host output")
            (products / "rtl").mkdir()
            nested = products / "rtl/time.log"
            nested.write_text("keep this input")
            rtl = products / "rtl/top.sv"
            rtl.write_text("module top; endmodule")
            inventory = module.generated_input_inventory(products)
            self.assertNotIn(str(products / "time.log"), inventory)
            self.assertIn(str(nested), inventory)
            self.assertIn(str(rtl), inventory)

    def test_rtl_change_is_still_detected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            products = Path(temp)
            rtl = products / "top.sv"
            rtl.write_text("first")
            before = module.generated_input_inventory(products)
            rtl.write_text("second")
            after = module.generated_input_inventory(products)
            self.assertNotEqual(before[str(rtl)], after[str(rtl)])


if __name__ == "__main__":
    unittest.main()
