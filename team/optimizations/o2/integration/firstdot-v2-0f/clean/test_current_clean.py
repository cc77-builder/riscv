"""Metadata adversarial tests only; no EMU execution or qualification."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import tempfile
import unittest
import current_clean_common as c
import current_clean_profile as p

BASELINE_PATH = None
REPO = None

class CurrentMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = c.baseline(BASELINE_PATH)

    def setUp(self):
        adapters = c.adapter_sources(Path(__file__).parent)
        self.source = "f" * 40
        self.before = dict(contract=c.CONTRACT, source_commit=self.source, source_root="/test/source",
            build_script_sha256=adapters["current_clean_build.py"], adapter_sources=adapters,
            baseline_pins_sha256=c.BASELINE_SHA, baseline_source_commit=c.BASELINE_SOURCE,
            hardware_bytes_equal_baseline=True, generated_outputs_reused=False,
            files=self.baseline["files"], dependency_files=self.baseline["dependency_files"],
            config="MinimalConfig", NUM_CORES=1, EMU_THREADS=1, profile="observe",
            JVM_XMX="8G", JVM_XSS="16m", BUILD_JOBS=2, cpu_affinity=[0, 1],
            generated_inventory_scope=c.GENERATED_SCOPE, **c.FLAGS)
        self.pins = copy.deepcopy(self.before)
        self.pins.update(emu_sha256="a" * 64, emu_bytes=123, emu_path="/test/source/build/emu")
        self.generated = sorted([dict(path="build/" + name, bytes=1, sha256=digest)
                                  for name, digest in c.AUX.items()] +
                                [dict(path="build/emu", bytes=123, sha256="a" * 64)], key=lambda row: row["path"])
        self.state = dict(contract=c.CONTRACT, status="CURRENT_CLEAN_BUILD_PASS", build_exit_code=0,
            build_executed=True, runtime_qualified=False, source_commit=self.source, source_root="/test/source",
            emu_sha256="a" * 64, profile="observe", flags=c.FLAGS, cpu_affinity=[0, 1],
            source_files=429, dependency_files=21236, dependencies=126, generated_files=len(self.generated),
            started_utc="2026-10-26T00:00:00+00:00", build_started_utc="2026-10-26T00:00:01+00:00",
            build_finished_utc="2026-10-26T00:00:02+00:00", finished_utc="2026-10-26T00:00:03+00:00")

    def check(self):
        p.validate_metadata(self.pins, self.state, self.before, self.baseline, self.generated,
                            self.before["build_script_sha256"], c.BASELINE_SHA, self.source)

    def test_consistent_metadata_allowed(self):
        self.check()

    def test_pure_software_source_identity_not_old_t17(self):
        self.assertNotEqual(self.source, "34bae6d4acceac939f958199dae53c14bc1f6183")
        self.check()

    def test_wrong_source_rejected(self):
        self.pins["source_commit"] = c.BASELINE_SOURCE
        with self.assertRaises(ValueError): self.check()

    def test_old_t17_status_rejected(self):
        self.state["status"] = "T17_CLEAN_BUILD_PASS"
        with self.assertRaises(ValueError): self.check()

    def test_failed_command_rejected(self):
        self.state["build_exit_code"] = 1
        with self.assertRaises(ValueError): self.check()

    def test_runtime_qualification_cannot_be_invented(self):
        self.state["runtime_qualified"] = True
        with self.assertRaises(ValueError): self.check()

    def test_cancel_fix_reversion_rejected(self):
        self.pins["files"][c.EXEUNIT] = "b" * 64
        with self.assertRaises(ValueError): self.check()

    def test_dependency_drift_rejected(self):
        key = next(iter(self.pins["dependency_files"]))
        self.pins["dependency_files"][key] = "b" * 64
        with self.assertRaises(ValueError): self.check()

    def test_reused_output_rejected(self):
        self.pins["generated_outputs_reused"] = self.before["generated_outputs_reused"] = True
        with self.assertRaises(ValueError): self.check()

    def test_builder_drift_rejected(self):
        self.pins["build_script_sha256"] = "b" * 64
        with self.assertRaises(ValueError): self.check()

    def test_adapter_drift_rejected(self):
        self.pins["adapter_sources"]["current_clean_common.py"] = "b" * 64
        with self.assertRaises(ValueError): self.check()

    def test_prepost_drift_rejected(self):
        self.before["JVM_XMX"] = "12G"
        with self.assertRaises(ValueError): self.check()

    def test_trace_flag_drift_rejected(self):
        self.pins["VDOT_O2_TRACE"] = self.before["VDOT_O2_TRACE"] = "0"
        with self.assertRaises(ValueError): self.check()

    def test_emu_inventory_mismatch_rejected(self):
        next(row for row in self.generated if row["path"] == "build/emu")["sha256"] = "b" * 64
        with self.assertRaises(ValueError): self.check()

    def test_generated_count_is_actual_not_fixed_1672(self):
        self.assertNotEqual(len(self.generated), 1672)
        self.check()
        self.state["generated_files"] = 1672
        with self.assertRaises(ValueError): self.check()

    def test_duplicate_generated_rejected(self):
        self.generated.append(copy.deepcopy(self.generated[0]))
        self.state["generated_files"] += 1
        with self.assertRaises(ValueError): self.check()

    def test_missing_aux_rejected(self):
        self.generated = [r for r in self.generated if r["path"] != "build/plusArgs"]
        self.state["generated_files"] = len(self.generated)
        with self.assertRaises(ValueError): self.check()

    def test_path_escape_rejected(self):
        self.generated[0]["path"] = "build/../outside"
        with self.assertRaises(ValueError): self.check()

    def test_time_inversion_rejected(self):
        self.state["finished_utc"] = "2026-10-25T00:00:00+00:00"
        with self.assertRaises(ValueError): self.check()

    def test_affinity_duplicate_rejected(self):
        self.state["cpu_affinity"] = self.pins["cpu_affinity"] = self.before["cpu_affinity"] = [0, 0]
        with self.assertRaises(ValueError): self.check()

    def test_inventory_detects_added_file_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "build").mkdir()
            for name in ("emu", *c.AUX): (root / "build" / name).write_bytes(b"ok")
            first = c.generated_inventory(root)
            (root / "build/extra.txt").write_bytes(b"new")
            self.assertNotEqual(c.generated_inventory(root), first)
            (root / "build/link").symlink_to("emu")
            with self.assertRaises(ValueError): c.generated_inventory(root)

class CleanIdentityTests(unittest.TestCase):
    def setUp(self):
        import current_clean_identity as identity
        self.i = identity
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "identity.json"
        self.record = Path("/test/build")
        self.profile = dict(source_commit="f" * 40, pins_sha256="a" * 64,
                            reference_provenance={"binary_sha256": "b" * 64})
        self.value = dict(contract=identity.CONTRACT, hardware_contract=p.CONTRACT,
            selected_hardware_commit=c.BASELINE_SOURCE, new_source_build=True,
            new_runtime_execution_completed=False, historical_fixed_hardware_acceptance=False,
            historical_t17_acceptance=False, adapter_files=identity.adapters(), flash_sha256=c.FLASH,
            source_commit="f" * 40, configuration={"source_commit": "f" * 40, "build_record": str(self.record)},
            hardware_profile=self.profile, metadata_sha256={n: "a" * 64 for n in p.META_NAMES},
            reference_sha256="b" * 64, support_files={"/test/support": "a" * 64},
            support_profile={"status": "synthetic for API test"})
    def tearDown(self):
        self.temp.cleanup()
    def check(self, physical=False):
        c.save(self.path, self.value)
        return self.i.validate_identity(Path("/test/repo"), self.path, physical=physical)
    def test_identity_api_returns_value(self):
        self.assertEqual(self.check(), self.value)
    def test_old_identity_contract_rejected(self):
        self.value["contract"] = "t17-current-entry-reproduction-v1"
        with self.assertRaises(ValueError): self.check()
    def test_identity_adapter_drift_rejected(self):
        self.value["adapter_files"][next(iter(self.value["adapter_files"]))] = "c" * 64
        with self.assertRaises(ValueError): self.check()
    def test_identity_reference_mismatch_rejected(self):
        self.value["reference_sha256"] = "c" * 64
        with self.assertRaises(ValueError): self.check()
    def test_physical_api_returns_value_files_profile(self):
        from unittest.mock import patch
        files = {str(self.record / n): "a" * 64 for n in p.META_NAMES}
        with patch.object(self.i, "hardware_profile", return_value=(files, self.profile)), \
             patch.object(self.i, "support_profile", return_value=(self.value["support_files"], self.value["support_profile"])):
            value, linked, profile = self.check(physical=True)
            self.assertEqual(value, self.value)
            self.assertEqual(profile, self.profile)
            self.assertTrue(set(self.i.adapters()) <= set(linked))
    def test_physical_support_drift_rejected(self):
        from unittest.mock import patch
        files = {str(self.record / n): "a" * 64 for n in p.META_NAMES}
        with patch.object(self.i, "hardware_profile", return_value=(files, self.profile)), \
             patch.object(self.i, "support_profile", return_value=({}, {})):
            with self.assertRaises(ValueError): self.check(physical=True)
    def test_restore_command_and_copy_flags_rejected(self):
        row = dict(source="/old", destination="/new", revision="a" * 40, origin="local",
                   command=["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", "/old", "/new"],
                   generated_products_copied=False, cache_worktree_used=False)
        self.i.restore_record(row, False)
        row["cache_worktree_used"] = True
        with self.assertRaises(ValueError): self.i.restore_record(row, False)


class CleanFixtureBindingTests(unittest.TestCase):
    """Execute real frozen host fixture builder/checker; never run NEMU or EMU."""

    def setUp(self):
        if REPO is None:
            self.skipTest("--repo required for real source fixture smoke")
        import sys
        import subprocess
        from types import SimpleNamespace
        import current_clean_fullcore as wrapper
        import current_clean_identity as identity
        sys.path.insert(0, str(REPO / "team/optimizations/o2/integration/firstdot-v2-0f"))
        self.temp = tempfile.TemporaryDirectory(prefix="fixture-smoke-", dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # This deliberately has a different SHA from the historical real NEMU.
        # Only host compile/link identity is exercised, never reference execution.
        source = self.root / "reference-stub.c"
        source.write_text("int current_clean_fixture_identity_stub(void) { return 20261026; }\n")
        self.reference = self.root / "reference-stub.so"
        subprocess.run(["gcc", "-shared", "-fPIC", "-O2", str(source), "-o", str(self.reference)], check=True)
        self.cfg = {"reference": str(self.reference)}
        digest = c.sha(self.reference)
        value = dict(contract=identity.CONTRACT, hardware_contract=p.CONTRACT,
            selected_hardware_commit=c.BASELINE_SOURCE, new_source_build=True,
            new_runtime_execution_completed=False, historical_fixed_hardware_acceptance=False,
            historical_t17_acceptance=False, adapter_files=identity.adapters(), flash_sha256=c.FLASH,
            source_commit="f" * 40, configuration={"source_commit": "f" * 40, "build_record": "/test/build"},
            hardware_profile=dict(source_commit="f" * 40, pins_sha256="a" * 64,
                                  reference_provenance={"binary_sha256": digest},
                                  emu_sha256="e" * 64),
            metadata_sha256={n: "a" * 64 for n in p.META_NAMES}, reference_sha256=digest,
            support_files={}, support_profile={})
        self.fc = wrapper.configure(REPO, value)
        import clean_entry
        self.historical = clean_entry.evidence
        self.historical_ref = self.historical.a.frozen_f.REFERENCE
        self.assertNotEqual(digest, self.historical_ref)
        self.fc.ce.install(REPO, value, physical=False)
        self.fixture_root = self.root / "fixture"
        self.fixture = self.fc.ce.a.frozen_m.build_negative(REPO, self.cfg, self.fixture_root)
        self.archive = SimpleNamespace(
            json=lambda n: c.read(self.fixture_root / n.split("/", 1)[1]),
            raw=lambda n: (self.fixture_root / n.split("/", 1)[1]).read_bytes())

    def check(self, fixture=None):
        self.fc.ce.evidence.fixture_identity(self.archive, "fixture", fixture or self.fixture,
                                            self.cfg, self.fc.ce.a.frozen_m)

    def test_real_fixture_with_new_reference_sha_passes_private_checker(self):
        self.check()
        self.assertIsNot(self.fc.ce.evidence, self.historical)
        self.assertIs(self.fc.ce.evidence.a, self.fc.ce.a)
        self.assertEqual(self.fc.ce.evidence.a.frozen_f.REFERENCE, c.sha(self.reference))
        self.assertEqual(self.historical.a.frozen_f.REFERENCE, self.historical_ref)

    def test_historical_checker_rejects_new_reference_fixture(self):
        # Reproduce the actual stale binding failure without changing old globals.
        with self.assertRaisesRegex(ValueError, "negative fixture identity"):
            self.historical.fixture_identity(self.archive, "fixture", self.fixture,
                                              self.cfg, self.fc.ce.a.frozen_m)
        self.check()

    def test_changed_reference_identity_rejected(self):
        wrong = dict(self.fixture, normal_reference_sha256=self.historical_ref)
        with self.assertRaisesRegex(ValueError, "negative fixture identity"):
            self.check(wrong)

    def test_changed_compile_receipt_rejected(self):
        path = self.fixture_root / "compile/command.json"
        receipt = c.read(path)
        receipt["exit_code"] = 1
        c.save(path, receipt)
        with self.assertRaisesRegex(ValueError, "fixture build receipt"):
            self.check()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-pins", type=Path, required=True)
    ap.add_argument("--repo", type=Path)
    args, rest = ap.parse_known_args()
    BASELINE_PATH = args.baseline_pins
    REPO = args.repo.resolve() if args.repo else None
    unittest.main(argv=[__file__] + rest)
