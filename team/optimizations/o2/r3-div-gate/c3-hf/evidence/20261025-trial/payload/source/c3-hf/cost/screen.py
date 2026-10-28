"""C3_HF screening: unchanged C1 thresholds, new frozen C3_HF local qualification.

This driver runs targeted OpenSTA only after the standard synthesis/five-profile
campaign completed. It never builds/runs the full core. Derived from C1 screen.py.
"""
import argparse,hashlib,importlib.util,json,re,subprocess,sys,datetime,gzip,math
from pathlib import Path
from qualification import validate
from control_contract import bind_states

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
    p.add_argument("--qualification",required=True,type=Path)
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
    qualification=validate(a.qualification,pins)
    head=qualification["candidate"]["head"]
    repo=Path(qualification["candidate"]["repo"])
    campaign=json.loads((a.work/"campaign.json").read_text())
    need(campaign.get("candidate_commit")==head and campaign.get("qualification_sha256")==sha(a.qualification),
         "standard cost campaign not bound to local qualification")
    generation=json.loads((a.work/"parent-cost-01/result.json").read_text())
    need(generation["source_commit"]==head and generation["mode"]=="o2" and generation["boundary"]=="parent",
         "wrong generated candidate")
    # Same mapping knobs and constraints; output paths are the only permitted
    # script differences here. No false path, relaxed uncertainty or TE case.
    def normal_map(root):
        return (root/"parent-map-01/map.ys").read_text().replace(str(root),"<WORK>")
    need(normal_map(a.baseline)==normal_map(a.work),"mapping command/RTL filename set differs")
    need((a.baseline/"parent-map-01/abc.constr").read_bytes()==(a.work/"parent-map-01/abc.constr").read_bytes(),"ABC constraints differ")
    def constraints(root,profile):
        lines=(root/"parent-sta-01"/profile/"timing.tcl").read_text().splitlines()
        return "\\n".join(lines[:next(i for i,l in enumerate(lines) if l.startswith("check_setup "))]).replace(str(root),"<WORK>")
    for profile in expected_profiles:
        need(constraints(a.baseline,profile)==constraints(a.work,profile),"standard STA constraints differ "+profile)
    save(a.output/"inputs.json",pins)
    def unchanged():
        for path,h in pins.items():need(sha(Path(path))==h,"input changed "+path)
    unchanged()
    need(json.loads((a.work/"campaign.json").read_text())["status"]=="C3_HF_STANDARD_PPA_COMPLETE_AWAIT_SCREEN","C3_HF standard PPA incomplete")
    state=dict(status="running",started=stamp(),steps=[])
    save(a.output/"state.json",state)
    targeted={}
    try:
        for version,root in [("before",a.baseline),("after",a.work)]:
            d=review.Design(root)
            regpins=bind_states(d)
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
                tcl+=['puts "C3_HF_CONTROL_STA_COMPLETE"',"exit"]
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
                need(rc==0 and "C3_HF_CONTROL_STA_COMPLETE" in log and not re.search(r"(?im)^Error|not found",log),"targeted STA error")
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
        for label,expected in [("state0",0.870094),("state1",1.930584),("state2",1.506153)]:
            need(abs(targeted["before"]["nominal"][label]["arrival_ns"]-expected)<1e-6,
                 "baseline state reproduction differs "+label)
        if control>1.737526:failures.append(f"control-state worst {control:.6f} > 1.737526ns")
        need(len(metrics)==45 and len({(m["profile"],m["path"]) for m in metrics})==45,"incomplete or duplicated 45-path screening")
        need(all(math.isfinite(m[side][k]) for m in metrics for side in ["before","after"] for k in ["arrival_ns","slack_ns"]),"non-finite timing metric")
        need(math.isfinite(control) and math.isfinite(area_after),"non-finite state or area")
        need(all(math.isfinite(path[key]) for version in targeted.values() for profile in version.values()
                 for path in profile.values() for key in ["arrival_ns","slack_ns"]),"non-finite targeted observation")
        need(all(set(paths)=={"state0","state1","state2","icg0","icg1","icg2"}
                 for version in targeted.values() for paths in version.values()),"missing/extra targeted state query")
        unchanged()
        result=dict(status="C3_HF_SCREEN_PASS" if not failures else "C3_HF_SCREEN_REJECT",
            candidate_head=head,local_qualification_sha256=sha(a.qualification),baseline_manifest_sha256=sha(sealed),
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
