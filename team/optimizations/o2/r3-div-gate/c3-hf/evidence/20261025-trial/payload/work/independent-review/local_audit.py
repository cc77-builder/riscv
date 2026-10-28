"""Read-only independent audit of completed C3-HF local execution artifacts."""
from pathlib import Path
import json,hashlib,re,subprocess,datetime,collections
W=Path("/home/riscv/riscv-lab/o2-c3-hf-20261025")
R=W/"repo";O=W/"independent-review";S=W/"supplement-02"
MAIN=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
V=MAIN/"team/optimizations/o2/r3-div-gate/c3-hf/validation"
HEAD="77d0a1228f0da7d584d5c7375b404dcda9763cf3"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,label):
 if not ok:raise ValueError(label)
pins=json.loads((O/"inputs-original-stages.json").read_text())
pins.update(json.loads((O/"inputs-source-review.json").read_text()))
pins.update(json.loads((O/"baseline-trace-audit.json").read_text())["inputs"])
def pin(p):pins[str(p)]=sha(p)
def js(p):pin(p);return json.loads(p.read_text())
need(subprocess.check_output(["git","rev-parse","HEAD"],cwd=R,text=True).strip()==HEAD,"candidate HEAD")
need(not subprocess.check_output(["git","status","--porcelain=v1"],cwd=R,text=True).strip(),"candidate dirty")
need(js(S/"runner.status.json")["passed"] is True,"supplement runner")
need((S/"source-commit.log").read_text().strip()==HEAD,"supplement source commit")
need((S/"source-after.status").read_text().strip()=="SOURCE_AND_DEPENDENCIES_UNCHANGED","source after")
need(not (S/"source-status.log").read_text().strip() and not (S/"working-tree.patch").read_text(),"dirty execution")
sources=js(S/"source.json")
for name,h in sources.items():
 f=R/name;need(sha(f)==h,"source "+name);pin(f)
need(sources["src/main/scala/xiangshan/backend/exu/ExeUnit.scala"]=="150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7","source C3 identity")
cmds=js(S/"commands.json");need(len(cmds)==20,"supplement commands count")
for rec in cmds:need(rec["exit_code"]==0,rec["log"]);pin(S/rec["log"])
for n in ["generated-files.json","artifacts.json"]:
 for a in js(S/n):
  p=S/a["path"];need(sha(p)==a["sha256"] and p.stat().st_size==a["bytes"],"artifact "+str(p));pin(p)
deps=js(S/"dependencies.json")
need(len(deps)==126 and deps==js(W/"fu-01/dependencies.json")==js(W/"parent-01/dependencies.json"),"dependency receipt equality")
for d in deps:
 dr=R/d["path"]
 need(subprocess.check_output(["git","rev-parse","HEAD"],cwd=dr,text=True).strip()==d["head"]==d["pin"],"dependency pin "+d["path"])
 need(not subprocess.check_output(["git","status","--porcelain=v1","--untracked-files=normal"],cwd=dr,text=True).strip(),"dirty dependency "+d["path"])
c2=js(S/"c2-observer-reuse.json");c3=js(S/"observer.json")
need(c2["changed"]==c3["changed"]==["VDotElasticParentTestTop.sv"],"only top changed")
need(c3["before"]==c2["after"],"observer chain")
need(sha(S/"observer-original-top.sv.txt")==c2["before"]["VDotElasticParentTestTop.sv"],"original top")
need(sha(S/"c3-observer-before-top.sv.txt")==c3["before"]["VDotElasticParentTestTop.sv"],"intermediate top")
need(c3["script_sha256"]==sha(V/"instrument_c3_parent.py"),"C3 instrument source")
need(c2["observer_script_sha256"]==c3["c2_observer_script_sha256"]==sha(MAIN/"team/optimizations/o2/r3-div-gate/c2/parent/instrument_parent.py"),"C2 observer source")
for name,h in c3["after"].items():
 need(sha(S/"rtl"/name)==h,"observed RTL hash")
 if name!="VDotElasticParentTestTop.sv":need(h==c3["before"][name]==c2["before"][name],"production edited "+name)
