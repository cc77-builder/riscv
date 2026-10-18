import json, os, subprocess
from pathlib import Path
root = Path('/home/amesotten/.cache/codex-rvinno/o1-parent-20261018/source-a02cb6dc9e84c327')
dest = Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018/flag-checks-direct-02')
dest.mkdir()
cp = ':'.join(s.split(':',3)[3] for s in json.loads((root/'out/vdotExu/runClasspath.json').read_text())['value'])
cp = cp.replace(str(root), '/home/amesotten/.cache/codex-rvinno/o1-trace-20261018/source-0d8e5ae781e51a3c')
scenarios = [
    ('bad-trace', {'VDOT_O1_TRACE':'TRUE'}, 'VDOT_O1_TRACE must be 0 or 1'),
    ('mixed-t12', {'VDOT_T12_TRACE':'1'}, 'O1 trace cannot be mixed'),
    ('mixed-t13', {'VDOT_T13_TRACE':'1'}, 'O1 trace cannot be mixed'),
    ('o1-old-t12', {'VDOT_O1_HANDOFF':'1','VDOT_T14_FUSED_INPUT':'1','VDOT_O1_TRACE':'0','VDOT_T12_TRACE':'1'}, 'O1 handoff cannot use the frozen'),
    ('o1-no-fusion', {'VDOT_O1_HANDOFF':'1'}, 'requires VDOT_T14_FUSED_INPUT=1'),
]
records = []
for name, extra, reason in scenarios:
    env = dict(os.environ, VDOT_O1_HANDOFF='0',VDOT_T14_FUSED_INPUT='0',VDOT_O1_TRACE='1',VDOT_T12_TRACE='0',VDOT_T13_TRACE='0',CHISEL_FIRTOOL_PATH='/home/amesotten/.cache/llvm-firtool/1.62.1/bin')
    env.update(extra)
    command = ['/usr/lib/jvm/java-21-openjdk-amd64/bin/java','-Xmx2G','-XX:ActiveProcessorCount=1','-cp',cp,'team.vdot.GenerateVDotExu',str(dest/(name+'-rtl'))]
    with (dest/(name+'.log')).open('wb') as f:
        code = subprocess.run(command, cwd=root, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    rec = dict(name=name,exit_code=code,expected=reason,matched=reason in (dest/(name+'.log')).read_text(),command=command)
    records.append(rec)
    (dest/'results.json').write_text(json.dumps(records,indent=2)+'\n')
    if code == 0 or not rec['matched']: raise SystemExit('Unexpected result: '+name)
print('O1_TRACE_ELABORATION_GUARDS_PASS')
