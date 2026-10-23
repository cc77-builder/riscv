from pathlib import Path
import subprocess,json,time,hashlib,sys
base=Path('/home/amesotten/.cache/codex-rvinno/merge-reg-20261023');root=base/'repo';out=base/'host-tests-01';out.mkdir(exist_ok=False)
env=json.loads((base/'native-environment.json').read_text());results=[]
for name,directory in [('fullcore','team/optimizations/o2/fullcore'),('workloads','team/optimizations/o2/fullcore/workloads'),('o5','team/optimizations/o5')]:
 command=[sys.executable,'-OO','-B','-m','unittest','discover','-s',directory,'-p','test_*.py']
 start=time.time()
 with (out/(name+'.log')).open('xb') as f:p=subprocess.run(command,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(name=name,command=command,cwd=str(root),started=start,finished=time.time(),exit_code=p.returncode,log_sha256=hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest()))
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
