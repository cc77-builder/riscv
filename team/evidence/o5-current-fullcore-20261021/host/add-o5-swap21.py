"""Temporary task-local backing file for WSL swap; no source or flag change."""
from pathlib import Path
import json,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021').resolve()
target=base/'temporary-build.swap'
if target.exists() or target.resolve().parent!=base:raise ValueError('unexpected swap target')
rows=[]
for command in (['fallocate','-l','8G',str(target)],['chmod','600',str(target)],
                ['mkswap',str(target)],['swapon',str(target)]):
    result=subprocess.run(command,capture_output=True,text=True)
    rows.append(dict(command=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
    (base/'temporary-swap-setup.json').write_text(json.dumps(dict(created=time.time(),commands=rows),indent=2)+'\n')
    if result.returncode:raise SystemExit(result.returncode)
print(subprocess.check_output(['free','-h'],text=True),flush=True)
