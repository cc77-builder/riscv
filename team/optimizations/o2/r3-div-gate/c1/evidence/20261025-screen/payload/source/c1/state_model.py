"""Finite-state induction for C1, conditional on the documented parent protocol."""
import argparse,itertools,json
from collections import deque
from pathlib import Path

# State: reference busy, C1 owner (0=int,1=float), reference int/float holds.
INITIAL=(0,0,0,0)
def step(s,e,mutation=None):
    busy,owner,hi,hf=s
    request,out_kind,out_ready,redirect,ready_both,vdot_occupied,reset=e
    # Outputs may linger after cancellation. While occupied, only the owner
    # can have an output; this is a protocol assumption checked in real traces.
    if busy and out_kind not in (-1,owner):
        return None
    accept=(request if request in (0,1) and not (busy or out_kind!=-1 or redirect or vdot_occupied or reset)
            and ready_both else -1)
    fires=(accept==0,accept==1)
    out_fires=(out_kind==0 and out_ready,out_kind==1 and out_ready)
    kill=bool(busy and redirect==2)
    old_clock=tuple(bool(fires[i] or (hi,hf)[i]) for i in range(2))
    new_clock=tuple(bool(fires[i] or (busy and owner==i)) for i in range(2))
    if mutation=="early_cancel_clock" and kill:
        new_clock=(False,False)
    holds=tuple(0 if reset else int(fires[i] or ((hi,hf)[i] and not (out_fires[i] or kill))) for i in range(2))
    nb=0 if reset or kill or any(out_fires) else (1 if accept!=-1 else busy)
    no=0 if reset else (accept if accept!=-1 else owner)
    cb=nb
    if mutation=="unrelated_cancel" and busy and redirect==1:
        cb=0
    if mutation=="omit_cancel" and kill and not (reset or any(out_fires)):
        cb=busy
    if mutation=="wrong_owner" and accept!=-1 and not reset:
        no=1-accept
    expected=(bool(holds[0]),bool(holds[1]))
    candidate=tuple(bool(cb and no==i) for i in range(2))
    ok=(old_clock==new_clock and expected==candidate and nb==int(any(holds)) and sum(holds)<=1)
    return (nb,no,*holds),ok,dict(accept=accept,kill=kill,old_clock=old_clock,new_clock=new_clock,
                                reference_holds=holds,candidate_holds=candidate)
def events():
    # -1=no request, 0=int,1=float,2=vdot; output -1 means not visible.
    return itertools.product((-1,0,1,2),(-1,0,1),(False,True),(0,1,2),(False,True),(False,True),(False,True))
def prove(mutation=None):
    seen={INITIAL};todo=deque([INITIAL]);count=0;coverage=set()
    while todo:
        s=todo.popleft()
        for e in events():
            r=step(s,e,mutation)
            if r is None:continue
            ns,ok,detail=r;count+=1
            if not ok:return dict(pass_=False,state=s,event=e,detail=detail,transitions=count)
            if detail["kill"]:coverage.add("matching_cancel")
            if e[3]==1 and s[0]:coverage.add("unrelated_redirect")
            if e[2] and e[1]!=-1 and detail["kill"]:coverage.add("complete_and_cancel")
            if e[6] and detail["kill"]:coverage.add("reset_and_cancel")
            if e[1]!=-1 and not s[0]:coverage.add("lingering_output")
            if e[1]!=-1 and not e[2]:coverage.add("output_stall")
            if detail["accept"]!=-1:coverage.add("accept_"+str(detail["accept"]))
            if ns not in seen:seen.add(ns);todo.append(ns)
    return dict(pass_=True,reachable_states=sorted(seen),transitions=count,coverage=sorted(coverage))
def rob_check():
    count=0
    for req,at,self_flush in itertools.product(range(96),range(96),(False,True)):
        distance=(req-at)%96
        if distance==48:continue
        # The queue ordering has a half-ring validity precondition. Exclude
        # opposite flag with equal value, which is the ambiguous full window.
        flag,value=divmod(req,48);af,av=divmod(at,48)
        rtl=(self_flush and req==at) or bool(flag ^ af ^ (value>av))
        oracle=self_flush if distance==0 else distance<48
        assert rtl==oracle,(req,at,self_flush)
        count+=1
    return count
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    base=prove();assert base["pass_"]
    mutations={m:prove(m) for m in ("early_cancel_clock","unrelated_cancel","omit_cancel","wrong_owner")}
    assert all(not x["pass_"] for x in mutations.values())
    result=dict(status="C1_ABSTRACT_STATE_EQUIVALENCE_PASS",proof=base,negative_controls=mutations,
                rob_relations_checked=rob_check(),
                assumptions=["No acceptance during reset/redirect, occupied DIV, visible DIV output, unready DIVs or VDot occupancy.",
                             "One selected DIV; while busy only the recorded owner can produce an output.",
                             "ROB age comparisons are within the non-ambiguous half ring."],
                scope="Exhaustive inductive abstract transition check; not an RTL formal equivalence proof or fullcore qualification")
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
