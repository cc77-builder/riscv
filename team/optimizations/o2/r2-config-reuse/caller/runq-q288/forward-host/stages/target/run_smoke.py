"""Run the bounded math/TLS contract on the unchanged T17 DiffTest runtime."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import shutil
import signal
import sys
import time
import types

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[8]
sys.path.insert(0, str(REPO/'team/optimizations/o2/r2-config-reuse'))
import runtime_experiment as parent

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

b=load('forward_math_smoke_build',HERE/'build_smoke.py')
h=b.h
need,save,sha=b.need,b.save,b.sha
MAX_CYCLES=1000000
TIMEOUT=1200

def read(path):return json.loads(Path(path).read_text())
def digest(path):return sha(Path(path).read_bytes())

def cleanup(record):
    """Own only the independent group whose actual PID the launcher recorded."""
    if not record.get('process_started'):return
    pid=record['pid']
    try:os.killpg(pid,0)
    except ProcessLookupError:record['process_group_absent_after_exit']=True;return
    record['residual_process_group']=True
    try:os.killpg(pid,signal.SIGKILL);record['cleanup_kill_sent']=True
    except ProcessLookupError:pass
    try:record['cleanup_wait_status']=os.waitpid(pid,0)[1]
    except ChildProcessError:record['direct_child_already_reaped']=True
    for unused in range(10):
        try:os.killpg(pid,0)
        except ProcessLookupError:record['process_group_absent_after_exit']=True;return
        time.sleep(.1)
    record['process_group_absent_after_exit']=False
    raise RuntimeError('owned EMU process group still exists after cleanup')

def validate_rows(lines, build, mode):
    """Recheck actual raw values independently of the target's PASS label."""
    expected_begin=f"MATH_BEGIN cases=24 tls_offset={build['errno_offset']} control={mode}"
    need(lines and lines[0]==expected_begin,'unique leading math identity/TLS offset')
    values=[]
    for line in lines[1:]:
        if not line.startswith('MATH_VALUE '):continue
        match=re.fullmatch(r'MATH_VALUE (\d+) (\d+) ([0-9a-f]{16}) ([0-9a-f]{16}) (-?\d+) (\d+)',line)
        need(match is not None,'canonical raw math value')
        index,kind=int(match[1]),int(match[2]);raw=[int(match[3],16),int(match[4],16)]
        error,fcsr=int(match[5]),int(match[6])
        need(index==len(values) and index<24,'ordered complete math cases')
        wanted_input=build['inputs'][index];wanted=build['expected'][index]
        need(kind==wanted_input[0],'actual math entry')
        for part,value in enumerate(raw):
            if wanted_input[1]&(1<<part):
                need(value<=0xffffffff and value&0x7f800000==0x7f800000 and value&0x7fffff,'specified binary32 NaN classification')
            else:need(value==wanted[part],'actual finite math result bits')
        need(error==wanted[2],'actual TLS errno')
        need(fcsr>>5==0 and fcsr&wanted_input[2]==wanted_input[2] and not fcsr&~wanted_input[3],
             'actual RNE and required/allowed exception flags')
        values.append(dict(index=index,kind=kind,raw=raw,errno=error,fcsr=fcsr))
    if mode==0:
        need(len(values)==24 and lines[-1]=='MATH_PASS cases=24 errors_checked=8 guard_checks=24' and
             len(lines)==26,'normal complete math transcript')
    elif mode==1:
        need(len(values)==1 and len(lines)==3 and lines[-1]=='MATH_REJECT 0 result','specific first golden rejection')
    elif mode==2:
        need(not values and lines==[expected_begin,'MATH_STACK_GUARD_REJECT'],'actual protected epilogue rejection')
    else:raise ValueError('unknown math control mode')
    return values

