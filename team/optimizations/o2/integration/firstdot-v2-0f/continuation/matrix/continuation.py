"""Continue an interrupted firstdot matrix without rewriting completed evidence."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

CONTRACT = "zjhwork-0f-firstdot-v2-continuation-v1"
RUN_PASS = "CURRENT_FIRSTDOT_RESUMED_PAIRED_C_ABI_PASS"
LEAF = Path("team/optimizations/o2/integration/firstdot-v2-0f")
AUDIT_SHA = "f0a5419a751d25404a51deb6555e162116f16a542b336d85d37fcfdcc4037d98"

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    value=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576),b""):value.update(block)
    return value.hexdigest()

def require(ok,message):
    if not ok:raise ValueError(message)

def read(path):
    return json.loads(Path(path).read_text())

def save(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")

def modules(repo):
    sys.dont_write_bytecode=True
    path=Path(__file__).with_name("audit_snapshot.py")
    require(sha(path)==AUDIT_SHA,"snapshot auditor changed")
    spec=importlib.util.spec_from_file_location("_resumed_matrix_audit",path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    combo=audit.load_combination(repo)
    return combo,audit

def snapshot(root):
    value={}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(),"prior evidence contains symlink: "+str(path))
        if path.is_file():value[str(path)]=dict(bytes=path.stat().st_size,sha256=sha(path))
    require(value,"empty prior evidence")
    return value

def verify_snapshot(root,expected):
    require(snapshot(root)==expected,"preserved prior attempt changed")

def ordered(combo,images):
    target=next(i for i in images if (i["shard"],i["dataset"],i["variant"])==(3,0,"firstdot"))
    rows=[("negative-firstdot-8x32",target,True,0),("recovery-firstdot-8x32",target,False,0)]
    for image in sorted(images,key=lambda i:(i["shard"],i["dataset"],
             combo.VARIANTS.index(i["variant"]) ^ ((i["shard"]+i["dataset"])%2))):
        if image["name"]!=target["name"]:rows.append(("formal-"+image["name"],image,False,0))
    rows.extend(("replay-"+i["name"],i,False,1) for i in images if i["dataset"]==0)
    require(len(rows)==33,"logical run inventory")
    return rows

def assert_no_active_worker(prior):
    # PID numbers may be reused after WSL restarted. Match the real command line.
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():continue
        try:
            raw=(directory/"cmdline").read_bytes()
            args=[x.decode(errors="replace") for x in raw.split(bytes([0])) if x]
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if not args:continue
        if Path(args[0]).name=="emu":
            try:cwd=(directory/"cwd").resolve()
            except (OSError,PermissionError):cwd=None
            if (cwd is not None and cwd.is_relative_to(prior)) or any(str(prior) in x for x in args):
                raise ValueError("prior EMU remains active: "+directory.name)
        if any(Path(x).name=="combination.py" for x in args) and str(prior) in args:
            raise ValueError("prior controller remains active: "+directory.name)

def image_inputs(combo,audit,repo,identity_path,build):
    identity,hardware,profile=combo.parent_identity(repo,identity_path,physical=True)
    f,m=combo.runtime(repo,identity)
    images=read(build/"images.json")["images"]
    require(read(build/"state.json")["status"]==combo.BUILD_PASS,"build incomplete")
    expected={combo.name(x):x for x in combo.inventory([1,3,5,7],[0,1,2])}
    require(len(images)==24 and {i["name"] for i in images}==set(expected),"24 images required")
    combo.verify_build_scope(repo,build,images,identity_path)
    for image in images:
        require(all(image[k]==v for k,v in expected[image["name"]].items()),"image selection drift")
        combo.validate_image(image,build)
        p=Path(image["path"]);combo.g.verify_build(p,repo)
        m.validate_selection(image,read(p/"data/manifest.json"),read(p/"build.json"))
        require(sha(p/"vdot-perf.bin")==image["image_sha256"],"BIN drift")
    common=audit.matrix_common(combo,repo,identity_path,build,images,hardware,m)
    require(combo.pairs(images,repo)==read(build/"pairs.json"),"build pair drift")
    return identity,hardware,profile,f,m,images,common

def check_record(combo,audit,repo,f,m,cfg,common,directory,image,negative,replay,fixture):
    record=read(directory/"result.json")
    audit.process_receipt(record,image,directory,common,cfg,m,negative,fixture,replay)
    suite=combo.g.load("_resumed_raw_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
    suite.validate_runtime((directory/"stdout.log").read_text()+(directory/"stderr.log").read_text(),record["reference"])
    if negative:
        with tempfile.TemporaryDirectory(prefix="firstdot-resume-negative-") as td:
            scratch=Path(td)
            for n in ("stdout.log","stderr.log"):shutil.copyfile(directory/n,scratch/n)
            detail=m.negative_check(repo,Path(image["path"]),scratch,record)
            require(detail==record["negative_details"]==read(directory/"negative.json"),"negative raw drift")
            require(read(scratch/"observation.json")==read(directory/"observation.json"),"negative observation drift")
            require(detail["vd"]==0 and detail["bit"]==100 and detail["word"]=="0x0388000b","negative target")
    else:
        windows,observation=f.verify_runtime(repo,Path(image["path"]),directory)
        require(audit.plain(windows)==read(directory/"windows.json") and
                audit.plain(observation)==read(directory/"observation.json"),"normal raw drift")
        manifest=read(Path(image["path"])/"data/manifest.json")
        values=[]
        for sample,plan in zip(windows["samples"],manifest["plan"]):
            row=manifest["rows"][plan["index"]]
            values.append(dict(sample,mode="merged",variant=image["variant"],shard=image["shard"],
                software=row["software"],m=row["m"],k=row["k"],scope=row["scope"],image_sha256=image["image_sha256"]))
        require(len(values)==24 and audit.plain(values)==record["samples"],"raw samples differ")
    return record

def prior_records(combo,audit,repo,identity_path,build,prior,identity,f,m,images,common):
    assert_no_active_worker(prior)
    state=read(prior/"state.json")
    require(state["contract"]==combo.CONTRACT and state["status"] in ("PERFORMANCE","REPLAY")
            and "finished" not in state,"requires original interrupted campaign")
    require(read(prior/"runtime-inputs.json")==common,"prior common identity drift")
    require(read(prior/"configuration.json")==dict(identity["configuration"],canonical_builds=[str(build)]),
            "prior configuration drift")
    require((prior/"parent-identity.json").read_bytes()==identity_path.read_bytes(),"prior hardware identity drift")
    require(read(prior/"hardware-profile.json")==identity["hardware_profile"],"prior hardware profile drift")
    require(read(prior/"pairs.json")==combo.pairs(images,repo),"prior pair drift")
    fixture=audit.negative_fixture(prior,identity["configuration"],m)
    sequence=ordered(combo,images)
    locations={};records=[];negative=None;interrupted=[];encountered_unfinished=False
    actual={p.name for p in (prior/"runs").iterdir()}
    require(actual=={x[0] for x in sequence[:state["new_emu_runs"]]},"prior run prefix differs")
    for label,image,is_negative,replay in sequence[:state["new_emu_runs"]]:
        path=prior/"runs"/label;record=read(path/"result.json")
        if record.get("finished"):
            require(not encountered_unfinished,"completed record after unfinished prefix")
            record=check_record(combo,audit,repo,f,m,identity["configuration"],common,path,image,is_negative,replay,fixture)
            locations[label]=str(path)
            if is_negative:negative=record
            else:records.append(record)
        else:
            encountered_unfinished=True
            require(record.get("process_started") is True and record.get("exit_code") is None
                    and record.get("status")=="RUNNING","unexpected incomplete record")
            require(state["active_result"]==str(path/"result.json") and state["active_pid"]==record["pid"],
                    "active interrupted record binding")
            interrupted.append(dict(label=label,record=str(path/"result.json"),record_sha256=sha(path/"result.json"),
                actual_exit_code=None,status="INTERRUPTED_PROCESS_ABSENT",process_was_started=True,
                actual_started=record["started"],detected_at=now(),
                raw_at_detection={n:sha(path/n) for n in ("stdout.log","stderr.log")}))
    require(len(interrupted)==1 and negative is not None,"expected one interrupted normal process")
    require(read(prior/"completed-runs.json")==records,"completed record cache differs")
    require(state["new_emu_runs"]==len(locations)+len(interrupted),"prior process accounting")
    m.validate_recovery(negative,next(r for r in records if r["name"]==negative["name"]))
    m.verify_files(common)
    return state,records,negative,locations,interrupted


def preflight(repo,identity_path,build,prior):
    combo,audit=modules(repo)
    original=snapshot(prior)
    identity,hardware,profile,f,m,images,common=image_inputs(combo,audit,repo,identity_path,build)
    prior_state,records,negative,locations,interrupted=prior_records(
        combo,audit,repo,identity_path,build,prior,identity,f,m,images,common)
    verify_snapshot(prior,original)
    remaining=[row for row in ordered(combo,images) if row[0] not in locations]
    proof=dict(contract=CONTRACT,status="CURRENT_FIRSTDOT_RESUME_PREFLIGHT_PASS",
        parent_identity_sha256=sha(identity_path),prior_root=str(prior),
        prior_processes_started=prior_state["new_emu_runs"],inherited_qualified_processes=len(locations),
        inherited_normal_runs=len(records),interrupted_processes=interrupted,
        remaining_runs=len(remaining),remaining_labels=[x[0] for x in remaining],
        final_qualified_processes=33,expected_total_processes_started=prior_state["new_emu_runs"]+len(remaining),
        historical_other_hardware_reused=False,source_snapshot_files=len(original),new_emu_runs=0)
    return combo,audit,identity,hardware,profile,f,m,images,common,prior_state,records,negative,locations,interrupted,original,proof

def run(repo,identity_path,build,prior,output,operation_id):
    combo,audit=modules(repo)
    cfg=combo.parent_identity(repo,identity_path)["configuration"]
    combo.outside_inputs(output,[repo,identity_path.parent,build,prior,Path(__file__).parent,
        cfg["hardware_source"],cfg["build_record"],cfg["am_home"]])
    require(not output.exists(),"new output required")
    output.mkdir(parents=True)
    state=dict(contract=CONTRACT,status="PREFLIGHT",operation_id=operation_id,started=now(),
        new_emu_runs=0,inherited_started=0,interrupted_runs=0,total_processes_started=0,
        qualified_processes=0,active_pid=None,active_result=None,hardware_changed=False,
        stable_default_changed=False,historical_performance_reused=False)
    persist=lambda:save(output/"state.json",state)
    persist()
    try:
        values=preflight(repo,identity_path,build,prior)
        combo,audit,identity,hardware,profile,f,m,images,common,old,records,negative,locations,interrupts,snap,proof=values
        inherited=dict(locations)
        controller={str(Path(__file__).resolve()):sha(__file__),
                    str(Path(__file__).with_name("audit_snapshot.py").resolve()):AUDIT_SHA,
                    str(Path(__file__).with_name("CONTRACT.md").resolve()):sha(Path(__file__).with_name("CONTRACT.md"))}
        save(output/"preflight.json",proof)
        save(output/"prior-evidence-snapshot.json",snap)
        save(output/"interrupted-processes.json",interrupts)
        save(output/"runtime-inputs.json",common)
        save(output/"continuation-inputs.json",dict(controller_files=controller,repo=str(repo),
            identity=str(identity_path),build=str(build),prior_root=str(prior),
            prior_snapshot_sha256=sha(output/"prior-evidence-snapshot.json"),
            prior_started=old["new_emu_runs"],prior_completed=len(inherited),interrupted_runs=len(interrupts)))
        save(output/"configuration.json",dict(cfg,canonical_builds=[str(build)]))
        save(output/"hardware-profile.json",profile)
        shutil.copyfile(identity_path,output/"parent-identity.json")
        save(output/"pairs.json",combo.pairs(images,repo))
        save(output/"completed-runs.json",records)
        save(output/"run-locations.json",locations)
        state.update(inherited_started=old["new_emu_runs"],interrupted_runs=len(interrupts),
            total_processes_started=old["new_emu_runs"],qualified_processes=len(inherited),status="PERFORMANCE",
            inherited_qualified_processes=len(inherited),expected_new_emu_runs=proof["remaining_runs"])
        persist()
        def launch(image,label,replay):
            before=state["new_emu_runs"];dest=output/"runs"/label
            locations[label]=str(dest);save(output/"run-locations.json",locations)
            def progress(record):
                state.update(new_emu_runs=before+int(record.get("process_started") is True),
                    total_processes_started=old["new_emu_runs"]+before+int(record.get("process_started") is True),
                    active_pid=record.get("pid") if "finished" not in record else None,
                    active_result=str(dest/"result.json") if "finished" not in record else None)
                persist()
            value=m.execute(repo,cfg,image,dest,common,None,replay,progress)
            print(label,value["status"],flush=True)
            return value
        for label,image,is_negative,replay in ordered(combo,images):
            if label in inherited:continue
            require(not is_negative,"do not repeat inherited negative")
            state["status"]="REPLAY" if replay else "PERFORMANCE";persist()
            record=launch(image,label,replay)
            if replay:
                parent=next(r for r in records if r["name"]==record["name"] and r["replay"]==0)
                require(m.signature(record)==m.signature(parent),"all-window replay differs")
            records.append(record)
            state["qualified_processes"]=len(records)+1
            save(output/"completed-runs.json",records);persist()
        final_identity,final_hardware,final_profile=combo.parent_identity(repo,identity_path,physical=True)
        require((identity,hardware,profile)==(final_identity,final_hardware,final_profile),"hardware identity changed")
        m.verify_files(common);m.verify_files(controller);verify_snapshot(prior,snap)
        require(combo.pairs(images,repo)==read(output/"pairs.json"),"paired bytes changed")
        coverage=combo.qualification(images,records,True,True)
        require(all(coverage[k] for k in ("negative_and_recovery","all_window_replay","full_matrix")),"coverage incomplete")
        summary=combo.summarize(records)
        require(state["new_emu_runs"]==proof["remaining_runs"] and state["qualified_processes"]==33
                and state["total_processes_started"]==34 and len(interrupts)==1,"continuation process accounting")
        state["status"]=RUN_PASS
        detail=dict(prior_root=str(prior),prior_snapshot_sha256=sha(output/"prior-evidence-snapshot.json"),
            locations_sha256=sha(output/"run-locations.json"),new_emu_runs=state["new_emu_runs"],
            inherited_started=old["new_emu_runs"],inherited_qualified_processes=len(inherited),
            interrupted_runs=len(interrupts),total_processes_started=state["total_processes_started"],
            qualified_processes=state["qualified_processes"])
        result=dict(status=RUN_PASS,contract=CONTRACT,underlying_contract=combo.CONTRACT,
            parent_identity_sha256=sha(identity_path),hardware_source_commit=identity["source_commit"],
            emu_sha256=profile["emu_sha256"],historical_pass_reused=False,runs=records,negative=negative,
            qualification=coverage,continuation=detail,**summary)
        save(output/"results.json",result)
        return result
    except BaseException as exc:
        state.update(status="FAILED",error=repr(exc));raise
    finally:
        state["finished"]=now();persist()

def qualify(repo,identity_path,build,output):
    combo,audit=modules(repo)
    state,result=read(output/"state.json"),read(output/"results.json")
    binding=read(output/"continuation-inputs.json")
    require(state["status"]==result["status"]==RUN_PASS and state["contract"]==result["contract"]==CONTRACT,
            "continued matrix incomplete")
    require(state["active_pid"] is None and state["active_result"] is None,"continued matrix active")
    require(binding["repo"]==str(repo) and binding["identity"]==str(identity_path) and binding["build"]==str(build),
            "continuation input selection")
    combo.g.require(binding["controller_files"]=={
        str(Path(__file__).resolve()):sha(__file__),
        str(Path(__file__).with_name("audit_snapshot.py").resolve()):AUDIT_SHA,
        str(Path(__file__).with_name("CONTRACT.md").resolve()):sha(Path(__file__).with_name("CONTRACT.md"))},
        "continuation controller changed")
    prior=Path(binding["prior_root"])
    require(binding["prior_snapshot_sha256"]==sha(output/"prior-evidence-snapshot.json"),"snapshot identity")
    verify_snapshot(prior,read(output/"prior-evidence-snapshot.json"))
    locations=read(output/"run-locations.json")
    images=read(build/"images.json")["images"];combo.verify_build_scope(repo,build,images,identity_path)
    expected=ordered(combo,images)
    require(set(locations)=={r[0] for r in expected},"logical location inventory")
    records=[];negative=None
    m=combo.g.load("_continued_status",repo/"team/optimizations/o2/r2-vector-accum/merged_screen.py")
    for label,image,rejected,replay in expected:
        directory=Path(locations[label])
        require(directory in (prior/"runs"/label,output/"runs"/label),"unexpected run origin")
        row=read(directory/"result.json")
        require(row["negative"] is rejected and row["replay"]==replay and row.get("finished")
                and row["process_started"] is True and row["exit_code"]==(1 if rejected else 0),"run execution incomplete")
        require(row["status"]==(m.NEGATIVE_PASS if rejected else m.NORMAL_PASS),"run status")
        require(row["cwd"]==str(directory/"cwd") and all(row[k]==image[k] for k in ("name","suite","variant","shard","dataset","path","image_sha256")),
                "run image/location identity")
        require(row["raw_sha256"]=={n:sha(directory/n) for n in ("stdout.log","stderr.log")},"raw transcript drift")
        if rejected:negative=row
        else:records.append(row)
    require(records==result["runs"]==read(output/"completed-runs.json") and negative==result["negative"],"result/location records differ")
    m=combo.g.load("_continued_status",repo/"team/optimizations/o2/r2-vector-accum/merged_screen.py")
    normals={r["name"]:r for r in records if r["replay"]==0}
    require(len(normals)==24 and len(records)==32,"normal/replay inventory")
    for row in records:
        if row["replay"]:
            require(row["dataset"]==0 and m.signature(row)==m.signature(normals[row["name"]]),"continued replay differs")
    m.validate_recovery(negative,normals[negative["name"]])
    require(negative["negative_details"]["vd"]==0 and negative["negative_details"]["bit"]==100
            and negative["negative_details"]["word"]=="0x0388000b","continued negative target")
    q=combo.qualification(images,records,True,True)
    require(result["qualification"]==q and all(q[k] for k in ("negative_and_recovery","all_window_replay","full_matrix")),
            "continued coverage")
    require(all(result[k]==v for k,v in combo.summarize(records).items()),"continued summary differs")
    require(result["measured_windows"]==384 and result["parent_identity_sha256"]==sha(identity_path)
            and result["historical_pass_reused"] is False,"continued qualification identity")
    detail=result["continuation"]
    for key in ("new_emu_runs","inherited_started","inherited_qualified_processes","interrupted_runs","total_processes_started","qualified_processes"):
        require(detail[key]==state[key],"process accounting drift: "+key)
    require(state["inherited_started"]==13 and state["inherited_qualified_processes"]==12
            and state["new_emu_runs"]==21 and state["total_processes_started"]==34
            and state["interrupted_runs"]==1 and state["qualified_processes"]==33,"continued actual process accounting")
    require(detail["prior_root"]==binding["prior_root"] and detail["prior_snapshot_sha256"]==binding["prior_snapshot_sha256"]
            and detail["locations_sha256"]==sha(output/"run-locations.json"),"continued source mapping drift")
    return dict(status="CURRENT_FIRSTDOT_CONTINUATION_QUALIFICATION_PASS",contract=CONTRACT,
        results_sha256=sha(output/"results.json"),state_sha256=sha(output/"state.json"),
        images_sha256=sha(build/"images.json"),parent_identity_sha256=sha(identity_path),
        locations_sha256=sha(output/"run-locations.json"),path=str(output),
        qualified_processes=33,total_processes_started=34,interrupted_processes=1,new_processes_in_continuation=21)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--action",choices=("preflight","run","qualify"),required=True)
    for key in ("repo","identity","build","prior","output"):p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--operation-id",default="20261026-cc77-builder-firstdot-continuation")
    args=p.parse_args()
    for key in ("repo","identity","build","prior","output"):setattr(args,key,getattr(args,key).resolve())
    if args.action=="run":
        if os.name=="posix":os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
        value=run(args.repo,args.identity,args.build,args.prior,args.output,args.operation_id)
    elif args.action=="qualify":
        value=qualify(args.repo,args.identity,args.build,args.prior)
        require(not args.output.exists(),"new qualification output required");save(args.output,value)
    else:
        value=preflight(args.repo,args.identity,args.build,args.prior)[-1]
        require(not args.output.exists(),"new preflight output required");save(args.output,value)
    print(json.dumps({k:v for k,v in value.items() if k not in ("runs","samples","rows")},indent=2))
if __name__=="__main__":main()
