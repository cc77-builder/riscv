#!/usr/bin/env python3
"""Read-only C2 final evidence audit. No build, simulator, EDA, or GitHub call."""
import argparse, datetime, hashlib, importlib.util, json, re, subprocess, sys
from pathlib import Path

HEAD="6704ce3502a7235cdb81697638c01ed23f6914f6"
BASE="0f12df675378556670afd0dd2153f47fcb330610"
EXU="src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
SHA="febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6"
pins={}
def need(x,m):
    if not x: raise ValueError(m)
def read(p):
    p=Path(p);b=p.read_bytes()
    digest=hashlib.sha256(b).hexdigest()
    need(str(p) not in pins or pins[str(p)]==digest,"input changed while auditing "+str(p))
    pins[str(p)]=digest
    return b
def js(p):return json.loads(read(p))
def sha(p):read(p);return pins[str(p)]
def text(p):return read(p).decode()
def module(name,p):
    sha(p)
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def git(repo,*args):
    p=subprocess.run(["git",*args],cwd=repo,capture_output=True,text=True)
    need(p.returncode==0,"git read failed "+str(args));return p.stdout
def fields(line):return {k:int(v) for k,v in re.findall(r"(\w+)=(\d+)",line)}
def summary(log,prefix):
    rows=[x for x in log.splitlines() if x.startswith(prefix)]
    need(len(rows)==1,"missing/duplicate PASS "+prefix);return fields(rows[0])
