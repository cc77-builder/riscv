#!/usr/bin/env python3
"""One bounded, logged mapping attempt; exits on tool or unmapped-cell errors."""
import argparse, hashlib, json, os, re, subprocess, time
from collections import Counter
from pathlib import Path
DEFAULT=Path("/home/riscv/riscv-lab/o4-cost-20261020")
def require(ok,message):
    if not ok:raise ValueError(message)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def library_areas(path):
    text=path.read_text()
    # Nangate cells each have a scalar area before their pins.
    pairs=re.findall(r"cell\s*\(\s*(\w+)\s*\)\s*\{.*?\barea\s*:\s*([0-9.eE+-]+)",text,re.S)
    if not pairs: raise ValueError("no cell areas")
    return {k:float(v) for k,v in pairs}
def main():
    p=argparse.ArgumentParser(); p.add_argument("generation",type=Path);p.add_argument("output",type=Path);p.add_argument("--work",type=Path,default=DEFAULT);a=p.parse_args()
    g=json.loads((a.generation/"result.json").read_text()); require(type(g.get("exit_code")) is int and g["exit_code"]==0 and not g.get("verification_error") and isinstance(g.get("source_inputs"),dict) and bool(g["source_inputs"]) and g.get("source_inputs_unchanged") is True, "synthesis input/mapping validation failed")
    a.output.mkdir(parents=True,exist_ok=False)
    lib=a.work/"library/NangateOpenCellLibrary_typical.lib"; bin=a.work/"tools/root/usr/bin"
    top="CommonFuCostTop" if g["boundary"]=="fu" else "CommonParentCostTop"
    rtl=sorted((a.generation/"rtl").glob("*.sv"))
    replacement=[]
    if g["boundary"]=="parent":
        originals=[f for f in rtl if f.stem=="ClockGate"];require(len(originals)==1, "synthesis input/mapping validation failed")
        original=originals[0].read_text()
        require(re.search(r"if\s*\(!CK\).*?EN\s*=\s*TE\s*\|\s*E",original,re.S), "synthesis input/mapping validation failed")
        require(re.search(r"assign\s+Q\s*=\s*CK\s*&\s*EN",original), "synthesis input/mapping validation failed")
        (a.output/"ClockGate.original.sv").write_text(original)
        mapfile=a.output/"ClockGate.map.v"
        mapfile.write_text("module ClockGate(input TE, E, CK, output Q);\n  CLKGATETST_X1 impl(.CK(CK), .E(E), .SE(TE), .GCK(Q));\nendmodule\n")
        rtl=[f for f in rtl if f not in originals]+[mapfile]
        replacement=[{"original":str(originals[0]),"sha256":sha(originals[0]),"replacement":str(mapfile),"replacement_sha256":sha(mapfile),"cell":"CLKGATETST_X1","behavior":"low CK transparent latch EN=TE|E; Q=CK&EN"}]
    (a.output/"abc.constr").write_text("set_driving_cell BUF_X1\nset_load 5.0\n")
    commands=[f"read_liberty -lib {lib}",*[f"read_verilog -sv -DSYNTHESIS {f}" for f in rtl],f"hierarchy -check -top {top}","proc","opt",f"write_json {a.output/'structure.json'}",f"synth -top {top} -flatten -noabc",f"dfflibmap -liberty {lib}",f"abc -exe {bin/'berkeley-abc'} -liberty {lib} -D 1000 -constr {a.output/'abc.constr'}","clean","check -assert",f"stat -liberty {lib}",f"write_json {a.output/'mapped.json'}",f"write_verilog -noattr {a.output/'mapped.v'}"]
    (a.output/"map.ys").write_text("\n".join(commands)+"\n")
    command=[str(bin/"yosys"),"-T","-s",str(a.output/"map.ys")]
    meta={"generation":str(a.generation),"generation_sha256":sha(a.generation/"result.json"),"mode":g["mode"],"boundary":g["boundary"],"top":top,"library_sha256":sha(lib),"command":command,"clockgate_mapping":replacement,"start":time.time(),"timeout_seconds":1800}
    try:
        with (a.output/"synthesis.log").open("w") as f:
            rc=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=1800).returncode
    except subprocess.TimeoutExpired: rc=124
    meta.update(exit_code=rc,end=time.time())
    (a.output/"run.json").write_text(json.dumps(meta,indent=2)+"\n")
    if rc: print(json.dumps(meta));raise SystemExit(rc)
    design=json.loads((a.output/"mapped.json").read_text())["modules"][top]
    counts=Counter(c["type"] for c in design["cells"].values());areas=library_areas(lib)
    unknown=sorted(set(counts)-set(areas))
    if unknown: raise ValueError(f"unknown or unmapped cells: {unknown}")
    area=sum(counts[k]*areas[k] for k in counts)
    log=(a.output/"synthesis.log").read_text()
    reportareas=re.findall(r"Chip area for module.*?:\s*([0-9.]+)",log)
    require(reportareas and abs(float(reportareas[-1])-area)<0.02, "synthesis input/mapping validation failed")
    summary={**meta,"ports":{k:{"direction":v["direction"],"width":len(v["bits"])} for k,v in design["ports"].items()},"cell_count":sum(counts.values()),"cell_histogram":dict(sorted(counts.items())),"cell_area_sum":area,"unknown_cells":unknown,"mapped_sha256":sha(a.output/"mapped.v"),"mapped_json_sha256":sha(a.output/"mapped.json"),"map_script_sha256":sha(a.output/"map.ys"),"pass":True}
    (a.output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:summary[k] for k in ["mode","boundary","cell_count","cell_area_sum","pass"]}))
if __name__=="__main__":main()
