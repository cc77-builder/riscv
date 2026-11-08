"""B4 bounded complete-call calibration. Import/host commands never launch targets."""
from pathlib import Path
import argparse,ast,contextlib,hashlib,importlib.util,json,os,signal,sys,time,traceback
from common import need,now,read,save,exclusive,sha
from supervisor import run_group
from watchdog import publish_deadline,require_batch_guard
HERE=Path(__file__).resolve().parent
PACKAGE=HERE.parent
CASE_IDS=('o2-control','original-c8-c48')
ROLE_NAMES=('bit100','candidate-full','baseline-full')
ADAPTER_DIRS={'o2-control':'/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r2-20261106/o2-control','original-c8-c48':'/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/c48/adapter-r1'}
SCOPES=('HOST_FIXTURE','HISTORICAL_LOG','TARGET_LOG_REQUIRES_RUNTIME_RECEIPT')
ENV={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/home/riscv','LANG':'C.UTF-8','LC_ALL':'C','OMP_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
KNOBS={'cpu_affinity':[4],'group_threads_max':4,'rss_cap_bytes':12884901888,'logs_cap_bytes':2147483648,'ram':'128MB','seed':1}
MODE={'reset':'fresh','checkpoint':False,'debug':False,'singlestep':False}
BUDGETS={'negative_wall_seconds':300,'normal_wall_seconds':2400,'negative_guest_cycles':100000,'normal_guest_cycles':1500000,'case_target_seconds':5100,'case_outer_seconds':6000,'case_host_seconds':900,'batch_max_processes':6,'batch_target_seconds':10200,'batch_outer_seconds':12000}
BASE_FREEZE_PIN={'path': '/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r7-20261106/cases/legacy-control/EXECUTION_FREEZE.json', 'bytes': 339388, 'sha256': 'c224b850fb57693ddec00557696adfa7b89088283f9ea6401d7c427669b6528a'}
_ADAPTERS={}

def objsha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def pin(path):
 p=Path(path);need(p.is_absolute() and p.is_file(),'existing absolute declared input '+str(p))
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def check_pin(item):need(pin(item['path'])==item,'declared path/bytes/SHA drift '+str(item['path']))
def contract():
 c=read(PACKAGE/'CALIBRATION_CONTRACT.json')
 need(c.get('schema')=='sp1-e-b4-complete-call-calibration-v1' and c.get('status')=='FROZEN_HOST_CONTRACT','root frozen host calibration contract required')
 need(c.get('case_ids')==list(CASE_IDS) and c.get('roles')==list(ROLE_NAMES),'exact two-load three-role calibration scope')
 need(c.get('budgets')==BUDGETS and c.get('resources')==KNOBS and c.get('mode')==MODE,'frozen explicit proposal caps/resources; no budget borrowing')
 return c

def case_root(case):
 need(case in CASE_IDS,'only two frozen calibration cases')
 return PACKAGE/'cases-r1'/case

def roles(case):
 case_root(case);b=contract()['budgets']
 return [(name,b['negative_wall_seconds'] if i==0 else b['normal_wall_seconds'],b['negative_guest_cycles'] if i==0 else b['normal_guest_cycles']) for i,name in enumerate(ROLE_NAMES)]

def source_version():
 paths=set(HERE.glob('*.py'))
 for directory in ADAPTER_DIRS.values():
  root=PACKAGE/directory;paths.update(root.glob('*.py'))
  closure=root/'SOURCE_FREEZE.json'
  need(closure.is_file(),'final adapter source closure required '+str(closure))
  for item in read(closure)['files']:
   if item['path'].endswith('.py'):paths.add(Path(item['path']))
 return {'schema':'sp1-e-b4-calibration-runtime-source-v1','source_sha256':{str(p):sha(p) for p in sorted(paths)}}

def validate_version():
 value=read(HERE/'SOURCE_VERSION.json');need(value==source_version(),'current calibration source drift')
 prior=Path(BASE_FREEZE_PIN['path']).parents[2]/'runtime'
 for name in ('common.py','supervisor.py','watchdog.py'):need(sha(HERE/name)==sha(prior/name),'unchanged R7 supervisor/guardian '+name)
 return value

def load_adapter(case):
 case_root(case)
 if case not in _ADAPTERS:
  path=PACKAGE/ADAPTER_DIRS[case]/'adapter.py'
  spec=importlib.util.spec_from_file_location('b4_adapter_'+case.replace('-','_'),path)
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);_ADAPTERS[case]=module
 return _ADAPTERS[case]

