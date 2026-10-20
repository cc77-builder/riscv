import hashlib,json,os,subprocess
from pathlib import Path
base=Path('/home/amesotten/.cache/codex-rvinno/sync20')
root=base/'source-d13def17dc8de4b8';out=base/'options-01';out.mkdir(exist_ok=False)
paths=[x.split(':',3)[-1] for x in json.loads((root/'out/vdotElasticParent/runClasspath.json').read_text())['value']]
cp=':'.join(paths)
source='''import xiangshan.backend.fu.wrapper.*;
public class O2OptionProbe { public static void main(String[] args) {
try {
 boolean o1=VDotHandoff.enabled(),o2=VDotO2.enabled(),e=VDotHandoff.traceEnabled(),f=VDotO1Trace.enabled(),t=VDotO2.traceEnabled();
 if ((e&&f)||(o2&&(e||f||o1))) throw new IllegalArgumentException("mixed mode or observers");
 System.out.println("ALLOW "+o1+" "+o2+" "+e+" "+f+" "+t);
} catch(IllegalArgumentException error) { System.out.println("REJECT "+error.getMessage());System.exit(10); }
}}'''
(out/'O2OptionProbe.java').write_text(source)
java='/usr/lib/jvm/java-21-openjdk-amd64/bin/'
subprocess.run([java+'javac','-cp',cp,'-d',str(out),str(out/'O2OptionProbe.java')],check=True)
env={k:v for k,v in os.environ.items() if not k.startswith('VDOT_')}
cases=[('default',{},0,'ALLOW false false false false false'),
       ('zeros',dict(VDOT_O2_ELASTIC='0',VDOT_O2_TRACE='0',VDOT_O1_HANDOFF='0'),0,None),
       ('legacy_t13',dict(VDOT_T13_TRACE='1'),0,None)]
for name,flags in [('frames_baseline',dict(VDOT_O1_TRACE='1',VDOT_O1_TRACE_PROFILE='frames')),
                   ('frames_t14',dict(VDOT_O1_TRACE='1',VDOT_O1_TRACE_PROFILE='frames',VDOT_T14_FUSED_INPUT='1')),
                   ('frames_o1',dict(VDOT_O1_TRACE='1',VDOT_O1_TRACE_PROFILE='frames',VDOT_T14_FUSED_INPUT='1',VDOT_O1_HANDOFF='1')),
                   ('events_t14',dict(VDOT_O1_TRACE='1',VDOT_T14_FUSED_INPUT='1')),
                   ('events_o1',dict(VDOT_O1_TRACE='1',VDOT_T14_FUSED_INPUT='1',VDOT_O1_HANDOFF='1',VDOT_T13_TRACE='1'))]:cases.append((name,flags,0,None))
o2=dict(VDOT_O2_ELASTIC='1',VDOT_T14_FUSED_INPUT='1')
cases += [('o2',o2,0,'ALLOW false true false false false'),
          ('o2_trace',dict(o2,VDOT_O2_TRACE='1'),0,'ALLOW false true false false true'),
          ('o2_t13',dict(o2,VDOT_O2_TRACE='1',VDOT_T13_TRACE='1'),0,None),
          ('missing_t14',dict(VDOT_O2_ELASTIC='1'),10,None),
          ('missing_o2',dict(VDOT_O2_TRACE='1'),10,None)]
for flag in ('VDOT_O1_HANDOFF','VDOT_T12_TRACE','VDOT_T13_TRACE'):
 cases.append(('mixed_'+flag,dict(o2,**{flag:'1'}),10,None))
for profile in ('frames','events'):
 cases.append(('mixed_trace_'+profile,dict(o2,VDOT_O1_TRACE='1',VDOT_O1_TRACE_PROFILE=profile),10,None))
for flag in ('VDOT_O2_ELASTIC','VDOT_O2_TRACE'):
 for index,bad in enumerate(('', '2', '-1', 'true')):
  cases.append((flag+'_invalid_'+str(index),dict(o2,**{flag:bad}),10,None))
cases += [('frames_t13',dict(VDOT_O1_TRACE='1',VDOT_O1_TRACE_PROFILE='frames',VDOT_T13_TRACE='1'),10,None),
          ('invalid_profile',dict(VDOT_O1_TRACE_PROFILE='other'),10,None)]
rows=[]
for name,flags,expected,marker in cases:
 p=subprocess.run([java+'java','-cp',str(out)+':'+cp,'O2OptionProbe'],env=dict(env,**flags),capture_output=True,text=True)
 (out/(name+'.stdout.log')).write_text(p.stdout);(out/(name+'.stderr.log')).write_text(p.stderr)
 assert p.returncode==expected,(name,p.stdout,p.stderr)
 assert p.stdout.startswith('ALLOW ' if expected==0 else 'REJECT '),(name,p.stdout)
 if marker:assert p.stdout.strip()==marker,(name,p.stdout)
 rows.append(dict(name=name,flags=flags,exit_code=p.returncode,expected_exit=expected))
classes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
 for p in (root/'out/xiangshan/compile.dest/classes/xiangshan/backend/fu/wrapper').glob('VDotO*.class')}
(out/'results.json').write_text(json.dumps(dict(status='COMPILED_MODE_OPTION_PASS',cases=rows,compiled_classes=classes),indent=2)+'\n')
print('COMPILED_MODE_OPTION_PASS',len(rows))
