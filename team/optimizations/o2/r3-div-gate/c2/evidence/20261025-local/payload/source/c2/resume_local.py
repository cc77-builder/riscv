"""Run the C2 original FU/parent gates sequentially; no PPA/fullcore."""
import argparse,datetime,hashlib,json,os,subprocess
from pathlib import Path
def stamp():return datetime.datetime.now().astimezone().isoformat()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args()
    record=a.work/'resumed-local-campaign.json';assert not record.exists()
    src=a.repo/'src/main/scala/xiangshan/backend/exu/ExeUnit.scala'
    digest=hashlib.sha256(src.read_bytes()).hexdigest()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.repo,text=True).strip()
    state=dict(status='running',started=stamp(),candidate_commit=head,exeunit_sha256=digest,steps=[])
    def save():
        temp=record.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(record)
    save()
    cmds=[
      ('fu-resumed',['python3','-B','team/optimizations/o2/run_rtl.py','fu',str(a.work/'fu-02')]),
      ('parent',['python3','-B','team/optimizations/o2/run_rtl.py','parent',str(a.work/'parent-01')]),
      ('parent-replay',['python3','-B','team/optimizations/o2/parent/check_trace.py','--log',str(a.work/'parent-01/result.log'),'--output',str(a.work/'parent-replay.json')])]
    try:
        for label,cmd in cmds:
            assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
            step=dict(label=label,command=cmd,cwd=str(a.repo),started=stamp(),status='running')
            state['steps'].append(step);save();print('START',label,flush=True)
            with (a.work/(label+'.log')).open('xb') as log:
                p=subprocess.Popen(cmd,cwd=a.repo,stdout=log,stderr=subprocess.STDOUT,
                     env=dict(os.environ,PYTHONUNBUFFERED='1',JAVA_OPTS='-Xmx12G -Xss16m',BUILD_JOBS='2'))
                step['pid']=p.pid;save();rc=p.wait()
            step.update(exit_code=rc,finished=stamp(),status='passed' if rc==0 else 'failed');save()
            assert rc==0,label+' failed; original output preserved'
            assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
            print('PASS',label,flush=True)
        state.update(status='ORIGINAL_FU_PARENT_GATES_PASS_AWAIT_C2_SUPPLEMENT',finished=stamp());save()
    except BaseException as e:
        state.update(status='failed',error=repr(e),finished=stamp());save();raise
if __name__=='__main__':main()
