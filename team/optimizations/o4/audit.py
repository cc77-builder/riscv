#!/usr/bin/env python3
"""Offline audits from raw mapped/STA files; no simulator or synthesis invocation."""
import hashlib, json, math, re
from collections import Counter
from pathlib import Path, PurePosixPath
from synthesize import library_areas
from timing import parse_path, validate_log, constant_warnings, required_paths, PROFILES
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def finite_number(value):
    return type(value) in (int,float) and math.isfinite(value)


def validate_profiles(summary):
    profiles=summary.get("profiles")
    if not isinstance(profiles,list) or len(profiles)!=len(PROFILES):raise ValueError("missing/duplicate sensitivity")
    if any(not isinstance(p,dict) or p.get("profile") not in PROFILES for p in profiles):raise ValueError("unknown sensitivity profile")
    if {p["profile"] for p in profiles}!=set(PROFILES):raise ValueError("missing/duplicate sensitivity")
    paths=required_paths(summary.get("boundary"))
    for p in profiles:
        if not all(finite_number(p.get(k)) for k in ("period_ns","load_ff")) or (p["period_ns"],p["load_ff"])!=PROFILES[p["profile"]]:raise ValueError("constraint mismatch")
        if not isinstance(p.get("paths"),dict) or set(p["paths"])!=paths:raise ValueError("required timing path inventory")
        for value in p["paths"].values():
            if not isinstance(value,dict) or value.get("exists") is not True:raise ValueError("missing required timing path")
            if not finite_number(value.get("arrival_ns")) or value["arrival_ns"]<0 or not finite_number(value.get("slack_ns")):raise ValueError("nonfinite timing value")
            if not all(isinstance(value.get(k),str) and value[k].strip() for k in ("startpoint","endpoint")):raise ValueError("missing timing endpoint")
    return profiles


def validate_tcl(tcl, profile, boundary):
    lines=[line.strip() for line in tcl.splitlines() if line.strip()]
    allowed={"fconfigure","read_liberty","read_verilog","link_design","set","foreach","create_clock","set_cmd_units","set_wire_load_mode","set_wire_load_model","set_clock_uncertainty","set_clock_transition","set_input_delay","set_output_delay","set_input_transition","set_load","set_case_analysis","puts","report_clock_properties","check_setup","report_checks","exit"}
    if any(";" in line or line.split()[0] not in allowed for line in lines):raise ValueError("unsupported Tcl command")
    for command in ("read_liberty","read_verilog","link_design","foreach","create_clock","report_clock_properties","check_setup","exit"):
        if sum(line.split()[0]==command for line in lines)!=1:raise ValueError("duplicate/missing Tcl command")
    fixed=["set_cmd_units -time ns -capacitance fF","set_wire_load_mode top","set_wire_load_model -name 5K_hvratio_1_1","set_clock_uncertainty 0.05 [get_clocks core_clk]","set_clock_transition 0.05 [get_clocks core_clk]","set_input_delay -max 0.1 -clock core_clk $inputs","set_output_delay -max 0.1 -clock core_clk $outputs","set_input_transition 0.05 $inputs",f"set_load {profile['load_ff']} $outputs"]
    cases=["set_case_analysis 0 [get_ports testEnable]"] if boundary=="parent" else []
    if any(lines.count(x)!=1 for x in fixed+cases):raise ValueError("actual Tcl constraints differ")
    constraints=[line for line in lines if line.startswith("set_")]
    if set(constraints)!=set(fixed+cases) or len(constraints)!=len(fixed+cases):raise ValueError("overriding/extra Tcl constraints")
    clocks=[line for line in lines if line.startswith("create_clock")]
    if len(clocks)!=1 or not re.fullmatch(r"create_clock -name core_clk -period [0-9.]+ \[get_ports clock\]",clocks[0]) or float(clocks[0].split()[4])!=profile['period_ns']:raise ValueError("clock/path constraints differ")
    variables={"set inputs {}","set outputs [all_outputs]","set q [all_registers -output_pins]","set d [all_registers -data_pins]"}
    declarations=[line for line in lines if line.startswith("set ")]
    extra=[line for line in declarations if line not in variables]
    if any(declarations.count(x)!=1 for x in variables):raise ValueError("STA input/output/register selectors differ")
    if boundary=="parent":
        if len(extra)!=3 or {line.split()[1] for line in extra}!={"vq","vd","ge"} or any(not re.fullmatch(r"set (vq|vd|ge) \[get_pins \{[^{}]+\}\]",line) for line in extra):raise ValueError("parent timing pin selectors differ")
    elif extra:raise ValueError("extra STA selectors")
    if lines.count('foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}')!=1:raise ValueError("input coverage differs")
    selectors={"r2r":"-from $q -to $d","i2r":"-from $inputs -to $d","r2o":"-from $q -to $outputs","i2o":"-from $inputs -to $outputs"}
    reports={}
    for line in lines:
        if not line.startswith("report_checks "):continue
        match=re.fullmatch(r"report_checks (.+) -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields \{capacitance slew input_pin net\} -digits 6 -no_line_splits > (\S+)",line)
        if not match:raise ValueError("timing report command differs")
        path=Path(match[2]);key=path.stem
        if key in reports or path.parent.name!=profile['profile']:raise ValueError("timing report target differs")
        reports[key]=match[1]
    if set(reports)!=required_paths(boundary):raise ValueError("required timing report commands missing")
    if any(reports[k]!=v for k,v in selectors.items()):raise ValueError("timing path selectors differ")
    if reports["ready"] not in ("-from [get_ports io_out_ready] -to [get_ports io_in_ready]","-from [get_ports io_out_ready] -to [get_ports io_in_ready_0]"):raise ValueError("ready path selector differs")
    if boundary=="parent" and any(reports[k]!=v for k,v in {"vdot_r2r":"-from $vq -to $vd","vdot_i2r":"-from $inputs -to $vd","vdot_r2o":"-from $vq -to $outputs","gate_enable":"-to $ge"}.items()):raise ValueError("parent timing path selectors differ")


