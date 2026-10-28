"""C1 screening against the predeclared area/timing thresholds."""
import argparse,hashlib,importlib.util,json,re,subprocess,sys,datetime
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
def need(x,m):
    if not x:raise ValueError(m)
def stamp():return datetime.datetime.now().astimezone().isoformat()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--work",required=True,type=Path)
    p.add_argument("--baseline",required=True,type=Path)
    p.add_argument("--source-repo",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    need(not a.output.exists(),"new output required");a.output.mkdir()
    mod=a.source_repo/"team/optimizations/o2/r3-div-gate/timing-review/review.py"
    spec=importlib.util.spec_from_file_location("prior_review",mod);review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
    tool=Path("/home/riscv/riscv-lab/o4-cost-20261020")
    sta=tool/"tools/root/usr/bin/sta"
    sealed=a.source_repo/"team/optimizations/o2/r3-div-gate/evidence/20261025-performance-cost/manifest.json"
    need(sha(sealed)=="9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77","original archive changed")
    original={x["path"]:x["raw_sha256"] for x in json.loads(sealed.read_text())["files"]}
    pins={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),str(mod):sha(mod),str(sealed):sha(sealed)}
    tools=json.loads((tool/"tools/executable-identities.json").read_text())
    for name,x in tools.items():
        path=tool/"tools/root/usr/bin"/name
        need(sha(path)==x["sha256"],"tool changed");pins[str(path)]=x["sha256"];pins.update(x["shared_library_sha256"])
    lib=tool/"library/NangateOpenCellLibrary_typical.lib";pins[str(lib)]=sha(lib)
    snapshots={}
    for version,root in [("before",a.baseline),("after",a.work)]:
        for folder in ["parent-map-01","parent-sta-01","parent-cost-01"]:
            for f in (root/folder).rglob("*"):
                if f.is_file():
                    h=sha(f);pins[str(f)]=h
                    if version=="before":need(original["cost/"+f.relative_to(root).as_posix()]==h,"baseline archive mismatch "+str(f))
        snapshots[version]=dict(mapping=json.loads((root/"parent-map-01/summary.json").read_text()),
                                timing=json.loads((root/"parent-sta-01/summary.json").read_text()))
    expected_profiles=["nominal","period050","period200","load001","load020"]
    for snapshot in snapshots.values():
        need(snapshot["mapping"]["pass"] and snapshot["timing"]["pass"],"incomplete PPA receipt")
        need([x["profile"] for x in snapshot["timing"]["profiles"]]==expected_profiles,"missing/reordered STA profiles")
    save(a.output/"inputs.json",pins)
    def unchanged():
        for path,h in pins.items():need(sha(Path(path))==h,"input changed "+path)
    unchanged()
    need(json.loads((a.work/"campaign-02.json").read_text())["status"]=="LOCAL_AND_STANDARD_PPA_COMPLETE_AWAIT_SCREEN","local pipeline incomplete")
    local= json.loads((a.work/"parent-replay.json").read_text())
    need(local["status"]=="O2_PARENT_OFFLINE_TRACE_PASS","parent replay failed")
    for stage in ("fu-02","parent-01"):
        need(json.loads((a.work/stage/"runner.status.json").read_text())["passed"],"local failed")
    state=dict(status="running",started=stamp(),steps=[])
    save(a.output/"state.json",state)
    targeted={}
    try:
        for version,root in [("before",a.baseline),("after",a.work)]:
            d=review.Design(root)
            semantics=["dut.elasticDivOccupied_divBusy"]+(
                ["dut.uncer_en_reg","dut.uncer_en_reg_1"] if version=="before" else ["dut.elasticDivOccupied_divOwnerIsFp"])
            regpins={}
            for semantic in semantics:
                cell,pin=d.drivers[d.net_bit(semantic)]
                need(pin in ("Q","QN") and d.mapping["cells"][cell]["type"].startswith("DFF"),"state must map to DFF "+semantic)
                regpins[semantic]=d.reverse[cell]+"/D"
            if version=="after":
                for old in ["dut.uncer_en_reg","dut.uncer_en_reg_1"]:
                    if old in d.mapping["netnames"]:
                        bit=d.net_bit(old);cell,pin=d.drivers[bit]
                        need(not d.mapping["cells"][cell]["type"].startswith("DFF"),"old hold DFF retained")
            save(a.output/(version+"-state-registers.json"),regpins)
            targeted[version]={}
            for profile in snapshots[version]["timing"]["profiles"]:
                name=profile["profile"];out=a.output/version/name;out.mkdir(parents=True)
                old=(d.sta/name/"timing.tcl").read_text().splitlines()
                tcl=old[:next(i for i,l in enumerate(old) if l.startswith("check_setup "))]
                queries={}
                for i,(semantic,pin) in enumerate(regpins.items()):
                    queries["state"+str(i)]=(f"-to [get_pins {{{pin}}}]",semantic)
                for i in range(3):
                    c="dut.ClockGate"+("_"+str(i) if i else "")+".impl"
                    queries["icg"+str(i)]=(f"-to [get_pins {{{d.reverse[c]}/E}}]",c)
                for key,(sel,_) in queries.items():
                    tcl.append(f"report_checks {sel} -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {{capacitance slew input_pin net}} -digits 6 -no_line_splits > {out/(key+'.rpt')}")
                tcl+=['puts "C1_CONTROL_STA_COMPLETE"',"exit"]
                (out/"timing.tcl").write_text("\n".join(tcl)+"\n")
                save(out/"queries.json",queries)
                cmd=[str(sta),"-no_init","-exit",str(out/"timing.tcl")]
                rec=dict(version=version,profile=name,command=cmd,started=stamp(),status="running")
                state["steps"].append(rec);save(a.output/"state.json",state)
                print("START",version,name,flush=True)
                with (out/"sta.log").open("xb") as log:
                    rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
                rec.update(exit_code=rc,finished=stamp(),status="passed" if rc==0 else "failed");save(out/"run.json",rec)
                log=(out/"sta.log").read_text()
                need(rc==0 and "C1_CONTROL_STA_COMPLETE" in log and not re.search(r"(?im)^Error|not found",log),"targeted STA error")
                paths={k:d.parse(out/(k+".rpt")) for k in queries}
                save(out/"paths.json",paths)
                targeted[version][name]=paths
                save(a.output/"state.json",state)
                print("PASS",version,name,flush=True)
        before,after=snapshots["before"],snapshots["after"]
        need(before["mapping"]["ports"]==after["mapping"]["ports"],"boundary ports changed")
        need(before["mapping"]["library_sha256"]==after["mapping"]["library_sha256"]==sha(lib),"library mismatch")
        need(not after["mapping"]["unknown_cells"],"unknown cells")
        need(after["mapping"]["cell_histogram"]["CLKGATETST_X1"]==3,"gate count")
        failures=[];metrics=[]
        area_before=before["mapping"]["cell_area_sum"];area_after=after["mapping"]["cell_area_sum"]
        if area_after>area_before*1.001:failures.append("area exceeds +0.1%")
        need(abs(area_before-284614.946)<0.00001,"baseline area mismatch")
        monitored=("r2r","i2r","vdot_r2r","vdot_i2r","vdot_r2o","ready")
        for bp,ap in zip(before["timing"]["profiles"],after["timing"]["profiles"]):
            need((bp["profile"],bp["period_ns"],bp["load_ff"])==(ap["profile"],ap["period_ns"],ap["load_ff"]),"profile mismatch")
            name=bp["profile"]
            for kind in monitored:
                x,y=bp["paths"][kind],ap["paths"][kind]
                delta=(y["arrival_ns"]/x["arrival_ns"]-1)*100
                ok=y["arrival_ns"]<=x["arrival_ns"]*1.01
                metrics.append(dict(profile=name,path=kind,before=x,after=y,delta_percent=delta,pass_=ok))
                if not ok:failures.append(f"{name}/{kind} exceeds +1% ({delta:.6f}%)")
            for i in range(3):
                kind="icg"+str(i);x,y=targeted["before"][name][kind],targeted["after"][name][kind]
                ok=y["arrival_ns"]<=x["arrival_ns"]*1.01 and (x["slack_ns"]<0 or y["slack_ns"]>=0)
                metrics.append(dict(profile=name,path=kind,before={k:x[k] for k in ["arrival_ns","slack_ns","startpoint","endpoint"]},
                         after={k:y[k] for k in ["arrival_ns","slack_ns","startpoint","endpoint"]},
                         delta_percent=(y["arrival_ns"]/x["arrival_ns"]-1)*100,pass_=ok))
                if not ok:failures.append(f"{name}/{kind} violates +1%/positive-slack gate")
        control=max(x["arrival_ns"] for n,x in targeted["after"]["nominal"].items() if n.startswith("state"))
        baseline_control=max(x["arrival_ns"] for n,x in targeted["before"]["nominal"].items() if n.startswith("state"))
        need(abs(baseline_control-1.930584)<1e-6,"baseline control reproduction differs")
        if control>1.737526:failures.append(f"control-state worst {control:.6f} > 1.737526ns")
        unchanged()
        result=dict(status="C1_SCREEN_PASS" if not failures else "C1_SCREEN_REJECT",
            area_before=area_before,area_after=area_after,area_delta_percent=(area_after/area_before-1)*100,
            control_before_ns=baseline_control,control_after_ns=control,control_delta_percent=(control/baseline_control-1)*100,
            failures=failures,comparisons=metrics,inputs_unchanged=True,fullcore_authorized_by_gate=not failures,
            disclaimer="Tool success is separate from screening; no fullcore/EMU run by this script.")
        save(a.output/"result.json",result)
        state.update(status=result["status"],finished=stamp());save(a.output/"state.json",state)
        print(json.dumps({k:v for k,v in result.items() if k!="comparisons"},indent=2),flush=True)
    except BaseException as e:
        state.update(status="failed",error=repr(e),finished=stamp());save(a.output/"state.json",state);raise
if __name__=="__main__":main()
