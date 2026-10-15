import datetime,json,os,pathlib,signal,subprocess,sys,time
j=pathlib.Path('/home/lizufan/xiangshan-t10-t11-supervisor-20261013/runs/final-acceptance-20261013-2155')
b=j.parents[1]; processes=[]
def now():return datetime.datetime.now().astimezone().isoformat()
def publish(name,obj):
 p=j/(name+'.tmp');p.write_text(json.dumps(obj,indent=2)+'\n');p.replace(j/name)
def interrupt(signum,frame):raise SystemExit(128+signum)
if (j/'started.json').exists():raise SystemExit('Run already started; refusing replay')
publish('started.json',{'started_at':now(),'pid':os.getpid(),'source':'1bd6f1d9c9485695876ff37a77fbb175a5125983'})
signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
try:
 for i in range(8):
  p=subprocess.Popen(['bash',str(j/'run-one.sh'),str(i)],start_new_session=True);processes.append((str(i),p))
 p=subprocess.Popen(['bash',str(j/'run-negative.sh')],start_new_session=True);processes.append(('negative',p))
 publish('children.json',{'started_at':now(),'processes':{name:p.pid for name,p in processes}})
 while any(p.poll() is None for _,p in processes):
  publish('progress.json',{'checked_at':now(),'children':{name:p.poll() for name,p in processes},'accepted':False})
  time.sleep(3)
 codes={name:p.returncode for name,p in processes};publish('child-exits.json',{'finished_at':now(),'exit_codes':codes})
 if any(code!=0 for code in codes.values()):raise RuntimeError('Some child runs failed; inspect each raw log')
 with (j/'union-check.log').open('w') as log:
  subprocess.run([sys.executable,'-B',str(j/'verify-union.py'),'--parent-data',str(b/'runs/closure-full-packed-data'),'--runs',str(j),'--repo',str(b/'closure-tval-repo'),'--output',str(j/'accepted.json')],stdout=log,stderr=subprocess.STDOUT,check=True)
 publish('completed.json',{'completed':True,'finished_at':now(),'exit_code':0,'accepted_file':'accepted.json'})
 print('FINAL_REAL_FULLCORE_ACCEPTANCE_COMPLETED',flush=True)
except BaseException as error:
 publish('interrupted-or-failed.json',{'completed':False,'finished_at':now(),'error':repr(error)})
 raise
finally:
 for _,p in processes:
  if p.poll() is None:
   try:os.killpg(p.pid,signal.SIGTERM)
   except ProcessLookupError:pass
 for _,p in processes:
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
