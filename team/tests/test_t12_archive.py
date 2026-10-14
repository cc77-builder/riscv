"""Archive integrity failures must reject before any PASS is reconstructed."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('t12_archive_checker',ROOT/'team/scripts/check-t12-archive.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class T12ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'suite').mkdir()
        pins={'source_commit':'reviewed-source','emu_sha256':'reviewed-emu'}
        (self.root/'suite/hardware-pins.json.gz').write_bytes(gzip.compress(json.dumps(pins).encode()))
        self.manifest={'files':{'suite/hardware-pins.json.gz':hashlib.sha256((self.root/'suite/hardware-pins.json.gz').read_bytes()).hexdigest()},'raw_log_sha256':{}}
        self.save()
    def save(self):
        (self.root/'archive-manifest.json').write_text(json.dumps(self.manifest))
    def check(self,source='reviewed-source',emu='reviewed-emu'):
        return checker.validate(self.root,source,emu,'ref','flash')
    def test_modified_archived_bytes_rejected(self):
        (self.root/'suite/hardware-pins.json.gz').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'byte mismatch'): self.check()
    def test_parent_path_rejected(self):
        self.manifest['files']={'../outside':'digest'};self.save()
        with self.assertRaisesRegex(ValueError,'escapes'): self.check()
    def test_unreviewed_hardware_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'source/binary'): self.check(source='other-source')
    def test_unreviewed_emulator_rejected(self):
        with self.assertRaisesRegex(ValueError,'source/binary'): self.check(emu='other-binary')
    def test_wrong_decoded_log_digest_rejected(self):
        (self.root/'run.log.gz').write_bytes(gzip.compress(b'original raw log'))
        self.manifest['raw_log_sha256']={'run.log.gz':'wrong'};self.save()
        with self.assertRaisesRegex(ValueError,'decoded log'): self.check()

if __name__=='__main__': unittest.main()
