"""Focused fail-closed checks for raw evidence receipt and archive handling."""
import copy
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import audit_combination as a


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root / "raw.log"
        self.raw.write_bytes(b"full128 raw transcript\n" * 7)
        self.archive = self.root / "archive"

    def pack(self):
        return a.pack_archive({"run/stdout.log": self.raw}, self.archive)

    def test_archive_roundtrip_without_original(self):
        proof = self.pack()
        self.raw.unlink()
        self.assertEqual(a.verify_archive(self.archive), proof)
        self.assertFalse(proof["standalone_raw_recomputation"])

    def test_changed_stored_payload_rejected(self):
        self.pack()
        (self.archive / "payload/000000.gz").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "stored archive"):
            a.verify_archive(self.archive)

    def test_changed_raw_digest_rejected(self):
        self.pack()
        manifest = a.read(self.archive / "manifest.json")
        manifest["files"][0]["raw_sha256"] = "0" * 64
        a.save(self.archive / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "decompressed"):
            a.verify_archive(self.archive)

    def test_duplicate_member_rejected(self):
        self.pack()
        manifest = a.read(self.archive / "manifest.json")
        manifest["files"].append(manifest["files"][0])
        a.save(self.archive / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            a.verify_archive(self.archive)

    def test_payload_path_traversal_rejected(self):
        self.pack()
        manifest = a.read(self.archive / "manifest.json")
        manifest["files"][0]["payload"] = "../raw.log"
        a.save(self.archive / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "unsafe"):
            a.verify_archive(self.archive)

    def test_extra_payload_rejected(self):
        self.pack()
        (self.archive / "payload/extra.gz").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "extra or missing"):
            a.verify_archive(self.archive)

    def test_standalone_reproduction_claim_rejected(self):
        self.pack()
        manifest = a.read(self.archive / "manifest.json")
        manifest["independent_clean_reproduction"] = True
        a.save(self.archive / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "contract"):
            a.verify_archive(self.archive)

    def test_fresh_output_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlaps"):
            a.fresh_output(self.root / "nested", [self.root])

    def test_existing_output_rejected(self):
        with self.assertRaisesRegex(ValueError, "new output"):
            a.fresh_output(self.root, [])

    def test_symlink_source_tree_rejected(self):
        (self.root / "linked").symlink_to(self.raw)
        with self.assertRaisesRegex(ValueError, "symlink"):
            a.tree_files(self.root)

    def test_mixed_input_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "mixed external"):
            a.merge_inputs({"file": "a"}, {"file": "b"})


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "run"
        self.run.mkdir()
        for name in ("stdout.log", "stderr.log"):
            (self.run / name).write_text("original")
        self.image = dict(suite="performance", shard=3, dataset=0, variant="firstdot",
                          name="performance-firstdot-d0-s03", path=str(self.root / "image"),
                          image_sha256="i" * 64)
        self.cfg = dict(hardware_source=str(self.root / "hardware"), reference="/ref.so", flash="/flash")
        self.m = types.SimpleNamespace(CONTRACT="current", AUX={"plusArgs": "a" * 64},
                                       NEGATIVE_PASS="negative-pass", NORMAL_PASS="normal-pass")
        self.common = {"/immutable": "d" * 64}
        cwd = self.run / "cwd"
        wanted = dict(self.common, **{str(cwd / "build/plusArgs"): "a" * 64,
                                     str(self.root / "image/vdot-perf.bin"): "i" * 64})
        self.record = dict(self.image, contract="current", mode="merged", negative=False, replay=0,
            cwd=str(cwd), reference="/ref.so", files=wanted,
            command=[str(self.root / "hardware/build/emu"), "-i", str(self.root / "image/vdot-perf.bin"),
                     "--flash=/flash", "--ram-size=128MB", "--diff=/ref.so", "--max-cycles=2000000", "--seed=1"],
            process_started=True, pid=123, exit_code=0, status="normal-pass",
            started="2026-10-26T00:00:00+00:00", finished="2026-10-26T00:00:01+00:00",
            environment_overrides={"XS_NEGATIVE_VECTOR_TARGET": None},
            raw_sha256={name: a.sha(self.run / name) for name in ("stdout.log", "stderr.log")})

    def check(self, record=None):
        return a.process_receipt(record or self.record, self.image, self.run,
                                 self.common, self.cfg, self.m)

    def test_good_receipt(self):
        self.assertEqual(self.check(), self.record["files"])

    def test_nonzero_exit_rejected(self):
        self.record["exit_code"] = 1
        with self.assertRaisesRegex(ValueError, "real exit"):
            self.check()

    def test_bool_exit_is_not_real_integer(self):
        self.record["exit_code"] = False
        with self.assertRaisesRegex(ValueError, "real exit"):
            self.check()

    def test_never_started_rejected(self):
        self.record["process_started"] = False
        with self.assertRaisesRegex(ValueError, "real exit"):
            self.check()

    def test_wrong_command_rejected(self):
        self.record["command"].append("--no-diff")
        with self.assertRaisesRegex(ValueError, "command/input"):
            self.check()

    def test_incomplete_input_closure_rejected(self):
        self.record["files"].pop("/immutable")
        with self.assertRaisesRegex(ValueError, "command/input"):
            self.check()

    def test_transcript_changed_rejected(self):
        (self.run / "stdout.log").write_text("altered")
        with self.assertRaisesRegex(ValueError, "transcript digest"):
            self.check()

    def test_negative_env_leaked_to_normal_rejected(self):
        self.record["environment_overrides"]["XS_NEGATIVE_VECTOR_TARGET"] = "vdot"
        with self.assertRaisesRegex(ValueError, "environment"):
            self.check()

    def test_timestamp_without_timezone_rejected(self):
        self.record["started"] = "2026-10-26T00:00:00"
        with self.assertRaisesRegex(ValueError, "timestamps"):
            self.check()


class PrivateCAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.rel = "team/optimizations/o2/r2-select/entry_c_api.py"
        self.source = self.repo / self.rel
        self.source.parent.mkdir(parents=True)
        self.source.write_text(
            'def audit_run(repo,build,run,external=None):\n'
            '    common=build\n'
            '    expected={"legacy":"fixed"}\n'
            '    g.require(common==expected,"C application common input inventory")\n'
            '    return True\n')
        self.base = types.ModuleType("private-test")
        self.base.g = types.SimpleNamespace(require=a.require)
        self.base.a = types.SimpleNamespace(frozen_m=types.SimpleNamespace(
            hardware_profile=lambda repo, cfg: ({"all-hardware": "fixed"}, {})))
        self.combo = types.SimpleNamespace(c_adapter=lambda repo, identity: self.base)

    def test_only_full_closure_extension_and_no_disk_edit(self):
        before = self.source.read_bytes()
        with patch.object(a, "PINNED_SOURCE", {self.rel: a.sha(self.source)}):
            base, proof = a.private_c_auditor(self.combo, self.repo, {"configuration": {}})
        self.assertTrue(base.audit_run(None, {"legacy": "fixed", "all-hardware": "fixed"}, None))
        with self.assertRaisesRegex(ValueError, "input inventory"):
            base.audit_run(None, {"legacy": "fixed"}, None)
        with self.assertRaisesRegex(ValueError, "input inventory"):
            base.audit_run(None, {"legacy": "fixed", "all-hardware": "fixed", "extra": "bad"}, None)
        self.assertEqual(before, self.source.read_bytes())
        self.assertFalse(proof["source_modified"])

    def test_changed_upstream_source_rejected(self):
        with patch.object(a, "PINNED_SOURCE", {self.rel: "0" * 64}):
            with self.assertRaisesRegex(ValueError, "frozen upstream"):
                a.private_c_auditor(self.combo, self.repo, {"configuration": {}})


class CleanArchiveScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.output = self.root / "output"
        self.output.mkdir()
        self.roots = [self.root / n for n in ("matrix-build", "matrix-run", "c-build", "c-run")]
        for root in self.roots:
            root.mkdir()
        for name in ("matrix-raw-proof.json", "c-raw-proof.json", "external-inputs.json", "evidence-inputs.json"):
            a.save(self.output / name, {})
        self.record = self.root / "hardware-build"
        self.record.mkdir()
        a.save(self.record / "state.json", {"build": "pass"})
        self.adapter = self.root / "adapter.py"
        self.adapter.write_text("fixed adapter")
        self.support = self.root / "support.json"
        a.save(self.support, {"support": "fixed"})
        self.identity = dict(
            contract="zjhwork-0f-firstdot-v2-clean-identity-v1",
            new_source_build=True, support_profile={"new_sources":True, "new_support_builds":True},
            adapter_files={str(self.adapter):a.sha(self.adapter)},
            support_files={str(self.support):a.sha(self.support)},
            configuration={"build_record":str(self.record)}, metadata_sha256={"state.json":a.sha(self.record / "state.json")})
        self.identity_path = self.root / "identity.json"
        a.save(self.identity_path, self.identity)

    def select(self):
        return a.archive_inputs(self.repo, self.identity_path, self.identity,
                                *self.roots, {}, self.output, None)

    def test_clean_contract_does_not_require_current_lock(self):
        selected = self.select()
        self.assertNotIn("identity/hardware-artifact-lock.json", selected)
        self.assertIn("identity/clean-adapter_files/000/adapter.py", selected)
        self.assertIn("identity/clean-support_files/000/support.json", selected)

    def test_clean_support_drift_rejected(self):
        self.support.write_text("changed")
        with self.assertRaisesRegex(ValueError, "support input differs"):
            self.select()

    def test_unknown_identity_contract_rejected(self):
        self.identity["contract"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.select()


if __name__ == "__main__":
    unittest.main(verbosity=2)
