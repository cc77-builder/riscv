"""Qualify the exact new W2 ELF against the unchanged independent NEMU."""
from pathlib import Path
import argparse, importlib.util, json, os, re, signal, struct, types
HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('w2_reference_build',HERE/'build.py')
c=load('w2_reference_process',HERE.parent/'consumer/run.py')
need,save,read,digest=b.need,b.save,b.read,b.digest
ORDER=[0,1,2,2,1,2,1,1,2]

def frozen(build,identity_path,adapter=None,physical=False):
    record=read(build/'result.json');need(record['status']=='W2_STATIC_GEOMETRY_AND_CAPTURE_PASS_NOT_RUNTIME' and record['contract']==b.CONTRACT,'new static identity')
    identity=c.r.parent.parent_identity(b.REPO,identity_path)
    _,checker=c.r.parent.runtime(b.REPO,identity)
    files=dict(record['external_pins'])
    def pin(p,value):
        p=str(Path(p).resolve());need(p not in files or files[p]==value,'no conflicting pin');files[p]=value
    for rel,value in record['source_pins'].items():pin(b.REPO/rel,value);pin(build/'source/repo'/rel,value)
    for key,root in (('actual_source_pins',build/'source'),('fixtures',build/'fixture'),('artifacts',build)):
        for name,value in record[key].items():pin(root/name,value)
    for p in (identity_path,build/'result.json',build/'tools.json',HERE/'reference.py'):pin(p,digest(p))
    for tool in read(build/'tools.json').values():pin(tool['path'],tool['sha256'])
    reference=Path(identity['configuration']['reference']);need(digest(reference)==identity['reference_sha256']=='8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9','original exact reference')
    pin(reference,digest(reference))
    if adapter:
        qualification=read(adapter/'build.json')
        need(qualification['status']=='REFERENCE_ADAPTER_BUILD_PASS' and qualification['inputs_sha256']==digest(adapter/'inputs.json'),'qualified original adapter')
        for name,value in read(adapter/'inputs.json')['files'].items():pin(name,value)
        for name,value in qualification['artifacts'].items():pin(adapter/name,value)
        pin(adapter/'build.json',digest(adapter/'build.json'))
        pin(adapter/'inputs.json',digest(adapter/'inputs.json'))
        need((adapter/'reference_runner.c').read_bytes()==(HERE.parent/'target/reference_runner.c').read_bytes(),'unchanged reviewed reference adapter source')
        compile_record=read(adapter/'compile.command.json')
        need(compile_record.get('exit_code')==0 and compile_record.get('status')=='exited' and compile_record.get('process_group_absent_after_exit') is True,'original adapter actual compile succeeded')
    if physical:
        actual,hardware,profile=c.r.parent.parent_identity(b.REPO,identity_path,physical=True)
        need(actual==identity,'same runtime identity')
        for name,value in hardware.items():pin(name,value)
    modules=[*list(__import__('sys').modules.values())];seen=set()
    while modules:
        m=modules.pop()
        if not isinstance(m,types.ModuleType) or id(m) in seen:continue
        seen.add(id(m));modules.extend(v for v in vars(m).values() if isinstance(v,types.ModuleType))
        name=getattr(m,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_relative_to(b.REPO) and p.is_file():pin(p,digest(p))
    checker.verify_files(files);b.executable(build/'real-w2.elf',build/'real-w2.bin')
    return record,identity,checker,files

def validate(build,dest,record,receipt,negative):
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and not receipt.get('residual_process_group')
         and not receipt.get('timed_out') and receipt['exit_code']==(2 if negative else 0),'owned reference terminal receipt')
    result=read(dest/'reference-result.json');abi=read(dest/'abi.json')
    need(abi['register_bytes']==abi['header_span']==1400 and abi['initial_pc']==0x10000000 and abi['initial_mode']==3,'original reset/ABI')
    need(result['state']==2 and result['reason']==('bad_trap' if negative else 'good_trap') and result['halt_ret']==(91 if negative else 0)
         and 0<result['retired']<=result['api_calls']<=100000000 and result['memory_dumps']==len(record['dump_plan']) and result['xiangshan_cycles_measured'] is False,'actual terminal state')
    text=(dest/'stdout.log').read_text();need(not (dest/'stderr.log').read_bytes() and not any(s in text.lower() for s in ('pma check failed','critical error','reference_adapter_reject','abort')),'no unexplained reference failure')
    sizes={n:s for n,_,s in record['dump_plan']};sizes.update({'initial-registers.bin':1400,'final-registers.bin':1400,'initial-csrs.bin':32768,'final-csrs.bin':32768})
    need({p.name for p in dest.glob('*.bin')}==set(sizes)|{'image.bin'},'exact dump inventory')
    for n,size in sizes.items():need((dest/n).stat().st_size==size,'complete dump '+n)
    expected=bytearray((build/'real-w2.bin').read_bytes());expected[record['control_offset']:record['control_offset']+8]=struct.pack('<2I',int(negative),0)
    need((dest/'image.bin').read_bytes()==expected,'only explicit negative/UART controls differ')
    for name in ('input','input-scales','weight','packed','scales','gold','slot-gold'):
        need(digest(dest/(name+'-after.bin'))==record['fixtures'][name+'.bin'],'entire immutable fixture unchanged '+name)
    report=struct.unpack('<64Q',(dest/'report.bin').read_bytes())
    need(report[:10]==(0x5232573254473031,1,int(negative),91 if negative else 0,0,1 if negative else 9,0 if negative else 9,0,0,1148 if negative else 0), 'exact actual report/progress/rejection')
    need(report[10]&0x6000 and report[10]&0x600 and report[11]==16 and not any(report[12:]),'FS/VS and complete report extent')
    guard=struct.pack('<2Q',*[0x5a1d8c2976e340bf]*2);gold=(build/'fixture/gold.bin').read_bytes();actual=(dest/'output.bin').read_bytes()
    good=guard+gold+guard
    if negative:
        need(actual!=good,'normal complete comparator rejects actual negative')
        bad=bytearray(good);bad[16+1148]^=1;need(actual==bad,'exact last output bit corruption')
    else:need(actual==good,'all 288 actual outputs and guards equal original')
    need((dest/'slots.bin').read_bytes()==guard+(build/'fixture/slot-gold.bin').read_bytes()+guard,'all 8 full128 slots and guards')
    samples=list(struct.iter_unpack('<8Q',(dest/'samples.bin').read_bytes()))
    if negative:need(not any(any(x) for x in samples),'no negative measurement admitted')
    else:
        for index,row in enumerate(samples):
            method,c0,i0,i1,c1,flags,fnv,reserved=row
            need(method==ORDER[index] and c1>c0 and i1>i0 and flags==1 and fnv==int(record['golden_fnv'],16) and reserved==0,'actual method/order/full result/flags/counters')
    return dict(status='EXPECTED_W2_REFERENCE_REJECTION' if negative else 'W2_REFERENCE_PASS',negative=negative,
                api_calls=result['api_calls'],retired=result['retired'],report=list(report),samples=[list(x) for x in samples],
                raw_sha256={n:digest(dest/n) for n in sizes},target_emu_runs=0,performance_qualified=False)

