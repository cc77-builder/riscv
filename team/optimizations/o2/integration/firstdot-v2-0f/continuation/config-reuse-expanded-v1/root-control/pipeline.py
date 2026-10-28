from pathlib import Path
import json,hashlib,subprocess,os,sys,importlib.util
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent
TOOLS=W/"reviews/config-reuse/expansion-v1"
OUT=W/"config-reuse-expanded-01"
SOURCE=W/"clean-02/checkout/source"
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def require(x,s):
    if not x:raise RuntimeError(s)
review=read(HERE/"review.json")
def sources():
    for path,digest in review["frozen_files"].items():
        p=Path(path);require(p.is_file() and not p.is_symlink() and sha(p)==digest,"frozen file changed "+path)
sources()
require(review["status"]=="ROOT_REVIEW_READY","review not ready")
for path in review["host_test_commands"]:
    require(read(Path(path)).get("exit_code")==0,"host tests incomplete "+path)
require(not OUT.exists(),"new output required")
require(read(HERE/"preflight.command.json").get("exit_code")==0,"preflight incomplete")
OUT.mkdir()
state=dict(status="STARTING",started=now(),review_sha256=sha(HERE/"review.json"),new_target_runs=0,
    hardware_changed=False,default_changed=False,uploaded=False)
save(OUT/"state.json",state)
base=["--repo",str(SOURCE),"--identity",str(W/"clean-02/identity/current.json"),
      "--matrix",str(W/"clean-02/matrix-build-01"),"--matrix-run",str(W/"clean-02/matrix-run-01")]
stages=[
    ("build",["python3","-B",str(TOOLS/"matrix.py"),*base,"--action","build","--output",str(OUT/"build-01")]),
    ("run",["taskset","-c","0,1,2,3","python3","-B",str(TOOLS/"matrix.py"),*base,"--action","run",
        "--build",str(OUT/"build-01"),"--output",str(OUT/"run-01"),"--workers","4",
        "--operation-id","zjhwork-config-reuse-expanded-20261027-01"]),
    ("audit",["python3","-B",str(TOOLS/"raw_audit.py"),*base,"--build",str(OUT/"build-01"),
        "--campaign",str(OUT/"run-01"),"--output",str(OUT/"audit-01.json")])]
try:
    for name,argv in stages:
        sources()
        if name=="run":
            alive=[]
            for p in Path("/proc").iterdir():
                if p.name.isdigit():
                    try:
                        if (p/"exe").resolve().name=="emu":alive.append(p.name)
                    except (OSError,RuntimeError):pass
            require(not alive,"existing EMU before expansion "+str(alive))
            require(read(OUT/"build-01/state.json")["status"]=="CURRENT_CONFIG_REUSE_MATRIX_STATIC_PASS","static build gate")
        state.update(status=name.upper(),stage=name,stage_started=now())
        save(OUT/"state.json",state)
        receipt=OUT/(name+".command.json")
        require(not receipt.exists(),"existing command receipt")
        code=subprocess.run(["python3","-B",str(W/"run_recorded.py"),str(receipt),str(SOURCE),*argv],cwd=SOURCE).returncode
        require(code==0 and read(receipt).get("exit_code")==0,name+" command failed")
    state["status"]="FINAL_IDENTITY"
    save(OUT/"state.json",state)
    helper=W/"reviews/config-reuse/execute_clean02_stage_v3.py"
    spec=importlib.util.spec_from_file_location("final_readonly_gate",helper)
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    plan=read(W/"reviews/config-reuse/clean02-launch-plan-v4.json")
    final=gate.capture_identity(plan)
    require(final==read(HERE/"identity-before.json"),"final physical identity/index changed")
    save(OUT/"identity-after.json",final)
    sources()
    result=read(OUT/"run-01/results.json");audit=read(OUT/"audit-01.json")
    require(result["new_emu_runs"]==audit["actual_target_processes"]==33,"target cardinality")
    require(audit["status"]=="EXPANDED_MATRIX_LOCAL_RAW_AUDIT_PASS","raw audit")
    state.update(status="EXPANDED_MATRIX_AND_RAW_AUDIT_PASS",new_target_runs=33,decisions=result["decisions"],
        identity_unchanged=True,source_files_unchanged=True)
    save(OUT/"completion.json",dict(state,finished=now(),run_sha256=sha(OUT/"run-01/results.json"),
        audit_sha256=sha(OUT/"audit-01.json"),identity_after_sha256=sha(OUT/"identity-after.json")))
except BaseException as exc:
    state.update(status="FAILED",error=repr(exc))
    raise
finally:
    state["finished"]=now()
    save(OUT/"state.json",state)
print("EXPANDED_MATRIX_AND_RAW_AUDIT_PASS")
