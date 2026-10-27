"""Exercise real launcher SIGKILL/child ownership without running a simulator."""
from pathlib import Path
import argparse
import ctypes
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('consumer_run_controls',HERE/'run.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def check(output):
    r.need(not output.exists() and not output.is_relative_to(r.REPO),'new isolated ownership-control evidence')
    output.mkdir(parents=True)
    # Adopt the deliberately orphaned test child so this check can reap it.
    r.need(ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0,'Linux child subreaper')
    program='''import json,os,subprocess,sys,time
from pathlib import Path
dest=Path(sys.argv[1]);mode=sys.argv[2]
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
record=dict(process_started=True,pid=child.pid,process_group=child.pid)
(dest/'result.json').write_text(json.dumps(record))
if mode=='normal':
 child.terminate();record['exit_code']=child.wait()
 record['process_group_absent_after_exit']=True
 (dest/'result.json').write_text(json.dumps(record))
else:
 time.sleep(30)
'''
    results={}
    for name in ('normal','killed-launcher'):
        case=output/name;case.mkdir();proc=None;child=None
        try:
            proc=subprocess.Popen([sys.executable,'-c',program,str(case),name],start_new_session=True)
            deadline=time.monotonic()+5
            while not (case/'result.json').exists() and time.monotonic()<deadline:time.sleep(.02)
            r.need((case/'result.json').exists(),'actual child receipt')
            # The launcher writes a tiny receipt once; wait for complete JSON.
            while True:
                try:record=json.loads((case/'result.json').read_text());break
                except ValueError:
                    r.need(time.monotonic()<deadline,'complete child receipt');time.sleep(.02)
            child=record['pid']
            if name=='killed-launcher':proc.kill()
            proc.wait(timeout=5)
            owned,_=r.case_ownership(output,name,proc);results[name]=owned
            if name=='normal':r.need(owned['cleanup_verified'] is True,'normal launcher and child fully reaped')
            else:
                r.need(owned['launcher_exit_code']==-signal.SIGKILL and
                    owned['launcher_group_present'] is False and owned['reference_group_present'] is True and
                    owned['cleanup_verified'] is False,'launcher death retains actual live-child ownership')
        finally:
            if proc is not None and proc.poll() is None:proc.kill();proc.wait(timeout=5)
            if child is not None:
                try:os.killpg(child,signal.SIGKILL)
                except ProcessLookupError:pass
                try:os.waitpid(child,0)
                except ChildProcessError:pass
                r.need(r.group_present(child) is False,'owned control child cleanup verified')
    results.update(status='ACTUAL_ORPHAN_OWNERSHIP_CONTROL_PASS',all_test_children_reaped=True,
                   source_sha256=r.digest(HERE/'run.py'),check_source_sha256=r.digest(HERE/'check_process_control.py'))
    r.save(output/'result.json',results);return results

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(check(args.output.resolve()),indent=2))
