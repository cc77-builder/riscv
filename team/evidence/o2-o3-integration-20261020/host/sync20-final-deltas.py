import subprocess,json,sys,re,hashlib
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv');out=root/'team/out/sync20-final-deltas';out.mkdir(exist_ok=False)
rows=[]
for name,path in [('parent','team/optimizations/o2/parent'),('fullcore','team/optimizations/o2/fullcore'),
                  ('performance','team/optimizations/o2/performance'),('o3','team/workloads/o3-gemv')]:
 cmd=[sys.executable,'-OO','-B','-m','unittest','discover','-s',path,'-p','test_*.py','-v']
 with (out/(name+'.log')).open('wb') as f:rc=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT).returncode
 raw=(out/(name+'.log')).read_bytes();matches=re.findall(rb'Ran (\d+) tests?',raw)
 rows.append(dict(suite=path,exit_code=rc,tests=int(matches[-1]) if matches else None,sha256=hashlib.sha256(raw).hexdigest(),log=name+'.log'))
 (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,rc,rows[-1]['tests'],flush=True)
raise SystemExit(any(r['exit_code'] for r in rows))