def verify_rtl(generation, receipt):
    files=receipt.get("rtl")
    if not isinstance(files,dict) or not files:raise ValueError("missing RTL inventory")
    expected={"rtl/"+p.name for p in (generation/"rtl").iterdir() if p.is_file()}
    required={"rtl/filelist.f","rtl/VDotProducts.sv","rtl/VDotReduce.sv",
              "rtl/"+("CommonFuCostTop.sv" if receipt.get("boundary")=="fu" else "CommonParentCostTop.sv")}
    if set(files)!=expected or not required<=set(files):raise ValueError("RTL physical inventory differs")
    for name,item in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or len(path.parts)!=2 or path.parts[0]!="rtl" or path.as_posix()!=name:raise ValueError("unsafe RTL path")
        file=generation/name
        if not isinstance(item,dict) or type(item.get("bytes")) is not int or file.stat().st_size!=item["bytes"] or sha(file)!=item.get("sha256"):raise ValueError("generated RTL changed")


def compare_interfaces(a,b):
    if a!=b:raise ValueError("O1/O2 interface mismatch")
def mapping_audit(directory,lib):
    s=json.loads((directory/"summary.json").read_text())
    if s.get("pass") is not True or type(s.get("exit_code")) is not int or s["exit_code"]!=0 or sha(lib)!=s["library_sha256"]:raise ValueError("mapping/library identity")
    if sha(directory/"mapped.v")!=s["mapped_sha256"] or sha(directory/"mapped.json")!=s["mapped_json_sha256"]:raise ValueError("mapped identity")
    m=json.loads((directory/"mapped.json").read_text())["modules"][s["top"]]
    counts=Counter(c["type"] for c in m["cells"].values());areas=library_areas(lib)
    if type(s.get("cell_count")) is not int or s["cell_count"]!=sum(counts.values()):raise ValueError("mapped cell count differs")
    ports={k:{"direction":v["direction"],"width":len(v["bits"])} for k,v in m["ports"].items()}
    if s.get("ports")!=ports or any(type(v.get("width")) is not int for v in s["ports"].values()):raise ValueError("mapped port inventory differs")
    if set(counts)-set(areas):raise ValueError("unmapped cells")
    area=sum(counts[k]*areas[k] for k in counts)
    histogram=s.get("cell_histogram",{})
    if not isinstance(histogram,dict) or any(type(v) is not int or v<=0 for v in histogram.values()):raise ValueError("invalid cell histogram")
    if not finite_number(s.get("cell_area_sum")) or any(not finite_number(v) or v<=0 for v in areas.values()):raise ValueError("invalid cell area")
    if dict(sorted(counts.items()))!=histogram or not math.isclose(area,s["cell_area_sum"],rel_tol=0,abs_tol=1e-7):raise ValueError("area/histogram")
    independent=re.findall(r"Chip area for module.*?:\s*([0-9.]+)",(directory/"synthesis.log").read_text())
    if not independent or abs(float(independent[-1])-area)>0.02:raise ValueError("area/log disagree")
    return s,m
