from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from threading import Lock
import os,time,json,shutil,hashlib
W=Path('/home/lizufan/riscv-lab/fullcore-6d2abe403-20261023-01')
OLD=W/'core-normal-parallel-02';NEW=W/'core-normal-parallel-04'
PLAN=json.loads((W/'four-way-handoff.json').read_text())

def save(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def execute(jobs,worker,max_workers,on_progress):
 assert max_workers==4 and len(jobs)==12
 byname={j[0]:j for j in jobs}
 assert set(byname)==set(PLAN['completed']+PLAN['inflight']+PLAN['pending'])
 records=[];lock=Lock();adopted=[]
 def append(record):
  with lock:
   records.append(record);on_progress(list(records))
  return record
 def adopt(name):
  src=OLD/name
  while not (src/'result.json').exists():
   # A stopped/superseded dispatcher is not a successful test result.
   proc=Path('/proc')/str(PLAN['old_pid'])
   assert proc.exists(),'old dispatcher ended without result: '+name
   time.sleep(.05)
  record=json.loads((src/'result.json').read_text())
  assert record['name']==name
  shutil.copytree(src,NEW/name)
  with lock:
   adopted.append({'name':name,'source':str(src),'copied_to':str(NEW/name),'result_sha256':hashlib.sha256((src/'result.json').read_bytes()).hexdigest(),'new_emu_executed':False})
   save(NEW/'adopted-jobs.json',adopted)
  return append(record)
 for name in PLAN['completed']:adopt(name)
 # The waiting lanes account for the old EMUs still running, so total actual
 # EMU concurrency never exceeds four during or after the handoff.
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures=[pool.submit(adopt,name) for name in PLAN['inflight']]
  futures += [pool.submit(lambda row:append(worker(*row)),byname[name]) for name in PLAN['pending']]
  for f in as_completed(futures):f.result()
 return records