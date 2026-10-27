"""Current 0f config-reuse ordinary C: preserved gates, 8x32-first case table."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, os, shutil, struct, sys, time, types

HERE=Path(__file__).resolve().parent
W=HERE.parents[2]
SOURCE=W/"clean-02/checkout/source"
ID=W/"clean-02/identity/current.json"
MATRIX=W/"config-reuse-expanded-01"
TOOLS=HERE.parent/"expansion-v1"
CONTRACT="zjhwork-config-reuse-8x32-c-qualification-v1"
TARGET="config_reuse_gemv_8x32_reuse_vdot"
PARENT=Path("team/optimizations/o2/r2-select/entry_c_api.py")
PASS="CURRENT_CONFIG_REUSE_8X32_C_QUALIFIED"
def require(x,s):
 if not x:raise ValueError(s)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def now():return datetime.now(timezone.utc).isoformat()
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify(files):
 for p,h in files.items():
  q=Path(p);require(q.is_file() and not q.is_symlink() and sha(q)==h,"input changed "+p)
def add_files(a,b):
 for k,v in b.items():
  require(k not in a or a[k]==v,"mixed input identity "+k);a[k]=v
 return a
def case_key(c):return json.dumps(c,sort_keys=True,separators=(",",":"))
def ordered_cases(cases):
 require(len(cases)==48 and len({case_key(c) for c in cases})==48,"48 distinct cases")
 focus=[c for c in cases if (c["m"],c["k"])==(8,32)]
 require(len(focus)==12 and {c["dataset"] for c in focus}=={0,1,2},"complete target datasets")
 require(len({c["api_symbol"] for c in focus})==4,"four target functions")
 result=sorted(cases,key=lambda c:(0 if (c["m"],c["k"])==(8,32) else 1,
       0 if c["api_symbol"]==TARGET and c["dataset"]==0 else 1))
 require(result[0]["api_symbol"]==TARGET and result[0]["dataset"]==0,"target first")
 require(Counter(map(case_key,cases))==Counter(map(case_key,result)),"case multiset changed")
 return result
def case_table(cases):
 return "\n".join("{"+",".join([c["api_symbol"],c["input_symbol"]]+
  ["UINT64_C("+str(c[k])+")" for k in ("m","k","size","dataset","api_index","expected_hash")])+"}," for c in cases)+"\n"
def reorder_generated(out):
 manifest=read(out/"manifest.json");old=manifest["cases"];new=ordered_cases(old)
 text=(out/"cases.h").read_text()
 marker="static const struct r4_c_case r4_c_cases[] __attribute__((used))={\n"
 require(text.count(marker)==1,"C table marker")
 head,table=text.split(marker)
 require(table==case_table(old)+"};\n","original complete C table bytes")
 (out/"cases.h").write_text(head+marker+case_table(new)+"};\n")
 manifest.update(cases=new,current_caller_contract=CONTRACT,case_order="8x32-d0-reuse-vdot-first",
  original_cases_sha256=hashlib.sha256((json.dumps(old,sort_keys=True)+"\n").encode()).hexdigest())
 save(out/"manifest.json",manifest)
 return manifest
def timing_proof(records,boot):
 require(len(records)==3 and [r["negative"] for r in records]==[True,False,False]
  and [r["replay"] for r in records]==[0,0,1],"three ordered target records")
 pids=set();previous=-1
 for r in records:
  t=r.get("current_c_monotonic",{});pid=r.get("pid")
  require(type(pid)is int and pid>0 and pid not in pids and type(t.get("pid"))is int and t["pid"]==pid,"actual PID")
  require(t.get("boot_id")==boot and t.get("scope")=="popen_wait_bracket","monotonic clock domain")
  a,b=t.get("start_ns"),t.get("end_ns")
  require(type(a)is int and type(b)is int and 0<=a<b and previous<=a,"serial typed envelopes")
  previous=b;pids.add(pid)
 return dict(processes=3,unique_pids=sorted(pids),boot_id=boot,serial=True,
  scope="popen_wait_bracket",exact_os_overlap_claimed=False)
def monitored_spawn(original,emu,out,check_outer):
 boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
 timings={}
 def spawn(argv,cwd,stdout,stderr,record,persist,env=None,timeout=600):
  if Path(argv[0]).resolve()!=emu:
   return original(argv,cwd,stdout,stderr,record,persist,env=env,timeout=timeout)
  check_outer()
  label="negative" if record["negative"] else ("replay" if record["replay"] else "recovery")
  require(label not in timings,"duplicate C launch")
  record["current_c_monotonic"]=dict(boot_id=boot,pid=None,start_ns=time.monotonic_ns(),end_ns=None,scope="popen_wait_bracket")
  persist()
  try:return original(argv,cwd,stdout,stderr,record,persist,env=env,timeout=timeout)
  finally:
   record["current_c_monotonic"].update(end_ns=time.monotonic_ns(),pid=record.get("pid"))
   timings[label]=dict(record["current_c_monotonic"]);persist()
   save(out/"monotonic-records.json",timings)
   check_outer()
 return spawn,boot

class CurrentC:
 def __init__(self):
  self.pins=read(HERE/"parent-pins.json");verify(self.pins)
  self.matrix=load("current_c_matrix",TOOLS/"matrix.py")
  self.p=self.matrix.Matrix(SOURCE,ID,W/"clean-02/matrix-build-01",W/"clean-02/matrix-run-01")
  self.images=self.p.selected(MATRIX/"build-01")
  self.audit_module=load("current_c_matrix_raw",TOOLS/"raw_audit.py")
  proof=read(MATRIX/"audit-01.json");result=read(MATRIX/"run-01/results.json")
  require(proof["status"]=="EXPANDED_MATRIX_LOCAL_RAW_AUDIT_PASS" and result["new_emu_runs"]==33
   and result["all_window_replay"] is True and result["decisions"]["8x32"]["decision"]=="PERFORMANCE_CANDIDATE",
   "qualified target matrix required")
  require(proof["campaign_evidence_sha256"]==self.audit_module.tree_seal(MATRIX/"run-01"),"matrix raw tree changed")
  self.c=load("current_c_config_api",SOURCE/"team/optimizations/o2/r2-config-reuse/c_api.py")
  self.app=self.p.combo.c_adapter(SOURCE,self.p.identity)
  self.app.CONTRACT=self.c.CONTRACT
  self.app.source_files=self.c.source_files
  self.app.generate=self.generate
  self.cfg=self.p.identity["configuration"]
  self.outer=dict(self.pins)
  add_files(self.outer,read(MATRIX/"run-01/runtime-inputs.json"))
  add_files(self.outer,{str(p):sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in (".py",".md",".json")})
 def generate(self,repo,out):
  self.c.generate(repo,out)
  return reorder_generated(out)
 def physical(self):return self.p.physical()
 def anchor(self,build):
  manifest=read(build/"source/manifest.json")
  public=self.c.g.ELF((build/"gemv-reference.o").read_bytes())
  names={r["api_symbol"] for r in manifest["rows"]}
  require(len(names)==16 and manifest["cases"][0]["api_symbol"]==TARGET and manifest["cases"][0]["dataset"]==0,"C scope")
  rows=[]
  for image in self.images:
   if image["variant"]!="config-reuse":continue
   parent=self.c.g.ELF((Path(image["path"])/"gemv-reference.o").read_bytes())
   m=read(Path(image["path"])/"data/manifest.json")
   for row in m["rows"]:
    symbol=self.c.public_name(row["api_symbol"])
    a,b=parent.symbol_data(row["api_symbol"]),public.symbol_data(symbol)
    require(symbol in names and a==b,"public leaf changed "+symbol)
    rows.append(dict(image=image["name"],symbol=symbol,dataset=image["dataset"],
     shard=image["shard"],sha256=hashlib.sha256(b).hexdigest()))
  require(len(rows)==48 and sum(x["shard"]==3 for x in rows)==12,"48 matrix leaf anchors")
  elf=self.c.g.ELF((build/"vdot-perf.elf").read_bytes());body=elf.symbol_data(TARGET)
  pcs=[elf.symbols[TARGET][0]+i for i in range(0,len(body),4) if struct.unpack_from("<I",body,i)[0]==0x0388000b]
  require(pcs,"actual target custom instruction")
  return dict(status="CURRENT_CONFIG_REUSE_C_LEAVES_ANCHORED",comparisons=rows,
   comparisons_count=48,target_comparisons=12,target_symbol=TARGET,negative_expected_pc=hex(pcs[0]),
   target_functions=4,target_distinct_cases=12,target_normal_executions=24,
   matrix_result_sha256=sha(MATRIX/"run-01/results.json"))
 def check_outer(self):verify(self.outer)
 def build(self,out):
  self.check_outer()
  result=self.app.build(SOURCE,self.cfg,out)
  anchor=self.anchor(out);save(out/"current-matrix-anchor.json",anchor)
  self.check_outer()
  return result,anchor
 def run(self,build,out):
  require(1<=len(os.sched_getaffinity(0))<=4,"run with <=4 allowed CPUs")
  self.check_outer();anchor=self.anchor(build)
  require(anchor==read(build/"current-matrix-anchor.json"),"build anchor drift")
  f=self.app.a.frozen_f;original=f.spawn
  spawn,boot=monitored_spawn(original,Path(self.cfg["hardware_source"])/"build/emu",out,self.check_outer)
  f.spawn=spawn
  try:state=self.app.run(SOURCE,self.cfg,build,out,"zjhwork-config-reuse-8x32-c-20261027-01")
  finally:f.spawn=original
  records=read(out/"results.json")["runs"]
  t=timing_proof(records,boot)
  detail=records[0]["negative_details"]
  require(detail["pc"]==anchor["negative_expected_pc"] and detail["word"]=="0x0388000b"
   and detail["vd"]==0 and detail["bit"]==100,"negative did not hit 8x32 reuse vdot")
  save(out/"current-c-qualification.json",dict(contract=CONTRACT,status=PASS,anchor=anchor,
   monotonic=t,performance_measured=False,default_changed=False))
  return state
 def audit(self,build,run,output):
  self.check_outer()
  before=self.audit_module.tree_seal(run)
  proof=self.app.audit_run(SOURCE,build,run)
  anchor=self.anchor(build);q=read(run/"current-c-qualification.json")
  records=read(run/"results.json")["runs"]
  t=timing_proof(records,q["monotonic"]["boot_id"])
  require(q==dict(contract=CONTRACT,status=PASS,anchor=anchor,monotonic=t,
   performance_measured=False,default_changed=False),"current C qualification drift")
  require(read(build/"current-matrix-anchor.json")==anchor,"anchor cached value")
  require(records[0]["negative_details"]["pc"]==anchor["negative_expected_pc"],"target PC mismatch")
  mon={label:record["current_c_monotonic"] for label,record in zip(("negative","recovery","replay"),records)}
  require(read(run/"monotonic-records.json")==mon,"monotonic receipts differ")
  manifest=read(build/"source/manifest.json")
  focus=[(i,c) for i,c in enumerate(manifest["cases"]) if (c["m"],c["k"])==(8,32)]
  require(len(focus)==12 and [i for i,c in focus]==list(range(12)),"target case positions")
  for rec in records[1:]:
   require(all(rec["validation"]["output_hashes"][i]==case["expected_hash"] for i,case in focus),"target C outputs")
  require(self.audit_module.tree_seal(run)==before,"read-only audit mutated campaign")
  self.check_outer()
  value=dict(status="CURRENT_CONFIG_REUSE_C_RAW_AUDIT_PASS",contract=CONTRACT,inner_proof=proof,
   anchor=anchor,timing=t,target_cases=[dict(index=i,**c) for i,c in focus],
   target_custom_commits_per_normal=sum(c["dots"] for i,c in focus),
   normal_output_replay_equal=records[1]["validation"]==records[2]["validation"],
   source_matrix_decisions=read(MATRIX/"run-01/results.json")["decisions"],
   new_emu_runs=0,actual_target_processes=3,performance_measured=False,default_changed=False,
   campaign_files=before)
  require(not output.exists(),"new audit output");save(output,value);return value
 def export(self,build,run,out):
  require(not out.exists(),"new export")
  q=read(run/"current-c-qualification.json");require(q["status"]==PASS,"C run qualification")
  self.app.verify_build(SOURCE,build)
  require(self.anchor(build)==q["anchor"],"public source anchor")
  out.mkdir()
  for name in ("gemv.S","gemv.h","main.c","cases.h","manifest.json","Makefile"):
   shutil.copyfile(build/"source"/name,out/name)
  save(out/"qualification.json",dict(contract=CONTRACT,status=PASS,
   current_8x32_performance_candidate=True,other_shape_performance_adoption=False,
   files={n:sha(out/n) for n in ("gemv.S","gemv.h","main.c","cases.h","manifest.json","Makefile")},
   new_c_performance_measurement=False,default_changed=False))

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True)
 args=ap.parse_args();out=args.output.resolve()
 require(not out.exists(),"new C campaign root")
 require(not any(out.is_relative_to(p.resolve()) for p in [SOURCE,HERE,MATRIX,W/"clean-02"]), "outside frozen inputs")
 experiment=CurrentC()
 before=experiment.physical()
 add_files(experiment.outer,before[1])
 out.mkdir()
 save(out/"identity-before.json",before)
 save(out/"outer-inputs.json",experiment.outer)
 state=dict(contract=CONTRACT,status="BUILDING",started=now(),new_emu_runs=0,performance_measured=False)
 save(out/"state.json",state)
 try:
  result,anchor=experiment.build(out/"build-01")
  state["status"]="RUNNING";save(out/"state.json",state)
  experiment.run(out/"build-01",out/"run-01")
  state.update(status="AUDITING",new_emu_runs=3);save(out/"state.json",state)
  proof=experiment.audit(out/"build-01",out/"run-01",out/"audit-01.json")
  require(experiment.physical()==before,"final physical identity changed")
  experiment.check_outer()
  experiment.export(out/"build-01",out/"run-01",out/"qualified-public")
  state.update(status=PASS,target_functions=4,target_cases=12,target_normal_executions=24,
   total_functions=16,total_cases=48,total_normal_executions=96,
   target_negative_pc=anchor["negative_expected_pc"],identity_unchanged=True,source_files_unchanged=True,
   default_changed=False,hardware_changed=False,github_uploaded=False)
 except BaseException as exc:
  state.update(status="FAILED",error=repr(exc));raise
 finally:
  state["finished"]=now();save(out/"state.json",state)
 print(json.dumps(state,ensure_ascii=False))
if __name__=="__main__":main()
