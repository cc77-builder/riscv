"""Check that fine FP FSMs refine the parent's conservative I/R/O quotient."""
from pathlib import Path
from itertools import product
import importlib.util,hashlib,json,re
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("fp_control",OUT/"fp_control_model.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def quotient(kind,state):return "I" if state==0 else ("O" if state==(5 if kind=="D" else 3) else "R")
def abstract_next(q,start,done):
    if q=="I":return {"R"} if start else {"I"}
    if q=="R":return {"R","O"}
    return {"I"} if done else {"O"}
rows=checks=edges=0;examples={}
for kind,maxstate,fn in [("D",6,m.d_next),("S",4,m.s_next)]:
    for st,start,done,flush,rst,clk in product(range(maxstate),(0,1),(0,1),(0,1),(0,1),(0,1)):
        for policy in ("sync","async"):
            q=quotient(kind,st)
            if rst and policy=="async":
                concrete=(0,);abstract={"I"}
            elif not clk:
                concrete=(st,);abstract={q}
            elif rst or flush:
                concrete=(0,);abstract={"I"}
            else:
                concrete=fn(st,start,done);abstract=abstract_next(q,start,done)
            projected={quotient(kind,x) for x in concrete}
            assert projected<=abstract,(kind,st,start,done,flush,rst,clk,policy,concrete,abstract)
            rows+=1;edges+=len(concrete)
            for x in projected:examples.setdefault(kind+":"+q+"->"+x,dict(state=st,start=start,done=done,flush=flush,reset=rst,clock_edge=clk,reset_mode=policy))
CORE=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/build/rtl")
COST=Path("/home/riscv/riscv-lab/o2-c1-owner-20261025/parent-cost-01/rtl")
binding={}
for name in ("VectorFloatDividerR64.sv","fpsqrt_vector_r16.sv"):
    pair={}
    for label,root in [("fullcore_async",CORE),("cost_sync",COST)]:
        p=root/name;lines=p.read_text().splitlines()
        assignments=[i for i,s in enumerate(lines) if "fsm_q <=" in s]
        lo=assignments[0]-1;hi=assignments[-1]
        body="\n".join(lines[lo:hi+1])
        proc=max(i for i in range(lo) if "always @" in lines[i])
        pair[label]=dict(path=str(p),sha256=sha(p),lines=[lo+1,hi+1],
            always_line=proc+1,always=lines[proc].strip(),body=body,
            normalized=re.sub(r"\s+","",body))
    assert pair["fullcore_async"]["normalized"]==pair["cost_sync"]["normalized"],name
    assert "posedge reset" in pair["fullcore_async"]["always"]
    assert "posedge reset" not in pair["cost_sync"]["always"]
    binding[name]=pair
for name in ("VFDivSqrt.sv","VectorFloatDivider.sv"):
    p=CORE/name
    binding[name]=dict(path=str(p),sha256=sha(p))
result=dict(status="FP_FINE_TO_IRO_SIMULATION_INCLUSION_PASS",input_rows=rows,
    concrete_successor_edges=edges,examples=examples,core_cost_fsm_bodies_equal_except_sensitivity=True,
    bindings=binding,model_sha256=sha(OUT/"fp_control_model.py"),
    meaning="Every enumerated fine control successor maps into the I/R/O successor set; this is an abstraction-inclusion check, not generated RTL formal equivalence.",
    scope="All legal one-hot decoded fine states, start/done/flush/reset/clock-edge Booleans and sync/async reset policies. No arithmetic or timing semantics claimed.")
p=OUT/"quotient-result.json";assert not p.exists()
p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ["status","input_rows","concrete_successor_edges","core_cost_fsm_bodies_equal_except_sensitivity"]},indent=2))
