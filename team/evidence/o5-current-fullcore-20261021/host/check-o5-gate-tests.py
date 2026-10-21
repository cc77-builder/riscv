from pathlib import Path
import hashlib, json, subprocess
root = Path('/mnt/c/Code/RVInno/riscv')
rows = []
for name, directory in [('gate-audit','team/optimizations/o1/audit'),
                        ('gate-g3','team/optimizations/o2/fullcore'),
                        ('gate-o1','team/optimizations/o1/fullcore')]:
    command = ['python3','-OO','-B','-m','unittest','discover','-s',directory,'-p','test_*.py','-v']
    path = root/'team/out'/('o5-'+name+'-final.log')
    with path.open('xb') as log:
        rc = subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
    rows.append(dict(command=command,exit_code=rc,log=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    print(name,rc,flush=True)
    if rc:break
(root/'team/out/o5-gate-tests.json').write_text(json.dumps(rows,indent=2)+'\n')
raise SystemExit(1 if any(row['exit_code'] for row in rows) else 0)
