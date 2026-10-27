"""Actual full-state reference qualification for the distinct W2 consumer."""
from pathlib import Path
import argparse,importlib.util,json,os,re,signal,struct,sys,types
HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('w2_full_consumer_build',HERE/'consumer_build.py')
old=load('w2_full_consumer_reference',HERE.parent/'consumer/run.py')
need,save,read,digest=b.need,b.save,b.read,b.digest
STATE_BYTES=old.STATE_BYTES;MAX_CALLS=old.MAX_CALLS
CASES=[('negative',4,'output'),('scalar',0,'normal'),('fr',1,'normal'),('ta',2,'normal'),
       ('fr-cache',3,'normal'),('ta-cache',4,'normal'),('pack-fault-fr',3,'pack'),('pack-fault-ta',4,'pack'),
       ('recovery',4,'normal'),('replay',4,'normal')]

def image(build,record,method,kind):
    raw=bytearray((build/'forward-consumer-w2.bin').read_bytes());offset=record['control_offset']
    controls=[method,3,int(kind=='output'),1];raw[offset:offset+16]=struct.pack('<4I',*controls)
    if kind=='pack':
        begin=record['w2_packed_offset'];raw[begin:begin+6*221184]=bytes(6*221184)
    return raw,dict(base_sha256=record['artifacts']['forward-consumer-w2.bin'],offset=offset,controls=controls,
        w2_pack_fault=kind=='pack',w2_packed_offset=record['w2_packed_offset'],sha256=b.old.f.h.sha(raw))

def validate(build,dest,record,method,kind,receipt):
    negative=kind=='output';fault=kind=='pack'
    expected,controls=image(build,record,method,kind)
    need((dest/'image.bin').read_bytes()==expected and read(dest/'image-control.json')==controls,'actual image differs only by declared controls/pack fault')
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and not receipt.get('residual_process_group')
        and not receipt.get('timed_out') and receipt['exit_code']==(2 if negative else 0),'complete owned reference process')
    result=read(dest/'reference-result.json');abi=read(dest/'abi.json')
    need(abi['register_bytes']==abi['header_span']==1400 and abi['initial_pc']==0x10000000 and abi['initial_mode']==3,'original reset/register ABI')
    need(result['state']==2 and result['reason']==('bad_trap' if negative else 'good_trap') and result['halt_ret']==(94 if negative else 0)
        and 0<result['retired']<=result['api_calls']<=MAX_CALLS and result['memory_dumps']==10 and result['xiangshan_cycles_measured'] is False,'exact actual terminal state and new dump inventory')
    plain=re.sub(r'\x1b\[[0-9;]*m','',(dest/'stdout.log').read_text())
    need(not (dest/'stderr.log').read_bytes() and not any(v in plain.lower() for v in ('pma check failed','critical error','reference_adapter_reject','abort')),'no unexplained reference failure')
    traps=[v for v in plain.splitlines() if 'HIT ' in v and ' TRAP' in v];need(len(traps)<=1,'at most one reference trap')
    for line in traps:
        m=re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT (GOOD|BAD) TRAP at pc = (0x[0-9a-fA-F]+)',line)
        need(m is not None and m[1]==('BAD' if negative else 'GOOD') and int(m[2],16)==result['halt_pc'],'canonical original reference trap')
    sizes={'report.bin':512,'snapshots.bin':6*STATE_BYTES,'live-state.bin':STATE_BYTES,'flags.bin':2048,'times.bin':8192,
        'weights-after.bin':17101440,'embedding-after.bin':36864000,'packed-after.bin':172*82944,'tail-scales-after.bin':13*288*9*4,
        'w2-packed-after.bin':6*221184,'initial-registers.bin':1400,'final-registers.bin':1400,'initial-csrs.bin':32768,'final-csrs.bin':32768}
    need({p.name for p in dest.glob('*.bin')}==set(sizes)|{'image.bin'},'exact complete new dump files')
    for n,size in sizes.items():need((dest/n).stat().st_size==size,'complete dump '+n)
    report=struct.unpack('<64Q',(dest/'report.bin').read_bytes());completed=1 if negative else 3
    need(report[:7]==(0x52325732434f3031,1,method,94 if negative else 0,3,int(negative),1),'new actual full consumer identity')
    need(report[7:10]==(completed-1,completed,completed) and report[10]&0x6000 and report[10]&0x600 and report[11]==16 and not any(report[12:]),'complete progress/FS/VS/report extent')
    flags=struct.unpack('<256Q',(dest/'flags.bin').read_bytes());need(all(v>>5==0 for v in flags[:completed]) and not any(flags[completed:]),'actual RNE and unused flags')
    raw=(dest/'snapshots.bin').read_bytes();live=(dest/'live-state.bin').read_bytes();reject=None
    if negative or fault:
        try:old.compare_normal_states(build,raw,completed)
        except ValueError as error:reject=str(error)
        need(reject is not None and reject.startswith('complete_state_mismatch position=0 byte='),'original whole-state comparator rejects actual negative')
        if negative:
            need(reject=='complete_state_mismatch position=0 byte=152476','specific last-logit comparator failure')
            damaged=bytearray((build/'fixture/host-state-p0.bin').read_bytes());damaged[152476]^=1
            need(raw[:STATE_BYTES]==damaged and live==damaged,'exact actual one-bit state damage')
        else:
            # With every W2 int8 value zero, its final output must actually be
            # zero. This checks the newly supplied pack is consumed at runtime.
            need(all(raw[p*STATE_BYTES+1152:p*STATE_BYTES+2304]==bytes(1152) for p in range(3)) and live[1152:2304]==bytes(1152),'all positions actually consume faulty W2 pack')
    else:
        old.compare_normal_states(build,raw,3);need(live==(build/'fixture/host-state-p2.bin').read_bytes(),'complete actual final live state')
    need(raw[completed*STATE_BYTES:]==bytes((6-completed)*STATE_BYTES),'all unused state snapshots remain zero')
    for name in ('weights','embedding','packed','tail-scales','w2-packed'):
        actual=dest/(name+'-after.bin')
        if fault and name=='w2-packed':need(actual.read_bytes()==bytes(6*221184),'exact actual deliberately zeroed new pack')
        else:need(digest(actual)==record['fixtures'][name+'.bin'],'entire immutable model input unchanged '+name)
    times=list(struct.iter_unpack('<4Q',(dest/'times.bin').read_bytes()));need(not any(any(row) for row in times[completed:]),'unused time records remain zero')
    status='EXPECTED_W2_PACK_ROUTE_REJECTION' if fault else 'EXPECTED_W2_FULL_STATE_REJECTION' if negative else 'PURE_W2_FORWARD_COMPLETE_REFERENCE_PASS'
    return dict(status=status,method=method,kind=kind,positions=completed,report=list(report),flags=list(flags[:completed]),
        normal_comparator_rejection=reject,api_calls=result['api_calls'],retired=result['retired'],
        raw_sha256={n:digest(dest/n) for n in sizes if n not in ('initial-registers.bin','final-registers.bin','initial-csrs.bin','final-csrs.bin')},
        standalone_reference_counter_samples=[list(row) for row in times[:completed]],target_emu_runs=0,performance_qualified=False)

