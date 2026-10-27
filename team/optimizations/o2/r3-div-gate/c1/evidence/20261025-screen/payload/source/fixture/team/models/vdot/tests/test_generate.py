"""Independent serialization, PRNG, state-vector and read-only CLI checks."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SOURCE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_DIR))
import generate


def load_rows(payload):
    return [json.loads(line) for line in payload.decode("utf-8").splitlines()]


def independent_sum(a, b):
    a_bytes = int(a, 16).to_bytes(16, "little")[:8]
    b_bytes = int(b, 16).to_bytes(16, "little")[:8]
    return sum(int.from_bytes(bytes([x]), "little", signed=True) *
               int.from_bytes(bytes([y]), "little", signed=True)
               for x, y in zip(a_bytes, b_bytes))


class GeneratorTests(unittest.TestCase):
    def test_directed_manual_expectations_and_formats(self):
        rows = generate.directed_rows()
        expected = [0, 8, 204, -8, 8, 129032, -130048, 131072, 0, 128, -16256]
        self.assertEqual(len(rows), 22)
        self.assertEqual([row["id"] for row in rows[:11]], [f"D{i:02d}" for i in range(11)])
        self.assertEqual([row["expected_sum"] for row in rows[:11]], expected)
        for row in rows:
            self.assertRegex(row["vs1"], r"^0x[0-9a-f]{32}$")
            self.assertRegex(row["vs2"], r"^0x[0-9a-f]{32}$")
            self.assertRegex(row["expected_vd"], r"^0x[0-9a-f]{32}$")
            oracle = independent_sum(row["vs1"], row["vs2"])
            self.assertEqual(row["expected_sum"], oracle, row["id"])
            self.assertEqual(int(row["expected_vd"], 16), oracle % (1 << 32), row["id"])
        self.assertEqual([row["expected_sum"] for row in rows[11:19]],
                         [-3, -6, -9, -12, -15, -18, -21, -24])
        self.assertTrue(all(row["expected_sum"] == 204 for row in rows[19:]))

    def test_prng_contract_byte_order_and_repeatability(self):
        seed = 0x20261011
        rows = generate.random_rows(seed, 33)
        for index in [0, 1, 31, 32]:
            digest = hashlib.sha256(("20261011:" + str(index)).encode("ascii")).digest()
            self.assertEqual(rows[index]["vs1"], "0x" + digest[:16][::-1].hex())
            self.assertEqual(rows[index]["vs2"], "0x" + digest[16:][::-1].hex())
            self.assertEqual(rows[index]["expected_sum"],
                             independent_sum(rows[index]["vs1"], rows[index]["vs2"]))
        self.assertEqual(rows, generate.random_rows(seed, 33))
        self.assertNotEqual(rows[0]["vs1"], generate.random_rows(seed + 1, 1)[0]["vs1"])

    def test_state_aliases_use_one_real_prestate(self):
        rows = generate.state_rows()
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        for row in rows:
            self.assertRegex(row["instruction"], r"^0x[0-9a-f]{8}$")
            if row["expected"]["outcome"] != "ok":
                self.assertTrue(row["expected"]["unchanged"])
                continue
            word = int(row["instruction"], 16)
            src1, src2 = (word >> 15) & 31, (word >> 20) & 31
            registers = row["registers"]
            total = independent_sum(registers.get(f"v{src1}", "0"),
                                    registers.get(f"v{src2}", "0"))
            self.assertEqual(row["expected"]["signed_sum"], total, row["id"])
            self.assertEqual(int(row["expected"]["vd"], 16), total % (1 << 32), row["id"])
            self.assertEqual(row["expected"]["vs_after"], 3)
        by_id = {row["id"]: row for row in rows}
        for name in ["ALIAS_vs1_vs2", "ALIAS_all", "REG_v0_all", "REG_v31_all"]:
            self.assertEqual(by_id[name]["expected"]["signed_sum"], 204)
        self.assertEqual(int(by_id["L03_prefilled_negative"]["registers"]["v10"], 16),
                         (1 << 128) - 1)
        self.assertEqual(by_id["L03_prefilled_negative"]["expected"]["vd"],
                         "0x000000000000000000000000fffffff8")
        for name, row in by_id.items():
            if name.startswith("ILLEGAL_"):
                self.assertEqual(row["expected"],
                                 {"outcome": "illegal_instruction", "cause": 2, "unchanged": True}, name)
            elif name.startswith("UNSUPPORTED_"):
                self.assertEqual(row["expected"]["outcome"], "unsupported_configuration", name)
            elif name.startswith("REJECT_"):
                self.assertEqual(row["expected"],
                                 {"outcome": "decoder_reject", "reason": "not_vdot", "unchanged": True}, name)
        self.assertEqual(by_id["REJECT_encoding_bit04"]["instruction"], "0x0284851b")
        self.assertEqual(by_id["REJECT_encoding_bit03"]["instruction"], "0x02848503")
        self.assertEqual({by_id[f"VS_{s}"]["config"]["vs"] for s in ["initial", "clean", "dirty"]},
                         {1, 2, 3})

    def test_manifest_hashes_and_smoke_selection(self):
        files = generate.build_files(random_count=40)
        self.assertEqual(files, generate.build_files(random_count=40))
        manifest = json.loads(files["manifest.json"])
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["seed"], 0x20261011)
        for name, item in manifest["files"].items():
            self.assertEqual(item["sha256"], hashlib.sha256(files[name]).hexdigest())
            self.assertEqual(item["count"], len(load_rows(files[name])))
        for name, digest in manifest["source_sha256"].items():
            self.assertEqual(digest, hashlib.sha256((SOURCE_DIR / name).read_bytes()).hexdigest())
        self.assertEqual(load_rows(files["smoke.jsonl"]),
                         load_rows(files["directed.jsonl"]) + load_rows(files["random.jsonl"])[:32])
        zero = generate.build_files(random_count=0)
        self.assertEqual(zero["random.jsonl"], b"")
        self.assertEqual(zero["smoke.jsonl"], zero["directed.jsonl"])

    def cli(self, output, *extra):
        return subprocess.run([sys.executable, "-B", str(SOURCE_DIR / "generate.py"),
                               "--output", str(output), "--random-count", "3", *extra],
                              capture_output=True, text=True)

    def test_check_missing_output_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "missing" / "data"
            result = self.cli(output, "--check")
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("directed.jsonl", result.stderr)
            self.assertFalse(output.parent.exists())

    def test_check_detects_corruption_and_leaves_every_file_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "data"
            result = self.cli(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.cli(output, "--check").returncode, 0)
            bad = output / "random.jsonl"
            bad.write_bytes(bad.read_bytes() + b"corrupt\n")
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
            result = self.cli(output, "--check")
            after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
            self.assertEqual(result.returncode, 1)
            self.assertIn("random.jsonl: byte mismatch", result.stderr)
            self.assertEqual(before, after)

    def test_check_without_python_B_is_readonly_and_detects_source_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            for name in ["model.py", "generate.py"]:
                (source / name).write_bytes((SOURCE_DIR / name).read_bytes())
            output = source / "data"
            command = [sys.executable, str(source / "generate.py"),
                       "--output", str(output), "--random-count", "1"]
            generated = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertFalse((source / "__pycache__").exists())
            (source / "model.py").write_bytes((source / "model.py").read_bytes() + b"\n# source drift\n")
            before = {p.relative_to(source).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                      for p in source.rglob("*") if p.is_file()}
            checked = subprocess.run(command + ["--check"], capture_output=True, text=True)
            after = {p.relative_to(source).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                     for p in source.rglob("*") if p.is_file()}
            self.assertEqual(checked.returncode, 1)
            self.assertIn("manifest.json: byte mismatch", checked.stderr)
            self.assertEqual(before, after)
            self.assertFalse((source / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
