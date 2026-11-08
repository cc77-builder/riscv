$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
#!/usr/bin/env python3
"""Transport one closed Booth3 cost continuation without changing qualification."""
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import time
import zipfile

ROOT = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main')
OUT = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-booth3-20261108-main/cost-resume-01/archive-01')
EXPECTED_RESULT = '0bf4fc5a537394179bd347518c2adfe6d9631e3fda34b0ef2b0635a673a1b8d2'


def digest(stream):
    h = hashlib.sha256()
    for b in iter(lambda: stream.read(1048576), b''):
        h.update(b)
    return h.hexdigest()


def info(path):
    with path.open('rb') as f:
        return dict(bytes=path.stat().st_size, sha256=digest(f))


def inventory():
    files = {}
    for name in ('input-cost-01', 'cost-resume-01'):
        root = ROOT / name
        assert root.is_dir() and not root.is_symlink()
        for p in sorted(root.rglob('*')):
            mode = p.lstat().st_mode
            assert not stat.S_ISLNK(mode), str(p)
            if stat.S_ISDIR(mode):
                continue
            assert stat.S_ISREG(mode), str(p)
            files[p.relative_to(ROOT).as_posix()] = info(p)
    return files


def interrupted(sig, frame):
    raise InterruptedError(str(sig))


os.sched_setaffinity(0, {2})
os.setpriority(os.PRIO_PROCESS, 0, 5)
signal.signal(signal.SIGALRM, interrupted)
signal.alarm(90)
started = time.time()
assert not OUT.exists() and not OUT.is_symlink()
run = ROOT/'cost-resume-01'
result = json.loads((run/'result.json').read_bytes())
assert info(run/'result.json')['sha256'] == EXPECTED_RESULT
assert result['contract'] == 'dot16-booth3-one-shot-cost-continuation-v1'
assert result['status'] in ('FAILED','BOOTH3_SERIALIZED_TWO_FEATURE_COST_COMPLETE')
assert result['prior_result_sha256'] == '63cee9334942c7e60405cef939ef3020b1817e5ee147cc7e12b22339884d9121'
assert result['prior_status_preserved'] == 'FAILED'
assert not any(result[k] for k in ('new_rtl','new_gold','new_fu_runs','new_core_runs','feature0_new_mapping_runs','parent_qualified','fullcore_qualified','application_performance_qualified','core_cost_qualified','production_default_changed'))
assert result['local_cost_recorded'] == (result['status']=='BOOTH3_SERIALIZED_TWO_FEATURE_COST_COMPLETE')
assert result['inputs_unchanged'] and not result['changed_inputs'] and result['all_children_reaped']
inputs=json.loads((run/'inputs.json').read_bytes())
originals=inputs['originals']
for path,h in originals.items(): assert info(Path(path))['sha256']==h,'changed original '+path
stage=ROOT/'input-cost-01/SOURCE_STAGING.json'
assert info(stage)['sha256']=='9d874b240e85db056d0aed0bcd6162beca73b11909a60ac4b7cae9e34044a6bf'
stagefiles=json.loads(stage.read_bytes())['files']
for x in stagefiles:
 p=ROOT/'input-cost-01'/x['path'];i=info(p);assert i['bytes']==x['bytes'] and i['sha256']==x['sha256']
assert all(c['reaped'] and c['group_absent'] for c in result['commands'])
expected_pids = {37118} | {c['pid'] for c in result['commands']}
live_groups=[]
for p in Path('/proc').iterdir():
 if p.name.isdecimal():
  try:
   fields=(p/'stat').read_text().rsplit(')',1)[1].split()
   if int(fields[2]) in expected_pids:live_groups.append(int(p.name))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert not live_groups,live_groups
files=inventory()
recorded=json.loads((run/'artifact-pins.json').read_bytes())['files']
actual_recorded={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name not in ('result.json','artifact-pins.json')}
assert set(recorded)==actual_recorded,'complete recorded artifact inventory'
for name,rec in recorded.items():
 assert files['cost-resume-01/'+name]==rec,name
for path,h in inputs['snapshots'].items(): assert info(Path(path))['sha256']==h,path
OUT.mkdir(parents=True,exist_ok=False)
manifest=dict(schema=1,files=files,omissions=[],source=str(ROOT),qualification='Byte transport only; original qualification remains unchanged.')
manifest_bytes=(json.dumps(manifest,indent=2)+'\n').encode()
archive=OUT/'raw.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for name in files:z.write(ROOT/name,name)
 z.writestr('ARCHIVE-MANIFEST.json',manifest_bytes)
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(files)+1 and set(z.namelist())==set(files)|{'ARCHIVE-MANIFEST.json'}
 assert z.read('ARCHIVE-MANIFEST.json')==manifest_bytes
 for name,rec in files.items():
  assert z.getinfo(name).file_size==rec['bytes']
  with z.open(name) as f:assert digest(f)==rec['sha256'],name
assert inventory()==files,'source changed during archive'
for path,h in originals.items():assert info(Path(path))['sha256']==h,'changed original after archive '+path
summary_names=[n for n in files if n.startswith('cost-resume-01/') and (len(Path(n).parts)==2 or n.endswith('.rpt') or n.endswith('/graph-audit.json'))]
with zipfile.ZipFile(OUT/'summary.zip','x',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for name in summary_names:z.write(ROOT/name,name)
 z.writestr('ARCHIVE-MANIFEST.json',manifest_bytes)
with zipfile.ZipFile(OUT/'summary.zip') as z:
 assert len(z.namelist())==len(summary_names)+1
 for name in summary_names:
  assert z.getinfo(name).file_size==files[name]['bytes']
  with z.open(name) as f:assert digest(f)==files[name]['sha256']
copies={}
for name in summary_names:
 relative=Path(name).relative_to('cost-resume-01')
 dst=OUT/'evidence'/relative;dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write((ROOT/name).read_bytes())
 assert info(dst)==files[name]
 copies[str(Path('evidence')/relative)]=info(dst)
audit=dict(status='BOOTH3_COST_CONTINUATION_ARCHIVE_VERIFIED',source_unchanged=True,
 files=len(files),raw_bytes=sum(x['bytes'] for x in files.values()),raw=info(archive),summary=info(OUT/'summary.zip'),
 copied_evidence=copies,commands=len(result['commands']),original_input_pins_verified=len(originals),
 staged_input_files_verified=len(stagefiles),recorded_artifact_pins_verified=len(recorded),
 original_run_status=result['status'],complete_cost_qualification=result['local_cost_recorded'],
 feature0_new_mapping_runs=result['feature0_new_mapping_runs'],feature1_new_mapping_runs=result['feature1_new_mapping_runs'],
 all_recorded_process_groups_absent=True,omitted_files=0,members_sha_and_crc_verified=True,new_eda_runs=0,new_guest_runs=0,
 cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),elapsed_seconds=time.time()-started)
assert audit['elapsed_seconds']<90
with (OUT/'audit.json').open('xb') as f:f.write((json.dumps(audit,indent=2)+'\n').encode())
signal.alarm(0)
print(json.dumps(audit),flush=True)

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
