"""Targeted rejection tests against the real GNU probe artifacts; no EMU."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

import runtime_experiment as a
import runtime_gate as g


class RuntimeGateTests(unittest.TestCase):
    repo = build = None

    @classmethod
    def setUpClass(cls):
        g.bind(cls.repo)
        cls.images = a.read(cls.build / "images.json")["images"]
        cls.left = Path(next(i["path"] for i in cls.images if i["variant"] == "firstdot"))
        cls.right = Path(next(i["path"] for i in cls.images if i["variant"] == "config-reuse"))
        cls.elves = [g.ELF((p / "vdot-perf.elf").read_bytes()) for p in (cls.left, cls.right)]
        cls.row = next(r for r in a.read(cls.right / "data/manifest.json")["rows"]
                       if r["software"] == "reuse" and r["method"] == "vdot")
        cls.codes = [e.symbol_data(cls.row["api_symbol"])[8:-4] for e in cls.elves]
        cls.proof = cls.row["config_reuse_proof"]

    def copied(self):
        temp = tempfile.TemporaryDirectory(prefix="s3-real-gate-")
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "candidate"
        shutil.copytree(self.right, path)
        return path

    def test_real_gnu_approved_erasure(self):
        self.assertEqual(g.erasure(*self.codes, self.proof), 7)

    def test_changed_retained_word_rejected(self):
        raw = bytearray(self.codes[1])
        raw[2] ^= 1
        with self.assertRaisesRegex(ValueError, "retained machine word"):
            g.erasure(self.codes[0], bytes(raw), self.proof)

    def test_nonconfiguration_erasure_rejected(self):
        words = [w for w, in struct.iter_unpack("<I", self.codes[0])]
        proof = copy.deepcopy(self.proof)
        removed = {r["index"] for r in proof["removed"]}
        index = next(i for i, w in enumerate(words) if i not in removed and w & 127 != 0x57)
        removed.add(index)
        proof["removed"].append({"index": index})
        proof["candidate_instructions"] -= 1
        proof["retained_indices"] = [i for i in range(len(words)) if i not in removed]
        wrong = b"".join(struct.pack("<I", words[i]) for i in proof["retained_indices"])
        with self.assertRaisesRegex(ValueError, "not vsetivli"):
            g.erasure(self.codes[0], wrong, proof)

    def test_nonzero_rd_configuration_erasure_rejected(self):
        raw = bytearray(self.codes[0])
        at = self.proof["removed"][0]["index"] * 4
        word = int.from_bytes(raw[at:at + 4], "little") | 128
        raw[at:at + 4] = word.to_bytes(4, "little")
        with self.assertRaisesRegex(ValueError, "not vsetivli"):
            g.erasure(bytes(raw), self.codes[1], self.proof)

    def test_nonleaf_loaded_byte_rejected(self):
        path = self.copied()
        raw = bytearray((path / "vdot-perf.bin").read_bytes())
        raw[0] ^= 1
        (path / "vdot-perf.bin").write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "non-kernel loaded bytes"):
            g.paired_layout(self.left, path)

    def test_wrapper_byte_inside_kernel_slot_rejected(self):
        path = self.copied()
        address = self.elves[0].symbols["t13_kernel_0"][0]
        rows = a.read(self.left / "data/manifest.json")["rows"]
        extents = [self.elves[0].symbols[r["api_symbol"]][:2] for r in rows]
        self.assertTrue(all(not start <= address < start + size for start, size in extents))
        offset = address - g.parent.original.RAM
        self.assertTrue(8192 <= offset < 16384)
        raw = bytearray((path / "vdot-perf.bin").read_bytes())
        raw[offset] ^= 1
        (path / "vdot-perf.bin").write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "outside old leaf extents"):
            g.paired_layout(self.left, path)

    def test_call_plan_change_rejected(self):
        path = self.copied()
        manifest = a.read(path / "data/manifest.json")
        manifest["plan"][0], manifest["plan"][1] = manifest["plan"][1], manifest["plan"][0]
        g.save(path / "data/manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "invocation order"):
            g.paired_layout(self.left, path)

    def test_forged_snapshot_digest_rejected(self):
        path = self.copied()
        rel = "team/optimizations/o2/r2-config-reuse/candidate.py"
        target = path / "source/repo" / rel
        target.write_bytes(target.read_bytes() + b"\n# tampered after build\n")
        receipt = a.read(path / "build.json")
        receipt["snapshot_files"][rel] = g.sha(target)
        g.save(path / "build.json", receipt)
        with self.assertRaisesRegex(ValueError, "selected source drift"):
            g.verify_build(path, self.repo)

    def test_missing_pair_rejected(self):
        with self.assertRaisesRegex(ValueError, "counterpart"):
            a.pairs([i for i in self.images if i["variant"] == "firstdot"], self.repo)

    def test_duplicate_image_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            a.pairs(self.images + self.images[:1], self.repo)

    def test_corrupt_baseline_digest_rejected(self):
        pins = a.baseline_pins(self.repo)
        key = self.left.name + "/vdot-perf.bin"
        pins[key]["stored_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "stored bytes"):
            a.anchor(self.repo, pins, key)

    def test_existing_output_cli_rejected_without_write(self):
        def inventory():
            return {p.relative_to(self.build).as_posix(): g.sha(p)
                    for p in self.build.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        before = inventory()
        result = subprocess.run([sys.executable, "-B", str(self.repo / g.S3 / "runtime_experiment.py"),
            "--repo", str(self.repo), "--action", "build", "--identity", "not-read.json",
            "--output", str(self.build)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("new external output required", result.stderr)
        self.assertEqual(before, inventory())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, build, output = [p.resolve() for p in (args.repo, args.build, args.output)]
    a.outside_inputs(output, [repo, build])
    g.require(not output.exists(), "new test result required")
    RuntimeGateTests.repo, RuntimeGateTests.build = repo, build
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeGateTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = dict(status="S3_RUNTIME_GATE_REGRESSIONS_PASS" if result.wasSuccessful() else "FAIL",
                  tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  skipped=len(result.skipped), new_emu_runs=0, new_compilations=0,
                  test_source_sha256=g.sha(Path(__file__)))
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
