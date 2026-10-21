"""Run actual current-candidate G3 only after a successfully verified fresh build."""
from pathlib import Path
import json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo';assets=base/'inputs'
build=base/'build-03'
state=json.loads((build/'build-state.json').read_text())
assert state['status']=='O2_FULLCORE_BUILD_PASS',state
env=json.loads((base/'native-environment.json').read_text())
out=base/'runs';out.mkdir(exist_ok=False)
rows=[]
def run(name,command):
    row=dict(name=name,command=command,cwd=str(root),started=time.time(),status='RUNNING')
    rows.append(row);(out/'launches.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (out/(name+'-launch.log')).open('wb') as log:
        rc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    row.update(exit_code=rc,finished=time.time(),status='PASS' if rc==0 else 'FAILED')
    (out/'launches.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(name,rc,flush=True)
    return rc
shared=['--hardware-pins',str(build/'hardware-inputs.json'),'--emu',str(root/'build/emu'),'--jobs','2',
        '--input-contract',str(assets/'input-contract-v1.json')]
core=run('core-01',['python3','-B','team/optimizations/o2/fullcore/run_suite.py','--output',str(out/'core-01'),*shared,
    '--t12-root',str(assets/'t12'),'--t14-root',str(assets/'t14'),'--dense-build',str(assets/'dense')])
extra=run('supplements-01',['python3','-B','team/optimizations/o2/fullcore/run_supplements.py','--output',str(out/'supplements-01'),*shared,
    '--diagnostic-build',str(assets/'supplement-diagnostic'),'--control-build',str(assets/'supplement-control')])
if core or extra:raise SystemExit(1)
rc=run('recheck-01',['python3','-B','team/optimizations/o2/fullcore/recheck.py','--campaign',str(out/'core-01'),
    '--supplements',str(out/'supplements-01'),'--output',str(out/'recheck-01')])
raise SystemExit(rc)
