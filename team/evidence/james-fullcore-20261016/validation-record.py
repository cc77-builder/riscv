"""Bind completed host checks to current sources; does not rerun or invent times."""
import hashlib,json
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv');out=repo/'team/out/james-fullcore-20261016'
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
records=[dict(command=['python3','-B','-m','unittest','discover','-s','team/tests'],log='host-tests-final.log',expected='Ran 167 tests',exit_code=0),
         dict(command=['python3','-OO','-B','-m','unittest','discover','-s','team/workloads/vdot-perf','-p','test_*.py'],log='t13-tests-final-opt2.log',expected='Ran 23 tests',exit_code=0)]
for record in records:
    log=out/record['log'];text=log.read_text()
    if record['expected'] not in text or '\nOK\n' not in text:raise ValueError('test log incomplete')
    record['raw_log_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
sources={p.relative_to(repo).as_posix():sha(p) for folder in ('team/scripts','team/tests','team/workloads/vdot-perf','team/workloads/vdot-regression') for p in (repo/folder).rglob('*.py')}
(out/'validation-record.json').write_text(json.dumps(dict(records=records,sources=sources,note='Commands completed before this receipt; no reconstructed start/end times. Windows broad run had two host GCC compile failures; final full suite used the project WSL toolchain.'),indent=2)+'\n')
print('HOST_VALIDATION_BOUND',len(sources))
