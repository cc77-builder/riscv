import os,json,hashlib,stat,zipfile
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main")
dest=Path("/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/archive-01")
assert not dest.exists() and not dest.is_symlink()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
expected={'local-01/result.json':'476d893ba770a9faf323a61b7f1403c5999f4f00569b68d95b4620ff9b61a473','serialization-01/result.json':'861ccfa472deb1e08057fa57bec36fe245bd4ebfdcf51f13767fb7c06bc19d8f','sta-resume-01/result.json':'f3fbcfcfae5052860c263fbb2bc4e342de383d461163192bc27d33184bb31c7f','sta-resume-01/inputs.json':'da20a77b5cafadf1761e97bdabd5fc473063db714beac408992deb7bbf370995'}
for name,h in expected.items():assert sha(root/name)==h
states={n:json.loads((root/n).read_bytes()) for n in expected if n.endswith('result.json')}
assert all(r['status']=='FAILED' for r in states.values())
last=states['sta-resume-01/result.json']
assert 'TimeoutExpired' in last['error'] and last['inputs_unchanged'] and last['changed_inputs']==[]
assert len(last['commands'])==1
assert all(last['commands'][0][k] for k in ('cleanup_complete','reaped','group_absent'))
pinsdoc=json.loads((root/'sta-resume-01/inputs.json').read_bytes())
assert len(pinsdoc['originals'])==64 and len(pinsdoc['generated'])==4
pins={**pinsdoc['originals'],**pinsdoc['generated']};assert len(pins)==68
for p,h in pins.items():assert sha(p)==h,'changed input '+p
groups=[]
for pid in (31999,32000,32003,32075,32076,32077,32078,32266,32267):
 try:os.killpg(pid,0);exists=True
 except ProcessLookupError:exists=False
 assert not exists,'process group exists '+str(pid)
 groups.append(dict(pgid=pid,absent=True))
missing=['setup-checks.rpt','r2r.rpt','i2r.rpt','r2o.rpt','i2o.rpt','ready.rpt']
assert all(not (root/'sta-resume-01'/n).exists() for n in missing)
def inventory():
 result=[]
 for p in sorted(root.rglob('*')):
  s=p.lstat();assert not stat.S_ISLNK(s.st_mode),'unexpected symlink '+str(p)
  if stat.S_ISDIR(s.st_mode):continue
  assert stat.S_ISREG(s.st_mode)
  result.append(dict(path=p.relative_to(root).as_posix(),source=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p)))
 return result
before=inventory()
top=sorted(p.name for p in root.iterdir())
assert top==sorted(['input-01','local-01','input-serial-01','serialization-01','input-sta-01','input-sta-02','sta-resume-01'])
dest.mkdir(parents=True,exist_ok=False)
manifest=json.dumps(before,indent=2).encode()+b'\n';raw=dest/'raw.zip'
with zipfile.ZipFile(raw,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in before:z.write(f['source'],f['path'])
 z.writestr('MANIFEST.json',manifest)
with zipfile.ZipFile(raw) as z:
 assert len(z.namelist())==len(before)+1 and len(set(z.namelist()))==len(z.namelist()) and z.testzip() is None
 for f in before:
  b=z.read(f['path']);assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
 assert z.read('MANIFEST.json')==manifest
assert inventory()==before
for p,h in pins.items():assert sha(p)==h,'changed input after archive '+p
a=dict(status='FA_FAILED_RUNS_CLOSED_ARCHIVE_PASS',time=datetime.now(timezone.utc).isoformat(),files=len(before),raw_bytes=sum(f['bytes'] for f in before),raw=dict(bytes=raw.stat().st_size,sha256=sha(raw)),manifest_sha256=hashlib.sha256(manifest).hexdigest(),directories=top,all_member_sha_crc_verified=True,omitted_files=0,source_inventory_and_contents_unchanged=True,actual_input_pins_verified=68,closed_groups=groups,preserved_result_sha256=expected,sta_missing_reports=missing,new_eda_runs=0,new_fu_runs=0,new_builds=0,new_emu_runs=0,cpu_affinity=[2],nice=5,sta_qualified=False,ppa_qualified=False)
(dest/'audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a))