def case_data(case):
 adapter=load_adapter(case);d=adapter.descriptor();need(d.get('case_id')==case,'adapter canonical case binding')
 check_pin(BASE_FREEZE_PIN);base=read(BASE_FREEZE_PIN['path']);runtime=dict(d['runtime'])
 need(set(runtime)=={'bin','elf','normal_reference','negative_reference'},'adapter exact four runtime artifacts')
 for key in ('candidate_emu','baseline_emu','flash'):runtime[key]=base['contract']['runtime'][key]
 need(runtime['candidate_emu']['sha256']!=runtime['baseline_emu']['sha256'],'distinct tested hardware candidates')
 need(runtime['negative_reference']['sha256']!=runtime['normal_reference']['sha256'],'case-specific fault reference distinct')
 negative_env=d['negative_environment'];need(isinstance(negative_env,dict) and negative_env and all(isinstance(k,str) and isinstance(v,str) for k,v in negative_env.items()),'frozen native injection environment')
 need(not set(negative_env)&set(ENV),'negative switch does not overwrite sanitized environment')
 return {'case_id':case,'contract_id':'SP1-E-B4-CALIBRATION-'+case.upper()+'-v1','runtime':runtime,'runtime_cwd':base['contract']['runtime_cwd'],'negative_environment':negative_env,'input_files':d['input_files'],'normal_pass_status':d['normal_pass_status'],'negative_pass_status':d['negative_pass_status'],'comparison_fields':d['comparison_fields'],'coverage':d['coverage'],'roles':roles(case),'calibration_only':True}

def inventory(case):
 d=case_data(case);validate_version();pins={}
 def add(item):
  check_pin(item)
  if item['path'] in pins:need(pins[item['path']]==item,'conflicting frozen identity')
  pins[item['path']]=item
 for p in (PACKAGE/'CALIBRATION_CONTRACT.json',HERE/'SOURCE_VERSION.json'):add(pin(p))
 for path in source_version()['source_sha256']:add(pin(path))
 add(BASE_FREEZE_PIN)
 for item in d['runtime'].values():add(item)
 # Both adapters are imported by the initial two-case verify; freeze their shared loaded-source closure.
 for other in CASE_IDS:
  descriptor=load_adapter(other).descriptor()
  for item in descriptor['input_files']:add(item)
  for name in ('CONTRACT.json','SOURCE_PINS.json','SOURCE_FREEZE.json'):
   metadata=PACKAGE/ADAPTER_DIRS[other]/name
   if metadata.is_file():
    add(pin(metadata))
    if name=='SOURCE_FREEZE.json':
     for dependency in read(metadata)['files']:add(dependency)
 old={x['path']:x for x in read(BASE_FREEZE_PIN['path'])['files']}
 for cwd in d['runtime_cwd'].values():
  for name in ('constantin.txt','plusArgs'):
   path=str(Path(cwd)/'build'/name);need(path in old,'tested runtime cwd support omitted');add(old[path])
 return {'schema':'sp1-e-b4-calibration-input-freeze-v1','case_id':case,'contract':d,'calibration_contract':pin(PACKAGE/'CALIBRATION_CONTRACT.json'),'runtime_version':pin(HERE/'SOURCE_VERSION.json'),'files':sorted(pins.values(),key=lambda x:x['path']),'role_plan':roles(case),'budget':contract()['budgets'],'execution_authorized':False,'formal_acceptance_qualified':False}