def validate(run, build, mode, record, cfg, gates):
    need(record.get('process_started') is True and not record.get('timed_out') and
         not record.get('residual_process_group') and record.get('process_group_absent_after_exit') is True and
         record.get('exit_code')==(0 if mode==0 else 1),'completed expected process exit')
    stdout=(run/'stdout.log').read_text();stderr=(run/'stderr.log').read_text()
    banner,gate,fatal,observer=gates
    banner.validate_runtime(stderr+stdout,cfg['reference'])
    for stream in (stdout,stderr):fatal.reject_fatal_output(stream)
    _,uart=observer.extract_events_and_uart(stderr+stdout)
    plain=gate.normalize_console(uart)
    # Reject every unexpected runtime failure. Only the one expected bad-trap
    # line is excluded in a negative run, after the exact application transcript.
    lines=[line for line in plain.splitlines() if line.startswith('MATH_')]
    values=validate_rows(lines,build,mode)
    need(plain.count('HIT GOOD TRAP')==(1 if mode==0 else 0) and
         plain.count('HIT BAD TRAP')==(0 if mode==0 else 1),'unique expected trap')
    for stream in (stdout,stderr,uart):
        normalized=gate.normalize_console(stream)
        if mode:
            retained=[]
            for line in normalized.splitlines():
                if 'HIT BAD TRAP' in line:
                    need(re.fullmatch(r'(?:Core 0: )?HIT BAD TRAP at pc = 0x[0-9a-f]+',line) is not None,
                         'canonical sole expected bad-trap record, without appended errors')
                else:retained.append(line)
            normalized='\n'.join(retained)
        gate.validate_failure_markers(normalized)
    return dict(status='MATH_DIFFTEST_PASS' if mode==0 else 'EXPECTED_MATH_REJECTION',
                mode=mode,tls_offset=build['errno_offset'],values=values,transcript=lines,
                full_forward_qualified=False,performance_qualified=False)

