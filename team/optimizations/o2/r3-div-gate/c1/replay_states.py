"""Replay actual parent observations through both state equations and compare baseline."""
import argparse,json,hashlib,importlib.util
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
p=argparse.ArgumentParser();p.add_argument("--work",type=Path,required=True);p.add_argument("--source-repo",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
need(not a.output.exists(),"output exists")
prior=Path("/home/riscv/riscv-lab/o2-r3-div-gate-20261024")
archive=a.source_repo/"team/optimizations/o2/r3-div-gate/evidence/20261024-local/manifest.json"
manifest={x["path"]:x["raw_sha256"] for x in json.loads(archive.read_text())["files"]}
base=prior/"green-parent-01/result.log";candidate=a.work/"parent-01/result.log"
need(sha(base)==manifest["runs/green-parent-01/result.log"],"baseline log changed")
for name in ["parent_test.cpp","check_trace.py","check_negative.py"]:
    old=a.source_repo/"team/optimizations/o2/parent"/name
    new=a.work/"repo/team/optimizations/o2/parent"/name
    need(sha(old)==sha(new),"checker/stimulus mismatch")
oldrows=[s for s in base.read_text().splitlines() if s.startswith("O2_PARENT_")]
newrows=[s for s in candidate.read_text().splitlines() if s.startswith("O2_PARENT_")]
need(oldrows==newrows,"baseline and C1 observed trajectories differ; inspect rather than waive")
busy=owner=hi=hf=0;cycles=0;events=dict(accept_int=0,accept_float=0,cancel=0,reset=0,complete=0)
for line in newrows:
    if not line.startswith("O2_PARENT_CYCLE "):continue
    row=dict(x.split("=",1) for x in line.split()[1:])
    n=lambda k:int(row[k])
    fire=n("child_fire")>>1;out=n("child_out")>>1
    need(fire in (0,1,2),"multiple DIV acceptance")
    if busy:need(out in (0,1<<owner),"non-owner output while busy")
    need((bool(hi),bool(hf))==(bool(busy and owner==0),bool(busy and owner==1)),"state mapping before cycle")
    expected=fire|(hi)|(hf<<1)
    actual=(n("clocks")>>1)&3
    need(actual==(3 if n("te") else expected),f"clock differs at {n('cycle')}")
    if fire:
        need(not (busy or n("reset") or n("redirect") or out or n("occupancy")),"accept priority assumption violated")
        need(n("child_ready")&6==6,"DIV acceptance without both ready")
    done=out if n("out_ready") else 0
    kill=n("kill_div")
    need(not kill or busy,"kill without live DIV")
    reset=n("reset")
    hi=0 if reset else int(bool(fire&1) or bool(hi and not (done&1 or kill)))
    hf=0 if reset else int(bool(fire&2) or bool(hf and not (done&2 or kill)))
    busy=0 if reset or kill or done else (1 if fire else busy)
    owner=0 if reset else (1 if fire==2 else (0 if fire==1 else owner))
    need((bool(hi),bool(hf))==(bool(busy and owner==0),bool(busy and owner==1)),"next state differs")
    events["accept_int"]+=fire==1;events["accept_float"]+=fire==2
    events["cancel"]+=bool(kill);events["reset"]+=bool(reset);events["complete"]+=bool(done)
    cycles+=1
need(cycles==35075 and not busy and not hi and not hf,"incomplete campaign")
a.output.write_text(json.dumps(dict(status="C1_REAL_PARENT_STATE_REPLAY_PASS",cycles=cycles,events=events,
    baseline_log_sha256=sha(base),candidate_log_sha256=sha(candidate),all_observed_parent_lines_identical=True,
    note="Observed cycle-level equivalence for the fixed real-parent stimulus, not all possible RTL traces"),indent=2)+"\n")
print(a.output.read_text())
