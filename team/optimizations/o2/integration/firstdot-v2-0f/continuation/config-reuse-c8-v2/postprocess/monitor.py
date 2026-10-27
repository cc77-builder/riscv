from pathlib import Path
import json,re,subprocess
W=Path("/home/riscv/riscv-lab/software-import-20261026")
O=W/"config-reuse-c8-02"
def read(p):return json.loads(p.read_text())
def tail(p,n=10000):
 with p.open("rb") as f:
  f.seek(max(0,p.stat().st_size-n));return f.read().decode(errors="replace")
for rel in ["state.json","run-01/state.json"]:
 p=O/rel
 if p.exists(): print(rel,read(p))
for d in sorted((O/"run-01/runs").glob("*")):
 p=d/"result.json"
 if not p.exists():continue
 r=read(p);v={k:r.get(k) for k in ["status","pid","exit_code","started","finished"]}
 out=d/"stdout.log";err=d/"stderr.log"
 if out.exists():
  text=tail(out,20000)
  cases=re.findall(r"R4C_CASE seq=(\d+) hash=(\d+)",text)
  v["observed_complete_case_lines"]=len(cases);v["last_case"]=int(cases[-1][0]) if cases else None
  v["guest_end_line"]="R4C_END executed=48 failures=0" in text
 if err.exists():
  text=tail(err);cycles=re.findall(r"cycle=\s*(\d+)",text)
  v["last_observer_cycle"]=int(cycles[-1]) if cycles else None
  v["stderr_bytes"]=err.stat().st_size
 print(d.name,v)
print("active", "\n".join(l for l in subprocess.check_output(["ps","-eo","pid,etimes,pcpu,args"],text=True).splitlines() if "/build/emu " in l))
p=W/"reviews/config-reuse/c8-preflight-02/pipeline.command.json"
print("pipeline",read(p))
p=p.with_suffix(".stderr.log")
if p.exists() and p.stat().st_size:print("pipeline error",tail(p,2200))
