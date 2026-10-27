"""New real-W2 campaign; reuses the frozen scheduler and original trace gates.

Whole-process budget is 12M cycles. The inherited counter checker retains its
stricter 8M-per-window bound. No observer, official runtime, or frozen parent
checker is changed. Large traces are audited with bounded live state.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, resource, shutil, signal
import struct, subprocess, sys, time, types
HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
ref=load('w2_runtime_reference',HERE/'reference.py');b=ref.b;r=ref.c.r
projection=load('w2_counter_auditor',HERE.parent/'projection/target/run.py')
stream=load('w2_stream_auditor',HERE.parent/'consumer/stream_audit.py')
REPO=b.REPO
need,save,read,digest=b.need,b.save,b.read,b.digest
MAX_CYCLES=12000000
TIMEOUT=10800

def raw_gates(paths,mode,gate,fatal):
    # The complete extracted UART below also applies these unchanged gates to
    # text split by observer rows. Per-line raw checks preserve all raw errors.
    for path in paths:
        with path.open('r',encoding='utf-8') as src:
            tail=''
            for line in src:
                need(len(line)<=stream.MAX_LINE,'bounded raw physical line')
                plain=gate.normalize_console(line);fatal.reject_fatal_output(tail+plain)
                tail=(tail+plain)[-4096:]
                if mode and 'HIT BAD TRAP' in plain:
                    need(re.fullmatch(r'(?:Core 0: )?HIT BAD TRAP at pc = 0x[0-9a-f]+\n?',plain) is not None,'canonical sole expected bad trap')
                else:gate.validate_failure_markers(plain)

def validate(dest,build,build_dir,mode,record,cfg,gates):
    need(record.get('process_started') is True and record.get('process_group_absent_after_exit') is True and
         not record.get('residual_process_group') and not record.get('timed_out') and
         record.get('exit_code')==(1 if mode else 0),'complete expected EMU process')
    logs=[dest/'stderr.log',dest/'stdout.log'];banner,gate,fatal,observer=gates
    image_name='negative.bin' if mode else 'real-w2.bin'
    need(record['image_sha256']==build['artifacts'][image_name] and
         record['command'][2]==str(build_dir/image_name),'actual image and invocation identity')
    need(record['raw_sha256']=={p.name:digest(p) for p in logs},'actual raw stream hashes')
    raw_gates(logs,mode,gate,fatal)
    raw=(build_dir/'ta-custom-pcs.bin').read_bytes();need(len(raw)==27648*8,'complete actual-ELF K768 PC plan')
    path=struct.unpack('<27648Q',raw);calls=2 if mode else 8;count=0;pc_hash=hashlib.sha256()
    def commit(f):
        nonlocal count
        need(count<calls*len(path) and f['pc']==path[count%len(path)],'exact ordered complete W2 custom path')
        pc_hash.update(struct.pack('<Q',f['pc']));count+=1
    protocol,uart,counters=stream.audit_files(logs,require_complete=True,commit_sink=commit)
    need(count==calls*27648 and protocol['counts']['COMMIT']==count,'all warm/measured custom calls completed')
    need(protocol['status']=='O2_TRACE_PASS' and protocol['schema']['slots']==2 and
         all(protocol[k]==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')),'complete original protocol/full128 arithmetic')
    banner.validate_runtime(uart,cfg['reference']);fatal.reject_fatal_output(uart);plain=gate.normalize_console(uart)
    lines=[line for line in plain.splitlines() if line.startswith('W2_')]
    need(lines and lines[0]==f'W2_BEGIN position=2 layer=5 rows=288 k=768 control={mode}','exact actual W2 identity')
    samples=[]
    for line in lines[1:]:
        if not line.startswith('W2_SAMPLE '):continue
        match=re.fullmatch(r'W2_SAMPLE (\d+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]{16})',line)
        need(match is not None,'canonical actual sample');index,method,cycles,insns,flags=map(int,match.groups()[:5]);value=match[6]
        need(index==len(samples) and index<9 and method==ref.ORDER[index] and flags==1 and value==build['golden_fnv'],'actual order, original complete-output hash and NX-only flags')
        need(0<cycles<MAX_CYCLES and 0<insns<(1<<32),'actual bounded counters')
        samples.append(dict(index=index,method=method,cycles=cycles,instret=insns,fcsr=flags,fnv1a64=value))
    if mode:need(not samples and lines==[lines[0],'W2_REJECT sample=0 method=2 name=result byte=1148'],'specific actual last-output negative rejection')
    else:need(len(samples)==9 and len(lines)==11 and lines[-1]=='W2_PASS samples=9 full_comparisons=18','complete actual W2 normal transcript')
    need(plain.count('HIT GOOD TRAP')==(0 if mode else 1) and plain.count('HIT BAD TRAP')==(1 if mode else 0),'unique expected canonical trap')
    traps=[line for line in plain.splitlines() if 'HIT ' in line and ' TRAP' in line]
    expected_trap='BAD' if mode else 'GOOD'
    need(len(traps)==1 and re.fullmatch(r'(?:Core 0: )?HIT '+expected_trap+r' TRAP at pc = 0x[0-9a-f]+',traps[0]) is not None,'sole canonical terminal trap line')
    kept=[]
    for line in plain.splitlines():
        if mode and 'HIT BAD TRAP' in line:
            need(re.fullmatch(r'(?:Core 0: )?HIT BAD TRAP at pc = 0x[0-9a-f]+',line) is not None,'canonical expected trap')
        else:kept.append(line)
    gate.validate_failure_markers('\n'.join(kept))
    timing=projection.counter_audit(counters,b.old.g.ELF((build_dir/'real-w2.elf').read_bytes()),build['counter_sites'],1 if mode else 9,samples,observer)
    save(dest/'counter-audit.json',timing);save(dest/'protocol.json',protocol)
    (dest/'uart.txt').write_text(uart);(dest/'counter-source.txt').write_text(counters)
    # Raw runtime banners include host-time text; only architectural/protocol
    # evidence enters exact replay. Three processes do not increase formal n.
    return dict(status='EXPECTED_W2_APPLICATION_REJECTION' if mode else 'W2_BOUNDARY_DIFFTEST_PASS',
        mode=mode,samples=samples,transcript=lines,protocol={k:v for k,v in protocol.items() if k!='input_sha256'},custom_commit_pc_sha256=pc_hash.hexdigest(),
        custom_count=count,ta_calls=calls,counter_audit=timing,full_forward_performance_qualified=False,
        full_retirement_window_audited=False)

def performance(validation):
    samples=validation['samples'];fr=[x['cycles'] for x in samples if x['method']==1];ta=[x['cycles'] for x in samples if x['method']==2]
    need(len(fr)==len(ta)==4 and samples[0]['method']==0,'one complete registered W2 plan')
    span=max(fr)/min(fr)-1;margin=1-max(ta)/min(fr)
    directions=[sum(samples[i]['cycles'] for i in group if samples[i]['method']==2)<sum(samples[i]['cycles'] for i in group if samples[i]['method']==1) for group in (range(1,5),range(5,9))]
    eligible=span<=.01
    selected='TA' if eligible and margin>=.005 and all(directions) else 'FR' if eligible and min(ta)>=max(fr) else 'HOLD'
    return dict(status='W2_LOCAL_PERFORMANCE_EVALUATED',selected=selected,formal_samples_per_vector_method=4,
        comparison_qualified=eligible,fr_span_limit_fraction=.01,ta_required_reduction_fraction=.005,
        scalar_cycles=samples[0]['cycles'],fr_cycles=fr,ta_cycles=ta,fr_span_fraction=span,
        conservative_ta_reduction_fraction=margin,both_order_groups_favor_ta=all(directions),
        scalar_to_fr_worst_speedup=samples[0]['cycles']/max(fr),scalar_to_ta_worst_speedup=samples[0]['cycles']/max(ta),
        same_elf_prepacked_selfwarm_only=True,full_forward_performance_qualified=False)

def run(identity_path,build_dir,reference_dir,output,cpu_count,operation):
    need(not output.exists(),'fresh campaign without overwrite/resume')
    initial=r.parent.parent_identity(REPO,identity_path);cfg=initial['configuration']
    r.parent.outside_inputs(output,[REPO,build_dir,reference_dir,identity_path.parent,cfg['hardware_source'],cfg['build_record'],cfg['am_home']])
    identity,hardware,profile=r.parent.parent_identity(REPO,identity_path,physical=True)
    f,m=r.parent.runtime(REPO,identity)
    build,identity2,checker,reference_files=ref.frozen(build_dir,identity_path)
    need(identity==identity2,'same qualified runtime identity')
    qualification=read(reference_dir/'results.json')
    reference_pins=read(reference_dir/'runtime-inputs.json');m.verify_files(reference_pins)
    for name,value in reference_pins.items():
        need(name not in reference_files or reference_files[name]==value,'same original reference execution pins')
        reference_files[name]=value
    need(qualification['status']=='W2_REFERENCE_CAMPAIGN_PASS' and qualification['contract']==b.CONTRACT,'actual prior reference campaign')
    for label,negative in (('negative',True),('normal',False),('replay',False)):
        actual=ref.validate(build_dir,reference_dir/label,build,read(reference_dir/label/'result.json'),negative)
        need(actual==qualification['validations'][label],'reference evidence re-audited before EMU')
    need(qualification['validations']['normal']==qualification['validations']['replay'],'complete reference recovery/replay')
    for p in reference_dir.rglob('*'):
        if p.is_file():reference_files[str(p)]=digest(p)
    allowed=sorted(os.sched_getaffinity(0));need(1<=cpu_count<=3 and cpu_count<=len(allowed),'at most three assigned emulator cores')
    cpus=allowed[:cpu_count];os.sched_setaffinity(0,[cpus[0]])
    need(len(list(Path('/proc/self/task').iterdir()))==1,'single-threaded parent before preexec affinity/mask setup')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=2*1024*1024*1024
    need(hard==resource.RLIM_INFINITY or hard>=limit,'inherited hard limit accommodates each complete custom log')
    resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    gates=(load('boundary_banner',REPO/'team/optimizations/o2/fullcore/run_suite.py'),
           load('boundary_failure_markers',REPO/'team/optimizations/o1/audit/runtime_gate.py'),
           load('boundary_fatal',REPO/'team/optimizations/o2/fullcore/recheck.py'),
           load('boundary_uart',REPO/'team/optimizations/o2/fullcore/analyze.py'))
    output.mkdir(parents=True);records=[];active={}
    state=dict(contract=b.CONTRACT,status='PREFLIGHT',operation_id=operation,started=b.old.h.now(),new_emu_runs=0,
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
        for mapping in (hardware,reference_files,m.checker_files(REPO)):
            for path,value in mapping.items():pin(path,value)
        for rel,value in build['source_pins'].items():pin(REPO/rel,value)
        for n,value in build['actual_source_pins'].items():pin(build_dir/'source'/n,value)
        for n,value in build['fixtures'].items():pin(build_dir/'fixture'/n,value)
        for n,value in build['artifacts'].items():pin(build_dir/n,value)
        for p in (identity_path,build_dir/'result.json',build_dir/'tools.json',HERE/'run.py'):pin(p,digest(p))
        for tool in read(build_dir/'tools.json').values():pin(tool['path'],tool['sha256'])
        modules=[*list(sys.modules.values()),b,r,b.old.h,ref,projection,stream,f,m,*gates];seen=set()
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
            image=build_dir/('negative.bin' if mode else 'real-w2.bin')
            argv=[str(Path(cfg['hardware_source'])/'build/emu'),'-i',str(image),'--flash='+cfg['flash'],
                  '--ram-size=128MB','--diff='+cfg['reference'],'--max-cycles='+str(MAX_CYCLES),'--seed=1']
            env=dict(os.environ);env.pop('XS_NEGATIVE_VECTOR_TARGET',None);env.update(OMP_NUM_THREADS='1',EMU_THREADS='1')
            rec=dict(name=label,mode=mode,command=argv,cwd=str(cwd),image_sha256=digest(image),started=b.old.h.now(),
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
        state['status']='NEGATIVE';launch('negative',1,cpus[0]);pending=[];negative_done=False;completed=[]
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
                rec.update(finished=b.old.h.now(),status='EXITED_AWAITING_VALIDATION')
                save(dest/'result.json',rec);del active[label];persist()
                if label=='negative':
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
        decision=performance(normals[0]);save(output/'performance.json',decision)
        state.update(status='W2_BOUNDARY_DIFFTEST_CAMPAIGN_PASS',performance_qualified=decision['comparison_qualified'])
        save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],records=records,validation=normals[0],
            scope='p2 layer5 complete W2 M288 K768; prequantized/prepacked; whole-boundary selfwarm',performance=decision,stage_performance_qualified=decision['comparison_qualified'],full_forward_performance_qualified=False))
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
                rec=item['record'];rec.update(status='FAILED',finished=b.old.h.now())
                for stream_name in ('stdout','stderr'):
                    try:item[stream_name].close()
                    except BaseException as error:rec[stream_name+'_close_error']=repr(error)
                try:
                    rec['raw_sha256']={n:digest(item['dest']/n) for n in ('stdout.log','stderr.log')}
                    save(item['dest']/'result.json',rec)
                except BaseException as error:state.setdefault('evidence_errors',[]).append(dict(name=rec['name'],error=repr(error)))
            state['finished']=b.old.h.now();persist()
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
    return state

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('W2 campaign signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('identity','build','reference','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu-count',type=int,default=3);p.add_argument('--operation-id',required=True)
    a=p.parse_args();result=run(a.identity.resolve(),a.build.resolve(),a.reference.resolve(),a.output.resolve(),a.cpu_count,a.operation_id)
    print(json.dumps({k:result[k] for k in ('status','started','finished','new_emu_runs','performance_qualified')},indent=2))
