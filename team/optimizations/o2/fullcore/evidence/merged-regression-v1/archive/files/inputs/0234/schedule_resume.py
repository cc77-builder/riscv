from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from threading import Lock
import os,signal,time,json,shutil,hashlib
from datetime import datetime
W=Path('/home/lizufan/riscv-lab/fullcore-6d2abe403-20261023-01')
OLD=W/'core-normal-partial-01';NEW=W/'core-normal-parallel-02'
OLD_PID=1152

def save(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def proc(pid):
 p=Path('/proc')/str(pid)
 try:
  cmd=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode()
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split()
  return {'pid':pid,'ppid':int(f[1]),'state':f[0],'start_ticks':f[19],'command':cmd}
 except FileNotFoundError:return None

def stop_old_dispatcher():
 current=proc(OLD_PID)
 if current is None:return {'status':'already_exited'}
 assert str(W/'tools-normal-partial/run_normal_partial.py') in current['command'] and str(OLD) in current['command']
 os.kill(OLD_PID,signal.SIGSTOP)
 time.sleep(.05)
 # Only this verified dispatcher's descendants may be stopped. Any accidental
 # next-job start is preserved as interrupted and is never counted as a pass.
 allprocs=[proc(int(p.name)) for p in Path('/proc').iterdir() if p.name.isdigit()]
 descendants=[];parents={OLD_PID}
 while True:
  extra=[p for p in allprocs if p and p['ppid'] in parents and p['pid'] not in parents]
  if not extra:break
  descendants.extend(extra);parents.update(p['pid'] for p in extra)
 for p in reversed(descendants):
  assert '/home/lizufan/riscv-lab/xiangshan/build/emu' in p['command'],p
  try:os.kill(p['pid'],signal.SIGTERM)
  except ProcessLookupError:pass
 os.kill(OLD_PID,signal.SIGTERM);os.kill(OLD_PID,signal.SIGCONT)
 result={'status':'DISPATCHER_RETIRED_AFTER_FUNCTIONAL_0_RESULT','old_process':current,'terminated_pending_descendants':descendants,
         'finished':datetime.now().astimezone().isoformat(),'completed_results_preserved':True,'restarted_running_functional_0':False}
 save(W/'parallel-transition.json',result)
 save(OLD/'orchestration-retired.json',result)
 return result

def execute(jobs,worker,max_workers,on_progress):
 assert max_workers==2 and len(jobs)==12
 records=[];lock=Lock();adopted=[]
 def append(record):
  with lock:
   records.append(record);on_progress(list(records))
  return record
 def adopt(name):
  src=OLD/name
  record=json.loads((src/'result.json').read_text())
  shutil.copytree(src,NEW/name)
  adopted.append({'name':name,'source':str(src),'copied_to':str(NEW/name),'result_sha256':hashlib.sha256((src/'result.json').read_bytes()).hexdigest(),'new_emu_executed':False})
  save(NEW/'adopted-jobs.json',adopted)
  return append(record)
 adopt('hello-vadd');adopt('negative-vdot')
 def finish_current():
  result=OLD/'functional-0/result.json'
  while not result.exists():
   assert proc(OLD_PID) is not None,'original dispatcher exited before functional-0 result'
   time.sleep(.01)
  stop_old_dispatcher()
  return adopt('functional-0')
 with ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(finish_current)]
  futures += [pool.submit(lambda row:append(worker(*row)),item) for item in jobs[3:]]
  for f in as_completed(futures):f.result()
 return records