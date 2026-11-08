"""Exactly one 900s host-only admission; target entry is separate and not invoked."""
from pathlib import Path
import os,sys,json
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N/'runtime'))
from watchdog import run_guard
from common import exclusive,now
if __name__=='__main__':
    exclusive(N/'HOST_LAUNCH.used.json',{'utc':now(),'retry_permitted':False,'target_permission':False})
    os.sched_setaffinity(0,{4})
    result=run_guard([sys.executable,'-B',str(N/'host_admission.py')],N,N/'external-host',900,False,'host-only-budget')
    print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'cleanup_ok':result['cleanup_ok']}))
    sys.exit(0 if result['status']=='GUARD_PASS' else 1)
