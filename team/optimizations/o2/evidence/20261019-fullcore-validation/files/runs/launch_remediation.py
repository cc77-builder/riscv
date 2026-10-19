import json,subprocess
from pathlib import Path
from datetime import datetime,timezone
w=Path("/home/riscv/riscv-lab/o2-fullcore-20261019")
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
def now():return datetime.now(timezone.utc).isoformat()
state=dict(status="STARTED",started=now(),stages=[],original_core_reused="core-02",source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=r,text=True).strip())
def save():
    p=w/"remediation-launch-state.json"
    t=p.with_suffix(".tmp");t.write_text(json.dumps(state,indent=2)+"\n");t.replace(p)
save()
jobs=[
 ("supplements-02",["python3","-B","team/optimizations/o2/fullcore/run_supplements.py","--output",str(w/"supplements-02"),"--hardware-pins",str(w/"build-03/hardware-inputs.json"),"--emu",str(r/"build/emu"),"--jobs","2"]),
 ("recheck-02",["python3","-B","team/optimizations/o2/fullcore/recheck.py","--campaign",str(w/"core-02"),"--supplements",str(w/"supplements-02"),"--output",str(w/"recheck-02")])]
for name,cmd in jobs:
    row=dict(name=name,command=cmd,started=now(),status="RUNNING")
    state["stages"].append(row);state["status"]=name.upper()+"_RUNNING";save()
    with (w/(name+"-launch.stdout.log")).open("xb") as out,(w/(name+"-launch.stderr.log")).open("xb") as err:
        rc=subprocess.run(cmd,cwd=r,stdout=out,stderr=err).returncode
    row.update(status="EXITED",exit_code=rc,finished=now());save()
state.update(status="ALL_COMMANDS_FINISHED",finished=now());save()
raise SystemExit(0 if all(x["exit_code"]==0 for x in state["stages"]) else 1)
