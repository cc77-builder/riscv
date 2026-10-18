import json
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import hashlib

root=Path('/mnt/c/Code/RVInno/riscv')
out=Path(tempfile.mkdtemp(prefix='rvinno-standards-review-',dir='/home/amesotten/.cache/codex-rvinno'))
runner=(root/'team/optimizations/o1/check-parent.sh').read_text()
gate=runner[runner.index('  test "$rc" -eq 1'):runner.index('\ndone\nsha256sum')]
log=out/'inject-high.log'
log.write_text('PARENT_INJECT high\nVFEX4_PARENT_FAIL tick=10 bounded divider progress\n')
wrong=subprocess.run(['bash','-c',gate],env=dict(__import__('os').environ,rc='1',out=str(out),fault='high'),capture_output=True,text=True)
sentinel=out/'existing-result.json'
sentinel.write_text('PRESERVE_EXISTING_RESULT\n')
recheck=subprocess.run([sys.executable,'-OO','-B',str(root/'team/optimizations/o1/recheck_extended_run.py'),
    '--run','/home/amesotten/.cache/codex-rvinno/o1-complete-20261018/runs-01',
    '--output',str(sentinel)],capture_output=True,text=True)
result={'output':str(out),'wrong_parent_failure_accepted':wrong.returncode==0,
        'parent_gate_exit':wrong.returncode,'recheck_exit':recheck.returncode,
        'existing_output_overwritten':sentinel.read_text()!='PRESERVE_EXISTING_RESULT\n',
        'recheck_stdout':recheck.stdout,'recheck_stderr':recheck.stderr}
source=Path('/home/amesotten/.cache/codex-rvinno/o1-complete-20261018/runs-01')
copied=out/'copied-run'
shutil.copytree(source,copied)
raw=copied/'control/stderr.log'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=digest(raw)
clobber=subprocess.run([sys.executable,'-OO','-B',str(root/'team/optimizations/o1/recheck_extended_run.py'),
    '--run',str(copied),'--output',str(raw)],capture_output=True,text=True)
after=digest(raw)
result.update(actual_input_clobber_exit=clobber.returncode,input_before_sha256=before,
              input_after_sha256=after,raw_input_clobbered=before!=after,
              clobber_stdout=clobber.stdout,clobber_stderr=clobber.stderr)
(out/'reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
receipt=root/'team/out/o1-publication-review-20261018/standards-repro'
receipt.mkdir(parents=True,exist_ok=True)
shutil.copyfile(out/'reproduction.json',receipt/'output-and-negative.json')
shutil.copyfile(log,receipt/'inject-high-wrong-reason.log')
shutil.copyfile(__file__,receipt/'output-and-negative-repro.py')
print(json.dumps(result,indent=2))
