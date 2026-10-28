"""Qualify the exact new NORM ELF against the unchanged independent NEMU."""
from pathlib import Path
import argparse, importlib.util, json, os, re, signal, struct, types
HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('norm_reference_build',HERE/'build.py')
c=load('norm_reference_process',HERE.parent/'consumer/run.py')
need,save,read,digest=b.need,b.save,b.read,b.digest
ORDER=[0,1,1,0,1,0,0,1]

def frozen(build,identity_path,adapter=None,physical=False):
    record=read(build/'result.json');need(record['status']=='NORM_STATIC_CAPTURE_AND_ELF_PASS_NOT_RUNTIME' and record['contract']==b.CONTRACT,'new static identity')
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
    checker.verify_files(files);b.executable(build/'real-norm.elf',build/'real-norm.bin')
    return record,identity,checker,files

def validate(build,dest,record,receipt,negative):
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and not receipt.get('residual_process_group')
         and not receipt.get('timed_out') and receipt['exit_code']==(2 if negative else 0),'owned reference terminal receipt')
    result=read(dest/'reference-result.json');abi=read(dest/'abi.json')
    need(abi['register_bytes']==abi['header_span']==1400 and abi['initial_pc']==0x10000000 and abi['initial_mode']==3,'original reset/ABI')
    elf=b.old.g.ELF((build/'real-norm.elf').read_bytes())
    pcs=[int(p,16) for p in record['failure_traps']] if negative else [elf.symbols['full_success_trap'][0]]
    need(result['state']==2 and result['reason']==('bad_trap' if negative else 'good_trap') and result['halt_ret']==(92 if negative else 0)
         and result['halt_pc'] in pcs and result['pc']==result['halt_pc']+4
         and 0<result['retired']<=result['api_calls']<=100000000 and result['memory_dumps']==len(record['dump_plan'])
         and result['xiangshan_cycles_measured'] is False,'actual terminal state and trap PC')
    need(all(result[n]==0 for n in ('mcause','mepc','mtval')),'no architectural exception')
    text=(dest/'stdout.log').read_text();need(not (dest/'stderr.log').read_bytes() and not any(s in text.lower() for s in ('pma check failed','critical error','reference_adapter_reject','abort')),'no unexplained reference failure')
    sizes={n:s for n,_,s in record['dump_plan']};sizes.update({'initial-registers.bin':1400,'final-registers.bin':1400,'initial-csrs.bin':32768,'final-csrs.bin':32768})
    need({p.name for p in dest.glob('*.bin')}==set(sizes)|{'image.bin'},'exact dump inventory')
    for n,size in sizes.items():need((dest/n).stat().st_size==size,'complete dump '+n)
    expected=bytearray((build/'real-norm.bin').read_bytes());expected[record['control_offset']:record['control_offset']+8]=struct.pack('<2I',int(negative),0)
    need((dest/'image.bin').read_bytes()==expected,'only explicit negative/UART controls differ')
    for name in ('input','weight','gold','flags'):
        need(digest(dest/(name+'-after.bin'))==record['fixtures'][name+'.bin'],'entire immutable fixture unchanged '+name)
    report=struct.unpack('<64Q',(dest/'report.bin').read_bytes())
    need(report[:10]==(0x52324e4f524d3031,1,int(negative),92 if negative else 0,0,0 if negative else 384,0 if negative else 8,0 if negative else 8,38 if negative else 0,1151 if negative else 0),'exact report/progress/rejection')
    need(report[10]&0x6000 and report[10]&0x600 and report[11]==16 and not any(report[12:]),'FS/VS and complete report extent')
    guard=struct.pack('<2Q',*[0x5a1d8c2976e340bf]*2)
    gold=(build/'fixture/gold.bin').read_bytes();inputs=(build/'fixture/input.bin').read_bytes()
    flags=struct.unpack('<48I',(build/'fixture/flags.bin').read_bytes())
    result_gold=lambda i:gold[i*1152:(i+1)*1152]
    sentinel=guard+bytes([0xa5])*1152+guard
    need((dest/'working-output.bin').read_bytes()==sentinel,'entire unused output and guards unchanged')
    working=guard+result_gold(38 if negative else 47)+guard
    if negative:
        bad=bytearray(working);bad[16+1151]^=1
        need((dest/'working-input.bin').read_bytes()==bad and bad!=working,'exact sole last output byte corruption and intact guards')
        for n in ('outputs.bin','observed-flags.bin','batch-input.bin','batch-output.bin'):
            need((dest/n).read_bytes()==bytes(sizes[n]),'negative never enters functional or batch work '+n)
    else:
        need((dest/'working-input.bin').read_bytes()==working,'final in-place functional output and guards')
        expected_outputs=b''.join(result_gold(i) for i in range(48) for j in range(8))
        need((dest/'outputs.bin').read_bytes()==expected_outputs,'all 384 whole results equal independent originals')
        expected_flags=[flags[i]|(0x18 if j%2 else 0) for i in range(48) for j in range(8)]
        need(list(struct.unpack('<384Q',(dest/'observed-flags.bin').read_bytes()))==expected_flags,'all cases/methods/aliases/sticky flags')
        x=b''.join(guard+(inputs[(26+j)*1152:(27+j)*1152] if j<12 else result_gold(38))+guard for j in range(13))
        y=b''.join(guard+result_gold(26+j)+guard if j<12 else sentinel for j in range(13))
        need((dest/'batch-input.bin').read_bytes()==x and (dest/'batch-output.bin').read_bytes()==y,'entire final 13-call input/output/guards')
    need((dest/'tls.bin').read_bytes()==bytes([0x6b])*16+struct.pack('<I',73)+bytes(60)+bytes([0xa7])*16,'actual TLS errno and bounds')
    need((dest/'control.bin').read_bytes()==struct.pack('<2I',int(negative),0),'actual reference controls')
    batch_fnv=b.old.fnv(gold[26*1152:39*1152])
    batch_flags=__import__('functools').reduce(lambda x,y:x|y,flags[26:39],0)
    need(batch_fnv==int(record['batch_fnv'],16) and batch_flags==record['batch_flags'],'independently recomputed full batch expectation')
    samples=list(struct.iter_unpack('<8Q',(dest/'samples.bin').read_bytes()))
    if negative:need(not any(any(x) for x in samples),'no negative measurement admitted')
    else:
        for index,row in enumerate(samples):
            method,c0,i0,i1,c1,observed_flags,fnv,reserved=row
            need(method==ORDER[index] and 0<c1-c0<2**32 and 0<i1-i0<2**32 and observed_flags==batch_flags and fnv==batch_fnv and reserved==0,'actual method/order/full result/flags/counters')
    return dict(status='EXPECTED_NORM_REFERENCE_REJECTION' if negative else 'NORM_REFERENCE_PASS',negative=negative,
                api_calls=result['api_calls'],retired=result['retired'],halt_pc=result['halt_pc'],report=list(report),samples=[list(x) for x in samples],
                raw_sha256={n:digest(dest/n) for n in sizes},target_emu_runs=0,performance_qualified=False)

def run(build,adapter,identity_path,output):
    need(not output.exists() and len(os.sched_getaffinity(0))==1,'fresh single-core reference output')
    record,identity,checker,files=frozen(build,identity_path,adapter)
    output.mkdir(parents=True);save(output/'runtime-inputs.json',files);state=dict(contract=b.CONTRACT,status='RUNNING',started=b.old.h.now(),records=[],active_pid=None)
    persist=lambda:save(output/'state.json',state);persist();validations={}
    try:
        for label,negative in (('negative',True),('normal',False),('replay',False)):
            dest=output/label;dest.mkdir();image=bytearray((build/'real-norm.bin').read_bytes())
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
        state['status']='NORM_REFERENCE_CAMPAIGN_PASS';save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],validations=validations))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=b.old.h.now();persist()
    return state

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('NORM reference signal')))
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','adapter','identity','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))]);print(json.dumps(run(*(getattr(a,n).resolve() for n in ('build','adapter','identity','output'))),indent=2))

