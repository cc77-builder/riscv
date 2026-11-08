$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
#!/usr/bin/env python3
"""Archive the failed Booth3 point, preserving its R20 solver timeout unchanged."""
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import time
import zipfile

ROOT = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main')
OUT = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-booth3-20261108-main/archive-01')
EXPECTED_SOURCE = '880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680'


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
    for name in ('input-01', 'local-01'):
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
signal.alarm(300)
started = time.time()
assert not OUT.exists() and not OUT.is_symlink()
run = ROOT / 'local-01'
result = json.loads((run / 'result.json').read_bytes())
assert info(run/'result.json')['sha256']=='7eb958143cc41f98cad195e0e7089b8924f827af340c51abca18ba573174d050'
assert result['status']=='FAILED' and result['candidate_source_sha256']==EXPECTED_SOURCE
assert result['contract']=='dot16-prefix-booth3-local-v1' and result['candidate_wrapper_sha256']=='1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238'
assert len(result['commands'])==8 and not result['fu_results'] and not result['cost_results']
assert not result['arithmetic_equivalent'] and not result['fu_qualified'] and not result['local_cost_recorded']
assert len(result['prefix_miters'])==2 and result['prefix_miters'][0]['status']=='PASS' and result['prefix_miters'][1]['status']=='FAILED'
assert result['prefix_miters'][0]['row_count']==3 and result['prefix_miters'][1]['row_count']==6
assert not result['prefix_miters'][1]['counterexample_found'] and not result['prefix_miters'][1]['solver_equivalence_proved']
assert 'ERROR: Called with -verify and proof did time out!' in (run/'actual-prefix-20-miter.log').read_text()
assert not (run/'final-artifact-pins.json').exists()
originals=json.loads((run/'inputs.json').read_bytes())['originals']
for path,h in originals.items():assert info(Path(path))['sha256']==h,'changed original '+path
stage=ROOT/'input-01/SOURCE_STAGING.json'
assert info(stage)['sha256']=='85b716d1851f26097838abdb274af7085cfa8ced6b467765d304e6cf99f208b1'
for x in json.loads(stage.read_bytes())['files']:
 p=ROOT/'input-01'/x['path'];i=info(p);assert i['bytes']==x['bytes'] and i['sha256']==x['sha256']
assert all(c['reaped'] and c['group_absent'] for c in result['commands'])
expected_pids = {34299} | {c['pid'] for c in result['commands']}
live_groups = []
for p in Path('/proc').iterdir():
    if p.name.isdecimal():
        try:
            fields = (p/'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) in expected_pids:
                live_groups.append(int(p.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
assert not live_groups, live_groups
files = inventory()
recorded={**json.loads((run/'inputs.json').read_bytes())['snapshots'],**json.loads((run/'overlay-classes.json').read_bytes())}
for entry in result['generated']:
 folder=run/(entry['kind']+'-feature'+str(entry['feature']))/'rtl'
 for f in entry['files']:
  path=run/f['path'];assert path.stat().st_size==f['bytes'];recorded[str(path)]=f['sha256']
 recorded[str(folder/'filelist.f')]=entry['filelist_sha256']
 recorded[str(folder/'firrtl_black_box_resource_files.f')]=entry['resource_manifest_sha256']
for m in result['prefix_miters']:
 width=m['width'];folder=run/('prefix-proof-'+str(width))
 for n,k in (('gold.sv','gold_sha256'),('gate.sv','gate_sha256'),('prove.ys','script_sha256')):recorded[str(folder/n)]=m[k]
 recorded[str(run/('actual-prefix-'+str(width)+'-miter.log'))]=m['log_sha256']
 recorded[str(run/('cost-feature'+str(m['feature']))/'rtl'/('VDotPrefixFinish'+str(width)+'.sv'))]=m['actual_rtl_sha256']
for path,h in recorded.items():
 p=Path(path);assert p.is_relative_to(run)
 assert files[p.relative_to(ROOT).as_posix()]['sha256']==h,str(p)
OUT.mkdir(parents=True, exist_ok=False)
manifest = dict(schema=1, files=files, omissions=[], source=str(ROOT),
                elapsed_engineering_seconds=None,
                qualification='Byte transport only; original qualification remains unchanged.')
manifest_bytes = (json.dumps(manifest, indent=2)+'\n').encode()
archive = OUT/'raw.zip'
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=3) as z:
    for name in files:
        z.write(ROOT/name, name)
    z.writestr('ARCHIVE-MANIFEST.json', manifest_bytes)
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist()) == len(files)+1
    assert set(z.namelist()) == set(files)|{'ARCHIVE-MANIFEST.json'}
    assert z.read('ARCHIVE-MANIFEST.json') == manifest_bytes
    for name, record in files.items():
        assert z.getinfo(name).file_size == record['bytes']
        with z.open(name) as f:
            assert digest(f) == record['sha256'], name
assert inventory() == files, 'source tree changed during transport'
for path,h in originals.items():assert info(Path(path))['sha256']==h,'changed original after archive '+path
summary_names = [n for n in files if n.startswith('local-01/') and
                 (len(Path(n).parts) == 2 or n.endswith('.rpt'))]
with zipfile.ZipFile(OUT/'summary.zip', 'x', zipfile.ZIP_DEFLATED, compresslevel=3) as z:
    for name in summary_names:
        z.write(ROOT/name, name)
    z.writestr('ARCHIVE-MANIFEST.json', manifest_bytes)
with zipfile.ZipFile(OUT/'summary.zip') as z:
    assert len(z.namelist()) == len(summary_names)+1
    for name in summary_names:
        assert z.getinfo(name).file_size == files[name]['bytes']
        with z.open(name) as f:
            assert digest(f) == files[name]['sha256']
copy_names=('result.json','inputs.json','overlay-classes.json','arithmetic-structure.json','actual-prefix-19-miter.log','actual-prefix-20-miter.log')
for name in copy_names:
 with (OUT/name).open('xb') as f:f.write((run/name).read_bytes())
 assert info(OUT/name)==files['local-01/'+name]
folder=OUT/'actual-rtl';folder.mkdir()
for feature in (0,1):
 name='VDotPrefixFinish'+str(20 if feature else 19)+'.sv'
 src=run/('cost-feature'+str(feature))/'rtl'/name;dst=folder/name
 with dst.open('xb') as f:f.write(src.read_bytes())
 assert info(dst)==files[src.relative_to(ROOT).as_posix()]
audit = dict(status='BOOTH3_FAILED_ARCHIVE_VERIFIED', source_unchanged=True,
             files=len(files), raw_bytes=sum(x['bytes'] for x in files.values()),
             raw=info(archive), summary=info(OUT/'summary.zip'),
             manifests={n:files['local-01/'+n] for n in copy_names},
             commands=8, original_input_pins_verified=len(originals), all_23_staged_inputs_verified=True, recorded_artifact_pins_verified=len(recorded), missing_final_success_manifest=True, original_run_status='FAILED', failure_category='R20_SAT_SOLVER_TIMEOUT', retry_performed=False, all_recorded_process_groups_absent=True, omitted_files=0,
             members_sha_and_crc_verified=True, new_eda_runs=0, new_guest_runs=0,
             cpu_affinity=sorted(os.sched_getaffinity(0)), nice=os.getpriority(os.PRIO_PROCESS, 0),
             elapsed_seconds=time.time()-started)
assert audit['elapsed_seconds'] < 300
with (OUT/'audit.json').open('xb') as f:
    f.write((json.dumps(audit, indent=2)+'\n').encode())
signal.alarm(0)
print(json.dumps(audit), flush=True)

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