def verify(case):
 frozen=read(case_root(case)/'EXECUTION_FREEZE.json');need(frozen==json.loads(json.dumps(inventory(case))),'frozen complete calibration inputs changed')
 return frozen

def admission():
 a=read(PACKAGE/'ADMISSION.json')
 need(a.get('schema')=='sp1-e-b4-calibration-admission-v1' and a.get('status')=='GO','host calibration admission required')
 need(a.get('case_ids')==list(CASE_IDS),'admission exact case order')
 need(a.get('runtime_version')==pin(HERE/'SOURCE_VERSION.json') and a.get('contract')==pin(PACKAGE/'CALIBRATION_CONTRACT.json'),'admission current source/contract binding')
 need(isinstance(a.get('evidence'),dict) and bool(a['evidence']),'actual frozen host evidence required')
 for item in a['evidence'].values():
  check_pin(item['artifact']);need(read(item['artifact']['path']).get('status')==item['required_status'],'actual host evidence status')
 return a

def validate_authorization():
 path=PACKAGE/'RUN_AUTHORIZATION.json'
 need(path.is_file(),'NO_CURRENT_EXPLICIT_CALIBRATION_AUTHORIZATION')
 a=read(path);c=contract();admission()
 need(a.get('schema')=='sp1-e-b4-complete-call-calibration-authorization-v1' and a.get('authorize_target_run') is True,'new explicit complete-call calibration authorization required')
 need(a.get('case_ids')==list(CASE_IDS) and a.get('role_names')==list(ROLE_NAMES),'exact two cases and three calibration roles')
 need(a.get('runtime_version')==pin(HERE/'SOURCE_VERSION.json') and a.get('contract')==pin(PACKAGE/'CALIBRATION_CONTRACT.json') and a.get('admission')==pin(PACKAGE/'ADMISSION.json'),'authorization binds exact current host inputs')
 need(a.get('budgets')==c['budgets'] and a.get('serial') is True and a.get('retry_permitted') is False,'calibration caps/serial/no-retry binding')
 need(isinstance(a.get('user_instruction'),str) and len(a['user_instruction'])>=20,'actual separate user instruction required')
 need(a.get('output')==str(PACKAGE/'target-01'),'one fixed calibration output')
 need(isinstance(a.get('cases'),list) and len(a['cases'])==2,'both exact calibration input bindings')
 for case,row in zip(CASE_IDS,a['cases']):need(row.get('case_id')==case and row.get('freeze')==pin(case_root(case)/'EXECUTION_FREEZE.json') and row.get('output')==str(case_root(case)/'target-01'),'case input freeze/output binding')
 return a

class OuterDeadline(Exception):pass
@contextlib.contextmanager
def deadline_guard(deadline):
 publish_deadline(deadline)
 remaining=deadline-time.monotonic();need(remaining>0,'HOST_OR_OUTER_WALL_LIMIT')
 def expired(sig,frame):raise OuterDeadline('HOST_OR_OUTER_WALL_LIMIT')
 handler=signal.signal(signal.SIGALRM,expired);timer=signal.setitimer(signal.ITIMER_REAL,remaining)
 try:yield
 finally:signal.setitimer(signal.ITIMER_REAL,*timer);signal.signal(signal.SIGALRM,handler)

def execution_plan(case,role):
 d=case_data(case);need(role in ROLE_NAMES,'fixed calibration role')
 index=ROLE_NAMES.index(role);guest=roles(case)[index][2];label='baseline' if role=='baseline-full' else 'candidate'
 r=d['runtime'];ref=r['negative_reference' if index==0 else 'normal_reference']['path']
 command=[r[label+'_emu']['path'],'-i',r['bin']['path'],'--flash='+r['flash']['path'],'--ram-size=128MB','--diff='+ref,'--max-cycles='+str(guest-16),'--seed=1','--no-snapshot']
 env=dict(ENV)
 if index==0:env.update(d['negative_environment'])
 return command,env,d['runtime_cwd'][label]

