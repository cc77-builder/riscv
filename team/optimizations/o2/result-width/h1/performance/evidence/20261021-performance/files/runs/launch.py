from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,os,traceback
R=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
W=Path("/home/riscv/riscv-lab/o2-h1-performance-20261021")
HEAD="f732d92d13fb47fdf9eea46d32c5e77bd4343363"
ENTRY="team/optimizations/o2/result-width/h1/performance"
def now():return datetime.now(timezone.utc).isoformat()
def save(p,data):
 t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n");t.replace(p)
state={"status":"RUNNING","pid":os.getpid(),"started":now(),"runtime_commit":HEAD,"steps":[]}
path=W/"supervisor-state.json"
assert not path.exists()
save(path,state)
try:
 for name,cmd in [
  ("campaign",["bash","-c","source team/scripts/activate.sh\npython3 -B "+ENTRY+"/compare.py --output "+str(W/"campaign-01")]),
  ("recheck",["bash","-c","source team/scripts/activate.sh\npython3 -B "+ENTRY+"/results.py --campaign "+str(W/"campaign-01")+" --output "+str(W/"results-01")])]:
  assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=R,text=True).strip()==HEAD
  step={"name":name,"status":"RUNNING","started":now(),"command":cmd}
  state["steps"].append(step);save(path,state)
  with (W/(name+".log")).open("xb") as out:
   p=subprocess.Popen(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT)
   step["pid"]=p.pid;save(path,state)
   rc=p.wait()
  step.update(status="PASS" if rc==0 else "FAILED",exit_code=rc,finished=now());save(path,state)
  if rc:raise RuntimeError(name+" failed with exit "+str(rc))
  assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=R,text=True).strip()==HEAD
 result=json.loads((W/"results-01/verification.json").read_text())
 state.update(status="B0_H1_MEASUREMENT_AND_RECHECK_PASS",
              cycle_nonregression_pass=result["cycle_nonregression_pass"],
              exact_measured_cycle_equality=result["exact_measured_cycle_equality"],finished=now())
except BaseException as e:
 state.update(status="FAILED",error=repr(e),finished=now())
 traceback.print_exc()
finally:
 save(path,state)
 print(state["status"],flush=True)
