from pathlib import Path
import sys,json,datetime
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
from common import read,save
from runner import pin
old=N.parent/'sp1-e-o2-cancel-m1-r4-r1-host-20261107'
files={r['path']:r for r in read(old/'EXECUTION_FREEZE.json')['files']}
for row in files.values():
 if pin(row['path'])!=row:raise ValueError('prior input changed '+row['path'])
paths=list((N/'runtime').glob('*.py'))+list((N/'runtime').glob('*.json'))+list((N/'host').glob('*.py'))
paths += [N/x for x in ['CONTRACT.json','USER_INSTRUCTION.txt','launch_host.py','launch_target.py','target_campaign.py','host_admission.py','freeze_inputs.py','FORMAT_BOUND.json','LEGACY_FORMAT_BOUND.json','BUDGET_POLICY.md']]
paths += [N.parent/'sp1-e-item19-observer-impl-20261107/host/sched_trace.py']
for role in ['01-bit100','02-candidate-normal']:
 paths += [old/'target-01'/role/x for x in ['stdout.log','stderr.log','record.json']]
c=read(N/'CONTRACT.json');paths += [Path(r['path'])for r in c['runtime'].values()]
i=read(N.parent/'sp1-e-item19-observer-diagnostic-20261108/RUNTIME_IDENTITY.json');paths += [Path(r['path'])for r in i['resolved_dependencies'].values()]
for f in paths:files[str(f)]=pin(f)
result={'schema':'observer-diagnostic-r1-freeze','files':sorted(files.values(),key=lambda x:x['path']),'roles':c['roles'],'limits':c['limits'],'operation_id':c['operation_id']}
with (N/'EXECUTION_FREEZE.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
print('FROZEN',len(files))
