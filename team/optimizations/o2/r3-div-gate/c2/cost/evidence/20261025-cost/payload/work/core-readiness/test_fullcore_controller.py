"""Offline gate tests; no building, mapping, STA, or simulator execution."""
import argparse
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("c2_fullcore_controller_draft", HERE / "fullcore_controller.py")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)
DIGEST = "a" * 64


def valid():
    screen = dict(status="C2_SCREEN_PASS", fullcore_authorized_by_gate=True,
                  inputs_unchanged=True, candidate_head=controller.SOURCE,
                  local_manifest_sha256=controller.LOCAL_MANIFEST,
                  baseline_manifest_sha256=controller.BASE_MANIFEST, failures=[],
                  comparisons=[dict(profile=i//9, path=i%9, pass_=True) for i in range(45)])
    audit = dict(status="C2_COST_INDEPENDENT_AUDIT_PASS", screening_pass=True, paths=45,
                 path_pass_count=45, failures=[], input_hashes_unchanged=True,
                 screen_result_sha256=DIGEST, candidate_head=controller.SOURCE,
                 candidate_exeunit_sha256=controller.EXE_SHA,
                 local_manifest_sha256=controller.LOCAL_MANIFEST)
    return screen, audit


class GateTests(unittest.TestCase):
    def test_valid_synthetic_receipt(self):
        controller.validate_gate_fields(*valid(), DIGEST)

    def test_every_material_gate_rejects(self):
        changes = [
            ("screen", "status", "C2_SCREEN_REJECT"),
            ("screen", "fullcore_authorized_by_gate", False),
            ("screen", "fullcore_authorized_by_gate", 1),
            ("screen", "inputs_unchanged", False),
            ("screen", "candidate_head", controller.BASE_SOURCE),
            ("screen", "local_manifest_sha256", "0"*64),
            ("screen", "baseline_manifest_sha256", "0"*64),
            ("screen", "failures", ["known regression"]),
            ("screen", "comparisons", [dict(pass_=True)]*44),
            ("screen", "comparisons", [dict(pass_=True)]*44 + [dict(pass_=False)]),
            ("audit", "status", "C2_COST_INDEPENDENT_AUDIT_FAILED"),
            ("audit", "screening_pass", False),
            ("audit", "screening_pass", 1),
            ("audit", "paths", 44),
            ("audit", "path_pass_count", 44),
            ("audit", "failures", ["known regression"]),
            ("audit", "input_hashes_unchanged", False),
            ("audit", "screen_result_sha256", "0"*64),
            ("audit", "candidate_head", controller.BASE_SOURCE),
            ("audit", "candidate_exeunit_sha256", "0"*64),
            ("audit", "local_manifest_sha256", "0"*64),
        ]
        for side, key, bad in changes:
            with self.subTest(side=side, key=key, bad=bad):
                screen, audit = valid()
                (screen if side == "screen" else audit)[key] = copy.deepcopy(bad)
                with self.assertRaises(ValueError):
                    controller.validate_gate_fields(screen, audit, DIGEST)

    def test_missing_required_fields_reject(self):
        good = valid()
        for index, sample in enumerate(good):
            for key in sample:
                screen, audit = valid()
                del (screen if index == 0 else audit)[key]
                with self.subTest(index=index, key=key):
                    with self.assertRaises(ValueError):
                        controller.validate_gate_fields(screen, audit, DIGEST)

    def test_default_no_execute_cannot_start_process(self):
        args = argparse.Namespace(execute=False, output=HERE/"never-created",
                                  screen=controller.COST/"screen-01/result.json",
                                  audit_dir=controller.COST/"independent-review/final-audit-01")
        with mock.patch.object(controller.subprocess, "Popen") as process:
            with self.assertRaisesRegex(ValueError, "--execute required"):
                controller.run(args)
            process.assert_not_called()
        self.assertFalse(args.output.exists())

    def test_failed_cost_gate_stops_before_source_or_process(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix="gate-test-") as raw:
            parent = Path(raw)
            repo = parent / "repo"
            repo.mkdir()
            args = argparse.Namespace(execute=True, output=parent/"run",
                                      screen=controller.COST/"screen-01/result.json",
                                      audit_dir=controller.COST/"independent-review/final-audit-01")
            with mock.patch.object(controller, "REPO", repo), \
                 mock.patch.object(controller, "collect_gate_pins", side_effect=ValueError("cost rejected")), \
                 mock.patch.object(controller, "collect_source_pins") as source, \
                 mock.patch.object(controller.subprocess, "Popen") as process:
                with self.assertRaisesRegex(ValueError, "cost rejected"):
                    controller.run(args)
                source.assert_not_called()
                process.assert_not_called()
                self.assertFalse(args.output.exists())


if __name__ == "__main__":
    unittest.main()
