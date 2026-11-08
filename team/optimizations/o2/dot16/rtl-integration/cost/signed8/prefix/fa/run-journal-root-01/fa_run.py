import os,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main");src=root/'input-01';out=root/'local-01'
items=json.loads("[{\"name\":\"fa_mapping.py\",\"bytes\":13081,\"sha256\":\"6716b4326a8e00e278e4bbd9088d6aafe4b2f6abf674c3a9a21f15e33244a2ce\"},{\"name\":\"fa_transform.py\",\"bytes\":9906,\"sha256\":\"5f5ee10d63ea1c2db3256fa4fa6f845ca2653eb1dd441e3ded910f86d6a1e36c\"},{\"name\":\"verify_csa.py\",\"bytes\":14051,\"sha256\":\"e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de\"},{\"name\":\"CONTRACT.md\",\"bytes\":3921,\"sha256\":\"41234f419562e0b27ef5a6e1ca31b28d9f18879500abe52fd37bce7b1efbe0ad\"}]")
for x in items:
 b=(src/x['name']).read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
p=(src/'PLAN_ONLY.json').read_bytes();assert len(p)==8984 and hashlib.sha256(p).hexdigest()=='dcb36a1e7872c482ce5ca301ccb9a11a1b1b3cbf81932f5c9fa9807a7c764b48'
assert not out.exists() and not out.is_symlink()
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=2097152
assert shutil.disk_usage(root).free>=536870912
heavy=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:
  name=(p/'comm').read_text().strip()
  if name in ('java','emu','yosys','berkeley-abc','sta','verilator_bin','clang','clang++','make','cc1plus'):
   aff=sorted(os.sched_getaffinity(int(p.name)));heavy.append(dict(pid=int(p.name),name=name,affinity=aff));assert 2 not in aff,'CPU2 engineering conflict '+str(p)
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
used={2,3} # CPU3 reserved for the authorized independent core archive
for x in heavy:used.update(x['affinity'])
assert len(used)<=4,'aggregate CPU budget'
if os.getpgrp()!=os.getpid():os.setsid()
argv=['/usr/bin/python3','-B',str(src/'fa_mapping.py'),'--output',str(out),'--execute']
print(json.dumps(dict(status='FA_X1_LAUNCH',started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,argv=argv)),flush=True)
os.execv(argv[0],argv)
