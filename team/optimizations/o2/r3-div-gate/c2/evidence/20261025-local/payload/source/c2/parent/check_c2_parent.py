#!/usr/bin/env python3
"""C2 supplement gate: strict existing trace replay + independent extra coverage."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

def require(ok,why):
    if not ok:
        raise ValueError(why)

def parse(line):
    tokens=line.split()[1:];values={}
    for token in tokens:
        k,v=token.split("=")
        require(k not in values,"duplicate field")
        values[k]=v if k in ("case","block_reason") else int(v)
    return values

def check(text,parent_dir):
    sys.path.insert(0,str(Path(parent_dir)))
    from check_trace import check_trace
    aux=[];rows=[];ordinary=[];pairs=[]
    for line in text.splitlines():
        if line.startswith("C2_PARENT_AUX "):
            a=parse(line)
            require(set(a)=={"schema","cycle","lane_ready","lane_finish","div_busy","op","live_op"},"aux schema")
            require(a["schema"]==1 and a["cycle"]==len(aux),"aux sequence")
            require(0<=a["lane_ready"]<4 and 0<=a["lane_finish"]<4 and a["div_busy"] in (0,1),"aux values")
            aux.append(a)
        else:
            ordinary.append(line)
            if line.startswith("O2_PARENT_CYCLE "):
                row=parse(line);rows.append(row)
                require(len(aux)==len(rows),"missing/late lane observation")
                pairs.append((row,aux[-1]))
    replay=check_trace("\n".join(ordinary)+"\n",require_campaign=False)
    require(len(aux)==len(rows) and len(rows)>0,"unpaired aux")
    req={};normal=set();cancel=set();reset=set();rob=set();switch=set()
    skew=Counter();skew_cancel=Counter();idle_after_cancel=0;window=None;previous_reset=False
    counts=Counter()
    for row,a in pairs:
        cycle=row["cycle"];case=row["case"]
        if not row["reset"]:
            require(a["div_busy"]==bool(row["divseq"]),"busy register disagrees with accepted identity")
            require(bool(row["child_ready"]&4)==(a["lane_ready"]==3),"two-lane ready mismatch")
            require(bool(row["child_out"]&4)==(a["lane_finish"]==3),"two-lane finish join mismatch")
            if not a["div_busy"]:
                counts["idle_ready_checks"]+=1
                require((row["child_ready"]&6)==6,"G0 invariant violated")
        if row["divseq"]:
            require(row["divseq"] in req,"missing live accepted identity")
            require(a["live_op"]==req[row["divseq"]]["op"],"live SQRT opcode changed")
        else:
            require(a["live_op"]==0,"opcode without DIV")
        if not row["reset"] and not row["te"]:
            clocks=int(bool(row["pseq"] or row["rseq"]))
            if row["divseq"]:
                clocks|=1<<req[row["divseq"]]["kind"]
            if row["accept"]:
                clocks|=1<<row["kind"]
            require(row["clocks"]==clocks,"extra or missing owner clock")
        if window:
            require(not (row["offered"] or row["reset"] or row["redirect"] or row["te"]
                or row["clocks"] or row["divseq"] or row["pseq"] or row["rseq"]),"immediate cancel-idle failure")
            idle_after_cancel+=1;window-=1
        if row["accept"]:
            req[row["accept_seq"]]=dict(op=a["op"],kind=row["kind"],case=case)
        if a["live_op"]==1 and row["divseq"] and not row["reset"] and a["lane_finish"] in (1,2):
            skew[a["lane_finish"]]+=1
            require(not(row["child_out"]&4) and not row["response"],"partial lane escaped")
        if case.startswith("C2-sqrt-") and row["response"]:
            request=req[row["response_seq"]]
            require(request["kind"]==2 and request["op"]==1 and request["case"]==case,"normal SQRT identity")
            require(case not in normal,"duplicate normal case");normal.add(case)
        if case.startswith("C2-cancel-") and row["kill_div"]:
            require(req[row["divseq"]]["op"]==1,"cancelled non-SQRT")
            require(case not in cancel,"duplicate SQRT cancel");cancel.add(case)
            if "-p1-" in case:
                require(a["lane_finish"] in (1,2),"skew-phase cancel not at real skew")
                skew_cancel[a["lane_finish"]]+=1
            window=3
        if case.startswith("C2-ROB-") and row["redirect"]:
            require(case not in rob,"duplicate ROB case");rob.add(case)
            require(req[row["divseq"]]["op"]==1,"ROB test is not SQRT")
            if row["kill_div"]:window=3
        if case.startswith("C2-reset-") and row["reset"] and not previous_reset:
            require(row["te"]==0,"dynamic reset secretly enabled TE")
            require(case not in reset,"duplicate reset case");reset.add(case)
            if "-empty-" not in case:
                require(row["reset_drop"]==1 and row["divseq"],"active reset missing drop")
                if case.endswith("-f1"):
                    old=req[row["divseq"]]
                    require(row["redirect"] and row["self"],"reset cancel overlap missing")
            else:
                require(row["reset_drop"]==0,"empty reset drops")
        previous_reset=bool(row["reset"])
        if case.startswith("C2-switch-") and row["accept"]:
            switch.add(case)
    require(not window,"truncated cancel idle")
    expect_normal={f"C2-sqrt-v{v}-s{s}" for v in range(5) for s in (0,1,7)}
    expect_cancel={f"C2-cancel-v{v}-p{p}-r{r}-n{n}" for v in (1,2) for p in range(4) for r in (0,1) for n in range(3)}
    expect_reset={f"C2-reset-e{e}-p{p}-f{f}" for e in range(3) for p in range(3) for f in (0,1)}|{f"C2-reset-empty-f{f}" for f in (0,1)}
    expect_rob={f"C2-ROB-r{r}-p{p}" for r in range(7) for p in (0,3)}
    expect_switch={f"C2-switch-o{o}-d{d}-s{s}" for o in range(3) for d in range(2) for s in (0,1,7)}
    for got,want,name in ((normal,expect_normal,"normal"),(cancel,expect_cancel,"cancel"),
                         (reset,expect_reset,"reset"),(rob,expect_rob,"ROB"),(switch,expect_switch,"switch")):
        require(got==want,f"{name} coverage mismatch missing={sorted(want-got)} extra={sorted(got-want)}")
    require(set(skew)=={1,2} and set(skew_cancel)=={1,2},"both physical skew directions not observed")
    require(idle_after_cancel==(48+6)*3,"wrong cancel idle sample count")
    require(replay["groups"]==6,"supplement groups incomplete")
    return dict(status="C2_PARENT_SUPPLEMENT_PASS",replay=replay,counts=dict(counts),
                normal_sqrt_cases=len(normal),sqrt_cancel_cases=len(cancel),
                te0_reset_cases=len(reset),sqrt_rob_cases=len(rob),sqrt_switch_cases=len(switch),
                real_lane_skew_cycles=dict(skew),real_lane_skew_cancel_cases=dict(skew_cancel),
                immediate_cancel_idle_samples=idle_after_cancel,
                scope="real parent supplemental control and exact directed SQRT; no fullcore/PPA")

def main():
    p=argparse.ArgumentParser();p.add_argument("--log",type=Path,required=True)
    p.add_argument("--parent-dir",type=Path,required=True);p.add_argument("--output",type=Path)
    a=p.parse_args();raw=a.log.read_bytes();result=check(raw.decode(),a.parent_dir)
    result["log_sha256"]=hashlib.sha256(raw).hexdigest()
    result["checker_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    text=json.dumps(result,indent=2)+"\n"
    if a.output:
        require(not a.output.exists(),"output exists");a.output.write_text(text)
    print(text,end="")
if __name__=="__main__":main()
