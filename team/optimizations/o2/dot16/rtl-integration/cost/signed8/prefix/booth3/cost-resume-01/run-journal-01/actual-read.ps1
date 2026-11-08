$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,json,hashlib
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/cost-resume-01")
def rec(p):
 b=p.read_bytes();return dict(path=str(p.relative_to(root)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
r=json.loads((root/'result.json').read_bytes())
r['result_file']=rec(root/'result.json')
r['top_files']=[rec(p) for p in sorted(root.iterdir()) if p.is_file()]
r['graph_audits']=[dict(file=rec(p),audit=json.loads(p.read_bytes())) for p in sorted(root.glob('feature*/serialized/graph-audit.json'))]
r['sta_logs']=[dict(file=rec(p),text=p.read_text(errors='replace')) for p in sorted(root.glob('sta-*.log'))]
print(json.dumps(r))

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
