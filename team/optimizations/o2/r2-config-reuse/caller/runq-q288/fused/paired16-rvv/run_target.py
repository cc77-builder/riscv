"""Bounded T17 negative/recovery/replay campaign; only EMUs run in parallel.

CPU IDs must be supplied from the current coordinator allocation. This program
does not build hardware, modify a reference, or start a new automation.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import argparse
import json
import os
import signal
import subprocess
import sys

import check_target as check
import target

need,sha,save,read=check.need,check.sha,check.save,check.read


def now():
    return datetime.now(timezone.utc).isoformat()


def hash_file(path):
    import hashlib
    value=hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):
            value.update(chunk)
    return value.hexdigest()


def verify_files(pins):
    for path,pin in pins.items():
        need(hash_file(path)==pin,'runtime input drift '+str(path))


def stop_process(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    return process.returncode


def run_process(build,out,name,core,pins,base,negative=False):
    """Process/receipt I/O only: never import or execute an analysis helper."""
    verify_files(pins)
    run=out/'runs'/name
    cwd=run/'cwd'
    cwd.mkdir(parents=True,exist_ok=False)
    reference=base.NEGATIVE if negative else base.REFERENCE
    command=['/usr/bin/taskset','-c',str(core),str(base.EMU),'-i',str(build/'paired16-target.bin'),
        '--flash='+str(base.FLASH),'--ram-size=128MB','--diff='+str(reference),
        '--max-cycles=12000000','--seed=1']
    env=dict(os.environ)
    env.pop('XS_NEGATIVE_VECTOR_TARGET',None)
    if negative:
        env['XS_NEGATIVE_VECTOR_TARGET']='vdot'
    receipt=dict(contract=target.CONTRACT,name=name,negative=negative,command=command,cwd=str(cwd),
        reference=str(reference),cpu_affinity=[core],emu_threads=1,started=now(),process_started=False,
        timed_out=False,exit_code=None,negative_target='vdot' if negative else None,
        analysis_in_worker=False)
    save(run/'runtime.json',receipt)
    process=None
    try:
        with (run/'stdout.log').open('wb') as stdout,(run/'stderr.log').open('wb') as stderr:
            process=subprocess.Popen(command,cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            receipt.update(pid=process.pid,process_started=True)
            save(run/'runtime.json',receipt)
            print(json.dumps(dict(event='started',name=name,pid=process.pid,core=core,at=receipt['started'])),flush=True)
            try:
                receipt['exit_code']=process.wait(timeout=5400)
            except subprocess.TimeoutExpired:
                receipt['timed_out']=True
                receipt['exit_code']=stop_process(process)
    except BaseException as error:
        if process is not None:
            receipt['exit_code']=stop_process(process)
        receipt.update(finished=now(),aborted=True,error=repr(error))
        try:
            save(run/'runtime.json',receipt)
        except OSError:
            pass
        raise
    receipt['finished']=now()
    save(run/'runtime.json',receipt)
    print(json.dumps(dict(event='process_exited',name=name,exit_code=receipt['exit_code'],
                          at=receipt['finished'])),flush=True)
    return receipt


def analyze_process(repo,build,out,name,receipt,pins,base):
    """Called on the main thread after process termination."""
    run=out/'runs'/name
    receipt['raw_sha256']={n:hash_file(run/n) for n in ('stdout.log','stderr.log')}
    save(run/'runtime.json',receipt)
    verify_files(pins)
    need(not receipt['timed_out'],'runtime timeout '+name)
    text=(run/'stderr.log').read_text()+(run/'stdout.log').read_text()
    need('The first instruction of core 0 has commited. Difftest enabled.' in text,
         'real DiffTest enable banner')
    need('The reference model is '+receipt['reference'] in text,'selected real reference')
    if receipt['negative']:
        ctx=check.support(repo)
        gate=ctx['base'].helper(repo,'team/optimizations/o1/audit/runtime_gate.py')
        fatal=ctx['base'].helper(repo,'team/optimizations/o2/fullcore/recheck.py')
        result=gate.validate_negative(text,receipt['exit_code'])
        fatal.reject_fatal_output(text)
        elf=ctx['model'].ELF((build/'paired16-target.elf').read_bytes())
        need(int(result['pc'],16)==elf.symbols['q_fault_probe'][0]+20,'isolated bit100 probe PC')
        result.update(status='PAIRED16_EXPECTED_BIT100_REJECTION',reference_unchanged=True)
    else:
        del text
        result=check.analyze(repo,build,run,receipt)
    save(run/'analysis.json',result)
    print(json.dumps(dict(event='checked_serially',name=name,status=result['status'],at=now())),flush=True)
    return dict(name=name,receipt=receipt,result=result)


def campaign(repo,build,validation,out,cores):
    need(not out.exists() and not out.is_relative_to(repo),'fresh isolated campaign')
    need(len(cores)==2 and len(set(cores))==2 and all(c>=0 for c in cores),'two distinct allocated CPU IDs')
    proof=read(validation)
    need(proof['status']=='PAIRED16_TARGET_ELF_DATASET_TIMER_PATH_PASS' and
         proof['contract']==target.CONTRACT,'actual ELF/data/timer proof before launch')
    modules=target.gs32_modules(repo)
    base=modules['run_target']
    pins=dict(base.PINS)
    pins.update({build/'paired16-target.elf':proof['elf_sha256'],
                 build/'paired16-target.bin':proof['bin_sha256'],validation:hash_file(validation),
                 build/'source/manifest.json':proof['manifest_sha256'],
                 build/'source/producer-inputs.json':proof['producer_inventory_sha256']})
    for relative,identity in proof['producer_files'].items():
        pins[repo/relative]=identity['physical_sha256']
    for relative,pin in modules['check_target'].HELPER_PINS.items():
        pins[repo/relative]=pin
    own=Path(__file__).resolve().parent
    controller=[own/n for n in ('CONTRACT.md','TARGET_CONTRACT.md','generate.py','screen.py',
                                'target.py','check_target.py','run_target.py')]
    for path in controller:
        current=hash_file(path)
        need(path not in pins or pins[path]==current,
             'controller equals preflight producer identity '+str(path))
        pins[path]=current
    verify_files(pins)
    out.mkdir(parents=True)
    (out/'controller').mkdir()
    for path in controller:
        (out/'controller'/path.name).write_bytes(path.read_bytes())
    save(out/'inputs.json',{str(path):pin for path,pin in pins.items()})
    state=dict(contract=target.CONTRACT,status='RUNNING',started=now(),new_emu_runs=0,
        required_runs=['negative','recovery','replay'],max_concurrent_emu=2,cpu_affinity=list(cores),
        analysis_policy='main-thread serial, only after both normal processes terminate',
        host_memory=Path('/proc/meminfo').read_text())
    save(out/'state.json',state)
    records=[]
    try:
        receipt=run_process(build,out,'negative',cores[0],pins,base,negative=True)
        negative=analyze_process(repo,build,out,'negative',receipt,pins,base)
        records.append(negative)
        state.update(new_emu_runs=1,negative_checked=True)
        save(out/'state.json',state)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs=[pool.submit(run_process,build,out,name,core,pins,base)
                  for name,core in zip(('recovery','replay'),cores)]
            receipts=[job.result() for job in jobs]
        # No dynamic module loading while either worker can still run.
        for name,receipt in zip(('recovery','replay'),receipts):
            need(receipt['started']>=negative['receipt']['finished'],
                 'normal run begins after expected negative termination')
            records.append(analyze_process(repo,build,out,name,receipt,pins,base))
        first,second=records[1:]
        need(first['result']['samples']==second['result']['samples'] and
             first['result']['all_stage_custom_pc_sha256']==second['result']['all_stage_custom_pc_sha256'],
             'exact deterministic counter/PC replay; not another performance observation')
        verify_files(pins)
        save(out/'results.json',dict(contract=target.CONTRACT,records=records))
        state.update(status='PAIRED16_TARGET_DIFFTEST_CAMPAIGN_PASS',new_emu_runs=3,replay_equal=True,
                     candidate_qualified=first['result']['selection']['candidate_qualified'])
    except BaseException as error:
        state.update(status='FAILED',error=repr(error),
            new_emu_runs=sum((out/'runs'/name/'runtime.json').is_file() for name in state['required_runs']))
        raise
    finally:
        state['finished']=now()
        save(out/'state.json',state)
    return state


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','build','validation','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--cores',type=int,nargs=2,required=True,
                        help='two CPU IDs explicitly assigned for this campaign')
    args=parser.parse_args()
    sys.dont_write_bytecode=True
    os.sched_setaffinity(0,args.cores)
    result=campaign(args.repo.resolve(),args.build.resolve(),args.validation.resolve(),
                    args.output.resolve(),tuple(args.cores))
    print(json.dumps({k:v for k,v in result.items() if k!='host_memory'},indent=2))
