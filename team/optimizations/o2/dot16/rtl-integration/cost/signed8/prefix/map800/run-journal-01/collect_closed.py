#!/usr/bin/env python3
"""Archive the closed D800 experiment byte for byte, without running EDA."""
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import time
import zipfile

ROOT = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-map800-20261108-main')
OUT = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-map800-20261108-main/archive-01')
EXPECTED_SOURCE = 'f854197eb5b3291d927d8cdbb88d6d1192f0411542c5a0d95ca88dfc64d8421c'


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
assert result['status'] == 'PREFIX_FEATURE1_MAP800_COST_COMPLETE'
assert info(ROOT/'input-01/map800.py')['sha256'] == EXPECTED_SOURCE
assert result['feature'] == 1 and result['abc_delay_ps'] == 800
assert result['mapped_netlist_equivalence_tested'] is False
assert result['all_children_reaped'] and result['inputs_unchanged']
assert len(result['commands']) == 2
assert all(c['exit_code'] == 0 for c in result['commands'])
assert all(c['reaped'] and c['group_absent'] for c in result['commands'])
expected_pids = {22994} | {c['pid'] for c in result['commands']}
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
for path, sha in json.loads((run/'inputs.json').read_bytes())['generated'].items():
    p = Path(path)
    assert p.is_relative_to(run)
    assert files[p.relative_to(ROOT).as_posix()]['sha256'] == sha, str(p)
assert files['local-01/mapped.v']['sha256'] == result['mapped_sha256']
assert files['local-01/mapped.json']['sha256'] == result['mapped_json_sha256']
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
                 len(Path(n).parts) == 2 and Path(n).name not in ('mapped.v', 'mapped.json')]
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
for name in ('result.json', 'inputs.json'):
    with (OUT/name).open('xb') as f:
        f.write((run/name).read_bytes())
    assert info(OUT/name) == files['local-01/'+name]
audit = dict(status='MAP800_CLOSED_ARCHIVE_VERIFIED', source_unchanged=True,
             files=len(files), raw_bytes=sum(x['bytes'] for x in files.values()),
             raw=info(archive), summary=info(OUT/'summary.zip'),
             manifests={n:files['local-01/'+n] for n in
                        ('result.json','inputs.json')},
             commands=2, all_recorded_process_groups_absent=True, omitted_files=0,
             members_sha_and_crc_verified=True, new_eda_runs=0, new_guest_runs=0,
             cpu_affinity=sorted(os.sched_getaffinity(0)), nice=os.getpriority(os.PRIO_PROCESS, 0),
             elapsed_seconds=time.time()-started)
assert audit['elapsed_seconds'] < 300
with (OUT/'audit.json').open('xb') as f:
    f.write((json.dumps(audit, indent=2)+'\n').encode())
signal.alarm(0)
print(json.dumps(audit), flush=True)
