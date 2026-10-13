"""Independent checks for the draft vdot-s8x8-r32-v0.1 model.

Run from the repository root with:
    python3 -m unittest discover -s team/models/vdot/tests -v

Only the Python standard library is used. These tests verify the software
contract; passing them is not evidence of RTL, NEMU, or full-core verification.
"""

from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
import random
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import model as dut  # noqa: E402


SEED = 0x20261011
MAX128 = (1 << 128) - 1
MATCH = 0x0200000B
MASK = 0xFE00707F

# Human-calculated cases from team/spec/vdot.md, section 7.1.
DIRECTED = (
    ("D00", [0] * 8, [127] * 8, 0, 0x00000000),
    ("D01", [1] * 8, [1] * 8, 8, 0x00000008),
    ("D02", list(range(1, 9)), list(range(1, 9)), 204, 0x000000CC),
    ("D03", [-1] * 8, [1] * 8, -8, 0xFFFFFFF8),
    ("D04", [-1] * 8, [-1] * 8, 8, 0x00000008),
    ("D05", [127] * 8, [127] * 8, 129032, 0x0001F808),
    ("D06", [-128] * 8, [127] * 8, -130048, 0xFFFE0400),
    ("D07", [-128] * 8, [-128] * 8, 131072, 0x00020000),
    ("D08", [1, -2, 3, -4, 5, -6, 7, -8],
     [8, 7, 6, 5, 4, 3, 2, 1], 0, 0x00000000),
    ("D09", [-128, 0, 0, 0, 0, 0, 0, 0],
     [-1, 0, 0, 0, 0, 0, 0, 0], 128, 0x00000080),
    ("D10", [0, 0, 0, 0, 0, 0, 0, -128],
     [0, 0, 0, 0, 0, 0, 0, 127], -16256, 0xFFFFC080),
)


def reference_pack(lanes, high64=0):
    """Independent byte serialization; never call the model's packer."""
    raw = bytes(value % 256 for value in lanes)
    return int.from_bytes(raw + high64.to_bytes(8, "little"), "little")


def reference_dot(vs1, vs2):
    """Read signed bytes independently of the model's lane/ALU helpers."""
    a = vs1.to_bytes(16, "little")
    b = vs2.to_bytes(16, "little")
    total = sum(
        int.from_bytes(a[i:i + 1], "little", signed=True)
        * int.from_bytes(b[i:i + 1], "little", signed=True)
        for i in range(8)
    )
    encoded = int.from_bytes(total.to_bytes(4, "little", signed=True), "little")
    return total, encoded