def timing_audit(directory,mapping,design):
    s=json.loads((directory/"summary.json").read_text())
    if s.get("pass") is not True or s["mapping_summary_sha256"]!=sha(mapping/"summary.json"):raise ValueError("STA identity")
    ms=json.loads((mapping/"summary.json").read_text())
    if (s.get("mode"),s.get("boundary"))!=(ms.get("mode"),ms.get("boundary")):raise ValueError("STA mode/boundary mismatch")
    if s["library_sha256"]!=ms["library_sha256"] or s["mapped_sha256"]!=ms["mapped_sha256"]:raise ValueError("STA library/netlist binding")
    if s["boundary"]=="parent":
        from compact import topology
        from canonical import bind,emit
        binding=json.loads((directory/"canonical-binding.json").read_text())
        if binding!=s["name_binding"] or type(binding.get("exit_code")) is not int or binding["exit_code"]!=0 or binding["input_mapping_json_sha256"]!=sha(mapping/"mapped.json"):raise ValueError("name binding")
        for filename,key in [("sta-names.json","import_json_sha256"),("sta-canonical.v","sta_netlist_sha256"),("instance-binding.json","instance_binding_sha256")]:
            if sha(directory/filename)!=binding[key]:raise ValueError("canonical identity")
        graph=json.loads((directory/"sta-names.json").read_text())["modules"][ms["top"]]
        graph=bind(graph,design,json.loads((directory/"instance-binding.json").read_text()))
        if Counter(c["type"] for c in graph["cells"].values())!=Counter(c["type"] for c in design["cells"].values()):raise ValueError("canonical changed cells")
        if topology(design)!=binding["topology_sha256"] or topology(graph,True)!=binding["topology_sha256"]:raise ValueError("canonical changed connectivity")
    for p in validate_profiles(s):
        d=directory/p["profile"];validate_log((d/"sta.log").read_text())
        tcl=(d/"timing.tcl").read_text()
        validate_tcl(tcl,p,s["boundary"])

        if sha(d/"sta.log")!=p["log_sha256"]:raise ValueError("STA log identity")
        run=json.loads((d/"run.json").read_text())
        if type(run.get("exit_code")) is not int or run["exit_code"]!=0:raise ValueError("real tool exit")
        expected_reports=required_paths(s["boundary"])|{"setup-checks"}
        if {x.stem for x in d.glob("*.rpt")}!=expected_reports:raise ValueError("timing report file inventory")
        for k,v in p["paths"].items():
            if parse_path((d/(k+".rpt")).read_text())!=v or not v["exists"]:raise ValueError("path mismatch")
        if constant_warnings((d/"setup-checks.rpt").read_text(),graph if s["boundary"]=="parent" else design,["testEnable"] if s["boundary"]=="parent" else [])!=p.get("reviewed_unconstrained_endpoints",p.get("constant_unconstrained_outputs")):raise ValueError("constraint coverage mismatch")
    return s
