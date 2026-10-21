"""A build receipt must bind executable drivers to its actual Git revision."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

import build_fullcore as build


class CommittedBuildTools(unittest.TestCase):
    def test_real_git_blob_binding_rejects_modified_or_untracked_executor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            driver = root / "executor.py"
            driver.write_bytes(b"# committed LF executor\n")
            subprocess.run(["git", "-C", str(root), "add", "executor.py"], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c",
                            "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)
            revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
            digest = hashlib.sha256(driver.read_bytes()).hexdigest()
            build.verify_committed_build_tools(root, revision, {"executor.py": digest})
            driver.write_bytes(b"# local replacement\n")
            with self.assertRaisesRegex(ValueError, "differs from committed"):
                build.verify_committed_build_tools(root, revision, {"executor.py": build.sha(driver)})
            with self.assertRaises(subprocess.CalledProcessError):
                build.verify_committed_build_tools(root, revision, {"untracked.py": digest})


if __name__ == "__main__":
    unittest.main()