class ArithmeticTests(unittest.TestCase):
    def test_contract_identity_and_dimensions(self):
        self.assertEqual(dut.CONTRACT_ID, "vdot-s8x8-r32-v0.1")
        self.assertEqual(
            (dut.INPUT_BITS, dut.PAIRS, dut.RESULT_BITS, dut.VLEN_BITS),
            (8, 8, 32, 128),
        )

    def test_D00_through_D10(self):
        for case_id, a, b, total, encoded in DIRECTED:
            with self.subTest(case=case_id):
                a_before, b_before = a[:], b[:]
                src1, src2 = reference_pack(a), reference_pack(b)
                self.assertEqual(dut.dot_s8(a, b), total)
                self.assertEqual(dut.dot_s8(tuple(a), tuple(b)), total)
                self.assertEqual(dut.pack_lanes(a), src1)
                self.assertEqual(dut.vdot(src1, src2), encoded)
                self.assertEqual(dut.vdot(src1, src2) >> 32, 0)
                self.assertEqual((a, b), (a_before, b_before))

    def test_all_65536_single_signed_byte_products(self):
        low, high = 0, 0
        a, b = [0] * 8, [0] * 8
        for x in range(-128, 128):
            a[0] = x
            for y in range(-128, 128):
                b[0] = y
                actual = dut.dot_s8(a, b)
                self.assertEqual(actual, x * y, (x, y))
                low, high = min(low, actual), max(high, actual)
        self.assertEqual((low, high), (-16256, 16384))

    def test_extrema_require_19_signed_bits(self):
        lower = dut.dot_s8([-128] * 8, [127] * 8)
        upper = dut.dot_s8([-128] * 8, [-128] * 8)
        self.assertEqual((lower, upper), (-130048, 131072))
        self.assertGreater(upper, (1 << 17) - 1)  # signed 18-bit maximum
        self.assertLessEqual(upper, (1 << 18) - 1)  # signed 19-bit maximum
        self.assertEqual(dut.vdot(reference_pack([-128] * 8),
                                  reference_pack([-128] * 8)), 0x00020000)

    def test_lane_order_and_one_hot_inputs(self):
        lanes = [-128, -1, 0, 1, 2, 64, 126, 127]
        self.assertEqual(dut.pack_lanes(lanes), 0x7F7E40020100FF80)
        for i in range(8):
            a = [0] * 8
            a[i] = 3
            with self.subTest(lane=i):
                self.assertEqual(dut.dot_s8(a, lanes), 3 * lanes[i])
                self.assertEqual(dut.vdot(reference_pack(a), reference_pack(lanes)),
                                 reference_dot(reference_pack(a), reference_pack(lanes))[1])

    def test_high_half_is_ignored_and_negative_is_not_128bit_sign_extended(self):
        highs = (0, (1 << 64) - 1, 0x5555555555555555, 0xAAAAAAAAAAAAAAAA)
        for high_a in highs:
            for high_b in highs:
                with self.subTest(high_a=hex(high_a), high_b=hex(high_b)):
                    a = dut.pack_lanes([-1] * 8, high64=high_a)
                    b = dut.pack_lanes([1] * 8, high64=high_b)
                    self.assertEqual(a, reference_pack([-1] * 8, high_a))
                    self.assertEqual(b, reference_pack([1] * 8, high_b))
                    self.assertEqual(dut.vdot(a, b), 0x000000000000000000000000FFFFFFF8)

    def test_10000_fixed_seed_pairs_with_independent_byte_oracle(self):
        rng = random.Random(SEED)
        for case in range(10000):
            src1, src2 = rng.getrandbits(128), rng.getrandbits(128)
            total, encoded = reference_dot(src1, src2)
            context = (case, hex(src1), hex(src2))
            self.assertEqual(dut.vdot(src1, src2), encoded, context)
            self.assertEqual(dut.vdot(src2, src1), encoded, context)
            self.assertGreaterEqual(total, -130048, context)
            self.assertLessEqual(total, 131072, context)
            # Simultaneous lane permutation is a mathematical invariant.
            order = list(range(8))
            rng.shuffle(order)
            a, b = src1.to_bytes(16, "little"), src2.to_bytes(16, "little")
            perm_a = int.from_bytes(bytes(a[i] for i in order) + a[8:], "little")
            perm_b = int.from_bytes(bytes(b[i] for i in order) + b[8:], "little")
            self.assertEqual(dut.vdot(perm_a, perm_b), encoded, context)


class EncodingTests(unittest.TestCase):
    def test_known_word_and_source_field_order(self):
        self.assertEqual(dut.encode(10, 8, 9), 0x0284850B)
        self.assertEqual(dut.encode(10, 8, 9).to_bytes(4, "little"),
                         bytes.fromhex("0b 85 84 02"))
        inst = dut.decode(0x0284850B)
        self.assertEqual((inst.vd, inst.vs2, inst.vs1), (10, 8, 9))
        self.assertEqual(inst, dut.Instruction(vd=10, vs2=8, vs1=9))
        with self.assertRaises(FrozenInstanceError):
            inst.vd = 0

    def test_all_32768_register_encodings(self):
        for vd in range(32):
            for vs2 in range(32):
                for vs1 in range(32):
                    expected = MATCH + vd * 128 + vs1 * 32768 + vs2 * 1048576
                    actual = dut.encode(vd, vs2, vs1)
                    self.assertEqual(actual, expected, (vd, vs2, vs1))
                    inst = dut.decode(expected)
                    self.assertEqual((inst.vd, inst.vs2, inst.vs1), (vd, vs2, vs1))

    def test_every_fixed_bit_flip_is_illegal(self):
        for bit in range(32):
            if MASK & (1 << bit):
                with self.subTest(bit=bit):
                    with self.assertRaises(dut.IllegalInstruction) as caught:
                        dut.decode(0x0284850B ^ (1 << bit))
                    self.assertEqual(caught.exception.cause, 2)

    def test_random_nonmatching_words_are_illegal(self):
        rng = random.Random(SEED ^ 0xDEC0DE)
        for _ in range(1000):
            word = rng.getrandbits(32)
            if word & MASK != MATCH:
                with self.assertRaises(dut.IllegalInstruction) as caught:
                    dut.decode(word)
                self.assertEqual(caught.exception.cause, 2)


