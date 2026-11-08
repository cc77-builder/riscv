"""Process original full logs with their original R2 binding. No target execution."""
from pathlib import Path
import sys,json,hashlib
N=Path(__file__).resolve().parent.parent
R2=N.parent/'sp1-e-o2-cancel-calibration-r2-20261107'
sys.path.insert(0,str(R2/'runtime'))
import adapter

def pin(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    r1=json.loads((R2/'R1_EVIDENCE.json').read_text())
    runs=[('R1-bit100','bit100',Path(r1['stdout']['path']).parent),('R2-bit100','bit100',R2/'target-01/01-bit100'),('R2-normal','candidate-normal',R2/'target-01/02-candidate-normal')]
    result=[]
    for label,role,d in runs:
        receipt=json.loads((d/'record.json').read_text())
        raw=[]
        for stream in ['stdout','stderr']:
            f=d/(stream+'.log');assert pin(f)['sha256']==receipt['raw_sha256'][stream];raw.append(f.read_text())
        parsed=adapter.collect(''.join(raw),role,receipt['exit_code'])
        expected='NEW_GUARD_BIT100_LOG_PASS' if role=='bit100' else 'SUPPLEMENT_TRACE_NOT_HIT'
        assert parsed['status']==expected
        result.append({'label':label,'status':parsed['status'],'record':pin(d/'record.json'),'stdout':pin(d/'stdout.log'),'stderr':pin(d/'stderr.log'),'old_FAIL_and_NOT_HIT_retained':True,'new_target_qualification':False})
    print(json.dumps({'status':'PASS_OLD_REAL_LOGS_ORIGINAL_BINDING','results':result,'new_targets':0,'native_reference_loads':0},indent=2))
if __name__=='__main__':main()
