import os,json,hashlib,re,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
old=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/local-01')
dst=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/evidence-input-01')
assert not dst.exists() and not dst.is_symlink()
fin=old/'final-artifact-pins.json';fb=fin.read_bytes()
assert hashlib.sha256(fb).hexdigest()=='07d4a614ba2b7fd06652290d266023ae405881578cc370fa86d368086baa3451'
pins=json.loads(fb)
paths=[old/'cost-feature1/rtl'/n for n in ('VDotCarrySaveRows.sv','VDotPrefixFinish20.sv','VDotElastic.sv','CommonFuCostTop.sv')]
paths += [old/'cost-feature1/mapped'/n for n in ('map.ys','timing.tcl','abc.constr')]
lib=Path('/home/lizufan/riscv-tools/nangate45/NangateOpenCellLibrary_typical.lib')
lb=lib.read_bytes();assert len(lb)==6692032 and hashlib.sha256(lb).hexdigest()=='8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1'
s=lb.decode();m=list(re.finditer(r'\bcell\s*\(FA_X1\)\s*\{',s));assert len(m)==1
a=m[0].start();beg=m[0].end();depth=1;quote=False;esc=False;end=None
for i in range(beg,len(s)):
 c=s[i]
 if quote:
  if esc:esc=False
  elif c=='\\':esc=True
  elif c=='"':quote=False
 else:
  if c=='"':quote=True
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:end=i+1;break
assert end is not None
cell=s[a:end].encode()
items={p.name:p.read_bytes() for p in paths}
for p in paths:assert stat.S_ISREG(p.lstat().st_mode) and hashlib.sha256(items[p.name]).hexdigest()==pins[str(p)]
dst.mkdir(parents=True,exist_ok=False)
audit=[]
for p in paths:
 b=items[p.name];q=dst/p.name;q.write_bytes(b);assert q.read_bytes()==b and p.read_bytes()==b
 audit.append(dict(source=str(p),name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(dst/'FA_X1.libcell').write_bytes(cell)
audit.append(dict(source=str(lib),name='FA_X1.libcell',bytes=len(cell),sha256=hashlib.sha256(cell).hexdigest(),source_sha256=hashlib.sha256(lb).hexdigest(),start_byte=a,end_byte=end))
assert lib.read_bytes()==lb and fin.read_bytes()==fb
result=dict(status='FA_INPUT_CAPTURE_ONLY',files=audit,new_eda_runs=0,inputs_unchanged=True)
(dst/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
