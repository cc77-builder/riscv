"""Ordinary C application calling the S1 public GEMV leaves; functional only."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import tempfile

import entry_candidate as candidate
import entry_gate as g
import entry_experiment as a

CONTRACT = "r4-gemv-c-application-v1"
FILES = ("gemv.S", "gemv.h", "cases.h", "manifest.json", "main.c", "Makefile")
MAIN = r'''#include <stdint.h>
#include <stddef.h>
#include "gemv.h"
#include "cases.h"
extern void _putc(char);
static const uint64_t canary = UINT64_C(0xd15ea5e5cafebabe);
static struct { uint64_t head[2]; int8_t value[1088]; uint64_t tail[2]; } input __attribute__((aligned(16)));
static struct { uint64_t head[2]; unsigned char value[16][16]; uint64_t tail[2]; } output __attribute__((aligned(16)));
static void text(const char *s) { while (*s) _putc(*s++); }
static void decimal(uint64_t x) {
  char buf[21]; unsigned n=0;
  do { buf[n++]=(char)('0'+x%10); x/=10; } while(x);
  while(n) _putc(buf[--n]);
}
static void fill(unsigned char *p, unsigned n, unsigned char v) { while(n--) *p++=v; }
static uint64_t hash(const unsigned char *p, unsigned n) {
  uint64_t h=UINT64_C(14695981039346656037);
  while(n--) { h^=*p++; h*=UINT64_C(1099511628211); }
  return h;
}
static unsigned judge(const struct r4_c_case *c) {
  if(input.head[0]!=canary || input.head[1]!=canary || input.tail[0]!=canary || input.tail[1]!=canary ||
     output.head[0]!=canary || output.head[1]!=canary || output.tail[0]!=canary || output.tail[1]!=canary) return 1;
  for(unsigned i=0;i<c->size;++i) if(input.value[i]!=c->packed[i]) return 2;
  for(unsigned i=c->size;i<1088;++i) if((unsigned char)input.value[i]!=0x5a) return 3;
  for(unsigned row=0;row<c->m;++row) {
    int32_t wanted=0;
    for(unsigned col=0;col<c->k;++col) wanted+=(int32_t)c->packed[row*c->k+col]*c->packed[c->m*c->k+col];
    for(unsigned byte=0;byte<16;++byte) {
      unsigned char value=byte<4?(unsigned char)((uint32_t)wanted>>(8*byte)):0;
      if(output.value[row][byte]!=value) return 10+row;
    }
  }
  for(unsigned row=c->m;row<16;++row) for(unsigned byte=0;byte<16;++byte)
    if(output.value[row][byte]!=0xa6) return 30;
  uint64_t vl,vtype,vstart,vcsr;
  __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr"
                   :"=r"(vl),"=r"(vtype),"=r"(vstart),"=r"(vcsr));
  if(vl!=8 || vtype!=0 || vstart!=0 || vcsr!=7) return 31;
  if(hash(&output.value[0][0],c->m*16)!=c->expected_hash) return 32;
  return 0;
}
int main(void) {
  __asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x600):"memory");
  text("R4C_BEGIN cases="); decimal(R4C_COUNT); text(" contract=" R4C_CONTRACT "\n");
  for(unsigned seq=0;seq<R4C_COUNT;++seq) {
    const struct r4_c_case *c=&r4_c_cases[seq];
    fill((unsigned char *)input.value,1088,0x5a);
    for(unsigned i=0;i<c->size;++i) input.value[i]=c->packed[i];
    fill(&output.value[0][0],256,0xa6);
    input.head[0]=input.head[1]=input.tail[0]=input.tail[1]=canary;
    output.head[0]=output.head[1]=output.tail[0]=output.tail[1]=canary;
    c->entry(input.value,output.value);
    unsigned verdict=judge(c);
    if(verdict) { text("R4C_FAIL seq="); decimal(seq); text(" verdict="); decimal(verdict); _putc('\n'); return 1; }
    if(seq==0) {
      unsigned detected=0;
      output.value[0][0]^=1; detected+=judge(c)!=0; output.value[0][0]^=1;
      output.value[0][15]^=0x80; detected+=judge(c)!=0; output.value[0][15]^=0x80;
      output.tail[0]^=1; detected+=judge(c)!=0; output.tail[0]^=1;
      input.value[0]^=1; detected+=judge(c)!=0; input.value[0]^=1;
      output.value[15][15]^=1; detected+=judge(c)!=0; output.value[15][15]^=1;
      text("R4C_CONTROLS detected="); decimal(detected); text(" expected=5\n");
      if(detected!=5 || judge(c)) return 2;
    }
    text("R4C_CASE seq="); decimal(seq); text(" hash="); decimal(hash(&output.value[0][0],c->m*16)); _putc('\n');
  }
  text("R4C_END executed="); decimal(R4C_COUNT); text(" failures=0\n");
  return 0;
}
'''
MAKEFILE = '''NAME = vdot-perf
SRCS = main.c gemv.S
INC_DIR += $(CURDIR)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
ifneq ($(R4_OBJ_ROOT),)
DST_DIR := $(R4_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
'''


def fnv(raw):
    value = 14695981039346656037
    for byte in raw:
        value = ((value ^ byte) * 1099511628211) & ((1 << 64) - 1)
    return value


def generate(repo, out):
    out.mkdir(parents=True, exist_ok=False)
    base = candidate.source(repo).load_base(repo)
    rows, cases, inputs, assembly = [], [], {}, []
    for shard in (1, 3, 5, 7):
        with tempfile.TemporaryDirectory(prefix="r4-c-api-generate-") as temp:
            path = Path(temp) / "data"
            manifest = candidate.generate(repo, path, "s1", 0, shard)
            assembly.append((path / "gemv.S").read_text())
        for row in manifest["rows"]:
            rows.append(dict(row, shard=shard))
        m, k = manifest["rows"][0]["m"], manifest["rows"][0]["k"]
        for dataset in range(3):
            matrix, vector = base.inputs(m, k, dataset)
            packed = bytes(x & 255 for r in matrix for x in r) + bytes(x & 255 for x in vector)
            name = f"r4_c_input_{shard}_{dataset}"
            inputs[name] = list(packed)
            output = b"".join(struct.pack("<i", sum(x*y for x,y in zip(r,vector))) + bytes(12) for r in matrix)
            for row in manifest["rows"]:
                cases.append(dict(api_symbol=row["api_symbol"], input_symbol=name, m=m, k=k, size=len(packed),
                                  dataset=dataset, api_index=next(i for i,v in enumerate(rows) if v["api_symbol"]==row["api_symbol"]),
                                  expected_hash=fnv(output), dots=row["dots"] if row["method"]=="vdot" else 0))
    header = ["#ifndef R4_PUBLIC_GEMV_H", "#define R4_PUBLIC_GEMV_H", "#include <stdint.h>",
              "/* S1 leaves; packed A||x, disjoint 16-byte output slots, VLEN128/VS enabled.",
              " * Vector configuration is clobbered. See ENTRY_CONTRACT.md. */"]
    header += [f"void {r['api_symbol']}(const int8_t *, void *);" for r in rows]
    header += ["#endif", ""]
    data = ["#include <stdint.h>", "#define R4C_COUNT 48", f'#define R4C_CONTRACT "{CONTRACT}"',
            "struct r4_c_case { void (*entry)(const int8_t *,void *); const int8_t *packed; uint64_t m,k,size,dataset,api_index,expected_hash; };",
            '_Static_assert(sizeof(struct r4_c_case)==64,"case ABI");']
    for name, raw in inputs.items():
        values = ",".join(str(x-256 if x>127 else x) for x in raw)
        data.append(f"static const int8_t {name}[] __attribute__((aligned(16),used))={{{values}}};")
    data.append("static const struct r4_c_case r4_c_cases[] __attribute__((used))={")
    for row in cases:
        data.append("{" + ",".join([row["api_symbol"], row["input_symbol"]] +
                    ["UINT64_C(" + str(row[k]) + ")" for k in ("m", "k", "size", "dataset", "api_index", "expected_hash")]) + "},")
    data += ["};", ""]
    manifest = dict(contract=CONTRACT, variant="s1", shapes=[[4,8],[8,32],[16,64],[4,13]], datasets=[0,1,2],
                    rows=rows, cases=cases, inputs=inputs, expected_dots=sum(r["dots"] for r in cases),
                    performance_measured=False, arbitrary_application_acceptance=False)
    (out / "gemv.S").write_text("\n".join(assembly))
    (out / "gemv.h").write_text("\n".join(header))
    (out / "cases.h").write_text("\n".join(data))
    (out / "main.c").write_text(MAIN)
    (out / "Makefile").write_text(MAKEFILE)
    g.save(out / "manifest.json", manifest)
    return manifest


def source_files(repo):
    g.require(Path(__file__).resolve() == repo / g.ENTRY / "entry_c_api.py" and
              Path(g.__file__).resolve() == repo / g.ENTRY / "entry_gate.py", "C application checker outside selected checkout")
    g.verify_sources(repo)
    paths = g.SOURCES | {str(g.ENTRY / "entry_c_api.py"), str(g.S1 / "gate.py"), str(g.REL / "machine_model.py")}
    return {rel: g.sha(repo / rel) for rel in sorted(paths)}


def executable(elf):
    """Default AM application layout, independent of benchmark fixed slots."""
    ram,end=g.original.RAM,g.original.RAM_END
    g.require(elf.kind==2 and "r2_unit_test_fixture" not in elf.symbols and elf.entry==ram and
              elf.symbols.get("_start",(None,))[0]==ram and
              all(n in elf.symbols for n in ("main","_trm_init","_halt","_putc")),"C application boot/runtime")
    g.require(not any(p[0] in (2,3) for p in elf.segments),"dynamic C application ELF")
    loads=[p for p in elf.segments if p[0]==1 and p[6]]
    g.require(loads and any(p[1]&1 and p[3]<=elf.entry<p[3]+p[5] for p in loads),"C application boot not loaded")
    for _,flags,offset,vaddr,paddr,filesz,memsz,align in loads:
        g.require(filesz<=memsz and vaddr==paddr and ram<=vaddr<vaddr+memsz<=end and
                  (align in (0,1) or (align&(align-1)==0 and (vaddr-offset)%align==0)),"C application load segment")
        elf.range(offset,filesz)
    for s in elf.sections:
        if s[2]&2 and s[5]:
            g.require(any(p[3]<=s[3] and s[3]+s[5]<=p[3]+p[6] and (s[1]==8 or
                      (s[3]+s[5]<=p[3]+p[5] and s[4]-p[2]==s[3]-p[3])) for p in loads),"C application allocated section")


def verify_build(repo, build):
    receipt = a.read(build / "build.json")
    g.require(receipt["contract"] == CONTRACT and receipt["exit_code"] == 0 and
              receipt["software_files"] == source_files(repo), "C application build identity")
    for name, sha in receipt["artifacts"].items():
        g.require(g.sha(build / name) == sha, "C application artifact drift")
    g.require(set(receipt["artifacts"]) == {"vdot-perf.elf", "vdot-perf.bin", "gemv-reference.o"}, "C build artifacts")
    for rel, sha in receipt["software_files"].items():
        g.require(g.sha(build / "source/repo" / rel) == sha, "C application snapshot drift")
    root=PurePosixPath(receipt["build_root"])
    tools=receipt["toolchain"]
    g.require(set(tools)=={"gcc","ld","ar","objcopy","objdump","readelf","make"},"C application toolchain inventory")
    expected_commands=[
        ("make-command",[tools["make"]["path"],"-C",str(root/"source"),"ARCH=riscv64-xs","MARCH=rv64gcv",
                          "CROSS_COMPILE="+tools["gcc"]["path"][:-3],"R4_OBJ_ROOT="+str(root/"objects"),
                          "BINARY="+str(root/"vdot-perf"),"-o","am","-o","klib","-j1","image"]),
        ("reference-command",[tools["gcc"]["path"],"-march=rv64gcv","-mabi=lp64d","-mno-relax","-c",
                               str(root/"source/gemv.S"),"-o",str(root/"gemv-reference.o")])]
    g.require(len(receipt["commands"])==2 and receipt["am_revision"]==a.frozen_f.AM_COMMIT,"C application build commands/AM")
    previous=None
    for i,(label,argv) in enumerate(expected_commands):
        command=a.read(build/label/"command.json")
        g.require(command==receipt["commands"][i] and command["command"]==argv and command["cwd"]==receipt["source_root"] and
                  command.get("process_started") is True and type(command.get("pid")) is int and command["pid"]>0 and
                  command.get("exit_code")==0 and not command.get("timed_out") and command["raw_sha256"]==
                  {n:g.sha(build/label/n) for n in ("stdout.log","stderr.log")},"C application build command receipt")
        start,finish=timeline(command)
        g.require(previous is None or previous<=start,"C application overlapping build steps")
        previous=finish
    with tempfile.TemporaryDirectory(prefix="r4-c-regenerate-") as temp:
        fresh = Path(temp) / "generated"
        manifest = generate(repo, fresh)
        for name in FILES:
            g.require((fresh / name).read_bytes() == (build / "source" / name).read_bytes(), "C application source regeneration: " + name)
    elf = g.ELF((build / "vdot-perf.elf").read_bytes())
    executable(elf)
    g.require(elf.binary() == (build / "vdot-perf.bin").read_bytes(), "C application ELF/BIN mismatch")
    public = g.ELF((build / "gemv-reference.o").read_bytes())
    g.require(public.kind == 1 and not any(s[1] in (4,9) and s[5] for s in public.sections), "C public reference relocations")
    reports, auditor = [], g.s1.auditor(repo)
    from collections import Counter
    for row in manifest["rows"]:
        symbol = row["api_symbol"]
        leaf = elf.symbol_data(symbol)
        g.require(leaf == public.symbol_data(symbol) and leaf[:8] == struct.pack("<II",0x00050613,0x00058693) and
                  leaf[-4:] == struct.pack("<I",0x00008067), "C application public function mismatch")
        core = leaf[8:-4]
        g.require(dict(Counter(auditor.decode(w)[0] for w, in struct.iter_unpack("<I",core))) == auditor.source_counts(row["body"]),
                  "C application compiled body differs")
        reports.append(dict(symbol=symbol, bytes=len(leaf), sha256=hashlib.sha256(leaf).hexdigest(),
                            semantics=g.semantic_check(core,row,repo)))
    for name, raw in manifest["inputs"].items():
        g.require(elf.symbol_data(name) == bytes(raw), "C application actual input bytes")
    cases = elf.symbol_data("r4_c_cases")
    expected = b"".join(struct.pack("<8Q", elf.symbols[r["api_symbol"]][0], elf.symbols[r["input_symbol"]][0],
                  *(r[k] for k in ("m","k","size","dataset","api_index","expected_hash"))) for r in manifest["cases"])
    g.require(cases == expected, "C application linked call table differs")
    return dict(status="R4_C_APPLICATION_LINKED_MODEL_PASS_NOT_RUNTIME", cases=48, public_functions=16,
                expected_dots=manifest["expected_dots"], image_sha256=g.sha(build / "vdot-perf.bin"), functions=reports)


def build(repo, cfg, out):
    a.protect_output(repo, cfg, out)
    out.mkdir(parents=True, exist_ok=False)
    generate(repo, out / "source")
    sources = source_files(repo)
    for rel in sources:
        target = out / "source/repo" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / rel, target)
    am = Path(cfg["am_home"])
    g.require(subprocess.check_output(["git","rev-parse","HEAD"],cwd=am,text=True).strip()==a.frozen_f.AM_COMMIT and
              not subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=am,text=True).strip(), "C application AM source")
    tools = {k: shutil.which(cfg["cross_prefix"]+k) for k in ("gcc","ld","ar","objcopy","objdump","readelf")}
    tools["make"] = shutil.which("make")
    g.require(all(tools.values()), "C application toolchain unavailable")
    libraries = [am/"am/build/am-riscv64-xs.a",am/"libs/klib/build/klib-riscv64-xs.a"]
    external = {str(p):g.sha(p) for p in libraries}
    env = a.build_environment(am, tools)
    commands = [
        ("make-command",[tools["make"],"-C",str(out/"source"),"ARCH=riscv64-xs","MARCH=rv64gcv",
                         "CROSS_COMPILE="+tools["gcc"][:-3],"R4_OBJ_ROOT="+str(out/"objects"),"BINARY="+str(out/"vdot-perf"),
                         "-o","am","-o","klib","-j1","image"]),
        ("reference-command",[tools["gcc"],"-march=rv64gcv","-mabi=lp64d","-mno-relax","-c",
                              str(out/"source/gemv.S"),"-o",str(out/"gemv-reference.o")])]
    receipt = dict(contract=CONTRACT, build_root=str(out), source_root=str(repo), software_files=sources, source_commit=subprocess.check_output(
                       ["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
                   am_revision=a.frozen_f.AM_COMMIT, external_files=external,
                   environment_contract=a.LIVE_CONTRACT, environment=dict(env),
                   toolchain={k:dict(path=p,sha256=g.sha(p)) for k,p in tools.items()}, commands=[], exit_code=None)
    g.save(out/"build.json",receipt)
    try:
        for label, argv in commands:
            receipt["commands"].append(a.frozen_f.command(argv,repo,out/label,env))
        a.frozen_m.verify_files(external)
        receipt.update(exit_code=0,artifacts={n:g.sha(out/n) for n in ("vdot-perf.elf","vdot-perf.bin","gemv-reference.o")})
        g.save(out/"build.json",receipt)
        validation=verify_build(repo,out)
        g.save(out/"elf-validation.json",validation)
        receipt["accepted"]=True
    except BaseException as exc:
        receipt.update(accepted=False,error=repr(exc))
        raise
    finally:
        g.save(out/"build.json",receipt)
    return validation


def normal_check(repo, build, run, record):
    g.require(record.get("process_started") is True and record.get("exit_code")==0 and not record.get("timed_out"),
              "C application incomplete/nonzero execution")
    gate=g.load("r4_c_runtime_failure",repo/"team/optimizations/o1/audit/runtime_gate.py")
    fatal=g.load("r4_c_fatal",repo/"team/optimizations/o2/fullcore/recheck.py")
    observer=g.load("r4_c_observer",repo/"team/optimizations/o2/fullcore/analyze.py")
    stdout,stderr=((run/n).read_text() for n in ("stdout.log","stderr.log"))
    for stream in (stdout,stderr):
        gate.validate_failure_markers(stream)
        fatal.reject_fatal_output(stream)
    # Observer records can interrupt individual UART bytes. Reuse the frozen
    # strict record parser before matching application lines, preserving all
    # non-observer characters and rejecting malformed/truncated records.
    _,uart=observer.extract_events_and_uart(stderr+stdout)
    gate.validate_failure_markers(uart)
    fatal.reject_fatal_output(uart)
    plain=gate.normalize_console(uart)
    manifest=a.read(build/"source/manifest.json")
    lines=[s for s in plain.splitlines() if s.startswith("R4C_")]
    expected=[f"R4C_BEGIN cases=48 contract={CONTRACT}","R4C_CONTROLS detected=5 expected=5"]
    expected += [f"R4C_CASE seq={i} hash={c['expected_hash']}" for i,c in enumerate(manifest["cases"])]
    expected += ["R4C_END executed=48 failures=0"]
    g.require(lines==expected and plain.count("HIT GOOD TRAP")==1,"C application raw cases/controls/GOOD TRAP differ")
    analysis=observer.analyze(stderr+stdout)
    g.require(analysis["status"]=="O2_TRACE_PASS" and analysis["schema"]["slots"]==2 and
              all(analysis.get(k)==0 for k in ("pending_count","pending_div_count","unfinished_rob_count")) and
              analysis["counts"].get("COMMIT")==manifest["expected_dots"],"C application complete O2 protocol/commit count")
    return dict(status="R4_C_APPLICATION_DIFFTEST_PASS",case_count=48,public_functions=16,
                output_hashes=[r["expected_hash"] for r in manifest["cases"]],performance_measured=False),analysis


def run(repo,cfg,build_dir,out,operation):
    a.protect_output(repo,cfg,out,[build_dir])
    out.mkdir(parents=True,exist_ok=False)
    state=dict(status="PREFLIGHT",contract=CONTRACT,operation_id=operation,started=a.frozen_f.now(),
               new_emu_runs=0,active_pid=None,active_result=None,performance_measured=False)
    persist=lambda:g.save(out/"state.json",state)
    persist()
    try:
        validation=verify_build(repo,build_dir)
        g.require(a.read(build_dir/"build.json").get("accepted") is True,"C application build not accepted")
        files=a.frozen_m.checker_files(repo)
        files.update({str(repo/rel):sha for rel,sha in source_files(repo).items()})
        hardware,profile=a.frozen_m.hardware_profile(repo,cfg)
        files.update(hardware)
        for name in ("build.json","elf-validation.json","vdot-perf.elf","vdot-perf.bin","gemv-reference.o"):
            files[str(build_dir/name)]=g.sha(build_dir/name)
        for name in FILES:
            files[str(build_dir/"source"/name)]=g.sha(build_dir/"source"/name)
        receipt=a.read(build_dir/"build.json")
        files.update(receipt["external_files"])
        files.update({r["path"]:r["sha256"] for r in receipt["toolchain"].values()})
        g.save(out/"runtime-inputs.json",files)
        g.save(out/"configuration.json",dict(cfg,canonical_build=str(build_dir),run_root=str(out),source_root=str(repo)))
        g.save(out/"hardware-profile.json",profile)
        fixture=a.frozen_m.build_negative(repo,cfg,out/"negative-fixture")
        records=[]
        for label,negative in (("negative",True),("recovery",False),("replay",False)):
            directory=out/"runs"/label
            cwd=directory/"cwd"
            (cwd/"build").mkdir(parents=True)
            for name in a.frozen_m.AUX:
                shutil.copyfile(Path(cfg["hardware_source"])/"build"/name,cwd/"build"/name)
            reference=fixture["binary"] if negative else cfg["reference"]
            inputs=dict(files)
            inputs.update({str(cwd/"build"/n):sha for n,sha in a.frozen_m.AUX.items()})
            if negative: inputs[reference]=fixture["negative_sha256"]
            argv=[str(Path(cfg["hardware_source"])/"build/emu"),"-i",str(build_dir/"vdot-perf.bin"),
                  "--flash="+cfg["flash"],"--ram-size=128MB","--diff="+reference,"--max-cycles=2000000","--seed=1"]
            record=dict(name="r4-c-api-s1",contract=CONTRACT,negative=negative,replay=int(label=="replay"),
                        image_sha256=validation["image_sha256"],command=argv,cwd=str(cwd),reference=reference,files=inputs,
                        process_started=False,exit_code=None,status="RUNNING",started=a.frozen_f.now(),performance_measured=False)
            before=state["new_emu_runs"]
            def progress():
                g.save(directory/"result.json",record)
                state.update(new_emu_runs=before+int(record.get("process_started") is True),
                             active_pid=record.get("pid") if "finished" not in record else None,
                             active_result=str(directory/"result.json") if "finished" not in record else None)
                persist()
            progress()
            try:
                a.frozen_m.verify_files(inputs)
                env=a.frozen_m.execution_environment(negative)
                record.update(environment_contract=a.LIVE_CONTRACT, environment=dict(env))
                record["environment_overrides"]={"XS_NEGATIVE_VECTOR_TARGET":"vdot" if negative else None}
                with (directory/"stdout.log").open("wb") as stdout,(directory/"stderr.log").open("wb") as stderr:
                    a.frozen_f.spawn(argv,cwd,stdout,stderr,record,progress,env=env,timeout=7200)
                suite=g.load("r4_c_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
                suite.validate_runtime((directory/"stdout.log").read_text()+(directory/"stderr.log").read_text(),reference)
                if negative:
                    details=a.frozen_m.negative_check(repo,build_dir,directory,record)
                    elf=g.ELF((build_dir/"vdot-perf.elf").read_bytes())
                    pc=int(details["pc"],16)
                    manifest=a.read(build_dir/"source/manifest.json")
                    g.require(any(elf.symbols[r["api_symbol"]][0]<=pc<sum(elf.symbols[r["api_symbol"]][:2]) for r in manifest["rows"]),
                              "C application fault outside public leaf")
                    record.update(status=a.frozen_m.NEGATIVE_PASS,negative_details=details)
                else:
                    result,analysis=normal_check(repo,build_dir,directory,record)
                    g.save(directory/"validation.json",result)
                    g.save(directory/"observation.json",analysis)
                    record.update(status=result["status"],validation=result)
                a.frozen_m.verify_files(inputs)
            except BaseException as exc:
                record.update(status="FAILED",error=repr(exc))
                raise
            finally:
                record.update(finished=a.frozen_f.now(),raw_sha256={n:g.sha(directory/n) for n in ("stdout.log","stderr.log") if (directory/n).is_file()})
                progress()
            records.append(record)
            g.save(out/"completed-runs.json",records)
            print(label,record["status"],flush=True)
        validate_recovery(records[0],records[1])
        g.require(records[1]["validation"]==records[2]["validation"],"C application output replay differs")
        hardware_after,profile_after=a.frozen_m.hardware_profile(repo,cfg)
        g.require(hardware_after==hardware and profile_after==profile,"C application hardware drift")
        a.frozen_m.verify_files(files)
        state.update(status="R4_C_APPLICATION_CALLS_PASS",distinct_cases=48,public_functions=16,normal_case_executions=96,
                     expected_negative_runs=1,normal_runs=2,new_emu_runs=3,whole_suite_acceptance=False)
        g.save(out/"results.json",dict(state,runs=records))
    except BaseException as exc:
        state.update(status="FAILED",error=repr(exc))
        raise
    finally:
        state["finished"]=a.frozen_f.now()
        persist()
    return state


def validate_recovery(negative,normal):
    g.require(negative["status"]==a.frozen_m.NEGATIVE_PASS and normal["status"]=="R4_C_APPLICATION_DIFFTEST_PASS" and
              negative["negative"] is True and normal["negative"] is False and
              negative["image_sha256"]==normal["image_sha256"] and negative["name"]==normal["name"] and
              negative["pid"]!=normal["pid"] and negative["reference"]!=normal["reference"],"C application recovery identity")
    start,finish=datetime.fromisoformat(normal["started"]),datetime.fromisoformat(negative["finished"])
    g.require(start.utcoffset() is not None and finish.utcoffset() is not None and start>=finish,"C application recovery time")


def timeline(record):
    start,finish=(datetime.fromisoformat(record[k]) for k in ("started","finished"))
    g.require(start.utcoffset() is not None and finish.utcoffset() is not None and start<=finish,"C application timestamps")
    return start,finish


def audit_run(repo,build,run,external=None):
    """Recompute C-case outputs/protocol from raw logs; external is sealed hashes."""
    validation=verify_build(repo,build)
    g.require(a.read(build/"elf-validation.json")==validation and a.read(build/"build.json").get("accepted") is True,
              "C application cached build validation")
    cfg,state,common=(a.read(run/n) for n in ("configuration.json","state.json","runtime-inputs.json"))
    g.require(state["status"]=="R4_C_APPLICATION_CALLS_PASS" and state["contract"]==CONTRACT and
              state["new_emu_runs"]==3 and state["active_pid"] is None and state["active_result"] is None and
              isinstance(state.get("operation_id"),str) and state["operation_id"].strip() and
              state["performance_measured"] is False and state["whole_suite_acceptance"] is False and
              state["distinct_cases"]==48 and state["public_functions"]==16 and state["normal_case_executions"]==96 and
              state["expected_negative_runs"]==1 and state["normal_runs"]==2,"C application campaign qualification")
    source,original_build=PurePosixPath(cfg["source_root"]),PurePosixPath(cfg["canonical_build"])
    expected={str(source/Path(p).relative_to(repo).as_posix()):sha for p,sha in a.frozen_m.checker_files(repo).items()}
    expected.update({str(source/rel):sha for rel,sha in source_files(repo).items()})
    expected.update({str(PurePosixPath(cfg["build_record"])/n):sha for n,sha in a.frozen_m.META.items()})
    expected.update({str(PurePosixPath(cfg["hardware_source"])/"build"/n):sha for n,sha in a.frozen_m.AUX.items()})
    profile=a.read(run/"hardware-profile.json")
    expected.update({str(PurePosixPath(cfg["hardware_source"])/"build/emu"):a.frozen_m.EMU,
                     cfg["reference"]:a.frozen_f.REFERENCE,cfg["flash"]:a.frozen_f.FLASH,
                     cfg["build_driver"]:profile["build_driver_sha256"],
                     str(PurePosixPath(cfg["hardware_source"])/"team/optimizations/o2/fullcore/build_fullcore.py"):
                       "8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0"})
    for n in ("build.json","elf-validation.json","vdot-perf.elf","vdot-perf.bin","gemv-reference.o"):
        expected[str(original_build/n)]=g.sha(build/n)
    for n in FILES: expected[str(original_build/"source"/n)]=g.sha(build/"source"/n)
    receipt=a.read(build/"build.json")
    g.require(receipt["build_root"]==cfg["canonical_build"] and receipt["source_root"]==cfg["source_root"],"C build/config root")
    g.require(set(receipt["external_files"])=={str(PurePosixPath(cfg["am_home"])/n) for n in
              ("am/build/am-riscv64-xs.a","libs/klib/build/klib-riscv64-xs.a")},"C application AM library inventory")
    expected.update(receipt["external_files"])
    expected.update({v["path"]:v["sha256"] for v in receipt["toolchain"].values()})
    g.require(common==expected,"C application common input inventory")
    fixture=a.read(run/"negative-fixture/fixture.json")
    g.require(fixture["source_sha256"]==a.frozen_m.NEGATIVE_SHA and fixture["normal_reference_sha256"]==a.frozen_f.REFERENCE and
              fixture["historical_negative_hash_claim"] is False and g.sha(run/"negative-fixture/negative-fixture.c")==a.frozen_m.NEGATIVE_SHA and
              g.sha(run/"negative-fixture/negative-reference.so")==fixture["negative_sha256"],"C negative fixture bytes")
    records,inputs=[],dict(common)
    suite=g.load("r4_c_offline_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
    for label in ("negative","recovery","replay"):
        directory=run/"runs"/label
        record=a.read(directory/"result.json")
        negative=label=="negative"
        reference=fixture["binary"] if negative else cfg["reference"]
        cwd=PurePosixPath(cfg["run_root"])/"runs"/label/"cwd"
        wanted=dict(common)
        wanted.update({str(cwd/"build"/n):sha for n,sha in a.frozen_m.AUX.items()})
        if negative: wanted[reference]=fixture["negative_sha256"]
        argv=[str(PurePosixPath(cfg["hardware_source"])/"build/emu"),"-i",str(original_build/"vdot-perf.bin"),
              "--flash="+cfg["flash"],"--ram-size=128MB","--diff="+reference,"--max-cycles=2000000","--seed=1"]
        g.require(record["name"]=="r4-c-api-s1" and record["contract"]==CONTRACT and record["negative"] is negative and
                  record["replay"]==int(label=="replay") and record["cwd"]==str(cwd) and record["command"]==argv and
                  record["reference"]==reference and record["files"]==wanted and record["process_started"] is True and
                  type(record["pid"]) is int and record["pid"]>0 and not record.get("timed_out") and
                  record["exit_code"]==(1 if negative else 0) and record["performance_measured"] is False and
                  record["status"]==(a.frozen_m.NEGATIVE_PASS if negative else "R4_C_APPLICATION_DIFFTEST_PASS") and
                  record["image_sha256"]==validation["image_sha256"] and record["environment_overrides"]==
                  {"XS_NEGATIVE_VECTOR_TARGET":"vdot" if negative else None},"C application execution identity")
        g.require(record["raw_sha256"]=={n:g.sha(directory/n) for n in ("stdout.log","stderr.log")},"C raw transcript identity")
        suite.validate_runtime((directory/"stdout.log").read_text()+(directory/"stderr.log").read_text(),reference)
        for path,sha in wanted.items():
            g.require(path not in inputs or inputs[path]==sha,"mixed C application input identity")
            inputs[path]=sha
        if negative:
            with tempfile.TemporaryDirectory(prefix="r4-c-negative-audit-") as temp:
                copy=Path(temp)
                for n in ("stdout.log","stderr.log"): shutil.copyfile(directory/n,copy/n)
                details=a.frozen_m.negative_check(repo,build,copy,record)
                g.require(details==record["negative_details"]==a.read(directory/"negative.json") and
                          a.read(copy/"observation.json")==a.read(directory/"observation.json"),"C negative raw replay")
                elf=g.ELF((build/"vdot-perf.elf").read_bytes())
                pc=int(details["pc"],16)
                g.require(any(elf.symbols[r["api_symbol"]][0]<=pc<sum(elf.symbols[r["api_symbol"]][:2])
                              for r in a.read(build/"source/manifest.json")["rows"]),"C negative outside public function")
        else:
            checked,analysis=normal_check(repo,build,directory,record)
            g.require(checked==record["validation"]==a.read(directory/"validation.json") and
                      json.loads(json.dumps(analysis))==a.read(directory/"observation.json"),"C normal raw replay")
        records.append(record)
    g.require({p.name for p in (run/"runs").iterdir()}=={"negative","recovery","replay"},"C application extra/missing run")
    validate_recovery(records[0],records[1])
    g.require(records[1]["validation"]==records[2]["validation"],"C functional output replay differs")
    start,finish=timeline(state)
    g.require(start<=timeline(records[0])[0] and timeline(records[-1])[1]<=finish and
              all(timeline(x)[1]<=timeline(y)[0] for x,y in zip(records,records[1:])),"C execution chronology")
    cached=a.read(run/"results.json")
    g.require(cached["runs"]==records==a.read(run/"completed-runs.json") and
              {k:v for k,v in cached.items() if k!="runs"}=={k:v for k,v in state.items() if k!="finished"},"C cached summary differs")
    if external is None:
        a.frozen_m.verify_files(inputs)
        _,actual_profile=a.frozen_m.hardware_profile(repo,{k:v for k,v in cfg.items() if k not in ("canonical_build","run_root","source_root")})
        g.require(profile==actual_profile,"C physical hardware profile drift")
    else:
        g.require(inputs==external,"C archived input closure differs")
    return dict(status="R4_C_APPLICATION_RAW_AUDIT_PASS",contract=CONTRACT,distinct_cases=48,public_functions=16,
                normal_case_executions=96,original_emu_processes=3,expected_negative_runs=1,
                ordinary_c_caller_executed=True,performance_measured=False,whole_suite_acceptance=False,
                physical_external_inputs_revalidated=external is None,new_emu_runs=0,new_nemu_runs=0)



if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--action",choices=("generate","build","verify-build","run","audit"),required=True)
    p.add_argument("--config",type=Path)
    p.add_argument("--build",type=Path)
    p.add_argument("--run",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--operation-id")
    args=p.parse_args()
    repo,out=args.repo.resolve(),args.output.resolve()
    g.require(not out.exists(),"C output path must be new")
    if args.action in ("generate","build"):
        if args.action=="build": g.require(args.config is not None,"C build requires runtime config")
        result=generate(repo,out) if args.action=="generate" else build(repo,a.config(args.config),out)
    elif args.action=="run":
        g.require(args.config is not None and args.build is not None and args.operation_id,"C run requires build/config/operation")
        result=run(repo,a.config(args.config),args.build.resolve(),out,args.operation_id)
    else:
        g.require(args.build is not None and all(not out.is_relative_to(p.resolve()) for p in (args.build,args.run) if p is not None),
                  "C audit output must be outside frozen inputs")
        if args.action=="verify-build":
            result=verify_build(repo,args.build.resolve())
        else:
            g.require(args.run is not None,"missing C run")
            result=audit_run(repo,args.build.resolve(),args.run.resolve())
        out.parent.mkdir(parents=True,exist_ok=True)
        g.save(out,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ("functions","rows","cases","inputs")},indent=2))
