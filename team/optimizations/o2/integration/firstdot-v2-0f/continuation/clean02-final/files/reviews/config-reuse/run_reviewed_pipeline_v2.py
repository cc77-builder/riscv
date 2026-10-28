#!/usr/bin/env python3
"""Execute the reviewed clean02 bounded software probe; never grants its own review."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
PLAN_SHA="8d69123dd57828b58656e2d0f21f8988ccba1d7ddeefd0c3dc2da15863b9d153"
EXECUTOR_SHA="889228456990c98a4793312ea1f41b2546977a107f18433a8549a881184f1340"
RECORDER_SHA="8191e873267ecee72fcffff7211dac4a9c6c35499d2b826c2f9f62f3c8d3713e"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def need(x,why):
    if not x:raise ValueError(why)
def now():return datetime.now(timezone.utc).isoformat()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--plan",type=Path,required=True);ap.add_argument("--review",type=Path,required=True);ap.add_argument("--state",type=Path,required=True)
    a=ap.parse_args();need(not a.state.exists(),"existing pipeline state; preserve, do not resume implicitly")
    need(sha(a.plan)==PLAN_SHA,"plan changed");plan=read(a.plan)
    driver_review=read(a.review).get("orchestration_driver",{})
    need(driver_review==dict(path=str(Path(__file__).resolve()),sha256=sha(__file__)),"pipeline source is not bound by actual root review")
    w=Path(plan["paths"]["work"]);repo=Path(plan["paths"]["repo"]);out=Path(plan["paths"]["output_root"])
    executor=Path(plan["external_executor"]["path"]);recorder=w/"run_recorded.py"
    need(sha(executor)==EXECUTOR_SHA and sha(recorder)==RECORDER_SHA,"source changed")
    spec=importlib.util.spec_from_file_location("bound_executor",executor);ex=importlib.util.module_from_spec(spec);spec.loader.exec_module(ex)
    ex.validate_plan(plan);ready=ex.gate_metadata(plan);ex.validate_review(plan,a.plan,a.review,ready,"import")
    need(not out.exists(),"existing probe output")
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():continue
        try:cmd=(proc/"cmdline").read_bytes().split(b"\0")[0].decode()
        except (OSError,UnicodeError):continue
        need(Path(cmd).name not in {"emu","verilator_bin","riscv64-nemu-interpreter"},"another target remains active: "+str(proc))
    cores=sorted(os.sched_getaffinity(0))[:4];need(bool(cores),"no allowed CPUs")
    affinity=",".join(map(str,cores))
    stages=[]
    import_receipt=w/"config-reuse-clean02-import-01.command.json"
    after_receipt=w/"config-reuse-clean02-after-audit-01.command.json"
    for label in ("import","after-audit"):
        receipt=executor.parent/"stage-receipts"/("root-clean02-"+label+"-01.json")
        need(not receipt.exists(),"existing stage execution receipt")
        command=["env","GIT_OPTIONAL_LOCKS=0","python3","-B",str(executor),"--stage",label,"--plan",str(a.plan),"--review",str(a.review),"--execute","--receipt",str(receipt)]
        stages.append((label,import_receipt if label=="import" else after_receipt,command))
    first,last=stages
    middle=[]
    for action in ("build","run","audit"):
        prefix=["env","GIT_OPTIONAL_LOCKS=0"]
        if action=="run":prefix+=["taskset","-c",affinity]
        middle.append((action,out/(action+"-01.command.json"),prefix+plan["cli"][action]))
    stages=[first,*middle,last]
    for _,receipt,_ in stages:need(not receipt.exists(),"existing completed or interrupted stage receipt")
    locked={str(a.plan):sha(a.plan),str(a.review):sha(a.review),str(executor):sha(executor),str(recorder):sha(recorder),str(Path(__file__).resolve()):sha(__file__)}
    for name,digest in plan["adapter_copy"]["files"].items():locked[str(Path(plan["adapter_copy"]["source"])/name)]=digest
    state=dict(started_monotonic_ns=time.monotonic_ns(),boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),monotonic_scope="outer orchestration stages only; not per-EMU overlap measurement",contract="clean02-reviewed-config-reuse-pipeline-v2-strict-c-retry",status="READY",started=now(),pid=os.getpid(),plan_sha256=PLAN_SHA,review_sha256=sha(a.review),source_files=locked,affinity=affinity,stages=[],active=None,target_process_limit=5,target_execution_delegated_to_fixed_probe=True)
    def save():
        a.state.parent.mkdir(parents=True,exist_ok=True);temp=a.state.with_suffix(".tmp");temp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n");temp.replace(a.state)
    save()
    try:
        for name,receipt,command in stages:
            need(all(sha(path)==digest for path,digest in locked.items()),"frozen pipeline input changed")
            state.update(status="RUNNING_"+name.upper(),active=name);save()
            argv=["python3","-B",str(recorder),str(receipt),str(repo),*command]
            started=now();started_monotonic_ns=time.monotonic_ns();code=subprocess.run(argv,cwd=repo,env={**os.environ,"GIT_OPTIONAL_LOCKS":"0","PYTHONDONTWRITEBYTECODE":"1"}).returncode
            recorded=read(receipt)
            state["stages"].append(dict(started_monotonic_ns=started_monotonic_ns,finished_monotonic_ns=time.monotonic_ns(),name=name,command=command,receipt=str(receipt),receipt_sha256=sha(receipt),started=started,finished=now(),exit_code=code));save()
            need(code==0 and recorded.get("exit_code")==0 and recorded["command"]==command,"stage failed: "+name)
            if name=="import":need(read(out/"preflight/import.json")["status"]=="CONFIG_REUSE_UNTRACKED_IMPORT_IDENTITY_UNCHANGED","import identity failed")
            if name=="build":
                value=read(out/"build-01/state.json")
                need(value["status"]=="CURRENT_CONFIG_REUSE_PROBE_STATIC_PASS" and value["images_completed"]==2,"two-image static build failed")
            if name=="run":
                value=read(out/"run-01/results.json")
                need(value["functional_status"]=="FUNCTIONAL_PASS" and value["new_emu_runs"]==5 and value["status"] in {"PERFORMANCE_CANDIDATE","REJECT","INCONCLUSIVE"},"bounded runtime failed")
                state["performance_decision"]=value["status"];state["actual_target_processes"]=5
            if name=="audit":need(read(out/"audit-01.json")["status"]=="PROBE_LOCAL_RAW_AUDIT_PASS","raw audit failed")
            if name=="after-audit":need(read(out/"preflight/after-audit.json")["status"]=="CONFIG_REUSE_PROBE_IDENTITY_UNCHANGED","final identity failed")
        state.update(status="FIVE_STAGE_COMMANDS_PASS_ROOT_RESULT_REVIEW_PENDING",active=None)
    except BaseException as e:
        state.update(status="FAILED",error=repr(e));raise
    finally:
        probe_state=out/"run-01/state.json"
        if probe_state.exists():state["actual_target_processes"]=read(probe_state).get("new_emu_runs")
        state["finished_monotonic_ns"]=time.monotonic_ns()
        state["finished"]=now();save()
    print(json.dumps({k:state.get(k) for k in ("status","performance_decision","actual_target_processes")}))
if __name__=="__main__":main()
