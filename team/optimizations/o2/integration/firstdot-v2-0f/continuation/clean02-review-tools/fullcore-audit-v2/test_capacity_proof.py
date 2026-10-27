"""Host-only exact evidence and synthetic mutation tests; never calls fc.audit."""
import ast
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import capacity_proof as cp


def original_binding(case):
    path = Path(case["spawn_source"])
    module = ast.parse(path.read_text(), filename=str(path))
    node = next(n for n in module.body if isinstance(n, ast.FunctionDef)
                and n.name == "spawn_binding")
    isolated = ast.Module(body=[node], type_ignores=[])
    namespace = {"p": SimpleNamespace(require=cp.require), "SPAWN_FIELDS": cp.SPAWN_FIELDS}
    exec(compile(ast.fix_missing_locations(isolated), str(path), "exec"), namespace)
    return SimpleNamespace(SPAWN_FIELDS=cp.SPAWN_FIELDS,
                           spawn_binding=namespace["spawn_binding"])


class CapacityProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = cp._case()
        run = Path(cls.case["run"])
        cls.base = dict(
            case=cls.case, state=cp.read(run / "state.json"),
            result=cp.read(run / "results.json"),
            rows={n: cp.read(run / "runs" / n / "result.json") for n in cls.case["expected_names"]},
            runtimes={n: cp.read(run / "runs" / n / "runtime.json") for n in cls.case["expected_names"]},
            outer=cp.read(cls.case["outer_command"]),
            failure=cp.read(cls.case["original_failure_command"]),
            post=cp.read(cls.case["original_post_state"]),
            stdout=Path(cls.case["outer_stdout"]).read_text(),
            failure_stderr=Path(cls.case["original_failure_stderr"]).read_text(),
        )
        cls.e = original_binding(cls.case)

    def checked(self, mutate=None):
        args = copy.deepcopy(self.base)
        if mutate:
            mutate(args)
        return cp._validate_loaded(**args, e=self.e)

    def rejected(self, mutate):
        with self.assertRaises((ValueError, KeyError)):
            self.checked(mutate)

    def test_real_case_read_only_and_deterministic(self):
        a = cp.process_proof(Path(self.case["run"]), self.e)
        b = cp.process_proof(Path(self.case["run"]), self.e)
        self.assertEqual(a, b)
        self.assertEqual(a["status"], cp.STATUS)
        self.assertEqual(a["wall_clock_capacity"], "FAIL")
        self.assertEqual(a["recorded_peak"], 4)
        self.assertFalse(a["os_monotonic_capacity_measured"])
        self.assertFalse(a["semantic_raw_audit_granted"])
        self.assertEqual(a["new_emu_runs"], 0)

    def test_source_input_map_is_the_exact_case_map(self):
        self.assertEqual(cp.source_inputs(), self.case["files"])
        self.assertEqual(len(cp.source_inputs()), 71)

    def test_another_run_rejected(self):
        with self.assertRaisesRegex(ValueError, "exact named"):
            cp.process_proof(Path("/tmp/not-this-run"), self.e)

    def test_case_bytes_changed_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "exact-case.json"
            path.write_bytes(cp.CASE_FILE.read_bytes() + b"\n")
            with patch.object(cp, "CASE_FILE", path):
                with self.assertRaisesRegex(ValueError, "case source changed"):
                    cp.source_inputs()

    def test_input_hash_drift_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "receipt.json"; path.write_text("changed")
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                cp._verify_files({str(path): "0" * 64})

    def test_input_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "target"; path.write_text("x")
            link = Path(temp) / "link"; link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "nonregular"):
                cp._verify_files({str(link): cp.digest(b"x")})

    def test_missing_process_rejected(self):
        self.rejected(lambda a: a["rows"].pop("functional-2"))

    def test_extra_process_rejected(self):
        self.rejected(lambda a: a["rows"].update(unexpected=a["rows"]["functional-2"]))

    def test_jobs_four_is_not_this_exception(self):
        self.rejected(lambda a: a["state"].update(jobs=4))

    def test_launch_count_drift_rejected(self):
        self.rejected(lambda a: a["state"].update(new_emu_launch_attempts=15))

    def test_active_job_rejected(self):
        self.rejected(lambda a: a["state"].update(active={"still_running": 1}))

    def test_runtime_result_binding_drift_rejected(self):
        self.rejected(lambda a: a["runtimes"]["functional-7"].update(pid=999999))

    def test_timeout_rejected(self):
        self.rejected(lambda a: a["rows"]["functional-7"].update(timed_out=True))

    def test_nonzero_normal_exit_rejected(self):
        self.rejected(lambda a: a["rows"]["functional-7"].update(exit_code=1))

    def test_boolean_exit_rejected(self):
        self.rejected(lambda a: a["rows"]["functional-7"].update(exit_code=False))

    def test_hardware_identity_drift_rejected(self):
        self.rejected(lambda a: a["result"].update(emu_sha256="0" * 64))

    def test_parent_nonzero_rejected(self):
        self.rejected(lambda a: a["outer"].update(exit_code=1))

    def test_original_failure_erased_rejected(self):
        self.rejected(lambda a: a["failure"].update(exit_code=0))

    def test_failure_error_replaced_rejected(self):
        self.rejected(lambda a: a.update(failure_stderr="a different failure"))

    def test_completion_order_changed_rejected(self):
        def mutate(a):
            lines = a["stdout"].splitlines()
            lines[10], lines[11] = lines[11], lines[10]
            a["stdout"] = "\n".join(lines)
        self.rejected(mutate)

    def test_second_anomaly_rejected(self):
        def mutate(a):
            value = "2026-10-27T04:10:38.000000+00:00"
            a["rows"]["functional-3"]["started"] = value
            a["runtimes"]["functional-3"]["started"] = value
        self.rejected(mutate)

    def test_exact_duration_changed_rejected(self):
        self.rejected(lambda a: a["rows"]["functional-7"].update(
            finished="2026-10-27T05:05:46.746957+00:00"))

    def test_original_anomaly_hidden_rejected(self):
        self.rejected(lambda a: a["rows"]["functional-7"].update(
            finished="2026-10-27T05:05:46.600000+00:00"))

    def test_negative_recovery_causal_reverse_rejected(self):
        self.rejected(lambda a: a["rows"]["negative-vdot"].update(
            finished="2026-10-27T03:53:08.235186+00:00"))

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "naive"):
            cp._date("2026-10-27T05:05:46.666837")


if __name__ == "__main__":
    unittest.main(verbosity=2)
