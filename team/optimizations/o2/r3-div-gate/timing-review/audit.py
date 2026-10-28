"""Offline cross-check of the timing review against sealed inputs and raw STA."""
import argparse,json,re,subprocess
from pathlib import Path
from review import Design,need,sha,save,stamp
p=argparse.ArgumentParser()
p.add_argument("--campaign",required=True,type=Path)
p.add_argument("--repo",required=True,type=Path)
p.add_argument("--output",required=True,type=Path)
a=p.parse_args()
need(not a.output.exists(),"receipt exists")
root=a.campaign
sealed=a.repo/"team/optimizations/o2/r3-div-gate/evidence/20261025-performance-cost/manifest.json"
need(sha(sealed)=="9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77","sealed manifest changed")
manifest={x["path"]:x["raw_sha256"] for x in json.loads(sealed.read_text())["files"]}
inputs=json.loads((root/"run-01/inputs.json").read_text())
roots={"before":Path("/home/riscv/riscv-lab/o2-h1-result32-20261021"),"after":Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025")}
bound=0
for path,h in inputs.items():
    need(sha(path)==h,"input changed")
    for label,base in roots.items():
        if Path(path).is_relative_to(base):
            key=("baseline-h1/" if label=="before" else "cost/")+str(Path(path).relative_to(base))
            need(manifest[key]==h,"input differs from sealed original "+key)
            bound+=1
original=json.loads((root/"run-01/original-paths.json").read_text())
pairs=json.loads((root/"run-01/comparison.json").read_text())
need(pairs["status"]=="R3_TARGETED_STA_REVIEW_PASS","main failed")
count=0
for mode,base in roots.items():
    d=Design(base)
    baseline=next(x for x in json.loads((base/"parent-sta-01/summary.json").read_text())["profiles"] if x["profile"]=="nominal")["paths"]
    for key,x in original[mode].items():
        for f in ("arrival_ns","slack_ns","startpoint","endpoint"):
            need(x[f]==baseline[key][f],"original parse disagrees "+mode+key+f)
    out=root/"run-01"/mode
    paths=json.loads((out/"paths.json").read_text())
    for name,x in paths.items():
        need(d.parse(out/(name+".rpt"))==x,"parsed report differs "+name)
        text=(out/(name+".rpt")).read_text()
        vals=re.findall(r"([-0-9.]+)\s+data arrival time",text)
        need(len(vals)==2 and abs(float(vals[0])+float(vals[1]))<1e-6,"arrival accounting "+name)
        count+=1
    for key in ("r2r","i2r"):
        x=paths["fixed_"+mode+"_"+key]
        need(x["arrival_ns"]==original[mode][key]["arrival_ns"],"fixed endpoint reproduction failed")
        need(x["startpoint"]==original[mode][key]["startpoint"] and x["endpoint"]==original[mode][key]["endpoint"],"endpoint differs")
    need(paths["icg0_all"]["arrival_ns"]==baseline["gate_enable"]["arrival_ns"],"gate reproduction failed")
    src=(base/"parent-sta-01/nominal/timing.tcl").read_text().splitlines()
    stop=next(i for i,l in enumerate(src) if l.startswith("check_setup "))
    need((out/"timing.tcl").read_text().splitlines()[:stop]==src[:stop],"constraints changed")
    if mode=="before": before=paths
    else: after=paths
for k,x in pairs["paths"].items():
    need(x["before_arrival_ns"]==before[k]["arrival_ns"] and x["after_arrival_ns"]==after[k]["arrival_ns"],"pair mismatched")
    need(abs(x["delta_ps"]-1000*(after[k]["arrival_ns"]-before[k]["arrival_ns"]))<1e-6,"delta wrong")
probe=json.loads((root/"cancel-path-01/results.json").read_text())
need(probe["status"]=="R3_CANCEL_PROBE_PASS","probe failed")
for name,x in probe["paths"].items():
    need(d.parse(root/"cancel-path-01"/(name+".rpt"))==x,"probe raw differs")
    count+=1
need((root/"cancel-path-01/timing.tcl").read_text().splitlines()[:stop]==src[:stop],"probe constraints changed")
# Verify unchanged gate-enable expressions in generated production interfaces.
gate_connections={}
for mode,base in roots.items():
    text=(base/"parent-cost-01/rtl/ExeUnit.sv").read_text()
    gates=re.findall(r"ClockGate\s+ClockGate(?:_\d+)?\s*\((.*?)\);",text,re.S)
    need(len(gates)==3,"gate instance count")
    gate_connections[mode]=[re.search(r"\.E\s*\((.*?)\),",g,re.S)[1].strip() for g in gates]
need(gate_connections["before"]==gate_connections["after"],"gate E RTL changed")
# The long after hold-D route shares the gate-enable node; no such stage before.
need(any("dut.ClockGate.E" in s["rtl_nets"] for s in after["float_hold_regs"]["stages"]),"missing shared node")
need(not any("dut.ClockGate.E" in s["rtl_nets"] for s in before["float_hold_regs"]["stages"]),"unexpected baseline shared node")
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=a.repo,text=True).strip()
need(head=="0f12df675378556670afd0dd2153f47fcb330610","source HEAD changed")
need(not subprocess.check_output(["git","diff","--name-only","HEAD","--","src"],cwd=a.repo,text=True).strip(),"production changes")
delay=after["float_hold_regs"]["arrival_ns"]-before["float_hold_regs"]["arrival_ns"]
buffers=after["float_hold_regs"]["buffer_delay_ns"]-before["float_hold_regs"]["buffer_delay_ns"]
save(a.output,dict(status="R3_TIMING_REVIEW_OFFLINE_AUDIT_PASS",completed=stamp(),source_commit=head,
    archive_manifest_sha256=sha(sealed),archive_bound_inputs=bound,raw_new_reports_reparsed=count,
    original_nominal_paths_crosschecked=18,fixed_endpoint_reproductions=4,gate_worst_reproductions=2,
    constraints_preserved=True,inputs_unchanged=True,gate_enable_expressions=gate_connections,
    float_hold_buffer_delta_ps=round(buffers*1000,3),float_hold_total_delta_ps=round(delay*1000,3),
    buffer_fraction_of_delta=buffers/delay,github_push=False,
    scope="Three actual STA processes, no synthesis/EMU/RTL modifications; not formal or physical timing closure"))
print(a.output.read_text())
