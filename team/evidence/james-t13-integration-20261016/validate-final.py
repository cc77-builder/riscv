import hashlib,json,os,subprocess,time
from pathlib import Path
root=Path('/home/amesotten/.cache/codex-rvinno/integration-t13-20261016')
output=Path('/mnt/c/Code/RVInno/integration-james-t13-20261016/team/out/t13-integration-20261016')
records=[]
def run(name,argv):
    start=time.monotonic()
    with (output/(name+'.log')).open('wb') as f:
        p=subprocess.run(argv,cwd=root,stdout=f,stderr=subprocess.STDOUT)
    records.append(dict(name=name,argv=argv,cwd=str(root),exit_code=p.returncode,expected_exit_code=0,seconds=round(time.monotonic()-start,3)))
    (output/'final-runs.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,p.returncode,flush=True)
    if p.returncode:raise RuntimeError(name)
run('final-checkout',['git','checkout','--detach','e967f207f'])
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
for opt in ('0','1','2'):
    os.environ['PYTHONOPTIMIZE']=opt
    run('final-t13-tests-opt'+opt,['python3','-B','-m','unittest','discover','-s','team/workloads/vdot-perf','-p','test_*.py'])
os.environ['PYTHONOPTIMIZE']='2'
run('final-archive-replay-opt2',['python3','-B','team/workloads/vdot-perf/verify_archive.py','--archive','team/evidence/t13-performance-20261015','--output',str(root/'team/out/t13-final-replay')])
def git(*args):return subprocess.check_output(['git',*args],cwd=root).decode()
paths=git('ls-files','-z').split('\0')
selected=[p for p in paths if p.startswith(('src/','team/scripts/','team/tests/','team/models/vdot/','team/workloads/vdot-perf/')) or p in ('build.sc','.gitmodules')]
binding={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in selected if (root/p).is_file()}
(output/'final-source-binding.json').write_text(json.dumps(dict(source=git('rev-parse','HEAD').strip(),files=binding,status=git('status','--porcelain','--untracked-files=no')),indent=2)+'\n')
print('T13_FINAL_VALIDATION_COMPLETE',flush=True)
