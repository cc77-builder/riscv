"""Continue interrupted ordinary-C recovery/replay without rewriting prior evidence."""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

CONTRACT = "current-firstdot-c-continuation-v1"
PASS = "CURRENT_FIRSTDOT_C_CONTINUATION_PASS"
LEAF = Path("team/optimizations/o2/integration/firstdot-v2-0f")
PARENT = Path("team/optimizations/o2/r2-select/entry_c_api.py")
PARENT_SHA = "4e1ae340c5b122d09d634631d7fce322ad121838ba9a4affdf193d2a4d9105fd"
RUNNER_SHA = "76353dc7a6929a0c7f3b254062b6ac7ed5ab28fce2b09659b67e6bf703b0da7b"

def require(ok,message):
    if not ok: raise ValueError(message)

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()

def tree(root):
    result={}
    for p in sorted(Path(root).rglob("*")):
        require(not p.is_symlink(),"prior evidence symlink")
        if p.is_file():result[str(p)]=sha(p)
    return result

def verify_files(files):
    require(files and all(sha(p)==h for p,h in files.items()),"frozen input drift")

def replace_one(text,old,new):
    require(text.count(old)==1,"private adapter source marker changed: "+old[:80])
    return text.replace(old,new)

def load(repo):
    sys.path.insert(0,str(repo/LEAF))
    import combination as combo
    require(combo.ROOT==repo,"combination loaded from wrong source")
    require(sha(repo/PARENT)==PARENT_SHA,"upstream C runner changed")
    combo.verify_imports()
    return combo

