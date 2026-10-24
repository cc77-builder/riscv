"""Refusal tests using the actual completed first-dot run; no simulator launched."""
import copy
import os
from pathlib import Path
import unittest
import tempfile

import runtime as r


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_dir = Path(os.environ["FIRSTDOT_RUN"]).resolve()
        cls.config = r.a.read(cls.run_dir / "configuration.json")
        cls.result = r.a.read(cls.run_dir / "result.json")
        cls.directory = Path(cls.config.get("negative_parent", cls.run_dir)) / "runs/0-firstdot-negative"
        cls.stdout = (cls.directory / "stdout.log").read_text()
        cls.stderr = (cls.directory / "stderr.log").read_text()

    def negative(self, stdout=None, stderr=None, code=1, target=None):
        return r.negative_check(self.stdout if stdout is None else stdout,
                                self.stderr if stderr is None else stderr, code, target or self.config["target"])

    def test_actual_full_state_negative(self):
        self.assertTrue(self.negative()["only_bit64_changed"])

    def test_wrong_negative_exit(self):
        with self.assertRaisesRegex(ValueError, "exit exactly 1"):
            self.negative(code=0)

    def test_old_destination_rejected(self):
        with self.assertRaisesRegex(ValueError, "target differs"):
            self.negative(target=dict(self.config["target"], rd=20))

    def test_wrong_pc_rejected(self):
        with self.assertRaisesRegex(ValueError, "target differs"):
            self.negative(target=dict(self.config["target"], pc="0x8000216c"))

    def test_other_state_bit_rejected(self):
        match = r.re.search(r"FIRSTDOT_STATE_AFTER=([0-9a-f]{2800})", self.stderr)
        value = bytearray.fromhex(match[1])
        value[0] ^= 1
        altered = self.stderr[:match.start(1)] + value.hex() + self.stderr[match.end(1):]
        with self.assertRaisesRegex(ValueError, "exceeds v0 bit64"):
            self.negative(stderr=altered)

    def test_duplicate_injection_rejected(self):
        line = r.INJECT.search(self.stderr)[0]
        with self.assertRaisesRegex(ValueError, "exactly one complete"):
            self.negative(stderr=self.stderr + "\n" + line + "\n")

    def test_fatal_rejected(self):
        with self.assertRaises(ValueError):
            self.negative(stderr=self.stderr + "\nCRITICAL ERROR\n")

    def test_ring_mutations_rejected(self):
        original = "inst 0388000b wen 0 dst 00"
        self.assertIn(original, self.stdout)
        for replacement in ("inst 0388000b wen 1 dst 00", "inst 0388000b wen 0 dst 01",
                            "inst 0388008b wen 0 dst 00"):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.negative(stdout=self.stdout.replace(original, replacement))
        line = next(s for s in self.stdout.splitlines() if original in s)
        for replacement in (line + " (S)", line + " (D)", line + " (00)", "", line + "\n" + line):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.negative(stdout=self.stdout.replace(line, replacement))
        with self.assertRaises(ValueError):
            self.negative(stdout=self.stdout.replace("cmtcnt 3 <--", "cmtcnt 2 <--"))

    def test_parent_output_isolation(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            parent = root / "failed-parent"
            parent.mkdir()
            for output in (parent, parent / "new-run", root):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    r.validate_output(output, (parent,))
            r.validate_output(root / "separate-run", (parent,))

    def test_audit_runtime_source_binding(self):
        import audit_runtime as audit
        files = {str(Path(r.__file__).resolve()): r.g.sha(r.__file__)}
        audit.bind_runtime(files)
        for changed in ({}, {next(iter(files)): "0" * 64}):
            with self.assertRaisesRegex(ValueError, "recorded execution source"):
                audit.bind_runtime(changed)

    def test_audit_output_protects_parent_and_inputs(self):
        import audit_runtime as audit
        for protected in (self.run_dir, Path(self.config["negative_parent"]), r.ROOT,
                          Path(self.config["admission"]), Path(self.config["hardware_root"])):
            with self.subTest(root=protected), self.assertRaisesRegex(ValueError, "external audit output"):
                audit.validate_output(protected / "new-audit-must-not-be-written.json", self.run_dir)
        with tempfile.TemporaryDirectory() as name:
            audit.validate_output(Path(name) / "audit.json", self.run_dir)

    def test_negative_parent_identity_rejected(self):
        if "negative_parent" not in self.config:
            self.fail("v2 continuation fixture required")
        parent = Path(self.config["negative_parent"])
        # Only copy the small pinned metadata: a corrupted parent must be
        # rejected before any large protected-input or stream processing.
        with tempfile.TemporaryDirectory() as name:
            altered = Path(name)
            for relative in r.PARENT:
                dest = altered / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((parent / relative).read_bytes())
            state = altered / "state.json"
            state.write_bytes(state.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "protected input drift"):
                r.import_negative(altered, self.config)
        with self.assertRaisesRegex(ValueError, "configuration differs"):
            r.import_negative(parent, dict(self.config, reference="wrong-reference.so"))

    def test_runtime_overrides_rejected(self):
        original = r.a.read(self.directory / "result.json")
        for key, value in (("command", original["command"] + ["--no-diff"]),
                           ("environment", dict(r.ENV, LD_PRELOAD="wrong.so")),
                           ("files", {}), ("raw_sha256", {}), ("cpu_affinity", [7]),
                           ("process_started", False)):
            changed = dict(original, **{key:value})
            with self.subTest(field=key), self.assertRaises(ValueError):
                r.validate_record(changed, self.directory, self.config, "firstdot", True, 0)

    def test_missing_or_duplicate_formal_sample_rejected(self):
        for extra in (False, True):
            records = copy.deepcopy(self.result["normal"])
            if extra:
                records[0]["samples"].append(records[0]["samples"][-1])
            else:
                records[0]["samples"].pop()
            with self.assertRaises(ValueError):
                r.summarize(records)

    def test_replay_counter_change_rejected(self):
        records = copy.deepcopy(self.result["normal"])
        records[2]["samples"][0]["cycles"] += 1
        with self.assertRaisesRegex(ValueError, "replay differs"):
            r.summarize(records)

    def test_actual_rvv_removal_and_shape_rejected(self):
        build = Path(self.config["admission"]) / "inputs/s03-s1"
        row = r.a.read(build / "data/manifest.json")["rows"][1]
        elf = r.g.ELF((build / "vdot-perf.elf").read_bytes())
        code = r.g.body_bytes(elf.symbol_data("t13_kernel_1"), r.g.auditor(r.ROOT))
        body = list(enumerate(word[0] for word in r.a.struct.iter_unpack("<I", code)))
        r.verify_rvv_work(body, row)
        for opcode in (0xec002057, 0xc4000057):
            index = next(i for i, (_, word) in enumerate(body) if word & 0xfc00707f == opcode)
            with self.assertRaisesRegex(ValueError, "RVV work"):
                r.verify_rvv_work(body[:index] + body[index+1:], row)
        with self.assertRaisesRegex(ValueError, "shape"):
            r.verify_rvv_work(body, dict(row, k=16))


if __name__ == "__main__":
    unittest.main()
