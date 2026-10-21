"""Current G3/checker compatibility using immutable historical raw payloads.

Temporary receipt adaptation is a host integration test, never a new EMU run or
a replacement for the archived command, seed, hardware identity or result.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import run_suite as runner


class DenseRuntimeIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = runner.load_module("o2_g3_dense_actual_checker",
                                        runner.ROOT / "team/workloads/vdot-perf/check.py")
        cls.build = runner.ROOT / "team/evidence/t13-performance-20261015/images-v3/performance-d0-s06"
        cls.archive = (runner.ROOT / "team/optimizations/o2/evidence/20261019-fullcore-validation"
                       / "files/runs/core-02/dense-batch128")
        cls.original = json.loads((cls.archive / "result.json").read_text(encoding="utf-8"))

    def receipt(self):
        record = copy.deepcopy(self.original)
        # These fields describe a hypothetical current invocation only. The
        # input logs remain the exact old hardware run, tested offline below.
        command = record["command"]
        record["command"] = runner.runtime_command(command[5], command[7],
            command[10].split("=", 1)[1], command[8].split("=", 1)[1])
        record.update(single_core=True, emu_threads=1)
        return runner.dense_runtime_receipt(record)

    def verify(self, receipt):
        with tempfile.TemporaryDirectory(prefix="o2-dense-compat-") as temporary:
            run = Path(temporary)
            for name in ("stdout.log", "stderr.log"):
                payload = self.checker.raw_bytes(self.archive / name)
                (run / name).write_bytes(payload)
                self.assertEqual(runner.sha(run / name), self.original["raw_logs_sha256"][name])
            runner.save(run / "result.json", receipt)
            return self.checker.verify(self.build, run, external=self.original["files"])

    def test_actual_architecture_elf_and_windows_accept_current_receipt_shape(self):
        original_bytes = (self.archive / "result.json").read_bytes()
        result = self.verify(self.receipt())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["samples"]), 12)
        self.assertEqual((self.archive / "result.json").read_bytes(), original_bytes)

    def test_old_live_receipt_shape_is_not_accepted_by_current_checker(self):
        with self.assertRaisesRegex(ValueError, "wrong core/thread configuration"):
            self.verify(self.original)

    def test_strict_shared_parser_rejects_wrappers_duplicate_unknown_and_missing_seed(self):
        command = self.receipt()["command"]
        for bad in (command[:2] + ["stdbuf", "-o0", "-e0"] + command[2:],
                    command + ["--diff=/foreign"], command + ["--unknown=1"], command[:-1]):
            with self.subTest(command=bad), self.assertRaises(ValueError):
                self.checker.runtime_roles(bad)

    def test_raw_and_core_metadata_cannot_be_omitted_or_replaced(self):
        for label in ("single_core", "emu_threads", "raw_sha256", "derived", "corrupt"):
            record = self.receipt()
            if label in ("single_core", "emu_threads", "raw_sha256"):
                record.pop(label)
            elif label == "derived":
                record["raw_sha256"]["run.log"] = self.original["raw_logs_sha256"]["run.log"]
            else:
                record["raw_sha256"]["stdout.log"] = "0" * 64
            with self.subTest(field=label), self.assertRaises(ValueError):
                self.verify(record)


if __name__ == "__main__":
    unittest.main()
