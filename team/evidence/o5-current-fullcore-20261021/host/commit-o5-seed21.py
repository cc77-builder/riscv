"""Keep original shared drivers in a fixed child, then merge that work into James."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
root=Path('/mnt/c/Code/RVInno/riscv')
baseline='0484f1feb25d0e8fa9fa281a643f1943eabc7bb5'
head='2b6c5d6c1d29cc4a933f73853ce2ccbfc449f2fa'
paths=['team/optimizations/o2/fullcore/run_supplements.py',
       'team/optimizations/o2/fullcore/test_supplement_seed.py']
receipt=root/'team/out/o5-seed-commit.json'
def git(*args,env=None,data=None):
    return subprocess.check_output(['git','-C',str(root),*args],env=env,input=data)
if receipt.exists():raise ValueError('source commit receipt already exists')
if git('rev-parse','HEAD').decode().strip()!=head or git('branch','--show-current').decode().strip()!='James_Hotten':
    raise ValueError('unexpected integration checkout')
if git('diff','--cached','--name-only').strip():raise ValueError('index is not clean')
if git('ls-files','--',paths[1]).strip():raise ValueError('new test already tracked')
bodies={name:(root/name).read_bytes() for name in paths}
with tempfile.TemporaryDirectory(prefix='o5-seed-index-') as temp:
    env=os.environ.copy();env['GIT_INDEX_FILE']=str(Path(temp)/'index')
    git('read-tree',baseline,env=env)
    for name,body in bodies.items():
        blob=git('hash-object','-w','--path='+name,'--stdin',data=body).decode().strip()
        git('update-index','--add','--cacheinfo','100644',blob,name,env=env)
    tree=git('write-tree',env=env).decode().strip()
    revision=git('commit-tree',tree,'-p',baseline,data=b'fix(g3): bind explicit supplement seed without changing core drivers\n').decode().strip()
for name,body in bodies.items():
    if git('show',revision+':'+name)!=body:
        raise ValueError('Git source differs from tested bytes: '+name)
row=dict(status='SOURCE_CREATED',source_commit=revision,parent=baseline,integration_parent=head,
         paths=paths,source_sha256={p:hashlib.sha256(b).hexdigest() for p,b in bodies.items()})
receipt.write_text(json.dumps(row,indent=2)+'\n')
# Both files were authored by this task and are now preserved in the immutable child.
git('restore','--source=HEAD','--worktree','--',paths[0])
if (root/paths[1]).read_bytes()!=bodies[paths[1]]:raise ValueError('test changed before integration')
(root/paths[1]).unlink()
subprocess.run(['git','-C',str(root),'merge','--no-ff',revision,'-m',
    'Merge Git-bound seeded supplement runner while retaining original G3 evidence'],check=True)
row.update(status='MERGED',integration_commit=git('rev-parse','HEAD').decode().strip())
receipt.write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps(row),flush=True)
