#!/usr/bin/env python3
"""Replay mutations only; these are checker negative controls, NOT RTL faults."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from check_c2_parent import check,parse

def replace(line,key,value):
    return re.sub(r"(?<!\S)"+key+r"=\S+",key+"="+str(value),line)

def mutate(lines,condition,key,value):
    found=False;out=[]
    for line in lines:
        if not found and condition(line):
            line=replace(line,key,value);found=True
        out.append(line)
    if not found:raise ValueError("mutation target not found")
    return "\n".join(out)+"\n"

def main():
    p=argparse.ArgumentParser();p.add_argument("--log",required=True,type=Path)
    p.add_argument("--parent-dir",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();raw=a.log.read_bytes();text=raw.decode();check(text,a.parent_dir)
    lines=text.splitlines();aux=lambda x:x.startswith("C2_PARENT_AUX ")
    cycle=lambda x:x.startswith("O2_PARENT_CYCLE ")
    mutations={}
    mutations["div-busy-owner"]=mutate(lines,lambda x:aux(x) and parse(x)["div_busy"]==1,"div_busy",0)
    mutations["early-lane-join"]=mutate(lines,lambda x:aux(x) and parse(x)["lane_finish"] in (1,2),"lane_finish",3)
    mutations["sqrt-opcode"]=mutate(lines,lambda x:aux(x) and parse(x)["op"]==1,"op",0)
    mutations["te0-reset-mislabeled"]=mutate(lines,lambda x:cycle(x) and parse(x)["case"].startswith("C2-reset-") and parse(x)["reset"],"te",1)
    mutations["idle-extra-clock"]=mutate(lines,lambda x:cycle(x) and parse(x)["case"]=="C2-final-idle","clocks",2)
    mutations["missing-aux"]="\n".join(x for i,x in enumerate(lines) if i!=next(j for j,v in enumerate(lines) if aux(v)))+"\n"
    mutations["erase-lane-skew"]="\n".join(replace(x,"lane_finish",0) if aux(x) and parse(x)["lane_finish"] in (1,2) else x for x in lines)+"\n"
    records=[]
    for name,bad in mutations.items():
        try:check(bad,a.parent_dir)
        except ValueError as exc:records.append(dict(mutation=name,detected=True,reason=str(exc),
            mutated_sha256=hashlib.sha256(bad.encode()).hexdigest()))
        else:raise RuntimeError("negative escaped: "+name)
    result=dict(status="C2_PARENT_SUPPLEMENT_NEGATIVE_PASS",source_log_sha256=hashlib.sha256(raw).hexdigest(),
        count=len(records),records=records,scope="offline observation mutations only; not RTL mutation coverage")
    if a.output.exists():raise ValueError("output exists")
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
