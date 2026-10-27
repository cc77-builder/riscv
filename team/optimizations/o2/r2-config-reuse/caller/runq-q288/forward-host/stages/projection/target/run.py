"""Bounded real projection boundaries, complete custom protocol and raw replay."""
from pathlib import Path
import argparse
import gc
import struct
from functools import cmp_to_key
from itertools import groupby
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
b=load('projection_boundary_build',HERE/'build.py')
r=load('projection_boundary_support',HERE.parents[1]/'target/run_smoke.py')
REPO=b.REPO
need,save,read,digest=b.need,b.save,b.read,b.digest
MAX_CYCLES=8000000
TIMEOUT=7200

def counter_audit(text,elf,sites,windows,samples,observer):
    """Bind every final-ELF counter read to enqueue/sample/retire observations.

    This does not reconstruct all retired instructions between the reads.
    The existing observer's full field parser handles widths and ROB syntax.
    """
    records={name:[] for name in observer.T13_FIELDS}
    for match in re.finditer(r'T13_(COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+([^\n]*)\n',text):
        kind,body=match.groups()
        records[kind].append(observer.parse_fields('T13_'+kind,body,observer.T13_FIELDS[kind].split(),t13=True))
    reads=windows*4
    need(all(len(v)==reads for v in records.values()),'one complete enqueue/sample/retire chain per measured CSR')
    need(len(sites)==4 and [int(x['csr'],16) for x in sites]==[0xc00,0xc02,0xc02,0xc00],'actual timer order')
    pairs=[];previous=-1
    for i,(enq,csr,ret) in enumerate(zip(records['COUNTER_ENQUEUE'],records['CSR_SAMPLE'],records['RETIRE'])):
        site=sites[i%4];pc=int(site['pc'],16);addr=int(site['csr'],16);word=struct.unpack('<I',elf.read(pc,4))[0]
        need(enq['pc']==ret['pc']==pc and enq['word']==ret['word']==word,'counter PC and word equal final ELF')
        need(word>>20==csr['addr']==addr and csr['wen']==0,'read-only actual CSR identity')
        need(enq['rob']==ret['rob'] and ret['count']==1 and ret['slot']==0 and ret['data']==csr['data'],'counter value reaches its unique architectural retirement')
        need(enq['empty']==1 and previous<enq['cycle']<csr['cycle']<ret['cycle'],'empty ROB at each fenced counter enqueue; ordered read chain')
        previous=ret['cycle'];pairs.append(dict(enqueue=enq,sample=csr,retire=ret))
    deltas=[]
    for i in range(windows):
        group=records['CSR_SAMPLE'][4*i:4*i+4]
        cycle_delta=(group[3]['data']-group[0]['data'])&((1<<64)-1)
        instret_delta=(group[2]['data']-group[1]['data'])&((1<<64)-1)
        need(0<cycle_delta<MAX_CYCLES and 0<instret_delta<(1<<32),'bounded actual counter delta')
        need(cycle_delta==group[3]['cycle']-group[0]['cycle'],'cycle delta equals independent global observer interval')
        if i<len(samples):need((cycle_delta,instret_delta)==(samples[i]['cycles'],samples[i]['instret']),'UART cycle and instret exactly equal actual sampled CSR data')
        deltas.append(dict(cycles=cycle_delta,instret=instret_delta))
    return dict(status='FENCED_COUNTER_SAMPLE_RETIRE_PASS',windows=windows,reads=reads,deltas=deltas,
        records=pairs,full_retirement_window_audited=False)

