"""Meaningful rejection tests for the C8 evidence and static-equivalence gates."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import qualification as q
import verify_c8_package as v


def identity():
    return {"contract": "zjhwork-0f-firstdot-v2-clean-identity-v1",
            "source_commit": q.SOURCE_COMMIT, "selected_hardware_commit": q.HARDWARE_COMMIT,
            "reference_sha256": q.REFERENCE_SHA256,
            "hardware_profile": {"source_commit": q.SOURCE_COMMIT,
                "selected_hardware_commit": q.HARDWARE_COMMIT, "emu_sha256": q.EMU_SHA256,
                "reference_provenance": {"binary_sha256": q.REFERENCE_SHA256}},
            "configuration": {"source_commit": q.SOURCE_COMMIT, **{k: "role/path" for k in
                ("hardware_source", "reference", "build_record", "am_home", "flash")}}}


def selection():
    matrix = {"contract": "zjhwork-clean-config-reuse-4shape-3dataset-matrix-v1",
              "status": "CURRENT_CONFIG_REUSE_MATRIX_SCREEN_COMPLETE", "functional_status": "FUNCTIONAL_PASS",
              "new_emu_runs": 33, "all_window_replay": True, "default_changed": False,
              "decisions": {"8x32": {"decision": "PERFORMANCE_CANDIDATE", "unexplained_controls": [],
                  "samples_per_cell": 12, "ordinary_public_C_application": "NOT_TESTED",
                  "stable_default_changed": False,
                  "dataset_decisions": {str(i): {"decision": "PERFORMANCE_CANDIDATE",
                      "unexplained_controls": [], "samples_per_cell": 4} for i in range(3)}}}}
    c8 = {"contract": "zjhwork-config-reuse-8x32-c-qualification-v1",
          "status": "CURRENT_CONFIG_REUSE_8X32_C_QUALIFIED", "performance_measured": False,
          "default_changed": False, "anchor": {"target_symbol": q.TARGET, "comparisons_count": 48,
              "target_comparisons": 12, "target_functions": 4, "target_distinct_cases": 12,
              "target_normal_executions": 24, "negative_expected_pc": "0x80000d64"}}
    return matrix, c8


def member(name, data):
    header = (name.ljust(16) + "0".ljust(12) + "0".ljust(6) + "0".ljust(6) +
              "100644".ljust(8) + str(len(data)).ljust(10) + "`\n").encode()
    return header + data + (b"\n" if len(data) % 2 else b"")


class IdentityGateTests(unittest.TestCase):
    def test_correct_semantic_identity(self):
        self.assertEqual(q.validate_identity(identity())["selected_hardware_commit"], q.HARDWARE_COMMIT)

    def test_wrong_hardware_even_after_rehash(self):
        data = identity()
        data["selected_hardware_commit"] = "0" * 40
        data["candidate_digest"] = v.digest(json.dumps(data).encode())
        with self.assertRaisesRegex(ValueError, "wrong software/hardware"):
            q.validate_identity(data)

    def test_wrong_nested_emu(self):
        data = identity()
        data["hardware_profile"]["emu_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            q.validate_identity(data)

    def test_wrong_nemu(self):
        data = identity()
        data["reference_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            q.validate_identity(data)

    def test_mixed_configuration(self):
        data = identity()
        data["configuration"]["source_commit"] = "f" * 40
        with self.assertRaises(ValueError):
            q.validate_identity(data)

    def test_missing_physical_input(self):
        data = identity()
        del data["configuration"]["flash"]
        with self.assertRaises(ValueError):
            q.validate_identity(data)


class SelectionGateTests(unittest.TestCase):
    def test_separate_historical_and_later_c_qualification(self):
        result = q.validate_selection(*selection())
        self.assertEqual(result["matrix_ordinary_C"], "NOT_TESTED")
        self.assertEqual(result["later_ordinary_C"], "QUALIFIED")

    def test_rewritten_historical_c_rejected(self):
        matrix, c8 = selection()
        matrix["decisions"]["8x32"]["ordinary_public_C_application"] = "PASS"
        with self.assertRaises(ValueError):
            q.validate_selection(matrix, c8)

    def test_missing_dataset(self):
        matrix, c8 = selection()
        del matrix["decisions"]["8x32"]["dataset_decisions"]["2"]
        with self.assertRaises(ValueError):
            q.validate_selection(matrix, c8)

    def test_control_drift(self):
        matrix, c8 = selection()
        matrix["decisions"]["8x32"]["dataset_decisions"]["1"]["unexplained_controls"] = ["drift"]
        with self.assertRaises(ValueError):
            q.validate_selection(matrix, c8)

    def test_wrong_c_target_after_rehash(self):
        matrix, c8 = selection()
        c8["anchor"]["target_symbol"] = "config_reuse_gemv_4x8_reuse_vdot"
        c8["candidate_digest"] = v.digest(json.dumps(c8).encode())
        with self.assertRaises(ValueError):
            q.validate_selection(matrix, c8)

    def test_incomplete_target_calls(self):
        matrix, c8 = selection()
        c8["anchor"]["target_normal_executions"] = 12
        with self.assertRaises(ValueError):
            q.validate_selection(matrix, c8)

    def test_new_performance_claim_rejected(self):
        matrix, c8 = selection()
        c8["performance_measured"] = True
        with self.assertRaises(ValueError):
            q.validate_selection(matrix, c8)


class StaticGateTests(unittest.TestCase):
    def test_archive_member(self):
        self.assertEqual(v.archive_member(b"!<arch>\n" + member("/", b"index") +
                                          member("gemv.o/", b"abc")), b"abc")

    def test_duplicate_member_rejected(self):
        with self.assertRaises(ValueError):
            v.archive_member(b"!<arch>\n" + member("gemv.o/", b"a") * 2)

    def test_wrong_member_rejected(self):
        with self.assertRaises(ValueError):
            v.archive_member(b"!<arch>\n" + member("other.o/", b"a"))

    def test_truncated_member_rejected(self):
        with self.assertRaises(ValueError):
            v.archive_member((b"!<arch>\n" + member("gemv.o/", b"abcd"))[:-1])

    def test_thin_archive_rejected(self):
        with self.assertRaises(ValueError):
            v.archive_member(b"!<thin>\n")

    def test_semantic_oracle_not_candidate_digest(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a", Path(d) / "b"
            a.write_bytes(b"wrong-callee")
            b.write_bytes(b"right-callee")
            self.assertEqual(v.sha(a), v.digest(a.read_bytes()))
            with self.assertRaises(ValueError):
                v.semantic_equal(a, b)

    def test_role_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                q.role_files({"roles": {"public": {"../escape": {"bytes": 0, "sha256": "0" * 64}}}},
                             {"public": Path(d)})

    def test_missing_role_rejected(self):
        with self.assertRaises(ValueError):
            q.role_files({"roles": {"public": {}}}, {})

    def test_changed_input_with_original_pin_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "source"
            path.write_bytes(b"original")
            expected = v.sha(path)
            path.write_bytes(b"modified")
            with self.assertRaises(ValueError):
                q.verify_map({str(path): expected})


if __name__ == "__main__":
    unittest.main()
