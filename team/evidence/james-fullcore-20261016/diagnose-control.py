"""Debug-only replay of the exact first ROB lifetime failure."""
import importlib.util,json,sys
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
out=Path('/mnt/c/Code/RVInno/riscv/team/out/james-fullcore-20261016')
root=Path((out/'build-copy.txt').read_text().strip())
spec=importlib.util.spec_from_file_location('control',root/'team/scripts/check-vdot-regression.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
captured={}
def trace(frame,event,arg):
    if event=='exception' and frame.f_code.co_name=='check' and str(arg[1])=='reallocated live ROB identity':
        v=frame.f_locals;key=v['key'];cycle=v['cycle'];events=v['events'];entry=v['entries'][key]
        relevant=[e for e in events if e[0]<=cycle and e[3]['rob']==v['f']['rob']]
        previous=[e for e in relevant if e[2]=='ENQUEUE' and e[0]<cycle][-1]
        window=[e for e in events if previous[0]<=e[0]<=cycle and (e[2]=='REDIRECT' or e[3]['rob']==v['f']['rob'])]
        captured.update(cycle=cycle,key=key,entry=entry,event=v['f'],window=window)
    return trace
text=(cache/'runs/t12-suite/control/run.log').read_text();manifest=json.loads((cache/'workloads/control/data/manifest.json').read_text())
sys.settrace(trace)
try:m.check(text,manifest,0)
except ValueError as e:captured['error']=str(e)
finally:sys.settrace(None)
(out/'control-diagnosis.json').write_text(json.dumps(captured,indent=2)+'\n')
print(json.dumps(captured,indent=2))
