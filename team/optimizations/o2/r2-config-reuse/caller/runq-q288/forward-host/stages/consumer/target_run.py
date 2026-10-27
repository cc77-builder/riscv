"""Run one bounded, owned original EMU; retain raw evidence for separate audit."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import resource
import shutil
import signal
import struct
import time
import types

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('consumer_target_inputs',HERE/'aux_run.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
r=a.r
need,read,save,digest=a.need,a.read,a.save,a.digest

def run(build,reference_campaign,adapter,identity_path,output,method,negative,max_cycles,timeout,log_mib,operation):
    need(method in (3,4) and 1<=max_cycles<=100000000 and 1<=timeout<=28800 and 128<=log_mib<=8192,'explicit bounded target parameters')
    need(not output.exists() and len(os.sched_getaffinity(0))==1,'fresh output and one assigned CPU')
    record,files,initial,checker=a.inputs(build,adapter,identity_path)
    need(record['kind']=='target','actual target harness')
    qualified=read(reference_campaign/'results.json');state=read(reference_campaign/'state.json')
    need(qualified['status']==state['status']=='SHARED_CONSUMER_AUX_REFERENCE_CAMPAIGN_PASS' and qualified['kind']=='target' and state['active_pid'] is None,'completed exact target-harness reference qualification')
    qinputs=read(reference_campaign/'runtime-inputs.json')
    for name,value in record['artifacts'].items():need(qinputs[str(build/name)]==value,'same reference-qualified final target artifact')
    cfg=initial['configuration']
    r.r.parent.outside_inputs(output,[r.REPO,build,reference_campaign,adapter,identity_path.parent,Path(cfg['hardware_source']),Path(cfg['build_record']),Path(cfg['am_home'])])
    identity,hardware,profile=r.r.parent.parent_identity(r.REPO,identity_path,physical=True)
    _,runtime=r.r.parent.runtime(r.REPO,identity)
    def pin(path,value):
        path=str(path);need(path not in files or files[path]==value,'no input identity rebinding');files[path]=value
    for name,value in hardware.items():pin(name,value)
    for p in (reference_campaign/'results.json',reference_campaign/'state.json',reference_campaign/'runtime-inputs.json',HERE/'target_run.py'):
        pin(p,digest(p))
    for module in list(__import__('sys').modules.values()):
        if not isinstance(module,types.ModuleType):continue
        name=getattr(module,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_relative_to(r.REPO) and p.is_file():pin(p,digest(p))
    # These exact original sources explain the new CLI profile. Never rewrite them.
    for rel in ('difftest/src/test/csrc/verilator/emu.cpp','difftest/verilator.mk',
                'difftest/src/main/scala/Difftest.scala','src/main/scala/xiangshan/backend/exu/ExeUnit.scala',
                'src/main/scala/xiangshan/backend/rob/Rob.scala','build/rtl/ExeUnit_17.sv'):
        path=Path(cfg['hardware_source'])/rel;pin(path,digest(path))
    runtime.verify_files(files)
    output.mkdir(parents=True);cwd=output/'cwd';(cwd/'build').mkdir(parents=True)
    for name,value in runtime.AUX.items():
        path=cwd/'build'/name;shutil.copyfile(Path(cfg['hardware_source'])/'build'/name,path);pin(path,value)
    image=bytearray((build/'consumer-target.bin').read_bytes());offset=record['control_offset']
    image[offset:offset+12]=struct.pack('<3I',method,int(negative),1);(output/'image.bin').write_bytes(image);pin(output/'image.bin',digest(output/'image.bin'))
    save(output/'image-control.json',dict(base_sha256=record['artifacts']['consumer-target.bin'],offset=offset,controls=[method,int(negative),1],sha256=digest(output/'image.bin')))
    pin(output/'image-control.json',digest(output/'image-control.json'))
    save(output/'runtime-inputs.json',files);save(output/'configuration.json',cfg);save(output/'hardware-profile.json',profile)
    shutil.copyfile(identity_path,output/'parent-identity.json');r.snapshot_runtime(output,files)
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=log_mib*1024*1024
    need(hard==resource.RLIM_INFINITY or hard>=limit,'inherited hard file limit supports declared budget');resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    argv=[str(Path(cfg['hardware_source'])/'build/emu'),'-i',str(output/'image.bin'),'--flash='+cfg['flash'],'--ram-size=128MB',
          '--diff='+cfg['reference'],'--max-cycles='+str(max_cycles),'--seed=1','--log-end=0']
    env=dict(os.environ);env.pop('XS_NEGATIVE_VECTOR_TARGET',None);env.update(OMP_NUM_THREADS='1',EMU_THREADS='1')
    rec=dict(contract=a.a.CONTRACT,operation_id=operation,status='RUNNING',command=argv,cwd=str(cwd),started=a.a.b.f.h.now(),
        process_started=False,exit_code=None,method=method,negative=negative,cpu_affinity=sorted(os.sched_getaffinity(0)),
        max_cycles=max_cycles,external_timeout_seconds=timeout,max_output_file_bytes=limit,
        environment_overrides={'XS_NEGATIVE_VECTOR_TARGET':None,'OMP_NUM_THREADS':'1','EMU_THREADS':'1'},
        log_profile='log-end=0; original bare O2/T13 printf retained; original DiffTest/UART enabled',
        target_correctness_qualified=False,performance_qualified=False)
    persist=lambda:save(output/'result.json',rec);persist();begin=time.monotonic()
    try:
        runtime.verify_files(files)
        with (output/'stdout.log').open('wb') as stdout,(output/'stderr.log').open('wb') as stderr:
            r.previous.spawn(argv,cwd,stdout,stderr,rec,persist,env,timeout)
        runtime.verify_files(files)
        need(r.r.parent.parent_identity(r.REPO,identity_path,physical=True)==(identity,hardware,profile),'physical hardware profile unchanged')
        rec.update(status='TARGET_PROCESS_EXITED_REQUIRES_RAW_AUDIT')
    except BaseException as error:rec.update(status='FAILED_OR_PARTIAL_REQUIRES_RAW_AUDIT',error=repr(error));raise
    finally:
        rec.update(finished=a.a.b.f.h.now(),observed_elapsed_seconds=time.monotonic()-begin,
            child_maxrss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            raw_sha256={name:digest(output/name) for name in ('stdout.log','stderr.log') if (output/name).exists()},
            raw_bytes={name:(output/name).stat().st_size for name in ('stdout.log','stderr.log') if (output/name).exists()})
        persist()
    return rec

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('consumer target signal')))
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','reference-campaign','adapter','identity','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--method',type=int,choices=(3,4),required=True);parser.add_argument('--negative',action='store_true')
    parser.add_argument('--max-cycles',type=int,required=True);parser.add_argument('--timeout',type=int,required=True)
    parser.add_argument('--log-mib',type=int,required=True);parser.add_argument('--operation-id',required=True);args=parser.parse_args()
    result=run(*(getattr(args,n).resolve() for n in ('build','reference_campaign','adapter','identity','output')),
        args.method,args.negative,args.max_cycles,args.timeout,args.log_mib,args.operation_id)
    print(json.dumps({n:result[n] for n in ('status','exit_code','observed_elapsed_seconds','raw_bytes','child_maxrss_kib','performance_qualified')},indent=2))