def run(build,adapter,identity_path,output):
    need(not output.exists() and len(os.sched_getaffinity(0))==1,'fresh single-core reference output')
    record,identity,checker,files=frozen(build,identity_path,adapter)
    output.mkdir(parents=True);save(output/'runtime-inputs.json',files);state=dict(contract=b.CONTRACT,status='RUNNING',started=b.old.h.now(),records=[],active_pid=None)
    persist=lambda:save(output/'state.json',state);persist();validations={}
    try:
        for label,negative in (('negative',True),('normal',False),('replay',False)):
            dest=output/label;dest.mkdir();image=bytearray((build/'real-w2.bin').read_bytes())
            image[record['control_offset']:record['control_offset']+8]=struct.pack('<2I',int(negative),0);(dest/'image.bin').write_bytes(image)
            argv=[str(adapter/'reference-runner'),identity['configuration']['reference'],str(dest/'image.bin'),str(dest),'builtin','100000000','300',str(build/'dump-plan.txt'),'1']
            rec=dict(name=label,negative=negative,command=argv,cwd=str(dest),started=b.old.h.now(),process_started=False,exit_code=None,status='RUNNING',cpu_affinity=sorted(os.sched_getaffinity(0)))
            state['records'].append(rec)
            def progress():
                state['active_pid']=rec.get('pid') if not rec.get('process_group_absent_after_exit') else None
                save(dest/'result.json',rec);persist()
            try:
                with (dest/'stdout.log').open('wb') as stdout,(dest/'stderr.log').open('wb') as stderr:
                    c.previous.spawn(argv,dest,stdout,stderr,rec,progress,dict(os.environ),330)
                checked=validate(build,dest,record,rec,negative);save(dest/'validation.json',checked);validations[label]=checked
                checker.verify_files(files);rec.update(status=checked['status'])
            except BaseException as error:rec.update(status='FAILED',error=repr(error));raise
            finally:rec['finished']=b.old.h.now();progress()
            print(label,rec['status'],flush=True)
        need(validations['normal']==validations['replay'],'independent exact reference replay')
        state['status']='W2_REFERENCE_CAMPAIGN_PASS';save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],validations=validations))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=b.old.h.now();persist()
    return state

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('W2 reference signal')))
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','adapter','identity','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))]);print(json.dumps(run(*(getattr(a,n).resolve() for n in ('build','adapter','identity','output'))),indent=2))
