from pathlib import Path
import json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
scripts=Path('/mnt/c/Code/RVInno/riscv/team/out')
deadline=time.monotonic()+1800
while True:
    r=json.loads((base/'recheck-launch-03.json').read_text())
    if r['status']!='RUNNING':break
    if time.monotonic()>deadline:raise ValueError('audit still running; leave evidence unchanged')
    time.sleep(5)
if r.get('exit_code')!=1 or not r.get('original_files_unchanged'):
    raise ValueError('inspect unexpected audit outcome')
for name in ('summarize-o5-final21.py','finish-o5-docs21.py','seal-o5-current22.py'):
    p=subprocess.run(['python3',str(scripts/name)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (base/(name+'.log')).write_bytes(p.stdout)
    print(name,p.returncode,p.stdout.decode(errors='replace')[-400:],flush=True)
    if p.returncode:raise SystemExit(p.returncode)
