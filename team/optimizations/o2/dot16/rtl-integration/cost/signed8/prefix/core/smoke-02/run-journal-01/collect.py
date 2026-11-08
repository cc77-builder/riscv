import hashlib,json,os,stat,time,zipfile
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main");run=root/'core-smoke-02';out=Path("/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-20261107-main/core-smoke-02-archive")
assert not out.exists() and not out.is_symlink()
def digest(f):
 h=hashlib.sha256()
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def pin(p):
 with p.open('rb') as f:return dict(bytes=p.stat().st_size,sha256=digest(f))
def inventory():
 rows={}
 for name in ('core-smoke-source-02','core-smoke-02'):
  for p in sorted((root/name).rglob('*')):
   m=p.lstat().st_mode;assert not stat.S_ISLNK(m),str(p)
   if stat.S_ISDIR(m):continue
   assert stat.S_ISREG(m),str(p)
   rows[p.relative_to(root).as_posix()]=pin(p)
 return rows
result=json.loads((run/'result.json').read_bytes())
assert result['status']=='PREFIX_FULLCORE_SIX_CASE_SMOKE_PASS'
assert all(result.get(k) is True for k in ('fullcore_smoke_qualified','inputs_unchanged','all_children_reaped'))
assert all(result.get(k) is False for k in ('fullcore_qualified','application_performance_qualified','ppa_qualified'))
assert [x['name'] for x in result['commands']]==['check-inputs-before','abi-build','abi-run','emulator','check-inputs-after']
assert all(x['exit_code']==0 and x['reaped'] and x['group_absent'] for x in result['commands'])
assert pin(run/'runtime-inputs.json')['sha256']==result['runtime_inputs_sha256']
inputs=json.loads((run/'runtime-inputs.json').read_bytes())
for path,h in inputs.items():assert pin(Path(path))['sha256']==h,path
for n,h in result['raw_logs_sha256'].items():assert pin(run/n)['sha256']==h,n
groups={26566}|{x['pid'] for x in result['commands']};live=[]
for p in Path('/proc').iterdir():
 if p.name.isdecimal():
  try:
   if int((p/'stat').read_text().rsplit(')',1)[1].split()[2]) in groups:live.append(int(p.name))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert not live,live
files=inventory();manifest=dict(schema=1,source=str(root),files=files,omissions=[],qualification='Archive transport only; original six-case qualification remains limited.')
mb=(json.dumps(manifest,indent=2)+'\n').encode()
out.mkdir(exist_ok=False);archive=out/'raw.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for n in files:z.write(root/n,n)
 z.writestr('ARCHIVE-MANIFEST.json',mb)
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(files)|{'ARCHIVE-MANIFEST.json'} and len(z.namelist())==len(files)+1
 assert z.read('ARCHIVE-MANIFEST.json')==mb
 for n,p in files.items():
  assert z.getinfo(n).file_size==p['bytes']
  with z.open(n) as f:assert digest(f)==p['sha256'],n
assert inventory()==files
for n in ('result.json','runtime-inputs.json','abi-layout.json','run.log'):
 (out/n).write_bytes((run/n).read_bytes());assert pin(out/n)==files['core-smoke-02/'+n]
audit=dict(status='PREFIX_CORE_SMOKE02_ARCHIVE_VERIFIED',time=datetime.now(timezone.utc).isoformat(),files=len(files),raw_bytes=sum(x['bytes'] for x in files.values()),raw=pin(archive),manifests={n:pin(out/n) for n in ('result.json','runtime-inputs.json','abi-layout.json','run.log')},originals_unchanged=True,all_member_sha_crc_verified=True,omitted_files=0,all_recorded_groups_absent=True,actual_runtime_input_pins_verified=len(inputs),commands=len(result['commands']),new_emu_runs=0,new_build_runs=0,cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0))
(out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
