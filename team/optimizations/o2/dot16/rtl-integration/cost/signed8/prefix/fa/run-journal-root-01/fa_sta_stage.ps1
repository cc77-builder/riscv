$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]8
$py=@'
import os,json,hashlib,subprocess,stat
from pathlib import Path
os.sched_setaffinity(0,{3});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/sta-resume-source-01')
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main');dst=root/'input-sta-01';out=root/'sta-resume-01'
items=json.loads("[{\"name\":\"fa_sta_resume.py\",\"bytes\":16152,\"sha256\":\"efba4c76e503cc4319c6e3b04d8abcf6c5e28c6b7bd3373220228ed07605348f\"},{\"name\":\"STA_RESUME_CONTRACT.md\",\"bytes\":4065,\"sha256\":\"8eca702338c12ac015d103e59350205753be755c408fb25d468b6d418138ad7b\"}]")
assert not dst.exists() and not dst.is_symlink() and not out.exists()
original={}
for x in items:
 p=src/x['name'];assert stat.S_ISREG(p.lstat().st_mode);b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];original[x['name']]=b
dst.mkdir(parents=True,exist_ok=False)
for x in items:
 p=dst/x['name'];p.write_bytes(original[x['name']]);assert p.read_bytes()==original[x['name']]
argv=['/usr/bin/python3','-B',str(dst/'fa_sta_resume.py')]
p=subprocess.run(argv,cwd=dst,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
(dst/'PLAN_ONLY.json').write_bytes(p.stdout);(dst/'PLAN_ONLY.stderr').write_bytes(p.stderr)
for x in items:assert (src/x['name']).read_bytes()==(dst/x['name']).read_bytes()==original[x['name']]
audit=dict(status='FA_STA_RESUME_STAGED_PLAN',files=items,plan=dict(bytes=len(p.stdout),sha256=hashlib.sha256(p.stdout).hexdigest()),plan_exit=p.returncode,stderr_bytes=len(p.stderr),output_absent=not out.exists(),sources_unchanged=True,new_eda_runs=0)
(dst/'SOURCE_STAGING.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
if p.returncode: print(p.stderr.decode(errors='replace'),file=__import__('sys').stderr)
assert p.returncode==0,'plan failed; no STA started'
plan=json.loads(p.stdout);assert plan['status']=='PLAN_ONLY' and plan['output']==str(out) and plan['new_yosys_runs']==0 and not out.exists()
print(json.dumps(dict(graph=plan['graph_audit'],cell_area=plan['cell_area'],cell_count=plan['cell_count'],input_pins=len(plan['original_pins']))))

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
