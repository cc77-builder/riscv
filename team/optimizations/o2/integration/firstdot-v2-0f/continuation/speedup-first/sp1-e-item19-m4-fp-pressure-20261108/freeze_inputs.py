from pathlib import Path
import sys,json
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
from common import read
from runner import pin
D=N.parent/'sp1-e-item19-observer-diagnostic-r1-20261108'
files={r['path']:r for r in read(D/'EXECUTION_FREEZE.json')['files']}
for r in files.values():
 if pin(r['path'])!=r:raise ValueError('prior freeze drift '+r['path'])
paths=[f for area in ['runtime','software','build-review']for f in (N/area).rglob('*')if f.is_file()]
paths += [N/x for x in ['CONTRACT.json','USER_INSTRUCTION.txt','DESIGN.md','launch_host.py','launch_target.py','target_campaign.py','host_admission.py','freeze_inputs.py','host/REUSE.json','PREP_COMMANDS.json']]
paths += [N.parent/'sp1-e-item19-m2-fp-pressure-20261108'/x for x in ['RESULT.json','review/TIMELINE.json']]
paths += [N.parent/'sp1-e-item19-m3-fp-pressure-20261108'/x for x in ['ADMISSION_REVOKED.json','software/manifest.json','EXECUTION_FREEZE.json']]
paths += [N.parent/'sp1-e-item19-m3-runtime-r1-20261108'/x for x in ['RESULT.json','review/TIMELINE.json','review/ARBITRATION_SOURCE_PINS.json']]
paths += [D/x for x in ['RESULT.json','host/RESULT.json','host/COST.json','offline-r1/RESULT.json','review/TIMELINE.json']]
c=read(N/'CONTRACT.json');paths += [Path(r['path'])for r in c['runtime'].values()]
for depfile in (N/'build-review/attempt-01').glob('*.d'):
 for name in depfile.read_text().replace('\\\n',' ').partition(':')[2].split():
  f=Path(name)
  if f.is_file():paths.append(f.resolve())
for f in paths:files[str(f)]=pin(f)
with (N/'EXECUTION_FREEZE.json').open('x')as f:json.dump({'operation_id':c['operation_id'],'roles':c['roles'],'limits':c['limits'],'files':sorted(files.values(),key=lambda x:x['path'])},f,indent=2);f.write('\n')
print('FROZEN',len(files))
