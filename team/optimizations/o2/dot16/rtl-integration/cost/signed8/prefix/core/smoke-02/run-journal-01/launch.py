import os,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{1});os.setpriority(os.PRIO_PROCESS,0,5)
planpath=Path("/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-20261107-main/core-smoke-plan-02/PLAN_ONLY.json");b=planpath.read_bytes()
assert len(b)==5493 and hashlib.sha256(b).hexdigest()=='f1515233de5f7e1c1c35ea4f3ca155970575a8918958b9d1b1bcc13c1c6e6044'
p=json.loads(b);out=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/core-smoke-02")
assert p['status']=='PLAN_ONLY_NO_SMOKE' and p['output']==str(out) and not out.exists() and not out.is_symlink()
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=2097152
assert shutil.disk_usage(out.parent).free>=536870912
heavy=[]
for q in Path('/proc').iterdir():
 if not q.name.isdecimal():continue
 try:
  name=(q/'comm').read_text().strip()
  if name in ('java','emu','yosys','berkeley-abc','sta','verilator_bin','clang','clang++','clang++-19','make','cc1plus','ninja'):
   aff=sorted(os.sched_getaffinity(int(q.name)));heavy.append(dict(pid=int(q.name),name=name,affinity=aff));assert 1 not in aff,'CPU1 engineering conflict '+str(q)
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
used={1}
for x in heavy:used.update(x['affinity'])
assert len(used)<=4
argv=json.loads("[\"/usr/bin/python3\",\"-B\",\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/core-smoke-source-02/prefix_core_smoke.py\",\"--core-build\",\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/core-build-02\",\"--core-result-sha256\",\"06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2\",\"--source-sha256\",\"cdd3dcd9e58ea0f16587884cc63226655c489f8536a0c4ca4a8f0bd2a758970b\",\"--contract-sha256\",\"0cd16c769269d636430c23e7518ab8d1f7576b9873669aad62c0ea885c22f35d\",\"--output\",\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/core-smoke-02\",\"--execute\",\"--budget-seconds\",\"1200\",\"--deadline-utc\",\"2026-11-08T03:45:00Z\"]")
if os.getpgrp()!=os.getpid():os.setsid()
print(json.dumps(dict(status='PREFIX_CORE_SMOKE02_LAUNCH',at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,plan_sha256=hashlib.sha256(b).hexdigest(),argv=argv)),flush=True)
os.execv(argv[0],argv)
