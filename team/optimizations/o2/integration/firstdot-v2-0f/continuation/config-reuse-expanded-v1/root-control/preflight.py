from pathlib import Path
import json, hashlib, importlib.util, subprocess, os
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent
MAIN=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
def now(): return datetime.now(timezone.utc).isoformat()
def save(name,value):
    p=HERE/name
    if p.exists(): raise RuntimeError("existing "+str(p))
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(["git",*args],cwd=MAIN,text=True).strip()
started=now()
helper=W/"reviews/config-reuse/execute_clean02_stage_v3.py"
assert sha(helper)=="889228456990c98a4793312ea1f41b2546977a107f18433a8549a881184f1340"
spec=importlib.util.spec_from_file_location("frozen_readonly_readiness",helper)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
plan=json.loads((W/"reviews/config-reuse/clean02-launch-plan-v4.json").read_text())
ready=gate.gate_metadata(plan)
gate.source_inputs(plan,imported=True)
identity=gate.capture_identity(plan)
assert identity==json.loads((W/"config-reuse-clean02-02/identity-after-02.json").read_text())
assert git("rev-parse","HEAD")=="c823a8786e052c6e26f6915563c42b6d730dd8e3"
assert git("branch","--show-current")=="local/zjhwork-integration-20261024"
assert git("diff","HEAD","--","src")==""
live=[]
for p in Path("/proc").iterdir():
    if not p.name.isdigit(): continue
    try:
        exe=(p/"exe").resolve()
        if exe.name=="emu":
            live.append(dict(pid=int(p.name),exe=str(exe),argv=(p/"cmdline").read_bytes().replace(b"\x00",b" ").decode(errors="replace")))
    except (FileNotFoundError,PermissionError,ProcessLookupError): pass
assert not live,live
save("identity-before.json",identity)
save("preflight.json",dict(status="FROZEN_INPUTS_AND_LOCAL_IDLE_PASS",started=started,finished=now(),
    readiness=ready,main_head=git("rev-parse","HEAD"),main_branch=git("branch","--show-current"),
    main_status=git("status","--short"),production_src_diff_empty=True,
    live_emus=live,meminfo=Path("/proc/meminfo").read_text(),affinity=sorted(os.sched_getaffinity(0)),
    prior_probe_completion_sha256=sha(W/"config-reuse-clean02-02/completion-02.json"),
    task_scope=dict(shapes=[[4,8],[8,32],[16,64],[4,13]],datasets=[0,1,2],images=24,target_processes=33,max_workers=4,
    formal_windows=384,normal_windows=768,replay_pairs=192,ordinary_new_public_C="NOT_TESTED",rtl_modified=False,upload=False)))
print("EXPANSION_PREFLIGHT_PASS")
