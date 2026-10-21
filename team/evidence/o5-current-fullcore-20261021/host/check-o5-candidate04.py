from pathlib import Path
import json,subprocess,sys
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo';assets=base/'inputs'
revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
command=['python3','-B','team/optimizations/o5/preflight.py','--source-commit',revision,
         '--input-contract',str(assets/'input-contract-v1.json'),'--t12-root',str(assets/'t12'),
         '--t14-root',str(assets/'t14'),'--dense-build',str(assets/'dense'),'--output',str(base/'input-preflight-04.json')]
subprocess.run(command,cwd=root,check=True)
report=json.loads((base/'input-preflight-04.json').read_text())
files=report['strict_current_preflight']['receipt']['driver_files']
sys.path.insert(0,str(root/'team/optimizations/o2/fullcore'));import recheck
blobs=recheck.bind_original_drivers(root,revision,files)
rows=[]
for kind in ('missing-helper','substituted-helper'):
    changed=dict(files);key=str(root/'team/optimizations/o2/fullcore/input_contract.py')
    if kind=='missing-helper':changed.pop(key)
    else:changed[key]='f'*64
    try:recheck.bind_original_drivers(root,revision,changed)
    except ValueError as error:rows.append(dict(probe=kind,status='EXPECTED_REJECTION',error=str(error)))
    else:raise AssertionError(kind)
(base/'git-driver-binding-04.json').write_text(json.dumps(dict(status='CURRENT_GIT_DRIVER_BINDING_PASS',candidate=revision,drivers=len(blobs),negatives=rows),indent=2)+'\n')
print('REAL_GIT_DRIVER_BINDING_PASS',len(blobs),flush=True)
