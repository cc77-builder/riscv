import subprocess,json,sys,hashlib,time
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv')
out=root/'team/out/o1-optimization-tests-02'
out.mkdir(exist_ok=False)
suites=[('o1','team/optimizations/o1'),('events','team/optimizations/o1/fullcore'),('audit','team/optimizations/o1/audit'),('paired','team/optimizations/o1/performance'),('project','team/tests')]
rows=[]
for name,path in suites:
    command=[sys.executable,'-OO','-B','-m','unittest','discover','-s',path,'-p','test_*.py','-v']
    start=time.time()
    with (out/(name+'.log')).open('wb') as f:
        rc=subprocess.run(command,cwd=root,stdout=f,stderr=subprocess.STDOUT).returncode
    raw=(out/(name+'.log')).read_bytes()
    rows.append(dict(name=name,command=command,exit_code=rc,seconds=time.time()-start,log_sha256=hashlib.sha256(raw).hexdigest()))
    print(name,rc,flush=True)
    (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
raise SystemExit(any(r['exit_code'] for r in rows))
