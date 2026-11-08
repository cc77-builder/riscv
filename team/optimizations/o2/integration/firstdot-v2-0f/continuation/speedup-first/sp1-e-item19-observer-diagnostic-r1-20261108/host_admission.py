from pathlib import Path
import sys,time,json,subprocess,traceback,resource,os
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
import runner,sched_trace,adapter
from common import save,read,need,now
from test_sched import S,u,inp,out

def main():
 start=read(N/'external-host/START.json')['started_monotonic'];result={'status':'RUNNING','target_runs':0}
 try:
  with runner.host_deadline(start+900):
   t=time.monotonic();runner.verify();hash_seconds=time.monotonic()-t
   command=[sys.executable,'-B','-m','unittest','-v','test_sched','test_streaming','test_diagnostic']
   with (N/'host/tests.log').open('w')as outlog:
    a=subprocess.run(command,cwd=N/'runtime',stdout=outlog,stderr=subprocess.STDOUT,timeout=max(.1,start+900-time.monotonic()))
   need(a.returncode==0,'difference tests fail')
   path=N/'host/stress.log';count=100000
   with path.open('w')as f:
    f.write(S)
    for i in range(count):
     c=3*i+1;rr=str((i//48)%2)+':'+str(i%48);f.write(u(c,rr)+inp(c+1,rr)+out(c+2,rr))
   t=time.monotonic()
   with path.open()as f:stress=sched_trace.audit_stream(f,response_sink=lambda row:None)
   parse_seconds=time.monotonic()-t
   need(stress['response_count']==count and stress['pending_at_end']==0,'stress complete lifetime')
   old=Path(read(N/'CONTRACT.json')['legacy_logs'])/'02-candidate-normal';text=(old/'stdout.log').read_text()+(old/'stderr.log').read_text()
   t=time.monotonic();normal=adapter.collect(text,'candidate-normal',0);legacy_seconds=time.monotonic()-t
   # Capacity screen, not an assertion of simulator throughput.
   projected=30+12*hash_seconds+3*parse_seconds*(864000000/path.stat().st_size)+2*legacy_seconds*(128*1024*1024/len(text.encode()))
   cost={'hash_seconds':hash_seconds,'stress_bytes':path.stat().st_size,'stress_transactions':count,'stream_parse_seconds':parse_seconds,'legacy_bytes':len(text.encode()),'legacy_seconds':legacy_seconds,'estimated_host_seconds':projected,'limit':900,'peak_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'target_cost':'NOT_MEASURED; bounded diagnostic risk accepted by current goal','log_stop_bytes':2147483648}
   save(N/'host/COST.json',cost);need(projected<900,'host estimate exceeds cap')
   runner.verify()
   result.update(status='PASS_HOST_ADMISSION',elapsed_seconds=time.monotonic()-start,tests=14,cost=cost,diagnostic_only=True,item19_qualified=False,scope='full sideband identity controls plus unchanged real M1 collectors; externally bounded target risk, not completion guarantee')
 except BaseException as e:result.update(status='FAIL_HOST_ADMISSION',failure=repr(e),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-start)
 save(N/'host/RESULT.json',result);print(result['status'],flush=True);return int(result['status']!='PASS_HOST_ADMISSION')
if __name__=='__main__':sys.exit(main())
