"""Seal raw current-source evidence after actual run and recheck completion."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
workspace=Path('/mnt/c/Code/RVInno/riscv')
target=workspace/'team/evidence/o5-current-fullcore-20261021'
if target.exists():raise ValueError('existing evidence must be retained')
state=json.loads((base/'build-05/build-state.json').read_text())
if state['status']!='O2_FULLCORE_BUILD_PASS':raise ValueError('actual build did not pass')
launches=json.loads((base/'runs/launches.json').read_text())
if len(launches)!=3 or any(row.get('exit_code')!=0 for row in launches):raise ValueError('campaign incomplete')
review=json.loads((base/'runs/recheck-01/result.json').read_text())
if review.get('status')!='O2_G3_OFFLINE_RECHECK_PASS' or review.get('g3_complete') is not True:
    raise ValueError('strict full G3 verdict missing')
target.mkdir(parents=True)
files={}
def copy(source,relative):
    destination=target/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:raise ValueError('copy drift')
    files[str(relative)]=dict(sha256=digest,bytes=destination.stat().st_size,source=str(source))
for source in sorted(base.iterdir()):
    if source.is_file() and source.suffix in ('.json','.jsonl','.log','.exit'):
        copy(source,Path('native')/source.name)
copy(base/'prepared-inputs-v3.zip',Path('native/prepared-inputs-v3.zip'))
copy(base/'repo/build/time.log',Path('native/build-05/root-make-time.log'))
for name in ('build-01','build-02','build-03','build-04','build-05','native-clang-probe-05','input-negatives-01','runs'):
    for source in sorted((base/name).rglob('*')):
        relative=source.relative_to(base)
        if not source.is_file() or any(part in ('failed-products','interrupted-products') for part in relative.parts):continue
        if source.suffix in ('.json','.jsonl','.log','.txt','.sh','.exit','.patch','.py','.stdout','.stderr') or name in ('runs','native-clang-probe-05'):
            copy(source,Path('native')/relative)
for source in sorted((workspace/'team/out').iterdir()):
    if source.is_file() and (source.name.startswith('o5-') and source.suffix=='.log' or
                            'o5' in source.name and source.suffix=='.py' or source.name=='prepare-lf21.py'):
        copy(source,Path('host')/source.name)
manifest=dict(schema_version=1,sealed_utc=datetime.now(timezone.utc).isoformat(),
    tested_build_commit=state['source_commit'],emu_sha256=state['emu_sha256'],
    scope='current-source O2 G3; not performance/PPA/independent T17 or human ACK',files=files)
(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('EVIDENCE_SEALED',len(files),sum(row['bytes'] for row in files.values()),flush=True)
