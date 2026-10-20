import json,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
w=Path("/home/riscv/riscv-lab/o2-performance-20261019")
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
def now():return datetime.now(timezone.utc).isoformat()
state=dict(status="WAITING_FOR_MATCHED_O1_BUILD",started_utc=now(),stages=[])
def save():
    p=w/"launch-state.json";t=p.with_suffix(".tmp");t.write_text(json.dumps(state,indent=2)+"\n");t.replace(p)
save()
while True:
    b=json.loads((w/"o1-build-01/build-state.json").read_text())
    if b["status"]=="O1_MATCHED_BUILD_PASS":break
    if b["status"]=="FAILED":
        state.update(status="BUILD_FAILED",finished_utc=now());save();raise SystemExit(1)
    time.sleep(5)
for name,command in [
    ("campaign-01",["python3","-B","team/optimizations/o2/performance/compare.py","--output",str(w/"campaign-01")]),
    ("results-01",["python3","-B","team/optimizations/o2/performance/results.py","--campaign",str(w/"campaign-01"),"--output",str(w/"results-01")])
]:
    row=dict(name=name,command=command,status="RUNNING",started_utc=now())
    state["stages"].append(row);state["status"]=name.upper()+"_RUNNING";save()
    with (w/(name+".stdout.log")).open("xb") as out,(w/(name+".stderr.log")).open("xb") as err:
        rc=subprocess.run(command,cwd=r,stdout=out,stderr=err).returncode
    row.update(status="EXITED",exit_code=rc,finished_utc=now());save()
    if rc:state.update(status="FAILED",finished_utc=now());save();raise SystemExit(rc)
state.update(status="ALL_COMMANDS_FINISHED",finished_utc=now());save()
