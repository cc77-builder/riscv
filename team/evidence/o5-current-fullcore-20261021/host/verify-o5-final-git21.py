"""Compare every sealed payload with committed Git bytes and working files."""
from pathlib import Path
import hashlib,json,subprocess
root=Path('/mnt/c/Code/RVInno/riscv')
relative=Path('team/evidence/o5-current-fullcore-20261021')
manifest=json.loads((root/relative/'manifest.json').read_text())
revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
with subprocess.Popen(['git','-C',str(root),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE) as batch:
    for name,row in manifest['files'].items():
        path=relative/name
        batch.stdin.write((revision+':'+path.as_posix()+'\n').encode());batch.stdin.flush()
        header=batch.stdout.readline().split()
        if len(header)!=3 or header[1]!=b'blob':raise ValueError('missing committed blob: '+name)
        committed=batch.stdout.read(int(header[2]))
        if batch.stdout.read(1)!=b'\n':raise ValueError('invalid Git batch boundary')
        if hashlib.sha256(committed).hexdigest()!=row['sha256']:raise ValueError('Git blob drift: '+name)
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('checkout drift: '+name)
    batch.stdin.close()
    if batch.wait()!=0:raise ValueError('Git batch failed')
result=dict(status='O5_FULLCORE_GIT_BLOBS_VERIFIED',revision=revision,files=len(manifest['files']),
            manifest_sha256=hashlib.sha256((root/relative/'manifest.json').read_bytes()).hexdigest())
output=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021/final-evidence-git-audit.json')
if output.exists():raise ValueError('audit already exists')
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
