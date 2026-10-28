"""Host-only adversarial evidence tests. No target program is executed."""
from pathlib import Path
from types import SimpleNamespace
import ast
import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("expanded_raw_audit_tests", HERE/"raw_audit.py")
audit = importlib.util.module_from_spec(sp)
sp.loader.exec_module(audit)
W = Path("/home/riscv/riscv-lab/software-import-20261026")
UTC = "2026-10-27T00:00:00+00:00"
BOOT = "12345678-1234-1234-1234-123456789abc"


def timing_fixture():
    specs = [dict(label="negative", negative=True, phase="negative"),
             dict(label="recovery", negative=False, phase="recovery")]
    specs += [dict(label="formal-"+str(n), negative=False, phase="formal") for n in range(23)]
    specs += [dict(label="replay-"+str(n), negative=False, phase="replay") for n in range(8)]
    intervals = [(10, 20), (30, 40)]
    intervals += [(50+10*(n//4), 59+10*(n//4)) for n in range(23)]
    intervals += [(120+10*(n//4), 129+10*(n//4)) for n in range(8)]
    records = [dict(pid=1000+n, process_started=True, exit_code=1 if n==0 else 0,
       started=UTC, finished=UTC, monotonic=dict(pid=1000+n, boot_id=BOOT,
       start_ns=start, end_ns=end, scope="popen_wait_bracket"))
       for n,(start,end) in enumerate(intervals)]
    for record, spec in zip(records, specs):
        record.update(label=spec["label"], phase=spec["phase"])
    state = dict(workers=4, boot_id=BOOT, monotonic_start_ns=1, monotonic_end_ns=150,
                 new_emu_runs=33, active_pids={}, started=UTC, finished=UTC)
    return records, specs, state


class TimingTests(unittest.TestCase):
    def setUp(self):
        self.records, self.specs, self.state = timing_fixture()
    def verify(self):
        return audit.audit_timing(self.records,self.specs,self.state)
    def test_actual_peak_four_from_events(self):
        result=self.verify()
        self.assertEqual(result["peak_process_envelopes"],4)
        self.assertFalse(result["utc_used_for_ordering"])
    def test_worker_budget_three_rejects_four_overlap(self):
        self.state["workers"]=3
        with self.assertRaisesRegex(ValueError,"concurrency exceeds"):self.verify()
    def test_bool_worker_rejected(self):
        self.state["workers"]=True
        with self.assertRaisesRegex(ValueError,"worker budget"):self.verify()
    def test_missing_record_rejected(self):
        self.records.pop()
        with self.assertRaisesRegex(ValueError,"33 actual"):self.verify()
    def test_duplicate_label_rejected(self):
        self.specs[-1]["label"]=self.specs[-2]["label"]
        with self.assertRaisesRegex(ValueError,"duplicate process labels"):self.verify()
    def test_duplicate_actual_pid_rejected(self):
        self.records[-1]["pid"]=self.records[-2]["pid"]
        with self.assertRaisesRegex(ValueError,"reused actual PID"):self.verify()
    def test_timing_pid_mismatch_rejected(self):
        self.records[-1]["monotonic"]["pid"]+=1
        with self.assertRaisesRegex(ValueError,"timing identity"):self.verify()
    def test_boot_mismatch_rejected(self):
        self.records[-1]["monotonic"]["boot_id"]="aaaaaaaa-1234-1234-1234-123456789abc"
        with self.assertRaisesRegex(ValueError,"timing identity"):self.verify()
    def test_wrong_scope_rejected(self):
        self.records[-1]["monotonic"]["scope"]="arbitrary outer wall-clock"
        with self.assertRaisesRegex(ValueError,"timing identity"):self.verify()
    def test_bool_clock_rejected(self):
        self.records[0]["monotonic"]["start_ns"]=True
        with self.assertRaisesRegex(ValueError,"monotonic bounds"):self.verify()
    def test_reversed_span_rejected(self):
        self.records[0]["monotonic"]["end_ns"]=9
        with self.assertRaisesRegex(ValueError,"monotonic bounds"):self.verify()
    def test_outside_campaign_rejected(self):
        self.records[-1]["monotonic"]["end_ns"]=151
        with self.assertRaisesRegex(ValueError,"monotonic bounds"):self.verify()
    def test_incomplete_target_rejected(self):
        self.records[-1]["exit_code"]=None
        with self.assertRaisesRegex(ValueError,"target incomplete"):self.verify()
    def test_unfinished_state_rejected(self):
        self.state["active_pids"]={"1":1032}
        with self.assertRaisesRegex(ValueError,"unfinished active"):self.verify()
    def test_negative_recovery_overlap_rejected(self):
        self.records[1]["monotonic"]["start_ns"]=19
        with self.assertRaisesRegex(ValueError,"negative/recovery"):self.verify()
    def test_formal_before_recovery_rejected(self):
        self.records[2]["monotonic"]["start_ns"]=39
        with self.assertRaisesRegex(ValueError,"before recovery"):self.verify()
    def test_replay_before_formal_barrier_rejected(self):
        self.records[25]["monotonic"]["start_ns"]=100
        with self.assertRaisesRegex(ValueError,"formal barrier"):self.verify()
    def test_wrong_phase_count_rejected(self):
        self.specs[-1]["phase"]="formal"
        self.records[-1]["phase"]="formal"
        with self.assertRaisesRegex(ValueError,"phase inventory"):self.verify()
    def test_utc_rollback_is_diagnostic_not_capacity_evidence(self):
        self.records[3]["started"]="2026-10-27T00:01:00+00:00"
        self.records[3]["finished"]="2026-10-26T23:59:00+00:00"
        self.assertEqual(self.verify()["status"],"MONOTONIC_PROCESS_CAPACITY_PASS")
    def test_record_label_mismatch_rejected(self):
        self.records[-1]["label"]="other"
        with self.assertRaisesRegex(ValueError,"label/phase"):self.verify()
    def test_record_phase_mismatch_rejected(self):
        self.records[-1]["phase"]="formal"
        with self.assertRaisesRegex(ValueError,"label/phase"):self.verify()
    def test_naive_utc_rejected(self):
        self.records[3]["started"]="2026-10-27T00:01:00"
        with self.assertRaisesRegex(ValueError,"timezone"):self.verify()


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.file=self.root/"input";self.file.write_bytes(b"input")
        self.expected={str(self.file):audit.sha(self.file)}
        def verify(files):
            for path,digest in files.items():
                audit.require(Path(path).is_file() and audit.sha(path)==digest,"physical drift")
        self.m=SimpleNamespace(verify_files=verify)
    def test_exact_map_passes(self):
        audit.verify_common(self.m,dict(self.expected),self.expected)
    def test_missing_input_rejected(self):
        with self.assertRaisesRegex(ValueError,"closure differs"):
            audit.verify_common(self.m,{},self.expected)
    def test_extra_input_rejected(self):
        with self.assertRaisesRegex(ValueError,"closure differs"):
            audit.verify_common(self.m,self.expected|{"/extra":"0"*64},self.expected)
    def test_real_input_tamper_rejected(self):
        self.file.write_bytes(b"tamper")
        with self.assertRaisesRegex(ValueError,"physical drift"):
            audit.verify_common(self.m,dict(self.expected),self.expected)
    def test_seal_detects_added_file(self):
        before=audit.tree_seal(self.root)
        (self.root/"extra").write_bytes(b"extra")
        self.assertNotEqual(before,audit.tree_seal(self.root))
    def test_seal_rejects_symlinks(self):
        (self.root/"link").symlink_to(self.file)
        with self.assertRaisesRegex(ValueError,"symlink"):audit.tree_seal(self.root)

class SummarySchemaTests(unittest.TestCase):
    def setUp(self):
        self.summary={"rows":[{"shape":"4x8"}],"samples":[{"cycles":3}],"measured_windows":384}
    def test_real_controller_results_constructor_is_nested(self):
        # Exercise the actual results constructor AST without executing any target.
        tree=ast.parse((HERE/"matrix.py").read_text())
        run=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="run")
        constructor=next(n.value for n in ast.walk(run) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=="result" for t in n.targets)
            and isinstance(n.value,ast.Call))
        variables=dict(CONTRACT="contract",RUN_PASS="screen_complete",
            sha=lambda p:"sha",self=SimpleNamespace(identity_path="identity",precondition="current"),
            records=[],rejected={},summary=self.summary,decisions={},replay_equal=True,
            proof={},workers=4,boot_id=BOOT)
        fixture=eval(compile(ast.Expression(constructor),"<actual matrix results constructor>","eval"),variables)
        self.assertEqual(fixture["summary"],self.summary)
        audit.verify_summary(fixture,self.summary)
        self.assertNotIn("measured_windows",fixture)
    def test_flattened_legacy_schema_rejected(self):
        with self.assertRaisesRegex(ValueError,"nested statistics"):
            audit.verify_summary(dict(self.summary),self.summary)
    def test_summary_mutation_rejected(self):
        changed=copy.deepcopy(self.summary);changed["samples"][0]["cycles"]+=1
        with self.assertRaisesRegex(ValueError,"nested statistics"):
            audit.verify_summary({"summary":changed},self.summary)
    def test_summary_added_field_rejected(self):
        with self.assertRaisesRegex(ValueError,"nested statistics"):
            audit.verify_summary({"summary":self.summary|{"extra":True}},self.summary)


class ActualRawTests(unittest.TestCase):
    """Reparse frozen qualified raw UART in temporary copies; no new target run."""
    @classmethod
    def setUpClass(cls):
        module_path=W/"reviews/config-reuse/adapter-v3/probe.py"
        spec=importlib.util.spec_from_file_location("raw_audit_frozen_adapter",module_path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        cls.repo=W/"clean-02/checkout/source"
        cls.probe=module.Probe(cls.repo,W/"clean-02/identity/current.json",
                              W/"clean-02/matrix-build-01",W/"clean-02/matrix-run-01")
        cls.f,cls.m=cls.probe.runtime()
        cls.campaign=W/"config-reuse-clean02-02/run-01"
        cls.common=audit.read(cls.campaign/"runtime-inputs.json")
        cls.process_common={k:v for k,v in cls.common.items() if not k.endswith("/vdot-perf.bin")}
        cls.cfg=audit.read(cls.campaign/"configuration.json")
        cls.fixture=audit.read(cls.campaign/"negative-fixture/fixture.json")
    def copied(self, label):
        origin=self.campaign/"runs"/label
        temp=tempfile.TemporaryDirectory(prefix="raw-audit-host-test-")
        self.addCleanup(temp.cleanup)
        target=Path(temp.name)
        for name in ("result.json","stdout.log","stderr.log","windows.json","observation.json","negative.json"):
            if (origin/name).is_file():shutil.copyfile(origin/name,target/name)
        record=audit.read(target/"result.json")
        image={k:record[k] for k in ("suite","shard","dataset","variant","name","path","image_sha256")}
        return target,record,image
    def verify(self,target,record,image):
        return audit.record_audit(self.repo,self.probe.g,self.f,self.m,self.cfg,image,target,
            self.common,record["contract"],replay=record["replay"],negative=record["negative"],
            fixture=self.fixture if record["negative"] else None,
            expected_cwd=record["cwd"],process_common=self.process_common)
    def test_real_24_window_raw_reparse_passes(self):
        target,record,image=self.copied("recovery-config-reuse")
        before=audit.tree_seal(target)
        result=self.verify(target,record,image)
        self.assertEqual(result["audit"]["windows"],24)
        self.assertEqual(audit.tree_seal(target),before)
    def test_real_bit100_negative_raw_reparse_passes(self):
        target,record,image=self.copied("negative-config-reuse")
        before=audit.tree_seal(target)
        result=self.verify(target,record,image)
        self.assertTrue(result["audit"]["negative"])
        self.assertEqual(record["negative_details"]["bit"],100)
        self.assertEqual(audit.tree_seal(target),before)
    def test_changed_loaded_bin_digest_rejected(self):
        target,record,image=self.copied("recovery-config-reuse")
        record["files"][str(Path(image["path"])/"vdot-perf.bin")]="0"*64
        (target/"result.json").write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,"runtime input inventory"):
            self.verify(target,record,image)
    def test_changed_cached_sample_rejected(self):
        target,record,image=self.copied("recovery-config-reuse")
        record["samples"][0]["cycles"]+=1
        (target/"result.json").write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,"cached samples"):
            self.verify(target,record,image)
    def test_changed_raw_transcript_rejected(self):
        target,record,image=self.copied("recovery-config-reuse")
        with (target/"stdout.log").open("a") as stream:stream.write("tamper")
        with self.assertRaisesRegex(ValueError,"raw transcript digest"):
            self.verify(target,record,image)


if __name__=="__main__":
    unittest.main(verbosity=2)
