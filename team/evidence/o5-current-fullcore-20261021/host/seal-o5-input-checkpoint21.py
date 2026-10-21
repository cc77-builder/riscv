"""Preserve completed input and host-review evidence while native build runs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
workspace=Path('/mnt/c/Code/RVInno/riscv')
target=workspace/'team/evidence/o5-inputs-20261021'
target.mkdir(parents=True,exist_ok=False)
files={}
def copy(path,relative):
    destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,destination)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:raise ValueError('copy drift')
    files[str(relative)]=dict(sha256=digest,bytes=path.stat().st_size,source=str(path))
for name in ('checkout.json','input-preflight-01.json','input-preflight-02.json','input-preflight-03.json',
             'git-driver-binding.json','git-driver-binding-03.json','prepared-inputs-v1-failed.json',
             'prepared-inputs-v2.json','prepared-inputs-v2.zip','build04-external-identity-audit-02.json',
             'native-contract-tests.log','o5-readiness-tests.log','supplement-workload-tests.log'):
    copy(base/name,Path('native')/name)
for path in sorted((base/'input-negatives-01').glob('*.json')):
    copy(path,Path('native/input-negatives-01')/path.name)
for path in sorted((workspace/'team/out').glob('o5-*.log')):
    copy(path,Path('host')/path.name)
for name in ('prepare-lf21.py','build-o5-inputs21.py','finish-o5-inputs21.py','audit-o5-inputs21.py',
             'check-o5-candidate03.py','audit-o5-build04-native21.py','seal-o5-inputs22.py',
             'seal-o5-input-checkpoint21.py'):
    copy(workspace/'team/out'/name,Path('scripts')/name)
manifest=dict(schema_version=1,status='INPUTS_AND_HOST_REVIEW_ONLY',created_utc=datetime.now(timezone.utc).isoformat(),
              current_build_status='BUILDING',emulators_executed=0,g3_complete=False,t17_complete=False,files=files)
(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('INPUT_CHECKPOINT_SEALED',len(files),sum(item['bytes'] for item in files.values()),flush=True)
