#!/usr/bin/env python3
"""Run fixed pre-layout setup STA; reject silently swallowed Tcl errors."""
import argparse, hashlib, json, math, re, subprocess, time
from pathlib import Path
from synthesize import DEFAULT
import live_contract

PROFILES={"nominal":(1,5),"period050":(.5,5),"period200":(2,5),"load001":(1,1),"load020":(1,20)}


def require(ok,message):
    if not ok:raise ValueError(message)


def required_paths(boundary):
    require(boundary in ("fu","parent"),"unknown timing boundary")
    paths={"r2r","i2r","r2o","i2o","ready"}
    if boundary=="parent":paths|={"vdot_r2r","vdot_i2r","vdot_r2o","gate_enable"}
    return paths


def constant_warnings(checks,design,case_zero_ports=()):
    constants=set()
    for port,info in design["ports"].items():
        if info["direction"]!="output":continue
        for i,bit in enumerate(info["bits"]):
            if bit in ["0","1"]:
                constants.add(port if len(info["bits"])==1 else f"{port}[{i+info.get('offset',0)}]")
    case_bits=set()
    for name in case_zero_ports:
        port=design["ports"][name]
        if port["direction"]!="input" or len(port["bits"])!=1:raise ValueError("unsupported case-analysis port")
        case_bits.update(port["bits"])
    for name,cell in design.get("cells",{}).items():
        if cell["type"]=="CLKGATETST_X1" and len(cell["connections"].get("SE",[]))==1 and cell["connections"]["SE"][0] in case_bits:
            constants.add(name+"/SE")
    warnings=re.findall(r"Warning: There are (\d+) unconstrained endpoints\.\n((?:  [^\n]+\n)*)",checks)
    allowed=set()
    for count,body in warnings:
        endpoints={x.strip() for x in body.strip().splitlines()}
        if len(endpoints)!=int(count) or not endpoints<=constants:
            raise ValueError(f"nonconstant unconstrained endpoints: {endpoints-constants}")
        allowed|=endpoints
    remaining=re.sub(r"Warning: There are \d+ unconstrained endpoints\.\n(?:  [^\n]+\n)*","",checks).strip()
    if remaining:raise ValueError(f"unreviewed setup warning: {remaining}")
    return sorted(allowed)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def parse_path(text):
    if "No paths found." in text:
        require(text.strip()=="No paths found.","ambiguous no-path report")
        return {"exists":False}
    if text.count("Startpoint:")!=1 or text.count("Endpoint:")!=1:
        raise ValueError("missing path or explicit no-path result")
    arrivals=re.findall(r"^\s*([-+0-9.]+)\s+data arrival time\s*$",text,re.M)
    slacks=re.findall(r"^\s*([-+0-9.]+)\s+slack \((?:MET|VIOLATED)\)",text,re.M)
    if len(arrivals) not in (1,2) or len(slacks)!=1: raise ValueError("missing/ambiguous arrival/slack")
    values=[float(v) for v in arrivals+slacks]
    require(all(math.isfinite(v) for v in values) and values[0]>=0,"nonfinite or negative path delay")
    if len(arrivals)==2:
        require(math.isclose(float(arrivals[1]),-values[0],abs_tol=1e-6),"inconsistent slack arrival subtraction")
    return {"exists":True,"arrival_ns":float(arrivals[0]),"slack_ns":float(slacks[-1]),"startpoint":re.search(r"Startpoint:\s*([^\n]+)",text).group(1),"endpoint":re.search(r"Endpoint:\s*([^\n]+)",text).group(1)}
def validate_log(text):
    if re.search(r"(?m)^(Error:|.*\bError:)",text) or text.splitlines().count("O4_STA_COMPLETE")!=1 or "not found" in text: raise ValueError("STA Tcl error or incomplete execution")
