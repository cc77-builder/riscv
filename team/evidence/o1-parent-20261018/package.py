"""Package this run's real inputs, failures, RTL, binaries and source bindings (WSL)."""
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

BASE = Path('/home/amesotten/.cache/codex-rvinno/o1-parent-20261018')
ROOT = Path('/mnt/c/Code/RVInno/riscv')
NATIVE = BASE/'source-a02cb6dc9e84c327'
OUT = ROOT/'team/evidence/o1-parent-20261018'
FINAL = BASE/'attempt-07'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

if (FINAL/'runner.status').read_text().strip() != 'exit_code=0':
    raise RuntimeError('Final regression did not pass')
if (BASE/'clock-repro-01/run.status').read_text().strip() != 'exit_code=1':
    raise RuntimeError('Missing old-RTL clock failure')
if 'canceled FU clock stayed enabled during idle' not in (BASE/'clock-repro-01/run.log').read_text():
    raise RuntimeError('Unexpected reproduction failure')

inputs = {}
for line in (FINAL/'source.sha256').read_text().splitlines():
    digest, name = line.split(maxsplit=1)
    if sha(NATIVE/name) != digest:
        raise RuntimeError('Native input drift: '+name)
    inputs[name] = digest
binding = json.loads((NATIVE/'build/source-binding.json').read_bytes())
blobs = {}
for name in binding['physical_root_sha256']:
    raw = (NATIVE/name).read_bytes().replace(b'\r\n', b'\n')
    blobs[name] = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
save('source-binding.json', dict(initial_snapshot=binding, tested_sha256=inputs,
     tested_root_git_blobs=blobs, scope='Real VFEX4 in MinimalConfig; asynchronous reset; clock gates enabled; no CPU'))
shutil.copyfile(FINAL/'inputs.tar.gz', OUT/'tested-inputs.tar.gz')
shutil.copyfile(FINAL/'working-tree.patch', OUT/'production-and-build.patch')
for name in ('run-parent-local.sh','debug-parent-local.sh'):
    shutil.copyfile(ROOT/'team/out'/name, OUT/name)

attempts = {}
with tarfile.open(OUT/'validation.tar.gz', 'w:gz') as archive:
    for label in [f'attempt-{n:02}' for n in range(1,8)]+['harness-01','clock-repro-01']:
        folder = BASE/label
        status = 'runner.status' if label.startswith('attempt') else 'run.status'
        attempts[label] = (folder/status).read_text().strip()
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            if 'obj' in path.relative_to(folder).parts and path.name != 'VVDotExuTestTop':
                continue
            if label == 'attempt-07' and path.name == 'inputs.tar.gz':
                continue # copied separately above
            archive.add(path, arcname=path.relative_to(BASE), recursive=False)
        log = 'runner.log' if label.startswith('attempt') else 'run.log'
        shutil.copyfile(folder/log, OUT/(label+'.log'))

results = {}
for mode in range(3):
    text = (FINAL/f'mode-{mode}/results.log').read_text()
    if not text.startswith(f'VFEX4_PARENT_PASS mode={mode} '):
        raise RuntimeError('Missing parent pass')
    results[str(mode)] = text.splitlines()
    shutil.copyfile(FINAL/f'mode-{mode}/results.log', OUT/f'mode-{mode}.log')
for fault in ('identity','wen','high','cancel'):
    text = (FINAL/f'inject-{fault}.log').read_text()
    if f'PARENT_INJECT {fault}' not in text or 'VFEX4_PARENT_FAIL' not in text:
        raise RuntimeError('Missing negative control')
save('verification.json', dict(attempts=attempts, results=results,
     source_commit=subprocess.check_output(['git','-C',str(NATIVE),'rev-parse','HEAD'],text=True).strip(),
     parent_simulated=True, fullcore_simulated=False, o1_default_enabled=False,
     old_clock_reproduction='clock-repro-01.log', negative_controls=['identity','wen','high','cancel'],
     no_new_system_installations=True, physical_timing_or_power_measured=False))
print('VFEX4_PARENT_EVIDENCE_PACKAGED')
