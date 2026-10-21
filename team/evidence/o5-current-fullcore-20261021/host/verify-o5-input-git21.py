from pathlib import Path
import hashlib,json,subprocess
root=Path('/mnt/c/Code/RVInno/riscv')
relative=Path('team/evidence/o5-inputs-20261021')
manifest=json.loads((root/relative/'manifest.json').read_text())
revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
for name,row in manifest['files'].items():
    path=relative/name
    committed=subprocess.check_output(['git','-C',str(root),'show',revision+':'+path.as_posix()])
    if hashlib.sha256(committed).hexdigest()!=row['sha256']:raise ValueError('Git blob drift: '+name)
    if hashlib.sha256((root/path).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('checkout drift: '+name)
result=dict(status='O5_INPUT_GIT_BLOBS_VERIFIED',revision=revision,files=len(manifest['files']),
            manifest_sha256=hashlib.sha256((root/relative/'manifest.json').read_bytes()).hexdigest())
output=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021/input-checkpoint-git-audit.json')
if output.exists():raise ValueError('audit already exists')
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
