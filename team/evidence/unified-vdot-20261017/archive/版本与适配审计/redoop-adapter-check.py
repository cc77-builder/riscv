#!/usr/bin/env python3
"""Host semantic check only; does not validate RTL or NEMU execution."""
import json
import random

def s8(n):
    return n - 256 if n & 128 else n

def reference(a, b):
    return sum(s8((a >> (8*i)) & 255) * s8((b >> (8*i)) & 255) for i in range(8)) & 0xffffffff

def native(a, b, old):
    out = 0
    for lane in range(4):
        partial = sum(s8((a >> (8*(lane*4+i))) & 255) * s8((b >> (8*(lane*4+i))) & 255) for i in range(4))
        value = (((old >> (lane*32)) & 0xffffffff) + partial) & 0xffffffff
        out |= value << (lane*32)
    return out

def adapter(regs, vd, vs1, vs2):
    # VL=4 e32: clear v2, compute all four packed partial sums.
    regs[2] = 0
    regs[2] = native(regs[vs1], regs[vs2], regs[2])
    # This clear occurs after source use, so output/input aliases are safe.
    regs[vd] = 0
    # VL=2 e32: only first two partial lanes enter the reduction.
    regs[vd] = ((regs[2] & 0xffffffff) + ((regs[2] >> 32) & 0xffffffff)) & 0xffffffff

rng = random.Random(20261017)
pairs = [(0,0), ((1<<128)-1, (1<<128)-1), (int.from_bytes(bytes([128]*16),'little'),)*2, (int.from_bytes(bytes([127]*16),'little'),int.from_bytes(bytes([128]*16),'little'))]
pairs += [(rng.getrandbits(128), rng.getrandbits(128)) for _ in range(10000)]
count = 0
for a,b in pairs:
    for vd,vs1,vs2 in [(4,1,5),(1,1,5),(5,1,5),(4,1,1),(1,1,1)]:
        regs = [rng.getrandbits(128) for _ in range(32)]
        regs[1], regs[5] = a,b
        expected = reference(regs[vs1],regs[vs2])
        before = list(regs)
        adapter(regs,vd,vs1,vs2)
        assert regs[vd] == expected
        assert all(regs[i] == before[i] for i in range(32) if i not in [vd,2])
        count += 1
print(json.dumps({'status':'REDOOP_ADAPTER_MODEL_PASS','cases':count,'input_pairs':len(pairs),'seed':20261017,'scope':'Python model only, not RTL'},indent=2))
