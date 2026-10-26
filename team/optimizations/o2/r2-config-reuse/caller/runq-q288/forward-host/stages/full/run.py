"""Execute full original/cache consumers on the fixed reference, then recheck RAM."""
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
import types

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
b=load('full_memory_build',HERE/'build.py')
r=load('full_memory_process_support',HERE.parent/'target/run_smoke.py')
REPO=b.REPO
need,save,read,digest=b.need,b.save,b.read,b.digest
MAX_CALLS=2000000000
WALL_SECONDS=1800
MAX_OUTPUT_BYTES=128*1024*1024

def spawn(argv,cwd,stdout,stderr,record,progress,environment,timeout):
    """Publish ownership before delivering an interrupt pending during Popen."""
    process=None
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM})
    try:
        try:
            process=subprocess.Popen(argv,cwd=cwd,stdout=stdout,stderr=stderr,
                env=environment,start_new_session=True,
                preexec_fn=lambda:signal.pthread_sigmask(signal.SIG_SETMASK,previous))
            record.update(process_started=True,pid=process.pid,process_group=process.pid)
            progress()
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK,previous)
        try:
            record['exit_code']=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            record['timed_out']=True
            raise
    finally:
        if process is not None:
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL);record['cleanup_kill_sent']=True
                except ProcessLookupError:pass
            record['exit_code']=process.wait()
            record['direct_child_reaped']=True
            r.cleanup(record)

def validate(build,run,negative,receipt):
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and
         not receipt.get('residual_process_group') and not receipt.get('timed_out') and
         receipt['exit_code']==(2 if negative else 0),'complete reference process')
    result=read(run/'reference-result.json');abi=read(run/'abi.json')
    need(abi['register_bytes']==abi['header_span']==1400 and abi['initial_pc']==0x10000000 and abi['initial_mode']==3,'fixed observed reference ABI and reset')
    need(result['state']==2 and result['reason']==('bad_trap' if negative else 'good_trap') and
         result['halt_ret']==(84 if negative else 0) and 0<result['retired']<=result['api_calls']<=MAX_CALLS and
         result['memory_dumps']==5 and result['xiangshan_cycles_measured'] is False,'actual exact reference terminal reason')
    stderr=(run/'stderr.log').read_text();stdout=(run/'stdout.log').read_text()
    plain=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',stdout)
    need(not stderr and not any(word in plain.lower() for word in ('pma check failed','critical error','reference_adapter_reject','abort')),'no unexplained reference failure output')
    trap_lines=[line for line in plain.splitlines() if 'HIT ' in line and ' TRAP' in line]
    need(len(trap_lines)<=1,'no duplicate reference trap output')
    for line in trap_lines:
        match=re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT (GOOD|BAD) TRAP at pc = (0x[0-9a-fA-F]+)',line)
        need(match is not None and match[1]==('BAD' if negative else 'GOOD') and int(match[2],16)==result['halt_pc'],'canonical optional reference trap line')
    sizes={'report.bin':256,'snapshots.bin':6*3691424,'events.bin':3*120*8,
           'weights-after.bin':17101440,'embedding-after.bin':36864000,
           'initial-registers.bin':1400,'final-registers.bin':1400,
           'initial-csrs.bin':32768,'final-csrs.bin':32768}
    need({p.name for p in run.glob('*.bin')}==set(sizes),'exact raw memory/state file set')
    for name,size in sizes.items():need((run/name).stat().st_size==size,'exact complete raw output size: '+name)
    report=struct.unpack('<32Q',(run/'report.bin').read_bytes())
    need(report[:3]==(0x523246554c4c3031,1,3),'complete report identity')
    need(report[3]==(84 if negative else 0) and report[4:9]==((0,1,13,0,0) if negative else (2,1,15,0,3)) and report[9]==0,'exact report progress or first-logit rejection')
    flags=report[10:12 if negative else 16]
    need(all(value>>5==0 for value in flags) and all(flags[i]==flags[i+1] for i in range(0,len(flags),2)),'RNE and matching actual final fflags')
    need(not any(report[12 if negative else 16:]),'no unexpected report tail')
    raw=(run/'snapshots.bin').read_bytes();need(len(raw)==6*3691424,'all six complete state slots')
    for pos in range(1 if negative else 3):
        gold=(build/'fixture'/f'host-state-p{pos}.bin').read_bytes();need(len(gold)==3691424,'complete independent host state')
        for method in range(2):
            actual=raw[(2*pos+method)*3691424:(2*pos+method+1)*3691424]
            if negative and method:
                damaged=bytearray(gold);damaged[24480]^=1;wanted=bytes(damaged)
            else:wanted=gold
            if actual!=wanted:
                offset=next(i for i,(a,c) in enumerate(zip(actual,wanted)) if a!=c)
                raise ValueError(f'actual target/host state differs: position={pos} method={method} byte={offset} actual={actual[offset]} expected={wanted[offset]}')
    if negative:need(raw[2*3691424:]==bytes(4*3691424),'negative stopped before later positions')
    events=list(struct.iter_unpack('<Ii',(run/'events.bin').read_bytes()))
    expected=[(b.h.gen.STAGES.index(name),layer) for name,layer in b.h.gen.expected_events()]
    need(events==(expected+[(0,0)]*240 if negative else expected*3),'complete actual ordered stage events')
    for name,source in (('weights-after.bin','weights.bin'),('embedding-after.bin','embedding.bin')):
        need(digest(run/name)==digest(build/'fixture'/source),'entire model remained read-only: '+source)
    return dict(status='EXPECTED_FULL_STATE_REJECTION' if negative else 'FULL_RISCV_REFERENCE_HOST_BITS_PASS',
                positions=0 if negative else 3,completed_calls=2 if negative else 6,report=list(report),
                raw_sha256={n:digest(run/n) for n in ('report.bin','snapshots.bin','events.bin','weights-after.bin','embedding-after.bin')},
                api_calls=result['api_calls'],retired=result['retired'],target_emu_runs=0,performance_qualified=False)

