"""Dependency gate: start the planned matrix only after the clean fullcore run exits successfully."""
from pathlib import Path
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
w=Path("/home/riscv/riscv-lab/software-import-20261026")
root=w/"clean-02"
plan_path=w/"clean-02-postbuild-plan.json"
plan=json.loads(plan_path.read_text())
out=root/"matrix-waiter-01.json"
if out.exists(): raise FileExistsError(out)
state=dict(status="WAITING_FOR_FULLCORE",started=datetime.now(timezone.utc).isoformat(),
           driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
           matrix_launched=False)
def save():
    tmp=out.with_suffix(".tmp")
    tmp.write_text(json.dumps(state,indent=2)+"\n")
    tmp.replace(out)
save()
try:
    receipt=root/"fullcore-run-01.command.json"
    while True:
        value=json.loads(receipt.read_text()) if receipt.exists() else {}
        if value.get("exit_code") is not None:
            if value["exit_code"] != 0:
                raise RuntimeError("Fullcore outer process failed; no matrix launch")
            break
        time.sleep(5)
    fullcore=json.loads((root/"fullcore-run-01/state.json").read_text())
    if fullcore["status"]!="CURRENT_CLEAN_FULLCORE_PASS":
        raise ValueError("Fullcore controller did not pass")
    c_receipt=root/"c-run-01.command.json"
    if c_receipt.exists() and json.loads(c_receipt.read_text()).get("exit_code") not in (None,0):
        raise RuntimeError("C already failed; no matrix launch")
    if json.loads((root/"program-byte-comparison-01.json").read_text())["status"]!="CURRENT_CLEAN_PROGRAM_BYTES_EQUAL_RUNTIME_NOT_COMPARED":
        raise ValueError("Program-byte gate not passed")
    if hashlib.sha256(plan_path.read_bytes()).hexdigest()!=state["plan_sha256"]:
        raise ValueError("Plan changed")
    stage=plan["stages"]["matrix"]
    if Path(stage["receipt"]).exists() or (root/"matrix-run-01").exists():
        raise FileExistsError("Matrix output/receipt already exists")
    argv=["taskset","-c",stage["affinity"],"python3","-B",str(w/"run_recorded.py"),
          stage["receipt"],plan["repo"],*stage["command"]]
    state.update(status="MATRIX_RUNNING",matrix_launched=True,fullcore_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),argv=argv)
    save()
    print("FULLCORE_EXIT_ZERO_START_MATRIX",flush=True)
    code=subprocess.run(argv).returncode
    state["matrix_outer_exit_code"]=code
    if code: raise RuntimeError("Matrix process failed")
    value=json.loads((root/"matrix-run-01/state.json").read_text())
    if value["status"]!="CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS":
        raise ValueError("Matrix controller did not pass")
    state["status"]="CLEAN_CORE_GATE_AND_MATRIX_PASS"
except BaseException as error:
    state.update(status="FAILED",error=repr(error))
    raise
finally:
    state["finished"]=datetime.now(timezone.utc).isoformat()
    save()
