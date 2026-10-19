"""Replay each actual raw protocol trace independently of the launch coordinator."""
import hashlib,json,sys
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv')
sys.path.insert(0,str(root/'team/optimizations/o1'))
from check_extended import extended_audit
from run_extended_core import module
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-optimization-20261019')
campaign=cache/'extended-01'
record=json.loads((campaign/'campaign.json').read_text())
assert record['status']=='O1_CONTROL_MATRIX_COUNTER_PASS'
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in campaign.rglob('*') if p.is_file()}
negative=module('recheck_negative',root/'team/scripts/check-vdot-negative.py')
functional=module('recheck_functional',root/'team/scripts/check-vdot-run.py')
results=[]
for row in record['runs']:
    name=row['name'];folder=campaign/name
    stdout=(folder/'stdout.log').read_text();stderr=(folder/'stderr.log').read_text()
    for leaf,digest in row['raw_sha256'].items():assert before[str(folder/leaf)]==digest
    if name=='negative':
        checked=negative.check(stderr+stdout,row['exit_code'])
        assert checked==json.loads((folder/'checked.json').read_text())
    else:
        assert row['exit_code']==0
        checked,_=extended_audit(stderr.splitlines(),vdot=name!='hello')
        assert checked==json.loads((folder/'trace.json').read_text())
        if name.startswith('matrix-'):
            index=name.split('-')[1]
            checked=functional.validate(stdout,'full',row['exit_code'],campaign/'images/matrix'/('data-'+index),require_diff=True)
            assert checked==json.loads((folder/'checked.json').read_text())
    results.append(dict(name=name,status='RAW_REPLAY_PASS'))
after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in campaign.rglob('*') if p.is_file()}
assert before==after and len(results)==13
with (cache/'extended-recheck.json').open('x') as f:
    json.dump(dict(status='O1_EXTENDED_RAW_REPLAY_PASS',runs=results,
                   raw_and_receipts_unchanged=True,new_emu_jobs=0,inputs=before),f,indent=2)
print('O1_EXTENDED_RAW_REPLAY_PASS',len(results))
