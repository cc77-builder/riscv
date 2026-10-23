"""Seal completed preparation only; hardware and EMU outcomes stay pending."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
base=Path('/home/amesotten/.cache/codex-rvinno/merge-reg-20261023')
workspace=Path('/mnt/c/Code/RVInno/riscv')
target=workspace/'team/evidence/merge-reg-20261023/inputs'
target.mkdir(parents=True,exist_ok=False)
files={}
def copy(source,relative):
    body=source.read_bytes();destination=target/relative
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(body)
    if destination.read_bytes()!=body:raise ValueError('copy drift')
    files[relative.as_posix()]=dict(sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),source=str(source))
for name in ('preparation.json','prepare.log','native-environment.json','input-preflight-01.json',
             'historical-partial-kill-diagnosis.json','prepared-inputs-v1.json','prepared-inputs-v1.zip'):
    copy(base/name,Path('native')/name)
for folder in ('host-tests-01','input-negatives-01'):
    for source in sorted((base/folder).rglob('*')):
        if source.is_file():copy(source,Path('native')/source.relative_to(base))
for source in sorted((base/'inputs').glob('*')):
    if source.is_file() and source.suffix in ('.json','.log','.exit'):
        copy(source,Path('native')/source.relative_to(base))
for name in ('prepare-merge-reg23.py','inputs-merge-reg23.py','finish-inputs-merge-reg23.py',
             'preflight-merge-reg23.py','audit-inputs-merge-reg23.py','test-merge-reg23.py',
             'diagnose-partial-kill23.py','seal-inputs-merge-reg23.py','seal-preparation-merge-reg23.py'):
    copy(workspace/'team/out'/name,Path('scripts')/name)
manifest=dict(schema_version=1,status='INPUTS_AND_HOST_REVIEW_PASS',
    sealed_utc=datetime.now(timezone.utc).isoformat(),
    source_commit='bc9e5ae469137a64b82744231acae9f9e3fe0359',
    host_tests=144,input_negative_probes=6,verified_supplement_builds=2,
    new_emu_runs=0,g3_complete=False,performance_measured=False,
    scope='Fresh current-source input preparation and host validation only; old trace diagnosis is historical',files=files)
(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PREPARATION_SEALED',len(files),sum(r['bytes'] for r in files.values()),flush=True)
