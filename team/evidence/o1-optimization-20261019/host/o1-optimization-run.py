"""Continue only after the fresh current-source build succeeds; preserve failures."""
import json, subprocess, time
from pathlib import Path

root=Path('/mnt/c/Code/RVInno/riscv')
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-optimization-20261019')
pack=root/'team/out/o1-optimization-20261019-pack'
status=cache/'core-build/launch.status'
while not status.exists():
    time.sleep(10)
if status.read_text().strip()!='0':
    raise SystemExit('Fresh build failed; no regression launched')
core=Path((pack/'build-copy.txt').read_text().strip())
common=['--core',str(core),'--receipt',str(cache/'core-build'),'--pack',str(pack),
        '--reference-root','/home/amesotten/.cache/codex-rvinno/fullcore-20261016/nemu/reference']
records=[]
for name,driver in [('extended-01','run_extended_core.py'),('software-01','run_software_core.py')]:
    command=['python3','-B',str(root/'team/optimizations/o1'/driver),*common,'--output',str(cache/name)]
    record=dict(name=name,command=command,status='RUNNING')
    records.append(record)
    (cache/'regression-progress.json').write_text(json.dumps(records,indent=2)+'\n')
    with (cache/(name+'.log')).open('xb') as log:
        rc=subprocess.run(command,cwd=core,stdout=log,stderr=subprocess.STDOUT).returncode
    record.update(status='PASS' if rc==0 else 'FAILED',exit_code=rc)
    (cache/'regression-progress.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,record['status'],flush=True)
    if rc:
        raise SystemExit(rc)
print('CURRENT_O1_SOFTWARE_AND_MATRIX_PASS',flush=True)
