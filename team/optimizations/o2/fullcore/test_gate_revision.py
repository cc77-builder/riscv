"""A corrected offline gate must be explicit, Git-bound and isolated."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

import recheck


class AuditGateRevision(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "audit"
        self.output.mkdir()
        self.original = object()
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")
        for name in (recheck.AUDITOR_PATH, recheck.DRIVERS[-1]):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((recheck.ROOT / name).read_bytes())
        self.revision = self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args])

    def commit(self):
        self.git("add", "team")
        self.git("-c", "user.name=Audit Test", "-c", "user.email=audit@example.invalid", "commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD").decode().strip()

    def test_default_preserves_original_gate_and_creates_no_override(self):
        with recheck.audit_runtime_gate(self.root, None, self.original, self.output) as (gate, identity):
            self.assertIs(gate, self.original)
            self.assertIsNone(identity)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_explicit_commit_ignores_dirty_gate_and_restores_module_cache(self):
        source = self.root / recheck.DRIVERS[-1]
        original_body = source.read_bytes()
        source.write_bytes(b"raise RuntimeError('unbound checkout gate executed')\n")
        name = "o2_selected_audit_runtime_gate"
        missing = object()
        previous = sys.modules.get(name, missing)
        poison = types.ModuleType(name)
        sys.modules[name] = poison
        try:
            with recheck.audit_runtime_gate(self.root, self.revision, self.original, self.output) as (gate, identity):
                text = ("DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=10 pc=0x80001000 instruction=0x0294050b\n"
                        "v10_high different at pc = 0x80001000, right= 0x0000001000000000, wrong = 0x0\n"
                        "Core 0: ABORT at pc = 0x80000000\n")
                self.assertEqual(gate.validate_negative(text, 1)["bit"], 100)
                self.assertEqual(identity["source_commit"], self.revision)
                self.assertEqual(identity["sha256"], hashlib.sha256(original_body).hexdigest())
                self.assertEqual(Path(identity["snapshot"]).read_bytes(), original_body)
            self.assertIs(sys.modules[name], poison)
        finally:
            if previous is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    def test_wrong_auditor_or_nonimmutable_revision_is_rejected(self):
        (self.root / recheck.AUDITOR_PATH).write_bytes(b"# another auditor\n")
        other = self.commit()
        for revision, message in ((other, "does not bind the executing auditor"),
                                  ("HEAD", "invalid original source commit")):
            with self.subTest(revision=revision), self.assertRaisesRegex(ValueError, message):
                with recheck.audit_runtime_gate(self.root, revision, self.original, self.output):
                    self.fail("unbound auditor accepted")
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
