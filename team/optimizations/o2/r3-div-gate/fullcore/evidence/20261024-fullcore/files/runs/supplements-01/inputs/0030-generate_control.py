"""New O2 speculation / writeback-competition corpus; frozen F2v is untouched."""
import argparse
import hashlib
import json
from pathlib import Path
import generate

TRIALS=256

def emit(out):
    out.mkdir(parents=True,exist_ok=False)
    asm=[".option norvc",".text"]
    initial=generate.initial()
    header=["#include <stdint.h>"]
    # Every group has one static conditional PC exercised 16 times, with
    # deterministic irregular outcomes; the branch depends on scalar divide.
    expected=[]
    trials=[]
    groups=[]
    for group in range(16):
        burst=group+1
        extra_gap=group%4
        rows=[]
        group_expected=[]
        for n in range(16):
            h=hashlib.sha256(f"O2-control-20261019:{group}:{n}".encode()).digest()
            numerator=int.from_bytes(h[:8],"little") | (1<<63)
            divisor=int.from_bytes(h[8:16],"little")%(1<<31)+3
            execute=(h[16]&1)==0
            rows.append([numerator,divisor,numerator//divisor if execute else (numerator//divisor)^1])
            regs=[r[:] for r in initial]
            regs[28]=list(bytes.fromhex("00006040")*4)
            regs[19][:8]=[255 if y==0 else x//y for x,y in zip(regs[8][:8],regs[9][:8])]
            regs[16]=generate.dot(regs[8],regs[9])
            if execute:
                for d in range(20,28):
                    regs[d]=generate.dot(regs[8],regs[9])
            group_expected.append(regs)
        trials+=rows
        expected+=group_expected
        asm.extend([".balign 64",f".global o2_control_{group}",f"o2_control_{group}:",
                    "li t6,16","li t5,0",f".Lo2_try_{group}:","mv t4,a0",
                    "vsetivli zero,16,e8,m1,tu,mu"])
        for reg in range(32):
            asm.extend([f"vl1re8.v v{reg},(t4)","addi t4,t4,16"])
        asm.extend(["li t0,0x40e00000","fmv.w.x ft0,t0","li t0,0x40000000","fmv.w.x ft2,t0",
                    "fdiv.s ft1,ft0,ft2","vsetivli zero,4,e32,m1,tu,mu"])
        asm.extend(["vfmv.v.f v28,ft1"]*burst)
        asm.extend(["vsetivli zero,8,e8,m1,tu,mu","ld t0,0(a2)","ld t1,8(a2)","ld t3,16(a2)",
                    "vdivu.vv v19,v8,v9",f".word 0x{generate.word(16,8,9):08x}",
                    "divu t2,t0,t1",f"bne t2,t3,.Lo2_skip_{group}"])
        asm.extend(["addi t5,t5,1"]*extra_gap)
        for reg in range(20,28):
            asm.append(f".word 0x{generate.word(reg,8,9):08x}")
        asm.append(f".Lo2_skip_{group}:")
        for reg in range(32):
            asm.extend([f"vs1r.v v{reg},(a1)","addi a1,a1,16"])
        asm.extend(["addi a2,a2,24","addi t6,t6,-1",f"bnez t6,.Lo2_try_{group}","fence rw,rw","ret",f".global o2_control_{group}_end",f"o2_control_{group}_end:"])
        header.append(f"extern void o2_control_{group}(const void*,void*,const void*);")
        groups.append(dict(id=group,burst=burst,decode_gap=extra_gap,trials=16,
                           expected_vdot_commits=16+8*sum(a//b==c for a,b,c in rows)))
    header += ["#define O2_CONTROL_GROUPS 16",
               "static void (*const entries[16])(const void*,void*,const void*) = {"+",".join(f"o2_control_{i}" for i in range(16))+"};",
               "static const uint8_t input[32][16] = "+generate.c_array(initial)+";",
               "static const uint64_t trials[256][3] = {"+",".join("{"+",".join(f"UINT64_C({x})" for x in r)+"}" for r in trials)+"};",
               "static const uint8_t expected[16][16][32][16] = "+generate.c_array([expected[g*16:(g+1)*16] for g in range(16)])+";"]
    (out/"kernels.S").write_text("\n".join(asm)+"\n")
    (out/"cases.h").write_text("\n".join(header)+"\n")
    manifest=dict(schema=1,contract="vdot-s8x8-r32-v0.1",purpose="O2 G3 targeted control, not a replacement for frozen F2v",
                  trials=TRIALS,groups=groups,whole_vector_bytes_checked=TRIALS*512,
                  expected_vdot_commits=sum(g["expected_vdot_commits"] for g in groups),
                  generated_sha256={n:generate.digest(out/n) for n in ["kernels.S","cases.h"]},
                  requested_observation_coverage=["FULL_STALL","KILL_P","KILL_R","PARTIAL_KILL"],
                  coverage_claim="pending actual O2 full-core observations",performance_measured=False)
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    manifest=emit(parser.parse_args().output)
    print(json.dumps(dict(status="O2_CONTROL_GENERATED",expected_vdot_commits=manifest["expected_vdot_commits"])))
