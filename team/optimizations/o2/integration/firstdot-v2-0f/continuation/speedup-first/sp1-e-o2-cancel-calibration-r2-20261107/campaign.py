"""One externally supervised admission+execution, one shared host/outer budget."""
from pathlib import Path
import json,os,sys,time,subprocess,traceback,re
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
import runner,adapter
from common import read,save,exclusive,sha,now,need
from watchdog import require_batch_guard,publish_deadline
sys.path.insert(0,str(N/'host'))
import review,reuse_passed,tag_review

def main():
 require_batch_guard(N);start=read(N/'external-batch/START.json')['started_monotonic'];deadline=start+900
 publish_deadline(deadline,'HOST');exclusive(N/'ADMISSION.used.json',{'started_monotonic':start,'utc':now(),'retry_permitted':False})
 result={'status':'RUNNING','started_utc':now(),'target_runs':0}
 try:
  with runner.host_deadline(deadline):
   t=time.monotonic();runner.verify();hash_seconds=time.monotonic()-t
   reused=reuse_passed.verify();save(N/'review/REUSE_RESULT.json',reused)
   env=dict(os.environ);env['PYTHONPATH']=str(N/'runtime')+':'+str(N/'host');env['PYTHONDONTWRITEBYTECODE']='1'
   cmd=[sys.executable,'-B','-m','unittest','-v','-f','test_tags.Tags','test_delta.Delta.test_01_unchanged_sources_and_frozen_manifest','test_delta.Delta.test_02_actual_ELF_guard_and_group_positive','test_delta.Delta.test_03_guard_binding_negative_controls','test_delta.Delta.test_08_cold_import_closed_source_and_no_target_authorization','test_delta.Delta.test_09_mutation_effect_assertions']
   with (N/'host/tests.log').open('wb') as out:
    completed=subprocess.run(cmd,cwd=N/'host',env=env,stdout=out,stderr=subprocess.STDOUT,timeout=max(.1,deadline-time.monotonic()))
   need(completed.returncode==0,'HOST_DELTA_TEST_FAIL')
   independent=review.review();independent['tag_review']=tag_review.review();save(N/'review/RESULT.json',independent)
   # Measure new parse/call paths and a finite idle-state stress fixture; no target.
   from fixtures_local import normal,negative
   from test_tags import raw_real
   t=time.monotonic();adapter.collect(raw_real(),'bit100',1);negative_seconds=time.monotonic()-t
   base=normal();t=time.monotonic();adapter.collect(base,'candidate-normal',0);normal_seconds=time.monotonic()-t
   state_lines=[x for x in base.splitlines() if x.startswith('SP1_STATE ')];last=state_lines[-1];lastcycle=int(re.search(r'cycle=(\d+)',last)[1]);stress=base+'\n'.join(re.sub(r'cycle=\d+','cycle='+str(lastcycle+i),last,count=1) for i in range(1,50001))+'\n'
   t=time.monotonic();adapter.collect(stress,'candidate-normal',0);stress_seconds=time.monotonic()-t
   # Six times300k/50k stress plus repeated hashes, admission time and25s allowance.
   host_so_far=time.monotonic()-start;estimate=host_so_far+12*hash_seconds+36*stress_seconds+4*negative_seconds+25
   cost={'status':'PASS_HOST_COST' if estimate<900 else 'HOLD_HOST_COST','measured_hash_seconds':hash_seconds,'negative_seconds':negative_seconds,'normal_seconds':normal_seconds,'stress_seconds':stress_seconds,'stress_extra_states':50000,'new_complete_call_fixture':'41 calls /77 retired custom; synthetic only','conservative_screen_seconds':estimate,'cap_seconds':900,'model':'actual new-path sample;36x stress allowance for300k state scale and6x event/host variability,12 hashes plus25s; not a mathematical completion guarantee; external900 host stop remains authoritative'}
   save(N/'host/COST.json',cost);need(estimate<900,'HOST_COST_NOT_ADMITTED')
   runner.verify()
   result.update(status='PASS_HOST_ADMISSION',ended_utc=now(),host_seconds_so_far=time.monotonic()-start,cost=cost,independent=independent,methods=9,reused_methods=4,reuse_evidence=reused,execution_authorized_by_current_user=True)
   save(N/'host/RESULT.json',result)
   exclusive(N/'RUN_AUTHORIZATION.json',{'operation_id':runner.C['operation_id'],'user_instruction_sha256':sha(N/'USER_INSTRUCTION.txt'),'freeze_sha256':sha(N/'EXECUTION_FREEZE.json'),'contract_sha256':sha(N/'CONTRACT.json'),'host_result_sha256':sha(N/'host/RESULT.json'),'roles':runner.ROLES,'limits':runner.C['limits'],'allow_retry':False,'basis':'current user explicitly authorizes two targets only after host admission'})
  outcome=runner.execute();return 0 if outcome['status']=='CALIBRATION_TRIGGER_HIT_ONLY' else 1
 except BaseException as e:
  if result['status']!='PASS_HOST_ADMISSION':
   result.update(status='FAIL_HOST_ADMISSION',failure=type(e).__name__+': '+str(e),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-start);save(N/'host/RESULT.json',result)
  else:save(N/'UNHANDLED_FAILURE.json',{'failure':str(e),'traceback':traceback.format_exc()})
  return 1

if __name__=='__main__':sys.exit(main())
