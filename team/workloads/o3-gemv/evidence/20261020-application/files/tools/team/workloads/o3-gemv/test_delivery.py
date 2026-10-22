import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import importlib.util
def local(name):
    path=Path(__file__).with_name(name+".py")
    spec=importlib.util.spec_from_file_location("o3_delivery_test_"+name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
archive=local("archive")
portable=local("portable")
results=local("results")

class DeliveryTests(unittest.TestCase):
    def manifest(self,root,records):
        raw=(json.dumps({"work_root":"/o3-work","files":records})+"\n").encode()
        (root/"archive-manifest.json").write_bytes(raw)
        (root/"archive-manifest.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  archive-manifest.json\n")
        (root/"files").mkdir()
    def test_recheck_rejects_incomplete_campaign(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/"state.json").write_text('{"status":"RUNNING"}')
            with self.assertRaisesRegex(ValueError,"incomplete"):results.recheck(root,root/"out")
    def test_export_rejects_unfinished_measurements(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"work";root.mkdir()
            for name in ("campaign-01","results-01"):(root/name).mkdir()
            (root/"campaign-01/result.json").write_text('{"status":"RUNNING"}')
            (root/"results-01/verification.json").write_text('{}')
            (root/"launch-state.json").write_text('{}')
            with self.assertRaises(AssertionError):archive.create(root,Path(t)/"archive")
            self.assertFalse((Path(t)/"archive").exists())
    def test_portable_rejects_manifest_digest_change(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.manifest(root,[])
            (root/"archive-manifest.sha256").write_text("0"*64)
            with self.assertRaisesRegex(ValueError,"manifest digest"):portable.audit(root,root/"result.json")
    def test_portable_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.manifest(root,[dict(stored="files/../../escape")])
            with self.assertRaisesRegex(ValueError,"archive path"):portable.audit(root,root/"result.json")
    def test_portable_rejects_changed_stored_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            self.manifest(root,[dict(stored="files/data",stored_bytes=1,stored_sha256="0"*64)])
            (root/"files/data").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError,"stored hash"):portable.audit(root,root/"result.json")
