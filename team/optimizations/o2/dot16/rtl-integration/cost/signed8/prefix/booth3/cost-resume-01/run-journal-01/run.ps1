$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,sys,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/input-cost-01")
pins=json.loads("[{\"path\":\"CONTRACT.md\",\"bytes\":4319,\"sha256\":\"fc6267cc664d900c143e21017f96b6adcab401c03aae642e00032a9a291fcfe0\"},{\"path\":\"FIXED_INPUTS.json\",\"bytes\":2878,\"sha256\":\"6766593ac8cf131c2326ac40f5236ec8c16968d4178eb5e27dedfbe51716bcde\"},{\"path\":\"REVIEW-controller.md\",\"bytes\":3901,\"sha256\":\"46f902acd4b1420a4a04023157b4bcabcf4661df0d9b8dd55f7086e7d784a3b6\"},{\"path\":\"REVIEW-graph.md\",\"bytes\":6518,\"sha256\":\"fc801be2f67e6534d2835c23d9f1cfc9ad00bb9164c03fcc7e816ab32e17d402\"},{\"path\":\"cost_resume.py\",\"bytes\":21597,\"sha256\":\"317f1919138e0c2e69c9d48514667fe82a871a0ec4caf8d6cc5fb206390f594a\"},{\"path\":\"review-pro2/REVIEW.md\",\"bytes\":6777,\"sha256\":\"b3895d3c46dc34a397f8badb027f786f7a1de36151c2098f1eb5f8cf44e5fa57\"},{\"path\":\"review-pro2/actual-read.json\",\"bytes\":8235,\"sha256\":\"25c447e1241baeb0408b806b494a4015300ae6cd4aaf00b25cee5e9c6608832c\"},{\"path\":\"review-pro2/read-receipts.json\",\"bytes\":25419,\"sha256\":\"3af967f8022249ab97ccfc8440ca318775223a99116f1072b2c51a264a24481e\"}]")
for item in pins:
 p=root/item['path'];b=p.read_bytes()
 assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],str(p)
stage=root/'SOURCE_STAGING.json';sb=stage.read_bytes()
assert len(sb)==1675 and hashlib.sha256(sb).hexdigest()=='9d874b240e85db056d0aed0bcd6162beca73b11909a60ac4b7cae9e34044a6bf','exact staging receipt'
s=json.loads(sb)
assert s['status']=='BOOTH3_COST_INPUT_STAGING_VERIFIED' and s['files']==pins and s['source_unchanged'] and s['all_bytes_verified'] and s['new_runtime_commands']==0
out=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/cost-resume-01");assert not out.exists() and not out.is_symlink(),'output already exists'
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()}
assert mem['MemAvailable']>=6*1024*1024,'less than6GiB available; no controller launch'
assert shutil.disk_usage(root).free>=536870912,'less than512MiB free; no controller launch'
heavy=[]
for q in Path('/proc').iterdir():
 if not q.name.isdecimal():continue
 try:
  name=(q/'comm').read_text().strip()
  if name in ('java','emu','yosys','berkeley-abc','sta','verilator_bin','clang','clang++','clang++-19','make','cc1plus','ninja'):
   aff=sorted(os.sched_getaffinity(int(q.name)));heavy.append(dict(pid=int(q.name),name=name,affinity=aff))
   assert 2 not in aff,'CPU2 engineering conflict '+str(q)
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
used={2}
for x in heavy:used.update(x['affinity'])
assert len(used)<=4,'aggregate CPU budget'
assert datetime.now(timezone.utc)<datetime(2026,11,8,7,10,tzinfo=timezone.utc),'latest planned actual start passed'
if os.getpgrp()!=os.getpid():os.setsid()
argv=['/usr/bin/python3','-B',str(root/'cost_resume.py'),'--execute']
print(json.dumps(dict(status='BOOTH3_COST_LAUNCH',started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,source_staging_sha256=hashlib.sha256(sb).hexdigest(),input_files=len(pins),argv=argv)),flush=True)
os.chdir(root)
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
