"""Wait for the exact C1 local/PPA attempt, then run the declared screen once."""
import datetime,json,subprocess,time,hashlib,shutil
from pathlib import Path
w=Path("/home/riscv/riscv-lab/o2-c1-owner-20261025")
source=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
script=source/"team/optimizations/o2/r3-div-gate/c1/screen.py"
snapshot=w/"screen.snapshot.py"
assert not snapshot.exists()
shutil.copy2(script,snapshot)
rec=dict(status="waiting_for_standard_ppa",started=datetime.datetime.now().astimezone().isoformat(),
         script_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest())
def save(): (w/"screen-controller.json").write_text(json.dumps(rec,indent=2)+"\n")
save()
while True:
    state=json.loads((w/"campaign-02.json").read_text())
    if state["status"]=="failed":
        rec.update(status="blocked_by_failed_local_or_ppa");save();raise SystemExit(1)
    if state["status"]=="LOCAL_AND_STANDARD_PPA_COMPLETE_AWAIT_SCREEN":break
    time.sleep(10)
assert json.loads((w/"state-trace-replay.json").read_text())["status"]=="C1_REAL_PARENT_STATE_REPLAY_PASS"
assert json.loads((w/"local-audit.json").read_text())["status"]=="C1_LOCAL_AND_GENERATION_AUDIT_PASS"
cmd=["python3","-B",str(snapshot),"--work",str(w),"--baseline","/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025","--source-repo",str(source),"--output",str(w/"screen-01")]
rec.update(status="running",command=cmd,run_started=datetime.datetime.now().astimezone().isoformat());save()
with (w/"screen.log").open("xb") as f:
    rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
rec.update(exit_code=rc,finished=datetime.datetime.now().astimezone().isoformat(),status="completed" if rc==0 else "failed");save()
print(json.dumps(rec,indent=2))
if (w/"screen-01/result.json").exists():
    x=json.loads((w/"screen-01/result.json").read_text());print(json.dumps({k:v for k,v in x.items() if k!="comparisons"},indent=2))
raise SystemExit(rc)
