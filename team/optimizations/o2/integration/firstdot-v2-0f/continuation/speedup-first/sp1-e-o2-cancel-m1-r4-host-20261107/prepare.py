#!/usr/bin/env python3
"""R4 one-shot GNU/static preparation. Never execute EMU/NEMU or load references."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time,traceback
N=Path(__file__).resolve().parent
OLD=N.parent/'sp1-e-o2-cancel-host-20261107'
R2=N.parent/'sp1-e-o2-cancel-calibration-r2-20261107'
def pin(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def save(name,v):(N/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    os.sched_setaffinity(0,{4})
    with (N/'PREP.used.json').open('x') as f:json.dump({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'retry':False},f)
    steps=[];start=time.monotonic();status='FAIL_PREPARATION';failure=None
    def run(name,argv):
        t=time.monotonic()
        with (N/'review'/ (name+'.stdout')).open('wb') as out, (N/'review'/(name+'.stderr')).open('wb') as err:
            proc=subprocess.run(argv,cwd=N,stdout=out,stderr=err,timeout=300,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        steps.append({'name':name,'argv':argv,'exit_code':proc.returncode,'seconds':time.monotonic()-t})
        save('PREP_COMMANDS.json',steps)
        if proc.returncode:raise RuntimeError(name+' failed; no retry')
    try:
        run('generate',[sys.executable,'-B',str(N/'software/generate.py')])
        unchanged=[]
        for name in ['main.c','judge.c','data.c','contract.h','cases.h']:
            a=pin(OLD/'software'/name);b=pin(N/'software'/name)
            if a['sha256']!=b['sha256']:raise ValueError('original C/data contract drift '+name)
            unchanged.append({'name':name,'source':a,'new':b})
        save('UNCHANGED_SOFTWARE.json',unchanged)
        run('gnu-build',[sys.executable,'-B',str(N/'build-review/build.py'),'attempt-01'])
        run('object-audit',[sys.executable,'-B',str(N/'build-review/audit.py'),str(N/'build-review/attempt-01')])
        m=json.loads((N/'software/manifest.json').read_text())
        pc={'schema':'sp1-e-o2-cancel-pc-contract-v1','software_manifest':pin(N/'software/manifest.json'),'pc_roles':{str(x['pc']):x for x in m['pc_roles']},'expected_commits':77,'expected_retired_pc_sequence':m['expected_retired_pc_sequence'],'call_plan':m['call_plan'],'uart_protocol':m['uart_protocol'],'images':m['images'],'scope':'M1 new frozen image binding; no actual target evidence'}
        save('host/PC_CONTRACT.json',pc);save('runtime/PC_CONTRACT.json',pc)
        run('negative-build',[sys.executable,'-B',str(N/'negative/build.py')])
        c=json.loads((R2/'CONTRACT.json').read_text());c['operation_id']='SP1-E-O2-CANCEL-M1-R4-HOST-20261107-01';c['software_manifest']=pin(N/'software/manifest.json')
        c['runtime'].update(elf=m['images']['elf'],bin=m['images']['bin'],negative_reference=pin(N/'negative/o2-cancel-negative-reference.so'))
        c['guard']={k:m['guard'][k] for k in ['pc','word','vd']};c['guard']['bit']=100
        c['cwd']=str(N/'runtime');c['user_authorized_if_host_passes']=False
        c['target_permission']='REQUIRES_SEPARATE_EXPLICIT_EXECUTION_REQUEST'
        c['design_contract']=pin(N.parent/'sp1-e-o2-cancel-r3-readonly-20261107/DESIGN_CONTRACT.json')
        save('CONTRACT.json',c)
        status='PASS_GNU_OBJECT_BIT100_PREPARATION_ONLY'
    except BaseException as e:
        failure={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    save('PREP_RESULT.json',{'status':status,'elapsed_seconds':time.monotonic()-start,'steps':steps,'failure':failure,'target_processes':0,'native_reference_loads':0,'retry':False})
    print(status,flush=True)
    return 0 if failure is None else 1
if __name__=='__main__':sys.exit(main())
