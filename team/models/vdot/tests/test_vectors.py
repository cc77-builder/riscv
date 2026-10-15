"""Validate the committed corpus independently of model.py/generate.py.

The arithmetic oracle decodes signed bytes; state expectations are derived
from serialized snapshots, never by calling the implementation under test.
"""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read_rows(name):
    return [json.loads(line) for line in (DATA / name).read_text(encoding="utf-8").splitlines()]


def reference_sum(a, b):
    a_bytes, b_bytes = a.to_bytes(16, "little"), b.to_bytes(16, "little")
    products = [int.from_bytes(a_bytes[i:i + 1], "little", signed=True)
                * int.from_bytes(b_bytes[i:i + 1], "little", signed=True)
                for i in range(8)]
    total = sum(products)
    encoded = int.from_bytes(total.to_bytes(4, "little", signed=True), "little")
    return total, encoded


class CommittedVectorTests(unittest.TestCase):
    def hex128(self, text):
        self.assertRegex(text, r"^0x[0-9a-f]{32}$")
        return int(text, 16)

    def test_manifest_and_all_file_hashes(self):
        manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["contract"], "vdot-s8x8-r32-v0.1")
        self.assertEqual(manifest["seed"], 0x20261011)
        self.assertEqual(manifest["random_count"], 10000)
        self.assertEqual(set(manifest["files"]),
                         {"directed.jsonl", "random.jsonl", "smoke.jsonl", "state.jsonl"})
        for name, info in manifest["files"].items():
            with self.subTest(file=name):
                payload = (DATA / name).read_bytes()
                self.assertNotIn(b"\r", payload)
                self.assertTrue(payload.endswith(b"\n"))
                self.assertEqual(hashlib.sha256(payload).hexdigest(), info["sha256"])
                rows = read_rows(name)
                self.assertEqual(len(rows), info["count"])
                self.assertEqual(len({row["id"] for row in rows}), len(rows))
        for name, digest in manifest["source_sha256"].items():
            self.assertIn(name, ("model.py", "generate.py"))
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_every_serialized_arithmetic_expectation(self):
        for name in ("directed.jsonl", "random.jsonl", "smoke.jsonl"):
            for row in read_rows(name):
                with self.subTest(file=name, case=row["id"]):
                    expected_sum, expected_vd = reference_sum(self.hex128(row["vs1"]),
                                                             self.hex128(row["vs2"]))
                    self.assertEqual(row["expected_sum"], expected_sum)
                    self.assertEqual(self.hex128(row["expected_vd"]), expected_vd)

    def test_fixed_prng_and_smoke_selection(self):
        random_rows = read_rows("random.jsonl")
        self.assertEqual(len(random_rows), 10000)
        for i, row in enumerate(random_rows):
            digest = hashlib.sha256(("20261011:" + str(i)).encode("ascii")).digest()
            self.assertEqual(row["id"], f"R{i:05d}")
            self.assertEqual(int(row["vs1"], 16), int.from_bytes(digest[:16], "little"))
            self.assertEqual(int(row["vs2"], 16), int.from_bytes(digest[16:], "little"))
        self.assertEqual(read_rows("smoke.jsonl"), read_rows("directed.jsonl") + random_rows[:32])

    def test_state_expectations_and_decoder_scope(self):
        counts = {}
        for row in read_rows("state.jsonl"):
            with self.subTest(case=row["id"]):
                self.assertRegex(row["instruction"], r"^0x[0-9a-f]{8}$")
                word = int(row["instruction"], 16)
                config, expected = row["config"], row["expected"]
                regs = [0] * 32
                for name, value in row["registers"].items():
                    self.assertRegex(name, r"^v(?:[0-9]|[12][0-9]|3[01])$")
                    regs[int(name[1:])] = self.hex128(value)
                outcome = expected["outcome"]
                counts[outcome] = counts.get(outcome, 0) + 1
                if word & 0xFE00707F != 0x0200000B:
                    # Some neighboring encodings are legal scalar instructions!
                    self.assertEqual(outcome, "decoder_reject")
                    self.assertNotIn("cause", expected)
                    self.assertTrue(expected["unchanged"])
                elif config["vlen_bits"] != 128:
                    self.assertEqual(outcome, "unsupported_configuration")
                    self.assertTrue(expected["unchanged"])
                elif (not config["vector_enabled"] or config["vs"] == 0
                      or config["vl"] != 8 or config["vstart"] != 0
                      or config["vtype"] not in (0, 64, 128, 192)):
                    self.assertEqual(outcome, "illegal_instruction")
                    self.assertEqual(expected["cause"], 2)
                    self.assertTrue(expected["unchanged"])
                else:
                    self.assertEqual(outcome, "ok")
                    total, encoded = reference_sum(regs[(word // 32768) % 32],
                                                   regs[(word // 1048576) % 32])
                    self.assertEqual(expected["signed_sum"], total)
                    self.assertEqual(self.hex128(expected["vd"]), encoded)
                    self.assertEqual(expected["vs_after"], 3)
        self.assertEqual(set(counts),
                         {"ok", "illegal_instruction", "unsupported_configuration", "decoder_reject"})


if __name__ == "__main__":
    unittest.main()
