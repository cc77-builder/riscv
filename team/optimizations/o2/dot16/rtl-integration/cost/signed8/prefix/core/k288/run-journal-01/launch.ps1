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
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k288-20261108-main');src=root/'input-02';out=root/'target-01'
items=json.loads("[{\"name\":\"run.py\",\"bytes\":25519,\"sha256\":\"d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3\"},{\"name\":\"TARGET_CONTRACT.md\",\"bytes\":4024,\"sha256\":\"18f5b8b22e5be4ccd98a8cc854662376f90210e1c4dbfa55fae4402f50c07447\"},{\"name\":\"source-derivation.json\",\"bytes\":8680,\"sha256\":\"1dabc73f6a113da24991870b08866af50a72039f9ad4f80bfb8d0a485a75749a\"}]")
for x in items:
 b=(src/x['name']).read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
profile_path=root/'preflight-01/profile.json';b=profile_path.read_bytes()
assert len(b)==93672 and hashlib.sha256(b).hexdigest()=='ff1fede1efbd70926b6f3ddb00ba1579efcba8a059b8292e514e7888215ffc8c'
p=json.loads(b)
assert p['contract']=='r3-prefix-k288-eight-window-regression-v1' and p['status']=='FROZEN_BEFORE_EMU'
assert p['k']==288 and p['fixture_kind']=='normal-0' and p['max_cycles']==4000000 and p['budget_seconds']==9000 and p['stream_limit_bytes']==16777216 and p['cpu']==1 and p['nice']==5
assert len(p['pins'])==457 and p['prefix_build_result_sha256']=='06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2' and p['prefix_smoke_result_sha256']=='2ec969938a8c4f790e10ba7067befe22f890946b58f2a533276d3051c0cc6eda'
assert p['runtime_source']==str(root/'preflight-01/inputs/run.py') and p['runtime_sha256']=='d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3'
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
assert datetime.now(timezone.utc)<datetime(2026,11,8,4,30,tzinfo=timezone.utc),'latest approved start has passed'
if os.getpgrp()!=os.getpid():os.setsid()
argv=['/usr/bin/python3','-B',p['runtime_source'],'run','--profile',str(profile_path),'--profile-sha256','ff1fede1efbd70926b6f3ddb00ba1579efcba8a059b8292e514e7888215ffc8c','--output',str(out)]
print(json.dumps(dict(status='PREFIX_K288_LAUNCH',started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,profile_sha256=hashlib.sha256(b).hexdigest(),argv=argv)),flush=True)
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
