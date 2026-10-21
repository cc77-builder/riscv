"""Retain the interrupted direct build and execute a fresh split contract."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess,sys,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo'
revision=sys.argv[1]
subprocess.run(['git','-C',str(root),'fetch','origin','James_Hotten'],check=True)
subprocess.run(['git','-C',str(root),'checkout','--detach',revision],check=True)
old=root/'build';retained=base/'build-03/interrupted-products'
if old.resolve().parent!=root.resolve() or retained.resolve().parent!=(base/'build-03').resolve() or retained.exists():
    raise ValueError('unsafe preservation target')
record=base/'build-03/interruption-observation.json'
if record.exists():raise ValueError('existing observation must be retained')
record.write_text(json.dumps(dict(status='OBSERVED_INTERRUPTED_OOM',observed_utc=datetime.now(timezone.utc).isoformat(),
    original_state=json.loads((base/'build-03/build-state.json').read_text())['status'],
    native_exit_code=None,kernel_log_sha256=hashlib.sha256((base/'build03-kernel.log').read_bytes()).hexdigest(),
    note='Kernel recorded Java OOM; supervisor ended before native final exit receipt. Original state retained.'),indent=2)+'\n')
old.rename(retained)
env=json.loads((base/'native-environment.json').read_text())
command=['python3','-B','team/optimizations/o2/fullcore/build_fullcore.py','--recipe','split-v1','--output',str(base/'build-04')]
(base/'build-launch-04.json').write_text(json.dumps(dict(command=command,cwd=str(root),source_commit=revision,
    started=time.time(),environment=env,launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
with (base/'build-launch-04.log').open('wb') as log:
    rc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
(base/'build-launch-04.exit').write_text(str(rc)+'\n')
print('FULLCORE_BUILD_04_EXIT',rc,flush=True)
raise SystemExit(rc)