def main():
    from collections import Counter
    p=argparse.ArgumentParser();p.add_argument("mapping",type=Path);p.add_argument("output",type=Path);p.add_argument("--work",type=Path,default=DEFAULT);a=p.parse_args()
    m=json.loads((a.mapping/"summary.json").read_text())
    require(m.get("pass") is True and type(m.get("exit_code")) is int and m["exit_code"]==0,"mapping incomplete")
    live_contract.validate(m.get("tool_contract"))
    require(m.get("tool_contract_unchanged") is True,"mapping tools not verified")
    contract=live_contract.verify(a.work,m["tool_contract"])
    require(sha(a.mapping/"mapped.v")==m["mapped_sha256"], 'timing input or canonical mapping validation failed')
    a.output.mkdir(parents=True,exist_ok=False)
    lib=a.work/"library/NangateOpenCellLibrary_typical.lib"
    require(sha(lib)==m["library_sha256"], 'timing input or canonical mapping validation failed')
    original=json.loads((a.mapping/"mapped.json").read_text())["modules"][m["top"]]
    design=original
    binding=None
    sta_netlist=a.mapping/"mapped.v"
    if m["boundary"]=="parent":
        from canonical import emit,bind
        from compact import topology
        sta_netlist=a.output/"sta-canonical.v"
        by_instance=emit(original,m["top"],sta_netlist)
        (a.output/"instance-binding.json").write_text(json.dumps(by_instance,sort_keys=True)+"\n")
        ys=a.output/"import-canonical.ys"
        ys.write_text(f"read_liberty -lib {lib}\nread_verilog {sta_netlist}\nhierarchy -check -top {m['top']}\nwrite_json {a.output/'sta-names.json'}\n")
        command=[str(a.work/"tools/root/usr/bin/yosys"),"-T","-s",str(ys)]
        with (a.output/"import-canonical.log").open("w") as f:
            try:rc=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=live_contract.environment()).returncode
            except subprocess.TimeoutExpired:rc=124
        binding={"command":command,"exit_code":rc,"input_mapping_json_sha256":sha(a.mapping/"mapped.json"),"sta_netlist_sha256":sha(sta_netlist),"instance_binding_sha256":sha(a.output/"instance-binding.json"),"import_json_sha256":sha(a.output/"sta-names.json") if (a.output/"sta-names.json").exists() else None}
        (a.output/"canonical-binding.json").write_text(json.dumps(binding,indent=2)+"\n")
        live_contract.verify(a.work,contract)
        binding.update(tool_contract=contract,tool_contract_unchanged=True)
        if rc:raise ValueError("canonical import failed")
        design=json.loads((a.output/"sta-names.json").read_text())["modules"][m["top"]]
        design=bind(design,original,by_instance)
        require({n:(v["direction"],len(v["bits"])) for n,v in original["ports"].items()}=={n:(v["direction"],len(v["bits"])) for n,v in design["ports"].items()}, 'timing input or canonical mapping validation failed')
        require(Counter(c["type"] for c in original["cells"].values())==Counter(c["type"] for c in design["cells"].values()), 'timing input or canonical mapping validation failed')
        require(topology(original)==topology(design,True), 'timing input or canonical mapping validation failed')
        binding["topology_sha256"]=topology(original)
        (a.output/"canonical-binding.json").write_text(json.dumps(binding,indent=2)+"\n")
    vdot_bits={b for n,v in design["netnames"].items() if n.startswith("dut.Vdot.") for b in v["bits"] if isinstance(b,int)}
    vdot_regs={n:c for n,c in design["cells"].items() if c["type"].startswith("DFF") and (c.get("attributes",{}).get("o4_vdot") in ["1",1] or any(b in vdot_bits for b in c["connections"].get("Q",[])))}
    gate_regs={n:c for n,c in design["cells"].items() if c["type"]=="CLKGATETST_X1"}
    if m["boundary"]=="parent":require(len(vdot_regs)>100 and len(gate_regs)==3, 'timing input or canonical mapping validation failed')
    ready_names=[n for n,v in design["ports"].items() if n in ["io_in_ready","io_in_ready_0"] and v["direction"]=="output"]
    require(len(ready_names)==1 and "io_out_ready" in design["ports"], 'timing input or canonical mapping validation failed')
    ready_out=ready_names[0]
    profiles=[("nominal",1.0,5),("period050",0.5,5),("period200",2.0,5),("load001",1.0,1),("load020",1.0,20)]
    allresults=[]
    for name,period,load in profiles:
        d=a.output/name;d.mkdir()
        lines=['fconfigure stdout -buffering line',f"read_liberty {lib}","set_cmd_units -time ns -capacitance fF","set_wire_load_mode top","set_wire_load_model -name 5K_hvratio_1_1",
          f"read_verilog {sta_netlist}",f"link_design {m['top']}",
          'set inputs {}','foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}','set outputs [all_outputs]',
          f"create_clock -name core_clk -period {period} [get_ports clock]","set_clock_uncertainty 0.05 [get_clocks core_clk]","set_clock_transition 0.05 [get_clocks core_clk]",
          "set_input_delay -max 0.1 -clock core_clk $inputs","set_output_delay -max 0.1 -clock core_clk $outputs","set_input_transition 0.05 $inputs",f"set_load {load} $outputs",
          'puts "O4_CMD_UNITS time=ns capacitance=fF (explicit set_cmd_units accepted)"',
          'puts "O4_CONSTRAINED_INPUT_BITS [llength $inputs]"','puts "O4_CONSTRAINED_OUTPUT_BITS [llength $outputs]"',
          'puts "O4_REGISTER_CELLS [llength [all_registers -cells]]"']
        if m["boundary"]=="parent":lines+=["set_case_analysis 0 [get_ports testEnable]"]
        lines+=["report_clock_properties [get_clocks core_clk]",f"check_setup -verbose > {d/'setup-checks.rpt'}","set q [all_registers -output_pins]","set d [all_registers -data_pins]"]
        paths={"r2r":"-from $q -to $d","i2r":"-from $inputs -to $d","r2o":"-from $q -to $outputs","i2o":"-from $inputs -to $outputs","ready":f"-from [get_ports io_out_ready] -to [get_ports {ready_out}]"}
        if m["boundary"]=="parent":
            qpins=" ".join(n+"/Q" for n in vdot_regs);dpins=" ".join(n+"/D" for n in vdot_regs);epins=" ".join(n+"/E" for n in gate_regs)
            lines += [f"set vq [get_pins {{{qpins}}}]",f"set vd [get_pins {{{dpins}}}]",f"set ge [get_pins {{{epins}}}]"]
            paths.update(vdot_r2r="-from $vq -to $vd",vdot_i2r="-from $inputs -to $vd",vdot_r2o="-from $vq -to $outputs",gate_enable="-to $ge")
        for key,selectors in paths.items():
            lines+=[f"report_checks {selectors} -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {{capacitance slew input_pin net}} -digits 6 -no_line_splits > {d/(key+'.rpt')}"]
        lines+=['puts "O4_STA_COMPLETE"',"exit"]
        (d/"timing.tcl").write_text("\n".join(lines)+"\n")
        command=[str(a.work/"tools/root/usr/bin/sta"),"-no_init","-exit",str(d/"timing.tcl")]
        live_contract.verify(a.work,contract)
        start=time.time()
        with (d/"sta.log").open("w") as f:
            try:rc=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=live_contract.environment()).returncode
            except subprocess.TimeoutExpired:rc=124
        (d/"run.json").write_text(json.dumps({"command":command,"exit_code":rc,"start":start,"end":time.time()},indent=2)+"\n")
        live_contract.verify(a.work,contract)
        (d/"run.json").write_text(json.dumps({"command":command,"exit_code":rc,"start":start,"end":time.time(),"tool_contract":contract,"tool_contract_unchanged":True},indent=2)+"\n")
        if rc:raise ValueError(f"STA nonzero {rc}")
        log=(d/"sta.log").read_text();validate_log(log)
        if "not found" in log:raise ValueError("unbound object in STA")
        parsed={k:parse_path((d/(k+".rpt")).read_text()) for k in paths}
        for k in paths:
            if not parsed[k]["exists"]:raise ValueError(f"missing required path {name}/{k}")
        checks=(d/"setup-checks.rpt").read_text();allowed=constant_warnings(checks,design,["testEnable"] if m["boundary"]=="parent" else [])
        allresults.append({"profile":name,"period_ns":period,"load_ff":load,"paths":parsed,"setup_checks":checks,"reviewed_unconstrained_endpoints":sorted(allowed),"log_sha256":sha(d/"sta.log")})
    summary={"mode":m["mode"],"boundary":m["boundary"],"mapping_summary_sha256":sha(a.mapping/"summary.json"),"mapped_sha256":m["mapped_sha256"],"library_sha256":m["library_sha256"],"wire_load_model":"5K_hvratio_1_1","name_binding":binding,"vdot_register_count":len(vdot_regs),"gate_count":len(gate_regs),"profiles":allresults,"pass":True}
    summary.update(tool_contract=contract,tool_contract_unchanged=True)
    (a.output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"mode":m["mode"],"boundary":m["boundary"],"profiles":len(allresults),"pass":True}))
if __name__=="__main__":main()
