import os,json,hashlib,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/local-01')
dst=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/review-01')
r=json.loads((src/'result.json').read_bytes())
assert r['status']=='FAILED' and r['error']=="ValueError('incomplete STA')" and len(r['commands'])==2
for c in r['commands']:
 assert c['exit_code']==0 and c['reaped'] and c['group_absent']
for pid in [31999]+[c['pid'] for c in r['commands']]:
 try:os.killpg(pid,0)
 except ProcessLookupError:pass
 else:raise RuntimeError('group remains '+str(pid))
assert not dst.exists();dst.mkdir(parents=True)
files=[]
for n in ['result.json','inputs.json','mapped-fa-bindings.json','sta-feature1.log','map-feature1.log','i2r.rpt','r2r.rpt','setup-checks.rpt']:
 p=src/n
 if not p.exists():continue
 b=p.read_bytes();assert stat.S_ISREG(p.lstat().st_mode)
 (dst/n).write_bytes(b);assert (dst/n).read_bytes()==b==p.read_bytes()
 files.append(dict(name=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
print(json.dumps(dict(status='CLOSED_FA_FAILURE_CAPTURE',files=files,all_groups_absent=True,commands=[{k:v for k,v in c.items() if k!='argv'} for c in r['commands']])))
