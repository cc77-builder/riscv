import json, subprocess, time
from pathlib import Path
from datetime import datetime, timezone
root=Path("/home/riscv/riscv-lab/o2-fullcore-20261019")
repo=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
def now(): return datetime.now(timezone.utc).isoformat()
def save(data):
    p=root/"launch-state.json"
    t=p.with_suffix(".tmp");t.write_text(json.dumps(data,indent=2)+"\n");t.replace(p)
state={"status":"WAITING_FOR_BUILD","started":now(),"stages":[]}
save(state)
while True:
    build=json.loads((root/"build-03/build-state.json").read_text())
    if build["status"]=="O2_FULLCORE_BUILD_PASS": break
    if build["status"]=="FAILED":
        state.update(status="BUILD_FAILED",finished=now());save(state);raise SystemExit(1)
    time.sleep(5)
common=["--hardware-pins",str(root/"build-03/hardware-inputs.json"),"--emu",str(repo/"build/emu")]
jobs=[
    ("core",["python3","-B","team/optimizations/o2/fullcore/run_suite.py","--output",str(root/"core-02"),*common,"--jobs","2"]),
    ("supplements",["python3","-B","team/optimizations/o2/fullcore/run_supplements.py","--output",str(root/"supplements-01"),*common,"--jobs","2"]),
    ("offline",["python3","-B","team/optimizations/o2/fullcore/recheck.py","--campaign",str(root/"core-02"),"--supplements",str(root/"supplements-01"),"--output",str(root/"recheck-01")]),
]
for name,command in jobs:
    record={"stage":name,"command":command,"started":now(),"status":"RUNNING"}
    state["stages"].append(record);state["status"]=name.upper()+"_RUNNING";save(state)
    with (root/(name+"-launch.stdout.log")).open("wb") as out,(root/(name+"-launch.stderr.log")).open("wb") as err:
        rc=subprocess.run(command,cwd=repo,stdout=out,stderr=err).returncode
    record.update(status="EXITED",exit_code=rc,finished=now());save(state)
state.update(status="ALL_COMMANDS_FINISHED",finished=now());save(state)
raise SystemExit(0 if all(x["exit_code"]==0 for x in state["stages"]) else 1)
