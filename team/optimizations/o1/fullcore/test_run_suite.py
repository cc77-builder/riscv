"""Host-only behavior checks: no XiangShan emulator or RTL build is executed."""
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest

import run_suite as runner


def negative_text(vd=10, pc="0x80001bdc", word="0x0294050b", right="0x0000001000000000", wrong="0x0"):
    return (f"DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd={vd} pc={pc} instruction={word}\n"
            f"v{vd}_high different at pc = {pc}, right= {right}, wrong = {wrong}\n")


def passing_records():
    rows = [{"name": "hello-vadd", "status": "HELLO_VADD_PASS"},
            {"name": "negative-vdot", "status": "EXPECTED_VDOT_HIGHBIT_REJECTION",
             "files": {"/frozen/image.bin": "abc"}, "finished": "2026-10-18T12:00:01+08:00"},
            {"name": "control", "status": "O1_CONTROL_REGRESSION_PASS"},
            {"name": "dense-batch128", "status": "O1_DENSE_HANDOFF_AND_WINDOWS_PASS"}]
    for i in range(8):
        rows.append({"name": f"functional-{i}", "status": "VDOT_MATRIX_SHARD_PASS",
                     "files": {"/frozen/image.bin": "abc"}, "started": "2026-10-18T12:00:02+08:00"})
    for row in rows:
        row["observation_status"] = "O1_PARTIAL_TRACE_AUDIT" if row["name"] == "negative-vdot" else "O1_TRACE_PASS"
    return rows


