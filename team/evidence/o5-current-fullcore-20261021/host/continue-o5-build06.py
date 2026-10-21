"""Wait for the real fresh build result, then launch its fixed G3 campaign."""
from pathlib import Path
import hashlib,json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
result=base/'build-launch-06.exit'
while not result.exists():time.sleep(5)
if result.read_text().strip()!='0':raise SystemExit('build failed; no campaign launched')
script=Path('/mnt/c/Code/RVInno/riscv/team/out/run-o5-g3-build06.py')
receipt=base/'g3-launch.json'
if receipt.exists():raise ValueError('campaign launch receipt already exists')
receipt.write_text(json.dumps(dict(script=str(script),sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
    command=['python3',str(script)],started=time.time()),indent=2)+'\n')
with (base/'g3-launch.log').open('xb') as log:
    rc=subprocess.run(['python3',str(script)],stdout=log,stderr=subprocess.STDOUT).returncode
(base/'g3-launch.exit').write_text(str(rc)+'\n')
print('G3_CAMPAIGN_EXIT',rc,flush=True)
raise SystemExit(rc)
