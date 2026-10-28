"""Audit the extra mapped DFF without changing either netlist."""
import argparse,json
from pathlib import Path
NET="dut.Vidiv.vidiv._16bit_divide_3.Bypass_final_rem_plus_d_reg"
def scan(root):
    d=json.loads((root/"parent-map-01/mapped.json").read_text())["modules"]["CommonParentCostTop"]
    drivers={bit:name for name,c in d["cells"].items() if c["type"].startswith("DFF") for bit in c["connections"]["Q"]}
    groups={name:set() for name in drivers.values()}
    byname={}
    for name,n in d["netnames"].items():
        if not name.startswith("dut."):continue
        for i,bit in enumerate(n["bits"]):
            if bit in drivers:
                label=name+(f"[{i}]" if len(n["bits"])>1 else "")
                groups[drivers[bit]].add(label);byname[label]=drivers[bit]
    bit=d["netnames"][NET]["bits"][2]
    sinks=[];outputs=[]
    for name,c in d["cells"].items():
        for pin,bits in c["connections"].items():
            if bit in bits:
                row=dict(cell=name,type=c["type"],pin=pin)
                (sinks if c["port_directions"][pin]=="input" else outputs).append(row)
    return groups,byname,dict(bit=bit,drivers=outputs,sinks=sinks)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--before",type=Path,required=True)
    ap.add_argument("--after",type=Path,required=True);ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    if a.output.exists():raise ValueError("output exists")
    bg,bn,bt=scan(a.before);ag,an,at=scan(a.after)
    split=[sorted(v) for v in bg.values() if len({an[n] for n in v if n in an})>1]
    merged=[sorted(v) for v in ag.values() if len({bn[n] for n in v if n in bn})>1]
    new=[dict(cell=k,nets=sorted(v)) for k,v in ag.items() if v and not v.intersection(bn)]
    assert len(bg)==17171 and len(ag)==17172 and not split and not merged
    assert len(new)==1 and new[0]["nets"]==[NET+"[2]"]
    assert not bt["drivers"] and not bt["sinks"]
    assert len(at["drivers"])==1 and at["drivers"][0]["type"]=="DFF_X1" and at["sinks"]
    result=dict(status="R3_DFF_MAPPING_DELTA_REVIEW_PASS",before_dffs=len(bg),after_dffs=len(ag),
        new_cells=new,before_target=bt,after_target=at,split_groups=split,merged_groups=merged,
        vdot_metadata_storage_unchanged=True,
        interpretation="One existing integer-DIV remainder register bit is retained by the new whole-parent synthesis; old mapped net has no driver/sinks. No new RTL register declaration or VDot state bit.")
    a.output.write_text(json.dumps(result,indent=2)+"\n");print(result["status"])
if __name__=="__main__":main()
