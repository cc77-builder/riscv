"""Run exact full-model projection consumers on the unchanged reference."""
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
import sys
import types

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
b=load('projection_build_runtime',HERE/'build.py')
previous=load('projection_previous_process_control',HERE.parent/'full/run.py')
r=previous.r
REPO=b.REPO
need,save,read,digest=b.need,b.save,b.read,b.digest
MAX_CALLS=4000000000
WALL_SECONDS=1800
MAX_OUTPUT_BYTES=128*1024*1024
STATE_BYTES=3691424
COUNTS=(25,315,10080,43,37,6,172,13)

def validate(build,run,negative,receipt):
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and
         not receipt.get('residual_process_group') and not receipt.get('timed_out') and
         receipt['exit_code']==(2 if negative else 0),'complete owned reference process')
    result=read(run/'reference-result.json');abi=read(run/'abi.json')
    need(abi['register_bytes']==abi['header_span']==1400 and abi['initial_pc']==0x10000000 and abi['initial_mode']==3,'actual fixed reference ABI/reset')
    need(result['state']==2 and result['reason']==('bad_trap' if negative else 'good_trap') and
         result['halt_ret']==(94 if negative else 0) and 0<result['retired']<=result['api_calls']<=MAX_CALLS and
         result['memory_dumps']==8 and result['xiangshan_cycles_measured'] is False,'exact actual terminal reason')
    plain=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',(run/'stdout.log').read_text())
    need(not (run/'stderr.log').read_bytes() and not any(s in plain.lower() for s in ('pma check failed','critical error','reference_adapter_reject','abort')),'no unexplained runtime failure')
    traps=[line for line in plain.splitlines() if 'HIT ' in line and ' TRAP' in line];need(len(traps)<=1,'at most one canonical trap line')
    for line in traps:
        m=re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT (GOOD|BAD) TRAP at pc = (0x[0-9a-fA-F]+)',line)
        need(m is not None and m[1]==('BAD' if negative else 'GOOD') and int(m[2],16)==result['halt_pc'],'canonical optional trap')
    sizes={'report.bin':256,'snapshots.bin':9*STATE_BYTES,'live-states.bin':3*STATE_BYTES,'counts.bin':576,
        'packed-after.bin':172*82944,'tail-scales-after.bin':13*288*9*4,'weights-after.bin':17101440,'embedding-after.bin':36864000,
        'initial-registers.bin':1400,'final-registers.bin':1400,'initial-csrs.bin':32768,'final-csrs.bin':32768}
    need({p.name for p in run.glob('*.bin')}==set(sizes),'complete exact dump set')
    for name,size in sizes.items():need((run/name).stat().st_size==size,'exact complete dump size '+name)
    report=struct.unpack('<32Q',(run/'report.bin').read_bytes())
    need(report[:3]==(0x523250524f4a3031,1,3),'new full consumer identity')
    need(report[3:14]==((94,0,1,36,31999,0,0,0,0,172,13) if negative else (0,2,2,36,0,15,0,3,0,172,13)),
         'exact first classifier-tail rejection or full progress')
    need(report[14]&0x6000 and report[14]&0x600 and report[15]==16,'observed FS/VS enabled and VLEN128')
    flags=report[16:25]
    if negative:need(flags[0]>>5==0 and not any(flags[1:]),'only original p0 flags saved before rejection')
    else:need(all(v>>5==0 for v in flags) and all(flags[3*p]==flags[3*p+1]==flags[3*p+2] for p in range(3)),
              'RNE and identical whole validation-program fflags per position')
    need(not any(report[25:]),'unused report tail remains zero')
    counts=list(struct.iter_unpack('<8Q',(run/'counts.bin').read_bytes()))
    wanted_counts=[(0,)*8]*9
    for pos in range(1 if negative else 3):
        for method in (1,) if negative else (1,2):wanted_counts[pos*3+method]=COUNTS
    need(counts==wanted_counts,'exact original call, quantization and block/tail route counts')
    snapshots=(run/'snapshots.bin').read_bytes();live=(run/'live-states.bin').read_bytes()
    for pos in range(1 if negative else 3):
        gold=(build/'fixture'/f'host-state-p{pos}.bin').read_bytes();need(len(gold)==STATE_BYTES,'independent complete original host state')
        for method in (0,) if negative else range(3):
            actual=snapshots[(pos*3+method)*STATE_BYTES:(pos*3+method+1)*STATE_BYTES]
            need(actual==gold,f'whole actual host/RISC-V state pos={pos} method={method}')
    if negative:
        need(snapshots[STATE_BYTES:]==bytes(8*STATE_BYTES),'candidate not saved and later snapshots untouched')
        gold=(build/'fixture/host-state-p0.bin').read_bytes();bad=bytearray(gold);bad[24480+31999*4]^=1
        need(live[:STATE_BYTES]==gold and live[STATE_BYTES:2*STATE_BYTES]==bytes(bad) and live[2*STATE_BYTES:]==bytes(STATE_BYTES),
             'actual last classifier tail output consumed; exact one-bit live-state damage')
    else:
        gold=(build/'fixture/host-state-p2.bin').read_bytes();need(live==gold*3,'all live final states equal complete p2 reference')
    packed,scales,layout=b.expected_pack((build/'fixture/weights.bin').read_bytes())
    need((run/'packed-after.bin').read_bytes()==packed and (run/'tail-scales-after.bin').read_bytes()==scales,'all packed weights/tail scales independently rebuilt')
    for name,original in (('weights-after.bin','weights.bin'),('embedding-after.bin','embedding.bin')):
        need(digest(run/name)==digest(build/'fixture'/original),'entire original model unchanged')
    return dict(status='EXPECTED_CLASSIFIER_TAIL_REJECTION' if negative else 'FULL_PROJECTION_REFERENCE_HOST_BITS_PASS',
        report=list(report),counts=counts,positions=0 if negative else 3,completed_calls=1 if negative else 9,
        raw_sha256={name:digest(run/name) for name in sizes if name not in ('initial-registers.bin','final-registers.bin','initial-csrs.bin','final-csrs.bin')},
        api_calls=result['api_calls'],retired=result['retired'],target_emu_runs=0,performance_qualified=False)

