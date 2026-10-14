#!/usr/bin/env bash
set -euo pipefail
cd /home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9
export CORE_SOURCE_PACK=/mnt/c/Code/RVInno/riscv/team/out/t10-source-pack-20261014-v5
export CORE_BUILD_EVIDENCE=/mnt/c/Code/RVInno/riscv/team/out/t10-core-final-20261014
export NEMU_HOME=/home/amesotten/.cache/codex-rvinno/t10/nemu-compatible/reference
export AM_HOME=/home/amesotten/.cache/codex-t05/nexus-am-086a238
export TEAM_EVIDENCE_DIR=/mnt/c/Code/RVInno/riscv/team/out/t10-image-negative-20261014
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess,shutil
p=Path(os.environ['TEAM_EVIDENCE_DIR']); p.mkdir(parents=True,exist_ok=True)
positive=p.parent/'t10-smoke-final-20261014'
assert json.loads((positive/'check.json').read_bytes())['status']=='VDOT_T10_CORE_SMOKE_PASS'
for name in ('source-before.json','build.status','build.log','workload.sha256'):
 shutil.copyfile(positive/name,p/name)
image=positive/'vdot-integration.bin'; original=image.read_bytes(); digest=hashlib.sha256(original).hexdigest()
(p/'check.json').write_bytes(b'{"status":"STALE_PASS"}\n')
try:
 changed=bytearray(original); changed[32]^=1; image.write_bytes(changed)
 run=subprocess.run(['bash','team/scripts/vdot-core-smoke.sh','run'],capture_output=True)
 (p/'rejection.log').write_bytes(run.stdout+run.stderr)
 assert run.returncode!=0 and not (p/'check.json').exists()
 assert not (p/'run-command.txt').exists(),'Corrupt image reached emulator'
 assert 'FAILED' in (p/'workload-verification.log').read_text(),'Unexpected failure stage'
finally:
 image.write_bytes(original)
assert hashlib.sha256(image.read_bytes()).hexdigest()==digest
(p/'negative-result.json').write_bytes((json.dumps(dict(status='T10_IMAGE_HASH_NEGATIVE_PASS',rejected_before_emulator=True,old_pass_removed=True,image_restored_sha256=digest),sort_keys=True,indent=2)+'\n').encode())
print('T10_IMAGE_HASH_NEGATIVE_PASS')
PY
