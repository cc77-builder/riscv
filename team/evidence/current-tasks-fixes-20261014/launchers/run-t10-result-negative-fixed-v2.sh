#!/usr/bin/env bash
set -euo pipefail
cd /home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9
export PYTHONOPTIMIZE=1
python3 - <<'PY'
from pathlib import Path
import json,shutil,subprocess,shlex,sys
sys.path.insert(0,str(Path('team/scripts').resolve()))
from vdot_core_checks import workload_inputs
from artifact_guard import digest,require
p=Path('/mnt/c/Code/RVInno/riscv/team/out/t10-result-negative-fixed-20261014-v2');p.mkdir(parents=True,exist_ok=True)
original=p.parent/'t10-audit-fixes-20261014-v2';old=p.parent/'t10-smoke-final-20261014'
am=Path('/home/amesotten/.cache/codex-t05/nexus-am-086a238')
nemu=Path('/home/amesotten/.cache/codex-rvinno/t10/nemu-compatible/reference')
core=p.parent/'t10-core-final-20261014'
for name in ('source-before.json','source-after.json','source-run.json','nemu-verification.json','runtime.sha256','build.status','build.log','vdot-integration.elf','vdot-integration.bin','boot-flash.bin'):
 shutil.copyfile(original/name,p/name)
shutil.copyfile(original/'source-before.json',p/'source-after-run.json')
(p/'data').mkdir(exist_ok=True)
for item in (original/'data').iterdir():
 if item.is_file():shutil.copyfile(item,p/'data'/item.name)
(p/'workload.sha256').write_bytes(''.join(digest(item)+'  '+str(item)+'\n' for item in workload_inputs(p,am)).encode())
command=shlex.split((original/'run-command.txt').read_text())
command=[arg.replace(str(original),str(p)) for arg in command]
(p/'run-command.txt').write_bytes((shlex.join(command)+'\n').encode())
(p/'emulator.status').write_bytes(b'exit_code=0\n')
log='\n'.join(row for row in (old/'emulator-output.log').read_text().splitlines() if not row.startswith(('T10_CASE ','T10_CORE_SMOKE_PASS ')))+'\n'
(p/'emulator-output.log').write_bytes(log.encode())
(p/'check.json').write_bytes(b'{"status":"STALE_PASS"}\n')
r=subprocess.run(['python3','team/scripts/vdot_core_checks.py','finish','--root',str(Path.cwd()),'--evidence',str(p),'--core',str(core),'--am',str(am),'--nemu',str(nemu)],capture_output=True)
(p/'rejection.log').write_bytes(r.stdout+r.stderr)
require(r.returncode!=0 and not (p/'check.json').exists(),'Missing results accepted or stale receipt retained')
require(b'Incomplete actual guest coverage' in r.stderr,'Unexpected rejection stage: '+r.stderr.decode())
result=dict(status='T10_MISSING_RESULTS_NEGATIVE_PASS',python_optimize=1,actual_case_rows=0,old_pass_removed=True,fixture_only=True)
(p/'negative-result.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(result,sort_keys=True))
PY
