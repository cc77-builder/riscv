"""Recover only unfinished O3 jobs; immutable original executor, separate evidence."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from threading import Lock
import campaign as c

def expected_jobs(images):
    expected={(mode,image["name"],0) for mode in ("o1","o2") for image in images}
    image=next(i for i in images if i["suite"]=="performance" and i["dataset"]==0 and i["shard"]==5)
    expected|={(mode,image["name"],r) for mode in ("o1","o2") for r in (1,2)}
    c.require(len(expected)==56,"exact 56 accepted-job plan")
    return expected

def frozen_executor(source):
    tree=ast.parse(source)
    run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run")
    nodes=[n for n in ast.walk(run) if isinstance(n,ast.FunctionDef) and n.name=="execute"]
    c.require(len(nodes)==1,"one original executor required")
    return nodes[0]

def importable(record,directory):
    if not record.get("finished_utc") or record.get("status")!="O3_IMAGE_DIFFTEST_STATE_WINDOWS_AND_PROTOCOL_PASS":
        return False
    c.require(record.get("exit_code")==0,"accepted previous job has bad exit")
    c.require((directory/"exit-code.txt").read_text()=="0\n","missing original actual exit")
    c.require(set(record["raw_sha256"])=={"stdout.log","stderr.log"},"raw stream inventory")
    for name,digest in record["raw_sha256"].items():c.require(c.sha(directory/name)==digest,"original raw log drift")
    for name in ("runtime.json","windows.json","observation.json"):c.require((directory/name).is_file(),"missing accepted evidence")
    runtime=json.loads((directory/"runtime.json").read_text())
    for key in ("mode","image","suite","shard","dataset","build","replay","command","cwd","started_utc","files"):
        c.require(runtime[key]==record[key],"previous immutable runtime drift "+key)
    return True

def run(previous,images_root,output):
    previous,images_root,output=map(Path,(previous,images_root,output))
    c.require(not output.exists(),"new recovery output directory required")
    old_state=json.loads((previous/"state.json").read_text())
    source_commit=old_state["source_commit"]
    frozen=(previous/"source/team/workloads/o3-gemv/campaign.py").read_text()
    recorded=subprocess.check_output(["git","show",source_commit+":team/workloads/o3-gemv/campaign.py"],cwd=c.ROOT)
    c.require(recorded==frozen.encode(),"frozen executor source differs from original Git")
    c.require((c.HERE/"campaign.py").read_bytes()==recorded,"runtime measurement source changed")
    files=json.loads((previous/"artifact-pins.json").read_text());c.verify_hashes(files)
    images=json.loads((images_root/"images.json").read_text())["images"];expected=expected_jobs(images)
    output.mkdir(parents=True)
    imported=[];incomplete=[]
    for path in sorted([*previous.glob("o1/*/runtime.json"),*previous.glob("o2/*/runtime.json")]):
        directory=path.parent;runtime=json.loads(path.read_text());key=(runtime["mode"],runtime["image"],runtime["replay"])
        c.require(key in expected,"unexpected previous job")
        result=directory/"result.json";record=json.loads(result.read_text()) if result.exists() else runtime
        if not importable(record,directory):
            incomplete.append(dict(key=list(key),directory=str(directory),reason="process absent and no complete actual-exit/evidence receipt",
                                   files={p.name:c.sha(p) for p in directory.iterdir() if p.is_file()}))
            continue
        c.require(key not in {(r["mode"],r["image"],r["replay"]) for r in imported},"duplicate accepted job")
        target=output/runtime["mode"]/directory.name;shutil.copytree(directory,target)
        imported.append(record)
    for name in ("artifact-pins.json","build-profile.json","o1-hardware-pins.json","o2-hardware-pins.json"):
        shutil.copy2(previous/name,output/name)
    shutil.copytree(previous/"source",output/"source")
    imported_keys={(r["mode"],r["image"],r["replay"]) for r in imported}
    pending=expected-imported_keys
    c.require(len(imported)==46 and len(incomplete)==2 and len(pending)==10,"unexpected recovery boundary; inspect before executing")
    recovery_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=c.ROOT,text=True).strip()
    proof=dict(status="O3_INTERRUPTION_RECOVERY_PLAN",previous=str(previous),output=str(output),source_commit=source_commit,
               recovery_source_commit=recovery_commit,imported_accepted_jobs=len(imported),pending_jobs=len(pending),
               incomplete_attempts=incomplete,imported_keys=[list(k) for k in sorted(imported_keys)],
               pending_keys=[list(k) for k in sorted(pending)],started_utc=c.now(),original_previous_files_unchanged=True,
               previous_file_sha256={p.relative_to(previous).as_posix():c.sha(p) for p in previous.rglob("*") if p.is_file()})
    c.save(output/"recovery.json",proof)
    node=frozen_executor(frozen)
    executor_dump=ast.dump(node,include_attributes=False)
    c.save(output/"execution-source.json",dict(original_source_commit=source_commit,
           original_source_sha256=hashlib.sha256(recorded).hexdigest(),
           execute_ast_sha256=hashlib.sha256(executor_dump.encode()).hexdigest(),
           recovery_source_commit=recovery_commit,recovery_script_sha256=c.sha(Path(__file__)),
           method="compile the exact unchanged execute FunctionDef from frozen original campaign source; new orchestration only"))
    recovery_source=output/"recovery-source";recovery_source.mkdir()
    for name in ("resume.py","test_resume.py"):
        source=c.HERE/name
        body=subprocess.check_output(["git","show",recovery_commit+":"+source.relative_to(c.ROOT).as_posix()],cwd=c.ROOT)
        c.require(body==source.read_bytes(),"recovery code uncommitted")
        (recovery_source/name).write_bytes(body)
    state=dict(status="RUNNING",source_commit=source_commit,recovery_source_commit=recovery_commit,
               started_utc=c.now(),new_emu_jobs=len(imported),new_recovery_emu_jobs=0,planned_jobs=56,
               reused_completed_jobs=len(imported),interrupted_attempts=len(incomplete),github_pushed=False,
               images=str(images_root),previous=str(previous))
    c.save(output/"state.json",state);c.save(output/"progress.json",[{k:v for k,v in r.items() if k!="samples"} for r in imported])
    pins={mode:json.loads((output/(mode+"-hardware-pins.json")).read_text()) for mode in ("o1","o2")}
    c.g4.validate_pair(pins["o1"],pins["o2"])
    gate=c.load("o3_resume_runtime_gate",c.ROOT/"team/optimizations/o1/audit/runtime_gate.py")
    fatal=c.load("o3_resume_fatal",c.ROOT/"team/optimizations/o2/fullcore/workloads/check.py")
    observers={mode:c.load("o3_resume_observer_"+mode,c.ROOT/("team/optimizations/"+mode+"/fullcore/analyze.py")) for mode in ("o1","o2")}
    records=imported[:];lock=Lock()
    namespace=dict(vars(c),out=output,records=records,state=state,files=files,pins=pins,gate=gate,fatal=fatal,observers=observers,lock=lock)
    tree=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(tree)
    exec(compile(tree,str(previous/"source/team/workloads/o3-gemv/campaign.py"),"exec"),namespace)
    execute=namespace["execute"]
    try:
        for stage in ("performance","replay"):
            state["stage"]=stage;c.save(output/"state.json",state)
            groups=sorted({(image,replay) for mode,image,replay in pending if (stage=="replay")==(replay>0)})
            def pair(task):
                name,replay=task;image=next(i for i in images if i["name"]==name)
                index=100 if replay else images.index(image)
                order=("o1","o2") if (index+replay)%2==0 else ("o2","o1")
                result=[]
                for mode in order:
                    if (mode,name,replay) not in pending:continue
                    row=execute(mode,image,replay);result.append(row)
                    if row["status"]=="FAILED":break
                return result
            with ThreadPoolExecutor(max_workers=2) as pool:
                pairs=[f.result() for f in as_completed([pool.submit(pair,t) for t in groups])]
            results=[row for pair_rows in pairs for row in pair_rows]
            c.require(all(r["status"]=="O3_IMAGE_DIFFTEST_STATE_WINDOWS_AND_PROTOCOL_PASS" for r in results),"recovery stage failed "+stage)
            state["new_recovery_emu_jobs"]=len(records)-len(imported);c.save(output/"state.json",state)
        c.require(len(records)==56,"accepted job count")
        for mode in ("o1","o2"):
            rows=[r for r in records if r["mode"]==mode and r["image"]=="performance-d0-s05"]
            base=next(r for r in rows if r["replay"]==0)
            c.require(len(rows)==3 and {r["replay"] for r in rows}=={0,1,2},"replay inventory")
            for row in rows:
                c.require([(s["seq"],s["cycles"],s["instructions"]) for s in row["samples"]]==[(s["seq"],s["cycles"],s["instructions"]) for s in base["samples"]],"cross-restart deterministic replay mismatch")
        stats=c.summarize(records);c.verify_hashes(files)
        for name,digest in proof["previous_file_sha256"].items():c.require(c.sha(previous/name)==digest,"original interrupted campaign modified")
        result=dict(status="O3_PAIRED_APPLICATION_CAMPAIGN_PASS",source_commit=source_commit,recovery_source_commit=recovery_commit,
                    runs=records,**stats,real_emu_jobs=56,accepted_emu_jobs=56,new_recovery_emu_jobs=10,reused_completed_jobs=46,
                    interrupted_emu_attempts=2,total_started_emu_attempts=58,validated_windows=sum(len(r["samples"]) for r in records),
                    measured_windows=768,replay_jobs=4,performance_measured=True,github_pushed=False,finished_utc=c.now())
        c.save(output/"result.json",result);state.update(status=result["status"],finished_utc=c.now(),new_recovery_emu_jobs=10)
        c.save(output/"state.json",state)
        print("O3_RECOVERY_COMPLETE",flush=True)
    except Exception as exc:
        state.update(status="FAILED",error=repr(exc),finished_utc=c.now());c.save(output/"state.json",state);raise

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--previous",required=True,type=Path)
    p.add_argument("--images",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.previous,a.images,a.output)
