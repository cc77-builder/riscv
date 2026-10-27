"""Exhaustive control abstraction for the fixed vector FP divider wrapper.
No RTL, simulator, synthesis, or external solver is invoked.
"""
from collections import deque, Counter
from itertools import product
from pathlib import Path
import hashlib, json, subprocess, time

OUT = Path(__file__).resolve().parent
BASE = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
C1 = Path("/home/riscv/riscv-lab/o2-c1-owner-20261025/repo")
RTLB = Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025/parent-cost-01/rtl")
RTLC = Path("/home/riscv/riscv-lab/o2-c1-owner-20261025/parent-cost-01/rtl")
SRCS = [
"src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala",
"src/main/scala/xiangshan/backend/fu/vector/VecNonPipedFuncUnit.scala",
"yunsuan/src/main/scala/yunsuan/vector/VectorFloatDivider.scala",
"yunsuan/src/main/scala/yunsuan/vector/vfsqrt/fpsqrt_vector_r16.scala",
"utility/src/main/scala/utility/ClockGate.scala",
]
SVS = ["VFDivSqrt.sv","VectorFloatDivider.sv","VectorFloatDividerR64.sv","fpsqrt_vector_r16.sv","ClockGate.sv"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
paths = [r/s for r in (BASE,C1) for s in SRCS] + [r/s for r in (RTLB,RTLC) for s in SVS]
paths += [BASE/"src/main/scala/xiangshan/backend/exu/ExeUnit.scala",C1/"src/main/scala/xiangshan/backend/exu/ExeUnit.scala"]
def check_sources():
    before = {str(p):sha(p) for p in paths}
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=BASE,text=True).strip()=="0f12df675378556670afd0dd2153f47fcb330610"
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=C1,text=True).strip()=="3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66"
    for s in SRCS: assert sha(BASE/s)==sha(C1/s),s
    for s in SVS: assert sha(RTLB/s)==sha(RTLC/s),s
    # Source guards supplement, rather than replace, manual line-by-line mapping.
    guards = {
    "vector_constant": ("src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala","mod.io.is_vec_i       := true.B"),
    "aggregate_finish": ("src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala","io.out.valid := vfdivs.map(_.io.finish_valid_o).reduce(_&_)"),
    "common_finish_ready": ("src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala","mod.io.finish_ready_i := io.out.ready & io.out.valid"),
    "sqrt_no_vector_early": ("yunsuan/src/main/scala/yunsuan/vector/vfsqrt/fpsqrt_vector_r16.scala","early_finish := Mux(vector_mode_i, false.B,"),
    "ctrl_capture": ("src/main/scala/xiangshan/backend/fu/vector/VecNonPipedFuncUnit.scala","protected val outCtrl     = DataHoldBypass(io.in.bits.ctrl, io.in.fire)"),
    }
    for k,(s,needle) in guards.items(): assert needle in (C1/s).read_text(),k
    sv=(RTLC/"VectorFloatDividerR64.sv").read_text()
    assert "assign io_start_ready_o = fsm_q[0];" in sv
    assert "assign io_finish_valid_o = fsm_q[5];" in sv
    assert "fsm_q <= io_start_valid_i ? 6'h2 : 6'h1;" in sv
    
    return before, guards

# State=(parentBusy,parentRob,childRob,div0,sqrt0,div1,sqrt1)
# D: 0 PRE0,1 PRE1,2 PRE2,3 ITER,4 POST0,5 POST1.
# S: 0 PRE0,1 PRE1,2 ITER,3 POST0.
INITIAL=(0,0,0,0,0,0,0)
# A redirect is an arbitrary predicate on two symbolic identities. This
# overapproximates actual ROB comparisons; equality of stored identities is
# established, not assumed. 0 is valid redirect killing neither identity.
EVENTS=list(product((0,1,2),(0,1),(-1,0,1,2,3),(0,1),(0,1),(0,1)))
# kind:0 no offered FP request,1 DIV,2 SQRT.
def killed(mask,tag): return mask>=0 and bool(mask&(1<<tag))
def state_info(st):
    b,pr,cr,d0,s0,d1,s1=st
    ready=(d0==s0==d1==s1==0)
    f0=(d0==5 or s0==3); f1=(d1==5 or s1==3)
    return ready,f0,f1
