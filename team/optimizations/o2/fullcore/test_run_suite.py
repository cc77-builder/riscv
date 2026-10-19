"""Host-only behavior checks: no XiangShan emulator or RTL build is executed."""
import copy
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest

import run_suite as runner


def negative_text(vd=10, pc="0x80001bdc", word="0x0294050b", right="0x0000001000000000", wrong="0x0"):
    return (f"DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd={vd} pc={pc} instruction={word}\n"
            f"v{vd}_high different at pc = {pc}, right= {right}, wrong = {wrong}\n"
            "Core 0: \x1b[31mABORT at pc = 0x800016b0\n\x1b[0m")


def passing_records():
    rows = [{"name": "hello-vadd", "status": "HELLO_VADD_PASS"},
            {"name": "negative-vdot", "status": "EXPECTED_VDOT_HIGHBIT_REJECTION",
             "files": {"/frozen/image.bin": "abc"}, "finished": "2026-10-18T12:00:01+08:00"},
            {"name": "control", "status": "O2_CONTROL_LEGACY_PASS"},
            {"name": "dense-batch128", "status": "O2_DENSE_ELASTIC_AND_WINDOWS_PASS"}]
    for i in range(8):
        rows.append({"name": f"functional-{i}", "status": "VDOT_MATRIX_SHARD_PASS",
                     "files": {"/frozen/image.bin": "abc"}, "started": "2026-10-18T12:00:02+08:00"})
    for row in rows:
        row["observation_counts"] = {key: 1 for key in runner.O2_REQUIRED_COVERAGE}
        row["observation_status"] = "O2_PARTIAL_TRACE_AUDIT" if row["name"] == "negative-vdot" else "O2_TRACE_PASS"
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
        with self.assertRaises(ValueError):
            runner.validate_failure_markers("DIFFTEST FAIL", negative=True)

    def test_partial_observation_never_passes_normal_job(self):
        runner.validate_observation({"status": "O2_TRACE_PASS"})
        runner.validate_observation({"status": "O2_PARTIAL_TRACE_AUDIT"}, negative=True)
        for status, negative in (("O2_PARTIAL_TRACE_AUDIT", False), ("O2_TRACE_PASS", True),
                                 ("PASS", False), ("O2_TRACE_FAIL", True)):
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
        for key, value in (("VDOT_T12_TRACE", "1"), ("VDOT_O2_TRACE", "0"), ("VDOT_O2_TRACE", 1),
                           ("NUM_CORES", True), ("EMU_THREADS", 2), ("files", {}), ("source_commit", "short")):
            bad = copy.deepcopy(pins); bad[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    runner.validate_pin_fields(bad)

    def test_control_legacy_gate_and_separate_o2_targets(self):
        control = {"status": "O2_CONTROL_REGRESSION_PASS",
                   "legacy_coverage": {key: True for key in runner.LEGACY_COVERAGE},
                   "legacy_coverage_complete": True,
                   "o2_coverage": {key.lower(): True for key in runner.O2_REQUIRED_COVERAGE},
                   "o2_coverage_complete": True}
        self.assertEqual(runner.classify_control(control)["status"], "O2_CONTROL_LEGACY_PASS")
        partial = copy.deepcopy(control)
        partial.update(status="O2_COVERAGE_INCOMPLETE", o2_coverage_complete=False)
        partial["o2_coverage"]["kill_p"] = False
        self.assertFalse(runner.classify_control(partial)["o2_coverage_complete"])
        for index in range(7):
            bad=copy.deepcopy(partial); bad["legacy_coverage"][runner.LEGACY_COVERAGE[index]]=False
            with self.assertRaises(ValueError): runner.classify_control(bad)
        for field,value in (("o2_coverage_complete",True),("status","PASS"),("o2_coverage",{}),
                            ("legacy_coverage_complete",False),("legacy_coverage",{})):
            bad=copy.deepcopy(partial);bad[field]=value
            with self.assertRaises(ValueError): runner.classify_control(bad)


    def test_real_control_checker_api_connects_to_runner(self):
        # Synthetic hardware trace; exercise the real cross-module API.
        from test_trace import Fixture
        import check_control
        f = Fixture()
        for i in range(5, 8):
            f.enqueue(f"0:{i}", i + 2)
        f.tick("0:5"); f.tick("0:6"); f.tick("0:7")
        f.tick(ready=0, wait="0:8"); f.drain()
        for reverse in (False, True):
            f.enqueue("0:10", 7); f.enqueue("0:11", 8)
            f.tick("0:11" if reverse else "0:10")
            f.tick("0:10" if reverse else "0:11")
            f.tick(ready=0, flush=("0:10", 0), auto_commit=False); f.drain()
        f.tick("0:12", div_fu=1 << 22); f.tick(div_done=True); f.tick()
        for i in range(9):
            rob = f"{i % 2}:20"
            f.enqueue(rob, 7, ftq=f"{i % 2}:1"); f.tick(rob); f.drain()
        text = ("The reference model is synthetic\n"
                "The first instruction of core 0 has commited. Difftest enabled.\n" + f.text() +
                "T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1\n" +
                "".join(f"T12_GROUP_PASS id={i} checkpoints=32 bytes=16384\n" for i in range(4)) +
                "T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0\nHIT GOOD TRAP\n")
        result = check_control.check(text, {"groups": [{"vdot_count": 14}],
                    "speculation": {"expected_architectural_vdot": 0}}, 0)
        qualified = runner.classify_control(result)
        self.assertEqual(qualified["status"], "O2_CONTROL_LEGACY_PASS")
        self.assertEqual(set(qualified["o2_coverage"]), set(runner.O2_REQUIRED_COVERAGE))
        self.assertTrue(qualified["o2_coverage_complete"])

    def test_suite_requires_exact_jobs_complete_observations_and_recovery(self):
        rows = passing_records()
        ok, recovery, coverage = runner.assess_suite(rows, Path("/frozen/image.bin"))
        self.assertTrue(ok and recovery)
        self.assertTrue(coverage["dense_elastic_complete"])
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

    def test_union_keeps_missing_targets_and_only_qualified_sources(self):
        rows=passing_records()
        for row in rows: row["observation_counts"]={}
        core_ok, _, coverage=runner.assess_suite(rows,Path("/frozen/image.bin"))
        self.assertTrue(core_ok)
        self.assertFalse(coverage["complete"])
        self.assertEqual(set(coverage["missing"]),set(runner.O2_REQUIRED_COVERAGE))
        for index,key in enumerate(runner.O2_REQUIRED_COVERAGE):
            rows[index]["observation_counts"][key]=1
        # Index1 is the negative partial run: its target cannot count.
        self.assertIn(runner.O2_REQUIRED_COVERAGE[1],runner.coverage_union(rows)["missing"])
        rows[0]["observation_counts"][runner.O2_REQUIRED_COVERAGE[1]]=1
        self.assertTrue(runner.coverage_union(rows)["complete"])
        failed={"name":"bad","status":"FAILED","observation_status":"O2_TRACE_PASS",
                "observation_counts":{key:100 for key in runner.O2_REQUIRED_COVERAGE}}
        self.assertFalse(runner.coverage_union([failed])["complete"])
        for bad in (True,-1,1.5,"1"):
            rows=passing_records();rows[0]["observation_counts"]["KILL_P"]=bad
            with self.assertRaises(ValueError):runner.coverage_union(rows)

    def test_scheduler_smoke_recovery_order_and_two_worker_limit(self):
        for workers in (1, 2):
            lock = threading.Lock()
            independent_started = threading.Event()
            flags = {"smoke": False, "negative_done": False, "active": 0, "peak": 0}
            progress = []
            names = ["hello", "negative", "recovery", "independent", "other"]
            def worker(name):
                with lock:
                    if name != "hello":
                        self.assertTrue(flags["smoke"])
                    flags["active"] += 1
                    flags["peak"] = max(flags["peak"], flags["active"])
                try:
                    if name == "hello":
                        flags["smoke"] = True
                    elif name == "negative":
                        if workers == 2:
                            self.assertTrue(independent_started.wait(5),
                                            "second worker remained idle during negative")
                        flags["negative_done"] = True
                    elif name == "recovery":
                        self.assertTrue(flags["negative_done"])
                    elif name == "independent":
                        independent_started.set()
                    return {"name": name, "status": "HOST_FIXTURE"}
                finally:
                    with lock:
                        flags["active"] -= 1
            rows = runner.execute_jobs([(name,) for name in names], worker, workers,
                                       lambda rows: progress.append([r["name"] for r in rows]))
            ordered = [r["name"] for r in rows]
            self.assertEqual(ordered[0], "hello")
            self.assertLess(ordered.index("negative"), ordered.index("recovery"))
            self.assertEqual(set(ordered), set(names))
            self.assertEqual(len(rows), len(names))
            self.assertEqual(flags["peak"], workers)
            self.assertEqual(progress[-1], ordered)
        with self.assertRaises(ValueError):
            runner.execute_jobs([], lambda: None, 4, lambda _: None)

    def test_real_subprocess_keeps_exit_and_separate_streams(self):
        # A host Python fixture, not EMU: exercise OS descriptors and exit status.
        with tempfile.TemporaryDirectory(prefix="o2-runner-host-test-") as temp:
            directory = Path(temp)
            command = [sys.executable, "-B", "-c",
                       "import os,sys;print(os.environ['O2_HOST_FIXTURE']);print('host-stderr',file=sys.stderr);sys.exit(42)"]
            env = os.environ.copy(); env["O2_HOST_FIXTURE"] = "host-stdout"
            rc, hashes = runner.run_process(command, directory, env)
            self.assertEqual(rc, 42)
            self.assertEqual((directory / "stdout.log").read_bytes(), b"host-stdout\n")
            self.assertEqual((directory / "stderr.log").read_bytes(), b"host-stderr\n")
            self.assertEqual((directory / "run.log").read_bytes(), b"host-stderr\nhost-stdout\n")
            self.assertEqual((directory / "exit-code.txt").read_text(), "42\n")
            self.assertTrue(all(runner.sha(directory / name) == value for name, value in hashes.items()))


if __name__ == "__main__":
    unittest.main()
