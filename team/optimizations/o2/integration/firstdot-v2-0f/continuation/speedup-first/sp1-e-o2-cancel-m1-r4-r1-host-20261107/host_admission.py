"""One host-only admission under the external 900-second supervisor. No target call."""
from pathlib import Path
import json,os,sys,time,subprocess,traceback,re
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'host'));sys.path.insert(0,str(N/'runtime'))
import runner,adapter,review_m1
from common import read,save,exclusive,sha,now,need

def main():
    start=read(N/'external-host/START.json')['started_monotonic'];deadline=start+900
    exclusive(N/'HOST_ADMISSION.used.json',{'utc':now(),'started_monotonic':start,'retry_permitted':False})
    result={'status':'RUNNING_HOST_ONLY','target_runs':0,'native_reference_loads':0,'started_utc':now()}
    try:
        with runner.host_deadline(deadline):
            t=time.monotonic();f=runner.verify();review_m1.check_closure(f);hash_seconds=time.monotonic()-t
            env=dict(os.environ);env['PYTHONPATH']=str(N/'runtime')+':'+str(N/'host');env['PYTHONDONTWRITEBYTECODE']='1'
            command=[sys.executable,'-B','-m','unittest','-v','-f','test_image_integration.Integration','test_m1.M1']
            with (N/'host/tests.log').open('wb') as out:
                proc=subprocess.run(command,cwd=N/'host',env=env,stdout=out,stderr=subprocess.STDOUT,timeout=max(.1,deadline-time.monotonic()))
            save(N/'host/TEST_COMMAND.json',{'argv':command,'exit_code':proc.returncode,'cwd':str(N/'host'),'scope':'HOST_ONLY_ACTUAL_OBJECT_AND_SYNTHETIC_CONTROL','target_processes':0})
            need(proc.returncode==0,'HOST_DIFFERENCE_GATE_FAIL')
            separate=review_m1.review();save(N/'review/SEPARATE_REVIEW.json',separate)
            from fixtures_local import normal,negative
            t=time.monotonic();adapter.collect(negative(2,2),'bit100',1);negative_seconds=time.monotonic()-t
            fixture=normal();t=time.monotonic();adapter.collect(fixture,'candidate-normal',0);normal_seconds=time.monotonic()-t
            states=[line for line in fixture.splitlines() if line.startswith('SP1_STATE ')];last=states[-1];cycle=int(re.search(r'cycle=(\d+)',last)[1])
            stress=fixture+'\n'.join(re.sub(r'cycle=\d+','cycle='+str(cycle+i),last,count=1) for i in range(1,50001))+'\n'
            t=time.monotonic();adapter.collect(stress,'candidate-normal',0);stress_seconds=time.monotonic()-t
            elapsed=time.monotonic()-start;estimate=elapsed+12*hash_seconds+36*stress_seconds+4*negative_seconds+25
            cost={'status':'PASS_HOST_COST' if estimate<900 else 'HOLD_HOST_COST','measured_hash_seconds':hash_seconds,'negative_seconds':negative_seconds,'normal_seconds':normal_seconds,'stress_seconds':stress_seconds,'stress_extra_states':50000,'host_seconds_at_screen':elapsed,'conservative_screen_seconds':estimate,'cap_seconds':900,'model':'Same R2 finite screen: elapsed+12 hashes+36x50k-state stress+4 negatives+25s. Not a mathematical target completion bound; external900 stop authoritative.','GNU_preparation_excluded_and_separately_recorded':True}
            save(N/'host/COST.json',cost);need(estimate<900,'HOST_COST_NOT_ADMITTED')
            runner.verify();review_m1.check_closure(f)
            text=(N/'host/tests.log').read_text()
            result.update(status='PASS_HOST_ADMISSION',ended_utc=now(),elapsed_seconds=time.monotonic()-start,test_methods=13,m1_sequence_negative_cases=len(re.findall(r'\bM1_NEGATIVE ([A-Za-z0-9_]+)',text)),binding_negative_cases=len(re.findall(r'\bM1_BINDING_NEGATIVE ([A-Za-z0-9_]+)',text)),freeze_negative_cases=len(re.findall(r'\bM1_FREEZE_NEGATIVE ([A-Za-z0-9_]+)',text)),cost=cost,separate_review=separate,C_judge_checks_reused=538,execution_authorized_by_current_user=False,dynamic_S0_S1_qualified=False,scope='Host preparation only. Ready for a separately authorized bounded two-role calibration, not full acceptance.')
            save(N/'host/RESULT.json',result)
        print(result['status'],flush=True);return 0
    except BaseException as e:
        result.update(status='FAIL_HOST_ADMISSION',ended_utc=now(),elapsed_seconds=time.monotonic()-start,failure=type(e).__name__+': '+str(e),traceback=traceback.format_exc())
        save(N/'host/RESULT.json',result);print(result['status'],flush=True);return 1
if __name__=='__main__':sys.exit(main())
