"""Regression tests for concrete source-association and input-closure forgeries."""
from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import evidence as e

def archive_fixture():
    cfg = dict(canonical_build="/test/build", build_record="/hardware/meta",
               hardware_source="/hardware/source", build_driver="/hardware/driver.py")
    m = SimpleNamespace(META={"hardware-inputs.json": "pins"}, AUX={"constantin.txt": "aux"})
    originals = {
        "campaign/runtime-inputs.json": "/test/run/runtime-inputs.json",
        "canonical/images.json": "/test/build/images.json",
        "tools/team/tool.py": "/test/repo/team/tool.py",
        "hardware/hardware-inputs.json": "/hardware/meta/hardware-inputs.json",
        "hardware/constantin.txt": "/hardware/source/build/constantin.txt",
        "hardware/build-driver.py": "/hardware/driver.py",
        "hardware/original-build-driver.py": "/hardware/source/team/optimizations/o2/fullcore/build_fullcore.py",
        "sealed-inputs.json": "generated:sealed-inputs",
        "support/host-tests.json": "/test/support/host-tests.json",
    }
    archive = SimpleNamespace(manifest=dict(source_root="/test/repo", work_root="/test/run"),
                              records={logical: dict(original=original) for logical, original in originals.items()})
    sealed = {"/test/build/images.json": dict(sha256="images", logical="canonical/images.json")}
    return archive, cfg, sealed, m

class SourceAssociation(unittest.TestCase):
    def test_valid_associations(self):
        e.original_identity(*archive_fixture())

    def test_changed_original_rejected(self):
        archive, cfg, sealed, m = archive_fixture()
        archive.records["canonical/images.json"]["original"] = "/different/build/images.json"
        with self.assertRaisesRegex(ValueError, "original path differs"):
            e.original_identity(archive, cfg, sealed, m)

    def test_duplicate_original_rejected(self):
        archive, cfg, sealed, m = archive_fixture()
        archive.records["support/extra.json"] = dict(original="/test/build/images.json")
        with self.assertRaisesRegex(ValueError, "duplicate or invalid"):
            e.original_identity(archive, cfg, sealed, m)

    def test_seal_redirect_to_other_valid_payload_rejected(self):
        archive, cfg, sealed, m = archive_fixture()
        sealed["/test/build/images.json"]["logical"] = "campaign/runtime-inputs.json"
        with self.assertRaisesRegex(ValueError, "logical/original association"):
            e.original_identity(archive, cfg, sealed, m)

class InputClosure(unittest.TestCase):
    def inputs(self):
        archive = archive_fixture()[0]
        common = {"/test/build/images.json": "images"}
        records = [dict(files=dict(common, **{"/normal.so": "normal"}))]
        identity = dict(external_files={"/am/library.a": "am"},
                        toolchain={"gcc": dict(path="/usr/bin/gcc", sha256="gcc")})
        sealed = {"/test/build/images.json": dict(sha256="images", logical="canonical/images.json"),
                  "/normal.so": dict(sha256="normal", logical=None),
                  "/am/library.a": dict(sha256="am", logical=None),
                  "/usr/bin/gcc": dict(sha256="gcc", logical=None)}
        return archive, common, records, identity, sealed

    def test_exact_closure(self):
        e.sealed_closure(*self.inputs())

    def test_extra_archived_input_rejected(self):
        args = list(self.inputs())
        args[-1]["/test/support/host-tests.json"] = dict(sha256="extra", logical="support/host-tests.json")
        with self.assertRaisesRegex(ValueError, "exact runtime/build closure"):
            e.sealed_closure(*args)

    def test_missing_external_input_rejected(self):
        args = list(self.inputs())
        del args[-1]["/normal.so"]
        with self.assertRaisesRegex(ValueError, "exact runtime/build closure"):
            e.sealed_closure(*args)

    def test_conflicting_run_input_rejected(self):
        args = list(self.inputs())
        args[2].append(dict(files={"/normal.so": "different"}))
        with self.assertRaisesRegex(ValueError, "conflicting sealed input"):
            e.sealed_closure(*args)

class ActualOrder(unittest.TestCase):
    def records(self):
        zero = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return [dict(cwd="/test/run/runs/" + label + "/cwd",
                     started=(zero + timedelta(seconds=2 * i)).isoformat(),
                     finished=(zero + timedelta(seconds=2 * i + 1)).isoformat())
                for i, label in enumerate(e.expected_order())]

    def test_ordered_receipts_can_be_archived_in_any_order(self):
        records = self.records()
        self.assertEqual(len(e.execution_order(list(reversed(records)))), 57)

    def test_all_s0_then_s1_reordering_rejected(self):
        records = self.records()
        i, j = 5, 6
        for key in ("started", "finished"):
            records[i][key], records[j][key] = records[j][key], records[i][key]
        with self.assertRaisesRegex(ValueError, "paired alternating plan"):
            e.execution_order(records)

    def test_replay_before_original_rejected(self):
        records = self.records()
        for key in ("started", "finished"):
            records[5][key], records[-1][key] = records[-1][key], records[5][key]
        with self.assertRaisesRegex(ValueError, "paired alternating plan"):
            e.execution_order(records)

    def test_concurrent_run_rejected(self):
        records = self.records()
        records[0]["finished"] = records[1]["finished"]
        with self.assertRaisesRegex(ValueError, "concurrent EMU"):
            e.execution_order(records)

