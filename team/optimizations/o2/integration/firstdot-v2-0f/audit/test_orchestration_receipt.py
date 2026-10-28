import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import orchestration_receipt as r
finalizer_path = Path(__file__).parent / "finalize_c.py"
if not finalizer_path.is_file():
    finalizer_path = Path(__file__).parent.parent / "orchestration/finalize_c.py"
_spec = importlib.util.spec_from_file_location("finalize_c_for_test", finalizer_path)
finalize_c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(finalize_c)
import audit_combination as audit


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class IndependentReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo, self.matrix, self.build, self.run = [self.root / n for n in ("repo", "matrix", "build", "run")]
        self.identity = self.root / "identity.json"
        self.cfg = {"hardware_source": "/fixed", "cross_prefix": "cross-"}
        save(self.identity, {"configuration": self.cfg})
        self.runner = self.repo / r.RUNNER
        self.runner.parent.mkdir(parents=True)
        self.runner.write_text("frozen fixture runner\n")
        self.patch = patch.object(r, "RUNNER_SHA256", r.sha(self.runner))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.combo = types.SimpleNamespace(
            CONTRACT="outer", upstream_c=types.SimpleNamespace(CONTRACT="c-contract"),
            parent_identity=lambda repo, identity: r.read(identity),
            verify_build_scope=lambda *args: None,
            library_anchor=lambda *args: {"anchor": "fixed"},
            adapter_files=lambda: {"adapter": "fixed"})
        self.state = dict(
            status="R4_C_APPLICATION_CALLS_PASS", contract="c-contract", new_emu_runs=3,
            active_pid=None, active_result=None, performance_measured=False,
            whole_suite_acceptance=False, distinct_cases=48, public_functions=16,
            normal_case_executions=96, expected_negative_runs=1, normal_runs=2,
            operation_id="independent", started="2026-10-26T00:00:00+00:00", finished="2026-10-26T00:01:00+00:00")
        for path, value in [
            (self.matrix / "images.json", {"images": []}),
            (self.matrix / "combination-build.json", {"fixed": True}),
            (self.build / "build.json", {"fixed": True}),
            (self.build / "matrix-anchor.json", {"anchor": "fixed"}),
            (self.build / "combination-c-build.json", {"contract": "outer", "adapter_files": {"adapter": "fixed"}}),
            (self.run / "state.json", self.state),
            (self.run / "configuration.json", dict(self.cfg, canonical_build=str(self.build), run_root=str(self.run), source_root=str(self.repo))),
            (self.run / "results.json", dict({k:v for k,v in self.state.items() if k != "finished"}, runs=[1,2,3])),
            (self.run / "completed-runs.json", [1,2,3])]:
            save(path, value)
        self.record = dict(
            contract="outer", hardware_identity_sha256=r.sha(self.identity),
            source_sha256=r.sha(self.runner), source_file=str(self.runner),
            matrix_images_sha256=r.sha(self.matrix / "images.json"), source_result=self.state,
            scope=r.SCOPE, combination_qualified=False, performance_measured=False)
        self.receipt = self.run / "independent-c-orchestration.json"
        save(self.receipt, self.record)
        self.command = self.run.with_name(self.run.name + ".command.json")
        self.launcher = dict(
            command=["python3","-B",str(self.runner),str(self.repo),str(self.identity),str(self.matrix),str(self.build),str(self.run)],
            cwd=str(self.repo), pid=100, child_pid=101, exit_code=0,
            started="2026-10-26T00:00:00+00:00", finished="2026-10-26T00:01:00+00:00")
        save(self.command, self.launcher)
        self.command.with_suffix(".stdout.log").write_text("ORDINARY_C_DONE_MATRIX_QUALIFICATION_PENDING" + chr(10))
        self.command.with_suffix(".stderr.log").write_text("")

    def verify(self):
        return r.validate_independent_receipt(self.combo, self.repo, self.identity, self.matrix, self.build, self.run)

    def test_valid_complete_binding(self):
        self.assertTrue(self.verify()["source_result_exact"])
        self.assertEqual(len(self.verify()["inputs"]), 16)

    def test_same_bytes_wrong_runner_path(self):
        alternate = self.root / "runner.py"
        alternate.write_bytes(self.runner.read_bytes())
        self.record["source_file"] = str(alternate)
        save(self.receipt, self.record)
        with self.assertRaisesRegex(ValueError, "runner path/source"):
            self.verify()

    def test_actual_work_directory_runner_allowed_with_bound_launcher(self):
        actual = self.run.parent / "run_c_independent.py"
        actual.write_bytes(self.runner.read_bytes())
        self.record["source_file"] = str(actual)
        self.launcher["command"][2] = str(actual)
        save(self.receipt, self.record)
        save(self.command, self.launcher)
        self.assertEqual(self.verify()["inputs"]["runner"]["path"], str(actual))

    def test_outer_output_target_mismatch_rejected(self):
        self.launcher["command"][-1] = "/unrelated/output"
        save(self.command, self.launcher)
        with self.assertRaisesRegex(ValueError, "outer launcher binding"):
            self.verify()

    def test_outer_launch_not_finished_rejected(self):
        self.launcher["exit_code"] = 1
        save(self.command, self.launcher)
        with self.assertRaisesRegex(ValueError, "outer launcher binding"):
            self.verify()

    def test_changed_runner_and_receipt_digest(self):
        self.runner.write_text("changed")
        self.record["source_sha256"] = r.sha(self.runner)
        save(self.receipt, self.record)
        with self.assertRaisesRegex(ValueError, "runner path/source"):
            self.verify()

    def test_source_result_not_completed_state(self):
        self.record["source_result"] = dict(self.state, distinct_cases=47)
        save(self.receipt, self.record)
        with self.assertRaisesRegex(ValueError, "source result"):
            self.verify()

    def test_wrong_canonical_build(self):
        path = self.run / "configuration.json"
        value = r.read(path)
        value["canonical_build"] = "/different/build"
        save(path, value)
        with self.assertRaisesRegex(ValueError, "configuration/build"):
            self.verify()

    def test_changed_results_records(self):
        save(self.run / "completed-runs.json", [1,2,4])
        with self.assertRaisesRegex(ValueError, "cached state/records"):
            self.verify()

    def test_extra_receipt_field(self):
        self.record["new_claim"] = "accepted"
        save(self.receipt, self.record)
        with self.assertRaisesRegex(ValueError, "field inventory"):
            self.verify()

    def test_unqualified_identity(self):
        self.record["hardware_identity_sha256"] = "0"*64
        save(self.receipt, self.record)
        with self.assertRaisesRegex(ValueError, "input identity"):
            self.verify()


class FinalizerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.args = [root / name for name in ("repo", "identity", "matrix", "matrix-run", "build", "run")]
        for path in self.args:
            path.mkdir()
        self.run = self.args[-1]
        self.identity = self.args[1] / "identity.json"
        self.identity.write_text("{}")
        self.args[1] = self.identity
        self.c = types.SimpleNamespace(
            CONTRACT="outer", matrix_qualification=lambda *args: {"matrix": "passed"},
            parent_identity=lambda *args: {}, g=types.SimpleNamespace(require=audit.require, sha=audit.sha))
        self.base = types.SimpleNamespace(audit_run=lambda *args: {"raw": "passed"})
        self.modules = patch.dict("sys.modules", {"combination": self.c})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.private = patch.object(audit, "private_c_auditor", return_value=(self.base, {"adapter": "fixed"}))
        self.private.start()
        self.addCleanup(self.private.stop)
        self.bound = patch.object(r, "validate_independent_receipt", return_value={"binding": "fixed"})
        self.validate = self.bound.start()
        self.addCleanup(self.bound.stop)

    def test_writes_proof_and_qualification_after_audit(self):
        result = finalize_c.finalize(*self.args)
        self.assertEqual(result["status"], "CURRENT_FIRSTDOT_C_APPLICATION_PASS")
        self.assertTrue((self.run / "combination-c-orchestration-proof.json").is_file())

    def test_raw_failure_leaves_no_qualification(self):
        self.base.audit_run = lambda *args: (_ for _ in ()).throw(ValueError("raw failed"))
        with self.assertRaisesRegex(ValueError, "raw failed"):
            finalize_c.finalize(*self.args)
        self.assertFalse((self.run / "combination-c-qualification.json").exists())

    def test_receipt_drift_leaves_no_qualification(self):
        self.validate.side_effect = [{"before": 1}, {"after": 2}]
        with self.assertRaisesRegex(ValueError, "changed during raw audit"):
            finalize_c.finalize(*self.args)
        self.assertFalse((self.run / "combination-c-qualification.json").exists())

    def test_existing_qualification_not_overwritten(self):
        path = self.run / "combination-c-qualification.json"
        path.write_text("preserve")
        with self.assertRaisesRegex(ValueError, "already exists"):
            finalize_c.finalize(*self.args)
        self.assertEqual(path.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main(verbosity=2)
