"""Exact-integer oracle for T15 standalone parameter experiments, not an ISA."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Parameters:
    element_bits: int
    pairs: int
    result_bits: int
    register_bits: int = 128

    def __post_init__(self):
        fields = (self.element_bits, self.pairs, self.result_bits, self.register_bits)
        if any(type(v) is not int for v in fields):
            raise ValueError("parameters must be integers, not bool")
        if self.element_bits not in (8, 16):
            raise ValueError("element_bits must be 8 or 16")
        if self.pairs < 1 or self.pairs & (self.pairs - 1):
            raise ValueError("pairs must be a positive power of two")
        if self.register_bits != 128 or self.element_bits * self.pairs > self.register_bits:
            raise ValueError("input must fit the 128-bit container")
        if not self.required_bits <= self.result_bits <= self.register_bits:
            raise ValueError("result field cannot represent the exact range")

    @property
    def limits(self):
        low = -(2 ** (self.element_bits - 1))
        high = -low - 1
        return self.pairs * low * high, self.pairs * low * low

    @property
    def required_bits(self):
        low, high = self.limits
        return max((~low).bit_length() + 1, high.bit_length() + 1)


BASELINE = Parameters(8, 8, 32)
EXTENSION = Parameters(16, 8, 64)
PROFILES = {"s8x8": BASELINE, "s16x8": EXTENSION}


def register(value):
    if type(value) is not int or not 0 <= value < 2 ** 128:
        raise ValueError("source must be an unsigned 128-bit integer")
    return value


def lanes(source, p):
    raw = register(source).to_bytes(16, "little")
    size = p.element_bits // 8
    return tuple(int.from_bytes(raw[i * size:(i + 1) * size], "little", signed=True)
                 for i in range(p.pairs))


def exact_sum(vs1, vs2, p):
    return sum(a * b for a, b in zip(lanes(vs1, p), lanes(vs2, p)))


def result(vs1, vs2, p):
    return exact_sum(vs1, vs2, p) % (2 ** p.result_bits)


def pack(values, p, padding=0):
    values = tuple(values)
    if len(values) != p.pairs:
        raise ValueError("wrong lane count")
    bound = 2 ** (p.element_bits - 1)
    if any(type(x) is not int or not -bound <= x < bound for x in values):
        raise ValueError("lane out of signed range")
    unused = p.register_bits - p.element_bits * p.pairs
    if type(padding) is not int or not 0 <= padding < 2 ** unused:
        raise ValueError("invalid padding")
    raw = b"".join(x.to_bytes(p.element_bits // 8, "little", signed=True) for x in values)
    return int.from_bytes(raw, "little") | (padding << (p.element_bits * p.pairs))
