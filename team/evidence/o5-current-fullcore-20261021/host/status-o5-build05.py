from pathlib import Path
import json
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
def read(path):
    return json.loads(path.read_text()) if path.exists() else None
state=read(base/'build-05/build-state.json')
split=read(base/'build-05/split/state.json')
report=dict(build=state['status'],phases=[(p['name'],p['status']) for p in split['phases']],
            objects=len(list((base/'repo/build/emu-compile').glob('*.o'))))
for name in ('core-01','supplements-01','recheck-01'):
    result=read(base/'runs'/name/'result.json')
    progress=read(base/'runs'/name/'progress.json')
    report[name]=dict(result=result.get('status') if result else None,
                     progress=[(p['name'],p['status']) for p in progress] if progress else [])
print(json.dumps(report),flush=True)
