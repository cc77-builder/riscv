from pathlib import Path
import hashlib,json,subprocess
root=Path('/mnt/c/Code/RVInno/riscv')
log=root/'team/out/o5-seed-g3-tests.log'
command=['python3','-OO','-B','-m','unittest','discover','-s','team/optimizations/o2/fullcore','-p','test_*.py','-v']
sources={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in (
    'team/optimizations/o2/fullcore/run_supplements.py','team/optimizations/o2/fullcore/test_supplement_seed.py')}
with log.open('xb') as stream:
    result=subprocess.run(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
with (root/'team/out/o5-seed-g3-tests.json').open('x') as stream:
    json.dump(dict(command=command,exit_code=result.returncode,sources=sources,
        log=str(log),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()),stream,indent=2)
print(result.returncode,flush=True)
raise SystemExit(result.returncode)