def run(argv,out,log):
    p=subprocess.run(argv,text=True,capture_output=True)
    (out/log).write_text(p.stdout+p.stderr)
    need(p.returncode==0,"offline checker failed "+str(argv))
    return dict(command=argv,exit_code=p.returncode,log=log)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--work",type=Path,required=True)
    ap.add_argument("--baseline-repo",type=Path,required=True);ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args();w=a.work.resolve();repo=w/"repo";base=a.baseline_repo.resolve();out=a.output_dir.resolve()
    out.mkdir(parents=True,exist_ok=True);need(not(out/"audit.json").exists(),"fresh output required")
    cp=base/"team/optimizations/o2/r3-div-gate/c2/parent"
    parent=repo/"team/optimizations/o2/parent"
    need(git(repo,"rev-parse","HEAD").strip()==HEAD,"candidate commit drift")
    need(not git(repo,"diff","HEAD","--","src").strip(),"candidate production dirty")
    need(sha(repo/EXU)==SHA,"candidate ExeUnit drift")
    need(git(base,"rev-parse","HEAD").strip()==BASE,"retained source HEAD drift")
    need(not git(base,"diff","HEAD","--","src").strip(),"retained production dirty")
    changed=git(repo,"diff","--name-only",BASE,HEAD,"--","src").splitlines()
    need(changed==[EXU],"production diff scope")
    sys.path.insert(0,str(parent))
    pneg=module("audit_parent_negative",parent/"check_negative.py")
    fneg=module("audit_fu_negative",repo/"team/optimizations/o2/check_negative_fu.py")
    campaigns={};source_maps={}
    for stage,expected in [("fu-02",4),("parent-01",16),("supplement-01",0)]:
        d=w/stage
        need(js(d/"runner.status.json")["passed"],"runner not passed")
        need(text(d/"source-commit.log").strip()==HEAD,"run commit wrong")
        need(text(d/"source-after.status").strip()=="SOURCE_AND_DEPENDENCIES_UNCHANGED","source-after missing")
        sources=js(d/"source.json");source_maps[stage]=sources
        for name,digest in sources.items():
            need(sha(repo/name)==digest,"source hash "+name)
        ng=na=0
        for manifest in ["generated-files.json","artifacts.json"]:
            rows=js(d/manifest)
            for row in rows:
                path=d/row["path"]
                need(sha(path)==row["sha256"] and path.stat().st_size==row["bytes"],"artifact drift "+str(path))
            if manifest=="generated-files.json":ng=len(rows)
            else:na=len(rows)
        cmds=js(d/"commands.json");bad=[];neg=[]
        for c in cmds:
            need((d/c["log"]).is_file(),"command log missing")
            sha(d/c["log"])
            if c["exit_code"]!=0:
                need(c["exit_code"]==1 and c["log"].startswith("inject-"),"unexpected command failure")
                fault=c["log"][7:-4];bad.append(fault)
                checks=[x for x in cmds if x["log"]=="check-"+fault+".log"]
                need(len(checks)==1 and checks[0]["exit_code"]==0,"negative check receipt")
                (fneg.check if stage=="fu-02" else pneg.check_negative)(fault,1,text(d/c["log"]))
                neg.append(dict(fault=fault,expected_rejection_exit=1,checker_exit=0))
        need(len(bad)==expected,"negative count")
        compiler=[c for c in cmds if c["log"]=="verilator.log"]
        need(len(compiler)==1 and "--assert" in compiler[0]["command"],"assertions disabled")
        need(len([c for c in cmds if c["log"]=="result.log" and c["exit_code"]==0])==1,"normal execution receipt")
        env=js(d/"run.env.json")
        need(env["VDOT_O2_ELASTIC"]=="1" and env["VDOT_O1_HANDOFF"]=="0","wrong mode")
        deps=js(d/"dependencies.json")
        need(all(x["pin"]==x["head"] and not x["status"] for x in deps),"dependency receipt dirty")
        campaigns[stage]=dict(commands=len(cmds),source_hash_checks=len(sources),generated_hash_checks=ng,
            artifact_hash_checks=na,negative_controls=neg,dependency_pins=len(deps))
    # Independently recheck every recorded dependency commit and present tracked changes.
    dep_checks=[]
    for dep in js(w/"parent-01/dependencies.json"):
        path=repo/dep["path"]
        need(git(path,"rev-parse","HEAD").strip()==dep["head"],"dependency HEAD drift")
        need(not git(path,"status","--porcelain","--untracked-files=no").strip(),"tracked dependency drift")
        dep_checks.append(dep["path"])
    need(js(w/"fu-02/dependencies.json")==js(w/"parent-01/dependencies.json")==js(w/"supplement-01/dependencies.json"),"dependency maps differ")
    # Actual observer must be exactly outputs plus three hierarchy-read assigns.
    obs=js(w/"supplement-01/observer.json");name="VDotElasticParentTestTop.sv"
    need(obs["changed"]==[name] and obs["production_modules_unchanged"],"observer scope receipt")
    need(set(obs["before"])==set(obs["after"]),"observer changed file set")
    for n,digest in obs["before"].items():
        need(sha(w/"parent-01/rtl"/n)==digest,"observer initial RTL not original parent")
        need(sha(w/"supplement-01/rtl"/n)==obs["after"][n],"observer final hash")
        if n!=name:need(digest==obs["after"][n],"production observer change")
    orig=text(w/"supplement-01/observer-original-top.sv.txt")
    actual=text(w/"supplement-01/rtl"/name)
    ports="  output [1:0] io_fp_lane_ready,\n               io_fp_lane_finish,\n  output       io_div_busy,\n"
    assigns=("  // C2 test-only hierarchical reads; no production nets are driven.\n"
        "  assign io_fp_lane_ready = {dut.Vfdiv._vfdivs_1_io_start_ready_o, dut.Vfdiv._vfdivs_0_io_start_ready_o};\n"
        "  assign io_fp_lane_finish = {dut.Vfdiv._vfdivs_1_io_finish_valid_o, dut.Vfdiv._vfdivs_0_io_finish_valid_o};\n"
        "  assign io_div_busy = dut.elasticDivOccupied_divBusy;\n")
    need(actual.count(ports)==1 and actual.count(assigns)==1,"observer exact addition missing")
    need(actual.replace(ports,"").replace(assigns,"")==orig,"observer modified other top logic")
    need(hashlib.sha256(orig.encode()).hexdigest()==obs["original_sha256"],"saved original observer hash")
    need(sha(cp/"instrument_parent.py")==obs["observer_script_sha256"],"observer source binding")
    # Golden original parent: original dirty checkout is bound by final source hashes.
    old=Path("/home/riscv/riscv-lab/o2-r3-div-gate-20261024/green-parent-01")
    c1=Path("/home/riscv/riscv-lab/o2-c1-owner-20261025")
    man=js(base/"team/optimizations/o2/r3-div-gate/evidence/20261024-local/manifest.json")
    archive={r["path"]:r["raw_sha256"] for r in man["files"]}
    for f in ["result.log","source.json","source-commit.log","source-status.log"]:
        need(sha(old/f)==archive["runs/green-parent-01/"+f],"old sealed data changed")
    original_sources=js(old/"source.json")
    prod=[p for p in original_sources if p.startswith("src/")]
    for p in prod:need(sha(base/p)==original_sources[p],"old baseline production differs from retained "+p)
    stimulus_names=["team/optimizations/o2/parent/"+n for n in
        ["parent_test.cpp","GenerateVDotElasticParent.scala","check_trace.py","check_negative.py"]]
    for p in stimulus_names:
        need(original_sources.get(p,archive["source-candidate/"+p])==source_maps["parent-01"].get(p,sha(repo/p))==sha(c1/"repo"/p),"parent stimulus changed")
    need(read(old/"vectors.tsv")==read(c1/"parent-01/vectors.tsv")==read(w/"parent-01/vectors.tsv"),"vector input mismatch")
    need(read(old/"result.log")==read(c1/"parent-01/result.log")==read(w/"parent-01/result.log"),"parent raw traces differ")
    strict=module("audit_trace",parent/"check_trace.py")
    original_replay=json.loads(json.dumps(strict.check_trace(text(w/"parent-01/result.log"))))
    prior_replay=js(w/"parent-replay.json")
    need(prior_replay["checker_sha256"]==sha(parent/"check_trace.py"),"strict checker binding")
    need(all(prior_replay[k]==v for k,v in original_replay.items()),"original parent replay drift")
    independent=pneg.check_positive(text(w/"parent-01/result.log"))
    # Offline replay and seven mutations run against original raw supplemental observations.
    offline=[]
    for script,result,log in [("check_c2_parent.py","supplement-replay.json","replay.log"),
                              ("negative_c2_parent.py","supplement-negative.json","negative.log")]:
        offline.append(run([sys.executable,"-B",str(cp/script),"--log",str(w/"supplement-01/result.log"),
                            "--parent-dir",str(parent),"--output",str(out/result)],out,log))
        need(js(out/result)==js(w/"supplement-01"/result),"supplemental replay differs")
    supplement=js(out/"supplement-replay.json")
    negative=js(out/"supplement-negative.json")
    need(negative["count"]==7 and all(x["detected"] for x in negative["records"]),"seven negatives")
    fu_summary=summary(text(w/"fu-02/result.log"),"O2_FU_PASS ")
    psummary=summary(text(w/"parent-01/result.log"),"O2_PARENT_PASS ")
    ssummary=summary(text(w/"supplement-01/result.log"),"O2_PARENT_PASS ")
    for s in [fu_summary,psummary,ssummary]:
        need(s["accepted"]==s["responses"]+s["cancelled"]+s["reset_dropped"],"terminal conservation")
    need(fu_summary["vectors"]==10022 and fu_summary["ii1_intervals"]==10021,"FU scope")
    # Recheck strict prefix identity/conservation in both raw traces (independent simple counter path).
    prefixes={}
    for st in ["parent-01","supplement-01"]:
        count=0
        for line in text(w/st/"result.log").splitlines():
            if not line.startswith("O2_PARENT_CYCLE "):continue
            d=fields(line)
            need(d["cycle"]==count,"cycle numbering")
            need(d["accepted_total"]==d["responses_total"]+d["cancels_total"]+d["resets_total"]+d["inflight"],"prefix conservation")
            count+=1
        prefixes[st]=count
    # Retain original failed dependency preflight; do not recast it as a simulation failure.
    fail=js(w/"local-campaign.json")
    need(fail["status"]=="failed" and fail["steps"][-1]["exit_code"]==1,"first failure missing")
    need(not js(w/"fu-01/runner.status.json")["passed"],"failed first FU missing")
    firstcmds=js(w/"fu-01/commands.json")
    need(not any(x["log"] in {"elaboration.log","verilator.log","result.log"} for x in firstcmds),"first attempt unexpectedly ran hardware")
    repair=js(w/"setup-nested-gitlinks-repair.json")
    # Re-evaluate earlier independent source/cone input pins as part of final frozen audit.
    for fname in ["source-review.json","c2-generated-cone.json","old-c1-cone.json"]:
        review=js(w/"rtl-review"/fname)
        for item in review["inputs"]:need(sha(Path(item["path"]))==item["sha256"],"review pin drift")
    review=js(w/"rtl-review/final-review.json")
    need(review["status"]=="C2_RTL_INDEPENDENT_REVIEW_PASS","structure review incomplete")
    # Count known host tests from real original logs.
    hosts={}
    for f in ["fu-host.log","parent-host.log"]:
        s=text(w/f);m=re.search(r"Ran (\d+) tests? in",s)
        need(m and s.rstrip().endswith("OK"),"host test receipt")
        hosts[f]=int(m[1])
    for p,digest in list(pins.items()):
        need(hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,"end audit input changed "+p)
    result=dict(status="C2_FINAL_READONLY_AUDIT_PASS",candidate_head=HEAD,
        candidate_exeunit_sha256=SHA,retained_head=BASE,production_files=changed,
        campaigns=campaigns,current_dependency_heads_and_tracked_clean=len(dep_checks),
        observer=dict(changed_test_top_only=True,production_generated_modules_unchanged=len(obs["before"])-1,
                      exact_readonly_addition_verified=True),
        baseline_trace=dict(original_run_head=text(old/"source-commit.log").strip(),
          original_checkout_was_dirty=True,source_equivalence_to_retained_production_files=len(prod),
          stimulus_files_equal=len(stimulus_names),three_way_result_bytes_equal=True,
          result_sha256=sha(old/"result.log"),cycles=original_replay["cycles"],
          note="Original run predates 0f commit; production source hashes match retained 0f, not a claim that run HEAD was 0f."),
        host_tests=hosts,fu_summary=fu_summary,parent_summary=psummary,supplement_summary=ssummary,
        parent_strict_replay=original_replay,parent_independent_identity_replay=independent,
        supplemental_summary=supplement,prefix_conservation_cycles=prefixes,
        negative_controls=dict(total=27,fu_runtime_observation=4,parent_runtime_observation=16,
             supplemental_offline_observation=7,rtl_mutation_runs=0),
        offline_commands=offline,failed_first_attempt=dict(preserved=True,stage="dependency preflight before elaboration",exit_code=1),
        source_hash_checks=sum(v["source_hash_checks"] for v in campaigns.values()),
        input_files_unique=len(pins),inputs=[dict(path=p,sha256=s) for p,s in sorted(pins.items())],
        time=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        boundaries=["Replays recorded evidence; no new simulator/build/EDA run.","FU full128 and exact directed SQRT numeric checks occur in original C++ harness; offline trace replays control/identity.",
                    "27 negative controls are observation corruptions, not RTL mutations or complete formal proof.",
                    "No C2 fullcore/NEMU, area, STA, power, performance or final adoption conclusion.",
                    "Dependency recheck verifies current pinned HEAD and tracked cleanliness; original run already records recursive status and source-after confirmation."])
    (out/"audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(result["status"],"unique_inputs",result["input_files_unique"],"source_checks",result["source_hash_checks"],
          "dependencies",len(dep_checks),"negative_controls",27)
if __name__=="__main__":main()
