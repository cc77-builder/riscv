"""Run the real shell entry with isolated tools; never launch a hardware build."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class RunnerPreflightTests(unittest.TestCase):
    def run_preflight(self, provide_java):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            script = root / "team/optimizations/o1/check-handoff.sh"
            script.parent.mkdir(parents=True)
            shutil.copyfile(Path(__file__).with_name("check-handoff.sh"), script)
            tools = Path(tmp) / "tools"
            activated = Path(tmp) / "activated"
            tools.mkdir()
            activated.mkdir()
            for name in ("dirname", "realpath", "mkdir", "tee", "python3"):
                source = shutil.which(name)
                self.assertIsNotNone(source)
                (tools / name).symlink_to(source)
            if provide_java:
                java = activated / "java"
                java.write_text("#!/bin/sh\nexit 99\n")
                java.chmod(0o755)
            activate = root / "team/scripts/activate.sh"
            activate.parent.mkdir()
            activate.write_text('export PATH="$TEST_ACTIVATED_TOOLS:$PATH"\n')
            env = dict(os.environ, PATH=str(tools), TEST_ACTIVATED_TOOLS=str(activated))
            output = Path(tmp) / "run"
            result = subprocess.run(["/bin/bash", str(script), str(output)], env=env,
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual((output / "runner.status").read_text(), "exit_code=2\n")
            return result.stdout, str(activated / "java")

    def test_activation_exposes_java_before_tool_checks(self):
        output, java = self.run_preflight(True)
        self.assertIn(java, output)
        self.assertIn("O1_RTL_NOT_RUN_MISSING_TOOL=mill", output)
        self.assertNotIn("O1_RTL_NOT_RUN_MISSING_TOOL=java", output)
        self.assertNotIn("O1_FU_RUNNER_PASS", output)

    def test_missing_java_is_still_rejected(self):
        output, _ = self.run_preflight(False)
        self.assertIn("O1_RTL_NOT_RUN_MISSING_TOOL=java", output)
        self.assertNotIn("O1_FU_RUNNER_PASS", output)


if __name__ == "__main__":
    unittest.main()
