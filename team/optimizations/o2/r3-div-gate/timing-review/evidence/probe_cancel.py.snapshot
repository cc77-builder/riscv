"""One bounded after-only probe motivated by the newly found hold-D regression."""
import argparse, json, subprocess
from pathlib import Path
from review import Design, need, save, sha, stamp

p=argparse.ArgumentParser()
p.add_argument("--campaign",type=Path,required=True)
a=p.parse_args()
root=a.campaign
inputs=json.loads((root/"run-01/inputs.json").read_text())
for path,h in inputs.items(): need(sha(path)==h,"changed input "+path)
d=Design(Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025"))
out=root/"cancel-path-01"
need(not (out/"run.json").exists(),"already run")
rob=json.loads((root/"cancel-targets.json").read_text())["rob_pins"]
sources={"rob":"[get_pins {"+" ".join(rob)+"}]",
         "divbusy":"[get_pins {"+d.reg("dut.elasticDivOccupied_divBusy")+"/Q}]",
         "flush_index":"[get_ports {io_flush_bits_robIdx*}]",
         "flush_level":"[get_ports io_flush_bits_level]"}
queries={}
for label,net in [("float_hold","dut.uncer_en_reg"),("int_hold","dut.uncer_en_reg_1")]:
    reg=d.reg(net)
    for kind,expr in dict(sources,self="[get_pins {"+reg+"/Q}]").items():
        queries[label+"_"+kind]=(expr,"[get_pins {"+reg+"/D}]")
lines=(d.sta/"nominal/timing.tcl").read_text().splitlines()
tcl=lines[:next(i for i,l in enumerate(lines) if l.startswith("check_setup "))]
for name,(frm,to) in queries.items():
    tcl.append(f"report_checks -from {frm} -to {to} -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {{capacitance slew input_pin net}} -digits 6 -no_line_splits > {out/(name+'.rpt')}")
tcl+=['puts "R3_CANCEL_PROBE_COMPLETE"',"exit"]
(out/"timing.tcl").write_text("\n".join(tcl)+"\n")
save(out/"queries.json",queries)
cmd=["/home/riscv/riscv-lab/o4-cost-20261020/tools/root/usr/bin/sta","-no_init","-exit",str(out/"timing.tcl")]
rec=dict(command=cmd,started=stamp(),script_sha256=sha(__file__))
save(out/"run.json",rec)
with (out/"sta.log").open("xb") as log:
    rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
rec.update(exit_code=rc,finished=stamp())
save(out/"run.json",rec)
need(rc==0 and "R3_CANCEL_PROBE_COMPLETE" in (out/"sta.log").read_text(),"STA failed")
results={k:d.parse(out/(k+".rpt")) for k in queries}
for path,h in inputs.items(): need(sha(path)==h,"input changed "+path)
save(out/"results.json",dict(status="R3_CANCEL_PROBE_PASS",paths=results,input_sha_unchanged=True))
print(json.dumps({k:{f:x[f] for f in ("arrival_ns","slack_ns","buffer_count")} for k,x in results.items()},indent=2))
