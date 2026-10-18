import datetime,hashlib,json,pathlib,subprocess,sys,time
ROOT=pathlib.Path('/mnt/c/Code/RVInno/riscv')
OUT=ROOT/'team/out/o1-publication-review-20261018'
OUT.mkdir(exist_ok=False)
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
head=git('rev-parse','HEAD')
refs=[]
for line in git('for-each-ref','--format=%(refname) %(objectname) %(symref)','refs/remotes/origin','refs/remotes/audit-lizufan').splitlines():
    parts=line.split()
    if len(parts)>2:continue
    name,sha=parts
    left,right=map(int,git('rev-list','--left-right','--count',head+'...'+sha).split())
    refs.append(dict(ref=name,sha=sha,current_only=left,remote_only=right))
save('branches.json',dict(head=head,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                         refs=refs,new_branch_commits=sum(r['remote_only'] for r in refs),
                         fetches=[dict(repository='https://github.com/cc77-builder/riscv.git',exit_code=0,
                                       retry='command-scoped OpenSSL after Schannel TLS handshake failure; no verification bypass'),
                                  dict(repository='https://github.com/LiZufan001/riscv.git',exit_code=0)]))
print('BRANCH_AUDIT',len(refs),'refs',sum(r['remote_only'] for r in refs),'unmerged commits',flush=True)
suites={'o0':'team/optimizations/o0','o1':'team/optimizations/o1','project':'team/tests',
        'perf':'team/workloads/vdot-perf','unified':'team/workloads/unified-vdot',
        'independent-model':'team/models/vdot/tests','parameter-model':'team/models/vdot-param/tests'}
results=[]
for name,folder in suites.items():
    command=[sys.executable,'-OO','-B','-m','unittest','discover','-s',folder,'-p','test_*.py','-v']
    start=time.monotonic()
    with (OUT/(name+'.log')).open('wb') as log:
        rc=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
    text=(OUT/(name+'.log')).read_text()
    import re
    count=re.search(r'Ran (\d+) tests? in',text)
    result=dict(suite=name,command=command,exit_code=rc,tests=int(count[1]) if count else None,
                seconds=time.monotonic()-start,log_sha256=hashlib.sha256((OUT/(name+'.log')).read_bytes()).hexdigest())
    results.append(result);save('tests.json',dict(head=head,suites=results))
    print(name,'exit',rc,'tests',result['tests'],flush=True)
if any(x['exit_code']!=0 for x in results):raise SystemExit(1)
