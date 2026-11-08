#!/usr/bin/env python3
"""Archive the closed Pgroup experiment byte for byte, without running EDA."""
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import time
import zipfile

ROOT = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-pgroup-20261108-main')
OUT = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-pgroup-20261108-main/archive-01')
EXPECTED_SOURCE = '1f9a4c807b30b8aa769e65595ce6b54619b190a5f2b5af1d531413de9970b90c'


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
assert result['status'] == 'PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE'
assert result['candidate_source_sha256'] == EXPECTED_SOURCE
assert result['all_children_reaped'] and result['inputs_unchanged']
assert result['generated_inputs_unchanged'] and result['original_classpath_unchanged']
assert len(result['commands']) == 32
assert all(c['reaped'] and c['group_absent'] for c in result['commands'])
expected_pids = {19565} | {c['pid'] for c in result['commands']}
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
audit = dict(status='PGROUP_CLOSED_ARCHIVE_VERIFIED', source_unchanged=True,
             files=len(files), raw_bytes=sum(x['bytes'] for x in files.values()),
             raw=info(archive), summary=info(OUT/'summary.zip'),
             manifests={n:files['local-01/'+n] for n in
                        ('result.json','inputs.json','overlay-classes.json','final-artifact-pins.json')},
             commands=32, all_recorded_process_groups_absent=True, omitted_files=0,
             members_sha_and_crc_verified=True, new_eda_runs=0, new_guest_runs=0,
             cpu_affinity=sorted(os.sched_getaffinity(0)), nice=os.getpriority(os.PRIO_PROCESS, 0),
             elapsed_seconds=time.time()-started)
assert audit['elapsed_seconds'] < 300
with (OUT/'audit.json').open('xb') as f:
    f.write((json.dumps(audit, indent=2)+'\n').encode())
signal.alarm(0)
print(json.dumps(audit), flush=True)
