"""Fixed one-shot external guardian for the approved2100s campaign."""
from pathlib import Path
import os,sys,json
N=Path(__file__).resolve().parent;sys.path.insert(0,str(N/'runtime'))
from common import exclusive,read,need,now
from watchdog import run_guard
if __name__=='__main__':
 c=read(N/'CONTRACT.json');need(c['limits']['outer_seconds']==2100,'exact cap')
 exclusive(N/'LAUNCH.used.json',{'utc':now(),'operation_id':c['operation_id'],'retry_permitted':False})
 os.sched_setaffinity(0,{4})
 result=run_guard([sys.executable,'-B',str(N/'campaign.py')],N,N/'external-batch',2100,True,'batch')
 print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'cleanup_ok':result['cleanup_ok']}))
 sys.exit(0 if result['status']=='GUARD_PASS' else 1)
