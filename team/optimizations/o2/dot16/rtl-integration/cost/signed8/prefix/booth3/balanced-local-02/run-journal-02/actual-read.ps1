$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,json,hashlib
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
r=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/local-02")
def info(p):
 b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
j=json.loads((r/'result.json').read_bytes())
d={k:v for k,v in j.items() if k not in ('generated','commands','source_files','input_pins')}
d['commands']=[{k:v for k,v in c.items() if k not in ('env','environment')} for c in j['commands']]
d['result_file']=info(r/'result.json')
d['top_files']=[dict(path=str(p.relative_to(r)),**info(p)) for p in sorted(r.iterdir()) if p.is_file()]
d['cost_files']=[dict(path=str(p.relative_to(r)),**info(p)) for p in sorted(r.rglob('*')) if p.is_file() and ('sta' in p.name or p.suffix=='.rpt')]
d['sta_logs']={str(p.relative_to(r)):p.read_text() for p in sorted(r.rglob('*sta*.log'))}
print(json.dumps(d))

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
