import gzip,hashlib,json,subprocess,tarfile
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/integration-james-t13-20261016')
native=Path('/home/amesotten/.cache/codex-rvinno/integration-t13-20261016')
source=root/'team/out/t13-integration-20261016'
dest=root/'team/evidence/james-t13-integration-20261016'
if dest.exists() and any(dest.iterdir()):raise RuntimeError('evidence directory is not empty')
dest.mkdir(exist_ok=True)
def save(path,value):path.write_bytes((json.dumps(value,indent=2)+'\n').encode())
def sha(data):return hashlib.sha256(data).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=native)
def tree(rev,prefix):
    result={}
    for row in git('ls-tree','-r','-z',rev,'--',prefix).split(b'\0'):
        if row:
            meta,path=row.split(b'\t');result[path.decode()]=meta.decode().split()[2]
    return result
preserved={}
for rev in ('4a48fb22301d3f767edc458728a23450c892ca35','3b337a5b186ed60163a8d11edaeb3677dfd67750'):
    before=tree(rev,'team/evidence');after=tree('HEAD','team/evidence')
    if not all(after.get(p)==h for p,h in before.items()):raise RuntimeError('changed historical evidence')
    preserved[rev]=dict(files=len(before),all_git_blobs_identical=True)
if git('diff','3b337a5b186ed60163a8d11edaeb3677dfd67750','HEAD','--','src','build.sc','.gitmodules'):raise RuntimeError('production drift')
binding=json.loads((source/'final-source-binding.json').read_text())
selected={p:h for p,h in binding['files'].items() if p!='team/workloads/vdot-perf/README.md'}
# Compare canonical Git bytes; Windows CRLF checkout is not a source edit.
requests=''.join('HEAD:'+p+'\n' for p in selected).encode()
data=subprocess.run(['git','cat-file','--batch'],cwd=native,input=requests,stdout=subprocess.PIPE,check=True).stdout
offset=0
for p,wanted in selected.items():
    end=data.index(b'\n',offset);header=data[offset:end].split();size=int(header[2]);offset=end+1
    content=data[offset:offset+size];offset+=size+1
    if sha(content)!=wanted:raise RuntimeError('tested source differs from Git: '+p)
main=subprocess.check_output(['git','rev-parse','refs/heads/main'],cwd='/mnt/c/Code/RVInno/riscv').decode().strip()
if main!='9d49a225619871f6bf5ec0481e5a504c4dbee703':raise RuntimeError('main changed')
save(dest/'integration-audit.json',dict(source=git('rev-parse','HEAD').decode().strip(),main=main,historical_evidence=preserved,production_identical_to='3b337a5b186ed60163a8d11edaeb3677dfd67750',tested_git_blobs_matched=len(selected),documentation_only_exclusion=['team/workloads/vdot-perf/README.md'],fresh_full_core_runs=0,remote_pushes=0))
raw_logs={}
for p in sorted(source.iterdir()):
    if p.is_file() and p.suffix in ('.json','.log','.py'):
        data=p.read_bytes()
        if p.suffix=='.log':
            (dest/(p.name+'.gz')).write_bytes(gzip.compress(data,mtime=0));raw_logs[p.name]=dict(raw_sha256=sha(data),raw_bytes=len(data))
        else:(dest/p.name).write_bytes(data)
save(dest/'raw-logs.json',raw_logs)
bundles={}
for folder in ('t13-host-judge','t13-final-replay','t13-fresh-stream'):
    base=native/'team/out'/folder
    entries={}
    with tarfile.open(dest/(folder+'.tar.gz'),'w:gz') as tar:
        for p in sorted(base.rglob('*')):
            if not p.is_file() or 'objects' in p.relative_to(base).parts:continue
            name=p.relative_to(base).as_posix();data=p.read_bytes()
            entries[name]=dict(sha256=sha(data),bytes=len(data))
            tar.add(p,arcname=name,recursive=False)
    bundles[folder]=entries
save(dest/'bundle-files.json',bundles)
(dest/'.gitattributes').write_bytes(b'* -text\n')
save(dest/'file-manifest.json',dict(files={p.relative_to(dest).as_posix():sha(p.read_bytes()) for p in sorted(dest.rglob('*')) if p.is_file()}))
print(json.dumps(dict(status='INTEGRATION_EVIDENCE_PASS',historical_evidence=preserved,tested_files=len(selected),bundles={k:len(v) for k,v in bundles.items()})))
