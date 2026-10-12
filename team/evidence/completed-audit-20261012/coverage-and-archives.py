import hashlib
import json
from pathlib import Path
import re
import subprocess

root=Path('/mnt/c/Code/RVInno/riscv')
summary={}
archives={}
for directory in ('stage1-20261009','script-check-20261010','t05-t05e-20261012','t08-nemu-20261012','t09-baseline-20261012'):
    folder=root/'team/evidence'/directory
    index=folder/('SHA256SUMS' if directory in ('stage1-20261009','script-check-20261010') else 'archive.sha256')
    mismatches=[]; total=0
    for line in index.read_text().splitlines():
        expected,name=line.split('  ',1);total+=1
        actual=hashlib.sha256((folder/name).read_bytes()).hexdigest()
        if actual!=expected:
            blob=subprocess.check_output(['git','-C',str(root),'show',f'HEAD:team/evidence/{directory}/{name}'])
            mismatches.append(dict(path=name,working_tree_matches=False,git_blob_matches=hashlib.sha256(blob).hexdigest()==expected,
                                   matches_after_crlf_to_lf=hashlib.sha256((folder/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected))
    archives[directory]=dict(total=total,mismatches=mismatches)
summary['archives']=archives
text=(root/'team/evidence/t08-nemu-20261012/random/run.log').read_text().split('VDOT_EXTENSION_BEGIN',1)[1]
records=[dict(re.findall(r'(\w+)=([^\s]+)',line)) for line in text.splitlines() if line.startswith('VDOT_CASE ')]
summary['t08_actual_pre_vs_by_cause']={}
for cause in (0,2):
    selected=[r for r in records if int(r['expected_cause'],0)==cause]
    states={str(v):sum(((int(r['pre_mstatus'],0)>>9)&3)==v for r in selected) for v in range(4)}
    summary['t08_actual_pre_vs_by_cause'][str(cause)]=states
data=root/'team/out/t09-data'
manifest=json.loads((data/'manifest.json').read_text())
if hashlib.sha256((data/'cases.jsonl').read_bytes()).hexdigest()!=manifest['cases_sha256']:
    raise RuntimeError('Input mismatch')
cases=[json.loads(line) for line in (data/'cases.jsonl').read_text().splitlines()][:manifest['smoke_count']]
baseline=json.loads((root/'team/evidence/t09-baseline-20261012/nemu/baseline-manifest.json').read_text())
summary['t09_actual_coverage']=dict(cases=len(cases),random_count=sum(c['id'].startswith('R') for c in cases),
    operand_registers=sorted({c[k] for c in cases for k in ('vd','vs1','vs2')}),
    operand_tuples=sorted({(c['vd'],c['vs1'],c['vs2']) for c in cases}),
    random_operand_tuples=sorted({(c['vd'],c['vs1'],c['vs2']) for c in cases if c['id'].startswith('R')}),
    scratch_tuples=sorted({tuple(s) for s in baseline['scratch_by_word'].values()}),
    actual_policy_rounding_saturation_combinations=len({(c['config']['vtype']>>6,c['config']['vxrm'],c['config']['vxsat']) for c in cases}))
(root/'team/out/completed-audit-20261012/coverage-and-archives.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps(summary,sort_keys=True,indent=2))
