import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location("r3_package",Path(__file__).with_name("package_evaluation.py"))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class ArchiveChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/"files").mkdir()
        raw=b"fixed evidence\n";packed=gzip.compress(raw,mtime=0)
        (self.root/"files/a.gz").write_bytes(packed)
        self.entry=dict(path="raw/a",stored="files/a.gz",gzip=True,raw_bytes=len(raw),raw_sha256=mod.sha(raw),
                        stored_bytes=len(packed),stored_sha256=mod.sha(packed))
        self.write([self.entry])
    def write(self,rows):(self.root/"manifest.json").write_text(json.dumps(dict(files=rows)))
    def test_valid(self):self.assertEqual(mod.verify(self.root)["files"],1)
    def test_raw_tamper_rejected(self):
        self.entry["raw_sha256"]="0"*64;self.write([self.entry])
        with self.assertRaises(ValueError):mod.verify(self.root)
    def test_stored_tamper_rejected(self):
        (self.root/"files/a.gz").write_bytes(b"corrupt")
        with self.assertRaises(ValueError):mod.verify(self.root)
    def test_extra_payload_rejected(self):
        (self.root/"files/extra").write_text("extra")
        with self.assertRaises(ValueError):mod.verify(self.root)
    def test_duplicate_payload_rejected(self):
        self.write([self.entry,self.entry])
        with self.assertRaises(ValueError):mod.verify(self.root)
    def test_path_escape_rejected(self):
        for key,value in (("path","../outside"),("stored","../outside")):
            entry=dict(self.entry);entry[key]=value;self.write([entry])
            with self.assertRaises(ValueError):mod.verify(self.root)

if __name__=="__main__":unittest.main()
