import hashlib, json, shutil, subprocess, sys
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv')
out=repo/'team/evidence/o1-trace-20261018'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={p.relative_to(repo).as_posix():sha(p) for p in (repo/'team/optimizations/o1').glob('*.py')}
command=[sys.executable,'-OO','-B','-m','unittest','discover','-s',str(repo/'team/optimizations/o1'),'-p','test_*.py','-v']
with (out/'host-tests-final.log').open('wb') as log:
    rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
if any(sha(repo/p)!=h for p,h in files.items()):raise SystemExit('checker input changed')
(out/'host-tests-final.json').write_text(json.dumps(dict(command=command,exit_code=rc,python=sys.version,files=files,log_sha256=sha(out/'host-tests-final.log')),indent=2)+'\n')
shutil.copyfile(Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018/archive-replay-02/replay.json'),out/'parent-replay-final.json')
raise SystemExit(rc)
