"""Targeted rejection tests on copies of actual GNU artifacts and raw logs.

No build or EMU is started. Original evidence is read only. Mutated identities
are made internally consistent where needed so deeper checks are exercised.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import struct
import tempfile

import experiment as e
import pathcheck
g=e.g

def patch_word(raw, address, word):
    """Change an allocated ELF word without relying on unique byte patterns."""
    raw=bytearray(raw)
    shoff=struct.unpack_from("<Q",raw,40)[0]
    size,count=struct.unpack_from("<HH",raw,58)
    for i in range(count):
        section=struct.unpack_from("<IIQQQQIIQQ",raw,shoff+i*size)
        if section[2]&2 and section[1]!=8 and section[3]<=address and address+4<=section[3]+section[5]:
            struct.pack_into("<I",raw,section[4]+address-section[3],word)
            return bytes(raw)
    raise ValueError("test address outside ELF allocated file data")

def run(build, runtime=None):
    results=[]
    positive=e.verification(e.ROOT,build)
    def reject(name, fn, message):
        try: fn()
        except ValueError as exc:
            g.require(message in str(exc),"wrong rejection gate for "+name+": "+str(exc))
            results.append(dict(name=name,status="EXPECTED_REJECTION",gate=str(exc)))
        else: raise ValueError("mutation was accepted: "+name)
    with tempfile.TemporaryDirectory(prefix="caller-rejections-") as temp:
        root=Path(temp)
        copy=root/"build";shutil.copytree(build,copy)
        original=e.read(copy/"build.json")
        elf_raw=(copy/"vdot-perf.elf").read_bytes();elf=g.ELF(elf_raw)
        # An unused public leaf still has to be frozen. Refresh ELF/BIN hashes
        # so this test reaches the complete leaf check, not the generic hash gate.
        unused="config_reuse_gemv_4x13_basic_vdot"
        address=elf.symbols[unused][0]
        modified=patch_word(elf_raw,address,0x00000013)
        (copy/"vdot-perf.elf").write_bytes(modified)
        (copy/"vdot-perf.bin").write_bytes(g.ELF(modified).binary())
        receipt=deepcopy(original)
        for name in ("vdot-perf.elf","vdot-perf.bin"):receipt["artifacts"][name]=g.sha(copy/name)
        g.save(copy/"build.json",receipt)
        reject("unused-public-leaf",lambda:e.verification(e.ROOT,copy),"caller changed qualified leaf")
        (copy/"vdot-perf.elf").write_bytes(elf_raw)
        shutil.copyfile(build/"vdot-perf.bin",copy/"vdot-perf.bin")
        # Both copies of a command receipt agree, but the resource/command
        # contract does not. This must not be accepted as a valid rebuild.
        receipt=deepcopy(original)
        cmd=receipt["commands"][0];cmd["command"][cmd["command"].index("-j4")]="-j5"
        g.save(copy/"build.json",receipt);g.save(copy/"make-command/command.json",cmd)
        reject("self-consistent-wrong-build-command",lambda:e.verification(e.ROOT,copy),"caller command/log identity")
        # Retain required flags and add an overriding flag on caller.c only.
        receipt=deepcopy(original)
        log=(copy/"make-command/stdout.log").read_text()
        source=str(Path(receipt["build_root"])/"source/caller.c")
        lines=log.splitlines()
        changed=0
        for i,line in enumerate(lines):
            if line.startswith(receipt["toolchain"]["gcc"]["path"]+" ") and line.endswith(source):
                lines[i]=line.replace(" -c -o "," -flto=auto -c -o ");changed+=1
        g.require(changed==1,"test actual caller compiler command not unique")
        (copy/"make-command/stdout.log").write_text("\n".join(lines)+"\n")
        receipt["commands"][0]["raw_sha256"]["stdout.log"]=g.sha(copy/"make-command/stdout.log")
        g.save(copy/"build.json",receipt);g.save(copy/"make-command/command.json",receipt["commands"][0])
        reject("caller-only-conflicting-lto",lambda:e.verification(e.ROOT,copy),"conflicting actual C option: caller")
        # Exercise scalar coverage directly; no artifact identity check is on
        # this path. The first byte store in the real packing loop is removed.
        raw=elf.symbol_data("caller_full")
        at=next(i for i in range(0,len(raw),4) if (int.from_bytes(raw[i:i+4],"little")&0x707f)==0x23)
        bad=g.ELF(patch_word(elf_raw,elf.symbols["caller_full"][0]+at,0x00000013))
        packed=bytes(e.read(build/"source/manifest.json")["inputs"][0])
        reject("missing-real-pack-store",lambda:pathcheck.path(bad,0,"vdot",packed),"compiled pack write coverage")
        # An unbounded branch must be rejected rather than traced from DUT.
        at=next(i for i in range(0,len(raw),4) if int.from_bytes(raw[i:i+4],"little")&127==0x63)
        bad=g.ELF(patch_word(elf_raw,elf.symbols["caller_full"][0]+at,0x00000063))
        reject("unbounded-real-c-loop",lambda:pathcheck.path(bad,0,"vdot",packed),"caller path exceeded finite budget")
        if runtime:
            checker=g.load("caller_rejection_checker",Path(__file__).with_name("check.py"))
            normal=runtime/"runs/recovery"
            rec=e.read(normal/"result.json")
            checker.normal(e.ROOT,build,normal,rec)
            mutated=root/"run";mutated.mkdir()
            shutil.copyfile(normal/"stdout.log",mutated/"stdout.log")
            original_log=(normal/"stderr.log").read_text()
            import re
            pattern=r"(T13_COUNTER_ENQUEUE cycle=\s*\d+ rob=\d+:\s*)(\d+)"
            text,count=re.subn(pattern,lambda m:m[1]+str(int(m[2])+1),original_log,count=1)
            g.require(count==1,"test counter enqueue not found")
            (mutated/"stderr.log").write_text(text)
            reject("counter-rob-mismatch",lambda:checker.normal(e.ROOT,build,mutated,rec),"counter identity mismatch")
            # Preserve the static path, instret sum and counter values, while
            # combining a real adjacent AUIPC/JALR into one retirement record.
            counter=g.load("caller_rejection_counter",e.ROOT/"team/workloads/unified-vdot/check.py")
            lines=original_log.splitlines(keepends=True);chosen=None
            retire=[]
            window=-1;active=False
            for i,line in enumerate(lines):
                if line.startswith("T13_RETIRE "):
                    row=counter.parse_events(line)["RETIRE"][0]
                    if row["word"]==pathcheck.START:window+=1;active=True
                    if active:row["window"]=window;retire.append((i,row))
                    if row["word"]==pathcheck.STOP:active=False
            for (i,a),(j,b) in zip(retire,retire[1:]):
                if a["window"]==b["window"] and a["word"]&127==0x17 and b["word"]&127==0x67 and a["count"]==b["count"]==1 and b["pc"]==a["pc"]+4:
                    chosen=(i,j);break
            g.require(chosen is not None,"test real AUIPC/JALR pair missing")
            i,j=chosen;g.require(lines[i].count(" count=1 ")==1,"test retirement count not unique")
            lines[i]=lines[i].replace(" count=1 "," count=2 ");lines[j]=""
            (mutated/"stderr.log").write_text("".join(lines))
            reject("call-hidden-by-rob-compression",lambda:checker.normal(e.ROOT,build,mutated,rec),"control hidden in ROB compression")
    return dict(status="CALLER_REJECTION_TESTS_PASS",contract=e.CONTRACT,build_sha256=g.sha(build/"build.json"),
                selftest_sha256=g.sha(__file__),positive_image=positive["image_sha256"],cases=results,
                rejected=len(results),new_emu_runs=0,original_evidence_modified=False)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build",type=Path,required=True);p.add_argument("--run",type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();build=args.build.resolve();out=args.output.resolve()
    g.require(not out.exists(),"selftest output must be new")
    identity=e.ROOT/e.parent.REPRO/"evidence/clean-reproduction-v1/reports/identity-02.json"
    cfg=e.parent.parent_identity(e.ROOT,identity)["configuration"]
    e.parent.outside_inputs(out,[e.ROOT,build,identity.parent]+[cfg[k] for k in ("am_home","hardware_source","build_record")]+
                            ([args.run.resolve()] if args.run else []))
    result=run(build,args.run.resolve() if args.run else None)
    g.save(out,result);print(json.dumps(result,indent=2))
