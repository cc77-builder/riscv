import subprocess, hashlib, json, pathlib, datetime

repo = pathlib.Path('/home/lizufan/xiangshan-validation-20261013/repo')
out = pathlib.Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/validation-20261013')
def git(*args):
    return subprocess.check_output(['git', *args], cwd=repo)
Z='4a916689e3dfa74680da19653f1df6b8b984edeb'
S='ffec67e372d80a0588a74a83496434c9f7c086bb'
M='a3a7fd7e53924be08ac9a1dabcebb1573caae13c'
C='45bea984445e6f07d0d9c0ee8e42302e225ba0b3'
B=git('merge-base',Z,S).decode().strip()
def tree(ref):
    entries={}
    for entry in git('ls-tree','-rz',ref).split(b'\0'):
        if entry:
            meta,path=entry.split(b'\t',1)
            entries[path.decode()] = meta.decode()
    return entries
trees={r:tree(r) for r in [B,Z,S,M,C]}
def changed(ref):
    return set(x.decode() for x in git('diff','--name-only','-z',B,ref).split(b'\0') if x)
zp,sp=changed(Z),changed(S)
assert zp & sp == {'team/README.md'}
parents=git('show','-s','--format=%P',M).decode().split()
assert parents == [Z,S]
assert git('show','-s','--format=%P',C).decode().split()==[M]
for ref in [Z,S,M]:
    subprocess.run(['git','merge-base','--is-ancestor',ref,C],cwd=repo,check=True)
for ref,paths in [(Z,zp-sp),(S,sp-zp)]:
    for p in paths:
        assert trees[M].get(p)==trees[ref].get(p),(ref,p)
links={r:{p:m for p,m in t.items() if m.startswith('160000 ')} for r,t in trees.items()}
assert len(links[Z])==10
assert links[Z]==links[S]==links[M]==links[C]
for p in ['.gitmodules','team/versions.env']:
    assert len({trees[r][p] for r in [Z,S,M,C]})==1
c_changes=git('diff','--name-only',M,C).decode().splitlines()
assert set(c_changes)=={'AGENTS.md','team/README.md','team/merge/2026-10-13-zjhwork-into-zufan.result.md','team/merge/2026-10-13-zjhwork-into-zufan.result.json'}
for p,entry in trees[M].items():
    if p not in c_changes: assert trees[C].get(p)==entry,p
readme={r:git('show',r+':team/README.md').decode() for r in [Z,S,M]}
# Preserve each side's additions since BASE; obsolete BASE lines may be replaced.
for r in [Z,S]:
    additions=[line[1:] for line in git('diff','--unified=0',B,r,'--','team/README.md').decode().splitlines() if line.startswith('+') and not line.startswith('+++')]
    assert all(line in readme[M].splitlines() for line in additions),r
hashes={}
for name,ref in [('rtl-fu-20261013',C),('rtl-datapath-20261012','5227c030fdae9b6087fd995a00a3535b15f6aefc'),('rtl-datapath-20261012',C)]:
    results=[]
    for line in git('show',C+':team/evidence/'+name+'/source.sha256').decode().splitlines():
        expected,path=line.split(None,1);path=path.lstrip('*')
        actual=hashlib.sha256(git('show',ref+':'+path)).hexdigest()
        results.append(dict(path=path,expected=expected,actual=actual,match=expected==actual))
    hashes[name+'@'+ref]=results
assert all(x['match'] for k,v in hashes.items() for x in v if not(k=='rtl-datapath-20261012@'+C and x['path']=='build.sc'))
assert len(next(v for k,v in hashes.items() if k.startswith('rtl-fu')))==16
assert [x['path'] for x in hashes['rtl-datapath-20261012@'+C] if not x['match']]==['build.sc']
result=dict(time=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),Z=Z,S=S,M=M,C=C,BASE=B,parents=parents,target_unique=len(zp-sp),source_unique=len(sp-zp),common=sorted(zp&sp),gitlinks=links[C],candidate_docs=c_changes,hashes=hashes,status='PASS')
(out/'independent-audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('INDEPENDENT_GIT_HASH_AUDIT_PASS target_unique=33 source_unique=51 gitlinks=10 fu=16/16 datapath_original=9/9 current=8/9 explained=build.sc')
commands=[('model',['bash','team/scripts/check-vdot-model.sh']),('baseline',['python3','-B','team/research/2026-10-12-vdot-review/experiments/check_candidates.py','--output',str(out/'baseline.json')]),('arithmetic',['python3','-B','team/research/2026-10-13-vdot-round2/experiments/check_arithmetic.py','--output',str(out/'arithmetic.json')])]
runs=[]
for name,cmd in commands:
    start=datetime.datetime.now().astimezone().isoformat()
    with (out/(name+'.log')).open('w') as f:
        r=subprocess.run(cmd,cwd=repo,stdout=f,stderr=subprocess.STDOUT)
    runs.append(dict(name=name,command=cmd,start=start,end=datetime.datetime.now().astimezone().isoformat(),exit_code=r.returncode))
    print(name, r.returncode)
(out/'host-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
assert all(r['exit_code']==0 for r in runs)