def validate(dest,build,build_dir,mode,record,cfg,gates):
    need(record.get('process_started') is True and record.get('process_group_absent_after_exit') is True and
         not record.get('residual_process_group') and not record.get('timed_out') and
         record.get('exit_code')==(1 if mode else 0),'complete expected EMU process')
    stdout=(dest/'stdout.log').read_text();stderr=(dest/'stderr.log').read_text()
    banner,gate,fatal,observer=gates
    text=stderr+stdout
    banner.validate_runtime(text,cfg['reference'])
    for stream in (stdout,stderr):fatal.reject_fatal_output(stream)
    events,uart=observer.extract_events_and_uart(text)
    fatal.reject_fatal_output(uart)
    commits=[f for _,_,kind,f in events if kind=='COMMIT']
    # The fixed observer permits multiple same-cycle retirements. Its protocol
    # checker orders these by ROB age, independent of printf ordering.
    def age(left,right):
        if left['rob']==right['rob']:return 0
        after=observer.flushed(left['rob'],right['rob'],0)
        before=observer.flushed(right['rob'],left['rob'],0)
        need(after!=before,'unambiguous same-cycle ROB age')
        return 1 if after else -1
    actual=[]
    for unused,group in groupby(commits,key=lambda x:x['cycle']):
        actual.extend(f['pc'] for f in sorted(group,key=cmp_to_key(age)))
    raw_path=(build_dir/'ta-custom-pcs.bin').read_bytes()
    need(len(raw_path)==10368*8,'whole final-ELF TA path')
    path=list(struct.unpack('<10368Q',raw_path));calls=4 if mode else 20
    need(actual==path*calls,'complete warm and measured custom retirement PC sequence')
    (dest/'custom-commit-pcs.bin').write_bytes(struct.pack('<'+str(len(actual))+'Q',*actual))
    pc_digest=digest(dest/'custom-commit-pcs.bin')
    del events,commits,actual,path
    gc.collect()
    plain=gate.normalize_console(uart)
    lines=[line for line in plain.splitlines() if line.startswith('TILE_')]
    need(lines and lines[0]==f'TILE_BEGIN position=2 cases=2 rows=320,768 q_calls=40 control={mode}','exact real runtime case identity')
    samples=[]
    for line in lines[1:]:
        if not line.startswith('TILE_SAMPLE '):continue
        match=re.fullmatch(r'TILE_SAMPLE (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]{16})',line)
        need(match is not None,'canonical raw target sample')
        case,index,arm,rows,cycles,insns,flags=map(int,match.groups()[:7]);value=match[8]
        need(case==len(samples)//4 and index==len(samples)%4 and case<2 and arm==[0,1,1,0][index],'actual balanced ordered samples')
        need(rows==build['cases'][case]['rows'] and flags==1 and value==build['cases'][case]['golden_fnv'],'actual row count, NX-only fcsr and original output digest')
        need(0<cycles<MAX_CYCLES and 0<insns<(1<<32),'actual bounded cycle and retirement counters')
        samples.append(dict(case=case,index=index,method=arm,rows=rows,cycles=cycles,instret=insns,fcsr=flags,fnv1a64=value))
    if mode:
        need(len(samples)==1 and len(lines)==3 and lines[-1]=='TILE_REJECT 0 1 result 1276','specific last classifier output rejection')
    else:
        need(len(samples)==8 and len(lines)==10 and lines[-1]=='TILE_PASS samples=8 full_comparisons=16 q_calls=40','complete normal application transcript')
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
    timing=counter_audit(text,b.g.ELF((build_dir/'projection-boundaries.elf').read_bytes()),build['counter_sites'],2 if mode else 8,samples,observer)
    save(dest/'counter-audit.json',timing)
    del stdout,stderr,uart,plain,normalized
    gc.collect()
    analysis=observer.analyze(text,require_complete=True)
    need(analysis['status']=='O2_TRACE_PASS' and analysis['schema']['slots']==2,'complete fixed two-slot O2 protocol')
    need(all(analysis[k]==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')),'all protocol and ROB work completed')
    need(analysis['counts']['COMMIT']==calls*10368,'exact complete custom count')
    save(dest/'protocol.json',analysis)
    protocol={k:analysis[k] for k in ('status','schema','counts','pending_count','pending_div_count','unfinished_rob_count')}
    del analysis,text
    gc.collect()
    return dict(status='EXPECTED_PROJECTION_APPLICATION_REJECTION' if mode else 'PROJECTION_BOUNDARY_DIFFTEST_PASS',
        mode=mode,position=2,samples=samples,transcript=lines,protocol=protocol,custom_commit_pc_sha256=pc_digest,
        counter_audit=timing,
        ta_calls=calls,total_q_calls=8 if mode else 40,full_forward_performance_qualified=False,
        full_retirement_window_audited=False,counter_scope='fixed T17 final ELF with IORW fences around cycle/instret; whole apply selfwarm ABBA')

def run(identity_path,build_dir,output,cpu_count,operation):
    need(not output.exists(),'fresh campaign without overwrite/resume')
    initial=r.parent.parent_identity(REPO,identity_path);cfg=initial['configuration']
    r.parent.outside_inputs(output,[REPO,build_dir,identity_path.parent,cfg['hardware_source'],cfg['build_record'],cfg['am_home']])
    identity,hardware,profile=r.parent.parent_identity(REPO,identity_path,physical=True)
    f,m=r.parent.runtime(REPO,identity)
    build=read(build_dir/'result.json');need(build['status']=='PROJECTION_BOUNDARY_STATIC_ELF_AND_MODELS_PASS_NOT_RUNTIME' and build['contract']==b.CONTRACT,'fixed complete stage image')
    for rel,value in build['source_pins'].items():need(digest(REPO/rel)==value and digest(build_dir/'source/repo'/rel)==value,'frozen build source')
    for n,value in build['actual_source_pins'].items():need(digest(build_dir/'source'/n)==value,'actual compiled source')
    for n,value in build['fixtures'].items():need(digest(build_dir/'fixture'/n)==value,'complete captured boundary input')
    for n,value in build['artifacts'].items():need(digest(build_dir/n)==value,'actual frozen compiled artifact')
    b.executable(build_dir/'projection-boundaries.elf',build_dir/'projection-boundaries.bin')
    allowed=sorted(os.sched_getaffinity(0));need(1<=cpu_count<=3 and cpu_count<=len(allowed),'at most three assigned emulator cores')
    cpus=allowed[:cpu_count];os.sched_setaffinity(0,[cpus[0]])
    need(len(list(Path('/proc/self/task').iterdir()))==1,'single-threaded parent before preexec affinity/mask setup')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=1024*1024*1024
    need(hard==resource.RLIM_INFINITY or hard>=limit,'inherited hard limit accommodates each complete custom log')
    resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    gates=(load('boundary_banner',REPO/'team/optimizations/o2/fullcore/run_suite.py'),
           load('boundary_failure_markers',REPO/'team/optimizations/o1/audit/runtime_gate.py'),
           load('boundary_fatal',REPO/'team/optimizations/o2/fullcore/recheck.py'),
           load('boundary_uart',REPO/'team/optimizations/o2/fullcore/analyze.py'))
    output.mkdir(parents=True);records=[];active={}
    state=dict(contract=b.CONTRACT,status='PREFLIGHT',operation_id=operation,started=b.h.now(),new_emu_runs=0,
        active=[],cpu_affinity_slots=cpus,max_cycles=MAX_CYCLES,external_timeout_seconds=TIMEOUT,max_output_file_bytes=limit,
        schedule='negative_then_independent_normal_recovery_replay',performance_qualified=False)
    def persist():
        state['active']=[dict(name=x['record']['name'],pid=x['record'].get('pid'),result=str(x['dest']/'result.json')) for x in active.values() if not x['record'].get('process_group_absent_after_exit')]
        save(output/'state.json',state)
    persist()
    try:
        files={}
        def pin(path,value):
            path=str(Path(path).resolve())
            need(path not in files or files[path]==value,'conflicting frozen input identity: '+path)
            need(digest(path)==value,'current runtime input matches frozen identity: '+path)
            files[path]=value
        for mapping in (hardware,build['external_pins'],m.checker_files(REPO)):
            for path,value in mapping.items():pin(path,value)
        for rel,value in build['source_pins'].items():pin(REPO/rel,value)
        for n,value in build['actual_source_pins'].items():pin(build_dir/'source'/n,value)
        for n,value in build['fixtures'].items():pin(build_dir/'fixture'/n,value)
        for n,value in build['artifacts'].items():pin(build_dir/n,value)
        for p in (identity_path,build_dir/'result.json',build_dir/'tools.json',HERE/'run.py'):pin(p,digest(p))
        for tool in read(build_dir/'tools.json').values():pin(tool['path'],tool['sha256'])
        modules=[*list(sys.modules.values()),b,r,b.h,f,m,*gates];seen=set()
        while modules:
            module=modules.pop()
            if not isinstance(module,types.ModuleType) or id(module) in seen:continue
            seen.add(id(module));modules.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
            p=getattr(module,'__file__',None)
            if p:
                p=Path(p).resolve()
                if p.is_relative_to(REPO) and p.is_file():pin(p,digest(p))
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
            image=build_dir/('bad-tail.bin' if mode else 'projection-boundaries.bin')
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
        def finalize(item):
            rec,dest=item['record'],item['dest']
            rec['raw_sha256']={n:digest(dest/n) for n in ('stdout.log','stderr.log')}
            save(dest/'result.json',rec)
            checked=validate(dest,build,build_dir,rec['mode'],rec,cfg,gates);save(dest/'validation.json',checked)
            rec.update(status=checked['status'],validation_sha256=digest(dest/'validation.json'));m.verify_files(item['inputs'])
            save(dest/'result.json',rec);save(output/'completed-runs.json',records)
            print(rec['name'],rec['status'],flush=True)
        state['status']='NEGATIVE';launch('bad-tail',1,cpus[0]);pending=[];negative_done=False;completed=[]
        while active or pending:
            for label,item in list(active.items()):
                proc,rec,dest=item['process'],item['record'],item['dest']
                if proc.poll() is None:
                    if time.monotonic()-item['started']>TIMEOUT:rec['timed_out']=True;raise TimeoutError(label+' exceeded bound')
                    continue
                rec.update(exit_code=proc.returncode,direct_child_reaped=True,
                    observed_elapsed_seconds=time.monotonic()-item['started'])
                if rec['observed_elapsed_seconds']>TIMEOUT:
                    rec['timed_out']=True;raise TimeoutError(label+' exit not observed within bound')
                r.cleanup(rec);item['stdout'].close();item['stderr'].close()
                rec.update(finished=b.h.now(),status='EXITED_AWAITING_VALIDATION')
                save(dest/'result.json',rec);del active[label];persist()
                if label=='bad-tail':
                    # No other emulator is running during negative parsing.
                    finalize(item)
                    negative_done=True;state['status']='NORMAL_RECOVERY_REPLAY';pending=[('normal',0),('recovery',0),('replay',0)]
                else:completed.append(item)
            busy={x['record']['cpu'] for x in active.values()}
            for cpu in cpus:
                if pending and cpu not in busy:
                    label,mode=pending.pop(0);need(negative_done,'recovery only after verified negative');launch(label,mode,cpu)
            if active:time.sleep(.25)
        need(len(completed)==3 and not active,'all normal processes reaped before expensive parsing')
        state['status']='SEQUENTIAL_RAW_AUDIT';persist()
        for item in completed:finalize(item)
        normals=[read(output/'runs'/name/'validation.json') for name in ('normal','recovery','replay')]
        need(normals[0]==normals[1]==normals[2],'exact raw target counter, fcsr and output replay across independent slots')
        need(len(records)==4 and len({x['pid'] for x in records})==4,'four independent completed EMUs')
        again=r.parent.parent_identity(REPO,identity_path,physical=True);need((identity,hardware,profile)==again,'same physical hardware profile after campaign')
        m.verify_files(files)
        state.update(status='PROJECTION_BOUNDARY_DIFFTEST_CAMPAIGN_PASS',performance_qualified=True)
        save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],records=records,validation=normals[0],
            scope='p2 complete layer5 W1 M768 and classifier rows31680..31999; prequantized; prepacked; whole-boundary selfwarm',stage_performance_qualified=True,full_forward_performance_qualified=False))
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
    def interrupted(signum,frame):raise InterruptedError('projection boundary campaign signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('identity','build','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu-count',type=int,default=3);p.add_argument('--operation-id',required=True)
    a=p.parse_args();print(json.dumps(run(a.identity.resolve(),a.build.resolve(),a.output.resolve(),a.cpu_count,a.operation_id),indent=2))