def register_groups(structure,mode):
    mn="VDot" if mode=="o1" else "VDotElastic"
    m=structure["modules"][mn]
    q={b for c in m["cells"].values() if c["type"]=="$dff" for b in c["connections"]["Q"]}
    patterns={"products":r"productsReg_|pProducts_","result":r"resultReg$|rPacket_res_data$","stage_state":r"state$|[pr]Valid$"}
    if mode=="o1":patterns.update(control=r"io_out_bits_ctrl_|savedVecWen$|savedV0Wen$|illegalReg$",perf=r"io_out_bits_perfDebugInfo_")
    else:patterns.update(p_control=r"pCtrl_",p_perf=r"pPerf_",r_control=r"rPacket_ctrl_",r_perf=r"rPacket_perfDebugInfo_")
    used=set();counts={}
    for group,pattern in patterns.items():
        bits={b for n,net in m["netnames"].items() if re.match(pattern,n) for b in net["bits"]}&q
        if bits&used:raise ValueError("register group overlap")
        used|=bits;counts[group]=len(bits)
    if used!=q:raise ValueError(f"unclassified registers {len(q-used)}")
    return {"total_bits":len(q),"groups":counts}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("work",type=Path);a=p.parse_args()
    work=a.work;lib=work/"library/NangateOpenCellLibrary_typical.lib"
    selection={"o1-fu":("o1-fu-map-02","o1-fu-sta-03"),"o2-fu":("o2-fu-map-01","o2-fu-sta-02"),"o1-parent":("o1-parent-map-01","o1-parent-sta-08"),"o2-parent":("o2-parent-map-01","o2-parent-sta-01")}
    result={}
    for key,(mapped,timed) in selection.items():
        s,m=mapping_audit(work/mapped,lib)
        if key!=s["mode"]+"-"+s["boundary"] or s["exit_code"]!=0:raise ValueError("missing/wrong mode or nonzero mapping")
        generation=work/Path(s["generation"]).name
        g=json.loads((generation/"result.json").read_text())
        if sha(generation/"result.json")!=s["generation_sha256"] or g["mode"]!=s["mode"] or g["boundary"]!=s["boundary"] or type(g.get("exit_code")) is not int or g["exit_code"]!=0:raise ValueError("generation/mapping binding")
        if not re.fullmatch(r"[0-9a-f]{40}",g.get("source_commit","")):raise ValueError("missing generation source commit")
        if g.get("verification_error") or ("source_inputs" in g and g.get("source_inputs_unchanged") is not True):raise ValueError("generation source verification failed")
        expected={"VDOT_T14_FUSED_INPUT":"1","VDOT_O1_HANDOFF":"1" if s["mode"]=="o1" else "0","VDOT_O2_ELASTIC":"1" if s["mode"]=="o2" else "0",**{x:"0" for x in ["VDOT_T12_TRACE","VDOT_T13_TRACE","VDOT_O1_TRACE","VDOT_O2_TRACE"]}}
        if g["flags"]!=expected:raise ValueError("mode/trace flags")
        verify_rtl(generation,g)
        if sha(work/mapped/"map.ys")!=s["map_script_sha256"]:raise ValueError("mapping script changed")
        t=timing_audit(work/timed,work/mapped,m)
        result[key]={"mapping":s,"timing":t}
        if key.endswith("-fu"):result[key]["registers"]=register_groups(json.loads((work/mapped/"structure.json").read_text()),s["mode"])
    for boundary in ["fu","parent"]:
        compare_interfaces(result["o1-"+boundary]["mapping"]["ports"],result["o2-"+boundary]["mapping"]["ports"])
    leaf_identity={}
    for leaf in ["VDotProducts.sv","VDotReduce.sv"]:
        module=leaf[:-3]
        variants={}
        for generation in ["o1-fu-02","o2-fu-01","o1-parent-01","o2-parent-01"]:
            path=work/generation/"rtl"/leaf
            text=path.read_text()
            body=text[text.index("module "+module):]
            variants[generation]={"raw_sha256":sha(path),"module_body_sha256":hashlib.sha256(body.encode()).hexdigest()}
        if variants["o1-fu-02"]["raw_sha256"]!=variants["o2-fu-01"]["raw_sha256"] or variants["o1-parent-01"]["raw_sha256"]!=variants["o2-parent-01"]["raw_sha256"]:raise ValueError("arithmetic differs between modes at same boundary")
        if len({v["module_body_sha256"] for v in variants.values()})!=1:raise ValueError("arithmetic module body differs across boundaries")
        leaf_identity[leaf]=variants
    final={"audit_pass":True,"results":result,"selection":selection,"not_signoff":True,"arithmetic_identity":leaf_identity}
    (work/"assessment.json").write_text(json.dumps(final,indent=2)+"\n")
    print("O4_OFFLINE_AUDIT_PASS")