def run(build,adapter,identity_path,output):
    need(not output.exists(),'fresh campaign; no overwrite or resume')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE)
    limit=min(MAX_OUTPUT_BYTES,hard) if hard!=resource.RLIM_INFINITY else MAX_OUTPUT_BYTES
    need(limit>=36864000,'host file limit permits the complete embedding dump')
    resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    identity=r.parent.parent_identity(REPO,identity_path)
    r.parent.outside_inputs(output,[REPO,build,adapter,identity_path.parent,identity['configuration']['hardware_source'],identity['configuration']['am_home']])
    f,m=r.parent.runtime(REPO,identity)
    record=read(build/'result.json');need(record['status']=='FULL_MEMORY_STATIC_ELF_PASS_NOT_RUNTIME' and record['contract']==b.CONTRACT,'full static build identity')
    for rel,value in record['source_pins'].items():need(digest(REPO/rel)==value and digest(build/'source/repo'/rel)==value,'frozen complete build source')
    for name,value in record['actual_source_pins'].items():need(digest(build/'source'/name)==value,'actual compiled full source')
    for name,value in record['fixtures'].items():need(digest(build/'fixture'/name)==value,'exact fixture/golden')
    for name,value in record['artifacts'].items():need(digest(build/name)==value,'exact complete image/dump plan')
    b.executable(build/'forward-memory.elf',build/'forward-memory.bin',build/'metadata.stdout.log',record['tls_errno_offset'])
    reference=Path(identity['configuration']['reference'])
    need(digest(reference)==identity['reference_sha256']=='8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9','fixed original reference')
    adapter_inputs=read(adapter/'inputs.json')['files']
    for p,value in adapter_inputs.items():need(digest(p)==value,'original adapter header/config identity')
    adapter_build=read(adapter/'build.json')
    need(adapter_build['status']=='REFERENCE_ADAPTER_BUILD_PASS' and
         adapter_build['inputs_sha256']==digest(adapter/'inputs.json'),'completed external adapter build identity')
    for name,value in adapter_build['artifacts'].items():need(digest(adapter/name)==value,'frozen actually built adapter artifact')
    need(set(adapter_build['artifacts'])=={'reference-runner','reference_runner.c','runner.d','compile.command.json',
        'compile.stdout.log','compile.stderr.log','nemu.config'},'complete external adapter build artifacts')
    compile_record=read(adapter/'compile.command.json')
    need(compile_record.get('exit_code')==0 and compile_record.get('status')=='exited' and
         compile_record.get('process_group_absent_after_exit') is True and
         str(adapter/'reference_runner.c') in compile_record['argv'] and
         compile_record['argv'][-2:]==['-o',str(adapter/'reference-runner')],'actual successful adapter compile receipt')
    need((adapter/'reference_runner.c').read_bytes()==(HERE.parent/'target/reference_runner.c').read_bytes(),'same reviewed external caller')
    output.mkdir(parents=True)
    state=dict(contract=b.CONTRACT,status='PREFLIGHT',started=b.h.now(),reference_runs=0,active_pid=None,active_result=None,
               max_api_calls=MAX_CALLS,wall_limit_seconds=WALL_SECONDS,external_timeout_seconds=WALL_SECONDS+30,
               max_idle_calls=1,max_output_file_bytes=limit,cpu_affinity=sorted(os.sched_getaffinity(0)))
    persist=lambda:save(output/'state.json',state)
    persist()
    try:
        files=dict(adapter_inputs);files.update(record['external_pins']);files[str(reference)]=digest(reference)
        for rel,value in record['source_pins'].items():files[str(REPO/rel)]=value
        for name,value in record['actual_source_pins'].items():files[str(build/'source'/name)]=value
        for name,value in record['fixtures'].items():files[str(build/'fixture'/name)]=value
        for name,value in record['artifacts'].items():files[str(build/name)]=value
        for name,value in adapter_build['artifacts'].items():files[str(adapter/name)]=value
        for p in (build/'result.json',build/'metadata.stdout.log',adapter/'build.json',adapter/'inputs.json',identity_path,HERE/'run.py',HERE.parent/'target/reference_runner.c'):
            files[str(p)]=digest(p)
        modules=[*list(sys.modules.values()),b,r,b.h,b.g,f,m];visited=set()
        while modules:
            module=modules.pop()
            if not isinstance(module,types.ModuleType) or id(module) in visited:continue
            visited.add(id(module));modules.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
            p=getattr(module,'__file__',None)
            if p:
                p=Path(p).resolve()
                if p.is_relative_to(REPO) and p.is_file():files[str(p)]=digest(p)
        save(output/'runtime-inputs.json',files);shutil.copyfile(identity_path,output/'parent-identity.json')
        for p,value in files.items():
            p=Path(p)
            if p.is_relative_to(REPO) and p.suffix in ('.py','.c','.h','.S','.md'):
                dest=output/'source'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);need(digest(dest)==value,'runtime source snapshot')
        records=[]
        for label,negative in (('normal',False),('bad-state',True),('recovery',False),('replay',False)):
            dest=output/label;dest.mkdir();image=build/('bad-state.bin' if negative else 'forward-memory.bin')
            argv=[str(adapter/'reference-runner'),str(reference),str(image),str(dest),'builtin',str(MAX_CALLS),str(WALL_SECONDS),str(build/'dump-plan.txt'),'1']
            rec=dict(name=label,negative=negative,command=argv,cwd=str(dest),started=b.h.now(),process_started=False,exit_code=None,status='RUNNING')
            before=state['reference_runs']
            def progress():
                save(dest/'result.json',rec)
                state.update(status=label.upper(),reference_runs=before+int(rec.get('process_started') is True),
                    active_pid=rec.get('pid') if not rec.get('process_group_absent_after_exit') else None,
                    active_result=str(dest/'result.json') if not rec.get('process_group_absent_after_exit') else None)
                persist()
            progress()
            try:
                m.verify_files(files)
                try:
                    with (dest/'stdout.log').open('wb') as stdout,(dest/'stderr.log').open('wb') as stderr:
                        spawn(argv,dest,stdout,stderr,rec,progress,dict(os.environ),WALL_SECONDS+30)
                finally:r.cleanup(rec)
                checked=validate(build,dest,negative,rec);save(dest/'validation.json',checked)
                rec.update(status=checked['status'],validation_sha256=digest(dest/'validation.json'))
                m.verify_files(files)
            except BaseException as error:rec.update(status='FAILED',error=repr(error));raise
            finally:
                rec.update(finished=b.h.now(),raw_sha256={p.name:digest(p) for p in dest.iterdir() if p.is_file() and p.name not in ('result.json','validation.json')});progress()
            records.append(rec);save(output/'completed-runs.json',records);print(label,rec['status'],flush=True)
        normals=[read(output/name/'validation.json') for name in ('normal','recovery','replay')]
        need(normals[0]==normals[1]==normals[2],'full raw memory, flags, retirement and event replay')
        need(len({rec['pid'] for rec in records})==4,'independent normal/negative/recovery/replay processes')
        m.verify_files(files);state.update(status='FULL_RISCV_REFERENCE_CAMPAIGN_PASS',active_pid=None,active_result=None)
        save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],records=records,validation=normals[0],target_emu_runs=0,performance_qualified=False))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=b.h.now();persist()
    return state

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('full reference signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build','adapter','identity','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    print(json.dumps(run(args.build.resolve(),args.adapter.resolve(),args.identity.resolve(),args.output.resolve()),indent=2))
