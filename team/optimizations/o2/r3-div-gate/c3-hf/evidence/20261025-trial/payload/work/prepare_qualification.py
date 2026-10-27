import datetime,hashlib,importlib.util,json,sys
from pathlib import Path
w=Path("/home/riscv/riscv-lab/o2-c3-hf-20261025")
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
m=r/"team/optimizations/o2/r3-div-gate/c3-hf"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
audit=w/"independent-review/local-audit.json"
assert audit.exists(),"Independent local audit is required"
a=read(audit);assert a["candidate_head"]=="77d0a1228f0da7d584d5c7375b404dcda9763cf3"
assert "PASS" in a["status"] and not any(s in a["status"] for s in ["FAIL","REJECT","NOT_PASS"])
q={"schema":"C3_HF_COST_QUALIFICATION_V1","created":datetime.datetime.now().astimezone().isoformat(),
"candidate":{"repo":str(w/"repo"),"head":"77d0a1228f0da7d584d5c7375b404dcda9763cf3",
"exeunit_sha256":"150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7","baseline":"0f12df675378556670afd0dd2153f47fcb330610"},
"checks":{},"source_manifests":{},"inputs":{}}
def check(key,path,field,value):
 p=Path(path)
 assert read(p)[field]==value
 q["checks"][key]={"path":str(p),"sha256":sha(p),"assertions":[{"keys":[field],"equals":value}]}
for key,stage in [("fu","fu-01"),("parent","parent-01"),("supplement","supplement-02")]:
 check(key,w/stage/"runner.status.json","passed",True)
 p=w/stage/"source.json"
 q["source_manifests"][key]={"path":str(p),"sha256":sha(p)}
 for name,value in read(p).items():
  if Path(name).is_absolute():
   assert sha(name)==value
   q["inputs"][str(Path(name).resolve())]=value
 for p in sorted((w/stage).rglob("*")):
  if p.is_file() and "obj" not in p.relative_to(w/stage).parts:
   q["inputs"][str(p.resolve())]=sha(p)
check("state",w/"supplement-02/c3-monitor-result.json","status","C3_HF_HOLD_MONITOR_PASS")
check("source_scope",w/"independent-review/source-review.json","status","C3_HF_SOURCE_SCOPE_REVIEW_PASS")
check("replay",w/"parent-replay.json","status","O2_PARENT_OFFLINE_TRACE_PASS")
check("negative_controls",w/"supplement-02/supplement-negative.json","status","C2_PARENT_SUPPLEMENT_NEGATIVE_PASS")
check("audit",audit,"status",a["status"])
for name in ["local-campaign.json","candidate.json","local-functional-result.json","protocol-review/instrument-review.json",
"independent-review/source-review.json","independent-review/local-audit.json","independent-review/original-stages-audit.json","independent-review/baseline-trace-audit.json","cost-review/implementation-freeze.json","cost-review/host-tests-02.json"]:
 p=w/name
 if p.exists():q["inputs"][str(p.resolve())]=sha(p)
qpath=w/"cost-qualification.json"
assert not qpath.exists()
qpath.write_text(json.dumps(q,indent=2)+"\n")
sys.path.insert(0,str(m/"cost"))
import qualification
pins={}
qualification.validate(qpath,pins)
result={"status":"C3_HF_QUALIFICATION_PREFLIGHT_PASS","qualification_sha256":sha(qpath),"input_files":len(pins),"candidate_head":q["candidate"]["head"]}
(w/"qualification-preflight.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))
