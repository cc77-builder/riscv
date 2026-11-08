$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]2
$py=@'
import os,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{1});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k768-20261108-main');src=root/'input-01';out=root/'target-01'
items=json.loads("[{\"name\":\"run.py\",\"bytes\":25519,\"sha256\":\"984ff535756419240db26deaea96214b3ee98d65e30b0e10476abcd9cab06ac9\"},{\"name\":\"TARGET_CONTRACT.md\",\"bytes\":5429,\"sha256\":\"379fb985f0c403bea0245c7ffbebbc15a1177e1273a4ef34ba8519a3c3d655b3\"},{\"name\":\"source-derivation.json\",\"bytes\":2136,\"sha256\":\"b7ede00dad15845efb8f1079065af254537e001f436e1ea04b91107f1895e2dd\"}]")
for x in items:
 b=(src/x['name']).read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
profile_path=root/'preflight-01/profile.json';b=profile_path.read_bytes()
assert len(b)==93667 and hashlib.sha256(b).hexdigest()=='c8afad336dc289e76cb7055b6430399a3df77632232eed2dfc8e77e4c5b248f9'
p=json.loads(b)
assert p['contract']=='r3-prefix-k768-eight-window-regression-v1' and p['status']=='FROZEN_BEFORE_EMU'
assert p['k']==768 and p['fixture_kind']=='normal' and p['max_cycles']==6000000 and p['budget_seconds']==7200 and p['stream_limit_bytes']==16777216 and p['cpu']==1 and p['nice']==5
assert len(p['pins'])==457 and p['prefix_build_result_sha256']=='06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2' and p['prefix_smoke_result_sha256']=='2ec969938a8c4f790e10ba7067befe22f890946b58f2a533276d3051c0cc6eda'
assert p['runtime_source']==str(root/'preflight-01/inputs/run.py') and p['runtime_sha256']=='984ff535756419240db26deaea96214b3ee98d65e30b0e10476abcd9cab06ac9'
for path,h in p['pins'].items():
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,'input changed '+path
assert not out.exists() and not out.is_symlink()
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=2097152
assert shutil.disk_usage(root).free>=536870912
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
assert len(used)<=4,'aggregate CPU budget'
assert datetime.now(timezone.utc)<datetime(2026,11,8,5,10,tzinfo=timezone.utc),'latest approved start has passed'
if os.getpgrp()!=os.getpid():os.setsid()
argv=['/usr/bin/python3','-B',p['runtime_source'],'run','--profile',str(profile_path),'--profile-sha256','c8afad336dc289e76cb7055b6430399a3df77632232eed2dfc8e77e4c5b248f9','--output',str(out)]
print(json.dumps(dict(status='PREFIX_K768_LAUNCH',started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,profile_sha256=hashlib.sha256(b).hexdigest(),argv=argv)),flush=True)
os.execv(argv[0],argv)

'@
$start=[Diagnostics.ProcessStartInfo]::new()
$start.FileName='C:\Windows\System32\wsl.exe'
$start.UseShellExecute=$false
$start.CreateNoWindow=$true
$start.RedirectStandardOutput=$true
$start.RedirectStandardError=$true
foreach($item in @('--distribution','Ubuntu-22.04','--exec','/usr/bin/python3','-B','-c',$py)){[void]$start.ArgumentList.Add($item)}
$p=[Diagnostics.Process]::new();$p.StartInfo=$start;[void]$p.Start()
$errTask=$p.StandardError.ReadToEndAsync()
while($null -ne ($line=$p.StandardOutput.ReadLineAsync().GetAwaiter().GetResult())){[Console]::WriteLine($line)}
$p.WaitForExit()
$err=$errTask.GetAwaiter().GetResult();$code=$p.ExitCode
$p.Dispose()
if($err){[Console]::Error.Write($err)}
if($code -ne 0){throw ('WSL bounded operation exit '+$code)}
