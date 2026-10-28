#!/usr/bin/env python3
"""Wait for the original paired run, recheck it, then run fixed local cost/STA."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import time

ROOT=Path(__file__).resolve().parents[5]
LAB=ROOT.parents[1]
WORK=LAB/"o2-r3-div-gate-cost-20261025"
PERF=LAB/"o2-r3-div-gate-performance-20261025"
TOOLS=LAB/"o4-cost-20261020"
MODULE=Path(__file__).resolve().parent

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(json.dumps(d,indent=2)+"\n");tmp.replace(p)
def need(v,m):
    if not v: raise ValueError(m)

def main():
    need(not (WORK/"campaign-state.json").exists(),"controller already has state")
    source_pins=json.loads((LAB/"o2-r3-div-gate-fullcore-20261024/build-01/hardware-inputs.json").read_text())
    files={str(ROOT/n):d for group in ("files","dependency_files") for n,d in source_pins[group].items()}
    for p in (ROOT/"team/optimizations/o4").iterdir():
        if p.is_file() and p.suffix in (".py",".scala",".json",".md"):files[str(p)]=sha(p)
    paths=[*MODULE.glob("*.py"),MODULE/"CONTRACT.md",
        ROOT/"team/optimizations/o2/r3-div-gate/performance/recheck.py",
        ROOT/"team/optimizations/o2/result-width/h1/compare_cost.py",
        TOOLS/"library/NangateOpenCellLibrary_typical.lib",
        TOOLS/"tools/executable-identities.json",
        LAB/"o2-h1-result32-20261021/candidate-inputs.json",
        ROOT/"team/optimizations/o2/result-width/h1/evidence/20261021-local/manifest.json"]
    identities=json.loads((TOOLS/"tools/executable-identities.json").read_text())
    for name,rec in identities.items():
        files[str(TOOLS/"tools/root/usr/bin"/name)]=rec["sha256"]
        files.update(rec["shared_library_sha256"])
    for p in paths:files[str(p)]=sha(p)
    pins=dict(source_commit=source_pins["source_commit"],files=files,hardware_build_pins_sha256=sha(LAB/"o2-r3-div-gate-fullcore-20261024/build-01/hardware-inputs.json"))
    save(WORK/"candidate-inputs.json",pins)
    def unchanged():
        for p,d in files.items():need(sha(p)==d,"frozen input changed: "+p)
    unchanged()
    state=dict(status="waiting_for_performance",pid=os.getpid(),started=stamp(),steps=[],hardware_steps_complete=False)
    save(WORK/"campaign-state.json",state)
    try:
        while True:
            s=json.loads((PERF/"campaign-01/state.json").read_text())
            if s["status"]=="FAILED":raise RuntimeError("performance failed; inspect original logs; no automatic retry")
            if s["status"]=="BEFORE_AFTER_PAIRED_PERFORMANCE_PASS":break
            time.sleep(15)
        state["status"]="running";save(WORK/"campaign-state.json",state)
        commands=[("performance-recheck",["python3","-B","team/optimizations/o2/r3-div-gate/performance/recheck.py","--campaign",str(PERF/"campaign-01"),"--output",str(PERF/"results-01")])]
        for boundary in ("fu","parent"):
            gen,mapping,sta=[WORK/(boundary+s) for s in ("-cost-01","-map-01","-sta-01")]
            commands.extend([
                (boundary+"-elaborate",["python3","-B","team/optimizations/o4/elaborate.py","o2",boundary,str(gen)]),
                (boundary+"-map",["python3","-B","team/optimizations/o4/synthesize.py",str(gen),str(mapping),"--work",str(TOOLS)]),
                (boundary+"-sta",["python3","-B","team/optimizations/o4/timing.py",str(mapping),str(sta),"--work",str(TOOLS)])])
        commands.append(("cost-audit",["python3","-B","team/optimizations/o2/r3-div-gate/cost/compare.py","--work",str(WORK),"--baseline",str(LAB/"o2-h1-result32-20261021"),"--tools",str(TOOLS),"--output",str(WORK/"results-01")]))
        for name,cmd in commands:
            unchanged()
            if name=="cost-audit":
                state["hardware_steps_complete"]=True
                save(WORK/"campaign-state.json",state)
            step=dict(name=name,command=cmd,cwd=str(ROOT),started=stamp(),status="running",log=name+".log")
            state["steps"].append(step);save(WORK/"campaign-state.json",state)
            print("START",name,flush=True)
            with (WORK/step["log"]).open("xb") as log:
                p=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                    env=dict(os.environ,PYTHONUNBUFFERED="1",JAVA_OPTS="-Xmx12G -Xss16m",BUILD_JOBS="2"))
                step["pid"]=p.pid;save(WORK/"campaign-state.json",state)
                rc=p.wait()
            step.update(exit_code=rc,finished=stamp(),status="passed" if rc==0 else "failed")
            save(WORK/"campaign-state.json",state)
            need(rc==0,name+" failed; preserve attempt and diagnose")
            unchanged()
            if name=="performance-recheck":
                review=json.loads((PERF/"results-01/verification.json").read_text())
                state["cycle_nonregression_pass"]=review["cycle_nonregression_pass"]
                # Even a measured regression must remain visible; cost can still be evaluated.
                save(WORK/"campaign-state.json",state)
            print("PASS",name,flush=True)
        state.update(status="passed",finished=stamp(),frozen_inputs_unchanged=True)
        save(WORK/"campaign-state.json",state)
        print("R3_DIV_GATE_PERFORMANCE_AND_COST_CAMPAIGN_PASS",flush=True)
    except BaseException as e:
        state.update(status="failed",error=repr(e),finished=stamp());save(WORK/"campaign-state.json",state)
        raise

if __name__=="__main__":main()