def execution_boot(record_boot_id=...):
 """Actual batch boot only. Preparation snapshots may come from an older boot."""
 claim=read(PACKAGE/'BATCH.used.json')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 need(claim.get('boot_id')==boot,'actual batch execution boot changed')
 need(claim.get('case_ids')==list(CASE_IDS) and claim.get('authorization_sha256')==sha(PACKAGE/'RUN_AUTHORIZATION.json'),'actual batch claim scope/authorization changed')
 if record_boot_id is not ...:need(isinstance(record_boot_id,str) and record_boot_id==boot,'receipt is not from actual batch boot')
 return boot

def check_actual_receipt(case,role,role_dir):
 """Kernel-observed process origin, owned PGID resources, untouched complete logs."""
 p=Path(role_dir);record=read(p/'record.json');launch=read(p/'launch.json');identity=read(p/'execution-identity.json')
 d=case_data(case);command,env,cwd=execution_plan(case,role);label='baseline' if role.startswith('baseline-') else 'candidate'
 need(record.get('role')==launch.get('role')==role,'role receipt binding')
 need(p==case_root(case)/'target-01'/('%02d-%s'%(ROLE_NAMES.index(role)+1,role)),'fixed role output path')
 previous=[read(p.parent/('%02d-%s'%(i+1,r))/'record.json') for i,r in enumerate(ROLE_NAMES[:ROLE_NAMES.index(role)])]
 prior_active=sum(x['active_wall_seconds'] for x in previous)
 prior_logs=sum(sum(x['retained_bytes'].values()) for x in previous)
 _,wall_cap,guest_cap=next(x for x in roles(case) if x[0]==role)
 expected_limits={'wall_seconds':min(wall_cap,BUDGETS['case_target_seconds']-prior_active),'guest_cycles':guest_cap,'cpu_affinity':[4],'thread_cap':4,'rss_cap_bytes':12884901888,'log_cap_bytes':2147483648-prior_logs}
 need(record['limits']==launch['limits']==expected_limits,'exact per-role remaining resource limits')
 need(record['exception'] is None and record['cleanup_error'] is None,'no execution/cleanup exception')
 need(launch['boot_id']==record['boot_id'],'launch/execution boot identity')
 need(identity['process']['pid']==identity['process']['pgid']==identity['process']['sid']==record['pid'],'owned new session/process group')
 need(record.get('execution_identity')==identity,'identity receipt binding')
 need(identity['pid']==record['pid'] and identity['process']['start_ticks']==record['known_pid_start_ticks'].get(str(record['pid']),record['known_pid_start_ticks'].get(record['pid'])),'PID birth binding')
 need(identity['executable']==d['runtime'][label+'_emu']['path'] and identity['executable_sha256']==d['runtime'][label+'_emu']['sha256'],'actual executable; fixtures cannot qualify targets')
 need(identity['command']==record['command']==launch['command']==command,'exact actual argv')
 need(identity['environment']==launch['env']==env,'actual sanitized environment')
 need(identity['cwd']==record['cwd']==launch['cwd']==cwd,'actual working directory')
 need(identity['process']['tids'] and all(x['cpu_affinity']=='4' for x in identity['process']['tids']),'startup CPU4')
 need(record.get('process_started') and record['pid']>0,'actual target started')
 need(record.get('raw_truncated') is False and record['observed_bytes']==record['retained_bytes'],'complete output retained')
 for stream in ('stdout','stderr'):
  need((p/(stream+'.log')).stat().st_size==record['retained_bytes'][stream],'actual retained output bytes')
  need(sha(p/(stream+'.log'))==record['raw_sha256'][stream],'actual original raw log hash')
 samples=[]
 with (p/'telemetry.jsonl').open() as f:
  for line in f:samples.append(json.loads(line))
 need(samples and len(samples)==record['sample_count'],'complete telemetry')
 need(max(x['threads'] for x in samples)==record['peak_threads']<=4,'all-group thread cap')
 need(max(x['rss_bytes'] for x in samples)==record['peak_rss_bytes']<=12884901888,'all-group RSS cap')
 for x in samples:
  need(all(t['cpu_affinity']=='4' for row in x['live_processes'] for t in row['tids']),'all group CPU4')
  need(all(row['pgid']==record['pid'] and row['start_ticks']==record['known_pid_start_ticks'].get(str(row['pid']),record['known_pid_start_ticks'].get(row['pid'])) for row in x['processes']),'sampled owned PGID and birth identity')
 need(record['final_snapshot'] is not None and not record['final_snapshot']['processes'] and record['cleanup_ok'],'owned group empty/reaped')
 need(record['resource_ok'] and record['stop_reason'] is None and record['limit'] is None,'no resource failure')
 need(record['ended_monotonic']>=record['started_monotonic'] and abs(record['elapsed_seconds']-record['ended_monotonic']+record['started_monotonic'])<1e-6,'monotonic elapsed')
 _,wall,guest=next(x for x in roles(case) if x[0]==role)
 need(record['elapsed_seconds']<=wall and isinstance(record.get('guest_cycles'),int) and 0<record['guest_cycles']<=guest,'actual per-role cap')
 execution_boot(record['boot_id'])
 mapped=record.get('observed_mapped_files',{});required={d['runtime']['normal_reference']['path']}
 if role==ROLE_NAMES[0]:required.add(d['runtime']['negative_reference']['path'])
 need(required<=set(mapped) and all(mapped[q]['pid']==record['pid'] for q in required),'observed current target reference mappings')
 need(record['exit_code']==(1 if role==ROLE_NAMES[0] else 0),'expected role exit')
 return {'status':'ACTUAL_RUNTIME_RECEIPT_PASS','case_id':case,'role':role,'pid':record['pid'],'start_ticks':identity['process']['start_ticks'],'boot_id':record['boot_id'],'role_output_dir':str(p),'guest_cycles':record['guest_cycles'],'files':{name:pin(p/name) for name in ('record.json','launch.json','execution-identity.json','telemetry.jsonl','stdout.log','stderr.log')},'scope':'observed 50ms group samples, not instantaneous kernel-enforced resource limits'}

