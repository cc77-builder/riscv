"""Targeted R2-SELECT tests against the actual immutable S1 v2 archive."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

import selection as s


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[4]
        cls.archive = Path(os.environ.get("R2_SELECT_ARCHIVE", cls.repo / s.S1 / "evidence/merged-v2"))
        cls.context = s.load_context(cls.repo, cls.archive)
        cls.temp = tempfile.TemporaryDirectory(prefix="r2-select-tests-")
        cls.root = Path(cls.temp.name)
        cls.bundle = cls.root / "original-bundle"
        cls.result = s.export_bundle(cls.context, cls.bundle)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def formal_records(self):
        return copy.deepcopy(self.context["records"])

    @staticmethod
    def performance(records):
        return next(r for r in records if r["suite"] == "performance" and r["replay"] == 0)

    def test_actual_matrix_and_exact_original_images(self):
        self.assertEqual(self.result["formal_windows"], 768)
        self.assertEqual(self.result["images"], 48)
        self.assertEqual(self.result["candidate_cells"], 64)
        self.assertFalse(self.result["scope"]["architecture_recomputed"])
        self.assertFalse(self.result["scope"]["new_dispatcher_qualified"])
        selection = json.loads((self.bundle / "selection.json").read_bytes())
        expected = {0: 111.5, 1: 155, 2: 237.25, 3: 278.25, 4: 634.25, 5: 701.25, 6: 131.25, 7: 175}
        for choice in selection["choices"]:
            self.assertEqual(choice["selected"], "s1:reuse:rvv" if choice["shard"] >= 6 else "s1:reuse:vdot")
            selected = next(c for c in choice["candidates"] if c["id"] == choice["selected"])
            self.assertEqual(selected["statistics"]["mean"], expected[choice["shard"]])
            self.assertEqual([d["dataset"] for d in selected["datasets"]], [0, 1, 2])
            self.assertEqual(sum(len(d["formal_windows"]) for d in selected["datasets"]), 12)
        image = self.bundle / "images/performance-s1-d0-s03/vdot-perf.bin"
        self.assertEqual(s.digest(image.read_bytes()), "74ff608fe5f80435242c7717c70768219291295750a3be6f04b9a82ec916a65f")

    def test_missing_and_duplicate_formal_samples_rejected(self):
        for duplicate in (False, True):
            records = self.formal_records()
            record = self.performance(records)
            if duplicate:
                record["samples"].append(copy.deepcopy(record["samples"][-1]))
            else:
                record["samples"].pop()
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                s.checked_summary(records, self.context["experiment"])

    def test_first_warmup_and_replay_are_not_extra_formal_samples(self):
        for phase in ("first", "warmup"):
            records = self.formal_records()
            sample = next(x for x in self.performance(records)["samples"] if x["phase"] == phase)
            sample["phase"] = "measured"
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                s.checked_summary(records, self.context["experiment"])
        records = self.formal_records()
        next(r for r in records if r["replay"] == 1)["replay"] = 0
        with self.assertRaises(ValueError):
            s.checked_summary(records, self.context["experiment"])

    def test_sample_shape_scope_dataset_case_and_image_binding(self):
        changes = {"m": 99, "scope": "invalid", "dataset": 99, "id": "another-case", "image_sha256": "0" * 64}
        for field, value in changes.items():
            records = self.formal_records()
            self.performance(records)["samples"][8][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                s.checked_summary(records, self.context["experiment"])

    def test_mixed_contract_unqualified_variant_and_incomplete_execution_rejected(self):
        for field, value in (("contract", "r2-s2"), ("variant", "firstdot"),
                             ("exit_code", 1), ("process_started", False), ("negative", True)):
            records = self.formal_records()
            self.performance(records)[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                s.checked_summary(records, self.context["experiment"])

    def test_missing_and_duplicate_normal_record_rejected(self):
        records = self.formal_records()
        records.pop()
        with self.assertRaises(ValueError):
            s.checked_summary(records, self.context["experiment"])
        records = self.formal_records()
        records[-1] = copy.deepcopy(records[0])
        with self.assertRaises(ValueError):
            s.checked_summary(records, self.context["experiment"])

    def test_fastest_nondefault_rvv_is_not_discarded(self):
        rows = copy.deepcopy(self.context["summary"]["rows"])
        row = next(r for r in rows if (r["shard"], r["variant"], r["software"]) == (3, "s0", "basic"))
        row["rvv"].update(total=12, mean=1, minimum=1, maximum=1, pstdev=0)
        choice = s.rank_rows(rows)[3]
        self.assertEqual(choice["selected"], "s0:basic:rvv")
        self.assertEqual(choice["fastest_rvv"], "s0:basic:rvv")
        self.assertFalse(choice["strict_advantage_over_rvv"])

    def test_equal_totals_prefer_rvv_and_do_not_claim_speedup(self):
        rows = copy.deepcopy(self.context["summary"]["rows"])
        for row in rows:
            if row["shard"] == 3:
                for method in ("vdot", "rvv"):
                    row[method].update(total=12, mean=1, minimum=1, maximum=1, pstdev=0)
        choice = s.rank_rows(rows)[3]
        self.assertEqual(choice["selected"], "s0:basic:rvv")
        self.assertEqual(choice["s0_vdot_fallback"], "s0:basic:vdot")
        self.assertEqual(choice["fastest_rvv_over_selected"], 1)
        self.assertFalse(choice["strict_advantage_over_rvv"])

    def test_candidate_requires_full_matrix_and_twelve_window_total(self):
        for field, value in (("samples", 4), ("mean", 0), ("total", -1)):
            rows = copy.deepcopy(self.context["summary"]["rows"])
            rows[0]["rvv"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                s.rank_rows(rows)
        with self.assertRaises(ValueError):
            s.rank_rows(self.context["summary"]["rows"][:-1])

    def test_wrong_self_consistent_archive_identity_rejected(self):
        target = self.root / "wrong-archive"
        target.mkdir()
        raw = s.json_bytes(dict(self.context["archive"].manifest, contract="another-software-contract"))
        (target / "archive-manifest.json").write_bytes(raw)
        (target / "archive-manifest.sha256").write_text(s.digest(raw) + "  archive-manifest.json\n")
        with self.assertRaisesRegex(ValueError, "not the qualified S1"):
            s.load_context(self.repo, target)

    def test_preloaded_reusable_modules_must_belong_to_selected_repo(self):
        a, g = self.context["experiment"], self.context["gate"]
        for module in (g.original, a.legacy_f, a.legacy_m):
            with self.subTest(module=module.__name__), mock.patch.object(module, "__file__", str(self.root / "other.py")):
                with self.assertRaisesRegex(ValueError, "conflicting imported module"):
                    s.load_engine(self.repo)

    def test_modified_elf_bin_manifest_and_run_receipt_rejected(self):
        names = ["images/performance-s1-d0-s03/" + n for n in
                 ("vdot-perf.elf", "vdot-perf.bin", "data/manifest.json")]
        names += ["runs/formal-performance-s1-d0-s03/result.json"]
        for name in names:
            target = self.bundle / name
            original = target.read_bytes()
            try:
                target.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "exported bytes differ"):
                    s.verify_bundle(self.context, self.bundle)
            finally:
                target.write_bytes(original)

    def test_wrong_case_and_missing_fallback_are_recomputed(self):
        target = self.bundle / "selection.json"
        original = target.read_bytes()
        try:
            value = json.loads(original)
            value["choices"][3]["candidates"][0]["datasets"][0]["case_index"] = 99
            target.write_bytes(s.json_bytes(value))
            with self.assertRaisesRegex(ValueError, "selection mapping differs"):
                s.verify_bundle(self.context, self.bundle)
            value = json.loads(original)
            value["choices"][7]["s0_vdot_fallback"] = "s2:reuse:vdot"
            target.write_bytes(s.json_bytes(value))
            with self.assertRaisesRegex(ValueError, "selection mapping differs"):
                s.verify_bundle(self.context, self.bundle)
        finally:
            target.write_bytes(original)

    def test_missing_extra_and_symlinked_export_files_rejected(self):
        target = self.bundle / "images/performance-s1-d0-s03/vdot-perf.bin"
        original = target.read_bytes()
        try:
            target.unlink()
            with self.assertRaisesRegex(ValueError, "file inventory differs"):
                s.verify_bundle(self.context, self.bundle)
        finally:
            target.write_bytes(original)
        extra = self.bundle / "unexpected.txt"
        try:
            extra.write_text("unexpected")
            with self.assertRaisesRegex(ValueError, "file inventory differs"):
                s.verify_bundle(self.context, self.bundle)
        finally:
            extra.unlink()
        if os.name == "posix":
            link = self.bundle / "unexpected-link"
            try:
                link.symlink_to(target)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    s.verify_bundle(self.context, self.bundle)
            finally:
                link.unlink()

    def test_qualification_and_scope_cannot_be_upgraded(self):
        target = self.bundle / "qualification/merged-v2-small-replay-audit-linux.json"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "qualification copy differs"):
                s.verify_bundle(self.context, self.bundle)
        finally:
            target.write_bytes(original)
        target = self.bundle / "bundle-state.json"
        original = target.read_bytes()
        try:
            value = json.loads(original)
            value["scope"]["new_dispatcher_qualified"] = True
            target.write_bytes(s.json_bytes(value))
            with self.assertRaisesRegex(ValueError, "state differs"):
                s.verify_bundle(self.context, self.bundle)
        finally:
            target.write_bytes(original)

    def test_export_and_report_refuse_qualified_input_tree(self):
        before = s.digest((self.archive / "archive-manifest.json").read_bytes())
        target = self.archive / "must-not-exist-selection"
        self.assertFalse(target.exists())
        with self.assertRaisesRegex(ValueError, "qualified input tree"):
            s.export_bundle(self.context, target)
        with self.assertRaisesRegex(ValueError, "qualified input tree"):
            s.validate_destination(self.context, self.archive / "must-not-exist-report.json", self.bundle)
        with self.assertRaisesRegex(ValueError, "qualified input tree"):
            s.validate_destination(self.context, self.repo / s.S1 / "must-not-exist-report.json", self.bundle)
        with self.assertRaisesRegex(ValueError, "qualified input tree"):
            s.validate_destination(self.context, self.archive / ".." / self.archive.name / "must-not-exist-report.json", self.bundle)
        with self.assertRaisesRegex(ValueError, "outside sealed bundle"):
            s.validate_destination(self.context, self.bundle / "report.json", self.bundle)
        self.assertFalse(target.exists())
        self.assertEqual(s.digest((self.archive / "archive-manifest.json").read_bytes()), before)

    def test_existing_bundle_is_never_overwritten(self):
        before = (self.bundle / "bundle-state.json").read_bytes()
        with self.assertRaises(FileExistsError):
            s.export_bundle(self.context, self.bundle)
        self.assertEqual((self.bundle / "bundle-state.json").read_bytes(), before)

    def test_incomplete_status_cannot_resolve_and_forged_pass_cannot_hide_missing_payload(self):
        target = self.bundle / "bundle-state.json"
        original = target.read_bytes()
        try:
            for status in ("EXPORTING", "FAILED"):
                value = json.loads(original)
                value["status"] = status
                target.write_bytes(s.json_bytes(value))
                with self.subTest(status=status), self.assertRaisesRegex(ValueError, "state differs"):
                    s.resolve(self.context, self.bundle, (8, 32), "endtoend", 0)
            target.unlink()
            with self.assertRaisesRegex(ValueError, "file inventory differs"):
                s.resolve(self.context, self.bundle, (8, 32), "endtoend", 0)
        finally:
            target.write_bytes(original)
        missing = self.bundle / "images/performance-s1-d0-s03/vdot-perf.elf"
        raw = missing.read_bytes()
        try:
            missing.unlink()
            with self.assertRaisesRegex(ValueError, "file inventory differs"):
                s.resolve(self.context, self.bundle, (8, 32), "endtoend", 0)
        finally:
            missing.write_bytes(raw)

    def test_unknown_shape_scope_dataset_or_role_is_unsupported(self):
        cases = [((4, 9), "endtoend", 0, "selected"), ((8, 32), "application", 0, "selected"),
                 ((8, 32), "endtoend", 3, "selected"), ((8, 32), "endtoend", 0, "firstdot")]
        for shape, scope, dataset, role in cases:
            with self.subTest(shape=shape, scope=scope, dataset=dataset, role=role), self.assertRaises(ValueError):
                s.resolve(self.context, self.bundle, shape, scope, dataset, role)

    def test_relocated_bundle_resolves_actual_local_paths_and_fallback(self):
        relocated = self.root / "relocated-bundle"
        shutil.copytree(self.bundle, relocated)
        selected = s.resolve(self.context, relocated, (8, 32), "endtoend", 0)
        self.assertEqual(selected["choice"], "s1:reuse:vdot")
        self.assertEqual(selected["artifact"]["symbol"], "t13_kernel_2")
        self.assertEqual(selected["artifact"]["entry_pc"], "0x80006000")
        for key in ("elf", "bin", "case_manifest", "run_result"):
            path = Path(selected["artifact"][key])
            self.assertTrue(path.is_file() and path.is_relative_to(relocated))
        tail = s.resolve(self.context, relocated, (4, 13), "endtoend", 2)
        fallback = s.resolve(self.context, relocated, (4, 13), "endtoend", 2, "s0_vdot_fallback")
        self.assertEqual(tail["choice"], "s1:reuse:rvv")
        self.assertEqual(fallback["choice"], "s0:reuse:vdot")
        self.assertNotEqual(tail["artifact"]["image"], fallback["artifact"]["image"])
        self.assertFalse(tail["new_execution_path_qualified"])


if __name__ == "__main__":
    unittest.main()
