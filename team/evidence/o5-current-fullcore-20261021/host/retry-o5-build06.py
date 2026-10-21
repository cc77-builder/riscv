"""Preserve the rejected v1 attempt, then launch a fresh bound v2 build."""
from pathlib import Path
import hashlib, json, subprocess, sys, time
base = Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
root = base/'repo'
revision = sys.argv[1]
old = root/'build'
retained = base/'build-05/interrupted-products'
if (old.resolve().parent != root.resolve() or
        retained.resolve().parent != (base/'build-05').resolve() or retained.exists()):
    raise ValueError('unsafe preservation target')
state = json.loads((base/'build-05/build-state.json').read_text())
if state['status'] != 'FAILED' or (base/'build-launch-05.exit').read_text().strip() != '1':
    raise ValueError('prior controlled stop has not completed')
old.rename(retained)
subprocess.run(['git', '-C', str(root), 'fetch', 'origin', 'James_Hotten'], check=True)
subprocess.run(['git', '-C', str(root), 'checkout', '--detach', revision], check=True)
env = json.loads((base/'native-environment.json').read_text())
command = ['python3', '-B', 'team/optimizations/o2/fullcore/build_fullcore.py',
           '--recipe', 'split-clang-v2', '--output', str(base/'build-06')]
with (base/'build-launch-06.json').open('x') as stream:
    json.dump(dict(command=command, cwd=str(root), source_commit=revision, started=time.time(),
        environment=env, launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), stream, indent=2)
with (base/'build-launch-06.log').open('xb') as log:
    rc = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
(base/'build-launch-06.exit').write_text(str(rc)+'\n')
print('FULLCORE_BUILD_06_EXIT', rc, flush=True)
raise SystemExit(rc)
