import json,subprocess
from pathlib import Path
from datetime import datetime,timezone
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
w=Path("/home/riscv/riscv-lab/o3-gemv-20261019")
command=["python3","-B","team/workloads/o3-gemv/campaign.py","--images",str(w/"images-02"),"--output",str(w/"campaign-01")]
def now():return datetime.now(timezone.utc).isoformat()
state=dict(status="RUNNING",command=command,cwd=str(r),started_utc=now())
def save():(w/"launch-state.json").write_text(json.dumps(state,indent=2)+"\n")
save()
with (w/"campaign-01.stdout.log").open("xb") as a,(w/"campaign-01.stderr.log").open("xb") as b:
 rc=subprocess.run(command,cwd=r,stdout=a,stderr=b).returncode
state.update(status="EXITED",exit_code=rc,finished_utc=now());save()
print(json.dumps(state),flush=True)
raise SystemExit(rc)
