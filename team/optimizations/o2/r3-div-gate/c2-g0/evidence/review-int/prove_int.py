#!/usr/bin/env python3
"""Source-linked safety abstraction; not an RTL-equivalence or arithmetic proof."""
from collections import deque
from itertools import product
from pathlib import Path
import hashlib,json,datetime,sys,time
ROOT=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
OUT=Path(__file__).resolve().parent
INPUTS=list(product(range(2),range(2),range(3),range(3),range(2),range(2),range(2),range(2),range(2)))
# reset, test_enable, requested_unit [none,int,other], redirect [none,unrelated,kill],
# early_finish, iter_finish, all_other_children_finished, output_ready, other_done
INIT=(0,0,0,0)
def inv(s):
    mode,top,child,hold=s
    return ((mode!=0 or top==0) and
            (mode==1 or top==0) and
            (hold==(mode==1)) and
            (top!=0 or child==0) and
            (top!=2 or child in (0,5)))
def child_next(kind,q,top,early,done):
    if q==0: return 1 if top==1 else 0
    if q==1: return (4 if early else 3) if kind=="I8" else 2
    if q==2: return 4 if early else 3
    if q==3: return 4 if done else 3
    if q==4: return 5
    if q==5: return 0 if top==2 else 5
    raise ValueError(q)
def step(s,u,kind,mutation=None):
    mode,top,q,h=s
    rst,te,sel,redir,early,done,others,ready,other_done=u
    kill=bool(mode and redir==2)
    # Actual parent dispatch is guarded by B, both out-valid and both ready.
    # Other DIV is represented by mode=2, accepting only from mode=0.
    accept=bool(mode==0 and top==0 and sel and not redir and not rst)
    ai=accept and sel==1
    ao=accept and sel==2
    ofi=bool(top==2 and ready)
    finish=bool(others and (q==5 or mutation=="drop_all_child_finish"))
    release=ofi or kill
    edge=bool(te or ai or h)
    if mutation=="mask_cancellation_edge" and kill: edge=False
    newh=0 if rst else (1 if ai else (0 if release else h))
    newmode=(0 if rst or kill or ofi or (mode==2 and other_done) else (1 if ai else (2 if ao else mode)))
    if mutation=="early_parent_clear" and top==1 and finish: newmode=0
    newtop,newq=top,q
    if edge:
        if rst and mutation!="drop_child_reset": newtop,newq=0,0
        elif redir==2 and top!=0 and mutation!="drop_child_flush": newtop,newq=0,0
        else:
            if top==0 and ai: newtop=1
            elif top==1 and finish: newtop=2
            elif top==2 and ready: newtop=0
            newq=child_next(kind,q,top,early,done)
    return (newmode,newtop,newq,newh)
def describe(s): return dict(zip(("parent_mode","top_state","representative_child_state","integer_hold"),s))
def trace(node,pred):
    r=[]
    while pred[node] is not None:
        old,inp=pred[node]
        r.append({"state":describe(old),"input":inp,"next":describe(node)})
        node=old
    return list(reversed(r))
def explore(kind,mutation=None):
    queue=deque([INIT]); pred={INIT:None}; transitions=0
    classes=set(); witnesses={}
    while queue:
        s=queue.popleft()
        for u in INPUTS:
            nxt=step(s,u,kind,mutation);transitions+=1
            rst,te,sel,redir,early,done,others,ready,other_done=u
            checks={
              "dynamic_reset_active_TE0":rst and not te and s[0]==1,
              "cancel_divide_TE0":not rst and not te and redir==2 and s[0]==1 and s[1]==1,
              "cancel_output_backpressured_TE0":not rst and not te and redir==2 and s[0]==1 and s[1]==2 and not ready,
              "finish_cancel_coincident":not rst and redir==2 and s[0]==1 and s[1]==2 and ready,
              "output_backpressure_child_drain":not rst and redir==0 and s[1]==2 and s[2]==5 and not ready,
              "same_edge_parent_and_child_release":not rst and redir==0 and s[1]==2 and s[2]==5 and ready,
              "arbitrary_iteration_stall":not rst and redir==0 and s[1]==1 and s[2]==3 and not done,
              "unrelated_redirect_running":not rst and redir==1 and s[0]==1,
              "other_division_owner":s[0]==2
            }
            for name,v in checks.items():
                if v:
                    classes.add(name)
                    if name not in witnesses: witnesses[name]=trace(s,pred)+[{"state":describe(s),"input":u,"next":describe(nxt)}]
            if not inv(nxt):
                return {"status":"COUNTEREXAMPLE","mutation":mutation,"kind":kind,"states_before_failure":len(pred),"transitions_checked":transitions,"trace":trace(s,pred)+[{"state":describe(s),"input":u,"next":describe(nxt)}]}
            if nxt not in pred:
                pred[nxt]=(s,u);queue.append(nxt)
    return {"status":"PASS","kind":kind,"reachable_states":len(pred),"states":[describe(s) for s in sorted(pred)],"input_tuples_per_state":len(INPUTS),"transitions_checked":transitions,"coverage":sorted(classes),"witnesses":witnesses}
