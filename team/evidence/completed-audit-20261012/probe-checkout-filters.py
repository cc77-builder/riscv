"""Read-only Git checkout-filter probe, does not rewrite historical evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

root=Path('/mnt/c/Code/RVInno/riscv')
results={}
for directory in ('stage1-20261009','script-check-20261010','t05-t05e-20261012','t08-nemu-20261012'):
    folder=root/'team/evidence'/directory
    index=folder/('SHA256SUMS' if directory in ('stage1-20261009','script-check-20261010') else 'archive.sha256')
    changed=[];total=0
    for line in index.read_text().splitlines():
        digest,name=line.split('  ',1);total+=1
        relative=f'team/evidence/{directory}/{name}'
        checkout=subprocess.check_output(['git','-c','core.autocrlf=true','-C',str(root),'cat-file','--filters',f'HEAD:{relative}'])
        if hashlib.sha256(checkout).hexdigest()!=digest: changed.append(name)
    results[directory]=dict(files=total,checksum_failures_with_windows_checkout_filters=changed)
(root/'team/out/completed-audit-20261012/checkout-filters.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
print(json.dumps(results,sort_keys=True,indent=2))
