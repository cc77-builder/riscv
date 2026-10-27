#!/usr/bin/env python3
"""Reconnect the qualified C8 SDK to the existing ordinary C fixture."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CONTRACT = "c8-existing-c-final-image-equivalence-v1"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pins_check(pins, aliases=()):
    for file, expected in pins.items():
        p = Path(file)
        require(p.is_file() and (not p.is_symlink() or file in aliases) and sha(p) == expected,
                "protected input changed: " + file)


def exact_tree(root, expected):
    actual = {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()}
    require(actual == expected, "sealed run tree differs: " + str(root))


def adapted_main(text):
    require(text.count('#include "gemv.h"') == 1, "main include anchor")
    return text.replace('#include "gemv.h"', '#include "selected_gemv_c8.h"')


def adapted_cases(text):
    result = text
    for suffix, alias in (("vdot", "xs_c8_gemv_8x32"), ("rvv", "xs_c8_gemv_8x32_rvv")):
        old = "config_reuse_gemv_8x32_reuse_" + suffix
        require(result.count(old) == 3, "exactly three dataset aliases required")
        result = result.replace(old, alias)
    return result


def plan_check(a, b):
    require(a == b, "case/input plan differs")


def allocated(elf):
    result = {}
    for name, s in elf.named.items():
        if not s[2] & 2:
            continue
        result[name] = {"type": s[1], "flags": s[2], "address": s[3], "bytes": s[5],
                        "alignment": s[8], "entry_size": s[9],
                        "sha256": None if s[1] == 8 else digest(elf.section(s))}
    return result


def loaded(elf):
    result = []
    for p in elf.segments:
        if p[0] != 1:
            continue
        _, flags, offset, va, pa, filesz, memsz, align = p
        require(0 <= filesz <= memsz and va == pa, "load ranges")
        elf.range(offset, filesz)
        result.append({"flags": flags, "virtual": va, "physical": pa, "file_bytes": filesz,
                       "memory_bytes": memsz, "zero_fill_bytes": memsz-filesz, "align": align,
                       "sha256": digest(elf.raw[offset:offset+filesz])})
    require(bool(result), "no loaded segments")
    return result


def compare_images(parser, original_raw, candidate_raw, original_bin, candidate_bin, plan):
    a, b = parser.ELF(original_raw), parser.ELF(candidate_raw)
    require(a.kind == b.kind == 2, "final ELF must be executable")
    require(a.entry == b.entry == 0x80000000, "boot entry differs")
    require(struct.unpack_from("<I", original_raw, 48) == struct.unpack_from("<I", candidate_raw, 48),
            "ELF ABI flags differ")
    require(not any(p[0] in (2, 3) for p in a.segments + b.segments), "dynamic/interpreter image")
    require(loaded(a) == loaded(b), "PT_LOAD bytes/ranges/permissions differ")
    require(allocated(a) == allocated(b), "allocated sections differ")
    require(a.binary() == original_bin and b.binary() == candidate_bin, "ELF reconstruction versus GNU BIN differs")
    require(original_bin == candidate_bin, "complete BIN differs")
    require(a.section(a.named[".riscv.attributes"]) == b.section(b.named[".riscv.attributes"]),
            "ISA attributes differ")
    for elf in (a, b):
        for name in ("_start", "main", "_trm_init", "_halt", "_putc"):
            require(name in elf.symbols, "missing runtime symbol")
    names = sorted({c["api_symbol"] for c in plan["cases"]})
    require(len(plan["cases"]) == 48 and len(names) == 16, "complete16-function48-case plan")
    anchors = []
    for name in ["_start", "main", "_trm_init", "_halt", "_putc", *names]:
        require(a.symbols[name][:2] == b.symbols[name][:2] and
                a.symbol_data(name) == b.symbol_data(name), "function address/bytes differ: " + name)
        anchors.append({"symbol": name, "address": a.symbols[name][0],
                        "bytes": a.symbols[name][1], "sha256": digest(a.symbol_data(name))})
    require(not any(n.startswith("xs_c8_") and s[1] > 0 for n, s in b.symbols.items()), "runtime wrapper")
    require(a.symbols["r4_c_cases"][:2] == b.symbols["r4_c_cases"][:2] and
            a.symbol_data("r4_c_cases") == b.symbol_data("r4_c_cases"), "call table differs")
    table = b.symbol_data("r4_c_cases")
    require(len(table) == 48 * 64, "call table size")
    inputs = {}
    for i, case in enumerate(plan["cases"]):
        row = struct.unpack_from("<8Q", table, i * 64)
        expected = (b.symbols[case["api_symbol"]][0], b.symbols[case["input_symbol"]][0],
                    case["m"], case["k"], case["size"], case["dataset"], case["api_index"], case["expected_hash"])
        require(row == expected, "final table does not match immutable plan: " + str(i))
        name = case["input_symbol"]
        require(a.symbols[name][:2] == b.symbols[name][:2] and
                a.symbol_data(name) == b.symbol_data(name), "input bytes/address differ")
        inputs[name] = {"address": b.symbols[name][0], "bytes": b.symbols[name][1],
                        "sha256": digest(b.symbol_data(name))}
    require(len(inputs) == 12, "three datasets for four shapes required")
    # All non-load program headers also retain their semantic descriptors/content.
    other_a = [p for p in a.segments if p[0] != 1]
    other_b = [p for p in b.segments if p[0] != 1]
    require(len(other_a) == len(other_b), "program header inventory")
    for x, y in zip(other_a, other_b):
        require(x[:2] + x[3:] == y[:2] + y[3:], "non-load segment semantics differ")
        require(a.raw[x[2]:x[2]+x[5]] == b.raw[y[2]:y[2]+y[5]], "non-load segment contents differ")
    require(set(a.named) == set(b.named), "section inventory differs")
    differences = []
    for name in a.named:
        x, y = a.named[name], b.named[name]
        if x[1] == 8 and y[1] == 8:
            continue
        if a.section(x) == b.section(y):
            continue
        require(not (x[2] | y[2]) & 2, "changed load section")
        require(name.startswith(".debug_") or name in (".symtab", ".strtab", ".shstrtab", ".comment"),
                "unexplained non-load section difference: " + name)
        differences.append({"section": name, "original_bytes": x[5], "candidate_bytes": y[5],
                            "original_sha256": digest(a.section(x)), "candidate_sha256": digest(b.section(y)),
                            "allocated": False})
    return {"status": "FINAL_LOADED_IMAGE_AND_PLAN_EQUIVALENT", "whole_elf_equal": original_raw == candidate_raw,
            "original_elf_sha256": digest(original_raw), "candidate_elf_sha256": digest(candidate_raw),
            "bin_sha256": digest(candidate_bin), "bin_bytes": len(candidate_bin), "entry": b.entry,
            "loads": loaded(b), "allocated_sections": allocated(b), "function_anchors": anchors,
            "table_cases": 48, "table_sha256": digest(table), "inputs": inputs,
            "nonload_differences": differences, "new_runtime_required": False}


def verify_inputs(repo, identity, matrix, c8, package, output):
    pinned = read(HERE / "INPUTS.json")
    roles = dict(package_report=package/"report.json",
        package_qualification=package/"qualification/qualification.json",
        package_source_inputs=package/"source-inputs.json",
        matrix_audit=package/"qualification/matrix-raw-audit.json",
        c8_audit=package/"qualification/c8-raw-audit.json",
        package_input_pins=HERE.parent/"INPUTS.json", c8_build=c8/"build-01/build.json",
        case_manifest=c8/"build-01/source/manifest.json", sdk_manifest=package/"sdk/manifest.json",
        elf_parser=repo/"team/optimizations/o2/r2-safe-tail/linked_gate.py")
    require(set(roles) == set(pinned["roles"]), "role inventory")
    for role, path in roles.items():
        require(sha(path) == pinned["roles"][role]["sha256"] and
                path.stat().st_size == pinned["roles"][role]["bytes"], "pinned role changed: " + role)
    report, q = read(roles["package_report"]), read(roles["package_qualification"])
    require(report["status"] == "CURRENT_C8_MINIMAL_PACKAGE_STATIC_PASS" and
            report["qualification"] == q, "package qualification binding")
    qualification = load("c8_relink_existing_qualification", HERE.parent/"qualification.py")
    current = read(identity)
    require(qualification.validate_identity(current) == q["current_identity"], "current physical identity differs")
    tools = qualification.toolchain(read(roles["package_input_pins"]))
    require(tools == q["toolchain"], "toolchain qualification changed")
    aliases = [item["path"] for item in tools.values() if item["link_text"] is not None]
    closure = {}
    for item in q["input_roles"].values():
        require(sha(item["path"]) == item["sha256"], "role closure changed")
        closure[item["path"]] = item["sha256"]
    for file in (c8/"outer-inputs.json", c8/"run-01/runtime-inputs.json", matrix/"run-01/runtime-inputs.json"):
        values = read(file)
        qualification.verify_map(values, aliases)
        closure.update(values)
    physical = read(c8/"identity-before.json")
    require(physical[0] == current and physical[2] == current["hardware_profile"], "original physical identity")
    closure.update(physical[1])
    qualification.verify_map(closure, aliases)
    for auditfile, root, key in ((roles["matrix_audit"], matrix/"run-01", "campaign_evidence_sha256"),
                                (roles["c8_audit"], c8/"run-01", "campaign_files")):
        audit = read(auditfile)
        exact_tree(root, audit[key])
        closure.update({str(root/rel): value for rel, value in audit[key].items()})
    qualification.validate_selection(read(matrix/"run-01/results.json"), read(c8/"run-01/current-c-qualification.json"))
    source_pins = read(roles["package_source_inputs"])
    pins_check(source_pins)
    closure.update(source_pins)
    sdk = package/"sdk"
    manifest = read(roles["sdk_manifest"])
    actual = {str(p.relative_to(sdk)):sha(p) for p in sdk.rglob("*") if p.is_file() and p.name != "manifest.json"}
    require(actual == manifest["files"], "SDK inventory or bytes changed")
    closure.update({str(sdk/rel):value for rel,value in actual.items()})
    for role, path in roles.items():
        closure[str(path)] = sha(path)
    build = read(roles["c8_build"])
    for rel, expected in build["artifacts"].items():
        require(sha(c8/"build-01"/rel) == expected, "qualified build artifact changed")
        closure[str(c8/"build-01"/rel)] = expected
    require(build["artifacts"]["vdot-perf.bin"] == pinned["prior_bin_sha256"] and
            build["artifacts"]["vdot-perf.elf"] == pinned["prior_elf_sha256"], "old image identity")
    package_checker = load("c8_relink_package_checker", HERE.parent/"verify_c8_package.py")
    obj = (c8/"build-01/gemv-reference.o").read_bytes()
    package_checker.check_archive(sdk/"libxs_gemv_c8.a", obj)
    require((c8/"build-01/objects/gemv.o").read_bytes() == obj, "original application object differs")
    closure[str(c8/"build-01/objects/gemv.o")] = digest(obj)
    for f in (c8/"build-01/source").iterdir():
        if f.is_file():
            closure[str(f)] = sha(f)
    output.mkdir()
    save(output/"protected-inputs.json", closure)
    summary = {"status":"SEALED_C8_PACKAGE_AND_PRIOR_RAW_EVIDENCE_REVALIDATED",
               "evidence_mode":"Complete current inputs plus unchanged sealed33+3 raw audit trees; no redundant raw parse",
               "protected_files":len(closure), "prior_matrix_processes":33, "prior_c_processes":3,
               "identity":q["current_identity"], "new_emu_runs":0, "new_nemu_runs":0}
    save(output/"report.json", summary)
    return tools, current, closure, summary


def main(args):
    repo, identity, matrix, c8, package, out = [p.resolve() for p in
        (args.repo,args.identity,args.matrix,args.c8,args.package,args.output)]
    require(not out.exists(), "fresh output required")
    for root in (repo,identity.parent.parent,matrix,c8,package):
        require(not out.is_relative_to(root) and not root.is_relative_to(out), "output overlaps protected input")
    os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    out.mkdir(parents=True)
    state = {"contract":CONTRACT,"status":"RUNNING","started":now(),"new_emu_runs":0,"new_nemu_runs":0}
    save(out/"state.json",state)
    commands=[]
    env=dict(os.environ)
    for key in ("CFLAGS","CPPFLAGS","CXXFLAGS","ASFLAGS","LDFLAGS","CC_OPT","MAKEFLAGS","MFLAGS","CC","AS","LD",
                "OBJCOPY","OBJDUMP","ARCH","MARCH","LIBS","PREBUILD","CPATH","C_INCLUDE_PATH","CPLUS_INCLUDE_PATH",
                "GCC_EXEC_PREFIX","COMPILER_PATH","LIBRARY_PATH","C8_SDK","R4_LINK_MAP"):
        env.pop(key,None)
    env.update(LC_ALL="C",LANG="C")

    def run(folder,label,argv,success=True,cwd=None):
        folder.mkdir(parents=True,exist_ok=True)
        require(not (folder/(label+".command.json")).exists(),"fresh receipt")
        before=now()
        proc=subprocess.run([str(x) for x in argv],cwd=cwd or out,env=env,capture_output=True,timeout=180)
        for stream in ("stdout","stderr"):
            (folder/(label+"."+stream+".log")).write_bytes(getattr(proc,stream))
        receipt={"command":[str(x) for x in argv],"cwd":str(cwd or out),"started":before,"finished":now(),
                 "exit_code":proc.returncode,"expected_success":success,"stdout_sha256":digest(proc.stdout),
                 "stderr_sha256":digest(proc.stderr)}
        save(folder/(label+".command.json"),receipt)
        commands.append(str((folder/(label+".command.json")).relative_to(out)))
        require((proc.returncode==0)==success,"command failed: "+str(folder/label))
        return proc.stdout

    try:
        tools,current,protected,binding=verify_inputs(repo,identity,matrix,c8,package,out/"qualification")
        parser=load("c8_relink_elf_parser",repo/"team/optimizations/o2/r2-safe-tail/linked_gate.py")
        own={str(p):sha(p) for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        am=Path(current["configuration"]["am_home"])
        require(subprocess.check_output(["git","rev-parse","HEAD"],cwd=am,text=True).strip()==read(c8/"build-01/build.json")["am_revision"],
                "AM revision differs")
        require(not subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=am,text=True).strip(),
                "AM tracked sources dirty")
        env.update(AM_HOME=str(am),LINUX_GNU_TOOLCHAIN="1")
        sdk=out/"sdk"
        shutil.copytree(package/"sdk",sdk)
        sdk_files={str(f.relative_to(sdk)):sha(f) for f in sdk.rglob("*") if f.is_file()}
        require(sdk_files=={str(f.relative_to(package/"sdk")):sha(f) for f in (package/"sdk").rglob("*") if f.is_file()},
                "copied SDK differs")
        original=c8/"build-01"
        source=original/"source"
        plan=read(source/"manifest.json")
        plan_check(plan,read(c8/"qualified-public/manifest.json"))
        generated={}
        make_trace="\n# Record member provenance without changing compiler/linker semantics.\nLDFLAGS += -Map=$(R4_LINK_MAP) --trace\n"
        for name in ("control","integrated"):
            root=out/name
            (root/"source").mkdir(parents=True)
            if name=="control":
                for file in ("main.c","gemv.S","gemv.h","cases.h","manifest.json","Makefile"):
                    shutil.copyfile(source/file,root/"source"/file)
                with (root/"source/Makefile").open("a") as f:f.write(make_trace)
            else:
                (root/"source/main.c").write_text(adapted_main((source/"main.c").read_text()))
                (root/"source/cases.h").write_text(adapted_cases((source/"cases.h").read_text()))
                shutil.copyfile(source/"manifest.json",root/"source/manifest.json")
                make=(source/"Makefile").read_text()
                require(make.count("SRCS = main.c gemv.S")==1,"source Makefile anchor")
                make=make.replace("SRCS = main.c gemv.S","SRCS = main.c")
                make=make.replace("INC_DIR += $(CURDIR)","INC_DIR += $(CURDIR) $(C8_SDK)/include")
                make+="\n# Replace only the old GEMV object slot with the complete C8 archive.\n"
                make+="LINK_FILES = $(OBJS) $(C8_SDK)/libxs_gemv_c8.a $(AM_HOME)/am/build/am-$(ARCH).a $(AM_HOME)/libs/klib/build/klib-$(ARCH).a\n"
                (root/"source/Makefile").write_text(make+make_trace)
            plan_check(read(root/"source/manifest.json"),plan)
            args_make=[tools["make"]["path"],"--trace","-C",root/"source","ARCH=riscv64-xs","MARCH=rv64gcv",
                "CROSS_COMPILE="+str(Path(tools["gcc"]["path"]))[:-3],
                "R4_OBJ_ROOT="+str(root/"objects"),"BINARY="+str(root/"vdot-perf"),
                "R4_LINK_MAP="+str(root/"link.map"),"-o","am","-o","klib","-j1","image"]
            if name=="integrated":args_make.append("C8_SDK="+str(sdk))
            run(root/"commands","make",args_make)
            require(not run(root/"commands","undefined",[tools["nm"]["path"],"-u",root/"vdot-perf.elf"]).strip(),
                    "final unresolved symbols")
            run(root/"commands","readelf",[tools["readelf"]["path"],"-hlSW",root/"vdot-perf.elf"])
            generated[name]={"artifacts":{n:sha(root/n) for n in ("vdot-perf.elf","vdot-perf.bin","link.map")},
                             "sources":{str(f.relative_to(root/"source")):sha(f) for f in (root/"source").iterdir() if f.is_file()}}
        require(not (out/"integrated/objects/gemv.o").exists() and not (out/"integrated/source/gemv.S").exists(),
                "integrated build contains bypass object/source")
        linkmap=(out/"integrated/link.map").read_text()
        require(str(sdk/"libxs_gemv_c8.a")+"(gemv.o)" in linkmap,"archive member not proven extracted")
        require(str(out/"integrated/objects/main.o") in linkmap,"actual caller missing from link map")
        trace=(out/"integrated/commands/make.stdout.log").read_text()
        linkline=[line for line in trace.splitlines() if "--start-group" in line and "riscv64-linux-gnu-ld" in line]
        require(len(linkline)==1 and str(sdk/"libxs_gemv_c8.a") in linkline[0] and
                "/objects/gemv.o" not in linkline[0],"actual GNU link did not use SDK")
        deps=(out/"integrated/objects/main.d").read_text()
        require(str(sdk/"include/selected_gemv_c8.h") in deps and str(sdk/"include/config_reuse_gemv.h") in deps,
                "actual compiler did not include SDK headers")
        old_raw=(original/"vdot-perf.elf").read_bytes()
        old_bin=(original/"vdot-perf.bin").read_bytes()
        checks={}
        for name in ("control","integrated"):
            checks[name]=compare_images(parser,old_raw,(out/name/"vdot-perf.elf").read_bytes(),
                                        old_bin,(out/name/"vdot-perf.bin").read_bytes(),plan)
            save(out/name/"equivalence.json",checks[name])
        # Check ELF semantics and equality against both old and independently rebuilt control.
        checks["control_vs_integrated"]=compare_images(parser,(out/"control/vdot-perf.elf").read_bytes(),
            (out/"integrated/vdot-perf.elf").read_bytes(),(out/"control/vdot-perf.bin").read_bytes(),
            (out/"integrated/vdot-perf.bin").read_bytes(),plan)
        save(out/"control-vs-integrated.json",checks["control_vs_integrated"])
        # Preserve real wrong-candidate bytes and ensure the comparator rejects them.
        negative=[]
        base=(out/"integrated/vdot-perf.elf").read_bytes()
        elf=parser.ELF(base)
        def reject(label,operation,file=None):
            try:operation()
            except ValueError as exc:
                negative.append({"case":label,"rejected":True,"reason":str(exc),
                                 "candidate_sha256":sha(file) if file else None})
            else:raise ValueError("negative accepted: "+label)
        for label in ("text-byte","call-table","boot-entry","bss-size","isa-attributes"):
            bad=bytearray(base)
            if label=="text-byte":offset=elf.named[".text"][4]+8;bad[offset]^=1
            elif label=="call-table":
                addr=elf.symbols["r4_c_cases"][0]
                s=elf.sections[elf.symbols["r4_c_cases"][2]]
                offset=s[4]+addr-s[3];bad[offset]^=4
            elif label=="boot-entry":struct.pack_into("<Q",bad,24,elf.entry+4)
            elif label=="isa-attributes":bad[elf.named[".riscv.attributes"][4]+20]^=1
            else:
                idx=elf.sections.index(elf.named[".bss"])
                shoff=struct.unpack_from("<Q",bad,40)[0]
                struct.pack_into("<Q",bad,shoff+64*idx+32,elf.named[".bss"][5]+16)
            file=out/"negative"/(label+".elf");file.parent.mkdir(exist_ok=True);file.write_bytes(bad)
            reject(label,lambda:compare_images(parser,old_raw,bytes(bad),old_bin,old_bin,plan),file)
        wrong_plan=json.loads(json.dumps(plan));wrong_plan["cases"][0]["dataset"]=2
        save(out/"negative/wrong-plan.json",wrong_plan)
        reject("input-plan",lambda:plan_check(plan,wrong_plan),out/"negative/wrong-plan.json")
        # GNU ld with an unrelated empty archive must fail final linking.
        d=out/"negative/wrong-library";d.mkdir()
        run(d,"archive",[tools["ar"]["path"],"rcsD",d/"empty.a"])
        original_args=linkline[0].strip()
        import shlex
        argv=shlex.split(original_args)
        argv=[str(d/"empty.a") if item==str(sdk/"libxs_gemv_c8.a") else
              str(d/"wrong.elf") if item==str(out/"integrated/vdot-perf.elf") else
              "-Map="+str(d/"wrong.map") if item=="-Map="+str(out/"integrated/link.map") else item
              for item in argv]
        run(d,"link",argv,success=False,cwd=out/"integrated/source")
        negative.append({"case":"wrong-library-final-link","compiler_rejected":True})
        # An actual debug byte change must not be misreported as changed executable behavior.
        harmless=bytearray(base);harmless[elf.named[".debug_str"][4]]^=1
        positive=compare_images(parser,old_raw,bytes(harmless),old_bin,old_bin,plan)
        save(out/"nonload-positive.json",{"status":positive["status"],"difference":".debug_str-only",
                                        "whole_elf_equal":False})
        pins_check(protected,[item["path"] for item in tools.values() if item["link_text"] is not None])
        pins_check(own)
        require(sdk_files=={str(f.relative_to(sdk)):sha(f) for f in sdk.rglob("*") if f.is_file()},"SDK changed during build")
        # Protect actual compiler dependencies and platform linker scripts in the result.
        dependency_paths=set()
        for name in ("control","integrated"):
            text=(out/name/"objects/main.d").read_text().replace("\\\n"," ")
            for token in text.split(":",1)[1].split():
                path=Path(token)
                if not path.is_absolute():path=out/name/"source"/path
                require(path.is_file(),"compiler dependency missing")
                dependency_paths.add(path.resolve())
        for rel in ("Makefile.app","Makefile.check","Makefile.compile","am/arch/riscv64-xs.mk",
                    "am/arch/isa/riscv64.mk","am/src/nemu/isa/riscv/boot/loader64.ld"):
            dependency_paths.add(am/rel)
        save(out/"build-dependencies.json",{str(path):sha(path) for path in sorted(dependency_paths)})
        save(out/"source-inputs.json",own)
        report={**state,"status":"C8_EXISTING_C_FINAL_IMAGE_EQUIVALENCE_PASS","finished":now(),
                "binding":binding,"builds":generated,"comparisons":checks,"negative_controls":negative,
                "nonload_positive":True,"command_receipts":commands,"toolchain":tools,
                "runtime_evidence":"REUSED_SAME_LOADED_IMAGE_AND_PLAN_RECORD26",
                "prior_functional_record":"CONFIG-REUSE-C8-DIVFIX0F-CLEAN02-20261027-02",
                "prior_package_record":"C8-PACKAGE-DIVFIX0F-CLEAN02-20261027-01",
                "new_fullcore_runs":0,"new_performance":"NOT_TESTED","new_ppa":"NOT_TESTED",
                "default_changed":False,"hardware_changed":False,"github_uploaded":False}
        save(out/"report.json",report)
        state.update(status=report["status"],finished=report["finished"],report_sha256=sha(out/"report.json"))
        save(out/"state.json",state)
        print(json.dumps({"status":report["status"],"bin_sha256":checks["integrated"]["bin_sha256"],
            "whole_elf_equal":checks["integrated"]["whole_elf_equal"],
            "metadata_differences":[x["section"] for x in checks["integrated"]["nonload_differences"]],
            "negative_controls":len(negative),"new_emu_runs":0}))
        return report
    except BaseException as exc:
        state.update(status="FAILED",error=repr(exc),finished=now())
        save(out/"state.json",state)
        raise


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ("repo","identity","matrix","c8","package","output"):
        parser.add_argument("--"+flag,type=Path,required=True)
    main(parser.parse_args())
