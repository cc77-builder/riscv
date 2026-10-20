import json,time,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone
w=Path("/home/riscv/riscv-lab/o2-performance-20261019")
build=w/"o1-build-01"
data=dict(started_utc=datetime.now(timezone.utc).isoformat(),invocations=[],resource_samples=[])
seen=set()
def save():
    p=w/"build-monitor.json";t=p.with_suffix(".tmp")
    t.write_text(json.dumps(data,indent=2)+"\n");t.replace(p)
while True:
    try:state=json.loads((build/"build-state.json").read_text())
    except FileNotFoundError:state={}
    matches=[]
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():continue
        try:
            argv=(p/"cmdline").read_bytes().decode(errors="replace").split("\0")
            exe=(p/"exe").resolve()
            if not (str(build/"products") in " ".join(argv)):continue
            if exe.name in ("clang","clang-19","clang++","clang++-19") and str(exe) not in seen:
                seen.add(str(exe))
                version=subprocess.check_output([str(exe),"--version"],text=True)
                data["invocations"].append(dict(pid=int(p.name),exe=str(exe),sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),version=version,command=argv))
            if exe.name in ("java","clang","clang-19","clang++","clang++-19","verilator_bin"):
                status=(p/"status").read_text()
                mem={line.split(":")[0]:line.split(":")[1].strip() for line in status.splitlines() if line.startswith(("VmRSS:","VmHWM:"))}
                matches.append(dict(pid=int(p.name),exe=str(exe),**mem))
        except (OSError,ProcessLookupError,ValueError):continue
    if len(data["resource_samples"])==0 or time.time()-last>30:
        data["resource_samples"].append(dict(time=datetime.now(timezone.utc).isoformat(),processes=matches));last=time.time()
    data["build_status"]=state.get("status");save()
    if state.get("status") in ("FAILED","O1_MATCHED_BUILD_PASS"):break
    time.sleep(5)
data["finished_utc"]=datetime.now(timezone.utc).isoformat();save()
