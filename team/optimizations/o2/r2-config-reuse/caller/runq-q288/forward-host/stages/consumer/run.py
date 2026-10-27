"""Actual standalone-reference qualification of the shared pure consumer."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import resource
import shutil
import signal
import struct
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
b=load('pure_consumer_build',HERE/'build.py')
previous=load('pure_consumer_process_control',HERE.parent/'full/run.py')
r=previous.r
need,save,read,digest=b.need,b.save,b.read,b.digest
REPO=b.REPO
MAX_CALLS=2000000000
WALL_SECONDS=600
STATE_BYTES=3691424
CASES=[('negative',4,True),('scalar',0,False),('fr',1,False),('ta',2,False),
       ('fr-cache',3,False),('ta-cache',4,False),('recovery',4,False),('replay',4,False)]

def group_present(group):
    try:os.killpg(group,0)
    except ProcessLookupError:return False
    except PermissionError:return None
    return True

def case_ownership(output,label,launcher):
    """An exited launcher does not prove its independently grouped child exited."""
    path=output/label/'result.json'
    ownership=dict(case=label,result_path=str(path),launcher_pid=launcher.pid,
                   launcher_exit_code=launcher.poll(),launcher_group_present=group_present(launcher.pid))
    try:record=read(path)
    except (OSError,ValueError) as error:
        ownership.update(cleanup_verified=False,receipt_error=repr(error));return ownership,None
    group=record.get('process_group')
    ownership.update(reference_pid=record.get('pid'),reference_group=group,
                     reference_group_present=group_present(group) if isinstance(group,int) and group>0 else None,
                     receipt_cleanup_verified=record.get('process_group_absent_after_exit') is True)
    ownership['cleanup_verified']=(ownership['launcher_exit_code'] is not None and
        ownership['launcher_group_present'] is False and record.get('process_started') is True and
        ownership['reference_group_present'] is False and ownership['receipt_cleanup_verified'] and
        not record.get('residual_process_group'))
    return ownership,record

def snapshot_runtime(output,files):
    for name,value in files.items():
        path=Path(name)
        if path.is_relative_to(REPO):
            dest=output/'runtime-source'/path.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,dest);need(digest(dest)==value,'exact runtime source snapshot')

def compare_normal_states(build,raw,positions):
    """The same comparator must reject the actual application negative."""
    for pos in range(positions):
        gold=(build/'fixture'/f'host-state-p{pos}.bin').read_bytes()
        need(len(gold)==STATE_BYTES,'complete independent original-host state')
        actual=raw[pos*STATE_BYTES:(pos+1)*STATE_BYTES]
        if actual!=gold:
            at=next((i for i,(a,c) in enumerate(zip(actual,gold)) if a!=c),min(len(actual),len(gold)))
            raise ValueError(f'complete_state_mismatch position={pos} byte={at}')

def validate(build,run,method,negative,receipt):
    controls=read(run/'image-control.json');base=read(build/'result.json')
    expected=bytearray((build/'forward-consumer.bin').read_bytes());offset=base['control_offset']
    expected[offset:offset+16]=struct.pack('<4I',method,3,int(negative),1)
    need((run/'image.bin').read_bytes()==bytes(expected) and controls==dict(base_sha256=base['artifacts']['forward-consumer.bin'],
         offset=offset,controls=[method,3,int(negative),1],sha256=b.f.h.sha(expected)),'actual loaded image differs only by explicit controls')
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and
         not receipt.get('residual_process_group') and not receipt.get('timed_out') and
         receipt['exit_code']==(2 if negative else 0),'complete owned reference process')
    result=read(run/'reference-result.json');abi=read(run/'abi.json')
    need(abi['register_bytes']==abi['header_span']==1400 and abi['initial_pc']==0x10000000 and abi['initial_mode']==3,'fixed actual reference ABI/reset')
    need(result['state']==2 and result['reason']==('bad_trap' if negative else 'good_trap') and
         result['halt_ret']==(94 if negative else 0) and 0<result['retired']<=result['api_calls']<=MAX_CALLS and
         result['memory_dumps']==9 and result['xiangshan_cycles_measured'] is False,'actual exact terminal state')
    plain=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',(run/'stdout.log').read_text())
    need(not (run/'stderr.log').read_bytes() and not any(v in plain.lower() for v in ('pma check failed','critical error','reference_adapter_reject','abort')),'no unexplained reference failure')
    traps=[v for v in plain.splitlines() if 'HIT ' in v and ' TRAP' in v];need(len(traps)<=1,'at most one canonical trap')
    for line in traps:
        match=re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT (GOOD|BAD) TRAP at pc = (0x[0-9a-fA-F]+)',line)
        need(match is not None and match[1]==('BAD' if negative else 'GOOD') and int(match[2],16)==result['halt_pc'],'canonical actual trap')
    sizes={'report.bin':512,'snapshots.bin':6*STATE_BYTES,'live-state.bin':STATE_BYTES,'flags.bin':2048,'times.bin':8192,
           'weights-after.bin':17101440,'embedding-after.bin':36864000,'packed-after.bin':172*82944,
           'tail-scales-after.bin':13*288*9*4,'initial-registers.bin':1400,'final-registers.bin':1400,
           'initial-csrs.bin':32768,'final-csrs.bin':32768}
    need({v.name for v in run.glob('*.bin')}==set(sizes)|{'image.bin'},'complete raw dump and actual image set')
    for name,size in sizes.items():need((run/name).stat().st_size==size,'complete raw size '+name)
    report=struct.unpack('<64Q',(run/'report.bin').read_bytes());completed=1 if negative else 3
    need(report[:7]==(0x5232434f4e533031,1,method,94 if negative else 0,3,int(negative),1),'actual consumer identity/controls/status')
    need(report[7:10]==(completed-1,completed,completed) and report[10]&0x6000 and report[10]&0x600 and report[11]==16 and not any(report[12:]),'actual progress, FS/VS and report extent')
    flags=struct.unpack('<256Q',(run/'flags.bin').read_bytes())
    need(all(v>>5==0 for v in flags[:completed]) and not any(flags[completed:]),'actual RNE and unused flags')
    raw=(run/'snapshots.bin').read_bytes();live=(run/'live-state.bin').read_bytes()
    reject=None
    if negative:
        try:compare_normal_states(build,raw,1)
        except ValueError as error:reject=str(error)
        need(reject=='complete_state_mismatch position=0 byte=152476','normal complete-state comparator rejects actual last-logit corruption')
        gold=(build/'fixture/host-state-p0.bin').read_bytes();damaged=bytearray(gold);damaged[24480+31999*4]^=1
        need(raw[:STATE_BYTES]==bytes(damaged) and live==bytes(damaged),'exact one-bit actual live and saved state')
    else:
        compare_normal_states(build,raw,3)
        need(live==(build/'fixture/host-state-p2.bin').read_bytes(),'complete live final p2 state')
    need(raw[completed*STATE_BYTES:]==bytes((6-completed)*STATE_BYTES),'unused complete snapshot slots stay zero')
    for name,original in (('weights-after.bin','weights.bin'),('embedding-after.bin','embedding.bin'),
                          ('packed-after.bin','packed.bin'),('tail-scales-after.bin','tail-scales.bin')):
        need(digest(run/name)==digest(build/'fixture'/original),'all actual model input bytes remain unchanged')
    times=list(struct.iter_unpack('<4Q',(run/'times.bin').read_bytes()))
    need(not any(any(v) for v in times[completed:]),'unused timing slots zero')
    return dict(status='EXPECTED_ACTUAL_STATE_COMPARATOR_REJECTION' if negative else 'PURE_FORWARD_COMPLETE_REFERENCE_PASS',
                method=method,positions=completed,report=list(report),flags=list(flags[:completed]),
                normal_comparator_rejection=reject,api_calls=result['api_calls'],retired=result['retired'],
                raw_sha256={name:digest(run/name) for name in sizes if name not in ('initial-registers.bin','final-registers.bin','initial-csrs.bin','final-csrs.bin')},
                standalone_reference_counter_samples=[list(v) for v in times[:completed]],
                target_emu_runs=0,performance_qualified=False)

def verify_inputs(build,adapter,identity_path):
    identity=r.parent.parent_identity(REPO,identity_path);runtime,checker=r.parent.runtime(REPO,identity)
    record=read(build/'result.json')
    need(record['status']=='PURE_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME' and record['contract']==b.CONTRACT,'new exact static contract')
    files=dict(record['external_pins'])
    def pin(path,value):
        path=str(path);need(path not in files or files[path]==value,'conflicting input identity');files[path]=value
    for rel,value in record['source_pins'].items():pin(REPO/rel,value);pin(build/'source/repo'/rel,value)
    for key,base in (('actual_source_pins',build/'source'),('fixtures',build/'fixture'),('artifacts',build)):
        for name,value in record[key].items():pin(base/name,value)
    b.f.executable(build/'forward-consumer.elf',build/'forward-consumer.bin',build/'metadata.stdout.log',record['tls_errno_offset'])
    functions=b.p.kernel_bytes(build/'forward-consumer.elf',record['kernel_identity']['functions'])
    for name,raw in functions.items():
        expected=record['kernel_identity']['functions'][name]
        need(len(raw)==expected['bytes'] and b.f.h.sha(raw)==expected['sha256'],'complete actual original kernel function')
    reference=Path(identity['configuration']['reference'])
    need(digest(reference)==identity['reference_sha256']=='8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9','fixed original normal reference')
    for path,value in read(adapter/'inputs.json')['files'].items():pin(path,value)
    ab=read(adapter/'build.json')
    need(ab['status']=='REFERENCE_ADAPTER_BUILD_PASS' and ab['inputs_sha256']==digest(adapter/'inputs.json'),'actual adapter build bound')
    need(set(ab['artifacts'])=={'reference-runner','reference_runner.c','runner.d','compile.command.json','compile.stdout.log','compile.stderr.log','nemu.config'},'complete original adapter artifacts')
    for name,value in ab['artifacts'].items():pin(adapter/name,value)
    cr=read(adapter/'compile.command.json')
    need(cr.get('exit_code')==0 and cr.get('status')=='exited' and cr.get('process_group_absent_after_exit') is True and
         str(adapter/'reference_runner.c') in cr['argv'] and cr['argv'][-2:]==['-o',str(adapter/'reference-runner')],'actual successful original adapter compile')
    need((adapter/'reference_runner.c').read_bytes()==(HERE.parent/'target/reference_runner.c').read_bytes(),'same original reviewed adapter')
    for path in (reference,build/'result.json',build/'metadata.stdout.log',adapter/'build.json',adapter/'inputs.json',identity_path,HERE/'run.py'):pin(path,digest(path))
    modules=[*list(sys.modules.values()),b,previous,r,runtime,checker];visited=set()
    while modules:
        module=modules.pop()
        if not isinstance(module,types.ModuleType) or id(module) in visited:continue
        visited.add(id(module));modules.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(REPO) and path.is_file():pin(path,digest(path))
    checker.verify_files(files)
    return record,files,identity,checker

def one(build,adapter,identity_path,output,case):
    need(not output.exists(),'new isolated case')
    method,negative={n:(m,x) for n,m,x in CASES}[case]
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=128*1024*1024
    if hard!=resource.RLIM_INFINITY:limit=min(limit,hard)
    need(limit>=100*1024*1024,'complete image/dump file budget');resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    record,files,identity,checker=verify_inputs(build,adapter,identity_path)
    r.parent.outside_inputs(output,[REPO,build,adapter,identity_path.parent,identity['configuration']['hardware_source'],identity['configuration']['am_home']])
    output.mkdir(parents=True)
    image=bytearray((build/'forward-consumer.bin').read_bytes());offset=record['control_offset']
    image[offset:offset+16]=struct.pack('<4I',method,3,int(negative),1);(output/'image.bin').write_bytes(image)
    save(output/'image-control.json',dict(base_sha256=record['artifacts']['forward-consumer.bin'],offset=offset,controls=[method,3,int(negative),1],sha256=digest(output/'image.bin')))
    files[str(output/'image.bin')]=digest(output/'image.bin')
    files[str(output/'image-control.json')]=digest(output/'image-control.json')
    save(output/'runtime-inputs.json',files);checker.verify_files(files)
    argv=[str(adapter/'reference-runner'),identity['configuration']['reference'],str(output/'image.bin'),str(output),'builtin',str(MAX_CALLS),str(WALL_SECONDS),str(build/'dump-plan.txt'),'1']
    rec=dict(contract=b.CONTRACT,name=case,method=method,negative=negative,command=argv,cwd=str(output),started=b.f.h.now(),
             process_started=False,exit_code=None,status='RUNNING',cpu_affinity=sorted(os.sched_getaffinity(0)),
             max_api_calls=MAX_CALLS,wall_limit_seconds=WALL_SECONDS,external_timeout_seconds=WALL_SECONDS+30,max_output_file_bytes=limit)
    progress=lambda:save(output/'result.json',rec)
    progress()
    try:
        with (output/'stdout.log').open('wb') as stdout,(output/'stderr.log').open('wb') as stderr:
            previous.spawn(argv,output,stdout,stderr,rec,progress,dict(os.environ),WALL_SECONDS+30)
        checked=validate(build,output,method,negative,rec);save(output/'validation.json',checked)
        checker.verify_files(files);rec.update(status=checked['status'],validation_sha256=digest(output/'validation.json'))
        print(case,checked['status'],flush=True)
    except BaseException as error:rec.update(status='FAILED',error=repr(error));raise
    finally:rec.update(finished=b.f.h.now());progress()
    return rec

def campaign(build,adapter,identity_path,output,cpus):
    need(not output.exists() and 1<=len(cpus)<=3 and len(set(cpus))==len(cpus) and set(cpus)<=os.sched_getaffinity(0),'fresh campaign and at most three unique allowed slots')
    record,files,identity,checker=verify_inputs(build,adapter,identity_path)
    r.parent.outside_inputs(output,[REPO,build,adapter,identity_path.parent,identity['configuration']['hardware_source'],identity['configuration']['am_home']])
    output.mkdir(parents=True);save(output/'runtime-inputs.json',files);shutil.copyfile(identity_path,output/'parent-identity.json')
    snapshot_runtime(output,files)
    state=dict(contract=b.CONTRACT,status='RUNNING',started=b.f.h.now(),active=[],completed=[],cpu_slots=cpus,reference_runs=0,
               schedule='negative_then_five_methods_then_recovery_and_replay',performance_qualified=False)
    persist=lambda:save(output/'state.json',state);persist()
    active={};records=[]
    def batch(names):
        queue=list(names)
        while queue or active:
            free=[cpu for cpu in cpus if cpu not in active]
            for cpu in free:
                if not queue:break
                label=queue.pop(0)
                argv=['taskset','-c',str(cpu),sys.executable,'-B',str(HERE/'run.py'),'--build',str(build),'--adapter',str(adapter),
                      '--identity',str(identity_path),'--output',str(output/label),'--case',label]
                logfile=(output/(label+'.launcher.log')).open('wb')
                oldmask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM})
                try:
                    proc=subprocess.Popen(argv,stdout=logfile,stderr=subprocess.STDOUT,start_new_session=True,
                                          preexec_fn=lambda:signal.pthread_sigmask(signal.SIG_SETMASK,oldmask))
                    active[cpu]=(proc,label,logfile);state['active']=[dict(pid=v[0].pid,case=v[1],cpu=k) for k,v in active.items()];persist()
                finally:signal.pthread_sigmask(signal.SIG_SETMASK,oldmask)
            for cpu,(proc,label,logfile) in list(active.items()):
                if proc.poll() is None:continue
                code=proc.wait();logfile.close()
                ownership,rec=case_ownership(output,label,proc)
                state.setdefault('launcher_receipts',[]).append(ownership);persist()
                need(ownership['cleanup_verified'],'case child ownership unresolved: '+label)
                del active[cpu]
                state['active']=[dict(pid=v[0].pid,case=v[1],cpu=k) for k,v in active.items()];persist()
                need(code==0,'case process succeeded: '+label)
                records.append(rec);state['completed'].append(label)
                state['reference_runs']+=int(rec.get('process_started') is True);persist()
            if active:time.sleep(0.1)
    try:
        batch(['negative']);batch(['scalar','fr','ta','fr-cache','ta-cache']);batch(['recovery','replay'])
        validations={name:read(output/name/'validation.json') for name,_,_ in CASES}
        need(validations['ta-cache']==validations['recovery']==validations['replay'],'complete actual states, flags and retirement independently replay')
        flags=[validations[n]['flags'] for n in ('scalar','fr','ta','fr-cache','ta-cache')]
        need(all(v==flags[0] for v in flags),'all five methods have equal final fflags')
        need(len({v['pid'] for v in records})==8,'eight independent reference processes')
        checker.verify_files(files);state.update(status='PURE_FORWARD_REFERENCE_CAMPAIGN_PASS',active=[])
        save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],records=records,validations=validations,
                                      target_emu_runs=0,performance_qualified=False))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:
        unresolved=[]
        for cpu,(proc,label,logfile) in active.items():
            if proc.poll() is None:
                try:os.killpg(proc.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:proc.wait(timeout=15)
                except subprocess.TimeoutExpired:pass
            logfile.close()
            ownership,_=case_ownership(output,label,proc);ownership['cpu']=cpu
            state.setdefault('launcher_receipts',[]).append(ownership)
            if not ownership['cleanup_verified']:unresolved.append(ownership)
        state['cleanup_unknown']=unresolved
        state['active']=[dict(pid=v['launcher_pid'],case=v['case'],cpu=v['cpu'],
            result_path=v['result_path'],ownership_unresolved=True) for v in unresolved]
        state['finished']=b.f.h.now();persist()
    return state

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('consumer reference signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','adapter','identity','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--case',choices=[n for n,_,_ in CASES]);parser.add_argument('--cpus',default='0,1,2')
    args=parser.parse_args();paths=[getattr(args,n).resolve() for n in ('build','adapter','identity','output')]
    result=one(*paths,args.case) if args.case else campaign(*paths,[int(v) for v in args.cpus.split(',')])
    print(json.dumps(dict(status=result['status']),indent=2))
