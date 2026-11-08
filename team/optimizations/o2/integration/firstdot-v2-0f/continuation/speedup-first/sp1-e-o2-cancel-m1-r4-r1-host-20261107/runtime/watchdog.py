"""External deadline guardian. Child signals/GIL cannot delay parent enforcement."""
from pathlib import Path
import argparse,ctypes,hashlib,json,math,os,signal,subprocess,sys,time
POLL_SECONDS=.05

def boot_id():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def process_info(pid):
 try:
  raw=(Path('/proc')/str(pid)/'stat').read_text();v=raw[raw.rfind(')')+2:].split()
  return {'pid':int(pid),'ppid':int(v[1]),'pgid':int(v[2]),'sid':int(v[3]),'state':v[0],'start_ticks':int(v[19])}
 except (FileNotFoundError,ProcessLookupError):return None

def snapshot():
 return {int(p.name):v for p in Path('/proc').iterdir() if p.name.isdigit() and (v:=process_info(int(p.name))) is not None}

def write_atomic(path,value):
 path=Path(path);tmp=path.with_name(path.name+'.tmp-'+str(os.getpid()))
 with tmp.open('w') as f:json.dump(value,f,sort_keys=True);f.write('\n')
 os.replace(tmp,path)

def context():
 pid=int(os.environ['B3_R5_GUARD_PID']);info=process_info(pid)
 if pid!=os.getppid() or info is None or info['start_ticks']!=int(os.environ['B3_R5_GUARD_BIRTH']) or boot_id()!=os.environ['B3_R5_GUARD_BOOT']:
  raise ValueError('external guardian parent identity mismatch')
 return Path(os.environ['B3_R5_GUARD_STATE'])

def publish_deadline(deadline,phase='HOST'):
 if not isinstance(deadline,(int,float)) or not math.isfinite(deadline) or deadline<=0:raise ValueError('finite absolute deadline required')
 if phase not in ('HOST','TARGET','OUTER'):raise ValueError('unknown supervised phase')
 path=context();info=process_info(os.getpid())
 write_atomic(path,{'schema':'b3-r5-external-phase-v1','pid':os.getpid(),'start_ticks':info['start_ticks'],'boot_id':boot_id(),'phase':phase,'deadline_monotonic':deadline,'published_monotonic':time.monotonic()})

def require_batch_guard(package):
 path=context()
 if path!=Path(package)/'external-batch/state.json' or os.environ.get('B3_R5_GUARD_MODE')!='batch':raise ValueError('run-batch requires its external guardian')

