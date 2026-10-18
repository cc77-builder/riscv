import json, subprocess, time
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv')
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018')
build=cache/'core-build'
deadline=time.monotonic()+3600
while not (build/'split-build.status').exists():
    if time.monotonic()>deadline:raise SystemExit('build wait timeout; no runtime attempted')
    time.sleep(5)
if (build/'split-build.status').read_text().strip()!='exit_code=0':raise SystemExit('build failed; no runtime attempted')
command=['python3','-OO','-B',str(repo/'team/optimizations/o1/run_trace_core.py'),
         '--core',str(cache/'source-0d8e5ae781e51a3c'),'--receipt',str(build),
         '--pack',str(repo/'team/out/o1-trace-20261018-core-pack'),
         '--reference-root','/home/amesotten/.cache/codex-rvinno/fullcore-20261016/nemu/reference',
         '--output',str(cache/'core-runs-01')]
(cache/'core-run-command.json').write_text(json.dumps(command,indent=2)+'\n')
with (cache/'core-run-driver.log').open('wb') as log:
    code=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
(cache/'core-run-driver.status').write_text('exit_code='+str(code)+'\n')
raise SystemExit(code)
