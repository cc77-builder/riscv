"""Read-only compact runtime snapshot; status does not imply acceptance."""
import json,re
from pathlib import Path
runs=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016/runs')
def tail(p,size=8192):
    if not p.exists():return ''
    with p.open('rb') as f:f.seek(max(0,p.stat().st_size-size));return f.read().decode(errors='replace')
for name in ('software-original','software-lean'):
    d=runs/name
    if not d.exists():continue
    r=json.loads((d/'result.json').read_text()) if (d/'result.json').exists() else {}
    print(name,json.dumps(dict(exit=r.get('exit_code'),error=r.get('verification_error'),checked=(d/'checked.json').exists(),latest_uart=tail(d/'stdout.log',2000).splitlines()[-2:],latest_cycle=re.findall(r'cycle=\s*(\d+)',tail(d/'stderr.log'))[-1:])))
for name in ('t13-main','t13-stream'):
    d=runs/name
    if not d.exists():continue
    results=[json.loads(p.read_text()) for p in d.glob('*/result.json')]
    active=[p.parent.name for p in d.glob('*/runtime.json') if not(p.parent/'result.json').exists()]
    print(name,json.dumps(dict(finished=len(results),nonzero=[(r['image'],r['replay'],r['exit_code']) for r in results if r['exit_code']!=0],active_count=len(active),active_examples=sorted(active)[:3])))
