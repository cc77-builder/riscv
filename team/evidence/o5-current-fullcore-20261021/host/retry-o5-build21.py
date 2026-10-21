from pathlib import Path
import json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo'
subprocess.run(['git','-C',str(root),'fetch','origin','James_Hotten'],check=True)
subprocess.run(['git','-C',str(root),'checkout','--detach','9577014a40e7ed8c2e4509421a323a53532b450f'],check=True)
env=json.loads((base/'native-environment.json').read_text())
command=['python3','-B','team/optimizations/o2/fullcore/build_fullcore.py','--output',str(base/'build-02')]
(base/'build-launch-02.json').write_text(json.dumps(dict(command=command,cwd=str(root),started=time.time(),environment=env),indent=2)+'\n')
with (base/'build-launch-02.log').open('wb') as log:
    rc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
(base/'build-launch-02.exit').write_text(str(rc)+'\n')
print('FULLCORE_BUILD_02_EXIT',rc,flush=True)
raise SystemExit(rc)