def d_next(d,start,done):
    if d==0:return (1,) if start else (0,)
    if d==1:return (2,)
    if d==2:return (3,)
    if d==3:return (3,4) # arbitrary final_iter: conservative for all operands
    if d==4:return (5,) # is_vec is tied true
    if d==5:return (0,) if done else (5,)
    raise ValueError(d)
def s_next(s,start,done):
    if s==0:return (1,2) if start else (0,) # arbitrary need_2_cycles_init
    if s==1:return (2,)
    if s==2:return (2,3) # arbitrary final_iter independently in each lane
    if s==3:return (0,) if done else (3,)
    raise ValueError(s)
def successors(st,e,mutation=None,reset_mode="sync"):
    b,pr,cr,d0,s0,d1,s1=st
    kind,tag,mask,outready,rst,te=e
    ready,f0,f1=state_info(st)
    out=f0 and f1
    accept=bool(kind and not b and not out and ready and mask<0 and not rst)
    parentkill=bool(b and killed(mask,pr))
    childkill=killed(mask,tag if ready else cr)
    parentout=(f0 or f1) if mutation=="premature_any_lane_release" else out
    parentdone=bool(parentout and outready)
    done=bool(out and outready) # wrapper still uses the real AND rendezvous
    edge=bool(te or b or accept)
    if rst and reset_mode=="async":edge=bool(te) # async parent busy has already cleared
    if mutation=="cancel_edge_suppressed" and parentkill:edge=bool(te)
    if mutation=="reset_hold_suppressed" and rst:edge=bool(te)
    if mutation=="child_cancel_missing":childkill=False
    nb=0 if rst or parentkill or parentdone else (1 if accept else b)
    np=tag if accept else pr
    nc=(1-tag if mutation=="wrong_child_identity" else tag) if accept and edge else cr
    if rst and reset_mode=="async":
        choices=((0,),(0,),(0,),(0,))
    elif not edge:
        choices=((d0,),(s0,),(d1,),(s1,))
    elif rst or childkill:
        choices=((0,),(0,),(0,),(0,))
    else:
        choices=(d_next(d0,accept and kind==1,done),s_next(s0,accept and kind==2,done),
                 d_next(d1,accept and kind==1,done),s_next(s1,accept and kind==2,done))
    for children in product(*choices):
        yield (nb,np,nc,*children),dict(kind=kind,sourceRob=tag,redirectMask=mask,
            outReady=outready,reset=rst,te=te,accepted=int(accept),parentKill=int(parentkill),
            childKill=int(childkill),childClockEdge=int(edge),parentDone=int(parentdone),childDone=int(done))
def violation(st):
    b,pr,cr,d0,s0,d1,s1=st
    ready,_,_=state_info(st)
    # The target is tested on all reached states, never used to prune search.
    if not b and not ready:return "parent_idle_with_child_not_ready"
    return None
def trace_to(st,pred):
    seq=[]
    while pred[st] is not None:
        prev,event=pred[st];seq.append(dict(before=prev,event=event,after=st));st=prev
    return list(reversed(seq))
