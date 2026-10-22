from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
w=Path("/home/riscv/riscv-lab/o3-gemv-20261019")
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
cmd=["python3","-B","team/workloads/o3-gemv/resume.py","--previous",str(w/"campaign-01"),"--images",str(w/"images-02"),"--output",str(w/"campaign-02")]
state=dict(status="RUNNING",command=cmd,cwd=str(r),started_utc=datetime.now(timezone.utc).isoformat(),recovery=True)
def save():
 t=w/"recovery-launch-state.json.tmp";t.write_text(json.dumps(state,indent=2)+"\n");t.replace(w/"recovery-launch-state.json")
save()
with (w/"campaign-02.stdout.log").open("xb") as a,(w/"campaign-02.stderr.log").open("xb") as b:
 rc=subprocess.run(cmd,cwd=r,stdout=a,stderr=b).returncode
state.update(status="EXITED",exit_code=rc,finished_utc=datetime.now(timezone.utc).isoformat());save()
print(json.dumps(state),flush=True)
raise SystemExit(rc)