class ExecutionTests(unittest.TestCase):
    def make_registers(self):
        # All slots are nonzero, including v0; untouched destinations are visible.
        return [int.from_bytes(bytes([i + 1]) * 16, "little") for i in range(32)]

    def assert_execution(self, vd, vs2, vs1, registers, config=None):
        if config is None:
            config = dut.VectorConfig()
        before, config_before = tuple(registers), asdict(config)
        total, encoded = reference_dot(before[vs1], before[vs2])
        result = dut.execute(dut.encode(vd, vs2, vs1), registers, config)
        expected = list(before)
        expected[vd] = encoded
        self.assertIsInstance(result.registers, tuple)
        self.assertEqual(result.registers, tuple(expected))
        self.assertEqual(result.signed_sum, total)
        self.assertEqual(result.config, replace(config, vs=3))
        self.assertEqual(tuple(registers), before, "execute mutated the caller's register bank")
        self.assertEqual(asdict(config), config_before, "execute mutated its input configuration")
        return result

    def test_directed_values_with_dirty_old_destination(self):
        for case_id, a, b, total, encoded in DIRECTED:
            with self.subTest(case=case_id):
                registers = self.make_registers()
                registers[8], registers[9] = reference_pack(a), reference_pack(b)
                registers[10] = MAX128
                result = self.assert_execution(10, 8, 9, registers)
                self.assertEqual((result.signed_sum, result.registers[10]), (total, encoded))

    def test_aliases_and_v0_v31_use_instruction_before_state(self):
        aliases = (
            (10, 8, 9), (9, 8, 9), (8, 8, 9), (10, 8, 8), (8, 8, 8),
            (0, 31, 9), (31, 0, 9), (9, 31, 0), (0, 0, 0), (31, 31, 31),
        )
        registers = self.make_registers()
        registers[0] = reference_pack([-128, -1, 2, -3, 4, -5, 6, -7], 0xA5A5A5A5A5A5A5A5)
        registers[8] = reference_pack([-1, 2, -3, 4, -5, 6, -7, 8])
        registers[9] = reference_pack([8, -7, 6, -5, 4, -3, 2, -1])
        registers[31] = reference_pack([127, -128, 3, -4, 5, -6, 7, -8])
        for vd, vs2, vs1 in aliases:
            with self.subTest(vd=vd, vs2=vs2, vs1=vs1):
                self.assert_execution(vd, vs2, vs1, registers)

    def test_policy_combinations_rounding_saturation_and_vs_dirty(self):
        registers = self.make_registers()
        registers[8], registers[9] = reference_pack([-1] * 8), reference_pack([1] * 8)
        for vtype in (0, 0x40, 0x80, 0xC0):
            for vs in (1, 2, 3):
                for vxrm in range(4):
                    for vxsat in (0, 1):
                        with self.subTest(vtype=vtype, vs=vs, vxrm=vxrm, vxsat=vxsat):
                            config = dut.VectorConfig(vtype=vtype, vs=vs, vxrm=vxrm, vxsat=vxsat)
                            self.assertEqual(config.vcsr, vxrm * 2 + vxsat)
                            result = self.assert_execution(10, 8, 9, registers, config)
                            self.assertEqual(result.config.vcsr, config.vcsr)
                            self.assertEqual(result.registers[10], 0xFFFFFFF8)

    def test_config_is_frozen_and_default_execution_works(self):
        config = dut.VectorConfig()
        with self.assertRaises(FrozenInstanceError):
            config.vs = 0
        registers = tuple(self.make_registers())
        result = dut.execute(dut.encode(10, 8, 9), registers)
        self.assertEqual(result.registers[10], reference_dot(registers[9], registers[8])[1])

    def test_256_random_register_banks_against_byte_oracle(self):
        rng = random.Random(SEED ^ 0xE7EC)
        for case in range(256):
            registers = [rng.getrandbits(128) for _ in range(32)]
            vd, vs2, vs1 = (rng.randrange(32) for _ in range(3))
            with self.subTest(case=case, vd=vd, vs2=vs2, vs1=vs1):
                self.assert_execution(vd, vs2, vs1, registers)

    def test_illegal_config_has_cause_two_and_no_input_changes(self):
        overrides = [{"vl": value} for value in (0, 1, 7, 9, 16)]
        overrides += [{"vstart": value} for value in (1, 7, 8, 16)]
        overrides += [{"vs": 0}, {"vector_enabled": False}]
        overrides += [{"vtype": 1 << bit} for bit in range(64) if bit not in (6, 7)]
        for override in overrides:
            with self.subTest(config=override):
                registers = self.make_registers()
                before = registers[:]
                config, config_before = None, None
                with self.assertRaises(dut.IllegalInstruction) as caught:
                    config = dut.VectorConfig(**override)
                    config_before = asdict(config)
                    dut.execute(dut.encode(10, 8, 9), registers, config)
                self.assertEqual(caught.exception.cause, 2)
                self.assertEqual(registers, before)
                if config_before is not None:
                    self.assertEqual(asdict(config), config_before)

    def test_illegal_encoding_preserves_inputs(self):
        for word in (0, MATCH ^ (1 << 25), MATCH ^ (1 << 26), MATCH ^ (1 << 12)):
            with self.subTest(word=hex(word)):
                registers = self.make_registers()
                before = registers[:]
                config = dut.VectorConfig(vs=1, vxrm=3, vxsat=1)
                config_before = asdict(config)
                with self.assertRaises(dut.IllegalInstruction) as caught:
                    dut.execute(word, registers, config)
                self.assertEqual(caught.exception.cause, 2)
                self.assertEqual(registers, before)
                self.assertEqual(asdict(config), config_before)

    def test_other_vlen_is_unsupported_configuration(self):
        for vlen in (64, 256, 512):
            with self.subTest(vlen=vlen):
                registers = self.make_registers()
                before = registers[:]
                with self.assertRaises(dut.UnsupportedConfiguration):
                    config = dut.VectorConfig(vlen_bits=vlen)
                    dut.execute(dut.encode(10, 8, 9), registers, config)
                self.assertEqual(registers, before)


