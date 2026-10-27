"""Real failure controls for the host runner; no target/emulator execution."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stages_check_controls',HERE/'check.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def controls(repo, output, accepted):
    c.need(not output.exists() and not output.is_relative_to(repo),'fresh controls outside source')
    output.mkdir(parents=True)
    results=[]
    child_code="import pathlib,sys,time; pathlib.Path(sys.argv[1]).write_text('ready'); time.sleep(1.5); pathlib.Path(sys.argv[2]).write_text('escaped')"
    for label, parent_sleep, timeout in [('timeout',10,0.6),('residual',0,5)]:
        ready=output/(label+'.ready');escaped=output/(label+'.escaped')
        parent_code=("import pathlib,subprocess,sys,time; "
                     "p=subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2],sys.argv[3]]); "
                     "\nwhile not pathlib.Path(sys.argv[2]).exists(): time.sleep(.01)\n"
                     "time.sleep(float(sys.argv[4]))")
        try:
            c.command([sys.executable,'-c',parent_code,child_code,ready,escaped,str(parent_sleep)],output,label,timeout=timeout)
            raise AssertionError('lifetime control was accepted')
        except (subprocess.TimeoutExpired, RuntimeError) as error:
            c.need(isinstance(error,subprocess.TimeoutExpired) if label=='timeout' else
                   'live process group' in str(error),'specific process lifetime failure')
        c.need(ready.read_text()=='ready','grandchild actually started before termination')
        time.sleep(1.7)  # Necessary observation window: the live child would write after 1.5 s.
        c.need(not escaped.exists(),'terminated grandchild cannot perform delayed write')
        receipt=json.loads((output/(label+'.command.json')).read_text())
        c.need(receipt['process_group_kill_sent'] and receipt['direct_child_reaped'],'actual group signal/direct-child wait receipt')
        results.append(dict(control=label,status='PASS',receipt=receipt))

    ready=output/'interrupted.ready';escaped=output/'interrupted.escaped'
    previous=signal.getsignal(signal.SIGALRM)
    def interrupt(signum, frame):
        raise KeyboardInterrupt('deliberate runner control')
    signal.signal(signal.SIGALRM,interrupt);signal.setitimer(signal.ITIMER_REAL,0.6)
    try:
        c.command([sys.executable,'-c',parent_code,child_code,ready,escaped,'10'],output,'interrupted',timeout=10)
        raise AssertionError('interrupt control accepted')
    except KeyboardInterrupt:
        pass
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
    time.sleep(1.7)
    receipt=json.loads((output/'interrupted.command.json').read_text())
    c.need(ready.exists() and not escaped.exists() and receipt['status']=='interrupted' and
           receipt['process_group_kill_sent'] and receipt['direct_child_reaped'],'interrupt kills owned ordinary descendants')
    results.append(dict(control='interrupt',status='PASS',receipt=receipt))

    existing=output/'already-exists';existing.mkdir();(existing/'sentinel').write_bytes(b'preserve')
    c.command([sys.executable,'-B',HERE/'check.py','--repo',repo,'--output',existing],output,'existing-output',expected=1)
    c.need([(p.name,p.read_bytes()) for p in existing.iterdir()]==[('sentinel',b'preserve')],
           'rejected existing output remains byte-identical and gains no failure receipt')
    results.append(dict(control='existing-output',status='PASS'))

    bad=output/'bad-reference.c';raw=(repo/c.Q/'forward-host/upstream/runq.c').read_bytes()
    bad.write_bytes(raw.replace(b'1e-5f',b'2e-5f',1))
    try:
        c.gen.generate(bad,output/'bad-forward.inc')
        raise AssertionError('modified reference accepted')
    except ValueError as error:
        c.need('upstream SHA-256' in str(error),'reference change rejected before generation')
    c.need(not (output/'bad-forward.inc').exists(),'bad reference creates no generated candidate')
    results.append(dict(control='modified-reference',status='PASS'))

    forged=output/'bad-stage';forged.mkdir();(forged/'normal').mkdir()
    shutil.copyfile(accepted/'normal.stdout.log',forged/'normal.stdout.log')
    rows=(accepted/'normal/stages.csv').read_text().splitlines()
    fields=rows[1].split(',');fields[4]='99';rows[1]=','.join(fields)
    (forged/'normal/stages.csv').write_text('\n'.join(rows)+'\n')
    try:
        c.read_run(forged,'normal',3,True)
        raise AssertionError('forged stage route accepted')
    except ValueError as error:
        c.need('raw stage labels' in str(error),'independent parser rejects altered actual interval')
    results.append(dict(control='raw-stage-route',status='PASS'))

    gcc=shutil.which('gcc')
    for label,code,flags in [
        ('ubsan','int main(void){volatile int x=2147483647;return (x+1)==0;}',['-fsanitize=undefined']),
        ('asan','#include <stdlib.h>\nint main(void){volatile int *p=malloc(sizeof(*p));p[1]=1;free((void*)p);return 0;}',
         ['-fsanitize=address']),
    ]:
        path=output/(label+'.c');path.write_text(code+'\n')
        c.command([gcc,'-O1',*flags,'-fno-sanitize-recover=all',path,'-o',output/label],output,'compile-control-'+label)
        c.command([output/label],output,'reject-'+label,expected=1,
                  environment={'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
        stderr=(output/('reject-'+label+'.stderr.log')).read_text()
        c.need(('signed integer overflow' if label=='ubsan' else 'heap-buffer-overflow') in stderr,'specific sanitizer rejection')
        results.append(dict(control=label,status='PASS'))
    result=dict(status='RUNNER_FAILURE_CONTROLS_PASS',controls=results,source_sha256=c.sha((HERE/'check.py').read_bytes()),
                test_source_sha256=c.sha((HERE/'test_runner.py').read_bytes()),target_emu_runs=0,completed_at=c.now())
    c.save(output/'result.json',result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--accepted-run',type=Path,required=True)
    args=parser.parse_args();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    result=controls(args.repo.resolve(),args.output.resolve(),args.accepted_run.resolve())
    print(json.dumps(dict(status=result['status'],controls=len(result['controls']))))
