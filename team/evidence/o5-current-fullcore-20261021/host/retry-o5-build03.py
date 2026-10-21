from pathlib import Path
import json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo'
subprocess.run(['git','-C',str(root),'fetch','origin','James_Hotten'],check=True)
subprocess.run(['git','-C',str(root),'checkout','--detach','6a75e7f77bd94098e4777f521e643d155c657e72'],check=True)
old=root/'build';retained=base/'build-02/failed-products'
assert old.resolve().parent==root.resolve() and retained.resolve().parent==(base/'build-02').resolve() and not retained.exists()
old.rename(retained)
env=json.loads((base/'native-environment.json').read_text())
command=['python3','-B','team/optimizations/o2/fullcore/build_fullcore.py','--output',str(base/'build-03')]
(base/'build-launch-03.json').write_text(json.dumps(dict(command=command,cwd=str(root),started=time.time(),environment=env),indent=2)+'\n')
with (base/'build-launch-03.log').open('wb') as log:
    rc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
(base/'build-launch-03.exit').write_text(str(rc)+'\n')
print('FULLCORE_BUILD_03_EXIT',rc,flush=True)
raise SystemExit(rc)
