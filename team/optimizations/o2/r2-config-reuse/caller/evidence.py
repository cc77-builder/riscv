"""Seal and independently recheck caller evidence without rerunning an EMU."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

import experiment as e
g=e.g

def time_range(record):
    start,finish=(datetime.fromisoformat(record[n]) for n in ("started","finished"))
    g.require(start.tzinfo and finish.tzinfo and start<=finish,"caller receipt timeline")
    return start,finish

def audit(build,run):
    """Recompute raw results and their exact input/command/receipt closure.

    This checks sealed identities, not the current physical external files.
    The original run separately checked its physical inputs before and after.
    """
    repo=e.ROOT
    valid=e.verification(repo,build);br=e.read(build/"build.json")
    g.require(br["accepted"] is True and e.read(build/"elf-validation.json")==valid,"caller cached build result")
    first,last=time_range(br)
    g.require(first<=time_range(br["commands"][0])[0] and time_range(br["commands"][-1])[1]<=last and
        all(time_range(a)[1]<=time_range(b)[0] for a,b in zip(br["commands"],br["commands"][1:])),"caller build command chronology")
    identity=run/"parent-identity.json"
    ident=e.parent.parent_identity(repo,identity)
    cfg=ident["configuration"]
    g.require(e.read(run/"configuration.json")==cfg and br["am_home"]==cfg["am_home"],"caller archived configuration")
    g.require(e.read(run/"hardware-profile.json")==ident["hardware_profile"],"caller archived hardware profile")
    f,m=e.parent.runtime(repo,ident)
    p=e.parent.t17.p
    source,original_build=map(PurePosixPath,(br["source_root"],br["build_root"]))
    hardware,record=PurePosixPath(cfg["hardware_source"]),PurePosixPath(cfg["build_record"])
    expected={str(record/n):sha for n,sha in ident["metadata_sha256"].items()}
    expected.update({str(hardware/"build"/n):sha for n,sha in p.AUX.items()})
    expected.update({str(hardware/"build/emu"):ident["hardware_profile"]["emu_sha256"],
        cfg["reference"]:ident["reference_sha256"],cfg["flash"]:ident["flash_sha256"],
        str(hardware/"team/optimizations/o2/fullcore/build_fullcore.py"):p.HELPER,cfg["build_driver"]:p.BUILDER})
    expected.update({str(source/rel):sha for rel,sha in e.sources(repo).items()})
    expected.update({str(source/Path(path).relative_to(repo).as_posix()):sha for path,sha in m.checker_files(repo).items()})
    # The original identity may have been selected through an arbitrary path;
    # all other common inputs have an exact canonical inventory.
    common=e.read(run/"runtime-inputs.json")
    identity_paths=[path for path,sha in common.items() if sha==e.parent.PARENT_IDENTITY_SHA]
    g.require(len(identity_paths)==1,"caller parent identity input inventory")
    expected[identity_paths[0]]=e.parent.PARENT_IDENTITY_SHA
    for name in ("build.json","elf-validation.json","vdot-perf.elf","vdot-perf.bin","gemv-reference.o"):
        expected[str(original_build/name)]=g.sha(build/name)
    for name in e.GENERATED: expected[str(original_build/"source"/name)]=g.sha(build/"source"/name)
    expected.update(br["external_files"])
    expected.update({t["path"]:t["sha256"] for t in br["toolchain"].values()})
    g.require(common==expected,"caller complete archived common input inventory")
    fixture=e.read(run/"negative-fixture/fixture.json")
    g.require(fixture["source_sha256"]==m.NEGATIVE_SHA and fixture["normal_reference_sha256"]==ident["reference_sha256"] and
        fixture["historical_negative_hash_claim"] is False and
        g.sha(run/"negative-fixture/negative-fixture.c")==m.NEGATIVE_SHA and
        g.sha(run/"negative-fixture/negative-reference.so")==fixture["negative_sha256"],"caller negative fixture identity")
    fixture_commands=[e.read(run/"negative-fixture"/label/"command.json") for label in ("compiler","compile","linkage")]
    fixture_command=fixture_commands[1]
    for label,cmd in zip(("compiler","compile","linkage"),fixture_commands):
        g.require(cmd.get("process_started") is True and type(cmd.get("pid")) is int and cmd["pid"]>0 and
            cmd.get("exit_code")==0 and not cmd.get("timed_out") and cmd["raw_sha256"]==
            {n:g.sha(run/"negative-fixture"/label/n) for n in ("stdout.log","stderr.log")},"caller negative fixture command receipt")
    g.require(fixture_command["command"]==fixture["command"] and
        'Shared library: ['+cfg["reference"]+']' in (run/"negative-fixture/linkage/stdout.log").read_text(),
        "caller negative fixture normal reference dependency")
    checker=g.load("caller_archive_check",Path(__file__).with_name("check.py"))
    suite=g.load("caller_archive_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
    records=[];outputs=[];original_run=None
    g.require({d.name for d in (run/"runs").iterdir()}=={"negative","recovery","replay"},"caller complete run inventory")
    for label in ("negative","recovery","replay"):
        directory=run/"runs"/label;rec=e.read(directory/"result.json");negative=label=="negative"
        cwd=PurePosixPath(rec["cwd"])
        g.require(cwd.name=="cwd" and cwd.parent.name==label and cwd.parent.parent.name=="runs","caller canonical run path")
        run_root=cwd.parent.parent.parent
        original_run=run_root if original_run is None else original_run
        g.require(original_run==run_root,"caller mixed run roots")
        reference=fixture["binary"] if negative else cfg["reference"]
        wanted=dict(common);wanted.update({str(cwd/"build"/n):sha for n,sha in m.AUX.items()})
        for name,sha in m.AUX.items():g.require(g.sha(directory/"cwd/build"/name)==sha,"caller archived auxiliary bytes")
        if negative:wanted[reference]=fixture["negative_sha256"]
        argv=[str(hardware/"build/emu"),"-i",str(original_build/"vdot-perf.bin"),"--flash="+cfg["flash"],
              "--ram-size=128MB","--diff="+reference,"--max-cycles="+str(e.MAX_CYCLES),"--seed=1"]
        g.require(rec["contract"]==e.CONTRACT and rec["name"]==label and rec["negative"] is negative and
            rec["image_sha256"]==valid["image_sha256"] and rec["reference"]==reference and rec["command"]==argv and
            rec["files"]==wanted and rec["environment_overrides"]=={"XS_NEGATIVE_VECTOR_TARGET":"vdot" if negative else None} and
            rec.get("process_started") is True and type(rec.get("pid")) is int and rec["pid"]>0 and
            rec.get("exit_code")==int(negative) and not rec.get("timed_out") and
            rec["status"]==("EXPECTED_VDOT_HIGHBIT_REJECTION" if negative else "CALLER_DIFFTEST_COUNTER_PATH_PASS"),
            "caller actual execution receipt")
        g.require(rec["raw_sha256"]=={n:g.sha(directory/n) for n in ("stdout.log","stderr.log")},"caller original raw log hashes")
        suite.validate_runtime((directory/"stdout.log").read_text()+(directory/"stderr.log").read_text(),reference)
        if negative:
            with tempfile.TemporaryDirectory(prefix="caller-negative-recheck-") as temp:
                copy=Path(temp)
                for name in ("stdout.log","stderr.log"):shutil.copyfile(directory/name,copy/name)
                detail=m.negative_check(repo,build,copy,rec)
                g.require(detail==rec["negative_details"]==e.read(directory/"negative.json") and
                    e.read(copy/"observation.json")==e.read(directory/"observation.json"),"caller negative raw recheck")
                elf=g.ELF((build/"vdot-perf.elf").read_bytes());leaf="config_reuse_gemv_8x32_reuse_vdot"
                raw=elf.symbol_data(leaf)
                pc=elf.symbols[leaf][0]+next(i for i in range(0,len(raw),4) if int.from_bytes(raw[i:i+4],"little")&0xfe00707f==0x0200000b)
                g.require(detail["vd"]==0 and detail["bit"]==100 and int(detail["pc"],16)==pc and detail["word"]=="0x0388000b", "caller actual first vdot negative target")
        else:
            checked=checker.normal(repo,build,directory,rec)
            g.require(checked==e.read(directory/"validation.json") and rec["validation_sha256"]==g.sha(directory/"validation.json"),
                      "caller cached normal validation differs from raw evidence")
            outputs.append(checked)
        records.append(rec)
    state=e.read(run/"state.json");cached=e.read(run/"results.json")
    fixture_root=original_run/"negative-fixture"
    expected_fixture=[fixture["command"][0],"-shared","-fPIC","-O2",'-DREF_SO="'+cfg["reference"]+'"',
        str(fixture_root/"negative-fixture.c"),"-Wl,--no-as-needed",cfg["reference"],"-ldl","-o",str(fixture_root/"negative-reference.so")]
    g.require(fixture["binary"]==str(fixture_root/"negative-reference.so") and fixture["command"]==expected_fixture and
        all(cmd["cwd"]==str(fixture_root) for cmd in fixture_commands) and
        fixture_commands[0]["command"]==[expected_fixture[0],"--version"] and
        fixture_commands[2]["command"]==[fixture_commands[2]["command"][0],"-d",fixture["binary"]],
        "caller negative fixture selected source/output/reference")
    g.require(state["contract"]==e.CONTRACT and state["status"]=="CALLER_CAMPAIGN_PASS" and state["new_emu_runs"]==3 and
        state["active_pid"] is None and state["active_result"] is None and isinstance(state["operation_id"],str) and
        state["operation_id"].strip() and len({r["pid"] for r in records})==3,"caller closed campaign")
    g.require(outputs[0]==outputs[1] and cached==dict(contract=e.CONTRACT,records=records,validation=outputs[0]) and
        e.read(run/"completed-runs.json")==records,"caller recovery/replay and complete cached result")
    start,end=time_range(state)
    g.require(time_range(br)[1]<=start<=time_range(fixture_commands[0])[0] and
        all(time_range(a)[1]<=time_range(b)[0] for a,b in zip(fixture_commands,fixture_commands[1:])) and
        time_range(fixture_commands[-1])[1]<=time_range(records[0])[0] and
        time_range(records[-1])[1]<=end and
        all(time_range(a)[1]<=time_range(b)[0] for a,b in zip(records,records[1:])),"caller serial process chronology")
    return dict(status="CALLER_RAW_EVIDENCE_AUDIT_PASS",contract=e.CONTRACT,image_sha256=valid["image_sha256"],
        original_emu_runs=3,new_emu_runs=0,physical_external_inputs_revalidated=False,
        windows_per_normal_run=144,formal_windows_used=96,replay_windows=144,
        ordinary_stack_demo_calls_per_normal_run=3,summary=outputs[0]["summary"],
        raw_sources_recomputed=True,stable_default_changed=False,hardware_changed=False)

def pack(build,run,out):
    result=audit(build,run)
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    with zipfile.ZipFile(out/"payload.zip","x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as payload:
        for role,root in (("build",build),("run",run)):
            for file in sorted(root.rglob("*")):
                g.require(not file.is_symlink(),"symlink in caller evidence")
                if not file.is_file() or "__pycache__" in file.parts:continue
                rel=file.relative_to(root)
                # The linked ELF/BIN/reference object and actual command logs
                # are retained. Temporary .o/.d and duplicate disassembly are not.
                if role=="build" and (rel.parts[0]=="objects" or str(rel)=="vdot-perf.txt"):continue
                if role=="run" and "cwd" in rel.parts and not (rel.parent.name=="build" and file.name in e.parent.t17.p.AUX):continue
                raw=file.read_bytes();name=role+"/"+rel.as_posix()
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.create_system=3
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                payload.writestr(info,raw,compresslevel=9)
                rows.append(dict(path=name,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest()))
    manifest=dict(contract=e.CONTRACT,format="caller-evidence-zip-v1",files=rows,
        raw_bytes=sum(r["raw_bytes"] for r in rows),stored_bytes=(out/"payload.zip").stat().st_size,
        payload_sha256=g.sha(out/"payload.zip"),
        evidence_source_sha256=g.sha(__file__),build_root=str(build),run_root=str(run))
    g.save(out/"archive-manifest.json",manifest);g.save(out/"original-audit.json",result)
    return dict(status="CALLER_EVIDENCE_PACKED",files=len(rows),raw_bytes=manifest["raw_bytes"],
        stored_bytes=manifest["stored_bytes"],archive_manifest_sha256=g.sha(out/"archive-manifest.json"))

def unpack(archive,out):
    manifest=e.read(archive/"archive-manifest.json")
    g.require(manifest["contract"]==e.CONTRACT and manifest["format"]=="caller-evidence-zip-v1" and
              manifest["evidence_source_sha256"]==g.sha(__file__),"caller archive format/auditor identity")
    sealed=archive/"payload.zip"
    g.require(not sealed.is_symlink() and sealed.stat().st_size==manifest["stored_bytes"] and
              g.sha(sealed)==manifest["payload_sha256"],"caller compressed payload identity")
    seen=set();out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(sealed) as payload:
        names=payload.namelist()
        g.require(len(names)==len(set(names))==len(manifest["files"]),"caller archive member cardinality")
        for row in manifest["files"]:
            rel=PurePosixPath(row["path"])
            g.require(not rel.is_absolute() and ".." not in rel.parts and "\\" not in row["path"] and
                      str(rel)==row["path"] and rel.parts[0] in ("build","run") and str(rel) not in seen,
                      "unsafe/duplicate caller archive member")
            g.require(re.fullmatch(r"[0-9a-f]{64}",row["raw_sha256"]),"caller archive raw digest")
            member=payload.getinfo(str(rel))
            g.require(member.external_attr>>16==0o100644 and not member.is_dir() and
                      member.file_size==row["raw_bytes"],"caller archive file type/size")
            raw=payload.read(member)
            g.require(hashlib.sha256(raw).hexdigest()==row["raw_sha256"],"caller decoded member identity")
            target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            seen.add(str(rel))
        g.require(set(names)==seen,"caller archive extra/missing member")
    g.require(sum(r["raw_bytes"] for r in manifest["files"])==manifest["raw_bytes"],"caller archive totals")
    return manifest

def audit_archive(archive):
    with tempfile.TemporaryDirectory(prefix="caller-archive-replay-") as temp:
        root=Path(temp)/"restored";manifest=unpack(archive,root)
        result=audit(root/"build",root/"run")
        g.require(result==e.read(archive/"original-audit.json"),"caller archive raw result drift")
    return dict(result,status="CALLER_ARCHIVE_RAW_AUDIT_PASS",archive_manifest_sha256=g.sha(archive/"archive-manifest.json"),
                files=len(manifest["files"]),raw_bytes=manifest["raw_bytes"],stored_bytes=manifest["stored_bytes"])

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--action",choices=("audit","pack","audit-archive"),required=True)
    p.add_argument("--build",type=Path);p.add_argument("--run",type=Path);p.add_argument("--archive",type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();out=args.output.resolve();g.require(not out.exists(),"caller evidence output must be new")
    roots=[e.ROOT]+[v.resolve() for v in (args.build,args.run,args.archive) if v]
    identity=e.ROOT/e.parent.REPRO/"evidence/clean-reproduction-v1/reports/identity-02.json"
    cfg=e.parent.parent_identity(e.ROOT,identity)["configuration"]
    roots += [identity.parent]+[cfg[k] for k in ("am_home","hardware_source","build_record")]
    e.parent.outside_inputs(out,roots)
    if args.action=="audit-archive":
        g.require(args.archive is not None,"caller archive required");result=audit_archive(args.archive.resolve());g.save(out,result)
    else:
        g.require(args.build and args.run,"caller build and run required")
        if args.action=="pack":result=pack(args.build.resolve(),args.run.resolve(),out)
        else:result=audit(args.build.resolve(),args.run.resolve());g.save(out,result)
    print(json.dumps(result,indent=2))
