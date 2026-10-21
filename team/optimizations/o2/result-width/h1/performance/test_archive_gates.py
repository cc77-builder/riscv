"""Exercise real optimized-Python archive commands, including corrupted evidence."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def digest(body):
    return hashlib.sha256(body).hexdigest()


def write_manifest(root, records):
    body = (json.dumps(dict(version=1, files=records)) + "\n").encode()
    (root / "archive-manifest.json").write_bytes(body)
    (root / "archive-manifest.sha256").write_text(
        digest(body) + "  archive-manifest.json\n", encoding="ascii")


def fixture(root):
    (root / "files").mkdir()
    records = []
    for name, encoding in (("plain.log", "identity"), ("packed.log.gz", "gzip")):
        raw = b"immutable evidence\n"
        stored = gzip.compress(raw, mtime=0) if encoding == "gzip" else raw
        (root / "files" / name).write_bytes(stored)
        records.append(dict(stored="files/" + name, encoding=encoding,
                            stored_bytes=len(stored), stored_sha256=digest(stored),
                            raw_bytes=len(raw), raw_sha256=digest(raw)))
    write_manifest(root, records)
    return records


class OptimizedArchive(unittest.TestCase):
    def command(self, root):
        return subprocess.run([sys.executable, "-OO", str(HERE / "archive.py"),
                               "--verify-only", "--output", str(root)],
                              capture_output=True, text=True)

    def test_valid_identity_and_gzip_archive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture(root)
            result = self.command(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["files"], 2)

    def test_bad_hashes_and_encoding_are_rejected_under_optimized_python(self):
        for field, value in (("stored_sha256", "0" * 64), ("raw_sha256", "0" * 64),
                             ("stored_bytes", 0), ("raw_bytes", True),
                             ("encoding", "unknown")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                records = fixture(root)
                records[0][field] = value
                write_manifest(root, records)
                self.assertNotEqual(self.command(root).returncode, 0)

    def test_manifest_hash_is_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture(root)
            (root / "archive-manifest.sha256").write_text("0" * 64 + "  archive-manifest.json\n")
            self.assertNotEqual(self.command(root).returncode, 0)

    def test_bad_paths_are_rejected_under_optimized_python(self):
        for path in ("../outside", "/absolute", "C:/absolute", "files\\alias", "outside", "files/../outside"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                records = fixture(root)
                records[0]["stored"] = path
                write_manifest(root, records)
                result = self.command(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(result.stderr, "unsafe portable path|stored path outside files/")

    def test_exact_inventory_and_duplicate_paths(self):
        for change in ("extra", "missing", "duplicate", "logical_alias"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                records = fixture(root)
                if change == "extra":
                    (root / "files/extra.log").write_bytes(b"extra")
                elif change == "missing":
                    (root / records[0]["stored"]).unlink()
                elif change == "duplicate":
                    records.append(copy.deepcopy(records[0]))
                else:
                    old = root / records[1]["stored"]
                    records[1]["stored"] = "files/plain.log.gz"
                    old.rename(root / records[1]["stored"])
                write_manifest(root, records)
                self.assertNotEqual(self.command(root).returncode, 0)

    def test_gzip_corruption_rejected_even_with_updated_stored_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            records = fixture(root)
            bad = (root / records[1]["stored"]).read_bytes()[:-4]
            (root / records[1]["stored"]).write_bytes(bad)
            records[1].update(stored_bytes=len(bad), stored_sha256=digest(bad))
            write_manifest(root, records)
            self.assertNotEqual(self.command(root).returncode, 0)

    def test_symlink_cannot_supply_matching_external_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            root = parent / "archive"
            root.mkdir()
            records = fixture(root)
            original = root / records[0]["stored"]
            external = parent / "external.log"
            original.rename(external)
            try:
                original.symlink_to(external)
            except OSError as exc:
                self.skipTest("host cannot create test symlink: " + str(exc))
            self.assertNotEqual(self.command(root).returncode, 0)

    def test_create_refuses_failed_source_receipts_without_creating_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            work = root / "work"
            (work / "campaign-01").mkdir(parents=True)
            (work / "results-01").mkdir()
            (work / "campaign-01/result.json").write_text(json.dumps(dict(status="FAILED", new_emu_jobs=36)))
            (work / "results-01/verification.json").write_text(json.dumps(dict(
                status="OFFLINE_B0_H1_PAIRED_RECHECK_PASS", original_evidence_unchanged=True)))
            (work / "supervisor-state.json").write_text(json.dumps(dict(
                status="B0_H1_MEASUREMENT_AND_RECHECK_PASS", steps=[dict(exit_code=0)])))
            output = root / "archive"
            result = subprocess.run([sys.executable, "-OO", str(HERE / "archive.py"),
                                     "--work-root", str(work), "--output", str(output)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("campaign did not complete", result.stderr)
            self.assertFalse(output.exists())


class OptimizedInputPreparation(unittest.TestCase):
    def test_bad_input_hash_and_path_fail_before_copy(self):
        for change in ("hash", "path"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                old = root / "old"
                (old / "ours").mkdir(parents=True)
                work = root / "work"
                (work / "campaign-01").mkdir(parents=True)
                source = root / "original.bin"
                source.write_bytes(b"frozen")
                item = dict(original=str(source), sha256=digest(b"frozen"))
                files = {"first.bin": item, **{f"unused-{i}.bin": item for i in range(208)}}
                (old / "ours/first.bin").write_bytes(b"changed" if change == "hash" else b"frozen")
                if change == "path":
                    files = {"../outside.bin": item, **{f"unused-{i}.bin": item for i in range(208)}}
                (old / "input-manifest.json").write_text(json.dumps(dict(files=files)))
                (work / "campaign-01/artifact-pins.json").write_text(json.dumps({str(source): item["sha256"]}))
                script = ("import sys; from pathlib import Path; import prepare_inputs as p; "
                          "p.FROZEN_INPUTS=Path(sys.argv[1]); p.prepare(Path(sys.argv[2]))")
                result = subprocess.run([sys.executable, "-OO", "-c", script, str(old), str(work)],
                                        cwd=HERE, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("frozen input hash mismatch" if change == "hash" else "unsafe portable path", result.stderr)
                self.assertFalse((work / "portable-inputs").exists())

    def test_support_refuses_overwrite_before_reading_git(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "support").mkdir()
            sentinel = root / "support/keep.txt"
            sentinel.write_bytes(b"preserve")
            result = subprocess.run([sys.executable, "-OO", str(HERE / "prepare_inputs.py"),
                                     "--archive", str(root)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("support output already exists", result.stderr)
            self.assertEqual(sentinel.read_bytes(), b"preserve")

    def test_input_mode_is_exclusive_under_optimized_python(self):
        result = subprocess.run([sys.executable, "-OO", str(HERE / "prepare_inputs.py")],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one", result.stderr)


if __name__ == "__main__":
    unittest.main()
