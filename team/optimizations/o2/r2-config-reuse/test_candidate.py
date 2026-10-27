"""State hazards and independent expectations for the config-reuse transform."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import candidate as c

C8 = "vsetivli zero, 8, e8, m1, tu, mu"
C32 = "vsetivli zero, 4, e32, m1, tu, mu"


class ConfigProofTests(unittest.TestCase):
    def kept(self, body):
        self.assertEqual(c.prune(body)[0], body)

    def test_first_configuration_and_csr_writes_are_retained(self):
        self.kept(["csrwi vstart, 0", "csrwi vcsr, 7", C8])

    def test_identical_configuration_is_an_identity_transition(self):
        before = [C8, "addi t6, a2, 0", "vle8.v v16, (t6)", C8]
        after, proof = c.prune(before)
        self.assertEqual(after, before[:3])
        self.assertEqual(proof["removed"][0]["index"], 3)
        self.assertEqual(proof["removed"][0]["dominated_by"], 0)
        self.assertEqual(before[-1], C8)
        self.assertEqual(c.prune(after)[0], after)

    def test_nonzero_vstart_cannot_be_ignored(self):
        self.kept([C8, "csrwi vstart, 1", C8])

    def test_unknown_vstart_write_is_a_barrier(self):
        self.kept([C8, "csrw vstart, t0", C8])

    def test_explicit_reset_restores_the_known_zero(self):
        before = [C8, "csrwi vstart, 1", "csrwi vstart, 0", C8]
        self.assertEqual(c.prune(before)[0], before[:-1])

    def test_vcsr_does_not_alias_vstart(self):
        self.assertEqual(c.prune([C8, "csrwi vcsr, 0", C8])[0], [C8, "csrwi vcsr, 0"])

    def test_fault_only_first_load_is_a_barrier(self):
        self.kept([C8, "vle8ff.v v16, (t6)", C8])

    def test_nonzero_destination_is_not_deleted(self):
        self.kept([C8, "vsetivli t0, 8, e8, m1, tu, mu", C8])

    def test_policy_bits_and_vl_are_part_of_the_configuration(self):
        for other in (C8.replace("tu", "ta"), C8.replace("mu", "ma"),
                      C8.replace("8, e8", "7, e8"), C32):
            with self.subTest(other=other):
                self.kept([C8, other, C8])

    def test_unknown_control_and_csr_instructions_are_barriers(self):
        for line in (".Lentry:", "bnez t0, .Lentry", "call unknown", "ret",
                     "csrw mstatus, t0", "vsetvl zero, t0, t1", "fence rw, rw"):
            with self.subTest(line=line):
                self.kept([C8, line, C8])

    def test_word_requires_exact_custom_encoding_and_legal_state(self):
        self.assertEqual(c.prune([C8, ".word 0x0388000b", C8])[0], [C8, ".word 0x0388000b"])
        for line in (".word 0x0188000b", ".word 0x0080d073", ".insn 4, 0x0388000b"):
            with self.subTest(line=line):
                self.kept([C8, line, C8])
        self.kept([C32, ".word 0x0388000b", C32])
        self.kept([C8, "csrwi vstart, 1", ".word 0x0388000b", C8])

    def test_unsupported_avl_is_retained(self):
        for line in ("vsetivli zero, 17, e8, m1, tu, mu",
                     "vsetivli zero, 32, e8, m2, tu, mu"):
            self.kept([line, line])

    def test_no_instruction_separator_or_prefix_matching(self):
        for line in ("addi t6, a2, 0; csrwi vstart, 1",
                     "vle8.v v16, (t6); vsetivli zero, 1, e8, m1, tu, mu",
                     C8 + "; csrwi vstart, 1", ".Lentry: " + C8):
            self.kept([C8, line, C8])

    def test_state_does_not_leak_between_invocations(self):
        c.prune([C8, C8])
        self.kept([C8])

    def test_body_type_is_checked(self):
        for value in (C8, [None], [1]):
            with self.assertRaises(ValueError):
                c.prune(value)

    def test_cli_preflight_never_writes_old_output_or_source(self):
        script = c.ROOT / c.REL / "check.py"
        with tempfile.TemporaryDirectory(prefix="config-preflight-test-") as temp:
            old = Path(temp) / "evidence"
            old.mkdir()
            (old / "failure.txt").write_bytes(b"preserve prior failure\n")
            for target in (old, c.ROOT):
                failure = target / "failure.txt"
                before = failure.read_bytes() if failure.exists() else None
                names = {p.name for p in target.iterdir()}
                result = subprocess.run([sys.executable, str(script), "--repo", str(c.ROOT),
                                         "--output", str(target), "--llvm-library", str(Path(temp) / "unused.so")],
                                        capture_output=True, text=True, timeout=15)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("fresh output outside source tree required", result.stderr)
                self.assertEqual(failure.read_bytes() if failure.exists() else None, before)
                self.assertEqual({p.name for p in target.iterdir()}, names)

    def test_assembler_helper_does_not_overwrite_existing_object(self):
        with tempfile.TemporaryDirectory(prefix="config-assembler-test-") as temp:
            source, output = Path(temp) / "input.S", Path(temp) / "old.o"
            source.write_text(".text\n", encoding="utf-8")
            output.write_bytes(b"preserve object\n")
            result = subprocess.run([sys.executable, str(c.ROOT / c.REL / "llvm_assemble.py"),
                                     str(source), str(output), "--library", str(Path(temp) / "unused.so")],
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), b"preserve object\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
