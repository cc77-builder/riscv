"""Preserve interrupted GCC products and build a fresh explicit Clang profile."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo'
revision=sys.argv[1]
old=root/'build';retained=base/'build-04/interrupted-products'
if old.resolve().parent!=root.resolve() or retained.resolve().parent!=(base/'build-04').resolve() or retained.exists():
    raise ValueError('unsafe preservation target')
observation=base/'build-04/interruption-observation.json'
if observation.exists():raise ValueError('existing observation')
observation.write_text(json.dumps(dict(status='OPERATOR_TERMINATED_AFTER_MEMORY_PRESSURE',
    observed_utc=datetime.now(timezone.utc).isoformat(),native_exit_code=None,outer_wsl_exit_code=1,
    last_observed_compiler=dict(pid=6463,rss_kib=11021828),objects_retained=len(list((old/'emu-compile').glob('*.o'))),
    evidence='build04-memory.jsonl',note='WSL commands timed out; distro terminated then shut down after confirming only Ubuntu-HDL was running. Original BUILDING state retained. No kernel OOM conclusion for this attempt.'),indent=2)+'\n')
old.rename(retained)
subprocess.run(['git','-C',str(root),'fetch','origin','James_Hotten'],check=True)
subprocess.run(['git','-C',str(root),'checkout','--detach',revision],check=True)
env=json.loads((base/'native-environment.json').read_text())
command=['python3','-B','team/optimizations/o2/fullcore/build_fullcore.py','--recipe','split-clang-v1','--output',str(base/'build-05')]
(base/'build-launch-05.json').write_text(json.dumps(dict(command=command,cwd=str(root),source_commit=revision,
    started=time.time(),environment=env,launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
with (base/'build-launch-05.log').open('wb') as log:
    rc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
(base/'build-launch-05.exit').write_text(str(rc)+'\n')
print('FULLCORE_BUILD_05_EXIT',rc,flush=True)
raise SystemExit(rc)
