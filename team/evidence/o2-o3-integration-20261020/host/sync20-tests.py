import subprocess,json,sys,hashlib,time
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv')
out=root/'team/out/sync20-host-01';out.mkdir(exist_ok=False)
suites=['team/optimizations/o1','team/optimizations/o1/fullcore','team/optimizations/o1/audit','team/optimizations/o1/performance','team/optimizations/o2','team/optimizations/o2/parent','team/optimizations/o2/fullcore','team/optimizations/o2/fullcore/workloads','team/optimizations/o2/performance','team/workloads/o3-gemv','team/tests']
rows=[]
for path in suites:
 name=path.replace('/','-');cmd=[sys.executable,'-OO','-B','-m','unittest','discover','-s',path,'-p','test_*.py','-v'];start=time.time()
 with (out/(name+'.log')).open('wb') as f:rc=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT).returncode
 rows.append(dict(suite=path,exit_code=rc,seconds=time.time()-start,log=name+'.log',sha256=hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest()))
 (out/'results.json').write_text(json.dumps(rows,indent=2));print(path,rc,flush=True)
raise SystemExit(any(r['exit_code'] for r in rows))