def inspect_prior(repo,identity,matrix,build,prior,physical=True):
    repo,identity,matrix,build,prior=map(Path,(repo,identity,matrix,build,prior))
    combo=load(repo)
    value=combo.parent_identity(repo,identity,physical=physical)
    if physical:value=value[0]
    base=combo.c_adapter(repo,value)
    cfg=value["configuration"]
    wanted=dict(cfg,canonical_build=str(build),run_root=str(prior),source_root=str(repo))
    require(read(prior/"configuration.json")==wanted,"prior configuration differs")
    state=read(prior/"state.json")
    require(state["contract"]==base.CONTRACT and state["status"]=="PREFLIGHT"
            and state["new_emu_runs"]==2 and state["performance_measured"] is False
            and "finished" not in state,"prior C campaign is not the supported interruption")
    require({p.name for p in (prior/"runs").iterdir()}=={"negative","recovery"},"prior run inventory")
    negative=read(prior/"runs/negative/result.json")
    incomplete=read(prior/"runs/recovery/result.json")
    require(read(prior/"completed-runs.json")==[negative],"completed C record inventory")
    require(incomplete["status"]=="RUNNING" and incomplete["process_started"] is True
            and incomplete["exit_code"] is None and "finished" not in incomplete
            and state["active_pid"]==incomplete["pid"]
            and state["active_result"]==str(prior/"runs/recovery/result.json"),"prior incomplete record differs")
    pidfile=Path("/proc")/str(incomplete["pid"])/"cmdline"
    if pidfile.exists():
        active=pidfile.read_bytes().split(b"\0")
        require(active[:len(incomplete["command"])]!=[x.encode() for x in incomplete["command"]],
                "original recovery process remains active")
    require(not (prior/"results.json").exists() and not (prior/"independent-c-orchestration.json").exists(),
            "do not continue a complete prior run")
    runner=prior.parent/"run_c_independent.py"
    command_path=prior.with_name(prior.name+".command.json")
    command=read(command_path)
    require(sha(runner)==RUNNER_SHA and sha(repo/LEAF/"orchestration/run_c_independent.py")==RUNNER_SHA,
            "original runner copy drift")
    require(command["command"]==["python3","-B",str(runner),str(repo),str(identity),str(matrix),str(build),str(prior)]
            and command["cwd"]==str(repo) and type(command["pid"]) is int and type(command["child_pid"]) is int
            and command["pid"]>0 and command["child_pid"]>0 and "exit_code" not in command
            and "finished" not in command,"original launcher is not the recorded interrupted invocation")
    common=read(prior/"runtime-inputs.json")
    verify_files(common)
    validation=base.verify_build(repo,build)
    require(read(build/"elf-validation.json")==validation and read(build/"build.json")["accepted"] is True,
            "C build receipt drift")
    require(combo.library_anchor(repo,build,matrix)==read(build/"matrix-anchor.json"),"C matrix anchor drift")
    require(read(build/"combination-c-build.json")==dict(contract=combo.CONTRACT,adapter_files=combo.adapter_files()),
            "C adapter closure differs")
    fixture=read(prior/"negative-fixture/fixture.json")
    reference=fixture["binary"]
    cwd=prior/"runs/negative/cwd"
    expected=dict(common)
    expected.update({str(cwd/"build"/n):h for n,h in base.a.frozen_m.AUX.items()})
    expected[reference]=fixture["negative_sha256"]
    argv=[str(Path(cfg["hardware_source"])/"build/emu"),"-i",str(build/"vdot-perf.bin"),
          "--flash="+cfg["flash"],"--ram-size=128MB","--diff="+reference,"--max-cycles=2000000","--seed=1"]
    require(negative["status"]==base.a.frozen_m.NEGATIVE_PASS and negative["negative"] is True
            and negative["replay"]==0 and negative["process_started"] is True and negative["exit_code"]==1
            and not negative.get("timed_out") and type(negative["pid"]) is int and negative["pid"]>0
            and negative["files"]==expected and negative["cwd"]==str(cwd) and negative["command"]==argv
            and negative["reference"]==reference and negative["contract"]==base.CONTRACT
            and negative["image_sha256"]==validation["image_sha256"]
            and negative["environment_overrides"]=={"XS_NEGATIVE_VECTOR_TARGET":"vdot"},"prior negative execution differs")
    verify_files(expected)
    require(fixture["source_sha256"]==base.a.frozen_m.NEGATIVE_SHA
            and fixture["normal_reference_sha256"]==base.a.frozen_f.REFERENCE
            and fixture["historical_negative_hash_claim"] is False
            and sha(prior/"negative-fixture/negative-fixture.c")==base.a.frozen_m.NEGATIVE_SHA
            and sha(reference)==fixture["negative_sha256"],"negative fixture differs")
    for n in ("stdout.log","stderr.log"):
        require(negative["raw_sha256"][n]==sha(prior/"runs/negative"/n),"prior negative raw log drift")
    suite=combo.g.load("resume_c_prior_runtime_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
    olddir=prior/"runs/negative"
    suite.validate_runtime((olddir/"stdout.log").read_text()+(olddir/"stderr.log").read_text(),reference)
    with tempfile.TemporaryDirectory(prefix="current-c-prior-raw-") as td:
        copy=Path(td)
        for n in ("stdout.log","stderr.log"):shutil.copyfile(olddir/n,copy/n)
        details=base.a.frozen_m.negative_check(repo,build,copy,negative)
        require(details==negative["negative_details"]==read(olddir/"negative.json")
                and read(copy/"observation.json")==read(olddir/"observation.json"),"negative raw replay differs")
        elf=combo.g.ELF((build/"vdot-perf.elf").read_bytes())
        pc=int(details["pc"],16)
        require(any(elf.symbols[r["api_symbol"]][0]<=pc<sum(elf.symbols[r["api_symbol"]][:2])
                    for r in read(build/"source/manifest.json")["rows"]),"negative outside public leaf")
    prior_files=tree(prior)
    prior_files.update({str(p):sha(p) for p in [runner,command_path,identity,matrix/"images.json",
                                               matrix/"combination-build.json",build/"matrix-anchor.json",
                                               build/"combination-c-build.json"]})
    proof=dict(contract=CONTRACT,status="CURRENT_FIRSTDOT_C_PRIOR_INTERRUPTION_BOUND",
        prior_root=str(prior),identity_sha256=sha(identity),prior_tree=tree(prior),frozen_files=prior_files,
        original_launched_processes=2,retained_completed_processes=1,interrupted_processes=1,
        interrupted_record=str(prior/"runs/recovery/result.json"),interrupted_status="INCOMPLETE_PROCESS_NOT_RUNNING",
        original_runner_sha256=RUNNER_SHA,original_command=str(command_path),
        original_command_sha256=sha(command_path),overall_started=state["started"],new_emu_runs=0)
    return combo,base,value,negative,fixture,common,proof

def private_run(base,negative,fixture,common,proof,source_lock):
    source=inspect.getsource(base.run)
    source=replace_one(source,'contract=CONTRACT,operation_id=operation,started=a.frozen_f.now(),',
        'contract=_resume_contract,operation_id=operation,started=a.frozen_f.now(),overall_started=_resume_proof["overall_started"],')
    source=replace_one(source,'    persist()\n    try:',
        '    persist()\n    g.save(out/"prior-interruption.json",_resume_proof)\n    g.save(out/"resume-source-lock.json",_resume_sources)\n    shutil.copyfile(_resume_source,out/"executed-resume_c.py")\n    try:')
    source=replace_one(source,'        g.save(out/"runtime-inputs.json",files)',
        '        g.require(files==_resume_common,"continuation original common closure differs")\n        g.save(out/"runtime-inputs.json",files)')
    source=replace_one(source,'        fixture=a.frozen_m.build_negative(repo,cfg,out/"negative-fixture")',
        '        fixture=_resume_fixture')
    source=replace_one(source,'        records=[]','        records=[_resume_negative]')
    source=replace_one(source,'        for label,negative in (("negative",True),("recovery",False),("replay",False)):',
        '        for label,negative in (("recovery",False),("replay",False)):')
    source=replace_one(source,'        state.update(status="R4_C_APPLICATION_CALLS_PASS",distinct_cases=48,public_functions=16,normal_case_executions=96,',
        '        state.update(status=_resume_pass,distinct_cases=48,public_functions=16,normal_case_executions=96,')
    source=replace_one(source,'expected_negative_runs=1,normal_runs=2,new_emu_runs=3,whole_suite_acceptance=False)',
        'expected_negative_runs=1,normal_runs=2,new_emu_runs=2,total_launched_processes=4,interrupted_processes=1,logical_completed_processes=3,whole_suite_acceptance=False,\n                     record_locations={"negative":str(Path(_resume_proof["prior_root"])/"runs/negative"),"recovery":str(out/"runs/recovery"),"replay":str(out/"runs/replay")})')
    namespace=dict(vars(base))
    namespace.update(_resume_contract=CONTRACT,_resume_pass=PASS,_resume_negative=negative,
                     _resume_fixture=fixture,_resume_common=common,_resume_proof=proof,
                     _resume_sources=source_lock,_resume_source=str(Path(__file__).resolve()))
    exec(compile(source,"<current-c-continuation-private-run>","exec"),namespace)
    return namespace["run"],hashlib.sha256(source.encode()).hexdigest()

def run(repo,identity,matrix,build,prior,output,operation_id):
    repo,identity,matrix,build,prior,output=[Path(p).resolve() for p in (repo,identity,matrix,build,prior,output)]
    require(not output.exists() and not any(output.is_relative_to(p) or p.is_relative_to(output)
            for p in (repo,identity.parent,matrix,build,prior)),"fresh disjoint output required")
    combo,base,value,negative,fixture,common,proof=inspect_prior(repo,identity,matrix,build,prior)
    lock=dict(contract=CONTRACT,source_sha256=sha(__file__),source_file=str(Path(__file__).resolve()),
              upstream_c_sha256=PARENT_SHA,adapter_files=combo.adapter_files(),prior_proof_sha256=hashlib.sha256(
                  json.dumps(proof,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
              hardware_identity_sha256=sha(identity),matrix_images_sha256=sha(matrix/"images.json"),
              c_build_sha256=sha(build/"build.json"),process_scope="2 new normal runs; 1 retained negative; 1 old interrupted run")
    execute,private_sha=private_run(base,negative,fixture,common,proof,lock)
    lock["private_run_sha256"]=private_sha
    cpus=sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0,[cpus[min(1,len(cpus)-1)]])
    result=execute(repo,value["configuration"],build,output,operation_id)
    require(tree(prior)==proof["prior_tree"],"prior evidence changed during continuation")
    verify_files(proof["frozen_files"]);verify_files(lock["adapter_files"])
    require(sha(__file__)==lock["source_sha256"],"continuation source changed")
    combo.parent_identity(repo,identity,physical=True)
    combo.g.save(output/"continuation-proof.json",dict(status="CURRENT_FIRSTDOT_C_CONTINUATION_INPUTS_STABLE",
        contract=CONTRACT,prior_interruption_sha256=sha(output/"prior-interruption.json"),
        source_lock_sha256=sha(output/"resume-source-lock.json"),state_sha256=sha(output/"state.json"),
        results_sha256=sha(output/"results.json"),new_emu_runs=2,total_launched_processes=4,
        logical_completed_processes=3,interrupted_processes=1,combination_qualified=False))
    print("CURRENT_FIRSTDOT_C_CONTINUATION_DONE_MATRIX_AND_RAW_AUDIT_PENDING",flush=True)
    return result

def qualify(repo,identity,matrix,build,run_path):
    repo,identity,matrix,build,run_path=[Path(p).resolve() for p in (repo,identity,matrix,build,run_path)]
    prior_proof=read(run_path/"prior-interruption.json")
    prior=Path(prior_proof["prior_root"])
    combo,base,value,negative,fixture,common,actual=inspect_prior(repo,identity,matrix,build,prior,physical=False)
    require(actual==prior_proof,"prior interruption proof drift")
    state=read(run_path/"state.json");result=read(run_path/"results.json")
    counts=dict(new_emu_runs=2,total_launched_processes=4,interrupted_processes=1,logical_completed_processes=3,
                distinct_cases=48,public_functions=16,normal_case_executions=96,expected_negative_runs=1,normal_runs=2)
    require(state["contract"]==CONTRACT and state["status"]==PASS and all(state.get(k)==v for k,v in counts.items())
            and state["performance_measured"] is False and state["whole_suite_acceptance"] is False
            and state["active_pid"] is None and state["active_result"] is None and "finished" in state,
            "C continuation campaign incomplete")
    locations={"negative":str(prior/"runs/negative"),"recovery":str(run_path/"runs/recovery"),"replay":str(run_path/"runs/replay")}
    require(state["record_locations"]==locations and {p.name for p in (run_path/"runs").iterdir()}=={"recovery","replay"},
            "C record locations differ")
    records=[read(Path(locations[label])/"result.json") for label in ("negative","recovery","replay")]
    require(records[0]==negative and records==read(run_path/"completed-runs.json")==result["runs"],"C record closure differs")
    require({k:v for k,v in result.items() if k!="runs"}=={k:v for k,v in state.items() if k!="finished"},
            "C cached state differs")
    require(records[1]["status"]==records[2]["status"]=="R4_C_APPLICATION_DIFFTEST_PASS"
            and records[1]["validation"]==records[2]["validation"],"C recovery/replay qualification differs")
    base.validate_recovery(records[0],records[1])
    require(read(run_path/"runtime-inputs.json")==common
            and read(run_path/"configuration.json")==dict(value["configuration"],canonical_build=str(build),
                run_root=str(run_path),source_root=str(repo)),"C continuation configuration/common drift")
    times=[datetime.fromisoformat(v) for v in (state["overall_started"],records[0]["started"],records[0]["finished"],
             state["started"],records[1]["started"],records[1]["finished"],records[2]["started"],records[2]["finished"],state["finished"])]
    require(all(t.utcoffset() is not None for t in times) and times==sorted(times),"C continuation chronology differs")
    lock=read(run_path/"resume-source-lock.json")
    require(lock["source_file"]==str(Path(__file__).resolve()) and lock["source_sha256"]==sha(__file__)
            and sha(run_path/"executed-resume_c.py")==sha(__file__) and lock["upstream_c_sha256"]==PARENT_SHA
            and lock["adapter_files"]==combo.adapter_files() and lock["hardware_identity_sha256"]==sha(identity)
            and lock["matrix_images_sha256"]==sha(matrix/"images.json") and lock["c_build_sha256"]==sha(build/"build.json")
            and lock["prior_proof_sha256"]==hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "C continuation source lock differs")
    _,private_sha=private_run(base,negative,fixture,common,actual,lock)
    require(private_sha==lock["private_run_sha256"],"C private execution transform differs")
    proof=read(run_path/"continuation-proof.json")
    require(proof==dict(status="CURRENT_FIRSTDOT_C_CONTINUATION_INPUTS_STABLE",contract=CONTRACT,
        prior_interruption_sha256=sha(run_path/"prior-interruption.json"),source_lock_sha256=sha(run_path/"resume-source-lock.json"),
        state_sha256=sha(run_path/"state.json"),results_sha256=sha(run_path/"results.json"),new_emu_runs=2,
        total_launched_processes=4,logical_completed_processes=3,interrupted_processes=1,combination_qualified=False),
        "C continuation final input seal differs")
    return dict(status="CURRENT_FIRSTDOT_C_CONTINUATION_METADATA_PASS",contract=CONTRACT,record_locations=locations,
                prior_root=str(prior),new_emu_runs=2,total_launched_processes=4,interrupted_processes=1,
                logical_completed_processes=3,state_sha256=sha(run_path/"state.json"),
                results_sha256=sha(run_path/"results.json"),proof_sha256=sha(run_path/"continuation-proof.json"),
                metadata_only=True,raw_recomputation_required=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("repo","identity","matrix","build","prior","output"):
        parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--action",choices=("inspect","run"),required=True)
    parser.add_argument("--operation-id",default="20261026-cc77-builder-firstdot-c-continuation")
    args=parser.parse_args()
    if args.action=="inspect":
        require(not args.output.exists(),"preserve existing inspection output")
        *_,proof=inspect_prior(args.repo.resolve(),args.identity.resolve(),args.matrix.resolve(),args.build.resolve(),args.prior.resolve())
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(proof,indent=2)+"\n")
        print(proof["status"])
    else:
        run(args.repo,args.identity,args.matrix,args.build,args.prior,args.output,args.operation_id)
