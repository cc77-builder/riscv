"""Negative gates for the fixed hardware identity; no EMU execution."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import current_hardware as h

IDENTITY = Path(os.environ.get("CURRENT_HARDWARE_IDENTITY",
    str(Path(__file__).resolve().parents[1] / "current-identity-v3.json")))


class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity = h.read_json(IDENTITY)
        cls.repo = Path(cls.identity["configuration"]["hardware_source"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def changed(self, edit, reseal=False):
        value = copy.deepcopy(self.identity)
        edit(value)
        if reseal:
            value["identity_sha256"] = h.seal(value)
        path = self.work / "identity.json"
        path.write_bytes(h.encoded(value))
        return path

    def test_original_identity(self):
        self.assertEqual(h.validate_identity(self.repo, IDENTITY), self.identity)

    def test_unsealed_identity_edit(self):
        path = self.changed(lambda v: v["configuration"].update(cross_prefix="bad-"))
        with self.assertRaisesRegex(ValueError, "integrity seal"):
            h.validate_identity(self.repo, path)

    def test_resealed_wrong_schema(self):
        path = self.changed(lambda v: v.update(schema=2), reseal=True)
        with self.assertRaisesRegex(ValueError, "version/contract"):
            h.validate_identity(self.repo, path)

    def test_resealed_wrong_hardware_version(self):
        path = self.changed(lambda v: v.update(source_commit="1" * 40), reseal=True)
        with self.assertRaisesRegex(ValueError, "hardware version"):
            h.validate_identity(self.repo, path)

    def test_resealed_wrong_metadata(self):
        path = self.changed(lambda v: v["metadata_sha256"].update(
            {"build-state.json": "0" * 64}), reseal=True)
        with self.assertRaisesRegex(ValueError, "metadata"):
            h.validate_identity(self.repo, path)

    def test_resealed_wrong_emu_profile(self):
        path = self.changed(lambda v: v["hardware_profile"].update(
            emu_sha256="0" * 64), reseal=True)
        with self.assertRaisesRegex(ValueError, "hardware profile"):
            h.validate_identity(self.repo, path)

    def test_resealed_wrong_reference(self):
        path = self.changed(lambda v: v.update(reference_sha256="0" * 64), reseal=True)
        with self.assertRaisesRegex(ValueError, "reference_sha256"):
            h.validate_identity(self.repo, path)

    def test_resealed_wrong_flash(self):
        path = self.changed(lambda v: v.update(flash_sha256="0" * 64), reseal=True)
        with self.assertRaisesRegex(ValueError, "flash_sha256"):
            h.validate_identity(self.repo, path)

    def test_resealed_wrong_inventory(self):
        path = self.changed(lambda v: v["hardware_profile"].update(
            generated_files=1671), reseal=True)
        with self.assertRaisesRegex(ValueError, "inventory"):
            h.validate_identity(self.repo, path)

    def test_resealed_replaced_lock(self):
        value = copy.deepcopy(h.ANCHOR)
        value["source_commit"] = "0" * 40
        lock = self.work / "false-lock.json"
        lock.write_bytes(h.encoded(value))
        path = self.changed(lambda v: v.update(
            hardware_lock=str(lock), hardware_lock_sha256=h.sha(lock)), reseal=True)
        with self.assertRaisesRegex(ValueError, "artifact lock"):
            h.validate_identity(self.repo, path)

    def test_actual_metadata_tamper(self):
        target = self.work / "metadata"
        source = Path(self.identity["configuration"]["build_record"])
        shutil.copytree(source, target)
        (target / "build-state.json").write_text("{}\n")
        with self.assertRaisesRegex(ValueError, "input drift"):
            h.validate_metadata(target)

    def test_binary_hash_fault_rejected_before_source_scan(self):
        cfg = self.identity["configuration"]
        emu = Path(cfg["hardware_source"]) / "build/emu"
        original = h.sha
        with patch.object(h, "sha", side_effect=lambda p: "0" * 64 if Path(p) == emu else original(p)):
            with self.assertRaisesRegex(ValueError, "input drift.*build/emu"):
                h.hardware_profile(self.repo, cfg)

    def test_replaced_reference_binary(self):
        fake = self.work / "reference.so"
        fake.write_bytes(b"not the frozen reference")
        cfg = dict(self.identity["configuration"], reference=str(fake))
        with self.assertRaisesRegex(ValueError, "input drift.*reference.so"):
            h.hardware_profile(self.repo, cfg)

    def test_profile_has_no_mutable_head_label(self):
        self.assertNotIn("source_head_at_verification", self.identity["hardware_profile"])
        self.assertEqual(self.identity["source_checkout_head"], h.ANCHOR["source_commit"])
        self.assertEqual(self.identity["hardware_profile"]["source_commit"], h.ANCHOR["source_commit"])


class GitHardwareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        def run(*args):
            subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.run = run
        run("init")
        run("config", "user.name", "identity-test")
        run("config", "user.email", "identity-test@example.invalid")
        (self.repo / "src").mkdir()
        (self.repo / "scripts").mkdir()
        (self.repo / "src/unit.scala").write_text("fixed hardware\n")
        run("add", ".")
        run("commit", "-m", "hardware fixture")
        self.base = h.git(self.repo, "rev-parse", "HEAD").decode().strip()
        self.pins = {"files": {"src/unit.scala": h.sha(self.repo / "src/unit.scala")}}
        self.anchor = dict(h.ANCHOR, source_commit=self.base)

    def test_software_only_commit_allowed(self):
        (self.repo / "team").mkdir()
        (self.repo / "team/software.c").write_text("software change\n")
        self.run("add", ".")
        self.run("commit", "-m", "software fixture")
        with patch.object(h, "ANCHOR", self.anchor):
            actual = h.verify_source(self.repo, self.pins)
        self.assertNotEqual(actual, self.base)

    def test_hardware_commit_rejected(self):
        (self.repo / "src/unit.scala").write_text("changed hardware\n")
        self.run("add", ".")
        self.run("commit", "-m", "hardware changed")
        with patch.object(h, "ANCHOR", self.anchor):
            with self.assertRaisesRegex(ValueError, "HEAD has hardware changes"):
                h.verify_source(self.repo, self.pins)

    def test_uncommitted_hardware_rejected(self):
        (self.repo / "src/unit.scala").write_text("changed worktree\n")
        with patch.object(h, "ANCHOR", self.anchor):
            with self.assertRaisesRegex(ValueError, "worktree differs"):
                h.verify_source(self.repo, self.pins)

    def test_ignored_compiler_input_rejected(self):
        (self.repo / ".gitignore").write_text("src/extra.scala\n")
        (self.repo / "src/extra.scala").write_text("injected hardware\n")
        with patch.object(h, "ANCHOR", self.anchor):
            with self.assertRaisesRegex(ValueError, "unknown or missing"):
                h.verify_source(self.repo, self.pins)


if __name__ == "__main__":
    unittest.main(verbosity=2)
