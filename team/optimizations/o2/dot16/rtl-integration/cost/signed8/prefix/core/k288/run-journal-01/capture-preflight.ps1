$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,json,hashlib,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k288-20261108-main')
dst=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-k288-20261108-main/preflight-review-01')
assert not dst.exists() and not dst.is_symlink()
paths={'profile.json':root/'preflight-01/profile.json','result.json':root/'preflight-01/result.json','SOURCE_STAGING.json':root/'input-02/SOURCE_STAGING.json','PREFLIGHT.stdout':root/'input-02/PREFLIGHT.stdout','PREFLIGHT.stderr':root/'input-02/PREFLIGHT.stderr'}
data={n:p.read_bytes() for n,p in paths.items()}
assert hashlib.sha256(data['profile.json']).hexdigest()=='ff1fede1efbd70926b6f3ddb00ba1579efcba8a059b8292e514e7888215ffc8c'
q=json.loads(data['profile.json']);assert q['status']=='FROZEN_BEFORE_EMU' and len(q['pins'])==457
assert q['runtime_sha256']=='d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3'
assert q['max_cycles']==4000000 and q['budget_seconds']==9000 and q['stream_limit_bytes']==16777216
dst.mkdir(parents=True,exist_ok=False);rows=[]
for n,p in paths.items():
 b=data[n];assert stat.S_ISREG(p.lstat().st_mode);(dst/n).write_bytes(b);assert (dst/n).read_bytes()==b and p.read_bytes()==b
 rows.append(dict(source=str(p),name=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
a=dict(status='K288_PREFLIGHT_CLOSED_CAPTURE',files=rows,source_unchanged=True,emu_runs=0,profile_pins=len(q['pins']),runtime=q['runtime_source'],emu=q['emu'])
(dst/'audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a))

'@
$start=[Diagnostics.ProcessStartInfo]::new()
$start.FileName='C:\Windows\System32\wsl.exe'
$start.UseShellExecute=$false
$start.CreateNoWindow=$true
$start.RedirectStandardOutput=$true
$start.RedirectStandardError=$true
foreach($item in @('--distribution','Ubuntu-22.04','--exec','/usr/bin/python3','-B','-c',$py)){[void]$start.ArgumentList.Add($item)}
$p=[Diagnostics.Process]::new();$p.StartInfo=$start;[void]$p.Start()
$outTask=$p.StandardOutput.ReadToEndAsync();$errTask=$p.StandardError.ReadToEndAsync()
$p.WaitForExit()
$out=$outTask.GetAwaiter().GetResult();$err=$errTask.GetAwaiter().GetResult();$code=$p.ExitCode
$p.Dispose()
[Console]::Write($out)
if($err){[Console]::Error.Write($err)}
if($code -ne 0){throw ('WSL bounded operation exit '+$code)}
