"""One predefined seed=1 experiment; preserve the complete incomplete campaign."""
from pathlib import Path
import hashlib,json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo';assets=base/'inputs'
old='0484f1feb25d0e8fa9fa281a643f1943eabc7bb5'
revision='afe589bffc1fe98785784100187d45e953b421e9'
fix='2b6c5d6c1d29cc4a933f73853ce2ccbfc449f2fa'
output=base/'runs/supplements-02'; receipt=base/'seed-supplement-launch-02.json'
log=base/'seed-supplement-launch-02.log';exit_file=base/'seed-supplement-launch-02.exit'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
if any(p.exists() for p in (output,receipt,log,exit_file)):raise ValueError('experiment output already exists')
audit=json.loads((base/'runs/recheck-02/result.json').read_text())
if audit['status']!='O2_G3_OFFLINE_RECHECK_INCOMPLETE' or audit['suite_coverage']['missing']!=['PARTIAL_KILL']:
    raise ValueError('unexpected earlier audit; inspect before experiment')
if not (audit['core_regression_pass'] and audit['supplements_pass'] and audit['original_evidence_unchanged']):
    raise ValueError('earlier audit has another defect')
if git('rev-parse','HEAD').decode().strip()!=old:raise ValueError('unexpected native HEAD')
auditor='team/optimizations/o2/fullcore/recheck.py'
if (root/auditor).read_bytes()!=git('show',fix+':'+auditor):raise ValueError('auditor changed')
frozen={str(p):sha(p) for p in (base/'runs').rglob('*') if p.is_file()}
env=json.loads((base/'native-environment.json').read_text())
if git('remote','get-url','origin').decode().strip()!='/mnt/c/Code/RVInno/riscv':raise ValueError('unexpected origin')
subprocess.run(['git','-C',str(root),'fetch','--no-tags','origin',revision],check=True)
changed=set(git('diff','--name-only',old,revision).decode().splitlines())
if changed!={'team/optimizations/o2/fullcore/run_supplements.py','team/optimizations/o2/fullcore/test_supplement_seed.py'}:
    raise ValueError('source candidate modifies more than seed runner/tests')
subprocess.run(['git','-C',str(root),'switch','--detach',revision],check=True)
drivers=json.loads((base/'runs/core-01/preflight.json').read_text())['driver_files']
if any(sha(p)!=h for p,h in drivers.items()):raise ValueError('original shared checker changed')
command=['python3','-B','team/optimizations/o2/fullcore/run_supplements.py',
         '--output',str(output),'--hardware-pins',str(base/'build-06/hardware-inputs.json'),
         '--emu',str(root/'build/emu'),'--jobs','2','--seed','1',
         '--input-contract',str(assets/'input-contract-v1.json'),
         '--diagnostic-build',str(assets/'supplement-diagnostic'),'--control-build',str(assets/'supplement-control')]
row=dict(status='RUNNING',started=time.time(),source_commit=revision,previous_native_head=old,
         command=command,cwd=str(root),launcher=str(Path(__file__).resolve()),launcher_sha256=sha(__file__),
         original_files=frozen,shared_driver_files=drivers,emu_seed=1,
         policy='One predefined explicit seed experiment; missing coverage remains incomplete')
receipt.write_text(json.dumps(row,indent=2)+'\n')
with log.open('xb') as stream:rc=subprocess.run(command,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT).returncode
exit_file.write_text(str(rc)+'\n')
row.update(exit_code=rc,finished=time.time(),original_evidence_unchanged=all(sha(p)==h for p,h in frozen.items()),
           launcher_unchanged=sha(__file__)==row['launcher_sha256'])
row['status']='PASS' if rc==0 and row['original_evidence_unchanged'] and row['launcher_unchanged'] else 'FAILED'
receipt.write_text(json.dumps(row,indent=2)+'\n')
print(row['status'],rc,flush=True)
raise SystemExit(0 if row['status']=='PASS' else 1)
