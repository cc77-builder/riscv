"""Small real-file closure tests; no hardware tree, compiler, or EMU is run."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import raw_audit
from probe import sha, require


def verify_files(files):
    for name,digest in files.items():
        require(Path(name).is_file() and sha(name)==digest, "physical file changed: "+name)


class CompleteCommonTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="probe-common-v2-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.hardware=self.root/"hardware";self.hardware.write_bytes(b"hardware")
        self.checker=self.root/"checker";self.checker.write_bytes(b"checker")
        self.build=self.root/"build";self.build.mkdir()
        for name in ("probe-build.json","state.json","images.json","pairs.json","baseline-current.json"):
            (self.build/name).write_text(name)
        image=self.build/"image";(image/"data").mkdir(parents=True)
        (image/"build.json").write_text("image build")
        (image/"data/manifest.json").write_text("manifest")
        self.images=[dict(path=str(image))]
        self.p=SimpleNamespace(repo=self.root)
        self.m=SimpleNamespace(checker_files=lambda repo:{str(self.checker):sha(self.checker)},
                               verify_files=verify_files)
        self.physical=({}, {str(self.hardware):sha(self.hardware)}, {})
        self.expected=raw_audit.complete_common(self.p,self.build,self.images,self.m,self.physical)

    def test_exact_complete_map_and_actual_files(self):
        self.assertEqual(len(self.expected),9)
        raw_audit.verify_common(self.m,dict(self.expected),self.expected)

    def test_missing_shared_input_rejected(self):
        changed=dict(self.expected);changed.pop(str(self.hardware))
        with self.assertRaisesRegex(ValueError,"complete runtime"):
            raw_audit.verify_common(self.m,changed,self.expected)

    def test_extra_shared_input_rejected(self):
        changed=dict(self.expected);changed[str(self.root/"unrelated")]="0"*64
        with self.assertRaisesRegex(ValueError,"complete runtime"):
            raw_audit.verify_common(self.m,changed,self.expected)

    def test_changed_shared_digest_rejected(self):
        changed=dict(self.expected);changed[str(self.hardware)]="0"*64
        with self.assertRaisesRegex(ValueError,"complete runtime"):
            raw_audit.verify_common(self.m,changed,self.expected)

    def test_changed_shared_file_rejected_even_if_receipt_matches(self):
        self.hardware.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"physical file changed"):
            raw_audit.verify_common(self.m,dict(self.expected),self.expected)

    def test_missing_shared_file_rejected_even_if_receipt_matches(self):
        self.hardware.unlink()
        with self.assertRaisesRegex(ValueError,"physical file changed"):
            raw_audit.verify_common(self.m,dict(self.expected),self.expected)

    def test_all_build_and_image_identity_inputs_present(self):
        required={str(self.build/n) for n in ("probe-build.json","state.json","images.json","pairs.json","baseline-current.json")}
        image=Path(self.images[0]["path"])
        required|={str(image/"build.json"),str(image/"data/manifest.json")}
        self.assertTrue(required<=self.expected.keys())


if __name__=="__main__":
    unittest.main()
