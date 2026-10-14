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

class T12ArchiveNewlineTests(unittest.TestCase):
    def test_log_decode_matches_live_file_reader(self):
        raw=b'hardware LF\nUART CRLF\r\nlegacy CR\rfinal\n'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'run.log'
            path.write_bytes(raw)
            self.assertEqual(checker.decode_log(raw), path.read_text())
            self.assertEqual(path.read_bytes(), raw)

    def test_crlf_control_summary_passes_but_failures_still_reject(self):
        spec=importlib.util.spec_from_file_location('archive_newline_fixture',
                ROOT/'team/tests/test_t12_regression.py')
        fixtures=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixtures)
        raw=fixtures.fixture().replace('\n','\r\n').encode()
        text=checker.decode_log(raw)
        manifest=fixtures.T12AcceptanceTests.manifest
        self.assertEqual(checker.control.check(text,manifest,0)['status'],
                         'T12_CONTROL_REGRESSION_PASS')
        bad=raw.replace(b'failures=0',b'failures=1')
        with self.assertRaisesRegex(ValueError,'summary'):
            checker.control.check(checker.decode_log(bad),manifest,0)
        with self.assertRaisesRegex(ValueError,'malformed|truncated'):
            checker.control.check(checker.decode_log(raw+b'T12_RESPON'),manifest,0)

    def test_invalid_utf8_log_is_not_silently_replaced(self):
        with self.assertRaises(UnicodeDecodeError):
            checker.decode_log(b'log\xff\n')

if __name__=='__main__': unittest.main()
