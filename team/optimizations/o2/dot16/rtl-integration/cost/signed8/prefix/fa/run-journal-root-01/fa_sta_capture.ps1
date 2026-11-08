$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,json,hashlib,stat,re
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main')
dst=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/sta-resume-input-review-01')
assert not dst.exists() and not dst.is_symlink()
paths=[root/'serialization-01'/n for n in ('result.json','inputs.json','serialize.ys','reparse.ys','splitnets-help.log','serialize.log','reparse.log','split.json','reparsed.json','mapped.v','timing.tcl')]
paths+=[root/'local-01/timing.tcl',root/'local-01/mapped.json']
before={str(p):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
assert before[str(root/'serialization-01/result.json')]['sha256']=='861ccfa472deb1e08057fa57bec36fe245bd4ebfdcf51f13767fb7c06bc19d8f'
result=json.loads((root/'serialization-01/result.json').read_bytes())
assert result['status']=='FAILED' and len(result['commands'])==3
groups=[]
for pid in [32075]+[x['pid'] for x in result['commands']]:
 try:os.killpg(pid,0);exists=True
 except ProcessLookupError:exists=False
 assert not exists;groups.append(dict(pgid=pid,absent=True))
assert not re.search(r'(?m)^\s*assign\s*\{',(root/'serialization-01/mapped.v').read_text())
dst.mkdir(parents=True,exist_ok=False);copied=[]
for p in paths:
 if p.name in ('split.json','reparsed.json','mapped.json','mapped.v'):continue
 n=p.parent.name+'--'+p.name;b=p.read_bytes();(dst/n).write_bytes(b);assert (dst/n).read_bytes()==b;copied.append(n)
assert all(p.stat().st_size==before[str(p)]['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==before[str(p)]['sha256'] for p in paths)
a=dict(status='CLOSED_SERIALIZATION_INPUT_REVIEW',files=before,copied_files=copied,closed_groups=groups,inputs_unchanged=True,concat_lhs_absent=True,new_eda_runs=0)
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
