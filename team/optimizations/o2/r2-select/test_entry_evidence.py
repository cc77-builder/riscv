"""Meaningful archive mutations using an actually completed R4 probe."""
import copy
import gzip
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import entry_evidence as e


class ChangedArchive:
    def __init__(self, root):
        self.root = root
        self.manifest = e.a.read(root / "archive-manifest.json")

    def record(self, logical):
        for row in self.manifest["files"]:
            name = row["stored"][len("files/"):]
            if row["encoding"] == "gzip":
                name = name[:-3]
            if name == logical:
                return row
        raise KeyError(logical)

    def change(self, logical, update):
        row = self.record(logical)
        path = self.root / row["stored"]
        stored = path.read_bytes()
        raw = gzip.decompress(stored) if row["encoding"] == "gzip" else stored
        data = json.loads(raw)
        update(data)
        raw = e.json_bytes(data)
        stored = gzip.compress(raw, mtime=0) if row["encoding"] == "gzip" else raw
        path.write_bytes(stored)
        row.update(raw_bytes=len(raw), raw_sha256=e.digest(raw), stored_bytes=len(stored), stored_sha256=e.digest(stored))

    def remove(self, logical):
        row = self.record(logical)
        (self.root / row["stored"]).unlink()
        self.manifest["files"].remove(row)

    def finish(self):
        raw = e.json_bytes(self.manifest)
        (self.root / "archive-manifest.json").write_bytes(raw)
        (self.root / "archive-manifest.sha256").write_text(e.digest(raw) + "  archive-manifest.json\n")
        portable, _, _ = e.modules(e.g.ROOT)
        archive = portable.Archive(self.root)
        e.g.save(self.root / "archive-check.json", dict(status=e.BYTE_PASS, **archive.bytes_result))


class ActualArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get("R4_ENTRY_ARCHIVE")
        if not value:
            raise RuntimeError("R4_ENTRY_ARCHIVE must identify the actual completed probe archive")
        cls.root = Path(value)
        cls.report = e.audit(e.g.ROOT, cls.root)
        if cls.report["qualification_scope"] != "probe":
            raise RuntimeError("mutation tests require the minimal actual probe, not a fabricated fixture")
        cls.meta = e.a.read(cls.root / "archive-manifest.json")
        cls.campaign = next(iter(cls.meta["campaigns"]))

    def altered(self, mutate, message):
        with tempfile.TemporaryDirectory(prefix="r4-archive-reject-") as tmp:
            dst = Path(tmp) / "evidence"
            shutil.copytree(self.root, dst)
            changed = ChangedArchive(dst)
            mutate(changed)
            changed.finish()
            # The modified archive is internally byte-consistent; the semantic
            # checker, not a stale manifest digest, must reject it.
            e.byte_check(e.g.ROOT, dst)
            with self.assertRaisesRegex(ValueError, message):
                e.audit(e.g.ROOT, dst)

    def test_actual_probe_has_exact_qualification(self):
        for key, value in dict(formal_normal_images=2, replay_images=2, expected_negative_runs=1,
                               original_emu_processes=5, formal_windows=32, all_window_replay_comparisons=48,
                               new_emu_runs=0, whole_suite_acceptance=False).items():
            self.assertEqual(self.report[key], value)

    def test_resealed_missing_auditor_is_rejected(self):
        self.altered(lambda x: x.remove("tools/" + str(e.g.ENTRY / "entry_evidence.py")), "required evidence tool/contract")

    def test_probe_cannot_be_relabelled_as_full_matrix(self):
        self.altered(lambda x: x.manifest.update(qualification_scope="matrix"), "cohort image inventory")

    def test_replay_cannot_precede_its_formal_run(self):
        prefix = "campaigns/" + self.campaign
        original = e.a.read(self.root / "archive-manifest.json")
        portable, _, _ = e.modules(e.g.ROOT)
        archive = portable.Archive(self.root)
        cached = archive.json(prefix + "/results.json")
        formal = next(r for r in cached["runs"] if r["variant"] == "s0" and r["replay"] == 0)
        replay = next(r for r in cached["runs"] if r["variant"] == "s0" and r["replay"] == 1)
        ftime, rtime = ({k: row[k] for k in ("started", "finished")} for row in (formal, replay))
        def mutate(changed):
            changed.change(prefix + "/runs/formal-" + formal["name"] + "/result.json", lambda x: x.update(rtime))
            changed.change(prefix + "/runs/replay-" + replay["name"] + "/result.json", lambda x: x.update(ftime))
            def summary(x):
                for row in x["runs"]:
                    if row["name"] == formal["name"]:
                        row.update(rtime if row["replay"] == 0 else ftime)
            changed.change(prefix + "/results.json", summary)
        self.altered(mutate, "execution order differs|replay time/signature differs")

    def test_cached_hardware_statement_cannot_contradict_pins(self):
        prefix = "campaigns/" + self.campaign
        self.altered(lambda x: x.change(prefix + "/hardware-profile.json", lambda p: p.update(source_commit="0" * 40)),
                     "cached hardware facts differ")

    def test_operation_identity_cannot_be_dropped(self):
        prefix = "campaigns/" + self.campaign
        self.altered(lambda x: x.change(prefix + "/state.json", lambda s: s.pop("operation_id")), "missing operation identity")


if __name__ == "__main__":
    unittest.main()
