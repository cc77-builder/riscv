$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,json,hashlib,subprocess,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/source-01')
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main")
dst=root/'input-01';out=root/'local-01'
items=json.loads("[{\"name\":\"fa_mapping.py\",\"bytes\":13081,\"sha256\":\"6716b4326a8e00e278e4bbd9088d6aafe4b2f6abf674c3a9a21f15e33244a2ce\"},{\"name\":\"fa_transform.py\",\"bytes\":9906,\"sha256\":\"5f5ee10d63ea1c2db3256fa4fa6f845ca2653eb1dd441e3ded910f86d6a1e36c\"},{\"name\":\"verify_csa.py\",\"bytes\":14051,\"sha256\":\"e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de\"},{\"name\":\"CONTRACT.md\",\"bytes\":3921,\"sha256\":\"41234f419562e0b27ef5a6e1ca31b28d9f18879500abe52fd37bce7b1efbe0ad\"}]")
assert not dst.exists() and not dst.is_symlink() and not out.exists()
original={}
for x in items:
 p=src/x['name'];assert stat.S_ISREG(p.lstat().st_mode);b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];original[x['name']]=b
dst.mkdir(parents=True,exist_ok=False)
for x in items:
 p=dst/x['name'];p.write_bytes(original[x['name']]);assert p.read_bytes()==original[x['name']]
argv=['/usr/bin/python3','-B',str(dst/'fa_mapping.py'),'--output',str(out)]
p=subprocess.run(argv,cwd=dst,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
(dst/'PLAN_ONLY.json').write_bytes(p.stdout);(dst/'PLAN_ONLY.stderr').write_bytes(p.stderr)
assert p.returncode==0,p.stderr.decode(errors='replace')
plan=json.loads(p.stdout);assert plan['status']=='PLAN_ONLY' and plan['output']==str(out)
assert not out.exists()
for x in items:assert (src/x['name']).read_bytes()==(dst/x['name']).read_bytes()==original[x['name']]
audit=dict(status='FA_X1_STAGED_PLAN_ONLY',files=items,total_bytes=sum(x['bytes'] for x in items),plan=dict(bytes=len(p.stdout),sha256=hashlib.sha256(p.stdout).hexdigest()),plan_exit=0,stderr_bytes=len(p.stderr),output_absent=True,sources_unchanged=True,new_eda_runs=0)
(dst/'SOURCE_STAGING.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))

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
