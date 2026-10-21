"""Acceptance checks for paired identity, sample matching, and replay rejection."""
import copy
import importlib.util
from pathlib import Path
import unittest
import tempfile

path = Path(__file__).with_name("compare.py")
spec = importlib.util.spec_from_file_location("paired_compare", path)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def pins():
    common=dict(files={"src/a":"1"},dependency_files={"dep/a":"2"},config="MinimalConfig",
                NUM_CORES=1,EMU_THREADS=1,JVM_XMX="12G",BUILD_JOBS=2,
                source_commit="a"*40,
                native_build_contract=dict(schema=2,make_args=list(compare.build_recipe.MAKE_ARGS),
                    mill_launch=["/tools/bash", "/tools/mill"],
                    launch_metadata={".mill-version":dict(sha256="d"*64,value="0.12.3")},
                    environment_sha256="a"*64,recipe_sha256="b"*64,
                    compilers={role:dict(path="/tools/"+role,sha256="c"*64,version="v1")
                               for role in ("cxx","cc","java","bash","mill","verilator","verilator_bin","firtool")}),
                VDOT_T14_FUSED_INPUT="1",VDOT_T12_TRACE="0",VDOT_T13_TRACE="1")
    return (dict(copy.deepcopy(common),VDOT_O1_HANDOFF="1",VDOT_O2_ELASTIC="0",VDOT_O1_TRACE="1",VDOT_O2_TRACE="0",VDOT_O1_TRACE_PROFILE="events"),
            dict(copy.deepcopy(common),VDOT_O1_HANDOFF="0",VDOT_O2_ELASTIC="1",VDOT_O1_TRACE="0",VDOT_O2_TRACE="1"))


def samples():
    result = []
    for mode in compare.MODES:
        for scenario in compare.SCENARIOS:
            for dataset in range(3):
                for repeat in range(2, 6):
                    for method in ("vdot", "rvv"):
                        cycle = 200 if method == "rvv" else 80 if mode == "o2" else 100
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
                               samples=[dict(seq=0, cycles=100 if mode == "o1" else 80, instructions=10)]))
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

    def test_contract_source_profile_and_boolean_counts_fail_closed(self):
        mutations = [lambda a,b: b.pop("native_build_contract"),
                     lambda a,b: b["native_build_contract"].update(environment_sha256="d"*64),
                     lambda a,b: b.update(source_commit="b"*40),
                     lambda a,b: a.update(VDOT_O1_TRACE_PROFILE="frames")]
        for key in ("NUM_CORES", "EMU_THREADS", "BUILD_JOBS"):
            mutations.append(lambda a,b,key=key: (a.update({key: True}), b.update({key: True})))
        for mutation in mutations:
            a,b = pins()
            mutation(a,b)
            with self.assertRaises(ValueError):
                compare.validate_pair(a,b)


class CurrentWindowCheckerCompatibility(unittest.TestCase):
    def checker(self):
        return compare.load_module("o2_current_window_checker_test",
                    compare.ROOT / "team/workloads/unified-vdot/check.py")

    def test_generated_runtime_command_passes_actual_shared_gate(self):
        command = compare.runtime_command("/current/emu", "/images/work.bin", "/reference/model.so", "/flash/boot.bin")
        self.assertEqual(self.checker().runtime_roles(command),
                         dict(emu="/current/emu",image="/images/work.bin",
                              reference="/reference/model.so",flash="/flash/boot.bin"))

    def test_shared_gate_still_rejects_duplicate_unknown_and_unsupported_wrappers(self):
        command = compare.runtime_command("/emu", "/image", "/reference", "/flash")
        for mutated in (command+["--seed=1"], command+["--unknown=1"],
                        command[:2]+["stdbuf","-o0","-e0"]+command[2:]):
            with self.assertRaises(ValueError):
                self.checker().runtime_roles(mutated)

    def test_saved_checker_capsule_reconstructs_transitive_provenance_import(self):
        checker = self.checker()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for source in compare.window_checker_sources(checker):
                destination=root/source.relative_to(compare.ROOT)
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(source.read_bytes())
                self.assertEqual(compare.sha(destination),compare.sha(source))
            restored=compare.load_module("o2_restored_window_checker_test",
                        root/"team/workloads/unified-vdot/check.py")
            command=compare.runtime_command("/emu","/image","/reference","/flash")
            self.assertEqual(restored.runtime_roles(command),checker.runtime_roles(command))
            self.assertEqual(Path(restored._provenance.__file__), root/"team/workloads/vdot-perf/check.py")


class Samples(unittest.TestCase):
    def test_ratio_and_reduction_use_each_modes_actual_rvv(self):
        rows = samples()
        for row in rows:
            if row["mode"] == "o2" and row["method"] == "rvv":
                row["cycles"] = 180
        result = compare.summarize(rows)
        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result[0]["custom_cycle_reduction"], 0.2)
        self.assertEqual(result[0]["o1"]["speedup_ratio_of_sums"], 2)
        self.assertEqual(result[0]["o2"]["speedup_ratio_of_sums"], 2.25)
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
            if row["mode"] == "o2" and row["method"] == "vdot":
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




class ObserverGates(unittest.TestCase):
    def test_complete_matching_modes(self):
        compare.observer_gate("o1",dict(status="O1_TRACE_PASS",schema={"handoff":1},counts={"COMMIT":2}),2)
        compare.observer_gate("o2",dict(status="O2_TRACE_PASS",schema={"slots":2},counts={"COMMIT":2},
                                      pending_count=0,pending_div_count=0,unfinished_rob_count=0),2)

    def test_wrong_observer_or_pending_cannot_be_performance_pass(self):
        base=dict(status="O2_TRACE_PASS",schema={"slots":2},counts={"COMMIT":2},
                  pending_count=0,pending_div_count=0,unfinished_rob_count=0)
        for patch in (dict(status="O2_PARTIAL_TRACE_AUDIT"),dict(pending_count=1),
                      dict(pending_div_count=1),dict(unfinished_rob_count=1),dict(counts={"COMMIT":1})):
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                compare.observer_gate("o2",dict(base,**patch),2)
        with self.assertRaises(ValueError):
            compare.observer_gate("o1",dict(status="O1_TRACE_PASS",schema={"handoff":0},counts={"COMMIT":2}),2)

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