def explore(mutation=None,initial=INITIAL,stop_on_bad=False,reset_mode="sync"):
    queue=deque([initial]);pred={initial:None};transitions=0;coverage=Counter()
    while queue:
        st=queue.popleft()
        bad=violation(st)
        if bad:
            return dict(status="COUNTEREXAMPLE",mutation=mutation,initial=initial,
                reached=len(pred),transitions=transitions,violation=bad,trace=trace_to(st,pred))
        b,pr,cr,d0,s0,d1,s1=st
        ready,f0,f1=state_info(st)
        if b and pr!=cr:coverage["active_identity_mismatch"]+=1
        if b and ready:coverage["busy_with_all_ready"]+=1
        if f0!=f1:coverage["lane_finish_skew_states"]+=1
        if (d0 and s0) or (d1 and s1):coverage["div_sqrt_overlap_states"]+=1
        if b and ((d0 and s1) or (s0 and d1)):coverage["cross_lane_opcode_mismatch"]+=1
        if d0!=d1:coverage["div_lane_state_skew_states"]+=1
        if s0!=s1:coverage["sqrt_lane_state_skew_states"]+=1
        for e in EVENTS:
            for nxt,event in successors(st,e,mutation,reset_mode):
                transitions+=1
                if event["accepted"]:coverage["accept_transitions"]+=1
                if event["parentKill"]:coverage["cancel_transitions"]+=1
                if event["parentDone"]:coverage["complete_transitions"]+=1
                if e[4] and not e[5] and b:coverage["active_te0_reset_transitions"]+=1
                if nxt not in pred:
                    pred[nxt]=(st,event);queue.append(nxt)
    return dict(status="ABSTRACT_CONTROL_INVARIANT_PASS",mutation=mutation,reached=len(pred),
        transitions=transitions,coverage=dict(coverage),
        reachable_states=[list(x) for x in sorted(pred)])
def main():
    before,guards=check_sources()
    start=time.monotonic()
    results={}
    for policy in ("sync","async"):
        result=explore(reset_mode=policy)
        assert result["status"]=="ABSTRACT_CONTROL_INVARIANT_PASS"
        for key in ("active_identity_mismatch","busy_with_all_ready","div_sqrt_overlap_states","cross_lane_opcode_mismatch"):
            assert result["coverage"].get(key,0)==0,key
        for key in ("lane_finish_skew_states","div_lane_state_skew_states","sqrt_lane_state_skew_states"):
            assert result["coverage"][key]>0,key
        results[policy]=result
    negative=[]
    for name in ["cancel_edge_suppressed","reset_hold_suppressed","child_cancel_missing","wrong_child_identity","premature_any_lane_release"]:
        x=explore(name,stop_on_bad=True,reset_mode="sync")
        assert x["status"]=="COUNTEREXAMPLE",name
        negative.append(x)
    uninit=explore("no_bootstrap",initial=(0,0,0,3,0,0,0),stop_on_bad=True)
    assert uninit["status"]=="COUNTEREXAMPLE"
    negative.append(uninit)
    assert before=={str(p):sha(p) for p in paths}
    output=dict(status="FP_G0_CONTROL_ABSTRACTION_PASS",elapsed_seconds=time.monotonic()-start,
        models=results,negative_controls=negative,inputs=before,input_hashes_unchanged=True,
        source_guards=guards,limits=[
            "No RTL formal equivalence or new RTL simulation.",
            "Two symbolic ROB identities and arbitrary kill predicates preserve equality-dependent control; actual RobPtr comparison proof belongs to parent audit.",
            "Nondeterministic per-lane initialization and iteration completion overapproximate arithmetic; no liveness bound or arithmetic correctness proved.",
            "Initial state follows effective reset of all child FSMs; arbitrary power-on states are rejected.",
            "FP-only transactions here; integer ownership/mutual exclusion must be discharged by parent model.",
            "Clock sampling is abstract; sync requires a delivered edge, async resets parent/child independently of gated edge. Actual reset type is bound by separate source audit.",
            "No analog glitch or asynchronous reset recovery/removal timing proof."
        ])
    p=OUT/"fp-control-result.json"
    assert not p.exists()
    p.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(status=output["status"],elapsed_seconds=output["elapsed_seconds"],
        models={k:dict(reached=v["reached"],transitions=v["transitions"],coverage=v["coverage"]) for k,v in results.items()},
        negatives=[dict(name=x["mutation"],depth=len(x["trace"]),violation=x["violation"]) for x in negative]),indent=2))

if __name__=="__main__":
    main()
