from pathlib import Path
import json,subprocess
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
env=json.loads((base/'native-environment.json').read_text())
log=base/'gnu-time-probe.log'
command=['/usr/bin/time','-avp','-o',str(log),'mill','--version']
result=subprocess.run(command,env=env,cwd=base/'repo',capture_output=True,text=True)
print(result.stdout,result.stderr)
print('EXIT',result.returncode)
print(log.read_text())
print('FALLBACK_SHELL',Path('/bin/sh').resolve())
raise SystemExit(result.returncode)
