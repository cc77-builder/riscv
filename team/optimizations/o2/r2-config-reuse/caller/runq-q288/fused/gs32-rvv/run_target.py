"""One bounded T17 campaign: bit100 rejection, then two isolated normal runs.

The normal runs use one thread each. The second run checks determinism and is
never counted as an additional performance observation. No source or reference
library is edited, and no build is started here.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import argparse
import json
import os
import signal
import subprocess
import sys

import check_target as check
import target

need, sha, save, read = check.need, check.sha, check.save, check.read
# The frozen checkers temporarily bind names in sys.modules. Keep their whole
# load/use sequence serial; the two owned EMU processes still run in parallel.
_CHECKER_LOCK = Lock()
T17 = Path('/home/lizufan/riscv-lab/t17-clean-20261024-0854')
EMU = T17/'clean-02/source/build/emu'
REFERENCE = T17/'support-01/nemu/reference/build/riscv64-nemu-interpreter-so'
FLASH = Path('/home/riscv/riscv-lab/t12-regression-20261013/repo/team/workloads/hello-vadd/build/boot-flash.bin')
NEGATIVE_ROOT = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/fullq-tail-target-20261026-1400/campaign-01/negative-fixture')
NEGATIVE = NEGATIVE_ROOT/'negative-reference.so'
PINS = {
    EMU:'ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f',
    REFERENCE:'8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9',
    FLASH:'a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994',
    NEGATIVE:'c70b0ad5b5a71032e96c3d32bfcdb3e17512eb8617ae85d201bf3fb6a85732e6',
    NEGATIVE_ROOT/'negative-fixture.c':'7b39400d0a566229ce018a8251ead8242b92a3afe05a1aee5711b38809056273',
    NEGATIVE_ROOT/'fixture.json':'39346acb3f337bcaaa2fe23705df0387df4bb1595c5fc95d7aa7376387e047f5',
    T17/'build-01/build-command.sh':'fea1dd529464a07aba5f0c99c57fd6b7987ce66b9758b2778622c3273d938d07',
    T17/'build-01/hardware-inputs.json':'7c42a8130e71b39e8f5ca08d7d662a85ac58f677040c6293d38007b007ac0dcc',
    T17/'build-01/build-state.json':'2d284bd2e1800ef1dee56e41f5a5f44f35739695b05312d94ffd3b514af2c36a',
}


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_files(pins):
    for path,pin in pins.items():
        need(sha(Path(path).read_bytes()) == pin, 'runtime input drift '+str(path))


def banner(text, reference):
    need('The first instruction of core 0 has commited. Difftest enabled.' in text,
         'real DiffTest enable banner')
    need('The reference model is '+str(reference) in text, 'selected real DiffTest reference')


def run_one(repo, build, out, name, core, pins, negative=False):
    verify_files(pins)
    run = out/'runs'/name
    cwd = run/'cwd'
    cwd.mkdir(parents=True, exist_ok=False)
    reference = NEGATIVE if negative else REFERENCE
    command = ['/usr/bin/taskset','-c',str(core),str(EMU),'-i',str(build/'gs32-target.bin'),
        '--flash='+str(FLASH),'--ram-size=128MB','--diff='+str(reference),
        '--max-cycles=12000000','--seed=1']
    env = dict(os.environ)
    env.pop('XS_NEGATIVE_VECTOR_TARGET',None)
    if negative:
        env['XS_NEGATIVE_VECTOR_TARGET'] = 'vdot'
    receipt = dict(contract=target.CONTRACT,name=name,negative=negative,command=command,
        cwd=str(cwd),reference=str(reference),cpu_affinity=[core],emu_threads=1,
        started=now(),process_started=False,timed_out=False,exit_code=None,
        negative_target='vdot' if negative else None)
    save(run/'runtime.json',receipt)
    with (run/'stdout.log').open('wb') as stdout, (run/'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command,cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        receipt.update(pid=process.pid,process_started=True)
        save(run/'runtime.json',receipt)
        print(json.dumps(dict(event='started',name=name,pid=process.pid,at=receipt['started'],core=core)),flush=True)
        try:
            receipt['exit_code'] = process.wait(timeout=5400)
        except subprocess.TimeoutExpired:
            receipt['timed_out'] = True
            os.killpg(process.pid,signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
            receipt['exit_code'] = process.returncode
    receipt.update(finished=now(),raw_sha256={n:sha((run/n).read_bytes()) for n in ('stdout.log','stderr.log')})
    save(run/'runtime.json',receipt)
    verify_files(pins)
    text = (run/'stderr.log').read_text()+(run/'stdout.log').read_text()
    banner(text,reference)
    need(not receipt['timed_out'], 'runtime timeout '+name)
    with _CHECKER_LOCK:
        if negative:
            gate = check.helper(repo,'team/optimizations/o1/audit/runtime_gate.py')
            result = gate.validate_negative(text,receipt['exit_code'])
            check.helper(repo,'team/optimizations/o2/fullcore/recheck.py').reject_fatal_output(text)
            model,_,_ = check.support(repo)
            elf = model.ELF((build/'gs32-target.elf').read_bytes())
            need(int(result['pc'],16) == elf.symbols['q_fault_probe'][0]+20, 'isolated bit100 probe PC')
            result.update(status='GS32_EXPECTED_BIT100_REJECTION',reference_unchanged=True)
        else:
            result = check.analyze(repo,build,run,receipt)
    save(run/'analysis.json',result)
    print(json.dumps(dict(event='checked',name=name,status=result['status'],at=now())),flush=True)
    return dict(name=name,receipt=receipt,result=result)


def campaign(repo, build, validation, out):
    need(not out.exists() and not out.is_relative_to(repo), 'fresh campaign outside source')
    proof = read(validation)
    need(proof['status'] == 'GS32_TARGET_ELF_DATASET_TIMER_PATH_PASS'
         and proof['contract'] == target.CONTRACT, 'actual ELF/data/timer proof before launch')
    pins = dict(PINS)
    pins.update({build/'gs32-target.elf':proof['elf_sha256'],build/'gs32-target.bin':proof['bin_sha256'],
                 validation:sha(validation.read_bytes())})
    for rel,pin in check.HELPER_PINS.items():
        pins[repo/rel] = pin
    own = Path(__file__).resolve().parent
    controller = [own/n for n in ('CONTRACT.md','generate.py','screen.py','target.py','check_target.py','run_target.py')]
    pins.update({p:sha(p.read_bytes()) for p in controller})
    verify_files(pins)
    out.mkdir(parents=True)
    (out/'controller').mkdir()
    for p in controller:
        (out/'controller'/p.name).write_bytes(p.read_bytes())
    save(out/'inputs.json',{str(p):pin for p,pin in pins.items()})
    state = dict(contract=target.CONTRACT,status='RUNNING',started=now(),new_emu_runs=0,
        required_runs=['negative','recovery','replay'],max_concurrent_emu=2,
        cpu_affinity=[0,1],host_memory=Path('/proc/meminfo').read_text())
    save(out/'state.json',state)
    records = []
    try:
        negative = run_one(repo,build,out,'negative',0,pins,negative=True)
        records.append(negative)
        state.update(new_emu_runs=1,negative_checked=True)
        save(out/'state.json',state)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(run_one,repo,build,out,name,core,pins)
                    for name,core in (('recovery',0),('replay',1))]
            records.extend(job.result() for job in jobs)
        a,b = records[1:]
        need(all(r['receipt']['started'] >= negative['receipt']['finished'] for r in (a,b)),
             'both normal runs start after successful negative termination')
        need(a['result']['samples'] == b['result']['samples'] and
             a['result']['all_stage_custom_pc_sha256'] == b['result']['all_stage_custom_pc_sha256'],
             'exact deterministic counter/PC replay; no extra performance sample')
        verify_files(pins)
        save(out/'results.json',dict(contract=target.CONTRACT,records=records))
        state.update(status='GS32_TARGET_DIFFTEST_CAMPAIGN_PASS',new_emu_runs=3,
            replay_equal=True,candidate_qualified=a['result']['selection']['candidate_qualified'])
    except BaseException as error:
        state.update(status='FAILED',error=repr(error),
            new_emu_runs=sum((out/'runs'/name/'runtime.json').is_file() for name in state['required_runs']))
        raise
    finally:
        state['finished'] = now()
        save(out/'state.json',state)
    return state


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--validation',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    sys.dont_write_bytecode = True
    os.sched_setaffinity(0,[0,1])
    result = campaign(a.repo.resolve(),a.build.resolve(),a.validation.resolve(),a.output.resolve())
    print(json.dumps({k:v for k,v in result.items() if k != 'host_memory'},indent=2))


if __name__ == '__main__':
    main()
