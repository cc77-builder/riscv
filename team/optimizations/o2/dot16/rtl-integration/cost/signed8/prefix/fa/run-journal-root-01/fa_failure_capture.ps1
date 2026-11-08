$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
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
