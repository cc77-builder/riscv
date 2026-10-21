"""Readiness must preserve frozen identities and aggregate actionable failures."""
import copy
import hashlib
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import preflight


class InputReadinessTests(unittest.TestCase):
    def test_actual_missing_matching_and_drifted_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.bin"
            expected = hashlib.sha256(b"frozen").hexdigest()
            self.assertEqual(preflight.inspect_file(path, expected)["status"], "MISSING")
            path.write_bytes(b"frozen")
            self.assertEqual(preflight.inspect_file(path, expected)["status"], "OK")
            path.write_bytes(b"drifted")
            self.assertEqual(preflight.inspect_file(path, expected)["status"], "DRIFT")

    def test_negative_wrapper_path_is_not_relocated_by_equal_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "nemu/reference/build/riscv64-nemu-interpreter-so"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"same bytes would still not authorize relocation")
            self.assertEqual(preflight.linked_reference_check(root)["status"], "WRONG_LINKED_REFERENCE_PATH")
        self.assertEqual(preflight.linked_reference_check(preflight.suite.DEFAULT_T12)["status"], "OK")

    def test_missing_roots_aggregate_all_matrix_and_frozen_artifact_requirements(self):
        frozen = copy.deepcopy(preflight.suite.FROZEN)
        perf = preflight.suite.load_module("o5_test_real_perf", preflight.ROOT / "team/workloads/vdot-perf/check.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hello = root / "t12/repo/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin"
            hello.parent.mkdir(parents=True)
            hello.write_bytes(b"wrong frozen hello")
            rows = preflight.collect_inputs(root / "t12", root / "t14", root / "dense", perf)
        self.assertEqual(next(row for row in rows if row["role"] == "hello")["status"], "DRIFT")
        self.assertEqual(len([row for row in rows if row["role"].startswith("matrix-") and "corpus" not in row["role"]]), 8)
        self.assertEqual(len([row for row in rows if row["role"] == "dense frozen artifact"]), 9)
        self.assertGreater(len([row for row in rows if row["status"] == "MISSING"]), 40)
        self.assertEqual(preflight.suite.FROZEN, frozen)

    def test_corrupt_provenance_is_reported_and_does_not_stop_other_inputs(self):
        perf = preflight.suite.load_module("o5_test_real_perf_corrupt", preflight.ROOT / "team/workloads/vdot-perf/check.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "t12/runs/t11-matrix-canonical/build-0/workload-provenance.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text("not json", encoding="utf-8")
            rows = preflight.collect_inputs(root / "t12", root / "t14", root / "dense", perf)
        self.assertEqual(next(row for row in rows if row["path"] == str(receipt))["status"], "INVALID_RECEIPT")
        self.assertTrue(any(row["role"] == "matrix-7" for row in rows))

    def test_missing_inputs_never_invoke_strict_preflight_or_claim_hardware(self):
        source = dict(head="a" * 40, expected_commit="a" * 40, head_matches=True, git_clean=True, dirty_entries=[])
        with tempfile.TemporaryDirectory() as temporary, patch.object(preflight, "source_state", return_value=source), \
                patch.object(preflight.suite, "preflight", side_effect=AssertionError("must not run")):
            root = Path(temporary)
            report = preflight.assess(SimpleNamespace(source_commit="a" * 40, t12_root=root / "t12",
                                                      t14_root=root / "t14", dense_build=root / "dense"))
        self.assertEqual(report["status"], "NOT_READY")
        self.assertFalse(report["hardware_checked"])
        self.assertFalse(report["native_tools_checked"])
        self.assertFalse(report["complete_input_identity_checked"])
        self.assertFalse(report["inventory_expansion_complete"])
        self.assertEqual(report["emulators_executed"], 0)

    def test_source_receipt_binds_actual_commit_and_detects_untracked_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=O5 Test", "-c", "user.email=o5@example.invalid",
                            "commit", "--allow-empty", "-qm", "fixture"], check=True)
            head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
            self.assertTrue(preflight.source_state(head, root)["git_clean"])
            self.assertFalse(preflight.source_state("0" * 40, root)["head_matches"])
            (root / "src").mkdir()
            (root / "src/candidate.scala").write_text("uncommitted", encoding="utf-8")
            self.assertFalse(preflight.source_state(head, root)["git_clean"])

    def test_output_cannot_overwrite_or_live_inside_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            outside = Path(temporary) / "new.json"
            self.assertEqual(preflight.output_path(outside, root), outside.resolve())
            outside.write_text("preserved", encoding="utf-8")
            for target in (root / "new.json", outside, Path("relative.json")):
                with self.subTest(target=target), self.assertRaises(ValueError):
                    preflight.output_path(target, root)
            self.assertEqual(outside.read_text(encoding="utf-8"), "preserved")


if __name__ == "__main__":
    unittest.main()
