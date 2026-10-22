#!/usr/bin/env python3
"""Check real frozen O3 renderer integration; compile objects, not runnable EMU images."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import candidate
import screen


def run(repo, output, clang="clang"):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    candidate.require(not output.exists(), "output must be new")
    compiler = shutil.which(clang)
    candidate.require(compiler is not None, "Clang required")
    output.mkdir(parents=True, exist_ok=False)
    base, audit = candidate.load_base(repo), screen.audit_module(repo)
    records, controls, metadata = [], {}, {}
    for dataset in range(3):
        for shard in (4, 5, 6, 7):
            for variant in ("s0", "s2"):
                target = output / f"{variant}-d{dataset}-s{shard}"
                value = candidate.generate(repo, target, variant, dataset, shard, "performance")
                commands = []
                (target / "abi.c").write_text('#include "cases.h"\n_Static_assert(sizeof(cases[0].expected[0]) == 16, "output width");\nunsigned plan_count(void) { return T13_PLAN_COUNT; }\n')
                for source in ("kernels.S", "abi.c"):
                    command = [compiler, "--target=riscv64", "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-ffreestanding", "-c", str(target/source), "-o", str(target/(source+".o"))]
                    done = subprocess.run(command, capture_output=True, text=True, timeout=45)
                    commands.append(dict(command=command, exit_code=done.returncode, stdout=done.stdout, stderr=done.stderr))
                    (target / "compile.json").write_text(json.dumps(commands, indent=2)+"\n")
                    candidate.require(done.returncode==0, "object compilation failed: "+done.stderr)
                funcs = audit.elf_functions((target/"kernels.S.o").read_bytes())
                verified = []
                for i,row in enumerate(value["rows"]):
                    addr,code = funcs[f"t13_kernel_{i}"]
                    info = audit.audit_kernel(code,addr)
                    candidate.require(info["counts"]==audit.source_counts(row["body"]), "wrapper/body count mismatch")
                    candidate.require(info["counts"].get("vdot.vv",0)==(row["dots"] if row["method"]=="vdot" else 0), "custom count metadata mismatch")
                    key=(dataset,shard,i)
                    if variant=="s0":
                        controls[key]=code
                        metadata[key]=row
                    else:
                        old=metadata[key]
                        for field in ("before","expected","outputs","stream","scratch","iterations","vtype","id"):
                            candidate.require(old[field]==row[field], "golden input or ABI changed")
                        if row["method"]=="rvv" or value["k"]!=13:
                            candidate.require(code==controls[key], "unaffected full function changed")
                    verified.append(dict(id=row["id"],function_sha256=hashlib.sha256(code).hexdigest(),body_sha256=info["body_sha256"],
                                         body_instructions=info["body_instructions"],marker_span_instructions=info["marker_span_instructions"],dots=row["dots"]))
                records.append(dict(id=target.name,source_files=value["files"],kernels=verified))
    report=dict(status="R2_S2_RENDERER_AND_OBJECTS_PASS_NOT_LINKED_NOT_EXECUTED",source_base=candidate.BASE,
                source_sets=len(records),kernel_functions=sum(len(r["kernels"]) for r in records),
                generated_c_abi_objects=len(records),runnable_benchmark_elfs=0,new_emu_runs=0,performance_measured=False,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),inputs=candidate.PINS,records=records)
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    p.add_argument("--clang",default="clang")
    a=p.parse_args()
    try:r=run(a.repo,a.output,a.clang)
    except (ValueError,OSError,subprocess.SubprocessError) as exc:p.exit(2,f"R2_INTEGRATION_REJECTED: {exc}\n")
    print(json.dumps({k:r[k] for k in ("status","source_sets","kernel_functions","runnable_benchmark_elfs","new_emu_runs")}))