def verify_inputs(build,adapter,identity_path):
    record=read(build/'result.json');need(record['status']=='PURE_W2_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME' and record['contract']==b.CONTRACT,'distinct new full-consumer contract')
    identity=old.r.parent.parent_identity(b.REPO,identity_path);runtime,checker=old.r.parent.runtime(b.REPO,identity)
    files=dict(record['external_pins'])
    def pin(p,value):
        p=str(Path(p).resolve());need(p not in files or files[p]==value,'consistent pinned identity');files[p]=value
    for rel,value in record['source_pins'].items():pin(b.REPO/rel,value);pin(build/'source/repo'/rel,value)
    for key,root in (('actual_source_pins',build/'source'),('fixtures',build/'fixture'),('artifacts',build)):
        for n,value in record[key].items():pin(root/n,value)
    b.old.f.executable(build/'forward-consumer-w2.elf',build/'forward-consumer-w2.bin',build/'metadata.stdout.log',record['tls_errno_offset'])
    functions=b.old.p.kernel_bytes(build/'forward-consumer-w2.elf',record['kernel_identity']['functions'])
    for n,raw in functions.items():need(len(raw)==record['kernel_identity']['functions'][n]['bytes'] and b.old.f.h.sha(raw)==record['kernel_identity']['functions'][n]['sha256'],'actual whole kernel '+n)
    reference=Path(identity['configuration']['reference']);need(digest(reference)==identity['reference_sha256']=='8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9','same original normal reference')
    for p,value in read(adapter/'inputs.json')['files'].items():pin(p,value)
    ab=read(adapter/'build.json');need(ab['status']=='REFERENCE_ADAPTER_BUILD_PASS' and ab['inputs_sha256']==digest(adapter/'inputs.json'),'qualified actual adapter')
    need(set(ab['artifacts'])=={'reference-runner','reference_runner.c','runner.d','compile.command.json','compile.stdout.log','compile.stderr.log','nemu.config'},'complete original adapter artifact inventory')
    for n,value in ab['artifacts'].items():pin(adapter/n,value)
    cr=read(adapter/'compile.command.json');need(cr.get('exit_code')==0 and cr.get('status')=='exited' and cr.get('process_group_absent_after_exit') is True
        and str(adapter/'reference_runner.c') in cr['argv'] and cr['argv'][-2:]==['-o',str(adapter/'reference-runner')],'actual original adapter compilation')
    need((adapter/'reference_runner.c').read_bytes()==(HERE.parent/'target/reference_runner.c').read_bytes(),'unchanged original adapter source')
    for p in (reference,build/'result.json',build/'metadata.stdout.log',build/'tools.json',adapter/'build.json',adapter/'inputs.json',identity_path,HERE/'consumer_run.py'):pin(p,digest(p))
    for v in read(build/'tools.json').values():pin(v['path'],v['sha256'])
    modules=[*list(sys.modules.values()),b,old,runtime,checker];seen=set()
    while modules:
        m=modules.pop()
        if not isinstance(m,types.ModuleType) or id(m) in seen:continue
        seen.add(id(m));modules.extend(v for v in vars(m).values() if isinstance(v,types.ModuleType))
        name=getattr(m,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_relative_to(b.REPO) and p.is_file():pin(p,digest(p))
    checker.verify_files(files);return record,identity,checker,files

def run(build,adapter,identity_path,output):
    need(not output.exists() and len(os.sched_getaffinity(0))==1,'new single-core full-state campaign')
    record,identity,checker,files=verify_inputs(build,adapter,identity_path)
    old.r.parent.outside_inputs(output,[b.REPO,build,adapter,identity_path.parent])
    output.mkdir(parents=True);save(output/'runtime-inputs.json',files)
    state=dict(contract=b.CONTRACT,status='RUNNING',started=b.old.f.h.now(),records=[],active_pid=None,cpu_affinity=sorted(os.sched_getaffinity(0)))
    persist=lambda:save(output/'state.json',state);persist();validations={}
    try:
        for label,method,kind in CASES:
            dest=output/label;dest.mkdir();raw,controls=image(build,record,method,kind);(dest/'image.bin').write_bytes(raw);save(dest/'image-control.json',controls);del raw
            argv=[str(adapter/'reference-runner'),identity['configuration']['reference'],str(dest/'image.bin'),str(dest),'builtin',str(MAX_CALLS),'600',str(build/'dump-plan.txt'),'1']
            rec=dict(name=label,method=method,kind=kind,command=argv,cwd=str(dest),started=b.old.f.h.now(),process_started=False,exit_code=None,status='RUNNING',cpu_affinity=sorted(os.sched_getaffinity(0)))
            state['records'].append(rec)
            def progress():
                state['active_pid']=rec.get('pid') if not rec.get('process_group_absent_after_exit') else None
                save(dest/'result.json',rec);persist()
            try:
                with (dest/'stdout.log').open('wb') as stdout,(dest/'stderr.log').open('wb') as stderr:
                    old.previous.spawn(argv,dest,stdout,stderr,rec,progress,dict(os.environ),630)
                checked=validate(build,dest,record,method,kind,rec);save(dest/'validation.json',checked);validations[label]=checked
                checker.verify_files(files);rec['status']=checked['status']
            except BaseException as error:rec.update(status='FAILED',error=repr(error));raise
            finally:rec['finished']=b.old.f.h.now();progress()
            print(label,rec['status'],flush=True)
        need(validations['ta-cache']==validations['recovery']==validations['replay'],'exact actual recovery and replay of new full consumer')
        baseline=validations['scalar']['flags'];need(all(validations[n]['flags']==baseline for n in ('fr','ta','fr-cache','ta-cache')),'all five actual methods have original scalar flags')
        state['status']='PURE_W2_FORWARD_REFERENCE_CAMPAIGN_PASS';save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],validations=validations,performance_qualified=False,target_emu_runs=0))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=b.old.f.h.now();persist()
    return state

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('W2 full reference signal')))
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','adapter','identity','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))]);r=run(*(getattr(a,n).resolve() for n in ('build','adapter','identity','output')))
    print(json.dumps({k:r[k] for k in ('status','started','finished','active_pid')},indent=2))