def check_cached(entry):
 need(entry['runtime']['status']=='ACTUAL_RUNTIME_RECEIPT_PASS','verified origin required')
 for x in entry['runtime']['files'].values():check_pin(x)
 need(objsha(entry['collector'])==entry['collector_digest'],'in-memory collector receipt changed')

def invoke_adapter(case,role,text,exit_code,run_id,scope):
 need(scope=='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT' and isinstance(run_id,str) and bool(run_id),'runtime bridge is TARGET-only; HOST/HISTORICAL use native adapter API')
 d=case_data(case);negative=role==ROLE_NAMES[0];mode='baseline' if role=='baseline-full' else 'candidate'
 ref=d['runtime']['negative_reference' if negative else 'normal_reference']['path']
 adapter=load_adapter(case);function=adapter.negative if negative else adapter.collect
 value=function(text,case,mode,ref,exit_code,run_id,scope)
 need(value.get('status')==d['negative_pass_status' if negative else 'normal_pass_status'],'native complete adapter status')
 for key,expected in [('case_id',case),('mode',mode),('run_id',run_id),('scope',scope)]:need(value.get(key)==expected,'adapter returned invocation identity '+key)
 return value

def field(value,path):
 for key in path.split('.'):
  need(isinstance(value,dict) and key in value,'declared native comparison field '+path);value=value[key]
 return value

