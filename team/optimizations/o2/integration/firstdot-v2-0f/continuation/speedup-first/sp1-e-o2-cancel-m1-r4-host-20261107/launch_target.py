"""Prepared two-role entry; requires a separate explicit future execution request."""
from pathlib import Path
import os,sys,json
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
import runner
from common import exclusive,read,need,now
from watchdog import run_guard

def main():
    # Must reject missing permission BEFORE locks/guardian/target subprocess.
    runner.verify();runner.validate_auth()
    c=read(N/'CONTRACT.json');need(c['limits']['outer_seconds']==2100,'exact cap')
    exclusive(N/'LAUNCH.used.json',{'utc':now(),'operation_id':c['operation_id'],'retry_permitted':False})
    os.sched_setaffinity(0,{4})
    result=run_guard([sys.executable,'-B',str(N/'target_campaign.py')],N,N/'external-batch',2100,True,'batch')
    print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'cleanup_ok':result['cleanup_ok']}))
    return 0 if result['status']=='GUARD_PASS' else 1
if __name__=='__main__':sys.exit(main())
