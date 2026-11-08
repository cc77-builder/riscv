$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main");src=root/'input-serial-01';out=root/'serialization-01'
items=json.loads("[{\"name\":\"fa_serialization.py\",\"bytes\":13071,\"sha256\":\"82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a\"},{\"name\":\"SERIALIZATION_CONTRACT.md\",\"bytes\":2047,\"sha256\":\"00db43f49848377d5c01bcec6eb008faf79a96e3956317cfdc0e045de60b1d1c\"}]")
for x in items:
 b=(src/x['name']).read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
p=(src/'PLAN_ONLY.json').read_bytes();assert len(p)==12887 and hashlib.sha256(p).hexdigest()=='38967267758c4a76589b0af1bb3d73708d425a5628a15db7461f1a207e5613cb'
q=json.loads(p);assert q['status']=='PLAN_ONLY' and q['output']==str(out)
for path,h in q['original_pins'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,'plan-frozen input changed '+path
assert not out.exists() and not out.is_symlink()
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=2097152
assert shutil.disk_usage(root).free>=536870912
heavy=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:
  name=(p/'comm').read_text().strip()
  if name in ('java','emu','yosys','berkeley-abc','sta','verilator_bin','clang','clang++','make','cc1plus'):
   aff=sorted(os.sched_getaffinity(int(p.name)));heavy.append(dict(pid=int(p.name),name=name,affinity=aff));assert 2 not in aff,'CPU2 engineering conflict '+str(p)
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
used={2}
for x in heavy:used.update(x['affinity'])
assert len(used)<=4,'aggregate CPU budget'
if os.getpgrp()!=os.getpid():os.setsid()
argv=['/usr/bin/python3','-B',str(src/'fa_serialization.py'),'--execute']
print(json.dumps(dict(status='FA_SERIALIZATION_LAUNCH',started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,mapped_json_sha256=q['original_pins'][str(root/'local-01/mapped.json')],argv=argv)),flush=True)
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
$outTask=$p.StandardOutput.ReadToEndAsync();$errTask=$p.StandardError.ReadToEndAsync()
$p.WaitForExit()
$out=$outTask.GetAwaiter().GetResult();$err=$errTask.GetAwaiter().GetResult();$code=$p.ExitCode
$p.Dispose()
[Console]::Write($out)
if($err){[Console]::Error.Write($err)}
if($code -ne 0){throw ('WSL bounded operation exit '+$code)}