def compare_calibration(case,candidate,baseline):
 check_cached(candidate);check_cached(baseline)
 x,y=candidate['collector'],baseline['collector'];d=case_data(case)
 need(candidate['runtime']['role']=='candidate-full' and baseline['runtime']['role']=='baseline-full','only two distinct complete calibration roles')
 need(candidate['runtime']['case_id']==baseline['runtime']['case_id']==x['case_id']==y['case_id']==case,'same actual case')
 need(x.get('mode')=='candidate' and y.get('mode')=='baseline' and x.get('run_id')!=y.get('run_id'),'distinct actual full-call identities')
 need(tuple(candidate['runtime'][k] for k in ('boot_id','pid','start_ticks'))!=tuple(baseline['runtime'][k] for k in ('boot_id','pid','start_ticks')),'distinct actual kernel processes')
 need(x.get('status')==y.get('status')==d['normal_pass_status'],'complete native function checks')
 fields=d['comparison_fields'];need(isinstance(fields,list) and fields and len(fields)==len(set(fields)),'declared existing comparison dimensions')
 for name in fields:
  a,b=field(x,name),field(y,name);need(a not in (None,'',[],{}) and a==b,'candidate/baseline existing functional summary '+name)
 return {'status':'CALIBRATION_FUNCTIONAL_PAIR_PASS','matched_fields':fields,'same_hardware_replay_performed':False,'formal_acceptance_qualified':False,'performance_qualified':False}

def host_deadline(start,target_active,outer_deadline):
 b=contract()['budgets'];return min(start+b['case_outer_seconds'],outer_deadline,start+target_active+b['case_host_seconds'])

def check_host_budget(start,target_active):
 host=time.monotonic()-start-target_active;need(-1e-6<=host<=contract()['budgets']['case_host_seconds'],'HOST_OVERHEAD_900_LIMIT');return host

