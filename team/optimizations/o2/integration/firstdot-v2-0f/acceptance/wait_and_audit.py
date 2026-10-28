"""Continue the bounded audit after the one actual supplementary execution completes."""
import json, subprocess, sys, time
from pathlib import Path
W=Path("/home/riscv/riscv-lab/software-import-20261026")
R=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
A=R/"team/optimizations/o2/integration/firstdot-v2-0f/acceptance"
run=W/"r5-g5-acceptance-01/clock-supplement-03"
deadline=time.monotonic()+7400
while True:
 state=json.loads((run/"state.json").read_text())
 if state["status"]=="FAILED":raise RuntimeError(state)
 if state["status"]=="R5_G5_COMPOSITE_FULLCORE_PASS":break
 if time.monotonic()>deadline:raise RuntimeError("bounded wait expired; inspect retained process")
 time.sleep(15)
cmd=["python3","-B",str(A/"audit_composite.py"),"--run",str(run),
 "--output",str(W/"r5-g5-acceptance-01/composite-audit-01"),
 "--old",str(W/"clean-02/fullcore-run-01"),"--source",str(W/"clean-02/checkout/source"),
 "--adapter",str(W/"clean-02/checkout/source/team/optimizations/o2/integration/firstdot-v2-0f/clean")]
print("Executing",json.dumps(cmd),flush=True)
raise SystemExit(subprocess.run(cmd,cwd=R).returncode)