structure=js(S/"c3-structure.json")
need(structure["status"]=="C3_HF_GENERATED_HOLD_STRUCTURE_PASS" and not structure["fp_set_forbidden"],"generated structure")
need(structure["source_sha256"]==sha(S/"rtl/ExeUnit.sv"),"generated ExeUnit")
need(structure["bindings"]["fp"]["hold"]=="uncer_en_reg" and structure["bindings"]["int"]["hold"]=="uncer_en_reg_1","retained double hold")
need(structure["bindings"]["fp"]["gate_e"]=="dispatchedInputs_childFires_0 | uncer_en_reg","FP gate")
# Firtool renamed the unchanged integer fire alias after introducing startUncertain.
need(structure["bindings"]["int"]["gate_e"]=="startUncertain_1 | uncer_en_reg_1","INT gate alias")
sv=(S/"rtl/ExeUnit.sv").read_text()
match=re.search(r"wire\s+startUncertain_1\s*=\s*([^;]+);",sv)
need(match is not None and set(match[1].strip().split(" & "))=={"_Vidiv_io_in_ready","_probe_120"},"INT fire alias binding")
need(structure["bindings"]["int"]["fire"]=="(_probe_120 & _Vidiv_io_in_ready)","actual INT instance handshake")
expected_set="io_in_valid & dispatchedInputs_selected_0 & ~elasticDivOccupied_divBusy & ~elasticDivOccupied_divOutValid & ~elasticVDotOccupied & ~io_flush_valid & ~reset"
need(" ".join(structure["bindings"]["fp"]["set"].replace("\\n"," ").split())==expected_set,"FP SET expression")
supp=js(S/"supplement-replay.json");neg=js(S/"supplement-negative.json");monitor=js(S/"c3-monitor-result.json")
need(supp["status"]=="C2_PARENT_SUPPLEMENT_PASS" and supp["replay"]["cycles"]==2959,"supplement replay")
need(sum(supp[k] for k in ["normal_sqrt_cases","sqrt_cancel_cases","te0_reset_cases","sqrt_rob_cases","sqrt_switch_cases"])==115,"115 cases")
need(supp["log_sha256"]==neg["source_log_sha256"]==monitor["parent_sha256"]==sha(S/"result.log"),"supplement log identity")
need(neg["status"]=="C2_PARENT_SUPPLEMENT_NEGATIVE_PASS" and neg["count"]==len(neg["records"])==7,"supplement negative count")
need(all(x["detected"] for x in neg["records"]),"supplement escaped")
need(monitor["status"]=="C3_HF_HOLD_MONITOR_PASS" and len(monitor["negative_controls"])==9,"monitor negative count")
need(all(x["detected"] for x in monitor["negative_controls"]),"monitor escaped")
need(monitor["monitor_sha256"]==sha(S/"c3-hold-monitor.log") and monitor["script_sha256"]==sha(V/"check_c3_monitor.py"),"monitor identity")
need((S/"result.log").read_bytes()==Path("/home/riscv/riscv-lab/o2-c2-readyless-20261025/supplement-01/result.log").read_bytes(),"identical reused suite behavior")
def parse(line):
 return {k:(int(val) if val.isdecimal() else val) for k,val in [field.split("=",1) for field in line.split()[1:]]}
rows=[parse(l) for l in (S/"c3-hold-monitor.log").read_text().splitlines()]
parents=[parse(l) for l in (S/"result.log").read_text().splitlines() if l.startswith("O2_PARENT_CYCLE ")]
need(len(rows)==len(parents)==2959,"monitor row count")
expected=[0,0];qualified=0;cnt=collections.Counter()
for i,(row,par) in enumerate(zip(rows,parents)):
 need(row["cycle"]==par["cycle"]==i and row["qualified"]==qualified,"monitor index/bootstrap")
 need(row["reset"]==par["reset"] and row["te"]==par["te"],"monitor reset/TE")
 need(row["fp_fire"]==int(bool(par["child_fire"]&4)) and row["int_fire"]==int(bool(par["child_fire"]&2)),"monitor accept binding")
 need(row["fp_out"]==int(bool(par["child_out"]&4 and par["out_ready"])) and row["int_out"]==int(bool(par["child_out"]&2 and par["out_ready"])),"monitor response binding")
 if not row["reset"]:need(row["cancel"]==par["kill_div"],"monitor cancel")
 if qualified:
  need(row["p"]==row["fp_fire"],"P must equal actual fire")
  need([row["fp_hold"],row["int_hold"]]==expected,"original fire hold recurrence")
  need([row["expected_fp"],row["expected_int"]]==expected,"shadow recurrence")
  cnt["qualified_cycles"]+=1
  for key,cond in [("fp_accepts",row["fp_fire"]),("int_accepts",row["int_fire"]),("fp_hold_cycles",row["fp_hold"]),("int_hold_cycles",row["int_hold"]),("te0_reset_cycles",row["reset"] and not row["te"]),("cancel_cycles",row["cancel"] and not row["reset"]),("fp_cancel_cycles",row["cancel"] and row["fp_hold"] and not row["reset"]),("fp_release_cycles",row["fp_out"] and not row["reset"]),("fp_backpressure_cycles",par["child_out"]&4 and not par["out_ready"] and not row["reset"]),("sqrt_accepts",str(par["case"]).startswith("C2-sqrt-") and row["fp_fire"])]:cnt[key]+=int(bool(cond))
 else:need(row["reset"] and row["te"],"uninitialized activity")
 expected=[0 if row["reset"] else int(row[k+"_fire"] or row[k+"_hold"] and not(row[k+"_out"] or row["cancel"])) for k in ["fp","int"]]
 if row["reset"] and row["te"]:qualified=1;cnt["bootstrap_edges"]+=1
