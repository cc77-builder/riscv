#!/usr/bin/env python3
"""Seal raw parent generation/mapping/STA attempts and final review receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--work',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
review=json.loads((a.work/'parent-review-04.json').read_text())
if review['status']!='PARENT_PAIR_REVIEW_PASS':raise ValueError('final review missing')
names=['parent-generation-01','parent-map-01','parent-timing-01','parent-timing-02','parent-timing-03','parent-timing-04','parent-provenance']
files=[f for name in names for f in (a.work/name).rglob('*') if f.is_file() and f.suffix!='.lib']
files += [a.work/name for name in ['parent-area-check.json','parent-review.json','parent-review-04.json','gate-tests.log','review-negative.log']]
manifest=[]
with zipfile.ZipFile(a.output/'parent-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(files):
        rel=str(f.relative_to(a.work));z.write(f,rel)
        manifest.append({'path':rel,'bytes':f.stat().st_size,'sha256':sha(f)})
    for f in Path(__file__).parent.glob('*.py'):
        rel='final-tools/'+f.name;z.write(f,rel)
        manifest.append({'path':rel,'bytes':f.stat().st_size,'sha256':sha(f)})
for src,dest in [('parent-map-01/result.json','mapping.json'),('parent-timing-04/result.json','timing.json'),('parent-review-04.json','review.json'),('parent-area-check.json','area-check.json')]:
    shutil.copyfile(a.work/src,a.output/dest)
derived=[{'path':str(f.relative_to(a.work)),'bytes':f.stat().st_size,'sha256':sha(f)} for f in (a.work/'parent-map-01').rglob('*.lib')]
summary={'status':'PARENT_COMPARISON_SEALED','archive_sha256':sha(a.output/'parent-evidence.zip'),'archive_bytes':(a.output/'parent-evidence.zip').stat().st_size,'files':manifest,'derived_libraries_reconstruct_from_pinned_inputs':derived,'production_defaults_changed':False,'full_physical_signoff':False,'final_timing_attempt':'parent-timing-04','crpr_enabled':False,'historical_attempts_preserved':names}
(a.output/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
with zipfile.ZipFile(a.output/'parent-evidence.zip') as z:
    if z.testzip() is not None:raise ValueError('archive CRC error')
    for row in manifest:
        data=z.read(row['path'])
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('archived bytes mismatch')
print(json.dumps({'status':summary['status'],'files':len(manifest),'archive_bytes':summary['archive_bytes']}))
