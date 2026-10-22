"""O3 exact straight-line ELF windows; original counter checks remain unchanged."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("o3_frozen_counter_checker",ROOT/"team/workloads/unified-vdot/check.py")
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def walk(words):
    start=[pc for pc,w in words.items() if w==base.START]
    stop=[pc for pc,w in words.items() if w==base.STOP]
    base.require(len(start)==len(stop)==1,"unique O3 markers")
    a,b=start[0],stop[0]
    base.require(a<b and (b-a)//4<20000,"invalid O3 straight-line window")
    result=[]
    for pc in range(a,b+4,4):
        base.require(pc in words,"O3 code hole")
        word=words[pc]
        base.require(word&127 not in (0x63,0x6f,0x67),"branch/call/jump in unrolled O3 kernel")
        result.append((pc,word))
    base.require([w for _,w in result if w in base.COUNTERS]==base.COUNTERS,"O3 counter order")
    return result

base.walk=walk

def verify(build,run,external=None):
    result=base.verify(Path(build),Path(run),external)
    result["scope"]="O3 full GEMV math/state, live DiffTest, original calibrated counters and exact straight-line ELF retirement"
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build",type=Path,required=True);p.add_argument("--run",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();value=verify(a.build,a.run)
    with a.output.open("x",encoding="utf-8") as f:json.dump(value,f,indent=2);f.write("\n")
    print(json.dumps({"status":value["status"],"windows":len(value["samples"])}))
