#!/usr/bin/env python3
"""Read existing reports and mapping JSON only; no EDA or simulator subprocess."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import re
from collections import Counter

COST = Path("/home/riscv/riscv-lab/o2-c2-cost-20261025")
ROOTS = {"before": COST.parent/"o2-r3-div-gate-cost-20261025", "after": COST}
PATHS = ["r2r", "vdot_r2r", "vdot_r2o", "ready", "icg2"]
PIN = re.compile(r"^\s+([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\s+([\^v])\s+(c\d+)/(\w+)\s+\(([^)]+)\)")
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def main(out):
    assert out.is_absolute() and not out.exists(), "fresh absolute JSON output required"
    assert out.parent.resolve()==Path(__file__).resolve().parent, "output confined to analysis directory"
    result={};inputs={}
    def read(p):
        inputs[str(p)]=sha(p);return json.loads(p.read_text())
    for version,root in ROOTS.items():
        m=read(root/"parent-map-01/mapped.json")["modules"]["CommonParentCostTop"]
        binding=read(root/"parent-sta-01/instance-binding.json")
        inverse={v:k for k,v in binding.items()}
        records={};selected=set()
        for name in PATHS:
            p=(COST/"screen-01"/version/"nominal/icg2.rpt" if name=="icg2"
               else root/"parent-sta-01/nominal"/(name+".rpt"))
            inputs[str(p)]=sha(p);text=p.read_text();rows=[];points={}
            for label in ["Startpoint","Endpoint"]:
                point=re.search(label+r": (\S+)",text).group(1)
                if point in binding:
                    cell=m["cells"][binding[point]]
                    points[label]=dict(canonical=point,original=binding[point],type=cell["type"],connections=cell["connections"])
                    for bits in cell["connections"].values():selected.update(bits)
                else:points[label]=dict(port=point)
            for line in text.split("data arrival time")[0].splitlines():
                match=PIN.match(line)
                if not match:continue
                slew,delay,time,edge,inst,pin,typ=match.groups()
                cell=m["cells"][binding[inst]];assert cell["type"]==typ
                bits=cell["connections"][pin];selected.update(bits)
                rows.append(dict(instance=inst,pin=pin,type=typ,delay_ns=float(delay),time_ns=float(time),
                                 slew_ns=float(slew),edge=edge,bits=bits,output=cell["port_directions"][pin]=="output"))
            arrival=float(re.search(r"([\d.]+)\s+data arrival time",text).group(1))
            external=.1 if "port" in points["Startpoint"] else 0
            logic=[x for x in rows if x["output"] and not x["type"].startswith("DFF")]
            q=[x for x in rows if x["output"] and x["type"].startswith("DFF")]
            wire=arrival-external-sum(x["delay_ns"] for x in logic+q)
            assert 0<=wire<.001,"unexpected residual delay"
            records[name]=dict(points=points,rows=rows,arrival_ns=arrival,external_ns=external,
                clock_to_q_ns=sum(x["delay_ns"] for x in q),logic_ns=sum(x["delay_ns"] for x in logic),
                wire_ns=wire,logic_cells=len(logic),types=dict(Counter(x["type"] for x in logic)),
                top_cell_delays=sorted(logic,key=lambda x:x["delay_ns"],reverse=True)[:6])
        aliases={bit:[] for bit in selected if isinstance(bit,int)}
        for name,row in m["netnames"].items():
            if name.startswith("$"):continue
            for i,bit in enumerate(row["bits"]):
                if bit in aliases:
                    aliases[bit].append(name+(f'[{i+row.get("offset",0)}]' if len(row["bits"])>1 else ""))
        for record in records.values():
            for row in record["rows"]:
                row["aliases"]={str(b):aliases.get(b,[]) for b in row["bits"]}
            for point in record["points"].values():
                if "connections" in point:
                    point["aliases"]={pin:{str(b):aliases.get(b,[]) for b in bits} for pin,bits in point["connections"].items()}
        drivers={}
        for name,cell in m["cells"].items():
            for pin,direction in cell["port_directions"].items():
                if direction=="output":
                    for bit in cell["connections"][pin]:
                        if isinstance(bit,int):
                            assert bit not in drivers,"ambiguous output driver"
                            drivers[bit]=(name,pin)
        gates={}
        for name,cell in m["cells"].items():
            if cell["type"]!="CLKGATETST_X1":continue
            visited=set();seen=set();queue=list(cell["connections"]["E"])
            while queue:
                bit=queue.pop()
                if bit in seen:continue
                seen.add(bit)
                if bit not in drivers:continue
                node,pin=drivers[bit];driver=m["cells"][node]
                if driver["type"].startswith(("DFF","SDFF","CLKGATE","LATCH","DLH","DLL")):continue
                visited.add(inverse[node])
                for p,d in driver["port_directions"].items():
                    if d=="input":queue+=driver["connections"][p]
            gates[name]=dict(canonical=inverse[name],E_cone_cell_count=len(visited),
                datapath_cell_overlap={p:sorted({r["instance"] for r in rec["rows"] if r["output"] and not r["type"].startswith("DFF")} & visited)
                                       for p,rec in records.items()})
        result[version]=dict(paths=records,gates=gates)
        del m,drivers;gc.collect()
    result["scope"]="Static existing report sums/bindings/cone intersections; no EDA, new timing or sensitization proof."
    result["input_sha256"]=inputs
    out.write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    main(p.parse_args().output)
