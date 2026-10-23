"""Limited architectural interpreter for compiled, straight-line O3/S2 bodies.

Not NEMU, a CPU simulator, or a cycle model. Unknown encodings fail closed.
Bounds are checked per A row and x, not merely against a padded allocation.
"""
from __future__ import annotations
from collections import Counter
import random
import struct

MASK64 = (1 << 64) - 1

def require(ok, message):
    if not ok:
        raise ValueError(message)

def signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value

class Machine:
    def __init__(self, matrix, vector, poison_seed=0):
        self.m, self.k = len(matrix), len(vector)
        require(self.m > 0 and self.k > 0 and all(len(r) == self.k for r in matrix), "shape")
        require(all(type(v) is int and -128 <= v < 128 for row in [*matrix, vector] for v in row), "int8")
        self.memory = bytes(v & 255 for row in [*matrix, vector] for v in row)
        self.x = [0] * 32
        self.x[12], self.x[13] = 0x1000, 0x2000
        rng = random.Random(poison_seed)
        self.v = [bytearray(rng.getrandbits(8) for _ in range(16)) for _ in range(32)]
        self.before = [bytes(r) for r in self.v]
        self.output = bytearray([0xa6] * (16 * self.m))
        self.vl, self.sew, self.lmul, self.ta, self.ma = 8, 8, 1, 0, 0
        self.vstart, self.vcsr = 0, 7
        self.counts, self.reads, self.stores = Counter(), [], []
        self.tail_dot_operands = []

    def write_x(self, rd, value):
        require(rd in (0, 5, 6, 7, 28, 29, 30, 31), "unexpected scalar register write")
        if rd:
            self.x[rd] = value & MASK64

    def read(self, address, size):
        offset = address - 0x1000
        require(0 <= offset and size > 0 and offset + size <= len(self.memory), "input allocation over-read")
        require(offset // self.k == (offset + size - 1) // self.k, "read crosses compact row/x boundary")
        self.reads.append((offset, size))
        return self.memory[offset:offset + size]

    def get(self, reg, nbytes):
        require(0 <= reg < 32 and reg * 16 + nbytes <= 512, "vector group")
        return b"".join(bytes(r) for r in self.v[reg:])[:nbytes]

    def put(self, reg, data, capacity):
        require(len(data) <= capacity and capacity % 16 == 0 and reg + capacity // 16 <= 32, "vector write size")
        previous = self.get(reg, capacity)
        new = data + (bytes([255]) * (capacity - len(data)) if self.ta else previous[len(data):])
        for i in range(capacity // 16):
            self.v[reg + i][:] = new[16 * i:16 * (i + 1)]

    def execute(self, code):
        require(len(code) % 4 == 0 and len(code) > 0, "fixed-width body required")
        for word, in struct.iter_unpack("<I", code):
            op, f3, f7, f6 = word & 127, (word >> 12) & 7, word >> 25, word >> 26
            rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
            imm = signed(word >> 20, 12)
            name = None
            if word & 0xfe00707f == 0x0200000b:
                require((self.vl, self.sew, self.lmul, self.vstart) == (8, 8, 1, 0), "illegal dot8 configuration")
                left, right = self.get(a, 8), self.get(b, 8)
                self.tail_dot_operands.append((left.hex(), right.hex()))
                val = sum(signed(x, 8) * signed(y, 8) for x, y in zip(left, right))
                self.v[rd][:] = (val & 0xffffffff).to_bytes(4, "little") + bytes(12)
                name = "vdot.vv"
            elif op == 0x13 and f3 == 0:
                self.write_x(rd, self.x[a] + imm); name = "addi"
            elif op == 3 and f3 == 0:
                self.write_x(rd, signed(self.read(self.x[a] + imm, 1)[0], 8)); name = "lb"
            elif op == 0x3b and f3 == 0 and f7 in (0, 1):
                value = self.x[a] * self.x[b] if f7 else self.x[a] + self.x[b]
                self.write_x(rd, signed(value, 32)); name = "mulw" if f7 else "addw"
            elif op == 0x73 and f3 == 5 and rd == 0 and word >> 20 in (8, 15):
                if word >> 20 == 8:
                    self.vstart = a
                else:
                    self.vcsr = a & 7
                name = "csrwi"
            elif op == 0x57 and f3 == 7 and word >> 30 == 3:
                vt = (word >> 20) & 1023
                require(vt & ~0xff == 0 and (vt & 7) in (0, 1), "unsupported vtype")
                self.sew, self.lmul = 8 << ((vt >> 3) & 7), 1 << (vt & 7)
                require(self.sew in (8, 16, 32) and a <= 128 * self.lmul // self.sew, "AVL outside checked model")
                self.vl, self.ta, self.ma, self.vstart = a, (vt >> 6) & 1, (vt >> 7) & 1, 0
                self.write_x(rd, self.vl); name = "vsetivli"
            elif op == 7 and word & 0xfff0707f == 0x02000007:
                require((self.sew, self.lmul, self.vstart) == (8, 1, 0), "load mode")
                self.put(rd, self.read(self.x[a], self.vl), 16); name = "vle8.v"
            elif op == 0x27 and word & 0xfff0707f == 0x02800027:
                off = self.x[a] - 0x2000
                require(0 <= off and off % 16 == 0 and off + 16 <= len(self.output), "output overrun")
                require(off not in self.stores, "duplicate output store")
                self.output[off:off + 16] = self.v[rd]
                self.stores.append(off); name = "vs1r.v"
            elif op == 0x57 and (word >> 25) & 1:
                require(self.vstart == 0, "nonzero vstart unsupported")
                if (f6, f3) == (0x17, 3) and b == 0:
                    val = (signed(a, 5) & ((1 << self.sew) - 1)).to_bytes(self.sew // 8, "little")
                    self.put(rd, val * self.vl, 16 * self.lmul); name = "vmv.v.i"
                elif (f6, f3) == (0x10, 2) and a == 0:
                    self.write_x(rd, signed(int.from_bytes(self.get(b, self.sew // 8), "little"), self.sew)); name = "vmv.x.s"
                elif (f6, f3) == (0x10, 6) and b == 0:
                    require(self.vl > 0, "empty scalar move")
                    self.put(rd, (self.x[a] & ((1 << self.sew) - 1)).to_bytes(self.sew // 8, "little"), 16)
                    name = "vmv.s.x"
                elif (f6, f3) == (0x3b, 2):
                    require((self.sew, self.lmul) == (8, 1) and rd % 2 == 0, "widen multiply mode")
                    require(a not in (rd, rd + 1) and b not in (rd, rd + 1), "unsupported overlap")
                    products = [signed(x, 8) * signed(y, 8) for x, y in zip(self.get(a, self.vl), self.get(b, self.vl))]
                    self.put(rd, b"".join((v & 65535).to_bytes(2, "little") for v in products), 32)
                    name = "vwmul.vv"
                elif (f6, f3) == (0x31, 0):
                    require((self.sew, self.lmul) == (16, 2) and b % 2 == 0, "widen reduction mode")
                    seed = signed(int.from_bytes(self.get(a, 4), "little"), 32)
                    vals = [v[0] for v in struct.iter_unpack("<h", self.get(b, self.vl * 2))]
                    self.put(rd, ((seed + sum(vals)) & 0xffffffff).to_bytes(4, "little"), 16)
                    name = "vwredsum.vs"
            require(name is not None, f"unsupported instruction 0x{word:08x}")
            self.counts[name] += 1
        return self

    def check(self, matrix, vector, stored=True):
        expected = b"".join((sum(x * y for x, y in zip(row, vector)) & 0xffffffff).to_bytes(4, "little") + bytes(12) for row in matrix)
        require(b"".join(bytes(v) for v in self.v[:self.m]) == expected, "full 128-bit output mismatch")
        require(all(bytes(self.v[i]) == self.before[i] for i in range(self.m, 16)), "protected vector clobber")
        require((self.vl, self.sew, self.lmul, self.ta, self.ma, self.vstart, self.vcsr) == (8, 8, 1, 0, 0, 0, 7), "final CSR mismatch")
        require(self.x[30] == self.m * self.k and self.x[12:14] == [0x1000, 0x2000] and self.x[0] == 0, "scalar ABI mismatch")
        if stored:
            require(self.output == expected and self.stores == list(range(0, 16 * self.m, 16)), "stored output mismatch")
        else:
            require(not self.stores, "core includes stores")
        return True
