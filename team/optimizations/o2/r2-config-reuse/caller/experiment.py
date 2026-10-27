"""Build/run the separate 8x32 C consumer without changing qualified inputs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
import runtime_experiment as parent
import runtime_gate as g
sys.path.insert(0, str(HERE))
import pathcheck

CONTRACT = "r2-s3-caller-8x32-v2"
MAX_CYCLES = 3000000
REL = Path("team/optimizations/o2/r2-config-reuse/caller")
LIB = REL.parent / "evidence/runtime-v1/library"
OBJECT_SHA = "f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3"
PUBLIC_SHA = {"gemv.S":"9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2",
              "gemv.h":"d6cbdadb8ed601e1ccd4d308970111588c5fe7e10098b821625630e2b5360be9"}
PHASES = ("full", "pack", "core", "extract")
OWN = ("caller.h", "caller.c", "demo.c", "main.c", "experiment.py", "pathcheck.py", "check.py", "CONTRACT.md")
GENERATED = ("caller.h","caller.c","demo.c","main.c","gemv.S","gemv.h","data.h","timers.S","Makefile","manifest.json")
PUBLIC_LEAVES = tuple("config_reuse_gemv_"+shape+"_"+variant+"_"+method
    for shape in ("4x8","8x32","16x64","4x13") for variant in ("basic","reuse") for method in ("vdot","rvv"))
AM_COMMIT = "086a238062fdfb3281b745a537b361983d0154b5"
TOOL_NAMES = ("gcc","objdump","ld","ar","objcopy","readelf","make")
C_REQUIRED = ("-std=gnu11","-march=rv64gv","-mabi=lp64d","-O2","-ffreestanding","-fno-lto",
    "-fno-tree-vectorize","-fno-tree-slp-vectorize","-fno-tree-loop-distribute-patterns",
    "-fno-ipa-cp","-fno-ipa-icf","-fno-optimize-sibling-calls","-mno-relax")

def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def digest(raw): return hashlib.sha256(raw).hexdigest()

def sources(repo):
    g.require(repo == ROOT and HERE == repo / REL, "caller source root")
    g.bind(repo)
    for name, sha in PUBLIC_SHA.items(): g.require(g.sha(repo / REL.parent / "public" / name)==sha, "qualified public source drift")
    g.require(g.sha(repo / LIB / "gemv.o")==OBJECT_SHA, "qualified complete object drift")
    paths = set(g.SOURCES) | set(g.FROZEN) | {str(REL/n) for n in OWN}
    paths |= {str(parent.REPRO/n) for n in parent.t17.ADAPTERS}
    paths |= {str(parent.REPRO / "clean_profile.py"), "team/workloads/unified-vdot/check.py",
              "team/optimizations/o2/r2-select/entry_c_api.py", "team/optimizations/o2/fullcore/analyze.py",
              "team/optimizations/o2/fullcore/recheck.py", "team/optimizations/o2/fullcore/run_suite.py",
              "team/optimizations/o1/audit/runtime_gate.py"}
    paths |= {str(REL.parent / "public" / n) for n in PUBLIC_SHA}
    return {p:g.sha(repo/p) for p in sorted(paths)}

def timer_source():
    lines=[".option norvc", ".option norelax", ".text"]
    for i,phase in enumerate(PHASES):
        name="caller_measure_"+str(i)
        lines += [".balign 64",f".global {name}",f".type {name}, @function",name+":",
                  "  addi sp, sp, -48", "  sd ra, 0(sp)", "  sd s0, 8(sp)", "  sd s1, 16(sp)",
                  "  sd s2, 24(sp)", "  sd s3, 32(sp)", "  sd s4, 40(sp)",
                  "  mv s0, a0", "  mv s1, a1", "  fence rw,rw", "  .word 0x51300013", "  fence rw,rw",
                  "  csrr a4, instret", "  fence rw,rw",
                  "  csrr a6, cycle", "  fence rw,rw", "  mv s2, a4", "  mv s3, a6", "  mv a0, s0",
                  f"  call caller_{phase}", "  fence rw,rw", "  csrr a7, cycle", "  fence rw,rw",
                  "  csrr a5, instret", "  fence rw,rw", "  .word 0x51400013", "  fence rw,rw",
                  "  sub a7, a7, s3", "  sub a5, a5, s2", "  sd a7, 0(s1)", "  sd a5, 8(s1)",
                  "  ld ra, 0(sp)", "  ld s0, 8(sp)", "  ld s1, 16(sp)", "  ld s2, 24(sp)",
                  "  ld s3, 32(sp)", "  ld s4, 40(sp)", "  addi sp, sp, 48", "  ret",f".size {name}, .-{name}"]
    return "\n".join(lines)+"\n"

MAKEFILE = '''NAME = vdot-perf
SRCS = main.c caller.c demo.c timers.S gemv.S
INC_DIR += $(CURDIR)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
CFLAGS += -fno-ipa-cp -fno-ipa-icf -fno-optimize-sibling-calls -fno-lto -mno-relax -mabi=lp64d
ifneq ($(CALLER_OBJ_ROOT),)
DST_DIR := $(CALLER_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
'''

def build_commands(tools, out):
    return [("make-command",[tools["make"],"--trace","--output-sync=target","-C",str(out/"source"),
                "ARCH=riscv64-xs","MARCH=rv64gv","CROSS_COMPILE="+tools["gcc"][:-3],
                "CALLER_OBJ_ROOT="+str(out/"objects"),"BINARY="+str(out/"vdot-perf"),
                "-o","am","-o","klib","-j4","image"]),
            ("reference-command",[tools["gcc"],"-march=rv64gcv","-mabi=lp64d","-mno-relax","-c",
                str(out/"source/gemv.S"),"-o",str(out/"gemv-reference.o")]),
            ("disassemble-command",[tools["objdump"],"-d","-M","no-aliases",str(out/"vdot-perf.elf")])]

def compiler_commands(log, record):
    """Check the actual make --trace command for every separate C object."""
    root=PurePosixPath(record["build_root"]); gcc=record["toolchain"]["gcc"]["path"]
    commands=[]
    for line in log.splitlines():
        if line.startswith(gcc+" "): commands.append(shlex.split(line))
    result={}
    for name in ("main","caller","demo"):
        source=str(root/"source"/(name+".c")); dest=str(root/"objects"/(name+".o"))
        selected=[cmd for cmd in commands if source in cmd]
        g.require(len(selected)==1,"missing/duplicate actual C compilation: "+name)
        cmd=selected[0]
        g.require(cmd[-4:]==["-c","-o",dest,source] and all(cmd.count(flag)==1 for flag in C_REQUIRED),
                  "actual C compiler flags/source/output differ: "+name)
        forbidden={"-flto","-fipa-cp","-fipa-icf","-foptimize-sibling-calls","-ftree-vectorize",
                   "-ftree-slp-vectorize","-ftree-loop-distribute-patterns","-mrelax"}
        g.require(not any(arg.split("=",1)[0] in forbidden or arg.startswith("@") or
            (arg.startswith("-march=") and arg!="-march=rv64gv") or
            (arg.startswith("-mabi=") and arg!="-mabi=lp64d") or
            (re.match(r"-O",arg) and arg!="-O2") for arg in cmd),"conflicting actual C option: "+name)
        result[name]=cmd
    return result

def generate(repo, out):
    out.mkdir(parents=True,exist_ok=False)
    base=g.parent.candidate.source(repo).load_base(repo)
    inputs=[]
    for d in range(3):
        a,x=base.inputs(8,32,d)
        inputs.append([v & 255 for row in a for v in row]+[v & 255 for v in x])
    rows=[]
    for stage,phase in enumerate(PHASES):
        for method in ("vdot","rvv"):
            rows.append(dict(id=len(rows),stage=stage,scope=phase,scenario="caller-"+phase,method=method,n=1,
                             dots=32 if stage in (0,2) else 0,leaf="config_reuse_gemv_8x32_reuse_"+method))
    plan=[dict(index=stage*2+(order^(rep&1)),stage=stage,dataset=d,repeat=rep,
               phase=("first" if rep==0 else "warmup" if rep==1 else "measured"))
          for d in range(3) for stage in range(4) for rep in range(6) for order in range(2)]
    for name in ("caller.h","caller.c","demo.c","main.c"): shutil.copyfile(HERE/name,out/name)
    for name in PUBLIC_SHA: shutil.copyfile(repo/REL.parent/"public"/name,out/name)
    header=["#include <stdint.h>",f'#define CALLER_CONTRACT "{CONTRACT}"',"#define CALLER_DATASETS 3",
            f"#define CALLER_WINDOWS {len(plan)}","static const int8_t caller_inputs[3][288] __attribute__((aligned(16),used))={"]
    header += ["{"+",".join(str(pathcheck.signed(v,8)) for v in raw)+"}," for raw in inputs]
    header += ["};",""]
    (out/"data.h").write_text("\n".join(header))
    (out/"timers.S").write_text(timer_source())
    (out/"Makefile").write_text(MAKEFILE)
    manifest=dict(contract=CONTRACT,dataset=-1,datasets=[0,1,2],shape=[8,32],rows=rows,plan=plan,inputs=inputs,
                  custom_mask=0xfe00707f,custom_match=0x0200000b,
                  expected_dots=3*(6*32*2+32),ordinary_stack_demo_calls=3,
                  scope="workspace C consumer; stack README example separately functional",
                  max_cycles=MAX_CYCLES,uart_format="CW seq cycles instructions",
                  main_metric="full",diagnostic_sum_is_endtoend=False,stable_default_changed=False,hardware_changed=False)
    g.save(out/"manifest.json",manifest)
    return manifest

def verification(repo,build):
    record=read(build/"build.json")
    g.require(record["contract"]==CONTRACT and record["software_files"]==sources(repo) and record["exit_code"]==0,"caller build identity")
    for rel,sha in record["software_files"].items(): g.require(g.sha(build/"source/repo"/rel)==sha,"caller source snapshot drift")
    for name,sha in record["artifacts"].items(): g.require(g.sha(build/name)==sha,"caller artifact drift")
    g.require(set(record["artifacts"])=={"vdot-perf.elf","vdot-perf.bin","gemv-reference.o"},"caller artifact inventory")
    with tempfile.TemporaryDirectory(prefix="caller-regenerate-") as temp:
        fresh=Path(temp)/"source"; manifest=generate(repo,fresh)
        for n in GENERATED: g.require((fresh/n).read_bytes()==(build/"source"/n).read_bytes(),"caller source regeneration: "+n)
    elf=g.ELF((build/"vdot-perf.elf").read_bytes())
    parent_c=g.load("caller_parent_executable",repo/"team/optimizations/o2/r2-select/entry_c_api.py")
    parent_c.executable(elf)
    g.require(elf.binary()==(build/"vdot-perf.bin").read_bytes(),"caller executable image mismatch")
    g.require(g.sha(build/"gemv-reference.o")==OBJECT_SHA,"full qualified object rebuild differs")
    reference=g.ELF((build/"gemv-reference.o").read_bytes())
    g.require({n for n in reference.symbols if n.startswith("config_reuse_gemv_")}==set(PUBLIC_LEAVES),
              "complete reference public symbol inventory")
    for symbol in PUBLIC_LEAVES:
        raw=elf.symbol_data(symbol)
        g.require(raw and raw==reference.symbol_data(symbol),"caller changed qualified leaf: "+symbol)
    g.require(elf.symbol_data("caller_inputs")==bytes(v for d in manifest["inputs"] for v in d),"compiled dataset drift")
    paths={}
    for row in manifest["rows"]:
        entries=[pathcheck.path(elf,row["stage"],row["method"],bytes(raw)) for raw in manifest["inputs"]]
        g.require(entries[0]==entries[1]==entries[2],"data-dependent caller control flow")
        p,detail=entries[0]
        paths[str(row["id"])]=dict(detail,path_sha256=digest(b"".join(struct.pack("<QI",pc,w) for pc,w in p)))
    # Prove the selected C source is separately compiled, not LTO/constant-propagated.
    commands=record["commands"]
    g.require(record["am_revision"]==AM_COMMIT and record["parent_identity_sha256"]==parent.PARENT_IDENTITY_SHA,
              "caller AM/parent identity")
    g.require(set(record["toolchain"])==set(TOOL_NAMES) and all(
        PurePosixPath(t["path"]).is_absolute() and re.fullmatch(r"[0-9a-f]{64}",t["sha256"])
        for t in record["toolchain"].values()),"caller toolchain inventory")
    am=PurePosixPath(record["am_home"])
    g.require(set(record["external_files"])=={str(am/n) for n in
        ("am/build/am-riscv64-xs.a","libs/klib/build/klib-riscv64-xs.a")},"caller AM library inventory")
    g.require(len(commands)==3 and all(c.get("process_started") is True and c.get("exit_code")==0 and
              not c.get("timed_out") for c in commands),"caller command receipt")
    expected=build_commands({k:v["path"] for k,v in record["toolchain"].items()},PurePosixPath(record["build_root"]))
    for (label,argv),c in zip(expected,commands):
        g.require(read(build/label/"command.json")==c and c["command"]==argv and
                  c["cwd"]==record["source_root"] and type(c.get("pid")) is int and c["pid"]>0 and c["raw_sha256"]==
                  {n:g.sha(build/label/n) for n in ("stdout.log","stderr.log")},"caller command/log identity")
    log=(build/"make-command/stdout.log").read_text()
    actual_compilation=compiler_commands(log,record)
    return dict(status="CALLER_LINKED_PATH_AND_IDENTITY_PASS",contract=CONTRACT,image_sha256=g.sha(build/"vdot-perf.bin"),
                public_leaves=len(PUBLIC_LEAVES),paths=paths,windows=len(manifest["plan"]),
                actual_c_compilation=actual_compilation,runtime_not_run=True)

def build(repo,identity_path,out):
    ident=parent.parent_identity(repo,identity_path);cfg=ident["configuration"]
    parent.outside_inputs(out,[repo,identity_path.parent,cfg["hardware_source"],cfg["build_record"],cfg["am_home"]])
    source_hashes=sources(repo)
    out.mkdir(parents=True,exist_ok=False)
    generate(repo,out/"source")
    for rel in source_hashes:
        dest=out/"source/repo"/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/rel,dest)
    am=Path(cfg["am_home"])
    f,m=parent.runtime(repo,ident)
    g.require(subprocess.check_output(["git","rev-parse","HEAD"],cwd=am,text=True).strip()==f.AM_COMMIT and
              not subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=am,text=True).strip(),"official AM drift")
    tools={k:shutil.which(cfg["cross_prefix"]+k) for k in ("gcc","objdump","ld","ar","objcopy","readelf")};tools["make"]=shutil.which("make")
    g.require(all(tools.values()),"caller tools missing")
    external={str(am/n):g.sha(am/n) for n in ("am/build/am-riscv64-xs.a","libs/klib/build/klib-riscv64-xs.a")}
    env=dict(os.environ)
    for key in ("CFLAGS","CPPFLAGS","CXXFLAGS","ASFLAGS","LDFLAGS","CC_OPT","MAKEFLAGS","MFLAGS","CC","AS","LD","OBJCOPY","OBJDUMP","ARCH","MARCH","LIBS","PREBUILD"):
        env.pop(key,None)
    env.update(AM_HOME=str(am),LINUX_GNU_TOOLCHAIN="1")
    commands=build_commands(tools,out)
    record=dict(contract=CONTRACT,source_root=str(repo),build_root=str(out),source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
                software_files=source_hashes,external_files=external,toolchain={k:dict(path=v,sha256=g.sha(v)) for k,v in tools.items()},
                parent_identity_sha256=g.sha(identity_path),am_home=str(am),am_revision=f.AM_COMMIT,
                commands=[],exit_code=None,accepted=False,started=now())
    g.save(out/"build.json",record)
    try:
        for label,argv in commands: record["commands"].append(f.command(argv,repo,out/label,env=env))
        m.verify_files(external)
        record.update(exit_code=0,artifacts={n:g.sha(out/n) for n in ("vdot-perf.elf","vdot-perf.bin","gemv-reference.o")})
        g.save(out/"build.json",record)
        result=verification(repo,out);g.save(out/"elf-validation.json",result);record["accepted"]=True
    except BaseException as exc:
        record["error"]=repr(exc);raise
    finally:
        record["finished"]=now();g.save(out/"build.json",record)
    return result

def run(repo,identity_path,build_dir,out,operation):
    parent.outside_inputs(out,[repo,identity_path.parent,build_dir])
    ident,hardware,profile=parent.parent_identity(repo,identity_path,physical=True)
    cfg=ident["configuration"]
    parent.outside_inputs(out,[cfg["hardware_source"],cfg["build_record"],cfg["am_home"]])
    valid=verification(repo,build_dir)
    g.require(read(build_dir/"build.json")["accepted"] is True,"caller build not accepted")
    f,m=parent.runtime(repo,ident)
    out.mkdir(parents=True,exist_ok=False)
    state=dict(contract=CONTRACT,status="PREFLIGHT",operation_id=operation,started=now(),new_emu_runs=0,active_pid=None,active_result=None)
    persist=lambda:g.save(out/"state.json",state)
    persist()
    check=g.load("caller_runtime_check",HERE/"check.py")
    g.require(Path(check.__file__).resolve()==HERE/"check.py", "caller runtime checker import")
    try:
        files=dict(hardware)
        files.update({str(repo/rel):sha for rel,sha in sources(repo).items()})
        files.update(m.checker_files(repo))
        files[str(identity_path)]=g.sha(identity_path)
        for n in ("build.json","elf-validation.json","vdot-perf.elf","vdot-perf.bin","gemv-reference.o"):
            files[str(build_dir/n)]=g.sha(build_dir/n)
        for n in GENERATED: files[str(build_dir/"source"/n)]=g.sha(build_dir/"source"/n)
        receipt=read(build_dir/"build.json")
        files.update(receipt["external_files"]);files.update({t["path"]:t["sha256"] for t in receipt["toolchain"].values()})
        g.save(out/"runtime-inputs.json",files);g.save(out/"configuration.json",cfg)
        g.save(out/"hardware-profile.json",profile);shutil.copyfile(identity_path,out/"parent-identity.json")
        fixture=m.build_negative(repo,cfg,out/"negative-fixture")
        records=[]
        for label in ("negative","recovery","replay"):
            negative=label=="negative";dest=out/"runs"/label;cwd=dest/"cwd";(cwd/"build").mkdir(parents=True)
            for name in m.AUX: shutil.copyfile(Path(cfg["hardware_source"])/"build"/name,cwd/"build"/name)
            reference=fixture["binary"] if negative else cfg["reference"]
            inputs=dict(files);inputs.update({str(cwd/"build"/n):h for n,h in m.AUX.items()})
            if negative:inputs[reference]=fixture["negative_sha256"]
            argv=[str(Path(cfg["hardware_source"])/"build/emu"),"-i",str(build_dir/"vdot-perf.bin"),"--flash="+cfg["flash"],
                  "--ram-size=128MB","--diff="+reference,"--max-cycles="+str(MAX_CYCLES),"--seed=1"]
            rec=dict(contract=CONTRACT,name=label,negative=negative,image_sha256=valid["image_sha256"],command=argv,cwd=str(cwd),
                     reference=reference,files=inputs,started=now(),process_started=False,exit_code=None,status="RUNNING")
            before=state["new_emu_runs"]
            def progress():
                g.save(dest/"result.json",rec)
                state.update(status=label.upper(),new_emu_runs=before+int(rec.get("process_started") is True),
                             active_pid=rec.get("pid") if "finished" not in rec else None,
                             active_result=str(dest/"result.json") if "finished" not in rec else None)
                persist()
            progress()
            try:
                m.verify_files(inputs)
                env=dict(os.environ);env.pop("XS_NEGATIVE_VECTOR_TARGET",None)
                if negative:env["XS_NEGATIVE_VECTOR_TARGET"]="vdot"
                rec["environment_overrides"]={"XS_NEGATIVE_VECTOR_TARGET":"vdot" if negative else None}
                with (dest/"stdout.log").open("wb") as stdout,(dest/"stderr.log").open("wb") as stderr:
                    f.spawn(argv,cwd,stdout,stderr,rec,progress,env,7200)
                banner=g.load("caller_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
                banner.validate_runtime((dest/"stdout.log").read_text()+(dest/"stderr.log").read_text(),reference)
                if negative:
                    detail=m.negative_check(repo,build_dir,dest,rec)
                    elf=g.ELF((build_dir/"vdot-perf.elf").read_bytes())
                    leaf="config_reuse_gemv_8x32_reuse_vdot";raw=elf.symbol_data(leaf)
                    pc=elf.symbols[leaf][0]+next(i for i in range(0,len(raw),4) if int.from_bytes(raw[i:i+4],"little")&0xfe00707f==0x0200000b)
                    g.require(detail["vd"]==0 and detail["bit"]==100 and int(detail["pc"],16)==pc and detail["word"]=="0x0388000b","caller actual first vdot fault")
                    rec.update(status="EXPECTED_VDOT_HIGHBIT_REJECTION",negative_details=detail)
                else:
                    result=check.normal(repo,build_dir,dest,rec)
                    g.save(dest/"validation.json",result);rec.update(status="CALLER_DIFFTEST_COUNTER_PATH_PASS",validation_sha256=g.sha(dest/"validation.json"))
                m.verify_files(inputs)
            except BaseException as exc:
                rec.update(status="FAILED",error=repr(exc));raise
            finally:
                rec.update(finished=now(),raw_sha256={n:g.sha(dest/n) for n in ("stdout.log","stderr.log") if (dest/n).is_file()});progress()
            records.append(rec);g.save(out/"completed-runs.json",records);print(label,rec["status"],flush=True)
        g.require(records[0]["image_sha256"]==records[1]["image_sha256"]==records[2]["image_sha256"] and
                  len({r["pid"] for r in records})==3,"caller recovery/replay process identity")
        g.require(read(out/"runs/recovery/validation.json")==read(out/"runs/replay/validation.json"),"caller complete replay differs")
        ident2,hardware2,profile2=parent.parent_identity(repo,identity_path,physical=True)
        g.require(ident==ident2 and hardware==hardware2 and profile==profile2,"caller fixed hardware drift")
        m.verify_files(files)
        state.update(status="CALLER_CAMPAIGN_PASS",new_emu_runs=3,active_pid=None,active_result=None)
        g.save(out/"results.json",dict(contract=CONTRACT,records=records,validation=read(out/"runs/recovery/validation.json")))
    except BaseException as exc:
        state.update(status="FAILED",error=repr(exc));raise
    finally:
        state["finished"]=now();persist()
    return state

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True);p.add_argument("--identity",type=Path,required=True)
    p.add_argument("--action",choices=("build","run","verify-build"),required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--build",type=Path);p.add_argument("--operation-id")
    args=p.parse_args();repo=args.repo.resolve();out=args.output.resolve()
    g.require(repo==ROOT and not out.exists(),"new output and selected checkout required")
    if os.name=="posix":os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if args.action=="build": result=build(repo,args.identity.resolve(),out)
    elif args.action=="run":
        g.require(args.build and args.operation_id,"run needs build and operation")
        result=run(repo,args.identity.resolve(),args.build.resolve(),out,args.operation_id)
    else:
        g.require(args.build is not None,"verification needs build")
        cfg=parent.parent_identity(repo,args.identity.resolve())["configuration"]
        parent.outside_inputs(out,[repo,args.build.resolve(),args.identity.resolve().parent,
                                  cfg["hardware_source"],cfg["build_record"],cfg["am_home"]])
        result=verification(repo,args.build.resolve());g.save(out,result)
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