def run_guard(command,cwd,output,wall_seconds,consume_state=False,mode='HOST_FIXTURE'):
 """One child attempt. Synthetic tests may call this; production CLI has fixed commands/caps."""
 out=Path(output);out.mkdir(parents=True,exist_ok=False)
 if not math.isfinite(wall_seconds) or wall_seconds<=0:raise ValueError('positive finite wall limit')
 if ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'PR_SET_CHILD_SUBREAPER')
 guardian=process_info(os.getpid());boot=boot_id();baseline={(p['pid'],p['start_ticks']) for p in snapshot().values() if p['ppid']==os.getpid()}
 env=dict(os.environ);env.update(B3_R5_GUARD_PID=str(os.getpid()),B3_R5_GUARD_BIRTH=str(guardian['start_ticks']),B3_R5_GUARD_BOOT=boot,B3_R5_GUARD_STATE=str(out/'state.json'),B3_R5_GUARD_MODE=mode,PYTHONDONTWRITEBYTECODE='1')
 started=time.monotonic();overall=started+wall_seconds;known={};events=[];reason=None;trigger=None;last_state=None;child=None
 result={'schema':'b3-r5-external-guard-v1','status':'RUNNING','mode':mode,'command':list(command),'cwd':str(cwd),'boot_id':boot,'guardian':guardian,'started_monotonic':started,'wall_limit_seconds':wall_seconds,'poll_seconds':POLL_SECONDS,'automatic_retry':False}
 write_atomic(out/'START.json',result)
 def discover():
  rows=snapshot();ids={pid for pid,x in known.items() if pid in rows and rows[pid]['start_ticks']==x['info']['start_ticks']}
  if child is not None and child.pid in rows and ('worker' not in result or rows[child.pid]['start_ticks']==result['worker']['start_ticks']):ids.add(child.pid)
  ids.update(pid for pid,x in rows.items() if x['ppid']==os.getpid() and (pid,x['start_ticks']) not in baseline)
  while True:
   more={pid for pid,x in rows.items() if x['ppid'] in ids}
   if more<=ids:break
   ids|=more
  for pid in ids:
   info=rows.get(pid)
   if info is None:continue
   if pid in known and known[pid]['info']['start_ticks']==info['start_ticks']:continue
   if pid in known:os.close(known.pop(pid)['fd'])
   try:fd=os.pidfd_open(pid,0)
   except ProcessLookupError:continue
   again=process_info(pid)
   if again is None or again['start_ticks']!=info['start_ticks']:os.close(fd);continue
   known[pid]={'info':info,'fd':fd};events.append({'event':'owned_process_observed','monotonic':time.monotonic(),'process':info})
  return rows
 def live_rows(rows):
  return [rows[pid] for pid,x in known.items() if pid in rows and rows[pid]['start_ticks']==x['info']['start_ticks'] and rows[pid]['state']!='Z']
 def kill_owned():
  rows=discover()
  for pid,x in known.items():
   row=rows.get(pid)
   if row is None or row['start_ticks']!=x['info']['start_ticks'] or row['state']=='Z':continue
   try:signal.pidfd_send_signal(x['fd'],signal.SIGKILL);events.append({'event':'SIGKILL','pid':pid,'start_ticks':row['start_ticks'],'monotonic':time.monotonic()})
   except ProcessLookupError:pass
 try:
  with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
   child=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True)
   rows=discover();result['worker']=known[child.pid]['info'];write_atomic(out/'START.json',result)
   while True:
    rows=discover();now=time.monotonic();deadline=min(overall,started+900) if mode=='batch' and last_state is None else overall
    if consume_state and last_state is not None and not (out/'state.json').exists():
     reason='MISSING_PHASE_STATE';trigger=now;break
    if consume_state and (out/'state.json').exists():
     st=json.loads((out/'state.json').read_text());now=time.monotonic();owner=result['worker']
     if st.get('schema')!='b3-r5-external-phase-v1' or st.get('pid')!=child.pid or st.get('start_ticks')!=owner['start_ticks'] or st.get('boot_id')!=boot or st.get('phase') not in ('HOST','TARGET','OUTER'):
      reason='INVALID_PHASE_IDENTITY';trigger=now;break
     d=st.get('deadline_monotonic');published=st.get('published_monotonic')
     if not isinstance(d,(int,float)) or not math.isfinite(d) or not isinstance(published,(int,float)) or not math.isfinite(published) or published<started or published>now:
      reason='INVALID_PHASE_DEADLINE';trigger=now;break
     last_state=st;deadline=min(overall,d)
    if now>=deadline:
     reason='EXTERNAL_WALL_LIMIT';trigger=now;result['deadline_at_trigger']=deadline;break
    if child.poll() is not None:
     rows=discover()
     if live_rows(rows):reason='DESCENDANTS_AFTER_WORKER_EXIT';trigger=now
     break
    time.sleep(min(POLL_SECONDS,max(0,deadline-now)))
 except BaseException as exc:
  reason='GUARD_EXCEPTION:'+type(exc).__name__+': '+str(exc);trigger=time.monotonic()
 finally:
  if reason is not None:kill_owned()
  cleanup_start=time.monotonic();cleanup_deadline=cleanup_start+2.0
  while child is not None:
   rows=discover();live=live_rows(rows)
   if live:kill_owned()
   for pid in list(known):
    if pid==child.pid:continue
    try:os.waitpid(pid,os.WNOHANG)
    except ChildProcessError:pass
   child.poll()
   if not live:break
   if time.monotonic()>=cleanup_deadline:break
   time.sleep(.01)
  rows=discover();remaining=live_rows(rows)
  rc=child.poll() if child is not None else None
  ended=time.monotonic();result.update(status='GUARD_PASS' if reason is None and rc==0 and not remaining else 'GUARD_FAIL',reason=reason or ('CHILD_EXIT_'+str(rc) if rc!=0 else None),worker_exit_code=rc,trigger_monotonic=trigger,ended_monotonic=ended,elapsed_seconds=ended-started,cleanup_seconds=ended-cleanup_start,cleanup_ok=not remaining,remaining_live_processes=remaining,last_phase=last_state,events=events)
  write_atomic(out/'RESULT.json',result)
  for x in known.values():os.close(x['fd'])
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=('budget','batch'));a=ap.parse_args();package=Path(__file__).resolve().parent.parent
 if a.mode=='budget':command=[sys.executable,'-B',str(package/'budget-review/measure_delta.py')];output=package/'budget-review/external-01';wall=900;phase=False
 else:command=[sys.executable,'-B',str(package/'runtime/runner.py'),'run-batch'];output=package/'external-batch';wall=14400;phase=True
 result=run_guard(command,package,output,wall,phase,a.mode)
 print(json.dumps({'status':result['status'],'reason':result['reason'],'elapsed_seconds':result['elapsed_seconds'],'cleanup_ok':result['cleanup_ok']}));raise SystemExit(0 if result['status']=='GUARD_PASS' else 1)
if __name__=='__main__':main()