def run_case(case,authorization_sha,outer_deadline,target_run=run_group):
 validate_authorization()
 root=case_root(case);out=root/'target-01';start=time.monotonic();total=0.;logs=0;results=[];cache={};b=contract()['budgets']
 publish_deadline(host_deadline(start,0,outer_deadline));batch_boot=execution_boot()
 status={'schema':'sp1-e-b4-calibration-case-result-v1','case_id':case,'status':'RUNNING','started_utc':now(),'started_monotonic':start,'role_results':results,'target_processes_started':0,'launch_attempts':0,'target_active_wall_seconds':0,'retry_permitted':False,'formal_acceptance_qualified':False,'performance_qualified':False}
 exclusive(root/'EXECUTION_FREEZE.json.used.json',{'case_id':case,'started_utc':now(),'boot_id':batch_boot,'freeze_sha256':sha(root/'EXECUTION_FREEZE.json'),'authorization_sha256':authorization_sha,'output':str(out),'retry_permitted':False,'calibration_only':True})
 out.mkdir(exist_ok=False);save(out/'campaign.json',status)
 try:
  with deadline_guard(host_deadline(start,total,outer_deadline)):
   frozen=verify(case);freeze_sha=sha(root/'EXECUTION_FREEZE.json')
  def precheck():
   need(execution_boot()==batch_boot,'actual calibration boot changed')
   need(sha(PACKAGE/'RUN_AUTHORIZATION.json')==authorization_sha,'authorization changed');validate_authorization()
   need(sha(root/'EXECUTION_FREEZE.json')==freeze_sha and verify(case)==frozen,'complete frozen inputs drift')
   allowed={x['path'] for x in frozen['files']}
   for module in list(sys.modules.values()):
    file=getattr(module,'__file__',None)
    if file and str(Path(file)).startswith('/home/') and file.endswith('.py'):
     need(str(Path(file)) in allowed,'loaded execution source omitted from adapter/common closure '+file)
  for index,(role,wall,guest) in enumerate(roles(case)):
   with deadline_guard(host_deadline(start,total,outer_deadline)):
    check_host_budget(start,total);precheck();command,env,cwd=execution_plan(case,role)
    need(total<b['case_target_seconds'] and logs<KNOBS['logs_cap_bytes'],'case target/log remaining limits')
    rd=out/('%02d-%s'%(index+1,role));limits={'wall_seconds':min(wall,b['case_target_seconds']-total),'guest_cycles':guest,'cpu_affinity':[4],'thread_cap':4,'rss_cap_bytes':12884901888,'log_cap_bytes':2147483648-logs}
    exclusive(out/('%02d-launch.json'%(index+1)),{'case_id':case,'role':role,'command':command,'limits':limits,'authorization_sha256':authorization_sha,'freeze_sha256':freeze_sha,'utc':now(),'calibration_only':True})
    status['launch_attempts']+=1
   publish_deadline(min(time.monotonic()+limits['wall_seconds'],start+b['case_outer_seconds'],outer_deadline),'TARGET')
   measured=target_run(command,cwd,env,rd,limits,outer_deadline=min(start+b['case_outer_seconds'],outer_deadline),role=role)
   publish_deadline(host_deadline(start,total+measured['active_wall_seconds'],outer_deadline))
   total+=measured['active_wall_seconds'];logs+=sum(measured['retained_bytes'].values())
   status['target_processes_started']+=int(measured.get('process_started') is True)
   status.update(target_active_wall_seconds=total,combined_retained_log_bytes=logs);save(out/'campaign.json',status)
   with deadline_guard(host_deadline(start,total,outer_deadline)):
    check_host_budget(start,total)
    need(measured['process_started'] and measured['resource_ok'] and measured['cleanup_ok'],'target start/resource/cleanup failure '+str(measured.get('stop_reason')))
    need(total<=b['case_target_seconds'] and logs<=KNOBS['logs_cap_bytes'],'case total cap');precheck()
    receipt=check_actual_receipt(case,role,rd)
    text=(rd/'stdout.log').read_text()+(rd/'stderr.log').read_text()
    run_id=case+':'+role+':'+str(receipt['pid'])+':'+receipt['boot_id']
    collected=invoke_adapter(case,role,text,measured['exit_code'],run_id,'TARGET_LOG_REQUIRES_RUNTIME_RECEIPT')
    entry={'collector':collected,'collector_digest':objsha(collected),'runtime':receipt};cache[role]=entry;save(rd/'validation.json',entry)
    results.append({'role':role,'status':'NEGATIVE_PASS' if index==0 else 'FULL_CALL_PASS','validation':pin(rd/'validation.json'),'guest_cycles':measured['guest_cycles'],'target_active_wall_seconds':measured['active_wall_seconds'],'peak_threads':measured['peak_threads'],'peak_rss_bytes':measured['peak_rss_bytes']})
    save(rd/'incremental.json',{'status':'CALIBRATION_ROLE_PASS','completed_roles':list(cache),'formal_acceptance_qualified':False,'performance_qualified':False})
    status['host_overhead_seconds']=check_host_budget(start,total);save(out/'campaign.json',status)
  with deadline_guard(host_deadline(start,total,outer_deadline)):
   precheck();need(len(results)==3 and list(cache)==list(ROLE_NAMES),'complete three-role calibration')
   comparison=compare_calibration(case,cache['candidate-full'],cache['baseline-full']);save(out/'comparison.json',comparison)
   status.update(status='CALIBRATION_COMPLETE',complete_call_calibration_qualified=True,comparison=pin(out/'comparison.json'),host_overhead_seconds=check_host_budget(start,total))
 except BaseException as exc:
  status.update(status='STOPPED',failure=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),complete_call_calibration_qualified=False)
 status.update(ended_utc=now(),ended_monotonic=time.monotonic(),supervision_wall_seconds=time.monotonic()-start,target_active_wall_seconds=total,combined_retained_log_bytes=logs)
 status['host_overhead_seconds']=status['supervision_wall_seconds']-total
 save(out/'campaign.json',status);return status

