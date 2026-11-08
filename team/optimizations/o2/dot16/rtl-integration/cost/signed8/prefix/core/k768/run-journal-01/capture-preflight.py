import os,json,hashlib,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k768-20261108-main')
dst=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-k768-20261108-main/preflight-review-01')
assert not dst.exists() and not dst.is_symlink()
paths={'profile.json':root/'preflight-01/profile.json','result.json':root/'preflight-01/result.json','SOURCE_STAGING.json':root/'input-01/SOURCE_STAGING.json','PREFLIGHT.stdout':root/'input-01/PREFLIGHT.stdout','PREFLIGHT.stderr':root/'input-01/PREFLIGHT.stderr'}
data={n:p.read_bytes() for n,p in paths.items()}
assert hashlib.sha256(data['profile.json']).hexdigest()=='c8afad336dc289e76cb7055b6430399a3df77632232eed2dfc8e77e4c5b248f9'
q=json.loads(data['profile.json']);assert q['status']=='FROZEN_BEFORE_EMU' and len(q['pins'])==457
assert q['runtime_sha256']=='984ff535756419240db26deaea96214b3ee98d65e30b0e10476abcd9cab06ac9'
assert q['max_cycles']==6000000 and q['budget_seconds']==7200 and q['stream_limit_bytes']==16777216
dst.mkdir(parents=True,exist_ok=False);rows=[]
for n,p in paths.items():
 b=data[n];assert stat.S_ISREG(p.lstat().st_mode);(dst/n).write_bytes(b);assert (dst/n).read_bytes()==b and p.read_bytes()==b
 rows.append(dict(source=str(p),name=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
a=dict(status='K768_PREFLIGHT_CLOSED_CAPTURE',files=rows,source_unchanged=True,emu_runs=0,profile_pins=len(q['pins']),runtime=q['runtime_source'],emu=q['emu'])
(dst/'audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a))
