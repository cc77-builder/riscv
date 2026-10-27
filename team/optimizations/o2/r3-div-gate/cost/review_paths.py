"""Read-only mapping of STA endpoints back to named RTL nets."""
import argparse,json
from pathlib import Path
def review(root):
    mapping=json.loads((root/"parent-map-01/mapped.json").read_text())["modules"]["CommonParentCostTop"]
    binding=json.loads((root/"parent-sta-01/instance-binding.json").read_text())
    timing=json.loads((root/"parent-sta-01/summary.json").read_text())
    nominal=next(x for x in timing["profiles"] if x["profile"]=="nominal")["paths"]
    targets={}
    for kind,path in nominal.items():
        for side in ("startpoint","endpoint"):
            name=path[side].split()[0]
            if name in binding:
                cell=mapping["cells"][binding[name]]
                pins=["Q"] if "Q" in cell["connections"] else ["E","GCK"]
                targets[(kind,side)]=dict(sta_name=name,original_cell=binding[name],type=cell["type"],
                    pins={pin:cell["connections"][pin] for pin in pins if pin in cell["connections"]})
            else:targets[(kind,side)]=dict(sta_name=name,type="port",pins={})
    needed={b for item in targets.values() for bits in item["pins"].values() for b in bits if isinstance(b,int)}
    names={b:[] for b in needed}
    for net,desc in mapping["netnames"].items():
        if not net.startswith("dut."):continue
        for i,b in enumerate(desc["bits"]):
            if b in needed:names[b].append(net+(f"[{i}]" if len(desc["bits"])>1 else ""))
    result={}
    for (kind,side),item in targets.items():
        item["rtl_nets"]={pin:sorted({n for b in bits for n in names.get(b,[])}) for pin,bits in item["pins"].items()}
        result.setdefault(kind,{})[side]=item
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--before",required=True,type=Path);p.add_argument("--after",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    if a.output.exists():raise ValueError("output exists")
    result={name:review(path) for name,path in [("before",a.before),("after",a.after)]}
    a.output.write_text(json.dumps(dict(status="R3_STA_ENDPOINT_REVIEW_COMPLETE",results=result),indent=2)+"\n")
    for mode,rows in result.items():
        for kind in ("r2r","i2r","gate_enable"):
            print(mode,kind,json.dumps(rows[kind],ensure_ascii=False))
if __name__=="__main__":main()
