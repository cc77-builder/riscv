from pathlib import Path
import sys,subprocess,time,traceback,json
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
import runner,adapter
from common import read,save,need
from fixtures_local import normal,negative

def main():
 start=read(N/'external-host/START.json')['started_monotonic'];out={'status':'RUNNING','target_runs':0}
 try:
  with runner.host_deadline(start+900):
   t=time.monotonic();runner.verify();hash_seconds=time.monotonic()-t
   with (N/'host/tests.log').open('w')as f:
    a=subprocess.run([sys.executable,'-B','-m','unittest','-v','test_m4'],cwd=N/'runtime',stdout=f,stderr=subprocess.STDOUT,timeout=max(.1,start+900-time.monotonic()))
   need(a.returncode==0,'M4 delta tests failed')
   t=time.monotonic();a=adapter.collect(normal(),'candidate-normal',0);b=adapter.collect(negative(2,2),'bit100',1);parse=time.monotonic()-t
   reused=read(N.parent/'sp1-e-item19-observer-diagnostic-r1-20261108/host/COST.json');estimate=reused['estimated_host_seconds']+12*hash_seconds+4*parse+10
   need(estimate<900,'host budget')
   need(a['status']=='SUPPLEMENT_TRACE_HIT'and b['status']=='NEW_GUARD_BIT100_LOG_PASS','host functional controls')
   runner.verify();out.update(status='PASS_HOST_ADMISSION',elapsed_seconds=time.monotonic()-start,tests=5,sequence_negatives=64,full_41_call_fixture=True,estimated_host_seconds=estimate,normal_budget_basis_seconds=580.93080918,new_normal_stop_seconds=900,original_538_C_judge_reused=True,item19_qualified=False)
 except BaseException as e:out.update(status='FAIL_HOST_ADMISSION',failure=repr(e),traceback=traceback.format_exc())
 save(N/'host/RESULT.json',out);print(out['status']);return int(out['status']!='PASS_HOST_ADMISSION')
if __name__=='__main__':sys.exit(main())
