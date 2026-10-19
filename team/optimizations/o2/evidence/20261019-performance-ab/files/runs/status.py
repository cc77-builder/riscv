import json,re
from pathlib import Path
from datetime import datetime,timezone
w=Path("/home/riscv/riscv-lab/o2-performance-20261019")
def read(p):
    try:return json.loads(p.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}
b=read(w/"o1-build-01/build-state.json");campaign=read(w/"campaign-01/state.json")
p=w/"o1-build-01/products"
info=dict(time=datetime.now(timezone.utc).isoformat(),build=b.get("status"),objects=len(list((p/"emu-compile").glob("*.o"))),
          launch=read(w/"launch-state.json").get("status"),campaign_status=campaign.get("status"),stage=campaign.get("stage"),finished_jobs=campaign.get("new_emu_jobs",0))
monitor=read(w/"build-monitor.json")
info["actual_compilers"]=[r["exe"] for r in monitor.get("invocations",[])]
running=[]
for runtime in (w/"campaign-01").glob("*/*/*/runtime.json"):
    if not (runtime.parent/"result.json").exists():
        job=read(runtime)
        text=(runtime.parent/"stdout.log").read_text(errors="replace")
        total=len(read(Path(job["build"])/"data/manifest.json").get("plan",[]))
        running.append(dict(name=job.get("name"),checked_uart_windows=len(re.findall(r"T13_(?:P|CASE) seq=",text)),planned_windows=total))
info["running"]=running
snap=w/"resource-monitor";snap.mkdir(exist_ok=True)
target=snap/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+".json")
if not target.exists():target.write_text(json.dumps(info,indent=2)+"\n")
print(json.dumps(info,ensure_ascii=False))