def run(identity_path, build_dir, output, operation):
    initial=parent.parent_identity(REPO,identity_path)
    cfg=initial['configuration']
    parent.outside_inputs(output,[REPO,identity_path.parent,build_dir,cfg['hardware_source'],cfg['build_record'],cfg['am_home']])
    need(not output.exists(),'fresh output; do not resume failed campaigns')
    ident,hardware,profile=parent.parent_identity(REPO,identity_path,physical=True)
    f,m=parent.runtime(REPO,ident)
    build=read(build_dir/'result.json')
    need(build['status']=='MATH_SMOKE_STATIC_ELF_PASS_NOT_RUNTIME' and build['contract']==b.CONTRACT,'qualified static smoke image')
    need(build['inputs']==[list(r) for r in b.inputs()],'fixed case policy')
    for rel,value in build['source_pins'].items():need(digest(REPO/rel)==value,'smoke source remains frozen: '+rel)
    for name,value in build['artifacts'].items():need(digest(build_dir/name)==value,'smoke artifact remains frozen: '+name)
    b.executable(build_dir/'math-smoke.elf',build_dir/'math-smoke.bin',build_dir/'target-metadata.stdout.log')
    gates=(load('math_runtime_banner',REPO/'team/optimizations/o2/fullcore/run_suite.py'),
           load('math_runtime_failures',REPO/'team/optimizations/o1/audit/runtime_gate.py'),
           load('math_runtime_fatal',REPO/'team/optimizations/o2/fullcore/recheck.py'),
           load('math_runtime_uart',REPO/'team/optimizations/o2/fullcore/analyze.py'))
    output.mkdir(parents=True)
    state=dict(contract=b.CONTRACT,status='PREFLIGHT',operation_id=operation,started=h.now(),new_emu_runs=0,
               active_pid=None,active_result=None,max_cycles=MAX_CYCLES,timeout_seconds=TIMEOUT,cpu_affinity=sorted(os.sched_getaffinity(0)))
    persist=lambda:save(output/'state.json',state)
    persist()
    try:
        files=dict(hardware);files.update(build['external_pins']);files.update(m.checker_files(REPO))
        files.update({str(REPO/rel):value for rel,value in build['source_pins'].items()})
        files[str(identity_path)]=digest(identity_path)
        for name in ('result.json','source-pins.json','external-pins.json','tools.json','target-metadata.stdout.log',*build['artifacts']):
            files[str(build_dir/name)]=digest(build_dir/name)
        for tool in read(build_dir/'tools.json').values():files[tool['path']]=tool['sha256']
        # Include the complete imported Python closure, including this new gate.
        modules=[*list(sys.modules.values()),b,h,parent,f,m,*gates];visited=set()
        while modules:
            module=modules.pop()
            if not isinstance(module,types.ModuleType) or id(module) in visited:continue
            visited.add(id(module))
            modules.extend(value for value in vars(module).values() if isinstance(value,types.ModuleType))
            path=getattr(module,'__file__',None)
            if path:
                path=Path(path).resolve()
                if path.is_relative_to(REPO) and path.is_file():files[str(path)]=digest(path)
        files[str(HERE/'run_smoke.py')]=digest(HERE/'run_smoke.py')
        save(output/'runtime-inputs.json',files);save(output/'configuration.json',cfg)
        save(output/'hardware-profile.json',profile);shutil.copyfile(identity_path,output/'parent-identity.json')
        for path,value in files.items():
            p=Path(path)
            if p.is_relative_to(REPO) and p.suffix in ('.py','.c','.h','.S','.md'):
                dest=output/'source'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
                need(digest(dest)==value,'runtime source snapshot')
        records=[]
        for label,mode,image in (('normal',0,'math-smoke.bin'),('bad-golden',1,'bad-golden.bin'),
                                 ('bad-guard',2,'bad-guard.bin'),('recovery',0,'math-smoke.bin'),('replay',0,'math-smoke.bin')):
            dest=output/'runs'/label;cwd=dest/'cwd';(cwd/'build').mkdir(parents=True)
            for name in m.AUX:shutil.copyfile(Path(cfg['hardware_source'])/'build'/name,cwd/'build'/name)
            inputs=dict(files);inputs.update({str(cwd/'build'/name):value for name,value in m.AUX.items()})
            argv=[str(Path(cfg['hardware_source'])/'build/emu'),'-i',str(build_dir/image),'--flash='+cfg['flash'],
                  '--ram-size=128MB','--diff='+cfg['reference'],'--max-cycles='+str(MAX_CYCLES),'--seed=1']
            rec=dict(contract=b.CONTRACT,name=label,mode=mode,command=argv,cwd=str(cwd),image_sha256=digest(build_dir/image),
                     started=h.now(),process_started=False,exit_code=None,status='RUNNING',files=inputs)
            before=state['new_emu_runs']
            def progress():
                save(dest/'result.json',rec)
                state.update(status=label.upper(),new_emu_runs=before+int(rec.get('process_started') is True),
                             active_pid=rec.get('pid') if not rec.get('process_group_absent_after_exit') else None,
                             active_result=str(dest/'result.json') if not rec.get('process_group_absent_after_exit') else None)
                persist()
            progress()
            try:
                m.verify_files(inputs)
                env=dict(os.environ);env.pop('XS_NEGATIVE_VECTOR_TARGET',None)
                env.update(OMP_NUM_THREADS='1',EMU_THREADS='1')
                rec['environment_overrides']={'XS_NEGATIVE_VECTOR_TARGET':None,'OMP_NUM_THREADS':'1','EMU_THREADS':'1'}
                try:
                    with (dest/'stdout.log').open('wb') as stdout,(dest/'stderr.log').open('wb') as stderr:
                        f.spawn(argv,cwd,stdout,stderr,rec,progress,env,TIMEOUT)
                finally:cleanup(rec)
                result=validate(dest,build,mode,rec,cfg,gates)
                save(dest/'validation.json',result);rec.update(status=result['status'],validation_sha256=digest(dest/'validation.json'))
                m.verify_files(inputs)
            except BaseException as error:rec.update(status='FAILED',error=repr(error));raise
            finally:
                rec.update(finished=h.now(),raw_sha256={name:digest(dest/name) for name in ('stdout.log','stderr.log') if (dest/name).is_file()});progress()
            records.append(rec);save(output/'completed-runs.json',records);print(label,rec['status'],flush=True)
        validations=[read(output/'runs'/label/'validation.json') for label in ('normal','recovery','replay')]
        need(validations[0]==validations[1]==validations[2],'all raw results reproduce in independent normal/recovery/replay processes')
        need(len({r['pid'] for r in records})==5,'five independent completed processes')
        ident2,hardware2,profile2=parent.parent_identity(REPO,identity_path,physical=True)
        need((ident,hardware,profile)==(ident2,hardware2,profile2),'fixed hardware profile after campaign')
        m.verify_files(files)
        save(output/'results.json',dict(contract=b.CONTRACT,status='MATH_TLS_DIFFTEST_CAMPAIGN_PASS',records=records,
             validation=validations[0],full_forward_qualified=False,performance_qualified=False))
        state.update(status='MATH_TLS_DIFFTEST_CAMPAIGN_PASS',active_pid=None,active_result=None)
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=h.now();persist()
    return state

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('math smoke signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--identity',type=Path,required=True);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--operation-id',required=True)
    args=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    print(json.dumps(run(args.identity.resolve(),args.build.resolve(),args.output.resolve(),args.operation_id),indent=2))
