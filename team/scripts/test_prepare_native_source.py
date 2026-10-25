"""Exercise native-source preparation with real temporary Git repositories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("prepare-native-source.py")


class NativeSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="native-source-test-")
        self.root = Path(self.temporary.name)
        self.origin = self.root / "origin"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_SYSTEM=os.devnull, GIT_AUTHOR_NAME="Fixture",
                        GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="Fixture",
                        GIT_COMMITTER_EMAIL="fixture@example.invalid")
        self.git(None, "init", "-q", "--template=", str(self.origin))
        (self.origin / "value.txt").write_text("committed-one\n")
        (self.origin / "raw.bin").write_bytes(b"\x00\r\n\xff")
        self.git(self.origin, "add", ".")
        self.git(self.origin, "commit", "-qm", "one")
        self.base = self.git(self.origin, "rev-parse", "HEAD").decode().strip()
        (self.origin / "value.txt").write_text("committed-two\n")
        self.git(self.origin, "commit", "-qam", "two")
        self.tip = self.git(self.origin, "rev-parse", "HEAD").decode().strip()
        self.counter = 0

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, repo, *args):
        command = ["git"] + (["-C", str(repo)] if repo else []) + list(args)
        return subprocess.run(command, env=self.env, capture_output=True, check=True).stdout

    def run_tool(self, *args, success=True, env=None):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                env=env or self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def store(self, source=None):
        self.counter += 1
        output = self.root / ("store-" + str(self.counter))
        self.run_tool("store", "--source", source or self.origin, "--revision", self.tip, "--output", output)
        return output

    def checkout(self, store, mode="shared", env=None):
        self.counter += 1
        output = self.root / ("checkout-" + str(self.counter))
        self.run_tool("checkout", "--store", store, "--mode", mode, "--output", output, env=env)
        return output / "source"

    def test_seven_layer_chain_is_sealed_without_copying_dirty_inputs(self):
        source = self.origin
        for index in range(6):
            target = self.root / ("chain-" + str(index))
            self.git(None, "clone", "-q", "--shared", str(source), str(target))
            source = target
        (source / "value.txt").write_text("uncommitted\n")
        (source / "untracked.txt").write_text("not a committed input\n")
        old_index = (source / ".git/index").read_bytes()
        old_alternate = (source / ".git/objects/info/alternates").read_bytes()
        store = self.store(source)
        self.assertFalse((store / "repository.git/objects/info/alternates").exists())
        checkout = self.checkout(store)
        self.assertEqual((checkout / "value.txt").read_text(), "committed-two\n")
        self.assertEqual((checkout / "raw.bin").read_bytes(), b"\x00\r\n\xff")
        self.assertFalse((checkout / "untracked.txt").exists())
        self.assertEqual((source / ".git/index").read_bytes(), old_index)
        self.assertEqual((source / ".git/objects/info/alternates").read_bytes(), old_alternate)
        self.assertEqual(self.git(checkout, "show", self.base + ":value.txt"), b"committed-one\n")

    def test_full_bundle_import_and_incremental_bundle_rejection(self):
        full, incremental = self.root / "full.bundle", self.root / "incremental.bundle"
        self.git(self.origin, "bundle", "create", str(full), "HEAD")
        self.git(self.origin, "bundle", "create", str(incremental), self.base + "..HEAD")
        store = self.store(full)
        self.assertEqual(self.git(store / "repository.git", "rev-parse", "HEAD").decode().strip(), self.tip)
        failed = self.root / "failed-bundle"
        self.run_tool("store", "--source", incremental, "--revision", self.tip, "--output", failed, success=False)
        self.assertEqual(json.loads((failed / "state.json").read_text())["status"], "FAILED")
        self.assertFalse((failed / "manifest.json").exists())

    def test_independent_checkout_survives_unavailable_source_and_store(self):
        store = self.store()
        checkout = self.checkout(store, "independent")
        self.origin.rename(self.root / "origin-unavailable")
        store.rename(self.root / "store-unavailable")
        self.assertFalse((checkout / ".git/objects/info/alternates").exists())
        self.git(checkout, "fsck", "--full")
        self.assertEqual(self.git(checkout, "show", self.base + ":value.txt"), b"committed-one\n")

    def test_shared_checkouts_have_independent_indexes(self):
        store = self.store()
        left, right = self.checkout(store), self.checkout(store)
        before = (right / ".git/index").read_bytes()
        refs = self.git(store / "repository.git", "show-ref")
        (left / "value.txt").write_text("only-left\n")
        self.git(left, "add", "value.txt")
        self.assertEqual((right / ".git/index").read_bytes(), before)
        self.assertEqual(self.git(store / "repository.git", "show-ref"), refs)
        self.assertEqual(self.git(right, "status", "--porcelain"), b"")
        self.assertEqual(self.git(left, "remote"), b"")
        self.assertEqual(self.git(right, "remote"), b"")
        self.assertEqual((right / ".git/objects/info/alternates").read_text().strip(),
                         str(store / "repository.git/objects"))

    def test_existing_and_nested_output_preserved(self):
        existing = self.root / "existing"
        existing.mkdir()
        (existing / "keep.txt").write_text("keep\n")
        for output in (existing, self.origin / "nested"):
            self.run_tool("store", "--source", self.origin, "--revision", self.tip, "--output", output, success=False)
        self.assertEqual((existing / "keep.txt").read_text(), "keep\n")
        self.assertFalse((self.origin / "nested").exists())

    def test_output_inside_transitive_donor_is_rejected_before_creation(self):
        source = self.root / "borrower"
        self.git(None, "clone", "-q", "--shared", str(self.origin), str(source))
        output = self.origin / "must-not-appear"
        self.run_tool("store", "--source", source, "--revision", self.tip, "--output", output, success=False)
        self.assertFalse(output.exists())

    def test_git_directory_and_working_subdirectory_are_not_source_roots(self):
        subdirectory = self.origin / "nested"
        subdirectory.mkdir()
        for index, source in enumerate((self.origin / ".git", subdirectory)):
            output = self.origin / ("must-not-appear-" + str(index))
            self.run_tool("store", "--source", source, "--revision", self.tip,
                          "--output", output, success=False)
            self.assertFalse(output.exists())

    def test_changed_manifest_and_head_are_rejected(self):
        store = self.store()
        path = store / "manifest.json"
        original = path.read_bytes()
        changed = json.loads(original)
        changed["scope"] = "wrong scope"
        path.write_text(json.dumps(changed))
        self.run_tool("checkout", "--store", store, "--mode", "shared",
                      "--output", self.root / "bad-manifest", success=False)
        path.write_bytes(original)
        self.git(store / "repository.git", "update-ref", "--no-deref", "HEAD", self.base)
        self.run_tool("checkout", "--store", store, "--mode", "shared",
                      "--output", self.root / "bad-head", success=False)

    def test_missing_commit_rejected(self):
        self.run_tool("store", "--source", self.origin, "--revision", "f" * 40,
                      "--output", self.root / "missing", success=False)

    def test_shallow_promisor_and_grafts_rejected(self):
        shallow = self.root / "shallow"
        self.git(None, "clone", "-q", "--depth=1", self.origin.as_uri(), str(shallow))
        self.run_tool("store", "--source", shallow, "--revision", self.tip,
                      "--output", self.root / "bad-shallow", success=False)
        self.git(self.origin, "config", "remote.origin.promisor", "true")
        self.run_tool("store", "--source", self.origin, "--revision", self.tip,
                      "--output", self.root / "bad-promisor", success=False)
        self.git(self.origin, "config", "--unset", "remote.origin.promisor")
        grafts = self.origin / ".git/info/grafts"
        grafts.parent.mkdir(exist_ok=True)
        grafts.write_text(self.tip + "\n")
        self.run_tool("store", "--source", self.origin, "--revision", self.tip,
                      "--output", self.root / "bad-grafts", success=False)

    def test_changed_pin_and_object_rejected(self):
        store = self.store()
        self.git(store / "repository.git", "update-ref", "refs/heads/pinned-source", self.base)
        self.run_tool("checkout", "--store", store, "--mode", "shared",
                      "--output", self.root / "bad-pin", success=False)
        self.git(store / "repository.git", "update-ref", "refs/heads/pinned-source", self.tip)
        manifest = json.loads((store / "manifest.json").read_text())
        path = store / "repository.git" / next(iter(manifest["objects"]))
        path.chmod(0o600)
        with path.open("ab") as stream:
            stream.write(b"tamper")
        self.run_tool("checkout", "--store", store, "--mode", "shared",
                      "--output", self.root / "bad-object", success=False)

    def test_git_environment_injection_is_ignored(self):
        store = self.store()
        env = dict(self.env, GIT_DIR=str(self.origin / ".git"),
                   GIT_WORK_TREE=str(self.origin), GIT_INDEX_FILE=str(self.root / "injected-index"),
                   GIT_ALTERNATE_OBJECT_DIRECTORIES=str(self.root / "missing-objects"))
        before = (self.origin / ".git/index").read_bytes()
        checkout = self.checkout(store, env=env)
        self.assertEqual((self.origin / ".git/index").read_bytes(), before)
        self.assertFalse((self.root / "injected-index").exists())
        self.assertEqual(self.git(checkout, "status", "--porcelain"), b"")


if __name__ == "__main__":
    unittest.main(verbosity=2)
