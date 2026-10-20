import ast
import json
from pathlib import Path
import tempfile
import unittest
import resume
class RecoveryTests(unittest.TestCase):
    def test_exact_pending_set(self):
        images=[dict(name=f"smoke-{s}",suite="smoke",dataset=0,shard=s) for s in (0,7)]
        images += [dict(name=f"performance-d{d}-s{s:02d}",suite="performance",dataset=d,shard=s) for d in range(3) for s in range(8)]
        expected=resume.expected_jobs(images)
        self.assertEqual(len(expected),56)
        self.assertEqual(len([x for x in expected if x[2]>0]),4)
    def test_extract_original_executor_without_rewriting(self):
        source=Path(resume.c.__file__).read_text()
        node=resume.frozen_executor(source)
        self.assertEqual(node.name,"execute")
        self.assertIn("subprocess.run",ast.unparse(node))
        self.assertNotIn("resume",ast.unparse(node))
    def test_partial_log_is_not_accepted_without_exit(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertFalse(resume.importable(dict(status="RUNNING"),Path(t)))
    def test_complete_marker_cannot_replace_actual_exit(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/"stdout.log").write_text("HIT GOOD TRAP")
            with self.assertRaises((FileNotFoundError,ValueError)):
                resume.importable(dict(status="O3_IMAGE_DIFFTEST_STATE_WINDOWS_AND_PROTOCOL_PASS",finished_utc="now",exit_code=0),root)
