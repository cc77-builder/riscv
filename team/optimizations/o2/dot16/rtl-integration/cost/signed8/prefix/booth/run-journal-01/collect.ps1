$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
#!/usr/bin/env python3
"""Archive the closed Booth9 experiment byte for byte, without running EDA."""
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import time
import zipfile

ROOT = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth-20261108-main')
OUT = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-booth-20261108-main/archive-01')
EXPECTED_SOURCE = 'f0a8bbe58440c6113aa56f848387c6b4e4a487d71ec2832a1e43fca55d3a8245'


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
assert result['status'] == 'BOOTH_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE'
assert result['candidate_source_sha256'] == EXPECTED_SOURCE
assert result['all_children_reaped'] and result['inputs_unchanged']
assert result['generated_inputs_unchanged'] and result['original_classpath_unchanged']
assert len(result['commands']) == 32
assert result['contract']=='dot16-prefix-booth9-local-v1' and result['candidate_wrapper_sha256']=='0fcc5df10355ee1e6382678ba40bc9d7ddf830b560dcc469c46e6a6888441556'
assert result['arithmetic_equivalent'] and result['fu_qualified'] and result['local_cost_recorded']
originals=json.loads((run/'inputs.json').read_bytes())['originals']
for path,h in originals.items():assert info(Path(path))['sha256']==h,'changed original '+path
stage=ROOT/'input-01/SOURCE_STAGING.json'
assert info(stage)['sha256']=='1d62de7b316c4a5345870922c7a3dfdf313186d8573aaa49b3f9d4b9c811513a'
for x in json.loads(stage.read_bytes())['files']:
 p=ROOT/'input-01'/x['path'];i=info(p);assert i['bytes']==x['bytes'] and i['sha256']==x['sha256']
assert all(c['reaped'] and c['group_absent'] for c in result['commands'])
expected_pids = {32962} | {c['pid'] for c in result['commands']}
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
for path, sha in json.loads((run/'final-artifact-pins.json').read_bytes()).items():
    p = Path(path)
    assert p.is_relative_to(run)
    assert files[p.relative_to(ROOT).as_posix()]['sha256'] == sha, str(p)
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
for name in ('result.json', 'inputs.json', 'overlay-classes.json', 'final-artifact-pins.json'):
    with (OUT/name).open('xb') as f:
        f.write((run/name).read_bytes())
    assert info(OUT/name) == files['local-01/'+name]
for feature in (0,1):
 folder=OUT/f'timing-feature{feature}';folder.mkdir()
 for name in ('r2r','i2r','r2o','i2o','ready','setup-checks'):
  src=run/f'cost-feature{feature}/mapped'/(name+'.rpt');dst=folder/(name+'.rpt')
  with dst.open('xb') as f:f.write(src.read_bytes())
  assert info(dst)==files[src.relative_to(ROOT).as_posix()]
audit = dict(status='BOOTH_CLOSED_ARCHIVE_VERIFIED', source_unchanged=True,
             files=len(files), raw_bytes=sum(x['bytes'] for x in files.values()),
             raw=info(archive), summary=info(OUT/'summary.zip'),
             manifests={n:files['local-01/'+n] for n in
                        ('result.json','inputs.json','overlay-classes.json','final-artifact-pins.json')},
             commands=32, original_input_pins_verified=len(originals), all_35_staged_inputs_verified=True, all_recorded_process_groups_absent=True, omitted_files=0,
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