def execute_batch(case_runner=run_case):
 validate_authorization();require_batch_guard(PACKAGE)
 b=contract()['budgets'];start=time.monotonic();deadline=start+b['batch_outer_seconds'];out=PACKAGE/'target-01'
 batch_boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 with deadline_guard(min(deadline,start+b['case_host_seconds'])):
  auth_sha=sha(PACKAGE/'RUN_AUTHORIZATION.json')
  for case in CASE_IDS:verify(case)
 exclusive(PACKAGE/'BATCH.used.json',{'started_utc':now(),'boot_id':batch_boot,'case_ids':list(CASE_IDS),'authorization_sha256':auth_sha,'retry_permitted':False,'calibration_only':True})
 out.mkdir(exist_ok=False)
 result={'schema':'sp1-e-b4-calibration-batch-result-v1','status':'RUNNING','case_ids':list(CASE_IDS),'cases':[],'started_monotonic':start,'started_utc':now(),'target_processes_started':0,'launch_attempts':0,'target_active_wall_seconds':0,'retry_permitted':False,'formal_acceptance_qualified':False,'performance_qualified':False}
 save(out/'batch.json',result)
 try:
  for case in CASE_IDS:
   with deadline_guard(min(deadline,time.monotonic()+b['case_host_seconds'])):
    need(execution_boot()==batch_boot and sha(PACKAGE/'RUN_AUTHORIZATION.json')==auth_sha,'actual batch boot/authorization drift');validate_authorization()
    need(time.monotonic()<deadline,'BATCH_OUTER_LIMIT')
   r=case_runner(case,auth_sha,deadline);result['cases'].append({'case_id':case,'result':r})
   result['target_processes_started']+=r.get('target_processes_started',0);result['launch_attempts']+=r.get('launch_attempts',0);result['target_active_wall_seconds']+=r.get('target_active_wall_seconds',0)
   save(out/'batch.json',result);need(execution_boot()==batch_boot,'batch boot drift after case')
   need(r.get('status')=='CALIBRATION_COMPLETE','case failure stops entire calibration batch '+case)
   need(r.get('target_processes_started')==r.get('launch_attempts')==3,'complete exact three-role calibration')
   need(r.get('target_active_wall_seconds',float('inf'))<=b['case_target_seconds'] and r.get('supervision_wall_seconds',float('inf'))<=b['case_outer_seconds'] and r.get('host_overhead_seconds',float('inf'))<=b['case_host_seconds'],'case limits cannot borrow')
   need(result['launch_attempts']<=b['batch_max_processes'] and result['target_active_wall_seconds']<=b['batch_target_seconds'],'aggregate limits')
  need(time.monotonic()<=deadline,'BATCH_OUTER_LIMIT')
  result.update(status='BATCH_CALIBRATION_COMPLETE',complete_call_calibration_qualified=True)
 except BaseException as exc:
  result.update(status='STOPPED',failure=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),complete_call_calibration_qualified=False)
 result.update(ended_utc=now(),ended_monotonic=time.monotonic(),wall_seconds=time.monotonic()-start)
 save(out/'batch.json',result);return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('describe','prepare-version','inventory','freeze','verify','verify-authorization','run-batch'));parser.add_argument('case',nargs='?');args=parser.parse_args()
 if args.action=='prepare-version':
  need(args.case is None,'no case');exclusive(HERE/'SOURCE_VERSION.json',source_version());print('B4_SOURCE_VERSION_PREPARED');return
 if args.action=='describe':
  need(args.case in CASE_IDS,'fixed case');print(json.dumps(case_data(args.case)));return
 if args.action=='inventory':print(json.dumps(inventory(args.case)));return
 if args.action=='freeze':
  frozen=inventory(args.case);root=case_root(args.case);root.mkdir(parents=True,exist_ok=True);exclusive(root/'EXECUTION_FREEZE.json',frozen);print('B4_HOST_INPUTS_FROZEN_NOT_AUTHORIZED');return
 if args.action=='verify':print(json.dumps(verify(args.case)));return
 if args.action=='verify-authorization':need(args.case is None,'no case');validate_authorization();print('B4_EXPLICIT_CALIBRATION_AUTHORIZATION_VERIFIED');return
 need(args.case is None,'no run-batch case override');validate_authorization();require_batch_guard(PACKAGE)
 result=execute_batch();print(json.dumps({'status':result['status']}));raise SystemExit(0 if result['status']=='BATCH_CALIBRATION_COMPLETE' else 1)
if __name__=='__main__':main()
