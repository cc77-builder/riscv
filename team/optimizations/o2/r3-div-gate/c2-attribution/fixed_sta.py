"""One fixed-netlist nominal STA per version, common semantic endpoints."""
import argparse,datetime,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,m):
    if not x:raise ValueError(m)
def main():
    p=argparse.ArgumentParser()
    for n in ("repo","before","after","output"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),"new output required");a.output.mkdir()
    helper=a.repo/"team/optimizations/o2/r3-div-gate/timing-review/review.py"
    spec=importlib.util.spec_from_file_location("review",helper);review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
    tool=Path("/home/riscv/riscv-lab/o4-cost-20261020");sta=tool/"tools/root/usr/bin/sta"
    identity=json.loads((tool/"tools/executable-identities.json").read_text())["sta"]
    pins={str(sta):identity["sha256"],str(helper):sha(helper),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    pins.update(identity["shared_library_sha256"])
    lib=tool/"library/NangateOpenCellLibrary_typical.lib";pins[str(lib)]=sha(lib)
    state=dict(status="running",started=datetime.datetime.now().astimezone().isoformat(),steps=[])
    def save(): (a.output/"state.json").write_text(json.dumps(state,indent=2)+"\n")
    save();allpaths={}
    for version,root in [("before",a.before),("after",a.after)]:
        for rel in ["parent-map-01/mapped.json","parent-sta-01/instance-binding.json","parent-sta-01/sta-canonical.v","parent-sta-01/nominal/timing.tcl"]:
            f=root/rel;pins[str(f)]=sha(f)
        d=review.Design(root);out=a.output/version;out.mkdir()
        def reg(name,end="Q"):
            cell,pin=d.drivers[d.net_bit(name)]
            need(d.mapping["cells"][cell]["type"].startswith("DFF"),"expected register "+name)
            return d.reverse[cell]+"/"+("D" if end=="D" else pin)
        gate=d.reverse["dut.ClockGate_1.impl"]+"/E"
        fp="dut.Vfdiv.vfdivs_0.u_vector_float_divider_r64.fsm_q[0]"
        busy="dut.elasticDivOccupied_divBusy"
        hold="dut.uncer_en_reg_1" if version=="before" else "dut.elasticDivOccupied_divOwnerIsFp"
        queries={
            "icg_all":f"-to [get_pins {{{gate}}}]",
            "icg_from_fpready":f"-from [get_pins {{{reg(fp)}}}] -to [get_pins {{{gate}}}]",
            "icg_from_busy":f"-from [get_pins {{{reg(busy)}}}] -to [get_pins {{{gate}}}]",
            "icg_from_hold_or_owner":f"-from [get_pins {{{reg(hold)}}}] -to [get_pins {{{gate}}}]",
            "icg_from_valid":f"-from [get_ports io_in_valid] -to [get_pins {{{gate}}}]",
            "icg_from_flush":f"-from [get_ports io_flush_valid] -to [get_pins {{{gate}}}]",
            "icg_from_reset":f"-from [get_ports reset] -to [get_pins {{{gate}}}]",
            "vdot_lane4":f"-from [get_pins {{{reg('dut.Vdot.pProducts_4[1]')}}}] -to [get_pins {{{reg('dut.Vdot.rPacket_res_data[18]','D')}}}]",
            "vdot_lane6":f"-from [get_pins {{{reg('dut.Vdot.pProducts_6[1]')}}}] -to [get_pins {{{reg('dut.Vdot.rPacket_res_data[18]','D')}}}]",
            "ready_fixed":"-from [get_ports io_out_ready] -to [get_ports io_in_ready]",
        }
        original=(root/"parent-sta-01/nominal/timing.tcl").read_text().splitlines()
        prefix=original[:next(i for i,x in enumerate(original) if x.startswith("check_setup "))]
        tcl=prefix+[f"report_checks {selector} -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {{capacitance slew input_pin net}} -digits 6 -no_line_splits > {out/(key+'.rpt')}" for key,selector in queries.items()]
        tcl+=['puts "C2_READ_ONLY_STA_COMPLETE"',"exit"]
        (out/"timing.tcl").write_text("\n".join(tcl)+"\n")
        (out/"queries.json").write_text(json.dumps(queries,indent=2)+"\n")
        for path,h in pins.items():need(sha(Path(path))==h,"input changed "+path)
        cmd=[str(sta),"-no_init","-exit",str(out/"timing.tcl")]
        rec=dict(version=version,command=cmd,started=datetime.datetime.now().astimezone().isoformat())
        state["steps"].append(rec);save()
        with (out/"sta.log").open("x") as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=300).returncode
        rec.update(exit_code=rc,finished=datetime.datetime.now().astimezone().isoformat());save()
        log=(out/"sta.log").read_text()
        need(rc==0 and "C2_READ_ONLY_STA_COMPLETE" in log and not re.search(r"(?im)^Error|not found",log),"STA tool error")
        allpaths[version]={key:d.parse(out/(key+".rpt")) for key in queries}
        (out/"paths.json").write_text(json.dumps(allpaths[version],ensure_ascii=False,indent=2)+"\n")
        print(version,{k:v["arrival_ns"] for k,v in allpaths[version].items()},flush=True)
    for path,h in pins.items():need(sha(Path(path))==h,"input changed "+path)
    (a.output/"inputs.json").write_text(json.dumps(pins,indent=2)+"\n")
    (a.output/"results.json").write_text(json.dumps(allpaths,ensure_ascii=False,indent=2)+"\n")
    state.update(status="C2_FIXED_NETLIST_STA_COMPLETE",finished=datetime.datetime.now().astimezone().isoformat());save()
if __name__=="__main__":main()
