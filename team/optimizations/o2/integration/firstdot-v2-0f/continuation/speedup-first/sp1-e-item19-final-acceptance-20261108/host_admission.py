"""One cold-process host admission and honest projected collector cost; no target execution."""
from pathlib import Path
import sys,json,subprocess,time,traceback
N=Path(__file__).resolve().parent;sys.path.insert(0,str(N/'runtime'))
import runner
from common import read,save,need,sha
C=read(N/'CONTRACT.json');P=N.parent

def main():
 start=read(N/'external-host/START.json')['started_monotonic'];out=dict(status='RUNNING',target_runs=0);steps=[]
 try:
  with runner.host_deadline(start+900):
   t=time.monotonic();runner.verify();hash_s=time.monotonic()-t
   def run(argv,label):
    t=time.monotonic();p=subprocess.run(argv,capture_output=True,text=True,timeout=max(.1,start+900-time.monotonic()));(N/'host'/(label+'.stdout')).write_text(p.stdout);(N/'host'/(label+'.stderr')).write_text(p.stderr);steps.append(dict(label=label,argv=argv,exit=p.returncode,seconds=time.monotonic()-t));save(N/'host/STEPS.json',steps);need(p.returncode==0,label+': '+p.stderr[-1600:])
   run([sys.executable,'-B',str(N/'test_collect.py'),C['supplement_stage'],str(N/'host/SUPPLEMENT_GLUE.json')],'synthetic-glue')
   cases=[('supplement','candidate',N/'host-fixture','observed-M4-projection'),('original','candidate',P/'sp1-e-b4-r2-20261106/cases-r1/o2-control/target-01/02-candidate-full','historical-candidate'),('original','baseline',P/'sp1-e-b4-r4-20261106/cases/o2-control/target-01/01-baseline-full','historical-baseline')]
   allowed={r['path']for r in read(N/'EXECUTION_FREEZE.json')['files']}
   parsed={}
   for kind,mode,rd,label in cases:
    q=N/'host'/(label+'.json');run([sys.executable,'-B',str(N/'collect.py'),'--kind',kind,'--stage',C['supplement_stage'],'--mode',mode,'--role-dir',str(rd),'--reference',C['runtime']['normal_reference']['path'],'--exit','0','--out',str(q)],label)
    obj=read(q);need(set(obj['loaded_sources'])<=allowed,'unfrozen collector source '+str(set(obj['loaded_sources'])-allowed));parsed[label]=obj['collector']
   need(parsed['observed-M4-projection']['detail']['witnesses']==read(Path(C['supplement_stage'])/'target-01/02-candidate-normal/validation.json')['collector']['witnesses'],'actual witness reuse')
   for mode in ['candidate','baseline']:
    a=parsed['historical-'+mode];b=read(N/'history'/(mode+'.json'))['collector'];need(a['functional_replay']==b['functional_replay']and a['cross_hardware_architecture']==b['cross_hardware_architecture'],'historical exact reparse')
   a,b=(parsed['historical-'+m]for m in ['candidate','baseline'])
   for field in ['cross_hardware_architecture','functional_replay.uart_checks','functional_replay.csr_contract']:need(runner.field(a,field)==runner.field(b,field),'original cross-hardware mismatch '+field)
   seen=[]
   def mock(s):seen.append(s['name']);return None
   def fail(s,v):raise ValueError('deliberate fail-stop')
   try:runner.schedule(mock,fail)
   except ValueError:pass
   need(seen==[C['roles'][0]['name']],'schedule must stop first failure')
   for spec in C['roles']:
    argv,env,cwd=runner.plan(spec['name']);need(argv[0]==C['runtime'][spec['emu']]['path']and argv[2]==C['images'][spec['image']]['bin']['path']and cwd==spec['cwd'],'mode/image/cwd binding')
    if spec['kind']=='original':
     rd=P/('sp1-e-b4-r2-20261106/cases-r1/o2-control/target-01/02-candidate-full'if spec['mode']=='candidate'else'sp1-e-b4-r4-20261106/cases/o2-control/target-01/01-baseline-full');old=read(rd/'record.json');need(argv==old['command']and env==old['execution_identity']['environment']and cwd==old['cwd'],'original exact execution recipe')
   estimate=4*sum(s['seconds']for s in steps)+30*hash_s+60
   need(estimate<900,'host cost estimate exceeds900')
   runner.verify();out.update(status='PASS_HOST_ADMISSION',elapsed_seconds=time.monotonic()-start,estimated_execution_host_seconds=estimate,cost_method='4x cold-parser/fixture total +30 full frozen-input hashes +60s receipt/telemetry allowance; hard live900s cap remains',complete_M4_witnesses=True,original_eight_digest_reparse=True,original_cross_hardware_pair=True,exact_original_recipe=True,failstop_mock=True,targets=5,target_seconds=7500,outer_seconds=8400)
 except BaseException as e:out.update(status='FAIL_HOST_ADMISSION',failure=repr(e),traceback=traceback.format_exc())
 save(N/'host/RESULT.json',out);print(out['status']);return int(out['status']!='PASS_HOST_ADMISSION')
if __name__=='__main__':sys.exit(main())
