#!/usr/bin/env bash
set -euo pipefail
cd /home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9
export CORE_SOURCE_PACK=/mnt/c/Code/RVInno/riscv/team/out/t10-source-pack-20261014-v5
export CORE_BUILD_EVIDENCE=/mnt/c/Code/RVInno/riscv/team/out/t10-core-final-20261014
export NEMU_HOME=/home/amesotten/.cache/codex-rvinno/t10/nemu-compatible/reference
export AM_HOME=/home/amesotten/.cache/codex-t05/nexus-am-086a238
export TEAM_EVIDENCE_DIR=/mnt/c/Code/RVInno/riscv/team/out/t10-relocation-negative-fixed-20261014-v2
export PYTHONOPTIMIZE=1
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess
p=Path(os.environ['TEAM_EVIDENCE_DIR']);p.mkdir(parents=True,exist_ok=True)
original=p.parent/'t10-audit-fixes-20261014-v2'
for name in ('build.status','build.log','source-before.json','source-after.json','workload.sha256','vdot-integration.bin','boot-flash.bin'):
 shutil.copyfile(original/name,p/name)
image=p/'vdot-integration.bin';image.write_bytes(image.read_bytes()+b'ISOLATED_NEGATIVE_TRAILER')
(p/'check.json').write_bytes(b'{"status":"STALE_PASS"}\n')
r=subprocess.run(['bash','team/scripts/vdot-core-smoke.sh','run'],capture_output=True)
(p/'rejection.log').write_bytes(r.stdout+r.stderr)
if r.returncode==0 or (p/'check.json').exists() or (p/'emulator-output.log').exists():
 raise RuntimeError('Relocated image was accepted or emulator started')
if b'Artifact paths differ from actual selected inputs' not in r.stdout+r.stderr:
 raise RuntimeError('Unexpected rejection stage: '+r.stderr.decode())
result=dict(status='T10_RELOCATED_IMAGE_NEGATIVE_PASS',python_optimize=1,rejected_before_emulator=True,old_pass_removed=True)
(p/'negative-result.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(result,sort_keys=True))
PY
