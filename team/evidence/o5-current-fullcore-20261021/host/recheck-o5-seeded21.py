"""Independently audit the predefined seeded followup without rewriting prior results."""
from pathlib import Path
import hashlib,json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo'
revision='afe589bffc1fe98785784100187d45e953b421e9'
fix='2b6c5d6c1d29cc4a933f73853ce2ccbfc449f2fa'
output=base/'runs/recheck-03';receipt=base/'recheck-launch-03.json'
log=base/'recheck-launch-03.log';exit_file=base/'recheck-launch-03.exit'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
if any(p.exists() for p in (output,receipt,log,exit_file)):raise ValueError('audit output already exists')
if (base/'seed-supplement-launch-02.exit').read_text().strip()!='0':raise ValueError('seeded supplement did not finish successfully')
if git('rev-parse','HEAD').decode().strip()!=revision:raise ValueError('native source changed')
auditor='team/optimizations/o2/fullcore/recheck.py'
if (root/auditor).read_bytes()!=git('show',fix+':'+auditor):raise ValueError('auditor not exact selected Git blob')
frozen={str(p):sha(p) for p in (base/'runs').rglob('*') if p.is_file()}
drivers=json.loads((base/'runs/core-01/preflight.json').read_text())['driver_files']
if any(sha(p)!=h for p,h in drivers.items()):raise ValueError('original shared driver changed')
env=json.loads((base/'native-environment.json').read_text())
command=['python3','-B',auditor,'--campaign',str(base/'runs/core-01'),
         '--supplements',str(base/'runs/supplements-02'),'--output',str(output),'--runtime-gate-commit',fix]
row=dict(status='RUNNING',started=time.time(),command=command,cwd=str(root),native_head=revision,
         audit_commit=fix,launcher_path=str(Path(__file__).resolve()),launcher_sha256=sha(__file__),
         original_files=frozen,shared_driver_files=drivers)
receipt.write_text(json.dumps(row,indent=2)+'\n')
with log.open('xb') as stream:rc=subprocess.run(command,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT).returncode
exit_file.write_text(str(rc)+'\n')
row.update(exit_code=rc,finished=time.time(),original_files_unchanged=all(sha(p)==h for p,h in frozen.items()),
           shared_drivers_unchanged=all(sha(p)==h for p,h in drivers.items()),
           launcher_unchanged=sha(__file__)==row['launcher_sha256'],
           native_head_unchanged=git('rev-parse','HEAD').decode().strip()==revision,
           audit_output_files={str(p):sha(p) for p in output.rglob('*') if p.is_file()})
row['status']='PASS' if rc==0 and all(row[k] for k in
    ('original_files_unchanged','shared_drivers_unchanged','launcher_unchanged','native_head_unchanged')) else 'FAILED'
receipt.write_text(json.dumps(row,indent=2)+'\n')
print(row['status'],rc,flush=True)
raise SystemExit(0 if row['status']=='PASS' else 1)
