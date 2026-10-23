from pathlib import Path
import json,sys
old=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');new=old.parent/'merge-reg-20261023'
a=json.loads((old/'inputs/input-contract-v1.json').read_text());b=json.loads((new/'inputs/input-contract-v1.json').read_text())
expected={p.replace(str(old),str(new)) for p in a['files']}
print('old',len(a['files']),'new',len(b['files']))
print('missing relative to prior contract',json.dumps(sorted(expected-set(b['files'])),indent=2))
sys.path.insert(0,str(new/'repo/team/optimizations/o2/fullcore'))
from types import SimpleNamespace
import run_suite as suite
args=SimpleNamespace(preflight_only=True,input_contract=new/'inputs/input-contract-v1.json',t12_root=new/'inputs/t12',t14_root=new/'inputs/t14',dense_build=new/'inputs/dense')
guard=suite.load_module('preflight_guard',new/'repo/team/scripts/artifact_guard.py');perf=suite.load_module('preflight_perf',new/'repo/team/workloads/vdot-perf/check.py')
try:
 result=suite.preflight(args,guard,perf)
 value=dict(status='CURRENT_INPUT_PREFLIGHT_PASS',receipt=result[2])
except Exception as e:
 value=dict(status='FAILED',error=repr(e));print(repr(e))
(new/'input-preflight-01.json').write_text(json.dumps(value,indent=2)+'\n')
print(value['status'],flush=True)
