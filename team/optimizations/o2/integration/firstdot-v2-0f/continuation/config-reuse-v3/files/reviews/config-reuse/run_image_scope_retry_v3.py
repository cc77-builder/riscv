"""One fresh five-process probe after the V2 image-role tooling failure."""
import hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
D=W/"reviews/config-reuse";OUT=W/"config-reuse-clean02-02"
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,why):
    if not ok:raise ValueError(why)
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def now():return datetime.now(timezone.utc).isoformat()
def main():
    review_path=Path(sys.argv[1]);review=read(review_path)
    need(review["approved"] is True and review["driver_sha256"]==sha(__file__),"actual root source review missing")
    locked=review["source_pins"]|{str(review_path):sha(review_path)}
    def check():need(all(sha(p)==h for p,h in locked.items()),"protected input changed")
    check()
    need(not OUT.exists(),"new output required; no resume")
    plan=read(D/"clean02-launch-plan-v4.json")
    executor=D/"execute_clean02_stage_v3.py"
    sp=importlib.util.spec_from_file_location("retry_executor",executor);ex=importlib.util.module_from_spec(sp);sp.loader.exec_module(ex)
    need(ex.gate_metadata(plan)==read(D/"actual-clean-readiness-01.json"),"clean qualification changed")
    ex.source_inputs(plan,imported=True)
    need(read(D/"pipeline-state-01.json")["status"]=="FAILED" and
         read(D/"pipeline-state-01.json")["actual_target_processes"]==2,"old failure not preserved")
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():continue
        try:cmd=(proc/"cmdline").read_bytes().split(b"\0")[0].decode()
        except (OSError,UnicodeError):continue
        need(Path(cmd).name not in {"emu","verilator_bin","riscv64-nemu-interpreter"},"active target "+str(proc))
    before=ex.capture_identity(plan)
    need(before==read(W/"config-reuse-clean02-01/preflight/identity-before.json"),"identity changed after V2 failure")
    OUT.mkdir();save(OUT/"identity-before.json",before)
    cores=sorted(os.sched_getaffinity(0))[:4];need(cores,"no allowed CPU")
    affinity=",".join(map(str,cores));repo=Path(plan["paths"]["repo"])
    state=dict(status="READY",contract="config-reuse-image-scope-v3-retry",started=now(),
        started_monotonic_ns=time.monotonic_ns(),boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        monotonic_scope="outer stages only; no per-EMU OS capacity measurement",stages=[],new_target_limit=5,
        old_failed_target_processes=2,production_rtl_changed=False,default_changed=False,
        review_sha256=sha(review_path),pid=os.getpid())
    save(OUT/"state.json",state)
    base=["env","GIT_OPTIONAL_LOCKS=0","python3","-B",str(D/"adapter-v3/probe.py"),
          "--repo",str(repo),"--identity",str(W/"clean-02/identity/current.json"),
          "--matrix",str(W/"clean-02/matrix-build-01"),"--matrix-run",str(W/"clean-02/matrix-run-01")]
    try:
        for action in ["build","run","audit"]:
            command=list(base)
            if action=="run":command[2:2]=["taskset","-c",affinity]
            command+=["--action",action,"--output",str(OUT/("audit-01.json" if action=="audit" else action+"-01"))]
            if action!="build":command+=["--build",str(OUT/"build-01")]
            if action=="run":command+=["--operation-id","20261027-config-reuse-image-scope-v3-01"]
            if action=="audit":command+=["--campaign",str(OUT/"run-01")]
            check();state["status"]="RUNNING_"+action.upper();save(OUT/"state.json",state)
            receipt=OUT/(action+"-01.command.json");need(not receipt.exists(),"receipt exists")
            start=time.monotonic_ns()
            code=subprocess.run(["python3","-B",str(W/"run_recorded.py"),str(receipt),str(repo),*command],
              cwd=repo,env={**os.environ,"GIT_OPTIONAL_LOCKS":"0","PYTHONDONTWRITEBYTECODE":"1"}).returncode
            state["stages"].append(dict(name=action,started_monotonic_ns=start,
              finished_monotonic_ns=time.monotonic_ns(),exit_code=code,receipt=str(receipt),receipt_sha256=sha(receipt)))
            save(OUT/"state.json",state)
            need(code==0 and read(receipt)["exit_code"]==0,"stage failed "+action)
        result=read(OUT/"run-01/results.json");audit=read(OUT/"audit-01.json")
        need(result["new_emu_runs"]==5 and result["functional_status"]=="FUNCTIONAL_PASS" and
             audit["status"]=="PROBE_LOCAL_RAW_AUDIT_PASS","result/raw audit failed")
        after=ex.capture_identity(plan);save(OUT/"identity-after.json",after)
        need(after==before,"physical identity/index changed")
        ex.source_inputs(plan,imported=True);check()
        need(ex.gate_metadata(plan)==read(D/"actual-clean-readiness-01.json"),"clean evidence changed")
        state.update(status="PROBE_V3_ALL_STAGES_PASS_RESULT_REVIEW_PENDING",performance_decision=result["status"],
          actual_target_processes=5,physical_identity_unchanged=True)
    except BaseException as e:
        state.update(status="FAILED",error=repr(e));raise
    finally:
        if (OUT/"run-01/state.json").exists():state["actual_target_processes"]=read(OUT/"run-01/state.json")["new_emu_runs"]
        state.update(finished=now(),finished_monotonic_ns=time.monotonic_ns());save(OUT/"state.json",state)
    print(json.dumps({k:state[k] for k in ["status","performance_decision","actual_target_processes"]}))
if __name__=="__main__":main()
