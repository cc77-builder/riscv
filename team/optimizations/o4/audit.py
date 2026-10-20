#!/usr/bin/env python3
"""Offline audits from raw mapped/STA files; no simulator or synthesis invocation."""
import hashlib, json, math, re
from collections import Counter
from pathlib import Path
from synthesize import library_areas
from timing import parse_path, validate_log, constant_warnings
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compare_interfaces(a,b):
    if a!=b:raise ValueError("O1/O2 interface mismatch")
def mapping_audit(directory,lib):
    s=json.loads((directory/"summary.json").read_text())
    if not s["pass"] or sha(lib)!=s["library_sha256"]:raise ValueError("mapping/library identity")
    if sha(directory/"mapped.v")!=s["mapped_sha256"] or sha(directory/"mapped.json")!=s["mapped_json_sha256"]:raise ValueError("mapped identity")
    m=json.loads((directory/"mapped.json").read_text())["modules"][s["top"]]
    counts=Counter(c["type"] for c in m["cells"].values());areas=library_areas(lib)
    if set(counts)-set(areas):raise ValueError("unmapped cells")
    area=sum(counts[k]*areas[k] for k in counts)
    if dict(sorted(counts.items()))!=s["cell_histogram"] or not math.isclose(area,s["cell_area_sum"],abs_tol=1e-7):raise ValueError("area/histogram")
    independent=re.findall(r"Chip area for module.*?:\s*([0-9.]+)",(directory/"synthesis.log").read_text())
    if not independent or abs(float(independent[-1])-area)>0.02:raise ValueError("area/log disagree")
    return s,m
def timing_audit(directory,mapping,design):
    s=json.loads((directory/"summary.json").read_text())
    if not s["pass"] or s["mapping_summary_sha256"]!=sha(mapping/"summary.json"):raise ValueError("STA identity")
    ms=json.loads((mapping/"summary.json").read_text())
    if s["library_sha256"]!=ms["library_sha256"] or s["mapped_sha256"]!=ms["mapped_sha256"]:raise ValueError("STA library/netlist binding")
    if s["boundary"]=="parent":
        from compact import topology
        from canonical import bind,emit
        binding=json.loads((directory/"canonical-binding.json").read_text())
        if binding!=s["name_binding"] or binding["exit_code"]!=0 or binding["input_mapping_json_sha256"]!=sha(mapping/"mapped.json"):raise ValueError("name binding")
        for filename,key in [("sta-names.json","import_json_sha256"),("sta-canonical.v","sta_netlist_sha256"),("instance-binding.json","instance_binding_sha256")]:
            if sha(directory/filename)!=binding[key]:raise ValueError("canonical identity")
        graph=json.loads((directory/"sta-names.json").read_text())["modules"][ms["top"]]
        graph=bind(graph,design,json.loads((directory/"instance-binding.json").read_text()))
        if Counter(c["type"] for c in graph["cells"].values())!=Counter(c["type"] for c in design["cells"].values()):raise ValueError("canonical changed cells")
        if topology(design)!=binding["topology_sha256"] or topology(graph,True)!=binding["topology_sha256"]:raise ValueError("canonical changed connectivity")
    expected={"nominal":(1,5),"period050":(.5,5),"period200":(2,5),"load001":(1,1),"load020":(1,20)}
    if set(p["profile"] for p in s["profiles"])!=set(expected) or len(s["profiles"])!=5:raise ValueError("missing/duplicate sensitivity")
    for p in s["profiles"]:
        if (p["period_ns"],p["load_ff"])!=expected[p["profile"]]:raise ValueError("constraint mismatch")
        d=directory/p["profile"];validate_log((d/"sta.log").read_text())
        tcl=(d/"timing.tcl").read_text()
        fixed=["set_cmd_units -time ns -capacitance fF","set_wire_load_mode top","set_wire_load_model -name 5K_hvratio_1_1","set_clock_uncertainty 0.05 [get_clocks core_clk]","set_clock_transition 0.05 [get_clocks core_clk]","set_input_delay -max 0.1 -clock core_clk $inputs","set_output_delay -max 0.1 -clock core_clk $outputs","set_input_transition 0.05 $inputs",f"set_load {p['load_ff']} $outputs"]
        if any(tcl.splitlines().count(x)!=1 for x in fixed):raise ValueError("actual Tcl constraints differ")
        clock=re.findall(r"^create_clock -name core_clk -period ([0-9.]+) ",tcl,re.M)
        if len(clock)!=1 or float(clock[0])!=p["period_ns"] or "set_false_path" in tcl:raise ValueError("clock/path constraints differ")
        if s["boundary"]=="parent" and "set_case_analysis 0 [get_ports testEnable]" not in tcl:raise ValueError("missing functional testEnable case")

        if sha(d/"sta.log")!=p["log_sha256"]:raise ValueError("STA log identity")
        if json.loads((d/"run.json").read_text())["exit_code"]!=0:raise ValueError("real tool exit")
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
        s,m=mapping_audit(work/mapped,lib); t=timing_audit(work/timed,work/mapped,m)
        result[key]={"mapping":s,"timing":t}
        if key.endswith("-fu"):result[key]["registers"]=register_groups(json.loads((work/mapped/"structure.json").read_text()),s["mode"])
    for boundary in ["fu","parent"]:
        compare_interfaces(result["o1-"+boundary]["mapping"]["ports"],result["o2-"+boundary]["mapping"]["ports"])
    for leaf in ["VDotProducts.sv","VDotReduce.sv"]:
        h=sha(work/"o1-fu-02/rtl"/leaf)
        for generation in ["o2-fu-01","o1-parent-01","o2-parent-01"]:
            if sha(work/generation/"rtl"/leaf)!=h:raise ValueError("arithmetic leaf differs")
    final={"audit_pass":True,"results":result,"selection":selection,"not_signoff":True}
    (work/"assessment.json").write_text(json.dumps(final,indent=2)+"\n")
    print("O4_OFFLINE_AUDIT_PASS")