def run(build,adapter,identity_path,output):
    need(not output.exists(),'fresh output; no resume/overwrite')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE)
    limit=min(MAX_OUTPUT_BYTES,hard) if hard!=resource.RLIM_INFINITY else MAX_OUTPUT_BYTES
    need(limit>=36864000,'complete model dump fits file limit');resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    identity=r.parent.parent_identity(REPO,identity_path)
    r.parent.outside_inputs(output,[REPO,build,adapter,identity_path.parent,identity['configuration']['hardware_source'],identity['configuration']['am_home']])
    f,m=r.parent.runtime(REPO,identity)
    record=read(build/'result.json');need(record['status']=='PROJECTION_STATIC_ELF_PASS_NOT_RUNTIME' and record['contract']==b.CONTRACT,'exact new build contract')
    files=dict(record['external_pins'])
    def pin(path,value):
        path=str(path)
        need(path not in files or files[path]==value,'conflicting frozen input identity: '+path)
        files[path]=value
    for rel,value in record['source_pins'].items():
        pin(REPO/rel,value);pin(build/'source/repo'/rel,value)
    for key,base in (('actual_source_pins',build/'source'),('fixtures',build/'fixture'),('artifacts',build)):
        for name,value in record[key].items():pin(base/name,value)
    b.f.executable(build/'forward-projection.elf',build/'forward-projection.bin',build/'metadata.stdout.log',record['tls_errno_offset'])
    functions=b.kernel_bytes(build/'forward-projection.elf',record['kernel_identity']['functions'])
    for name,raw in functions.items():
        expected=record['kernel_identity']['functions'][name]
        need(len(raw)==expected['bytes'] and b.f.h.sha(raw)==expected['sha256'],'complete final frozen kernel function')
        p=build/'kernel-reference'/f'{name}.bin';need(p.read_bytes()==raw,'raw prior accepted kernel copy');pin(p,digest(p))
    reference=Path(identity['configuration']['reference']);need(digest(reference)==identity['reference_sha256']=='8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9','fixed unchanged reference')
    adapter_inputs=read(adapter/'inputs.json')['files']
    for path,value in adapter_inputs.items():pin(path,value)
    ab=read(adapter/'build.json');need(ab['status']=='REFERENCE_ADAPTER_BUILD_PASS' and ab['inputs_sha256']==digest(adapter/'inputs.json'),'actual adapter build identity')
    need(set(ab['artifacts'])=={'reference-runner','reference_runner.c','runner.d','compile.command.json','compile.stdout.log','compile.stderr.log','nemu.config'},'complete adapter artifact closure')
    for name,value in ab['artifacts'].items():pin(adapter/name,value)
    cr=read(adapter/'compile.command.json')
    need(cr.get('exit_code')==0 and cr.get('status')=='exited' and cr.get('process_group_absent_after_exit') is True and
        str(adapter/'reference_runner.c') in cr['argv'] and cr['argv'][-2:]==['-o',str(adapter/'reference-runner')],'actual successful adapter compile receipt')
    need((adapter/'reference_runner.c').read_bytes()==(HERE.parent/'target/reference_runner.c').read_bytes(),'same reviewed adapter source')
    for p in (reference,build/'result.json',build/'metadata.stdout.log',adapter/'build.json',adapter/'inputs.json',identity_path,HERE/'run.py'):
        pin(p,digest(p))
    modules=[*list(sys.modules.values()),b,previous,r,f,m];visited=set()
    while modules:
        module=modules.pop()
        if not isinstance(module,types.ModuleType) or id(module) in visited:continue
        visited.add(id(module));modules.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
        p=getattr(module,'__file__',None)
        if p:
            p=Path(p).resolve()
            if p.is_relative_to(REPO) and p.is_file():pin(p,digest(p))
    m.verify_files(files)
    output.mkdir(parents=True);save(output/'runtime-inputs.json',files);shutil.copyfile(identity_path,output/'parent-identity.json')
    for path,value in files.items():
        p=Path(path)
        if p.is_relative_to(REPO) and p.suffix in ('.py','.c','.h','.S','.md'):
            dest=output/'source'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);need(digest(dest)==value,'runtime source snapshot')
    state=dict(contract=b.CONTRACT,status='PREFLIGHT',started=b.f.h.now(),reference_runs=0,active_pid=None,active_result=None,
        max_api_calls=MAX_CALLS,wall_limit_seconds=WALL_SECONDS,external_timeout_seconds=WALL_SECONDS+30,
        max_idle_calls=1,max_output_file_bytes=limit,cpu_affinity=sorted(os.sched_getaffinity(0)),performance_qualified=False)
    persist=lambda:save(output/'state.json',state)
    persist()
    try:
        records=[]
        for label,negative in (('normal',False),('bad-tail',True),('recovery',False),('replay',False)):
            dest=output/label;dest.mkdir();image=build/('bad-tail.bin' if negative else 'forward-projection.bin')
            argv=[str(adapter/'reference-runner'),str(reference),str(image),str(dest),'builtin',str(MAX_CALLS),str(WALL_SECONDS),str(build/'dump-plan.txt'),'1']
            rec=dict(name=label,negative=negative,command=argv,cwd=str(dest),started=b.f.h.now(),process_started=False,exit_code=None,status='RUNNING')
            before=state['reference_runs']
            def progress():
                save(dest/'result.json',rec)
                state.update(status=label.upper(),reference_runs=before+int(rec.get('process_started') is True),
                    active_pid=rec.get('pid') if not rec.get('process_group_absent_after_exit') else None,
                    active_result=str(dest/'result.json') if not rec.get('process_group_absent_after_exit') else None);persist()
            progress()
            try:
                m.verify_files(files)
                with (dest/'stdout.log').open('wb') as stdout,(dest/'stderr.log').open('wb') as stderr:
                    previous.spawn(argv,dest,stdout,stderr,rec,progress,dict(os.environ),WALL_SECONDS+30)
                checked=validate(build,dest,negative,rec);save(dest/'validation.json',checked)
                rec.update(status=checked['status'],validation_sha256=digest(dest/'validation.json'));m.verify_files(files)
            except BaseException as error:rec.update(status='FAILED',error=repr(error));raise
            finally:
                rec.update(finished=b.f.h.now(),raw_sha256={p.name:digest(p) for p in dest.iterdir() if p.is_file() and p.name not in ('result.json','validation.json')});progress()
            records.append(rec);save(output/'completed-runs.json',records);print(label,rec['status'],flush=True)
        normals=[read(output/name/'validation.json') for name in ('normal','recovery','replay')]
        need(normals[0]==normals[1]==normals[2],'all raw states/model, counters, flags and retirement repeat exactly')
        need(len({v['pid'] for v in records})==4,'four independent actual processes');m.verify_files(files)
        state.update(status='FULL_PROJECTION_REFERENCE_CAMPAIGN_PASS',active_pid=None,active_result=None)
        save(output/'results.json',dict(contract=b.CONTRACT,status=state['status'],records=records,validation=normals[0],target_emu_runs=0,performance_qualified=False))
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=b.f.h.now();persist()
    return state

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('projection reference signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build','adapter','identity','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();os.sched_setaffinity(0,[3])
    print(json.dumps(run(args.build.resolve(),args.adapter.resolve(),args.identity.resolve(),args.output.resolve()),indent=2))
