"""Offline independently rerun immutable semantic checks for the selected 13+1 evidence."""
import argparse, importlib.util, json, sys
from pathlib import Path
import clock_supplement as c

def audit(args):
    root, out, old, source=args.run,args.output,args.old,args.source
    c.require(not out.exists(),"fresh audit directory")
    state=c.read(root/"state.json");saved=c.read(root/"results.json")
    c.require(state["status"]==saved["status"]=="R5_G5_COMPOSITE_FULLCORE_PASS","composite unfinished")
    c.require(state["controller_sha256"]==c.sha(Path(__file__).with_name("clock_supplement.py"))
              and state["contract_sha256"]==c.sha(Path(__file__).with_name("CONTRACT.md")),"controller/contract drift")
    c.require(saved["new_emu_runs"]==1 and saved["reused_execution_verdicts"]==13 and saved["fresh_14_campaign"] is False,
              "execution provenance differs")
    c.require({p.name for p in (root/"runs").iterdir()}=={c.REPLACEMENT},"new process inventory")
    sys.path.insert(0,str(args.adapter))
    import current_clean_fullcore as adapter
    identity=c.read(root/"identity.json")
    fc=adapter.configure(source,identity);ctx=fc.bind(source,identity,physical=True)
    fc.prepare(ctx,None,old/"negative-fixture")
    c.require(ctx.inputs==c.read(root/"runtime-inputs.json")==c.read(old/"runtime-inputs.json"),"input closure")
    fc.ce.a.frozen_m.verify_files(ctx.inputs)
    out.mkdir(parents=True)
    old_audit=out/"old";new_audit=out/"new";old_audit.mkdir();new_audit.mkdir()
    rows=[];raws=[]
    for name,image,data,reference in ctx.jobs.values():
        fresh=name==c.REPLACEMENT
        campaign=(root if fresh else old)/"runs"
        directory=campaign/name
        raw=c.read(directory/"result.json")
        c.binding(c.read(directory/"runtime.json"),raw)
        origin=saved["origins"][name]
        c.require(origin==dict(kind="NEW_EXECUTION" if fresh else "REUSED_RAW_RECHECKED",
                              path=str(directory),result_sha256=c.sha(directory/"result.json")),"origin changed")
        row=fc.evaluate(ctx,name,image,data,reference,raw,campaign,new_audit if fresh else old_audit)
        c.require(all(row.get(k)==raw.get(k) for k in fc.SEMANTIC if k in row),"raw semantics")
        rows.append(row);raws.append(raw)
    proof=fc.aggregate(ctx,rows,raws)
    for key in ("suite_coverage","normal_reference_recovery","matrix_unique","matrix_executed",
                "selected_jobs","emu_sha256","reference_sha256","negative_sha256"):
        c.require(proof[key]==saved[key],"aggregate differs: "+key)
    byname={r["name"]:r for r in saved["records"]}
    c.require(set(byname)==set(ctx.jobs),"cached record inventory")
    for row in rows:
        c.require(all(row.get(k)==byname[row["name"]].get(k) for k in fc.SEMANTIC if k in row),"cached row differs")
    c.require(c.capacity(raws,3)==saved["selected_utc_capacity"],"UTC proof differs")
    clock=c.read(root/"runs"/c.REPLACEMENT/"clock.json")
    raw=next(r for r in raws if r["name"]==c.REPLACEMENT)
    check=c.clock_check(clock,raw)
    c.require(check==saved["new_phase_clock"]==c.read(root/"clock-audit.json"),"monotonic proof differs")
    original=[c.read(old/"runs"/n/"result.json") for n in ctx.jobs]
    c.require(c.capacity(original,3)["status"]=="FAIL","old failure not retained")
    fc.ce.a.frozen_m.verify_files(ctx.inputs)
    result=dict(status="R5_G5_COMPOSITE_RAW_AUDIT_PASS",source_new_emu_runs=1,new_emu_runs=0,
        selected_runs=14,reused_old_runs=13,original_campaign_wall_clock="FAIL_PRESERVED",
        selected_utc_capacity=saved["selected_utc_capacity"],new_phase_clock=check,
        hardware_identity_sha256=c.sha(root/"identity.json"),source_result_sha256=c.sha(root/"results.json"),
        suite_coverage=proof["suite_coverage"],performance_measured=False)
    c.save(out/"results.json",result);print(json.dumps(result))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("run","output","old","source","adapter"):p.add_argument("--"+key,type=Path,required=True)
    audit(p.parse_args())
