from pathlib import Path
import sys,json,hashlib
N=Path(__file__).resolve().parent
P=N.parent
sys.path.insert(0,str(N/'runtime'))
from common import read,sha

def pin(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
S=Path(read(N/'CONTRACT.json')['supplement_stage'])
files={r['path']:r for r in read(S/'EXECUTION_FREEZE.json')['files']}
for r in files.values():
 if pin(r['path'])!=r:raise ValueError('frozen supplement source drift '+r['path'])
# The original numeric collector's own immutable closure is checked before reuse.
O=P/'sp1-e-b4-r4-20261106/numeric'
c=read(O/'CONTRACT.json')
for r in c['input_files']:
 if pin(r['path'])!=r:raise ValueError('original closure drift '+r['path'])
 files[r['path']]=r
paths=[q for folder in ['runtime','history','host-fixture']for q in (N/folder).rglob('*')if q.is_file()]
paths += [q for q in N.iterdir()if q.is_file()]
paths += [O/x for x in ['adapter.py','CONTRACT.json','history.py','HISTORICAL_CANDIDATE_SUMMARY.json']]
old=read(c['old_collector']['path'].replace('/collector.py','/CONTRACT.json'))
for r in old['dependency_pins']:
 if pin(r['path'])!=r:raise ValueError('original dependency changed '+r['path'])
 files[r['path']]=r
paths += [Path(c['old_collector']['path']),Path(c['old_collector']['path']).with_name('CONTRACT.json')]
paths += [Path(x)for q in (P/'sp1-e-item19-closeout-prep-20261108').glob('original-*-offline.json')for x in read(q)['loaded_sources']]
paths += [S/x for x in ['RESULT.json','target-01/batch.json','target-01/01-bit100/validation.json','target-01/01-bit100/record.json','target-01/02-candidate-normal/validation.json','target-01/02-candidate-normal/record.json','target-01/02-candidate-normal/stdout.log','target-01/02-candidate-normal/stderr.log','target-01/02-candidate-normal/legacy-projection.log','external-batch/RESULT.json']if(S/x).exists()]
for d in [P/'sp1-e-b4-r2-20261106/cases-r1/o2-control/target-01/02-candidate-full',P/'sp1-e-b4-r4-20261106/cases/o2-control/target-01/01-baseline-full']:
 paths += [d/x for x in ['stdout.log','stderr.log','record.json','validation.json','execution-identity.json']if(d/x).exists()]
C=read(N/'CONTRACT.json');paths += [Path(r['path'])for r in C['runtime'].values()]+[Path(r['path'])for img in C['images'].values()for r in img.values()]
for q in paths:files[str(q.resolve())]=pin(q.resolve())
with(N/'EXECUTION_FREEZE.json').open('x')as f:json.dump(dict(operation_id=C['operation_id'],roles=C['roles'],limits=C['limits'],files=sorted(files.values(),key=lambda r:r['path'])),f,indent=2);f.write('\n')
print('FROZEN',len(files))