class FullcoreRunnerTests(unittest.TestCase):
    def test_negative_binds_exit_pc_destination_instruction_and_bit(self):
        accepted = runner.validate_negative(negative_text(), 1)
        self.assertEqual((accepted["vd"], accepted["bit"]), (10, 100))
        for status in (0, 2, 3, 124, 134, -9):
            with self.subTest(status=status):
                with self.assertRaises(ValueError):
                    runner.validate_negative(negative_text(), status)
        bad = [negative_text(vd=9), negative_text(word="0x02940557"),
               negative_text(right="0x2000000000"), negative_text(right="0x1000000001"),
               negative_text().replace("different at pc = 0x80001bdc", "different at pc = 0x80001be0"),
               negative_text().replace("v10_high different", "v11_high different"),
               negative_text() + negative_text(), negative_text() + "HIT GOOD TRAP\n",
               negative_text() + "NEGATIVE_FIXTURE_SETUP_FAIL original reference load\n",
               negative_text() + "v11_high different at pc = 0x80001bdc, right= 0x1, wrong = 0x0\n",
               negative_text().replace("bit=100", "bit=99"), ""]
        for index, text in enumerate(bad):
            with self.subTest(case=index):
                with self.assertRaises(ValueError):
                    runner.validate_negative(text, 1)

    def test_unrelated_failure_markers_cannot_hide_behind_negative_detection(self):
        for message in ("Assertion at arbitrary/file.scala:42 failed", "ABORT", "HIT BAD TRAP"):
            for negative in (False, True):
                with self.subTest(message=message, negative=negative):
                    with self.assertRaises(ValueError):
                        runner.validate_failure_markers(message, negative=negative)
            with self.assertRaises(ValueError):
                runner.validate_negative(negative_text() + message, 1)
        for message in ("DIFFTEST FAIL", "v10_high different at pc = 0x80000000"):
            with self.assertRaises(ValueError):
                runner.validate_failure_markers(message)
        runner.validate_failure_markers("DIFFTEST FAIL", negative=True)

    def test_partial_observation_never_passes_normal_job(self):
        runner.validate_observation({"status": "O1_TRACE_PASS"})
        runner.validate_observation({"status": "O1_PARTIAL_TRACE_AUDIT"}, negative=True)
        for status, negative in (("O1_PARTIAL_TRACE_AUDIT", False), ("O1_TRACE_PASS", True),
                                 ("PASS", False), ("O1_TRACE_FAIL", True)):
            with self.assertRaises(ValueError):
                runner.validate_observation({"status": status}, negative=negative)

    def test_diff_runtime_reference_path_is_exact_and_unique(self):
        banner = "The first instruction of core 0 has commited. Difftest enabled.\n"
        runner.validate_runtime(banner + "The reference model is /frozen/ref.so\n", Path("/frozen/ref.so"))
        for text in (banner, "The reference model is /frozen/ref.so\n",
                     banner + "The reference model is /frozen/ref.so.extra\n",
                     banner + "The reference model is /wrong/ref.so\n",
                     banner + "The reference model is /frozen/ref.so\n" * 2):
            with self.assertRaises(ValueError):
                runner.validate_runtime(text, Path("/frozen/ref.so"))

    def test_pin_modes_types_and_paths_fail_closed(self):
        pins = dict(runner.PIN_FIELDS, source_commit="a" * 40, emu_sha256="b" * 64,
                    files={"src/real.scala": "c" * 64}, dependency_files={"utility/real.scala": "d" * 64})
        runner.validate_pin_fields(pins)
        for key in runner.PIN_FIELDS:
            bad = copy.deepcopy(pins)
            bad.pop(key)
            with self.subTest(missing=key):
                with self.assertRaises(ValueError):
                    runner.validate_pin_fields(bad)
        for value in ("../outside", "/absolute/outside"):
            bad = copy.deepcopy(pins); bad["files"] = {value: "c" * 64}
            with self.assertRaises(ValueError):
                runner.validate_pin_fields(bad)
        for key, value in (("VDOT_T12_TRACE", "1"), ("VDOT_O1_TRACE", "0"), ("VDOT_O1_TRACE", 1),
                           ("NUM_CORES", True), ("EMU_THREADS", 2), ("files", {}), ("source_commit", "short")):
            bad = copy.deepcopy(pins); bad[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    runner.validate_pin_fields(bad)

    def test_control_can_defer_only_handoff_to_dense(self):
        control = {"status": "O1_CONTROL_REGRESSION_PASS", "legacy_coverage": {str(i): True for i in range(7)},
                   "legacy_coverage_complete": True, "handoff_coverage_complete": True}
        self.assertEqual(runner.classify_control(control)["status"], "O1_CONTROL_REGRESSION_PASS")
        partial = dict(control, status="O1_COVERAGE_INCOMPLETE", handoff_coverage_complete=False)
        result = runner.classify_control(partial)
        self.assertEqual(result["status"], "O1_CONTROL_LEGACY_COMPLETE_HANDOFF_PENDING")
        self.assertEqual(result["control_coverage_status"], "O1_COVERAGE_INCOMPLETE")
        for index in range(7):
            bad = copy.deepcopy(partial); bad["legacy_coverage"][str(index)] = False
            with self.assertRaises(ValueError):
                runner.classify_control(bad)
        for key, value in (("legacy_coverage_complete", False), ("status", "PASS"),
                           ("legacy_coverage", {}), ("handoff_coverage_complete", None)):
            bad = copy.deepcopy(partial); bad[key] = value
            with self.assertRaises(ValueError):
                runner.classify_control(bad)

    def test_suite_requires_exact_jobs_complete_observations_and_recovery(self):
        rows = passing_records()
        ok, recovery, coverage = runner.assess_suite(rows, Path("/frozen/image.bin"))
        self.assertTrue(ok and recovery)
        self.assertTrue(coverage["handoff_from_dense"])
        for i in range(len(rows)):
            for mutate in ("remove", "failed", "partial", "unknown"):
                bad = copy.deepcopy(rows)
                if mutate == "remove": bad.pop(i)
                elif mutate == "failed": bad[i]["status"] = "FAILED"
                elif mutate == "partial": bad[i]["observation_status"] = "UNKNOWN_PARTIAL"
                else: bad[i]["status"] = "UNKNOWN_SUCCESS"
                with self.subTest(index=i, mutation=mutate):
                    self.assertFalse(runner.assess_suite(bad, Path("/frozen/image.bin"))[0])
        bad = copy.deepcopy(rows); bad.append(copy.deepcopy(rows[0]))
        self.assertFalse(runner.assess_suite(bad, Path("/frozen/image.bin"))[0])
        for field, value in (("files", {"/frozen/image.bin": "different"}),
                             ("started", "2026-10-18T12:00:00+08:00")):
            bad = copy.deepcopy(rows)
            normal = next(r for r in bad if r["name"] == "functional-0"); normal[field] = value
            self.assertFalse(runner.assess_suite(bad, Path("/frozen/image.bin"))[0])

    def test_split_coverage_never_hides_local_control_incompleteness(self):
        rows = passing_records()
        ctl = next(r for r in rows if r["name"] == "control")
        ctl["status"] = "O1_CONTROL_LEGACY_COMPLETE_HANDOFF_PENDING"
        ok, _, coverage = runner.assess_suite(rows, Path("/frozen/image.bin"))
        self.assertTrue(ok)
        self.assertTrue(coverage["coverage_split_across_workloads"])
        self.assertFalse(coverage["handoff_from_control"])
        next(r for r in rows if r["name"] == "dense-batch128")["status"] = "FAILED"
        self.assertFalse(runner.assess_suite(rows, Path("/frozen/image.bin"))[0])

    def test_real_subprocess_keeps_exit_and_separate_streams(self):
        # A host Python fixture, not EMU: exercise OS descriptors and exit status.
        with tempfile.TemporaryDirectory(prefix="o1-runner-host-test-") as temp:
            directory = Path(temp)
            command = [sys.executable, "-B", "-c",
                       "import os,sys;print(os.environ['O1_HOST_FIXTURE']);print('host-stderr',file=sys.stderr);sys.exit(42)"]
            env = os.environ.copy(); env["O1_HOST_FIXTURE"] = "host-stdout"
            rc, hashes = runner.run_process(command, directory, env)
            self.assertEqual(rc, 42)
            self.assertEqual((directory / "stdout.log").read_bytes(), b"host-stdout\n")
            self.assertEqual((directory / "stderr.log").read_bytes(), b"host-stderr\n")
            self.assertEqual((directory / "run.log").read_bytes(), b"host-stderr\nhost-stdout\n")
            self.assertEqual((directory / "exit-code.txt").read_text(), "42\n")
            self.assertTrue(all(runner.sha(directory / name) == value for name, value in hashes.items()))


if __name__ == "__main__":
    unittest.main()