need(dict(cnt)==monitor["counts"] and expected==[0,0],"monitor aggregate")
cmd=["python3","-B",str(V/"check_c3_monitor.py"),"--monitor",str(S/"c3-hold-monitor.log"),"--parent-log",str(S/"result.log"),"--output",str(O/"monitor-replay.json")]
proc=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(O/"monitor-replay.log").write_text(proc.stdout)
(O/"monitor-replay.command.json").write_text(json.dumps(dict(command=cmd,exit_code=proc.returncode),indent=2)+"\n")
need(proc.returncode==0,"monitor replay command")
need(js(O/"monitor-replay.json")==monitor,"monitor replay differs")
bad=W/"supplement-01";failed=js(bad/"runner.status.json")
need(failed["passed"] is False and not (bad/"result.log").exists(),"failure preserved")
bc=js(bad/"commands.json");need(bc[-1]["log"]=="verilator.log" and bc[-1]["exit_code"]!=0,"original failure command")
need("WIDTHTRUNC" in (bad/"verilator.log").read_text(),"original failure reason")
badsrc=js(bad/"source.json")
v1=W/"protocol-review/instrument_c3_parent-v1.py.txt"
need(badsrc[str(V/"instrument_c3_parent.py")]==sha(v1),"historical instrument snapshot");pin(v1)
original=js(O/"original-stages-audit.json");scope=js(O/"source-review.json");baseline=js(O/"baseline-trace-audit.json")
pin(Path(__file__))
for p,h in pins.items():need(sha(Path(p))==h,"changed final input "+p)
final=dict(status="C3_HF_LOCAL_INDEPENDENT_AUDIT_PASS",candidate_head=HEAD,candidate_exeunit_sha256="150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7",time=datetime.datetime.now().astimezone().isoformat(),original_stages=original,source_scope=scope["status"],baseline_trace=baseline["status"],supplement=dict(stage="supplement-02",status="PASS",source_files=len(sources),commands=len(cmds),cycles=2959,scenarios=115,result_sha256=sha(S/"result.log"),byte_equal_prior_C2_suite_result=True,suite_status_name="C2 names identify unchanged test suite; new C3 execution/source independently bound"),monitor=dict(status="PASS",counts=dict(cnt),negative_controls=9,preedge_original_fire_recurrence_independently_recomputed=True),observer=dict(two_test_top_only_instrumentations=True,production_modules_unchanged=len(c3["after"])-1),negative_controls=dict(total=36,fu_runtime_observation=4,parent_runtime_observation=16,supplement_offline_observation=7,hold_monitor_offline_observation=9,rtl_mutations=0),dependencies=126,inputs_unique=len(pins),input_hashes_unchanged=True,failed_attempt=dict(stage="supplement-01",failure="test-only file-descriptor width warning before RTL execution",preserved=True,historical_instrument_sha256=sha(v1)),area_sta="NOT_TESTED",fullcore="NOT_TESTED",cycles="NOT_TESTED",scope="New C3 local executions audited; no EDA or simulation run by this reviewer; local qualification only, no cost/fullcore adoption.")
need(not (O/"local-audit.json").exists(),"new local audit output required")
(O/"local-audit.json").write_text(json.dumps(final,indent=2)+"\n")
(O/"inputs-local-audit.json").write_text(json.dumps(pins,indent=2)+"\n")
print(json.dumps({k:v for k,v in final.items() if k!="original_stages"},indent=2))
