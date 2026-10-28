"""Read-only C2 predicate audit; no simulator or EDA tool is invoked."""
from pathlib import Path
import hashlib, itertools, json, subprocess
ROOT = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
C1 = Path("/home/riscv/riscv-lab/o2-c1-owner-20261025")
OUT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
paths = [
    ROOT/"src/main/scala/xiangshan/backend/exu/ExeUnit.scala",
    C1/"repo/src/main/scala/xiangshan/backend/exu/ExeUnit.scala",
    C1/"repo/src/main/scala/xiangshan/backend/fu/wrapper/VIDiv.scala",
    C1/"repo/src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala",
    C1/"repo/yunsuan/src/main/scala/yunsuan/vector/VectorIdiv/VectorIdiv.scala",
    C1/"repo/yunsuan/src/main/scala/yunsuan/vector/VectorFloatDivider.scala",
    C1/"repo/yunsuan/src/main/scala/yunsuan/vector/vfsqrt/fpsqrt_vector_r16.scala",
    C1/"repo/utility/src/main/scala/utility/ClockGate.scala",
    C1/"parent-cost-01/rtl/ExeUnit.sv",
    Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025/parent-cost-01/rtl/ExeUnit.sv"),
    C1/"parent-01/result.log",
    C1/"parent-map-01/map.ys",
    ROOT/"team/optimizations/o2/r3-div-gate/c1/RESULT.md",
    ROOT/"team/optimizations/o2/r3-div-gate/c1/STATE_EQUIVALENCE.md",
    ROOT/"team/optimizations/o2/r3-div-gate/c1/CONTRACT.md",
]
before={str(p):sha(p) for p in paths}
assert sha(C1/"parent-01/result.log")=="a38e8d806dc84c46b16af6f3c17323ee5f404ba3eb221d94fa15e127bf22ee6d"
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()=="0f12df675378556670afd0dd2153f47fcb330610"
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=C1/"repo",text=True).strip()=="3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66"
counts=dict(cycles=0,guarded_prelaunch=0,idle_nonreset_samples=0,idle_nonreset_notready=0,
    idle_noout_nonreset_notready=0,guarded_fire_mismatch=0,guarded_gate_mismatch=0,
    naive_valid_gate_extra=0)
examples={}
busy=owner=0
for line in (C1/"parent-01/result.log").read_text().splitlines():
    if not line.startswith("O2_PARENT_CYCLE "): continue
    r=dict(x.split("=",1) for x in line.split()[1:]);n=lambda k:int(r[k])
    ready=(n("child_ready")>>1)&3;out=(n("child_out")>>1)&3;fire=(n("child_fire")>>1)&3
    if not busy and not n("reset"):
        counts["idle_nonreset_samples"]+=1
        if ready!=3:
            counts["idle_nonreset_notready"]+=1;examples.setdefault("idle_nonreset_notready",r)
            if not out:counts["idle_noout_nonreset_notready"]+=1
    pre=bool(n("offered") and n("kind") in (1,2) and not busy and out==0 and
             not n("occupancy") and not n("redirect") and not n("reset"))
    start=(1<<(n("kind")-1)) if pre else 0
    hold=(1<<owner) if busy else 0
    expected=3 if n("te") else (fire|hold)
    assert expected==((n("clocks")>>1)&3)
    gate=3 if n("te") else (start|hold)
    if start!=fire:
        counts["guarded_fire_mismatch"]+=1;examples.setdefault("guarded_fire_mismatch",r)
    if gate!=expected:
        counts["guarded_gate_mismatch"]+=1;examples.setdefault("guarded_gate_mismatch",r)
    naive=(1<<(n("kind")-1)) if n("offered") and n("kind") in (1,2) else 0
    naive_gate=3 if n("te") else (naive|hold)
    if naive_gate & ~expected:
        counts["naive_valid_gate_extra"]+=1;examples.setdefault("naive_valid_gate_extra",r)
    counts["cycles"]+=1;counts["guarded_prelaunch"]+=int(pre)
    busy=0 if n("reset") or n("kill_div") or (out and n("out_ready")) else (1 if fire else busy)
    owner=0 if n("reset") else (1 if fire==2 else (0 if fire==1 else owner))
assert counts["cycles"]==35075 and counts["guarded_prelaunch"]==1744
assert not counts["guarded_fire_mismatch"] and not counts["guarded_gate_mismatch"]
# Truth-table comparison retains all decode/occupied/out/flush/reset guards.
# This is a Boolean lemma conditioned on a stronger invariant, not a proof of
# that invariant in the RTL. The C1 event contract permitted stale not-ready.
truth=dict(total=0,invariant_rows=0,invariant_mismatches=0,unrestricted_mismatches=0)
counterexample=None
for bits in itertools.product((0,1),repeat=11):
    b,t,ri,rf,oi,of,vo,fl,rst,v,te=bits
    for kind in (0,1,2):
        choose=(1<<(kind-1)) if kind else 0
        pre=bool(v and choose and not b and not oi and not of and not vo and not fl and not rst)
        start=choose if pre else 0
        fire=start if ri and rf else 0
        hold=(1<<t) if b else 0
        old=3 if te else (fire|hold)
        new=3 if te else (start|hold)
        inv=bool(rst or b or (ri and rf))
        truth["total"]+=1;truth["invariant_rows"]+=inv
        if old!=new:
            truth["unrestricted_mismatches"]+=1
            if inv:truth["invariant_mismatches"]+=1
            if counterexample is None:
                counterexample=dict(busy=b,owner=t,int_ready=ri,float_ready=rf,int_out=oi,float_out=of,
                    vdot_occupied=vo,flush=fl,reset=rst,valid=v,te=te,kind=kind,
                    old_gate=old,new_gate=new)
assert truth["invariant_mismatches"]==0 and truth["unrestricted_mismatches"]>0
assert before=={str(p):sha(p) for p in paths}
result=dict(status="READ_ONLY_SEMANTIC_ATTRIBUTION_COMPLETE",
    trace=counts,trace_examples=examples,truth_table=truth,unrestricted_counterexample=counterexample,
    stronger_invariant="outside reset, !divBusy implies int_ready && float_ready",
    limits=["Trace projection is not new RTL simulation.",
        "No full-RTL formal proof of the stronger invariant; existing C1 abstract contract is insufficient.",
        "Existing dynamic inputs do not add sqrt coverage; no new full-core, performance, area or STA result."],
    inputs=before,protected_inputs_unchanged=True)
p=OUT/"predicate-audit.json"
assert not p.exists()
p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ["status","trace","truth_table","unrestricted_counterexample"]},indent=2))
