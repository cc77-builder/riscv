import tempfile
from pathlib import Path
import unittest
import build_o1 as build

class PreservationTests(unittest.TestCase):
    def fixture(self,base):
        root=base/"build";root.mkdir()
        (root/"emu").write_bytes(b"original executable")
        (root/"constantin.cpp").write_bytes(b"old auxiliary")
        (root/"rtl").mkdir();(root/"rtl/SimTop.sv").write_bytes(b"old rtl")
        saved=base/"saved";pins=build.preserve_generated(root,saved)
        return root,saved,pins

    def test_old_generation_restored_and_new_auxiliary_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);root,saved,pins=self.fixture(b)
            (root/"constantin.cpp").write_bytes(b"new auxiliary")
            (root/"extra.txt").write_bytes(b"new fixed path")
            alterations=build.restore_generated(root,saved,pins,b/"changed")
            self.assertEqual((root/"constantin.cpp").read_bytes(),b"old auxiliary")
            self.assertEqual((root/"rtl/SimTop.sv").read_bytes(),b"old rtl")
            self.assertEqual((root/"emu").read_bytes(),b"original executable")
            self.assertFalse((root/"extra.txt").exists())
            self.assertEqual((b/"changed/extra.txt.removed-from-original").read_bytes(),b"new fixed path")
            self.assertEqual(len(alterations),2)

    def test_unexpected_new_rtl_not_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);root,saved,pins=self.fixture(b)
            unexpected=root/"rtl/unexpected.sv";unexpected.write_bytes(b"unexpected")
            with self.assertRaisesRegex(ValueError,"unexpected new"):
                build.restore_generated(root,saved,pins,b/"changed")
            self.assertEqual(unexpected.read_bytes(),b"unexpected")

    def test_corrupted_preserved_file_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);root,saved,pins=self.fixture(b)
            (saved/"constantin.cpp").write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError,"preserved source changed"):
                build.restore_generated(root,saved,pins,b/"changed")

if __name__=="__main__":unittest.main()
