"""Audit immutable campaign with an explicitly Git-bound repaired gate."""
from pathlib import Path
import hashlib, json, subprocess, time

base = Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
root = base/'repo'
build_commit = '0484f1feb25d0e8fa9fa281a643f1943eabc7bb5'
audit_commit = '2b6c5d6c1d29cc4a933f73853ce2ccbfc449f2fa'
auditor = 'team/optimizations/o2/fullcore/recheck.py'
gate = 'team/optimizations/o1/audit/runtime_gate.py'
receipt = base/'recheck-launch-02.json'

def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])

def sha(body):
    return hashlib.sha256(body).hexdigest()

if any(p.exists() for p in (receipt, base/'runs/recheck-02',
                           base/'recheck-launch-02.log', base/'recheck-launch-02.exit')):
    raise ValueError('audit attempt already exists')
env = json.loads((base/'native-environment.json').read_text())
launcher = Path(__file__).resolve()
launcher_sha = sha(launcher.read_bytes())
if not (base/'g3-launch.exit').exists():
    raise ValueError('original campaign is still active')
if git('rev-parse', 'HEAD').decode().strip() != build_commit:
    raise ValueError('native HEAD changed')
launches = json.loads((base/'runs/launches.json').read_text())
if [(r['name'], r['exit_code']) for r in launches] != [('core-01', 1), ('supplements-01', 0)]:
    raise ValueError('unexpected campaign outcome; inspect separately')
frozen = {str(p): sha(p.read_bytes()) for name in ('core-01', 'supplements-01')
          for p in (base/'runs'/name).rglob('*') if p.is_file()}
frozen[str(base/'runs/launches.json')] = sha((base/'runs/launches.json').read_bytes())
old_auditor = (root/auditor).read_bytes()
old_gate = (root/gate).read_bytes()
if old_auditor != git('show', build_commit+':'+auditor) or old_gate != git('show', build_commit+':'+gate):
    raise ValueError('original auditor or gate was modified')
# origin is the local Windows repository; this fetch changes no checkout or remote.
origin = git('remote', 'get-url', 'origin').decode().strip()
if origin != '/mnt/c/Code/RVInno/riscv':
    raise ValueError('unexpected native origin: '+origin)
subprocess.run(['git', '-C', str(root), 'fetch', '--no-tags', 'origin', audit_commit], check=True)
new_auditor = git('show', audit_commit+':'+auditor)
(root/auditor).write_bytes(new_auditor)
command = ['python3', '-B', auditor, '--campaign', str(base/'runs/core-01'),
           '--supplements', str(base/'runs/supplements-01'), '--output', str(base/'runs/recheck-02'),
           '--runtime-gate-commit', audit_commit]
row = dict(status='RUNNING', started=time.time(), command=command, cwd=str(root),
           launcher_path=str(launcher), launcher_sha256=launcher_sha,
           native_head=build_commit, audit_commit=audit_commit, native_origin=origin,
           deployed_file=auditor, old_sha256=sha(old_auditor), new_sha256=sha(new_auditor),
           original_gate_unchanged_sha256=sha(old_gate), original_files=frozen)
receipt.write_text(json.dumps(row, indent=2)+'\n')
with (base/'recheck-launch-02.log').open('xb') as log:
    result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
row.update(exit_code=result.returncode, finished=time.time())
(base/'recheck-launch-02.exit').write_text(str(result.returncode)+'\n')
row['original_files_unchanged'] = all(sha(Path(p).read_bytes()) == digest for p,digest in frozen.items())
row['native_head_unchanged'] = git('rev-parse','HEAD').decode().strip() == build_commit
row['original_gate_unchanged'] = (root/gate).read_bytes() == old_gate
row['audit_output_files'] = {str(p): sha(p.read_bytes())
    for p in (base/'runs/recheck-02').rglob('*') if p.is_file()}
row['launcher_unchanged'] = sha(launcher.read_bytes()) == launcher_sha
row['status'] = 'PASS' if result.returncode == 0 and row['launcher_unchanged'] and all(row[k] for k in
    ('original_files_unchanged','native_head_unchanged','original_gate_unchanged')) else 'FAILED'
receipt.write_text(json.dumps(row, indent=2)+'\n')
print(row['status'], result.returncode, flush=True)
raise SystemExit(0 if row['status'] == 'PASS' else 1)
