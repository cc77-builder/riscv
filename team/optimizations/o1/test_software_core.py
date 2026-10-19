"""Reject partial plans, relocated artifact drift and mixed software identities."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import run_software_core as runner


class FrozenSoftware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.images = Path(cls.temporary.name) / "images"
        cls.inventory = runner.extract_images(cls.images)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def profile(self, baseline="original"):
        image = self.images / ("software-" + baseline)
        return (json.loads((image / "current-profile.json").read_text()),
                json.loads((image / "data/manifest.json").read_text()))

    def test_both_complete_frozen_plans_and_relocated_builds(self):
        for baseline, count in runner.PLANS.items():
            self.assertEqual(runner.verify_plan_profile(*self.profile(baseline), baseline), count)
            result = runner.verify_archived_build(self.images / ("software-" + baseline))
            self.assertFalse(result["new_compilation"])

    def test_partial_or_boolean_plan_rejected(self):
        for field, value in (("limit", 189), ("limit", True), ("start", 1), ("start", False)):
            profile, manifest = self.profile()
            profile[field] = value
            with self.assertRaisesRegex(ValueError, "incomplete compiled"):
                runner.verify_plan_profile(profile, manifest, "original")

    def test_foreign_profile_rejected(self):
        profile, manifest = self.profile()
        profile["baseline"] = "lean"
        with self.assertRaisesRegex(ValueError, "wrong software plan"):
            runner.verify_plan_profile(profile, manifest, "original")

    def test_missing_plan_row_rejected(self):
        profile, manifest = self.profile()
        manifest["schedule"].pop()
        with self.assertRaisesRegex(ValueError, "wrong software plan"):
            runner.verify_plan_profile(profile, manifest, "original")

    def test_binary_corruption_rejected(self):
        image = self.images / "software-lean"
        binary = image / "test.bin"
        original = binary.read_bytes()
        try:
            binary.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            with self.assertRaisesRegex(ValueError, "compiled artifact changed"):
                runner.verify_archived_build(image)
        finally:
            binary.write_bytes(original)

    def test_missing_elf_or_escaping_path_rejected(self):
        image = self.images / "software-original"
        path = image / "workload-provenance.json"
        original = path.read_bytes()
        receipt = json.loads(original)
        try:
            for kind in ("missing", "escape"):
                changed = copy.deepcopy(receipt)
                elf = next(p for p in changed["images_sha256"] if p.endswith(".elf"))
                digest = changed["images_sha256"].pop(elf)
                if kind == "escape":
                    changed["images_sha256"][str(Path(elf).parent) + "/../test.elf"] = digest
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    runner.verify_archived_build(image)
        finally:
            path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
