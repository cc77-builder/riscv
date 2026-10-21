from pathlib import Path
import json
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
def read(path):
    return json.loads(path.read_text()) if path.exists() else None
state=read(base/'build-06/build-state.json')
split=read(base/'build-06/split/state.json')
report=dict(build=state['status'] if state else None,phases=[(p['name'],p['status']) for p in (split or {}).get('phases',[])],
            objects=len(list((base/'repo/build/emu-compile').glob('*.o'))))
memory=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
report['memory']={key:memory[key].strip() for key in ('MemAvailable','SwapFree','SwapTotal')}
large=base/'repo/build/emu-compile/VSimTop___024root__DepSet_hd5918264__151.cpp'
report['previous_large_unit']={'source_present':large.is_file(),'object_present':large.with_suffix('.o').is_file()}
for name in ('core-01','supplements-01','recheck-02','supplements-02','recheck-03'):
    result=read(base/'runs'/name/'result.json')
    progress=read(base/'runs'/name/'progress.json')
    campaign=read(base/'runs'/name/'campaign-state.json')
    report[name]=dict(result=result.get('status') if result else None,
                     state=campaign.get('status') if campaign else None,
                     progress=[(p['name'],p['status']) for p in progress] if progress else [])
    active=[]
    for runtime in (base/'runs'/name).glob('*/runtime.json'):
        if (runtime.parent/'result.json').exists():continue
        stdout=runtime.parent/'stdout.log'
        exit_file=runtime.parent/'exit-code.txt'
        active.append(dict(name=runtime.parent.name,stdout_bytes=stdout.stat().st_size if stdout.exists() else None,
                           exit_code=exit_file.read_text().strip() if exit_file.exists() else None))
    report[name]['active']=active
print(json.dumps(report),flush=True)
