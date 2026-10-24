"""Actual archived-ELF admission and corruption checks; no simulator or compiler."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import unittest

import admit as a


class AdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a.g.require(os.name == "posix", "test exact generation using Linux LF sources")
        a.verify_sources()
        cls.temporary = tempfile.TemporaryDirectory(prefix="firstdot-tests-")
        cls.root = Path(cls.temporary.name)
        cls.archive = Path(os.environ.get("FIRSTDOT_ARCHIVE", str(a.ROOT / a.ARCHIVE)))
        cls.inputs = cls.root / "inputs"
        a.extract(cls.archive, cls.inputs)
        cls.build = cls.inputs / "s03-firstdot"

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @contextmanager
    def changed(self, relative, body):
        path = self.build / relative
        original = path.read_bytes()
        path.write_bytes(body)
        try:
            yield
        finally:
            path.write_bytes(original)

    def test_two_actual_images_and_pair(self):
        for variant in ("s1", "firstdot"):
            checked = a.verify_image(self.inputs / ("s03-" + variant), variant)
            self.assertEqual(len(checked["finite_model"]), 4)
            self.assertTrue(all(r["trials"] == 9 for r in checked["finite_model"]))
        self.assertEqual(a.verify_pair(self.inputs)["removed_body_instructions"], {"basic": 32, "reuse": 20})

    def test_actual_first_custom_requires_new_destination(self):
        elf = a.g.ELF((self.build / "vdot-perf.elf").read_bytes())
        manifest = a.read(self.build / "data/manifest.json")
        self.assertEqual(a.negative_target(elf, manifest, "firstdot")["rd"], 0)
        with self.assertRaisesRegex(ValueError, "operand identity"):
            a.negative_target(elf, manifest, "s1")

    def test_regeneration_rejects_changed_assembly(self):
        path = self.build / "data/kernels.S"
        with self.changed("data/kernels.S", path.read_bytes() + b"nop\n"):
            with self.assertRaisesRegex(ValueError, "generated source differs"):
                a.verify_image(self.build, "firstdot")

    def test_regeneration_rejects_rehashed_manifest(self):
        manifest = a.read(self.build / "data/manifest.json")
        manifest["plan"][0]["repeat"] = 99
        body = (json.dumps(manifest) + "\n").encode()
        receipt = a.read(self.build / "build.json")
        receipt["artifacts"]["data/manifest.json"] = a.hashlib.sha256(body).hexdigest()
        with self.changed("data/manifest.json", body), self.changed("build.json", json.dumps(receipt).encode()):
            with self.assertRaisesRegex(ValueError, "exact first-dot regeneration"):
                a.verify_image(self.build, "firstdot")

    def test_missing_source_receipt_rejected(self):
        receipt = a.read(self.build / "build.json")
        receipt["source_sha256"] = {}
        with self.changed("build.json", json.dumps(receipt).encode()):
            with self.assertRaisesRegex(ValueError, "receipt inventory"):
                a.verify_image(self.build, "firstdot")

    def test_changed_build_log_rejected(self):
        with self.changed("make-command/stdout.log", b"forged cached PASS\n"):
            with self.assertRaisesRegex(ValueError, "command log changed"):
                a.verify_image(self.build, "firstdot")

    def test_changed_rvv_loaded_bytes_rejected(self):
        data = bytearray((self.build / "vdot-perf.bin").read_bytes())
        data[16384] ^= 1
        with self.changed("vdot-perf.bin", data):
            with self.assertRaisesRegex(ValueError, "RVV slot changed"):
                a.verify_pair(self.inputs)

    def test_changed_nonkernel_loaded_bytes_rejected(self):
        data = bytearray((self.build / "vdot-perf.bin").read_bytes())
        data[0] ^= 1
        with self.changed("vdot-perf.bin", data):
            with self.assertRaisesRegex(ValueError, "non-kernel loaded bytes differ"):
                a.verify_pair(self.inputs)

    def test_archive_payload_corruption_rejected(self):
        record = next(r for r in a.read(self.archive / "archive-manifest.json")["files"]
                      if r["stored"].startswith(a.PREFIX))
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / record["stored"]
            target.parent.mkdir(parents=True)
            data = bytearray((self.archive / record["stored"]).read_bytes())
            data[-1] ^= 1
            target.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "stored bytes differ"):
                a.archive_bytes(Path(temporary), record)

    def test_archive_identity_and_paths_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "archive-manifest.json").write_text('{"files": []}')
            with self.assertRaisesRegex(ValueError, "frozen archive identity"):
                a.extract(root, root / "output")
        for name in ("../escape", "/absolute", "C:/absolute", "a/../../escape", "a\\..\\escape"):
            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                a.safe_relative(name)

    def test_output_inside_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlap source"):
            a.main(self.archive, a.ROOT / "forbidden-admission-output")


if __name__ == "__main__":
    unittest.main()
