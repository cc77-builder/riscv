import hashlib, json, os, subprocess
from pathlib import Path
old = Path('/home/amesotten/.cache/codex-rvinno/o1-parent-20261018/source-a02cb6dc9e84c327')
root = Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018/source-0d8e5ae781e51a3c')
cache = root.parent
out = cache/'trace-off-equivalence'
out.mkdir()
cp = ':'.join(s.split(':',3)[3] for s in json.loads((old/'out/vdotExu/runClasspath.json').read_text())['value']).replace(str(old),str(root))
def sums(folder):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob('*.sv'))}
results=[]
for mode in range(3):
    env=dict(os.environ,VDOT_O1_TRACE='0',VDOT_T12_TRACE='0',VDOT_T13_TRACE='0',VDOT_T14_FUSED_INPUT=str(int(mode>0)),VDOT_O1_HANDOFF=str(int(mode==2)),CHISEL_FIRTOOL_PATH='/home/amesotten/.cache/llvm-firtool/1.62.1/bin')
    command=['/usr/lib/jvm/java-21-openjdk-amd64/bin/java','-Xmx2G','-XX:ActiveProcessorCount=1','-cp',cp,'team.vdot.GenerateVDotExu',str(out/f'mode-{mode}/rtl')]
    with (out/f'mode-{mode}.log').open('wb') as f:
        rc=subprocess.run(command,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
    before=sums(old.parent/f'attempt-07/mode-{mode}/rtl')
    after=sums(out/f'mode-{mode}/rtl')
    record=dict(mode=mode,exit_code=rc,command=command,before=before,after=after,identical=bool(before) and before==after)
    results.append(record)
    (out/'result.json').write_text(json.dumps(results,indent=2)+'\n')
    if rc or not record['identical']: raise SystemExit('Not equivalent: '+str(mode))
print('O1_TRACE_OFF_PARENT_RTL_BYTE_IDENTICAL modes=3')