def main():
    start=time.monotonic()
    identities=json.loads((OUT/"inputs.json").read_text())
    for item in identities:
        assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()==item["sha256"],item["path"]
    # Fail closed if source control fragments used by this manual abstraction drift.
    checks={
     "yunsuan/src/main/scala/yunsuan/vector/VectorIdiv/VectorIdiv.scala":[
       "val idle :: divide :: output :: Nil = Enum(3)",
       "io.div_in_ready := stateReg(idle)", "io.div_out_valid := stateReg(output)",
       "finish := divide_8_finish.reduce(_ & _) & divide_16_finish.reduce(_ & _) & divide_32_finish.reduce(_ & _) & divide_64_finish.reduce(_ & _)"],
     "yunsuan/src/main/scala/yunsuan/vector/VectorIdiv/I8DivNr4.scala":[
       "val idle :: pre :: iter :: post :: output :: Nil = Enum(5)",
       "when(io.flush) {", "stateReg := Mux(early_finish, oh_post, oh_iter)",
       "stateReg := Mux(iter_finish, oh_post, oh_iter)", "stateReg(output) & io.div_out_ready"],
     "yunsuan/src/main/scala/yunsuan/vector/VectorIdiv/SRT16Divint.scala":[
       "val idle :: pre_0 :: pre_1 :: iter :: post :: output :: Nil = Enum(6)",
       "when (io.flush) {", "when(early_finish) {", "when(iter_finish) {",
       "when (io.div_out_ready) {"],
     "src/main/scala/xiangshan/backend/fu/wrapper/VIDiv.scala":[
       "subIO.div_out_ready := io.out.ready & io.out.valid",
       "subIO.flush         := thisRobIdx.needFlush(io.flush)",
       "thisRobIdx := outCtrl.robIdx"],
     "src/main/scala/xiangshan/backend/exu/ExeUnit.scala":[
       "val divRobIdx = RegEnable(io.in.bits.robIdx, divAccept)",
       "val divCancelled = divBusy && divRobIdx.needFlush(io.flush)",
       "fu.io.out.fire || elasticDivCancelled.get"]
    }
    for file,fragments in checks.items():
        txt=(ROOT/file).read_text()
        for text in fragments: assert text in txt,(file,text)
    results=[explore(k) for k in ("I8","SRT")]
    assert all(x["status"]=="PASS" for x in results)
    mutations=[explore("SRT",m) for m in ("drop_child_flush","mask_cancellation_edge","early_parent_clear","drop_child_reset","drop_all_child_finish")]
    assert all(x["status"]=="COUNTEREXAMPLE" for x in mutations)
    unknown=(0,1,3,0)
    reset_no_clock=(1,0,0,0,0,0,0,0,0)
    after=step(unknown,reset_no_clock,"SRT")
    assert after[0]==0 and after[1]!=0 and not inv(after)
    # ROB capture equality is symbolic in width. Finite exhaustive equality audit
    # is diagnostic only; it is not substituted for the equal-expression argument.
    rob_checks=0
    for parent_old,child_old,new_id,fire,edge in product(range(8),range(8),range(8),range(2),range(2)):
        if fire and not edge: continue # gate E includes selected child's fire
        p=new_id if fire else parent_old
        c=new_id if fire and edge else child_old
        if fire or parent_old==child_old: assert p==c
        rob_checks+=1
    result={
      "status":"INTEGER_SOURCE_LINKED_CONTROL_PROOF_PASS_CONDITIONAL_BOOTSTRAP",
      "abstraction":"Universal representative child, all-finish implies its out-valid; nondeterministic early/iteration completion; no fairness assumption.",
      "assumptions":[
        "At least one valid reset edge reached all relevant DIV state flops before INIT.",
        "Parent/selected child acceptance is identical and one-hot, as ExeUnit source enforces.",
        "For an active integer transaction, parent and child flush compare the same ROB captured on that identical acceptance.",
        "Other DIV abstraction can start only when parent/int is idle and never changes integer state.",
        "Clock gate is ideal, delivers each root edge when fire|hold|TE is true."
      ],
      "scope":"Safety only, no arithmetic/liveness/RTL equivalence; I8 representative covers 8 identical instances, SRT covers 4x16,2x32,2x64 instances independent of data.",
      "results":results,"mutation_checks":mutations,
      "bootstrap_counterexample":{"state":describe(unknown),"input":reset_no_clock,"next":describe(after),"interpretation":"Illustrates why initial parent reset alone is insufficient if child reset is synchronous and its gate was closed; not claimed a normal post-bootstrap trace."},
      "rob_capture_equal_expression_audit_cases":rob_checks,
      "elapsed_seconds":time.monotonic()-start,
      "utc_completed":datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    for item in identities:
        assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()==item["sha256"],item["path"]
    (OUT/"proof.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("results","mutation_checks")},indent=2))
    print(json.dumps({"results":[{k:v for k,v in r.items() if k not in ("states","witnesses")} for r in results],"mutations":[(r["mutation"],r["status"],len(r["trace"])) for r in mutations]},indent=2))
if __name__=="__main__":main()
