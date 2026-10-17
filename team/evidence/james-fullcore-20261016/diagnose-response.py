"""Debug-only replay; original logs and frozen hardware source are read-only."""
import importlib.util,json,sys
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
repo=Path('/mnt/c/Code/RVInno/riscv')
spec=importlib.util.spec_from_file_location('control',repo/'team/scripts/check-vdot-regression.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
captured={}
def trace(frame,event,arg):
    if event=='exception' and frame.f_code.co_name=='check':
        v=frame.f_locals;cycle=v.get('cycle',0);f=v.get('f',{})
        captured.update(error=str(arg[1]),cycle=cycle,entry=v.get('entries',{}).get(v.get('key')),window=[e for e in v.get('events',[]) if cycle-25<=e[0]<=cycle+5])
    return trace
sys.settrace(trace)
try:m.check((cache/'runs/t12-suite/control/run.log').read_text(),json.loads((cache/'workloads/control/data/manifest.json').read_text()),0)
except ValueError:pass
finally:sys.settrace(None)
(repo/'team/out/james-fullcore-20261016/response-diagnosis.json').write_text(json.dumps(captured,indent=2)+'\n')
print(json.dumps(captured,indent=2))
