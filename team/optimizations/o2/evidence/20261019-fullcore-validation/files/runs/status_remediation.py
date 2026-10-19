from pathlib import Path
from datetime import datetime,timezone
import json,re
root=Path("/home/riscv/riscv-lab/o2-fullcore-20261019")
repo=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}
result={"time":datetime.now(timezone.utc).isoformat(),"build":read(root/"build-03/build-state.json").get("status"),"launch":read(root/"remediation-launch-state.json").get("status"),"jobs":[]}
if result["build"]!="O2_FULLCORE_BUILD_PASS":
    result["objects"]=len(list((repo/"build/emu-compile").glob("*.o")))
for campaign in ("supplements-02",):
    for p in sorted((root/campaign).glob("*/runtime.json")):
        state=read(p.parent/"result.json") or read(p)
        item={"name":p.parent.name,"status":state.get("status"),"exit_code":state.get("exit_code")}
        if "error" in state:item["error"]=state["error"]
        for name in ("stdout.log","stderr.log"):
            f=p.parent/name
            if not f.exists():continue
            with f.open("rb") as fd:
                fd.seek(max(0,f.stat().st_size-65536));tail=fd.read().decode("utf-8",errors="replace")
            cyc=re.findall(r"O2_[A-Z_]+ cycle=\s*(\d+)",tail)
            if cyc:item["latest_cycle"]=max(int(x) for x in cyc)
        result["jobs"].append(item)
result["emu_memory_samples"]=[]
for proc in Path("/proc").iterdir():
    if not proc.name.isdigit():continue
    try:
        argv=(proc/"cmdline").read_bytes().split(b"\0")
        if not argv or argv[0] != str(repo/"build/emu").encode():continue
        mem=(proc/"status").read_text()
        result["emu_memory_samples"].append({"pid":int(proc.name),"sampled_peak_rss_kib":int(re.search(r"VmHWM:\s+(\d+)",mem)[1])})
    except (OSError,TypeError,AttributeError):continue
snapshots=root/"resource-monitor"
snapshots.mkdir(exist_ok=True)
snapshot=snapshots/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+".json")
if not snapshot.exists():snapshot.write_text(json.dumps(result,indent=2)+chr(10))
print(json.dumps(result,indent=2))
