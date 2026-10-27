"""Real reference qualification of shared-object API and target harnesses."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import resource
import shutil
import signal
import struct
import types

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
a=load('consumer_aux_build',HERE/'aux_build.py')
r=load('consumer_aux_reference_support',HERE/'run.py')
need,read,save,digest=r.need,r.read,r.save,r.digest
S=r.STATE_BYTES

def inputs(build,adapter,identity_path):
    record=read(build/'result.json')
    need(record['status']=='SHARED_CONSUMER_HARNESS_STATIC_PASS_NOT_RUNTIME' and record['contract']==a.CONTRACT,'actual shared-object static gate')
    parent,files,identity,checker=r.verify_inputs(Path(record['qualified_build']),adapter,identity_path)
    need(record['qualified_consumer_object_sha256']==parent['artifacts']['consumer.o'],'same qualified consumer object')
    def pin(path,value):
        path=str(path);need(path not in files or files[path]==value,'no rebinding input');files[path]=value
    for path,value in record['external_pins'].items():pin(path,value)
    for rel,value in record['source_pins'].items():pin(r.REPO/rel,value);pin(build/'source/repo'/rel,value)
    for key,base in (('actual_source_pins',build/'source'),('fixtures',build/'fixture'),('artifacts',build)):
        for name,value in record[key].items():pin(base/name,value)
    for path in (build/'result.json',build/'tools.json',HERE/'aux_run.py'):pin(path,digest(path))
    for tool in read(build/'tools.json').values():pin(tool['path'],tool['sha256'])
    modules=[*list(__import__('sys').modules.values()),a,r];seen=set()
    while modules:
        module=modules.pop()
        if not isinstance(module,types.ModuleType) or id(module) in seen:continue
        seen.add(id(module));modules.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_relative_to(r.REPO) and path.is_file():pin(path,digest(path))
    kind=record['kind'];prefix='consumer-'+kind
    inspect=a.uart_executable if kind=='target' else a.b.f.executable
    inspect(build/(prefix+'.elf'),build/(prefix+'.bin'),build/'metadata.stdout.log',record['tls_errno_offset'])
    funcs=a.b.p.kernel_bytes(build/(prefix+'.elf'),record['kernel_identity']['functions'])
    for name,raw in funcs.items():
        wanted=record['kernel_identity']['functions'][name]
        need(len(raw)==wanted['bytes'] and a.b.f.h.sha(raw)==wanted['sha256'],'complete unchanged linked kernel')
    checker.verify_files(files);return record,files,identity,checker

def validate(build,output,record,receipt,method,negative):
    kind=record['kind'];result=read(output/'reference-result.json');abi=read(output/'abi.json')
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and
         not receipt.get('residual_process_group') and not receipt.get('timed_out') and receipt['exit_code']==(2 if negative else 0),'complete owned actual reference')
    need(result['state']==2 and result['reason']==('bad_trap' if negative else 'good_trap') and result['halt_ret']==(94 if negative else 0)
         and 0<result['retired']<=result['api_calls']<=r.MAX_CALLS and result['xiangshan_cycles_measured'] is False,'actual bounded terminal state')
    need(abi['register_bytes']==abi['header_span']==1400 and abi['initial_pc']==0x10000000 and abi['initial_mode']==3,'original actual ABI/reset')
    text=(output/'stdout.log').read_text()
    need(not (output/'stderr.log').read_bytes() and not any(s in text.lower() for s in ('pma check failed','critical error','reference_adapter_reject','abort')),'no reference fault or adapter rejection')
    sizes={n:s for n,_,s in record['dump_plan']};sizes.update({'initial-registers.bin':1400,'final-registers.bin':1400,'initial-csrs.bin':32768,'final-csrs.bin':32768})
    need({p.name for p in output.glob('*.bin')}==set(sizes)|{'image.bin'} and result['memory_dumps']==len(record['dump_plan']),'exact raw output inventory')
    for name,size in sizes.items():need((output/name).stat().st_size==size,'complete raw size '+name)
    image=bytearray((build/('consumer-'+kind+'.bin')).read_bytes())
    if kind=='target':image[record['control_offset']:record['control_offset']+12]=struct.pack('<3I',method,int(negative),0)
    need((output/'image.bin').read_bytes()==image,'actual image differs only by explicit reference UART/method/negative control')
    for name in ('weights','embedding','packed','tail-scales'):
        need(digest(output/(name+'-after.bin'))==digest(build/'fixture'/(name+'.bin')),'complete model unchanged '+name)
    report=struct.unpack('<64Q',(output/'report.bin').read_bytes());gold=[(build/'fixture'/f'host-state-p{p}.bin').read_bytes() for p in range(3)]
    need(all(len(v)==S for v in gold),'complete independent original host gold')
    need(report[10]&0x6000 and report[10]&0x600 and report[11]==16 and not any(report[12:16]),'actual FS/VS, VLEN128 and report extent')
    if kind=='api':
        need(report[:10]==(0x5232434150493031,1,0,0,10,2,3,5,6,0) and not any(report[21:]),'actual API calls/rejections and snapshots completed')
        raw=(output/'snapshots.bin').read_bytes();zero=bytes(S)
        pairs=[(gold[0],zero),(gold[0],gold[0]),(gold[1],gold[0]),(gold[1],zero),(gold[1],gold[0]),(gold[2],gold[0])]
        need(raw==b''.join(x+y for x,y in pairs),'all six pairs: exact independent state, reset and no cross-state effect')
        live=(output/'states.bin').read_bytes();guard=struct.pack('<2Q',*[0xb5e9c13f6a0742d8]*2)
        need(live==guard+gold[2]+guard+guard+gold[0]+guard,'complete final live state and all guards')
        qualified=read(Path(record['qualified_campaign'])/'results.json')['validations']
        flags=(qualified['ta-cache']['flags'][0],qualified['fr-cache']['flags'][0],qualified['ta-cache']['flags'][1],
               qualified['fr-cache']['flags'][0],qualified['ta-cache']['flags'][2])
        need(report[16:21]==flags,'all five final flags reproduce individually qualified paths')
        status='SHARED_CONSUMER_API_REFERENCE_PASS'
    else:
        need(report[:9]==(0x5232435447543031,1,method,94 if negative else 0,1,int(negative),0,1,0 if negative else S)
            and report[9]==(152476 if negative else 0) and not any(report[21:]),'actual complete comparison or exact last-logit rejection')
        raw=(output/'state.bin').read_bytes();expected=bytearray(gold[0])
        if negative:expected[152476]^=1
        need(raw==expected,'exact full actual state including negative one-bit location')
        if negative:
            try:r.compare_normal_states(build,raw,1)
            except ValueError as error:rejection=str(error)
            else:rejection=None
            need(rejection=='complete_state_mismatch position=0 byte=152476','normal complete-state comparator rejects actual negative')
        qualified=read(Path(record['qualified_campaign'])/'results.json')['validations']
        need(report[20]==qualified['fr-cache' if method==3 else 'ta-cache']['flags'][0],'same final actual flags')
        need(report[19]>report[16] and report[18]>report[17],'actual bounded counter samples; no target timing claim')
        status='EXPECTED_SHARED_TARGET_STATE_REJECTION' if negative else 'SHARED_TARGET_HARNESS_REFERENCE_PASS'
    return dict(status=status,kind=kind,method=method,negative=negative,report=list(report),
        raw_sha256={n:digest(output/n) for n in sizes},api_calls=result['api_calls'],retired=result['retired'],
        target_emu_runs=0,performance_qualified=False)

def run(build,adapter,identity_path,output):
    record,files,identity,checker=inputs(build,adapter,identity_path)
    r.r.parent.outside_inputs(output,[r.REPO,build,Path(record['qualified_build']),adapter,identity_path.parent,
        Path(identity['configuration']['hardware_source']),Path(record['am_home'])])
    need(not output.exists(),'fresh isolated auxiliary reference campaign')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=128*1024*1024
    need(hard==resource.RLIM_INFINITY or hard>=limit,'complete raw image budget');resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    output.mkdir(parents=True);save(output/'runtime-inputs.json',files);r.snapshot_runtime(output,files)
    shutil.copyfile(identity_path,output/'parent-identity.json')
    state=dict(contract=a.CONTRACT,status='RUNNING',kind=record['kind'],started=a.b.f.h.now(),active_pid=None,records=[])
    persist=lambda:save(output/'state.json',state);persist()
    cases=[('api',None,False)] if record['kind']=='api' else [('negative',4,True),('fr',3,False),('ta',4,False),('replay',4,False)]
    try:
        validations={}
        for label,method,negative in cases:
            dest=output/label;dest.mkdir();image=bytearray((build/('consumer-'+record['kind']+'.bin')).read_bytes())
            if record['kind']=='target':image[record['control_offset']:record['control_offset']+12]=struct.pack('<3I',method,int(negative),0)
            (dest/'image.bin').write_bytes(image);casefiles=dict(files);casefiles[str(dest/'image.bin')]=digest(dest/'image.bin')
            save(dest/'runtime-inputs.json',casefiles);checker.verify_files(casefiles)
            argv=[str(adapter/'reference-runner'),identity['configuration']['reference'],str(dest/'image.bin'),str(dest),'builtin',str(r.MAX_CALLS),str(r.WALL_SECONDS),str(build/'dump-plan.txt'),'1']
            rec=dict(name=label,method=method,negative=negative,command=argv,cwd=str(dest),started=a.b.f.h.now(),
                process_started=False,exit_code=None,status='RUNNING',cpu_affinity=sorted(os.sched_getaffinity(0)),
                max_api_calls=r.MAX_CALLS,wall_limit_seconds=r.WALL_SECONDS,external_timeout_seconds=r.WALL_SECONDS+30,max_output_file_bytes=limit)
            state['records'].append(rec)
            def progress():
                state['active_pid']=rec.get('pid') if not rec.get('process_group_absent_after_exit') else None
                state['active_result']=str(dest/'result.json') if state['active_pid'] else None
                save(dest/'result.json',rec);persist()
            progress()
            try:
                with (dest/'stdout.log').open('wb') as stdout,(dest/'stderr.log').open('wb') as stderr:
                    r.previous.spawn(argv,dest,stdout,stderr,rec,progress,dict(os.environ),r.WALL_SECONDS+30)
                checked=validate(build,dest,record,rec,method,negative);save(dest/'validation.json',checked)
                checker.verify_files(casefiles);rec.update(status=checked['status'],validation_sha256=digest(dest/'validation.json'));validations[label]=checked
            except BaseException as error:rec.update(status='FAILED',error=repr(error));raise
            finally:rec['finished']=a.b.f.h.now();progress()
            print(label,rec['status'],flush=True)
        if record['kind']=='target':need(validations['ta']==validations['replay'],'exact independent full target-harness raw replay')
        checker.verify_files(files);state.update(status='SHARED_CONSUMER_AUX_REFERENCE_CAMPAIGN_PASS')
        save(output/'results.json',dict(contract=a.CONTRACT,status=state['status'],kind=record['kind'],records=state['records'],validations=validations,target_emu_runs=0,performance_qualified=False))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=a.b.f.h.now();persist()
    return state

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('consumer auxiliary signal')))
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','adapter','identity','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    result=run(*(getattr(args,n).resolve() for n in ('build','adapter','identity','output')))
    print(json.dumps(dict(status=result['status'],kind=result['kind']),indent=2))
