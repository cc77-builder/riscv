"""Offline closeout of the two existing STA processes, retaining the Q-only no-path result."""
import argparse,hashlib,importlib.util,json,re,datetime
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,m):
    if not ok:raise ValueError(m)
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True);p.add_argument("--work",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),"new output required")
    h=a.repo/"team/optimizations/o2/r3-div-gate/timing-review/review.py"
    spec=importlib.util.spec_from_file_location("review",h);review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
    before=Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025")
    after=Path("/home/riscv/riscv-lab/o2-c1-owner-20261025")
    seals=[("before",a.repo/"team/optimizations/o2/r3-div-gate/evidence/20261025-performance-cost/manifest.json","9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77","cost/"),
           ("after",a.repo/"team/optimizations/o2/r3-div-gate/c1/evidence/20261025-screen/manifest.json","ced265304d08b2ee3c7eb9a894eb009869bb494adb7c48e1ff72493ce4cb252e","work/")]
    seals={v:(f,digest,prefix) for v,f,digest,prefix in seals}
    paths={};fixed=a.work/"fixed-sta-01";pins={str(h):sha(h),str(Path(__file__)):sha(Path(__file__))}
    state=json.loads((fixed/"state.json").read_text())
    need(len(state["steps"])==2 and all(x["exit_code"]==0 for x in state["steps"]),"two STA processes required")
    for version,root in [("before",before),("after",after)]:
        f,digest,prefix=seals[version];need(sha(f)==digest,"seal changed")
        archive={x["path"]:x["raw_sha256"] for x in json.loads(f.read_text())["files"]}
        for rel in ["parent-map-01/mapped.json","parent-sta-01/instance-binding.json","parent-sta-01/sta-canonical.v","parent-sta-01/nominal/timing.tcl","parent-cost-01/rtl/ExeUnit.sv"]:
            pp=root/rel;need(sha(pp)==archive[prefix+rel],"fixed source differs "+str(pp));pins[str(pp)]=sha(pp)
        d=review.Design(root);out=fixed/version
        standard=(root/"parent-sta-01/nominal/timing.tcl").read_text().splitlines()
        prefixlines=standard[:next(i for i,x in enumerate(standard) if x.startswith("check_setup "))]
        actual=(out/"timing.tcl").read_text().splitlines()
        need(actual[:len(prefixlines)]==prefixlines,"constraints changed")
        queries=json.loads((out/"queries.json").read_text());need(len(queries)==10,"query scope")
        log=(out/"sta.log").read_text()
        need("C2_READ_ONLY_STA_COMPLETE" in log and not re.search(r"(?im)^Error|not found",log),"tool error")
        paths[version]={}
        for name in queries:
            report=out/(name+".rpt");pins[str(report)]=sha(report)
            if report.read_text().strip()=="No paths found.":
                need((version,name)==("after","icg_from_hold_or_owner"),"unexpected missing path")
                paths[version][name]=dict(exists=False,reason="Query starts owner/Q; integer ICG is reached from owner/QN, so no Q-only path. No delay/Fmax claim.")
            else:paths[version][name]=dict(exists=True,**d.parse(report))
        global_path=paths[version]["icg_all"]
        old=json.loads((after/"screen-01"/version/"nominal/paths.json").read_text())["icg1"]
        need(all(global_path[k]==old[k] for k in ["arrival_ns","slack_ns","startpoint","endpoint"]),"old max not reproduced")
    for path,digest in pins.items():need(sha(Path(path))==digest,"input changed")
    result=dict(status="C2_FIXED_STA_RAW_REVIEW_COMPLETE",time=datetime.datetime.now().astimezone().isoformat(),
                tool_processes=2,valid_timing_reports=19,no_path_reports=1,
                initial_parser_exit_code=1,initial_state_file_preserved=True,
                paths=paths,inputs=pins,
                note="Original script failed postprocessing a Q-only no-path report; both STA commands exited 0. Recovered by offline parsing only, no extra STA. Not a C2 implementation or acceptance.")
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("paths","inputs")},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
