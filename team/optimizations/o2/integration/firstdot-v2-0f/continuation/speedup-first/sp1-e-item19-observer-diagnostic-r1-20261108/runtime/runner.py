"""Exactly two ordered target roles, fail-stop, immutable new image; no retry entry."""
from pathlib import Path
import argparse,contextlib,importlib.util,json,os,signal,sys,time,traceback
from common import need,read,save,exclusive,sha,now
from supervisor import run_group
from watchdog import publish_deadline,require_batch_guard
import adapter,diagnostic
N=Path(__file__).resolve().parent.parent
C=read(N/'CONTRACT.json')
ROLES=C['roles']

def pin(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}

def plan(role):
    spec=next(s for s in ROLES if s['name']==role);r=C['runtime']
    argv=[r['candidate_emu']['path'],'-i',r['bin']['path'],'--flash='+r['flash']['path'],'--ram-size=128MB','--diff='+r[spec['reference']]['path'],'--max-cycles='+str(spec['guest_cycles']-16),'--seed=1','--no-snapshot']
    env=dict(C['env'])
    if role=='bit100':env['SP1_CHAIN_BIT100']='1'
    return argv,env,C['cwd']

def verify():
    f=read(N/'EXECUTION_FREEZE.json')
    for row in f['files']:need(pin(row['path'])==row,'frozen input changed '+row['path'])
    allowed={x['path'] for x in f['files']}
    for m in list(sys.modules.values()):
        name=getattr(m,'__file__',None)
        if name and name.startswith('/home/') and name.endswith('.py'):need(str(Path(name).resolve()) in allowed,'loaded source omitted '+name)
    need(f['roles']==ROLES and f['limits']==C['limits'],'frozen role/limit drift')
    return f

def validate_auth():
    a=read(N/'RUN_AUTHORIZATION.json')
    need(C['user_authorized_if_host_passes'] and C['diagnostic_only'],'current autonomous goal binds diagnostic scope')
    need(a['operation_id']==C['operation_id'] and a['user_instruction_sha256']==sha(N/'EXECUTION_REQUEST.txt'),'explicit current task binding')
    need(a['freeze_sha256']==sha(N/'EXECUTION_FREEZE.json') and a['contract_sha256']==sha(N/'CONTRACT.json'),'authorization frozen identity')
    need(a['roles']==ROLES and a['limits']==C['limits'] and a['allow_retry'] is False,'exact authorized roles/caps')
    need(read(N/'host/RESULT.json')['status']=='PASS_HOST_ADMISSION','host admission must pass')
    need(a['host_result_sha256']==sha(N/'host/RESULT.json'),'exact host result bound')
    return sha(N/'RUN_AUTHORIZATION.json')

