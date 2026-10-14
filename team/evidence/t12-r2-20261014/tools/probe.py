import argparse,datetime,hashlib,json,os,signal,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--cycles',type=int,required=True);p.add_argument('--timeout',type=int,default=180);p.add_argument('--trace-begin',type=int);a=p.parse_args();out=a.output.resolve();out.mkdir(exist_ok=False)
old=Path('/home/lizufan/xiangshan-t10-t11-supervisor-20261013');image=a.image.resolve()
cmd=[str(old/'repo/build/emu'),'-i',str(image),'--flash',str(old/'runs/final-acceptance-20261013-2155/run-0/evidence/boot-flash.bin'),'--ram-size=128MB','--diff',str(old/'nemu-xs-tval/reference/build/riscv64-nemu-interpreter-so'),'-C',str(a.cycles),'--no-snapshot']
if a.trace_begin is not None:cmd+=['--dump-commit-trace','-b',str(a.trace_begin),'-e',str(a.cycles)]
now=lambda:datetime.datetime.now().astimezone().isoformat()
m={'argv':cmd,'started_at':now(),'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'source_parent':'b8272f2e8a62557437869c936b6ea9ce5fff84fe','timeout_seconds':a.timeout};t=time.monotonic()
with (out/'run.log').open('wb') as log:
 child=subprocess.Popen(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);m['pid']=child.pid;(out/'process.json').write_text(json.dumps(m,indent=2)+'\n')
 try:rc=child.wait(timeout=a.timeout);m['timeout']=False
 except subprocess.TimeoutExpired:
  m['timeout']=True;os.killpg(child.pid,signal.SIGTERM)
  try:rc=child.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);rc=child.wait()
 m.update(exit_code=rc,finished_at=now(),host_seconds=time.monotonic()-t);(out/'process.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m))
