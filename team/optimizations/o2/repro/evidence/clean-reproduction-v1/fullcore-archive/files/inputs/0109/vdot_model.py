"""Independent integer oracle and candidate-contract state model (not NEMU)."""

from dataclasses import dataclass, replace

CONTRACT_ID = "vdot-s8x8-r32-v0.1"
MODEL_VERSION = "1.0.0"
MATCH = 0x0200000B
MASK = 0xFE00707F
VLEN = 128
PAIRS = 8


class NotVdot(ValueError):
    """A nonmatching word may belong to another instruction; do not trap it here."""


def unsigned(value: int, bits: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < (1 << bits):
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")
    return value


def encode(vd: int, vs1: int, vs2: int) -> int:
    for name, reg in (("vd", vd), ("vs1", vs1), ("vs2", vs2)):
        unsigned(reg, 5, name)
    return MATCH | (vd << 7) | (vs1 << 15) | (vs2 << 20)


def decode(word: int) -> tuple[int, int, int]:
    unsigned(word, 32, "instruction")
    if word & MASK != MATCH:
        raise NotVdot(f"0x{word:08x} is not this vdot encoding")
    return (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31


def dot_s8(a, b) -> int:
    """Use mathematical integers, with no hardware intermediate truncation."""
    if len(a) != PAIRS or len(b) != PAIRS:
        raise ValueError("exactly eight signed int8 elements per source required")
    if any(type(x) is not int or not -128 <= x <= 127 for x in (*a, *b)):
        raise ValueError("source elements must be signed int8 integers")
    return sum(x * y for x, y in zip(a, b))


def result128(src1: int, src2: int) -> int:
    sources = [unsigned(s, VLEN, "source").to_bytes(16, "little") for s in (src1, src2)]
    signed = [[int.from_bytes(bytes([x]), "little", signed=True) for x in s[:8]]
              for s in sources]
    return dot_s8(*signed) & 0xFFFFFFFF


@dataclass(frozen=True)
class VectorState:
    regs: tuple[int, ...] = (0,) * 32
    pc: int = 0x80000000
    vl: int = 8
    vtype: int = 0
    vstart: int = 0
    vxrm: int = 0
    vxsat: int = 0
    vs: int = 1
    vlen: int = VLEN

    def __post_init__(self):
        if type(self.regs) is not tuple or len(self.regs) != 32:
            raise ValueError("32 immutable vector-register values required")
        for reg in self.regs:
            unsigned(reg, 128, "register")
        for name in ("pc", "vl", "vtype", "vstart"):
            unsigned(getattr(self, name), 64, name)
        unsigned(self.vxrm, 2, "vxrm")
        unsigned(self.vxsat, 1, "vxsat")
        unsigned(self.vs, 2, "VS")
        if self.vlen != VLEN:
            raise ValueError("build configuration must have VLEN=128")

    @property
    def vcsr(self):
        return (self.vxrm << 1) | self.vxsat


def illegal_reasons(state: VectorState) -> tuple[str, ...]:
    reasons = []
    if state.vs == 0:
        reasons.append("VS_OFF")
    if state.vtype >> 63:
        reasons.append("VILL")
    if state.vtype & 0x7FFFFFFFFFFFFF00:
        reasons.append("RESERVED_VTYPE")
    if (state.vtype >> 3) & 7:
        reasons.append("SEW")
    if state.vtype & 7:
        reasons.append("LMUL")
    if state.vl != PAIRS:
        reasons.append("VL")
    if state.vstart:
        reasons.append("VSTART")
    return tuple(reasons)


@dataclass(frozen=True)
class Outcome:
    state: VectorState
    cause: int | None = None
    fault_pc: int | None = None
    reasons: tuple[str, ...] = ()


def execute(word: int, state: VectorState) -> Outcome:
    vd, vs1, vs2 = decode(word)
    reasons = illegal_reasons(state)
    if reasons:
        # This models the instruction boundary only, not privilege trap entry.
        return Outcome(state, 2, state.pc, reasons)
    regs = list(state.regs)
    regs[vd] = result128(state.regs[vs1], state.regs[vs2])
    return Outcome(replace(state, regs=tuple(regs), pc=(state.pc + 4) & ((1 << 64) - 1), vs=3))
