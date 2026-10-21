"""Acceptance checks for paired identity, sample matching, and replay rejection."""
import copy
import importlib.util
from pathlib import Path
import unittest
import tempfile
import threading
import time

path = Path(__file__).with_name("compare.py")
spec = importlib.util.spec_from_file_location("paired_compare", path)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def pins():
    common=dict(files={"src/a":"1","build.sc":"old", "src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala":"old"},
                dependency_files={"dep/a":"2"},config="MinimalConfig",
                NUM_CORES=1,EMU_THREADS=1,JVM_XMX="12G",BUILD_JOBS=2,
                VDOT_T14_FUSED_INPUT="1",VDOT_T12_TRACE="0",VDOT_T13_TRACE="1",
                VDOT_O1_HANDOFF="0",VDOT_O2_ELASTIC="1",VDOT_O1_TRACE="0",VDOT_O2_TRACE="1")
    other=copy.deepcopy(common)
    other["files"]["build.sc"]="new"
    other["files"]["src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"]="new"
    return common,other


def samples():
    result = []
    for mode in compare.MODES:
        for scenario in compare.SCENARIOS:
            for dataset in range(3):
                for repeat in range(2, 6):
                    for method in ("vdot", "rvv"):
                        cycle = 200 if method == "rvv" else 80 if mode == "h1" else 100
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
                               samples=[dict(seq=0, cycles=100 if mode == "b0" else 80, instructions=10)]))
    return result


class PairIdentity(unittest.TestCase):
    def test_only_legal_mode_and_observer_difference_allowed(self):
        self.assertTrue(compare.validate_pair(*pins()))

    def test_illegal_mode_pairing_rejected(self):
        a, b = pins()
        b["VDOT_O2_ELASTIC"] = "0"
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
            if row["mode"] == "h1" and row["method"] == "rvv":
                row["cycles"] = 180
        result = compare.summarize(rows)
        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result[0]["custom_cycle_reduction"], 0.2)
        self.assertEqual(result[0]["b0"]["speedup_ratio_of_sums"], 2)
        self.assertEqual(result[0]["h1"]["speedup_ratio_of_sums"], 2.25)
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
            if row["mode"] == "h1" and row["method"] == "vdot":
                row["cycles"] = 103
        self.assertTrue(all(r["investigation_required"] for r in compare.summarize(rows)))

    def test_expected_instruction_count_uses_manifest_plan(self):
        manifest = {"rows": [{"method": "vdot", "dots": 128}, {"method": "rvv", "dots": 128}],
                    "plan": [{"index": 0}, {"index": 1}, {"index": 0}]}
        self.assertEqual(compare.expected_commits(manifest), 256)


class Replay(unittest.TestCase):
    def test_repeated_image_pairs_never_overlap(self):
        active = 0
        peak = 0
        order = []
        lock = threading.Lock()

        def pair(task):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
                order.append(("start", task))
            time.sleep(0.02)
            with lock:
                order.append(("end", task))
                active -= 1
            return task

        result = compare.execute_stage_pairs("replay", [1, 2], pair)
        self.assertEqual(sorted(result), [1, 2])
        self.assertEqual(peak, 1)
        self.assertEqual(order, [("start", 1), ("end", 1), ("start", 2), ("end", 2)])

    def test_distinct_images_can_run_in_parallel(self):
        barrier = threading.Barrier(2)

        def pair(task):
            barrier.wait(timeout=5)
            return task

        self.assertEqual(sorted(compare.execute_stage_pairs("performance", [1, 2], pair)), [1, 2])

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




class ObserverGates(unittest.TestCase):
    def test_complete_matching_modes(self):
        for mode in compare.MODES:
            compare.observer_gate(mode,dict(status="O2_TRACE_PASS",schema={"slots":2},
                counts={"COMMIT":2},pending_count=0,pending_div_count=0,unfinished_rob_count=0),2)

    def test_wrong_observer_or_pending_cannot_pass(self):
        base=dict(status="O2_TRACE_PASS",schema={"slots":2},counts={"COMMIT":2},
                  pending_count=0,pending_div_count=0,unfinished_rob_count=0)
        for mode in compare.MODES:
            for patch in (dict(status="O1_TRACE_PASS"),dict(pending_count=1),
                          dict(pending_div_count=1),dict(unfinished_rob_count=1),
                          dict(counts={"COMMIT":1}),dict(schema={"slots":1})):
                with self.subTest(mode=mode,patch=patch),self.assertRaises(ValueError):
                    compare.observer_gate(mode,dict(base,**patch),2)

class StrictNonRegression(unittest.TestCase):
    def test_one_cycle_regression_not_hidden_by_mean(self):
        rows=samples()
        for s in rows:
            if s["method"]=="vdot":s["cycles"]=100 if s["mode"]=="b0" else 99
        target=next(s for s in rows if s["mode"]=="h1" and s["scenario"]=="single" and s["method"]=="vdot")
        target["cycles"]=101
        self.assertTrue(compare.summarize(rows)[0]["investigation_required"])
        self.assertEqual(sum(s["delta_cycles"]>0 for s in compare.paired_deltas(rows)),1)

    def test_equal_integer_windows_pass(self):
        rows=samples()
        for s in rows:s["cycles"]=100
        self.assertEqual(len(compare.paired_deltas(rows)),96)
        self.assertTrue(all(s["delta_cycles"]==0 for s in compare.paired_deltas(rows)))

    def test_rvv_regression_reported(self):
        rows=samples()
        next(s for s in rows if s["mode"]=="h1" and s["method"]=="rvv")["cycles"]+=1
        self.assertTrue(compare.summarize(rows)[0]["investigation_required"])

    def test_zero_or_noninteger_rejected(self):
        for value in (0,-1,1.5,True):
            rows=samples();rows[0]["cycles"]=value
            with self.assertRaises(ValueError):compare.paired_deltas(rows)

    def test_missing_cross_version_identity_rejected(self):
        rows=samples();rows[-1]["seq"]+=100
        with self.assertRaises(ValueError):compare.paired_deltas(rows)

    def test_build_entry_extra_change_rejected(self):
        from build_profile import validate_build_sc,O4_ENTRY
        validate_build_sc("before\\nafter", "before\\n"+O4_ENTRY+"after")
        with self.assertRaises(ValueError):
            validate_build_sc("before\\nafter", "different\\n"+O4_ENTRY+"after")

    def test_monitor_external_effects_rejected(self):
        from build_profile import monitor_effect_check
        monitor_effect_check('input clock; $fwrite(2, "output");')
        for text in ('output y;', 'inout y;', 'import "DPI-C" function f();', '$finish;', 'force y=1;'):
            with self.assertRaises(ValueError):monitor_effect_check(text)

class BuildSettings(unittest.TestCase):
    def test_only_product_path_normalizes(self):
        from build_profile import normalized_verilator
        a="time -avp -o /one/time.log verilator --exe -O3 --cc --threads 1 -I/one/rtl"
        b=a.replace("/one","/two")
        self.assertEqual(normalized_verilator(a,Path("/one")),normalized_verilator(b,Path("/two")))
        self.assertNotEqual(normalized_verilator(a+" -DCHANGED",Path("/one")),normalized_verilator(b,Path("/two")))

    def test_duplicate_or_wrong_thread_command_rejected(self):
        from build_profile import normalized_verilator
        line="verilator --exe -O3 --cc --threads 1 -I/a/rtl"
        for bad in (line+"\n"+line,line.replace("--threads 1","--threads 2"),"no command"):
            with self.assertRaises(ValueError):
                normalized_verilator(bad,Path("/a"))

if __name__ == "__main__":
    unittest.main()
