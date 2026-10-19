import copy
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import run_supplements as run

class SupplementTest(unittest.TestCase):
    def setUp(self):
        self.ref=Path("/normal.so")
        self.text="The reference model is /normal.so\nThe first instruction of core 0 has commited. Difftest enabled.\nHIT GOOD TRAP\n"
        self.manifest={"expected_vdot_commits":1158}
        self.observation=dict(status="O2_TRACE_PASS",counts={"COMMIT":1158},pending_count=0,unfinished_rob_count=0)
        self.analyze=types.SimpleNamespace(
            analyze=lambda text,require_complete: copy.deepcopy(self.observation),
            extract_events_and_uart=lambda text:([],text))
        self.workload=types.SimpleNamespace(
            check=lambda *args:dict(status="O2_DIAGNOSTIC_PASS",checked_register_bytes=5120),
            check_control=lambda *args:dict(status="O2_CONTROL_DIAGNOSTIC_PASS",checked_register_bytes=131072))

    def evaluate(self,**changes):
        args=dict(text=self.text,exit_code=0,kind="diagnostic",manifest=self.manifest,
                  reference=self.ref,analyze=self.analyze,workload=self.workload)
        args.update(changes)
        return run.evaluate(**args)

    def test_positive_preserves_trace_counts(self):
        observed,uart,result=self.evaluate()
        self.assertEqual(observed["counts"],{"COMMIT":1158})
        self.assertEqual(result["status"],"O2_DIAGNOSTIC_PASS")

    def test_runtime_failure_and_timeout_rejected(self):
        for code in [1,124,-9,False]:
            with self.subTest(code=code),self.assertRaises(ValueError):
                self.evaluate(exit_code=code)
        for marker in ["ABORT","EXCEEDING CYCLE/INSTR LIMIT","HIT BAD TRAP","different at pc"]:
            with self.subTest(marker=marker),self.assertRaises(ValueError):
                self.evaluate(text=self.text+marker)

    def test_reference_and_banner_are_mandatory(self):
        for text in [self.text.replace("/normal.so","/other.so"),self.text.replace("Difftest enabled.","disabled")]:
            with self.assertRaises(ValueError):
                self.evaluate(text=text)

    def test_partial_or_unfinished_trace_rejected(self):
        for changes in [dict(status="O2_PARTIAL_TRACE_AUDIT"),dict(pending_count=1),
                        dict(unfinished_rob_count=1),dict(counts={"COMMIT":1157}),
                        dict(counts={"COMMIT":1158,"FULL_STALL":True})]:
            old=copy.deepcopy(self.observation)
            self.observation.update(changes)
            with self.assertRaises(ValueError):
                self.evaluate()
            self.observation=old

    def test_manifest_or_checker_status_mismatch(self):
        with self.assertRaises(ValueError):
            self.evaluate(manifest={"expected_vdot_commits":1208})
        self.workload.check=lambda *args:dict(status="PASS",checked_register_bytes=5120)
        with self.assertRaises(ValueError):
            self.evaluate()

    def records(self):
        return [dict(name=name,status="O2_SUPPLEMENT_PASS",observation_status="O2_TRACE_PASS",
                     exit_code=0,observation_counts={"COMMIT":spec["commits"]},
                     expected_vdot_commits=spec["commits"]) for name,spec in run.JOBS.items()]

    def test_assess_inventory_and_counts(self):
        records=self.records()
        self.assertTrue(run.assess(records))
        self.assertFalse(run.assess(records[:1]))
        self.assertFalse(run.assess([records[0],records[0]]))
        records[0]["observation_counts"]["COMMIT"]-=1
        self.assertFalse(run.assess(records))

    def test_failed_record_cannot_supply_union_coverage(self):
        records=self.records()
        records[0].update(status="FAILED",observation_counts={"COMMIT":1158,**{key:1 for key in run.suite.O2_REQUIRED_COVERAGE}})
        union=run.suite.coverage_union(records)
        self.assertFalse(union["complete"])
        self.assertEqual(union["missing"],list(run.suite.O2_REQUIRED_COVERAGE))

    def test_file_drift_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"input"
            p.write_bytes(b"first")
            wanted={str(p):run.suite.sha(p)}
            run.verify_files(wanted)
            p.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                run.verify_files(wanted)

    def test_recheck_rejects_altered_raw_before_analysis(self):
        # Minimal sealed job reaches the raw hash gate without any real EMU.
        import json
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            manifest=b'{"expected_vdot_commits":1158}\n'
            (directory/"input-manifest.json").write_bytes(manifest)
            command=["timeout","120m","stdbuf","-o0","-e0","/emu","-i","/build/o2-diag.bin",
                     "--flash=/flash","--ram-size=128MB","--diff=/normal.so","--max-cycles=5000000"]
            spec=run.JOBS["o2-diagnostic"]
            record=dict(name="o2-diagnostic",kind="diagnostic",command=command,
                        archived_manifest_sha256=run.suite.sha(directory/"input-manifest.json"),
                        input_manifest_sha256=run.suite.sha(directory/"input-manifest.json"),
                        files={"/build/o2-diag.bin":spec["image_sha256"],"/flash":run.suite.FROZEN["flash"],
                               "/normal.so":run.suite.FROZEN["reference"]},
                        raw_logs_sha256={"stdout.log":"0"*64,"stderr.log":"0"*64,"run.log":"0"*64})
            for name in ["runtime.json","result.json"]:
                (directory/name).write_text(json.dumps(record))
            (directory/"build-receipt.json").write_text(json.dumps(dict(kind="diagnostic",images_sha256={"o2-diag.bin":spec["image_sha256"]})))
            (directory/"stdout.log").write_text("changed")
            with self.assertRaisesRegex(ValueError,"raw stream"):
                run.recheck_job(directory,self.analyze,self.workload)

if __name__=="__main__":
    unittest.main()
