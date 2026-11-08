import os,json,hashlib,subprocess,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/serialization-source-01')
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main")
dst=root/'input-serial-01';out=root/'serialization-01'
items=json.loads("[{\"name\":\"fa_serialization.py\",\"bytes\":13071,\"sha256\":\"82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a\"},{\"name\":\"SERIALIZATION_CONTRACT.md\",\"bytes\":2047,\"sha256\":\"00db43f49848377d5c01bcec6eb008faf79a96e3956317cfdc0e045de60b1d1c\"}]")
assert not dst.exists() and not dst.is_symlink() and not out.exists()
original={}
for x in items:
 p=src/x['name'];assert stat.S_ISREG(p.lstat().st_mode);b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];original[x['name']]=b
dst.mkdir(parents=True,exist_ok=False)
for x in items:
 p=dst/x['name'];p.write_bytes(original[x['name']]);assert p.read_bytes()==original[x['name']]
argv=['/usr/bin/python3','-B',str(dst/'fa_serialization.py')]
p=subprocess.run(argv,cwd=dst,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
(dst/'PLAN_ONLY.json').write_bytes(p.stdout);(dst/'PLAN_ONLY.stderr').write_bytes(p.stderr)
assert p.returncode==0,p.stderr.decode(errors='replace')
plan=json.loads(p.stdout);assert plan['status']=='PLAN_ONLY' and plan['output']==str(out)
assert not out.exists()
for x in items:assert (src/x['name']).read_bytes()==(dst/x['name']).read_bytes()==original[x['name']]
audit=dict(status='FA_SERIALIZATION_STAGED_PLAN_ONLY',files=items,total_bytes=sum(x['bytes'] for x in items),plan=dict(bytes=len(p.stdout),sha256=hashlib.sha256(p.stdout).hexdigest()),plan_exit=0,stderr_bytes=len(p.stderr),output_absent=True,sources_unchanged=True,new_eda_runs=0)
(dst/'SOURCE_STAGING.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
