"""Reject additions, omissions and dependency drift at live reuse boundaries."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import live_inputs


class InventoryTests(unittest.TestCase):
    def test_macro_and_untracked_additions_and_omissions_are_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root/"macros").mkdir()
            (root/"macros/A.scala").write_text("object A")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            inventory = live_inputs.hardware_files(root)
            self.assertIn("macros/A.scala", inventory)
            with patch("build_inputs.verify_dependencies"), patch.object(live_inputs, "dependency_snapshot", return_value=([], {"dep/a":"a"*64})):
                pins = dict(files=inventory,dependency_files={},native_build_contract={})
                with self.assertRaisesRegex(ValueError, "dependency compiler inventory"):
                    live_inputs.verify(root, pins)
                (root/"macros/B.scala").write_text("object B")
                with self.assertRaisesRegex(RuntimeError, "inventory changed"):
                    live_inputs.verify(root, pins)
                with self.assertRaisesRegex(RuntimeError, "inventory changed"):
                    live_inputs.verify(root, dict(pins, files={}))


if __name__ == "__main__":
    unittest.main()
