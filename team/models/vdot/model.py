"""Independent integer oracle for the draft vdot-s8x8-r32-v0.1 contract.

This module models values, encoding and a small vector-state transition only.
It is not an implementation of NEMU, a CPU, a trap handler or RTL timing.
All arithmetic is Python exact-integer arithmetic; no RTL adder tree is reused.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace


CONTRACT_ID = "vdot-s8x8-r32-v0.1"
INPUT_BITS = 8
PAIRS = 8
RESULT_BITS = 32
RESULT_LO = 0
VLEN_BITS = 128
MATCH_VDOT = 0x0200000B
MASK_VDOT = 0xFE00707F


class IllegalInstruction(Exception):
    """The vdot-only model rejects this encoding or architectural state."""

    cause = 2


class UnsupportedConfiguration(ValueError):
    """A machine configuration is outside this oracle's supported domain."""


def _integer(value: int, name: str, low: int, high: int) -> int:
    # bool is an int subclass, but silently accepting it hides malformed input.
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _sequence(values: Sequence[int], size: int, name: str) -> tuple[int, ...]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of {size} integers")
    if len(values) != size:
        raise ValueError(f"{name} must contain exactly {size} integers")
    return tuple(values)


def _lanes(values: Sequence[int], name: str) -> tuple[int, ...]:
    lanes = _sequence(values, PAIRS, name)
    for i, value in enumerate(lanes):
        _integer(value, f"{name}[{i}]", -(1 << (INPUT_BITS - 1)), (1 << (INPUT_BITS - 1)) - 1)
    return lanes


def dot_s8(a: Sequence[int], b: Sequence[int]) -> int:
    """Return the exact signed dot product of exactly eight signed int8s."""
    a = _lanes(a, "a")
    b = _lanes(b, "b")
    return sum(x * y for x, y in zip(a, b))


def pack_lanes(values: Sequence[int], high64: int = 0) -> int:
    """Pack signed lanes 0..7 into low bytes, plus an unsigned high half."""
    values = _lanes(values, "values")
    _integer(high64, "high64", 0, (1 << 64) - 1)
    packed = high64 << 64
    for i, value in enumerate(values):
        packed |= (value & 0xFF) << (INPUT_BITS * i)
    return packed


def _unpack_source(value: int, name: str) -> tuple[int, ...]:
    _integer(value, name, 0, (1 << VLEN_BITS) - 1)
    unsigned = tuple((value >> (INPUT_BITS * i)) & 0xFF for i in range(PAIRS))
    return tuple(x if x < 128 else x - 256 for x in unsigned)


def _source_sum(vs1: int, vs2: int) -> int:
    return dot_s8(_unpack_source(vs1, "vs1"), _unpack_source(vs2, "vs2"))


def vdot(vs1: int, vs2: int) -> int:
    """Return a full unsigned 128-bit destination (upper 96 bits are zero)."""
    return _source_sum(vs1, vs2) & ((1 << RESULT_BITS) - 1)


@dataclass(frozen=True)
class Instruction:
    vd: int
    vs2: int
    vs1: int

    def __post_init__(self) -> None:
        for name in ("vd", "vs2", "vs1"):
            _integer(getattr(self, name), name, 0, 31)


def encode(vd: int, vs2: int, vs1: int) -> int:
    """Use assembly operand order: vdot.vv vd, vs2, vs1."""
    inst = Instruction(vd, vs2, vs1)
    return MATCH_VDOT | (inst.vs2 << 20) | (inst.vs1 << 15) | (inst.vd << 7)


def decode(word: int) -> Instruction:
    """Reject non-vdot encodings; this is not a general RISC-V decoder."""
    _integer(word, "word", 0, (1 << 32) - 1)
    if word & MASK_VDOT != MATCH_VDOT:
        raise IllegalInstruction(f"not a {CONTRACT_ID} encoding: 0x{word:08x}")
    return Instruction(vd=(word >> 7) & 31, vs2=(word >> 20) & 31, vs1=(word >> 15) & 31)


@dataclass(frozen=True)
class VectorConfig:
    """Relevant input state; vtype is its raw RV64 CSR value, VS is 0..3.

    Accept structurally valid but unsupported states so rejection can be tested.
    vcsr is derived from vxrm/vxsat rather than independently mutable state.
    """

    vlen_bits: int = VLEN_BITS
    vl: int = PAIRS
    vtype: int = 0
    vstart: int = 0
    vs: int = 3
    vxrm: int = 0
    vxsat: int = 0
    vector_enabled: bool = True

    def __post_init__(self) -> None:
        _integer(self.vlen_bits, "vlen_bits", 1, 65536)
        for name in ("vl", "vtype", "vstart"):
            _integer(getattr(self, name), name, 0, (1 << 64) - 1)
        _integer(self.vs, "vs", 0, 3)
        _integer(self.vxrm, "vxrm", 0, 3)
        _integer(self.vxsat, "vxsat", 0, 1)
        if type(self.vector_enabled) is not bool:
            raise ValueError("vector_enabled must be a bool")

    @property
    def vcsr(self) -> int:
        return (self.vxrm << 1) | self.vxsat

    @property
    def vta(self) -> int:
        return (self.vtype >> 6) & 1

    @property
    def vma(self) -> int:
        return (self.vtype >> 7) & 1


def _check_config(config: VectorConfig) -> None:
    if not isinstance(config, VectorConfig):
        raise ValueError("config must be a VectorConfig")
    if config.vlen_bits != VLEN_BITS:
        raise UnsupportedConfiguration(f"VLEN={config.vlen_bits}; this oracle requires VLEN=128")
    if not config.vector_enabled or config.vs == 0:
        raise IllegalInstruction("vector state is disabled")
    # e8/m1/vill=0 and no reserved bits: only vta/vma may be set.
    if config.vtype & ~0xC0:
        raise IllegalInstruction(f"unsupported vtype: 0x{config.vtype:016x}")
    if config.vl != PAIRS:
        raise IllegalInstruction(f"unsupported vl: {config.vl}; expected 8")
    if config.vstart != 0:
        raise IllegalInstruction(f"unsupported vstart: {config.vstart}; expected 0")


@dataclass(frozen=True)
class ExecutionResult:
    registers: tuple[int, ...]
    config: VectorConfig
    signed_sum: int


def execute(
    word: int,
    registers: Sequence[int],
    config: VectorConfig = VectorConfig(),
) -> ExecutionResult:
    """Pure vector-state adapter: snapshot sources, replace one destination.

    No caller state is mutated, including on errors. Exceptions here describe
    the oracle's rejection, not an implemented architectural trap mechanism.
    Check ordering does not specify full-CPU exception priority.
    """
    _check_config(config)
    before = _sequence(registers, 32, "registers")
    for i, value in enumerate(before):
        _integer(value, f"registers[{i}]", 0, (1 << VLEN_BITS) - 1)
    inst = decode(word)
    total = _source_sum(before[inst.vs1], before[inst.vs2])
    after = list(before)
    after[inst.vd] = total & ((1 << RESULT_BITS) - 1)
    return ExecutionResult(tuple(after), replace(config, vs=3), total)
