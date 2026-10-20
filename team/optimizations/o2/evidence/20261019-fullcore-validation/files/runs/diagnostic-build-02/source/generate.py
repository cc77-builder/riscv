"""Generate O2-A3 correctness diagnostics; unchanged fixed 128 vdots per case."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

TOTAL = 128
SEED = "o2-g3-20261019-v1"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def signed(byte):
    return byte if byte < 128 else byte - 256

def dot(a, b):
    total = sum(signed(a[i]) * signed(b[i]) for i in range(8))
    return list((total & 0xffffffff).to_bytes(4, "little")) + [0] * 12

def word(d, a, b):
    return 0x0200000b | d << 7 | a << 15 | b << 20

def initial():
    return [list(hashlib.sha256(f"{SEED}:{i}".encode()).digest()[:16]) for i in range(32)]

def c_array(data):
    if isinstance(data, list):
        return "{" + ",".join(c_array(x) for x in data) + "}"
    return str(data)

def generate(out):
    out.mkdir(parents=True, exist_ok=False)
    asm = [".option norvc", ".text"]
    cases = []
    def emit(case_id, kind, lanes, before, ops):
        index = len(cases)
        after = [x[:] for x in before]
        body = []
        counts = {"vdot": 0, "vidiv": 0, "vfdiv": 0}
        for op in ops:
            counts[op["op"]] += 1
            d, a, b = op["d"], op["a"], op["b"]
            if op["op"] == "vdot":
                if kind == "transitions":
                    body.append("vsetivli zero, 8, e8, m1, tu, mu" if not body else
                                "vsetvli zero, t2, e8, m1, tu, mu")
                body.append(f".word 0x{word(d,a,b):08x}")
                after[d] = dot(after[a], after[b])
            elif op["op"] == "vidiv":
                body.append("vsetivli zero, 4, e32, m1, tu, mu" if not body else
                            "vsetvli zero, t2, e32, m1, tu, mu")
                body.append(f"vdivu.vv v{d}, v{a}, v{b}")
                aa, bb = struct.unpack("<4I",bytes(after[a])), struct.unpack("<4I",bytes(after[b]))
                after[d] = list(struct.pack("<4I",*(x//y if y else 0xffffffff for x,y in zip(aa,bb))))
            else:
                body.append("vsetivli zero, 4, e32, m1, tu, mu" if not body else
                            "vsetvli zero, t2, e32, m1, tu, mu")
                body.append(f"vfdiv.vv v{d}, v{a}, v{b}")
                aa, bb = struct.unpack("<4f",bytes(after[a])), struct.unpack("<4f",bytes(after[b]))
                after[d] = list(struct.pack("<4f",*(x/y for x,y in zip(aa,bb))))
            # Make the next vtype/VL update depend on this exact result, ensuring
            # the next requested FU starts after the previous FU has responded.
            if kind == "transitions":
                nxt = ops[len([x for x in body if x.startswith("vmv.x.s")])+1:]
                next_vl = 8 if not nxt or nxt[0]["op"] == "vdot" else 4
                low = int.from_bytes(bytes(after[d][:4]),"little",signed=True)
                constant = (low ^ next_vl) & ((1 << 64) - 1)
                body += [f"vmv.x.s t2, v{d}", f"li t3, 0x{constant:016x}", "xor t2, t2, t3"]
        if kind == "transitions":
            # Final state has the same e8/VL8 control contract as every diagnostic.
            body.append("vsetvli zero, t2, e8, m1, tu, mu")
        asm.extend([".balign 64", f".global o2_diag_{index}",
                    f".type o2_diag_{index}, @function", f"o2_diag_{index}:",
                    "li t0, 0x6600", "csrs mstatus, t0", "csrwi vstart, 0",
                    "csrwi vcsr, 7", "csrwi fcsr, 0",
                    "vsetivli zero, 16, e8, m1, tu, mu", "mv t0, a0"])
        for reg in range(32):
            asm.extend([f"vl1re8.v v{reg}, (t0)", "addi t0, t0, 16"])
        asm.append("vsetivli zero, 8, e8, m1, tu, mu")
        asm.append(f".global o2_diag_{index}_begin")
        asm.append(f"o2_diag_{index}_begin:")
        asm.extend(body)
        asm.append(f".global o2_diag_{index}_end")
        asm.append(f"o2_diag_{index}_end:")
        asm.append("mv t0, a1")
        for reg in range(32):
            asm.extend([f"vs1r.v v{reg}, (t0)", "addi t0, t0, 16"])
        for offset, csr in enumerate(["vtype", "vl", "vstart", "vxrm", "vxsat", "vcsr", "fflags"]):
            asm.extend([f"csrr t0, {csr}", f"sd t0, {offset * 8}(a2)"])
        asm.extend(["fence rw, rw", "ret", f".size o2_diag_{index}, .-o2_diag_{index}"])
        cases.append(dict(id=case_id,kind=kind,lanes=lanes,before=before,expected=after,
                          counts=counts,ops=ops,body_instructions=body))
    for kind in ["shared-input", "distinct-input", "recurrence"]:
        for lanes in [1,2,4]:
            regs = initial()
            ops = []
            for n in range(TOTAL):
                lane = n % lanes
                d = 16 + lane
                a = d if kind == "recurrence" else (8 if kind == "shared-input" else 8 + lane * 2)
                b = 9 if kind == "shared-input" else 9 + lane * 2
                ops.append(dict(op="vdot",d=d,a=a,b=b))
            emit(f"{kind}-{lanes}",kind,lanes,regs,ops)
    regs = initial()
    regs[10] = list(struct.pack("<4I",100,10,0xffffffff,0))
    regs[11] = list(struct.pack("<4I",7,3,255,1))
    regs[12] = list(struct.pack("<4f",7.0, -6.0, 16.0, 0.5))
    regs[13] = list(struct.pack("<4f",2.0, 3.0, 4.0, 2.0))
    ops=[]
    for left in ["vdot","vidiv","vfdiv"]:
        for right in ["vdot","vidiv","vfdiv"]:
            for op in [left,right]:
                a,b={"vdot":(8,9),"vidiv":(10,11),"vfdiv":(12,13)}[op]
                ops.append(dict(op=op,d=16+len(ops)%4,a=a,b=b))
    emit("vfex4-all-pairs","transitions",0,regs,ops)
    (out/"kernels.S").write_text("\n".join(asm)+"\n")
    header = ["#ifndef O2_DIAG_CASES_H", "#define O2_DIAG_CASES_H",
              "#include <stdint.h>",
              "struct diag_case { const char *id; void (*entry)(const void *,void *,void *); unsigned dots; uint8_t before[32][16], expected[32][16]; };"]
    for i in range(len(cases)):
        header.append(f"extern void o2_diag_{i}(const void *, void *, void *);")
    header.append(f"#define O2_DIAG_CASES {len(cases)}")
    header.append("static const struct diag_case cases[O2_DIAG_CASES] = {")
    for i,c in enumerate(cases):
        header.append('{'+f'"{c["id"]}", o2_diag_{i}, {c["counts"]["vdot"]},'+c_array(c["before"])+","+c_array(c["expected"])+"},")
    header.extend(["};","#endif"])
    (out/"cases.h").write_text("\n".join(header)+"\n")
    manifest=dict(schema=1,seed=SEED,contract="vdot-s8x8-r32-v0.1",fixed_dots=TOTAL,
                  diagnostic_only=True,performance_measured=False,
                  expected_vdot_commits=sum(c["counts"]["vdot"] for c in cases),
                  cases=cases,generated_sha256={name:digest(out/name) for name in ["kernels.S","cases.h"]})
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=generate(args.output)
    print(f'O2_DIAG_GENERATED cases={len(result["cases"])} vdot_commits={result["expected_vdot_commits"]}')