def receipt(role,rd,limits):
    spec=next(s for s in ROLES if s['name']==role);r=read(rd/'record.json');launch=read(rd/'launch.json');ident=read(rd/'execution-identity.json')
    argv,env,cwd=plan(role)
    need(r['role']==launch['role']==role and r['limits']==launch['limits']==limits,'role and limits')
    need(r['resource_ok'] and r['cleanup_ok'] and r['stop_reason'] is None and r['exception'] is None and r['cleanup_error'] is None,'resource/cleanup failed '+str(r['stop_reason']))
    need(r['exit_code']==spec['expected_exit'],'unexpected role exit')
    need(0<r['guest_cycles']<=spec['guest_cycles'] and r['elapsed_seconds']<=spec['wall_seconds'],'role wall/guest bound')
    need(r['boot_id']==launch['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'current boot')
    need(r['execution_identity']==ident and ident['pid']==r['pid']==ident['process']['pgid']==ident['process']['sid'],'live PID/PGID identity')
    need(ident['process']['start_ticks']==r['known_pid_start_ticks'][str(r['pid'])],'birth identity')
    need(ident['command']==r['command']==launch['command']==argv and ident['environment']==launch['env']==env and ident['cwd']==r['cwd']==launch['cwd']==cwd,'actual argv/environment/cwd')
    need(ident['executable']==C['runtime']['candidate_emu']['path'] and ident['executable_sha256']==C['runtime']['candidate_emu']['sha256'],'actual candidate binary')
    need(r['process_started'] and r['observed_bytes']==r['retained_bytes'] and not r['raw_truncated'],'complete target logs')
    for stream in ('stdout','stderr'):
        q=rd/(stream+'.log');need(q.stat().st_size==r['retained_bytes'][stream] and sha(q)==r['raw_sha256'][stream],'raw hash/length')
    samples=[json.loads(line) for line in (rd/'telemetry.jsonl').read_text().splitlines()]
    need(samples and len(samples)==r['sample_count'],'sample completeness')
    need(max(x['threads'] for x in samples)==r['peak_threads']<=4 and max(x['rss_bytes'] for x in samples)==r['peak_rss_bytes']<=12884901888,'sampled group caps')
    for x in samples:
        need(all(t['cpu_affinity']=='4' for row in x['live_processes'] for t in row['tids']),'all TIDs CPU4')
        need(all(row['pgid']==r['pid'] and row['start_ticks']==r['known_pid_start_ticks'][str(row['pid'])] for row in x['processes']),'sample group births')
    need(not r['final_snapshot']['processes'],'owned group empty')
    refs={C['runtime']['normal_reference']['path']}
    if role=='bit100':refs.add(C['runtime']['negative_reference']['path'])
    need(refs<=set(r['observed_mapped_files']) and all(r['observed_mapped_files'][s]['pid']==r['pid'] for s in refs),'observed native reference mappings')
    return {'status':'ACTUAL_RUNTIME_RECEIPT_PASS','role':role,'pid':r['pid'],'start_ticks':ident['process']['start_ticks'],'boot_id':r['boot_id'],'guest_cycles':r['guest_cycles'],'files':{name:pin(rd/name) for name in ['record.json','launch.json','execution-identity.json','telemetry.jsonl','stdout.log','stderr.log']},'resource_scope':'sampled entire PGID at nominal50ms, not instantaneous kernel ceiling'}

@contextlib.contextmanager
def host_deadline(deadline):
    publish_deadline(deadline,'HOST');remaining=deadline-time.monotonic();need(remaining>0,'host/outer deadline')
    def expired(sig,frame):raise TimeoutError('HOST_BUDGET_LIMIT')
    old=signal.signal(signal.SIGALRM,expired);timer=signal.setitimer(signal.ITIMER_REAL,remaining)
    try:yield
    finally:signal.setitimer(signal.ITIMER_REAL,*timer);signal.signal(signal.SIGALRM,old)

def schedule(run,check):
    """Single role order used by both host fake receipts and actual execution."""
    results=[]
    for s in ROLES:
        value=run(s);check(s,value);results.append(value)
    return results

def execute():
    require_batch_guard(N);a=validate_auth();guard=read(N/'external-batch/START.json');start=guard['started_monotonic'];caps=C['limits'];outer=start+caps['outer_seconds']
    need(guard['wall_limit_seconds']==caps['outer_seconds'] and guard['mode']=='batch','exact external guard')
    exclusive(N/'BATCH.used.json',{'operation_id':C['operation_id'],'started_utc':now(),'started_monotonic':start,'boot_id':guard['boot_id'],'authorization_sha256':a,'retry_permitted':False})
    out=N/'target-01';out.mkdir(exist_ok=False)
    state={'status':'RUNNING','started_utc':now(),'started_monotonic':start,'roles':[],'target_processes_started':0,'launch_attempts':0,'target_active_seconds':0,'log_bytes':0,'item19_qualified':False,'performance_qualified':False}
    save(out/'batch.json',state)
    def deadline():return min(outer,start+state['target_active_seconds']+caps['host_seconds'])
    def precheck():
        need(validate_auth()==a,'authorization drift');verify()
        need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==guard['boot_id'],'batch boot drift')
    def run(s):
        with host_deadline(deadline()):
            precheck();argv,env,cwd=plan(s['name']);index=ROLES.index(s)+1;rd=out/('%02d-%s'%(index,s['name']))
            lim={k:caps[k] for k in ['cpu_affinity','thread_cap','rss_cap_bytes']};lim.update(wall_seconds=min(s['wall_seconds'],caps['target_seconds']-state['target_active_seconds']),guest_cycles=s['guest_cycles'],log_cap_bytes=caps['log_cap_bytes']-state['log_bytes'])
            exclusive(out/('%02d-launch.json'%index),{'role':s['name'],'command':argv,'limits':lim,'authorization_sha256':a,'utc':now()});state['launch_attempts']+=1;save(out/'batch.json',state)
        publish_deadline(min(outer,time.monotonic()+lim['wall_seconds']),'TARGET')
        measured=run_group(argv,cwd,env,rd,lim,outer_deadline=outer,role=s['name'])
        state['target_active_seconds']+=measured['active_wall_seconds'];state['log_bytes']+=sum(measured['retained_bytes'].values());state['target_processes_started']+=int(measured['process_started'])
        publish_deadline(deadline(),'HOST');save(out/'batch.json',state)
        return {'directory':str(rd),'limits':lim,'measurement':measured}
    def check(s,value):
        with host_deadline(deadline()):
            precheck();rd=Path(value['directory']);rc=receipt(s['name'],rd,value['limits']);parsed=diagnostic.collect(rd,s['name'],value['measurement']['exit_code'])
            if s['name']=='candidate-normal':need(parsed['guest_cycles']==rc['guest_cycles'],'normal guest receipt agreement')
            save(rd/'validation.json',{'runtime':rc,'collector':parsed,'actual_target':True,'item19_qualified':False})
            state['roles'].append({'role':s['name'],'status':parsed['status'],'guest_cycles':rc['guest_cycles'],'active_seconds':value['measurement']['active_wall_seconds'],'validation':pin(rd/'validation.json')});save(out/'batch.json',state)
            if s['name']=='candidate-normal':need(parsed['status'] in ('SUPPLEMENT_TRACE_HIT','SUPPLEMENT_TRACE_NOT_HIT'),'diagnostic complete result required')
            need(state['target_active_seconds']<=caps['target_seconds'] and state['log_bytes']<=caps['log_cap_bytes'],'batch caps')
    try:
        schedule(run,check)
        with host_deadline(deadline()):precheck();state['status']='DIAGNOSTIC_COMPLETE_ONLY'
    except BaseException as e:
        state.update(status='NOT_HIT' if 'NOT_HIT_COMPLETED' in str(e) else 'STOPPED',failure=type(e).__name__+': '+str(e),traceback=traceback.format_exc())
    state.update(ended_utc=now(),elapsed_seconds=time.monotonic()-start,host_seconds=time.monotonic()-start-state['target_active_seconds']);save(out/'batch.json',state)
    return state

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['run','verify']);a=ap.parse_args()
    if a.action=='verify':verify();print('FROZEN_INPUTS_MATCH')
    else:
        result=execute();print(json.dumps({'status':result['status']}));sys.exit(0 if result['status']=='DIAGNOSTIC_COMPLETE_ONLY' else 1)