class GitDelivery(unittest.TestCase):
    """Exercise the actual index, including ignore omission and stale stored bytes."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="s1-index-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.helper = e.index_helper(e.ROOT)
        self.git("init", "-q")
        self.git("-c", "user.name=S1 test", "-c", "user.email=s1-test@example.invalid",
                 "commit", "--allow-empty", "-qm", "fixture")
        (self.repo / ".gitattributes").write_text("archive/** -text\n")
        self.archive_path = self.repo / "archive"
        (self.archive_path / "files").mkdir(parents=True)
        raw = b"binary\0payload\r\nwith mixed newline\n" * 40
        stored = gzip.compress(raw, mtime=0)
        (self.archive_path / "files/data.bin.gz").write_bytes(stored)
        manifest = dict(version=1, contract=e.a.CONTRACT, files=[dict(
            original="/fixture/data.bin", stored="files/data.bin.gz", encoding="gzip",
            raw_bytes=len(raw), raw_sha256=e.digest(raw), stored_bytes=len(stored),
            stored_sha256=e.digest(stored))])
        self.manifest = manifest
        self.write_manifest()
        self.portable = e.g.load("s1_index_test_portable", e.ROOT / e.PORTABLE)
        self.refresh_cache()

    def git(self, *args, data=None):
        return self.helper.git(self.repo, *args, data=data)

    def write_manifest(self):
        raw = e.json_bytes(self.manifest)
        (self.archive_path / "archive-manifest.json").write_bytes(raw)
        (self.archive_path / "archive-manifest.sha256").write_text(
            e.digest(raw) + "  archive-manifest.json\n", encoding="ascii")

    def refresh_cache(self):
        archive = self.portable.Archive(self.archive_path)
        (self.archive_path / "archive-check.json").write_bytes(e.json_bytes(
            dict(status="R2_S1_ARCHIVE_BYTES_PASS", **archive.bytes_result)))

    def check(self):
        archive = self.portable.Archive(self.archive_path)
        return e.index_payloads(self.repo, self.archive_path, archive, self.helper)

    def test_complete_binary_and_gzip_blobs(self):
        self.git("add", "--", "archive")
        result = self.check()
        self.assertEqual(result["archive_files_in_git_index"], 4)
        self.assertFalse(result["architecture_replayed"])

    def test_ignored_payload_is_not_silent_success(self):
        (self.repo / ".gitignore").write_text("*.bin.gz\n")
        self.git("add", "--", "archive")
        with self.assertRaisesRegex(ValueError, "missing=1 extra=0"):
            self.check()

    def test_missing_metadata(self):
        self.git("add", "--", "archive")
        self.git("rm", "--cached", "--", "archive/archive-manifest.sha256")
        with self.assertRaisesRegex(ValueError, "missing=1 extra=0"):
            self.check()

    def test_stale_gzip_blob(self):
        self.git("add", "--", "archive")
        oid = self.git("hash-object", "-w", "--stdin", data=b"stale\0stored bytes").decode().strip()
        self.git("update-index", "--cacheinfo", "100644", oid, "archive/files/data.bin.gz")
        with self.assertRaisesRegex(ValueError, "staged archive bytes differ"):
            self.check()

    def test_extra_index_entry(self):
        extra = self.archive_path / "stale.json"
        extra.write_text("{}\n")
        self.git("add", "--", "archive")
        extra.unlink()
        with self.assertRaisesRegex(ValueError, "missing=0 extra=1"):
            self.check()

    def test_extra_archive_root_report(self):
        (self.archive_path / "audit.json").write_text("{}\n")
        self.git("add", "--", "archive")
        with self.assertRaisesRegex(ValueError, "disk inventory"):
            self.check()

    def test_old_contract_and_old_cache_rejected(self):
        self.manifest["contract"] = "r2-merged-s2-software-screen-v1"
        self.write_manifest()
        self.refresh_cache()
        self.git("add", "--", "archive")
        with self.assertRaisesRegex(ValueError, "wrong S1 archive contract"):
            self.check()
        self.manifest["contract"] = e.a.CONTRACT
        self.write_manifest()
        self.refresh_cache()
        path = self.archive_path / "archive-check.json"
        cached = json.loads(path.read_text())
        cached["status"] = "R2_MERGED_ARCHIVE_BYTES_PASS"
        path.write_bytes(e.json_bytes(cached))
        self.git("add", "--", "archive")
        with self.assertRaisesRegex(ValueError, "cached byte check differs"):
            self.check()

if __name__ == "__main__":
    unittest.main(verbosity=2)
