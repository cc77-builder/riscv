"""Semantic rejection tests over real probe payloads, without editing the seal.

The read-only overlay represents mutations with a newly consistent byte seal;
this checks inner provenance/acceptance guards beyond gzip/SHA corruption.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
from unittest import mock
import unittest
import rvv_probe_evidence as v

ROOT = Path(__file__).resolve().parents[4]


class Overlay:
    def __init__(self, base):
        self.base = base
        self.records = dict(base.records)
        self.manifest = copy.deepcopy(base.manifest)
        self.bytes_result = base.bytes_result
        self.overrides = {}

    def raw(self, name):
        return self.overrides[name] if name in self.overrides else self.base.raw(name)

    def json(self, name):
        return json.loads(self.raw(name))

    def put(self, name, value):
        self.overrides[name] = v.e.json_bytes(value)


class ProbeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get("R2_RVV_PROBE_TEST_ARCHIVE")
        if not value:
            raise unittest.SkipTest("set R2_RVV_PROBE_TEST_ARCHIVE to completed five-process evidence")
        cls.path = Path(value)
        cls.archive = v.archive_open(ROOT, cls.path)

    def reject(self, overlay, pattern):
        with mock.patch.object(v, "archive_open", return_value=overlay):
            with self.assertRaisesRegex(ValueError, pattern):
                v.audit(ROOT, self.path)

    def test_probe_cannot_be_relabelled_final_selection(self):
        overlay = Overlay(self.archive)
        state = overlay.json("campaign/state.json")
        state["final_selection_qualified"] = True
        overlay.put("campaign/state.json", state)
        self.reject(overlay, "state incomplete or scope changed")

    def test_missing_replay_receipt_rejected(self):
        overlay = Overlay(self.archive)
        images = overlay.json("canonical/images.json")["images"]
        name = "campaign/runs/" + images[0]["name"] + "-r1/result.json"
        overlay.records.pop(name)
        self.reject(overlay, "archived run inventory")

    def test_complete_but_unrelated_library_names_rejected(self):
        overlay = Overlay(self.archive)
        images = overlay.json("canonical/images.json")["images"]
        common = overlay.json("campaign/runtime-inputs.json")
        sealed = overlay.json("sealed-inputs.json")
        changed = {}
        for image in images:
            logical = "canonical/images/" + image["name"] + "/build.json"
            record = overlay.json(logical)
            new_libraries = {}
            for n, (name, digest) in enumerate(record["external_files"].items()):
                alternate = "/unrelated/libraries/" + str(n) + ".a"
                new_libraries[alternate] = digest
                if name in sealed:
                    sealed[alternate] = sealed.pop(name)
            record["external_files"] = new_libraries
            overlay.put(logical, record)
            original = image["path"] + "/build.json"
            changed[original] = common[original] = v.e.digest(overlay.raw(logical))
            sealed[original]["sha256"] = common[original]
        overlay.put("campaign/runtime-inputs.json", common)
        overlay.put("sealed-inputs.json", sealed)
        summary = overlay.json("campaign/results.json")
        for job in v.jobs(images):
            logical = "campaign/runs/" + job + "/result.json"
            record = overlay.json(logical)
            record["files"].update(changed)
            overlay.put(logical, record)
            if record["negative"]:
                summary["negative"] = record
            else:
                summary["runs"] = [record if (r["name"], r["replay"]) == (record["name"], record["replay"])
                                   else r for r in summary["runs"]]
        overlay.put("campaign/results.json", summary)
        self.reject(overlay, "probe build/library identity")

    def test_actual_loaded_reference_cannot_be_relabelled(self):
        overlay = Overlay(self.archive)
        images = overlay.json("canonical/images.json")["images"]
        job = images[1]["name"] + "-r0"
        logical = "campaign/runs/" + job + "/result.json"
        record = overlay.json(logical)
        record["reference"] = "/different/reference.so"
        record["command"] = ["--diff=/different/reference.so" if arg.startswith("--diff=") else arg
                             for arg in record["command"]]
        overlay.put(logical, record)
        self.reject(overlay, "run command/reference differs")

    def test_faster_rvv_summary_must_match_raw_windows(self):
        overlay = Overlay(self.archive)
        result = overlay.json("campaign/results.json")
        result["fastest_rvv"]["mean"] -= 1
        overlay.put("campaign/results.json", result)
        self.reject(overlay, "cached statistics differ: fastest_rvv")


if __name__ == "__main__":
    unittest.main()
