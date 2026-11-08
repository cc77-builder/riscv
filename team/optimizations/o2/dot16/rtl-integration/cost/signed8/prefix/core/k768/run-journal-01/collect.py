import os,json,hashlib,stat,zipfile,time
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{1});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k768-20261108-main')
dest=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-k768-20261108-main/archive-01')
assert not dest.exists() and not dest.is_symlink()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
profile_path=root/'preflight-01/profile.json'
assert profile_path.stat().st_size==93667 and sha(profile_path)=='c8afad336dc289e76cb7055b6430399a3df77632232eed2dfc8e77e4c5b248f9'
profile=json.loads(profile_path.read_bytes());status=json.loads((root/'target-01/status.json').read_bytes())
assert status['status']=='PACKED_WS_EIGHT_WINDOW_TARGET_PASS' and status['contract']=='r3-prefix-k768-eight-window-regression-v1'
assert status['target_runtime_qualified'] and status['input_identities_unchanged'] and not status['changed_inputs']
assert status['process_reaped'] and status['process_group_absent'] and status['exit_code']==0 and status['signals']==dict(first=None,count=0)
assert status['checks_sha256']=='4c0f3bd2254ec4043d996635718ac6e7751d2d0d118332a70bb16fa8889e1775'==sha(root/'target-01/checks.json')
for name,desc in status['raw_logs'].items():
 p=root/'target-01'/name;assert p.stat().st_size==desc['bytes'] and sha(p)==desc['sha256']
assert len(profile['pins'])==457
for path,h in profile['pins'].items():assert sha(path)==h,'input changed '+path
groups=[]
for pid in (32395,32396):
 try:os.killpg(pid,0);exists=True
 except ProcessLookupError:exists=False
 assert not exists;groups.append(dict(pgid=pid,absent=True))
def inventory():
 result=[]
 for label in ('input-01','preflight-01','target-01'):
  folder=root/label;assert folder.is_dir() and not folder.is_symlink()
  for p in sorted(folder.rglob('*')):
   s=p.lstat();assert not stat.S_ISLNK(s.st_mode)
   if stat.S_ISDIR(s.st_mode):continue
   assert stat.S_ISREG(s.st_mode)
   result.append(dict(path=p.relative_to(root).as_posix(),source=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p)))
 return result
before=inventory();dest.mkdir(parents=True,exist_ok=False);rawzip=dest/'raw.zip'
manifest=json.dumps(before,indent=2).encode()+b'\n'
with zipfile.ZipFile(rawzip,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for x in before:z.write(x['source'],x['path'])
 z.writestr('MANIFEST.json',manifest)
with zipfile.ZipFile(rawzip) as z:
 assert len(z.namelist())==len(before)+1 and len(set(z.namelist()))==len(z.namelist()) and z.testzip() is None
 for x in before:
  b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert z.read('MANIFEST.json')==manifest
assert inventory()==before
for path,h in profile['pins'].items():assert sha(path)==h,'input changed after archive '+path
for name,src in [('status.json',root/'target-01/status.json'),('checks.json',root/'target-01/checks.json'),('profile.json',profile_path),('stdout.log',root/'target-01/stdout.log')]:
 b=src.read_bytes();(dest/name).write_bytes(b);assert (dest/name).read_bytes()==b
a=dict(status='PREFIX_K768_CLOSED_ARCHIVE_PASS',time=datetime.now(timezone.utc).isoformat(),files=len(before),raw_bytes=sum(x['bytes'] for x in before),raw=dict(bytes=rawzip.stat().st_size,sha256=sha(rawzip)),manifest_sha256=hashlib.sha256(manifest).hexdigest(),all_member_sha_crc_verified=True,omitted_files=0,source_inventory_and_contents_unchanged=True,actual_input_pins_verified=457,closed_groups=groups,new_emu_runs=0,new_builds=0,cpu_affinity=[1],nice=5,profile_sha256=sha(profile_path),status_sha256=sha(root/'target-01/status.json'),checks_sha256=sha(root/'target-01/checks.json'))
(dest/'audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a))
