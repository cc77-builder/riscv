"""Bounded independent EMUs; original DiffTest and exact raw RoPE replay."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('rope_stage_build',HERE/'build.py')
r=load('rope_runtime_support',HERE.parent/'target/run_smoke.py')
REPO=b.REPO
need,save,read,digest=b.need,b.save,b.read,b.digest
MAX_CYCLES=6000000
TIMEOUT=7200

def validate(dest,build,mode,record,cfg,gates):
    need(record.get('process_started') is True and record.get('process_group_absent_after_exit') is True and
         not record.get('residual_process_group') and not record.get('timed_out') and
         record.get('exit_code')==(1 if mode else 0),'complete expected EMU process')
    stdout=(dest/'stdout.log').read_text();stderr=(dest/'stderr.log').read_text()
    banner,gate,fatal,observer=gates
    banner.validate_runtime(stderr+stdout,cfg['reference'])
    for stream in (stdout,stderr):fatal.reject_fatal_output(stream)
    _,uart=observer.extract_events_and_uart(stderr+stdout)
    plain=gate.normalize_console(uart)
    lines=[line for line in plain.splitlines() if line.startswith('ROPE_')]
    need(lines and lines[0]==f'ROPE_BEGIN cases=6 selected=2 position=2 layers=6 pairs=24 bytes=13824 control={mode}','exact runtime case identity')
    samples=[]
    for line in lines[1:]:
        if not line.startswith('ROPE_SAMPLE '):continue
        match=re.fullmatch(r'ROPE_SAMPLE (\d+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]{16})',line)
        need(match is not None,'canonical raw target sample')
        index,method,cycles,insns,flags=map(int,match.groups()[:5]);value=match[6]
        need(index==len(samples) and index<4 and method==[0,1,1,0][index],'actual balanced ordered samples')
        need(0<cycles<MAX_CYCLES and 0<insns<(1<<32),'actual bounded cycle/retirement counters')
        need(flags==1 and value==build['cases'][2]['after_fnv'],'exact NX-only fcsr and original complete-output digest')
        samples.append(dict(index=index,method=method,cycles=cycles,instret=insns,fcsr=flags,fnv1a64=value))
    if mode:
        need(len(samples)==1 and len(lines)==3 and lines[-1]=='ROPE_REJECT 1 result 0','specific first cached output rejection')
    else:
        need(len(samples)==4 and len(lines)==6 and lines[-1]=='ROPE_PASS samples=4 full_comparisons=8 bytes=13824','complete normal application transcript')
    need(plain.count('HIT GOOD TRAP')==(0 if mode else 1) and plain.count('HIT BAD TRAP')==(1 if mode else 0),'unique expected target trap')
    for stream in (stdout,stderr,uart):
        normalized=gate.normalize_console(stream)
        if mode:
            kept=[]
            for line in normalized.splitlines():
                if 'HIT BAD TRAP' in line:
                    need(re.fullmatch(r'(?:Core 0: )?HIT BAD TRAP at pc = 0x[0-9a-f]+',line) is not None,'sole canonical expected application bad trap')
                else:kept.append(line)
            normalized='\n'.join(kept)
        gate.validate_failure_markers(normalized)
    return dict(status='EXPECTED_ROPE_APPLICATION_REJECTION' if mode else 'ROPE_STAGE_DIFFTEST_PASS',
        mode=mode,position=2,samples=samples,transcript=lines,full_forward_performance_qualified=False)

def run(identity_path,build_dir,output,cpu_count,operation):
    need(not output.exists(),'fresh campaign without overwrite/resume')
    initial=r.parent.parent_identity(REPO,identity_path);cfg=initial['configuration']
    r.parent.outside_inputs(output,[REPO,build_dir,identity_path.parent,cfg['hardware_source'],cfg['build_record'],cfg['am_home']])
    identity,hardware,profile=r.parent.parent_identity(REPO,identity_path,physical=True)
    f,m=r.parent.runtime(REPO,identity)
    build=read(build_dir/'result.json');need(build['status']=='ROPE_STAGE_STATIC_ELF_PASS_NOT_RUNTIME' and build['contract']==b.CONTRACT,'fixed complete stage image')
    for rel,value in build['source_pins'].items():need(digest(REPO/rel)==value and digest(build_dir/'source/repo'/rel)==value,'frozen build source')
    for n,value in build['actual_source_pins'].items():need(digest(build_dir/'source'/n)==value,'actual compiled source')
    for n,value in build['fixtures'].items():need(digest(build_dir/'fixture'/n)==value,'complete captured boundary input')
    for n,value in build['artifacts'].items():need(digest(build_dir/n)==value,'actual frozen compiled artifact')
    b.executable(build_dir/'rope-stage.elf',build_dir/'rope-stage.bin',build_dir/'metadata.stdout.log')
    allowed=sorted(os.sched_getaffinity(0));need(1<=cpu_count<=3 and cpu_count<=len(allowed),'at most three assigned emulator cores')
    cpus=allowed[:cpu_count];os.sched_setaffinity(0,[cpus[0]])
    need(len(list(Path('/proc/self/task').iterdir()))==1,'single-threaded parent before preexec affinity/mask setup')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=128*1024*1024
    if hard!=resource.RLIM_INFINITY:limit=min(limit,hard)
    need(limit>=16*1024*1024,'bounded sufficient log capacity');resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    gates=(load('rope_banner',REPO/'team/optimizations/o2/fullcore/run_suite.py'),
           load('rope_failure_markers',REPO/'team/optimizations/o1/audit/runtime_gate.py'),
           load('rope_fatal',REPO/'team/optimizations/o2/fullcore/recheck.py'),
           load('rope_uart',REPO/'team/optimizations/o2/fullcore/analyze.py'))
    output.mkdir(parents=True);records=[];active={}
    state=dict(contract=b.CONTRACT,status='PREFLIGHT',operation_id=operation,started=b.h.now(),new_emu_runs=0,
        active=[],cpu_affinity_slots=cpus,max_cycles=MAX_CYCLES,external_timeout_seconds=TIMEOUT,max_output_file_bytes=limit,
        schedule='negative_then_independent_normal_recovery_replay',performance_qualified=False)
    def persist():
        state['active']=[dict(name=x['record']['name'],pid=x['record'].get('pid'),result=str(x['dest']/'result.json')) for x in active.values() if not x['record'].get('process_group_absent_after_exit')]
        save(output/'state.json',state)
    persist()
    try:
        files=dict(hardware);files.update(build['external_pins']);files.update(m.checker_files(REPO))
        files.update({str(REPO/rel):value for rel,value in build['source_pins'].items()})
        files.update({str(build_dir/'source'/n):value for n,value in build['actual_source_pins'].items()})
        files.update({str(build_dir/'fixture'/n):value for n,value in build['fixtures'].items()})
        files.update({str(build_dir/n):value for n,value in build['artifacts'].items()})
        for p in (identity_path,build_dir/'result.json',build_dir/'tools.json',HERE/'run.py'):files[str(p)]=digest(p)
        for tool in read(build_dir/'tools.json').values():files[tool['path']]=tool['sha256']
        modules=[*list(sys.modules.values()),b,r,b.h,f,m,*gates];seen=set()
        while modules:
            module=modules.pop()
            if not isinstance(module,types.ModuleType) or id(module) in seen:continue
            seen.add(id(module));modules.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
            p=getattr(module,'__file__',None)
            if p:
                p=Path(p).resolve()
                if p.is_relative_to(REPO) and p.is_file():files[str(p)]=digest(p)
        save(output/'runtime-inputs.json',files);save(output/'configuration.json',cfg);save(output/'hardware-profile.json',profile)
        shutil.copyfile(identity_path,output/'parent-identity.json')
        for p,value in files.items():
            p=Path(p)
            if p.is_relative_to(REPO) and p.suffix in ('.py','.c','.h','.S','.md'):
                dest=output/'source'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);need(digest(dest)==value,'runtime source closure snapshot')
        def launch(label,mode,cpu):
            dest=output/'runs'/label;cwd=dest/'cwd';(cwd/'build').mkdir(parents=True)
            for name in m.AUX:shutil.copyfile(Path(cfg['hardware_source'])/'build'/name,cwd/'build'/name)
            inputs=dict(files);inputs.update({str(cwd/'build'/name):value for name,value in m.AUX.items()})
            m.verify_files(inputs)
            image=build_dir/('bad-output.bin' if mode else 'rope-stage.bin')
            argv=[str(Path(cfg['hardware_source'])/'build/emu'),'-i',str(image),'--flash='+cfg['flash'],
                  '--ram-size=128MB','--diff='+cfg['reference'],'--max-cycles='+str(MAX_CYCLES),'--seed=1']
            env=dict(os.environ);env.pop('XS_NEGATIVE_VECTOR_TARGET',None);env.update(OMP_NUM_THREADS='1',EMU_THREADS='1')
            rec=dict(name=label,mode=mode,command=argv,cwd=str(cwd),image_sha256=digest(image),started=b.h.now(),
                process_started=False,exit_code=None,status='STARTING',cpu=cpu,files=inputs,
                environment_overrides={'XS_NEGATIVE_VECTOR_TARGET':None,'OMP_NUM_THREADS':'1','EMU_THREADS':'1'})
            records.append(rec);save(dest/'result.json',rec)
            stdout=(dest/'stdout.log').open('wb');stderr=(dest/'stderr.log').open('wb')
            previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM})
            try:
                def child_setup():
                    os.sched_setaffinity(0,[cpu]);signal.pthread_sigmask(signal.SIG_SETMASK,previous)
                proc=subprocess.Popen(argv,cwd=cwd,stdout=stdout,stderr=stderr,env=env,start_new_session=True,preexec_fn=child_setup)
                rec.update(process_started=True,pid=proc.pid,process_group=proc.pid,status='RUNNING')
                active[label]=dict(process=proc,record=rec,dest=dest,stdout=stdout,stderr=stderr,started=time.monotonic(),inputs=inputs)
                state['new_emu_runs']+=1;save(dest/'result.json',rec);persist()
            except BaseException as error:
                rec.update(status='FAILED',error=repr(error));save(dest/'result.json',rec);raise
            finally:
                if label not in active:stdout.close();stderr.close()
                signal.pthread_sigmask(signal.SIG_SETMASK,previous)
        state['status']='NEGATIVE';launch('bad-output',1,cpus[0]);pending=[];negative_done=False
        while active or pending:
            for label,item in list(active.items()):
                proc,rec,dest=item['process'],item['record'],item['dest']
                if proc.poll() is None:
                    if time.monotonic()-item['started']>TIMEOUT:rec['timed_out']=True;raise TimeoutError(label+' exceeded bound')
                    continue
                rec.update(exit_code=proc.returncode,direct_child_reaped=True)
                r.cleanup(rec);item['stdout'].close();item['stderr'].close()
                rec['raw_sha256']={n:digest(dest/n) for n in ('stdout.log','stderr.log')};rec['finished']=b.h.now()
                save(dest/'result.json',rec)
                checked=validate(dest,build,rec['mode'],rec,cfg,gates);save(dest/'validation.json',checked)
                rec.update(status=checked['status'],validation_sha256=digest(dest/'validation.json'));m.verify_files(item['inputs'])
                save(dest/'result.json',rec);del active[label];save(output/'completed-runs.json',records);persist()
                print(label,rec['status'],flush=True)
                if label=='bad-output':
                    negative_done=True;state['status']='NORMAL_RECOVERY_REPLAY';pending=[('normal',0),('recovery',0),('replay',0)]
            busy={x['record']['cpu'] for x in active.values()}
            for cpu in cpus:
                if pending and cpu not in busy:
                    label,mode=pending.pop(0);need(negative_done,'recovery only after verified negative');launch(label,mode,cpu)
            if active:time.sleep(.25)
        normals=[read(output/'runs'/name/'validation.json') for name in ('normal','recovery','replay')]
        need(normals[0]==normals[1]==normals[2],'exact raw target counter, fcsr and output replay across independent slots')
        need(len(records)==4 and len({x['pid'] for x in records})==4,'four independent completed EMUs')
        again=r.parent.parent_identity(REPO,identity_path,physical=True);need((identity,hardware,profile)==again,'same physical hardware profile after campaign')
        m.verify_files(files)
        state.update(status='ROPE_STAGE_DIFFTEST_CAMPAIGN_PASS',performance_qualified=True)
        save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],records=records,validation=normals[0],
            scope='p2 warm six-layer aggregate with prepare included',stage_performance_qualified=True,full_forward_performance_qualified=False))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:
        previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM})
        try:
            # First stop every owned group, then reap every child. No file I/O
            # may interrupt this phase and leave a later emulator running.
            for item in active.values():
                rec=item['record'];proc=item['process']
                try:
                    if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);rec['cleanup_kill_sent']=True
                except ProcessLookupError:pass
                except BaseException as error:rec['cleanup_signal_error']=repr(error)
            for item in active.values():
                rec=item['record'];proc=item['process']
                try:
                    rec['exit_code']=proc.wait(timeout=10);rec['direct_child_reaped']=True;r.cleanup(rec)
                except BaseException as error:rec['cleanup_error']=repr(error)
            for item in active.values():
                rec=item['record'];rec.update(status='FAILED',finished=b.h.now())
                for stream in ('stdout','stderr'):
                    try:item[stream].close()
                    except BaseException as error:rec[stream+'_close_error']=repr(error)
                try:
                    rec['raw_sha256']={n:digest(item['dest']/n) for n in ('stdout.log','stderr.log')}
                    save(item['dest']/'result.json',rec)
                except BaseException as error:state.setdefault('evidence_errors',[]).append(dict(name=rec['name'],error=repr(error)))
            state['finished']=b.h.now();persist()
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
    return state

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('rope campaign signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('identity','build','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu-count',type=int,default=3);p.add_argument('--operation-id',required=True)
    a=p.parse_args();print(json.dumps(run(a.identity.resolve(),a.build.resolve(),a.output.resolve(),a.cpu_count,a.operation_id),indent=2))