class InvalidApiTests(unittest.TestCase):
    def test_lane_inputs_require_exact_length_and_signed_integers(self):
        invalid_vectors = (None, True, 8, 8.0, "12345678", [], [0] * 7, [0] * 9)
        invalid_values = (-129, 128, True, False, 1.0, "1", None)
        for vector in invalid_vectors:
            with self.subTest(vector=repr(vector)):
                with self.assertRaises(ValueError):
                    dut.dot_s8(vector, [0] * 8)
                with self.assertRaises(ValueError):
                    dut.dot_s8([0] * 8, vector)
                with self.assertRaises(ValueError):
                    dut.pack_lanes(vector)
        for value in invalid_values:
            vector = [0] * 8
            vector[3] = value
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    dut.dot_s8(vector, [1] * 8)
                with self.assertRaises(ValueError):
                    dut.dot_s8([1] * 8, vector)
                with self.assertRaises(ValueError):
                    dut.pack_lanes(vector)

    def test_packed_sources_and_high_half_require_unsigned_integer_domains(self):
        for invalid in (-1, 1 << 128, True, False, 1.0, "1", None):
            with self.subTest(source=repr(invalid)):
                with self.assertRaises(ValueError):
                    dut.vdot(invalid, 0)
                with self.assertRaises(ValueError):
                    dut.vdot(0, invalid)
        for invalid in (-1, 1 << 64, True, False, 1.0, "1", None):
            with self.subTest(high64=repr(invalid)):
                with self.assertRaises(ValueError):
                    dut.pack_lanes([0] * 8, high64=invalid)

    def test_instruction_input_ranges_and_types(self):
        for invalid in (-1, 32, True, False, 1.0, "1", None):
            for position in range(3):
                fields = [10, 8, 9]
                fields[position] = invalid
                with self.subTest(field=position, value=repr(invalid)):
                    with self.assertRaises(ValueError):
                        dut.encode(*fields)
                    with self.assertRaises(ValueError):
                        dut.Instruction(*fields)
        for invalid in (-1, 1 << 32, True, False, 1.0, "1", None):
            with self.subTest(word=repr(invalid)):
                with self.assertRaises(ValueError):
                    dut.decode(invalid)
                with self.assertRaises(ValueError):
                    dut.execute(invalid, [0] * 32)

    def test_register_bank_domains(self):
        for invalid in (None, True, 32, "0" * 32, [], [0] * 31, [0] * 33):
            with self.subTest(bank=repr(invalid)):
                with self.assertRaises(ValueError):
                    dut.execute(MATCH, invalid)
        for value in (-1, 1 << 128, True, False, 1.0, "1", None):
            registers = [0] * 32
            registers[20] = value  # Reject even an otherwise unused malformed slot.
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    dut.execute(MATCH, registers)

    def test_config_api_types_and_small_field_ranges(self):
        numeric_fields = ("vlen_bits", "vl", "vtype", "vstart", "vs", "vxrm", "vxsat")
        invalid_overrides = []
        for field in numeric_fields:
            invalid_overrides.extend({field: value} for value in (True, False, 1.0, "1", None))
        for field in ("vl", "vtype", "vstart"):
            invalid_overrides.extend({field: value} for value in (-1, 1 << 64))
        invalid_overrides.extend(({"vlen_bits": 0}, {"vlen_bits": 65537}))
        invalid_overrides.extend({"vector_enabled": value} for value in (0, 1, 1.0, "true", None))
        invalid_overrides.extend(({"vs": 4}, {"vs": -1}, {"vxrm": 4},
                                  {"vxrm": -1}, {"vxsat": 2}, {"vxsat": -1}))
        for override in invalid_overrides:
            with self.subTest(config=override):
                with self.assertRaises(ValueError):
                    config = dut.VectorConfig(**override)
                    dut.execute(MATCH, [0] * 32, config)
        for invalid in (None, True, 0, {}, "config"):
            with self.subTest(config=repr(invalid)):
                with self.assertRaises(ValueError):
                    dut.execute(MATCH, [0] * 32, invalid)


if __name__ == "__main__":
    unittest.main()
