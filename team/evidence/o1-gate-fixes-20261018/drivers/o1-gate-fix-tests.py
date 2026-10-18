import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path('/mnt/c/Code/RVInno/riscv')
out=pathlib.Path('/home/amesotten/.cache/codex-rvinno/o1-gate-fixes-20261018/host-tests-01')
out.mkdir(exist_ok=False)
suites={'o0':'team/optimizations/o0','o1':'team/optimizations/o1','project':'team/tests',
        'perf':'team/workloads/vdot-perf','unified':'team/workloads/unified-vdot',
        'independent-model':'team/models/vdot/tests','parameter-model':'team/models/vdot-param/tests'}
results=[]
for name,folder in suites.items():
    command=[sys.executable,'-OO','-B','-m','unittest','discover','-s',folder,'-p','test_*.py','-v']
    start=time.monotonic()
    with (out/(name+'.log')).open('wb') as log:
        rc=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
    import re
    raw=(out/(name+'.log')).read_bytes();count=re.search(rb'Ran (\d+) tests? in',raw)
    result=dict(suite=name,command=command,exit_code=rc,tests=int(count[1]) if count else None,
                seconds=time.monotonic()-start,log_sha256=hashlib.sha256(raw).hexdigest())
    results.append(result)
    (out/'tests.json').write_text(json.dumps(dict(suites=results),indent=2,sort_keys=True)+'\n')
    print(name,rc,result['tests'],flush=True)
if any(x['exit_code']!=0 for x in results):raise SystemExit(1)
