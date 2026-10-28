from pathlib import Path
import subprocess,json,time,datetime,sys
ROOT=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
OUT=Path(__file__).parent
jobs=[]
def unit(name,d,pattern="test_*.py"):
 jobs.append((name,["python3","-B","-m","unittest","discover","-s",d,"-p",pattern,"-v"]))
base="team/optimizations/o2/"
unit("kernel-host",base+"r2-kernel-audit")
unit("safe-tail-host",base+"r2-safe-tail")
unit("s1-host",base+"r2-vector-accum")
unit("selection-entry-host",base+"r2-select")
unit("merged-regression-host",base+"fullcore","test_merged_regression*.py")
def audit(name,module,archive,extra=[]):
 jobs.append((name,["python3","-B",base+module,"--repo",str(ROOT),"--action","audit","--archive",str(ROOT/base/archive),"--output",str(OUT/(name+".json"))]+extra))
audit("s1-archive","r2-vector-accum/evidence.py","r2-vector-accum/evidence/merged-v2")
audit("s1-small-replay","r2-vector-accum/complete_replay.py","r2-vector-accum/evidence/merged-v2",["--supplement","replay-small-01"])
audit("s2-fixed-archive","r2-safe-tail/fixed_evidence.py","r2-safe-tail/evidence/fixed-screen-v1")
audit("s2-rvv-probe","r2-safe-tail/rvv_probe_evidence.py","r2-safe-tail/evidence/rvv-probe-v1")
audit("entry-archive","r2-select/entry_evidence.py","r2-select/evidence/entry-v1")
audit("c-api-archive","r2-select/entry_c_evidence.py","r2-select/evidence/c-api-v1",["--matrix",str(ROOT/base/"r2-select/evidence/entry-v1")])
for action in ["audit","verify-index"]:
 jobs.append(("merged-regression-"+action,["python3","-B",base+"fullcore/merged_regression_evidence.py",action,"--archive",str(ROOT/base/"fullcore/evidence/merged-regression-v1/archive"),"--output",str(OUT/("merged-regression-"+action+".json"))]))
results=[]
for name,cmd in jobs:
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 print("START",name,flush=True)
 with (OUT/(name+".stdout")).open("w") as stdout,(OUT/(name+".stderr")).open("w") as stderr:
  try: code=subprocess.run(cmd,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=900).returncode
  except subprocess.TimeoutExpired: code=124
 receipt={"name":name,"command":cmd,"cwd":str(ROOT),"started":started,"finished":datetime.datetime.now(datetime.timezone.utc).isoformat(),"returncode":code}
 results.append(receipt)
 (OUT/"checks.json").write_text(json.dumps(results,indent=2)+"\n")
 print("DONE",name,"rc",code,flush=True)
 if code: print((OUT/(name+".stderr")).read_text()[-1800:],flush=True)
print("ALL_DONE",sum(x["returncode"]==0 for x in results),len(results),flush=True)
