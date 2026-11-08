"""SP1-C explicit-root build; never invokes EMU, clean, PGO, or Git publication."""
from pathlib import Path
from datetime import datetime, timezone
import os, sys, json, hashlib, subprocess, time, signal
R=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
C=Path('/home/riscv/riscv-lab/speedup-first-20261103/sp1-ab/candidate')
P=R/'team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first'
A=P/'sp1-ab'; O=P/'sp1-cd/build'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def save(p,v):
 q=Path(str(p)+'.tmp'); q.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n'); q.replace(p)
def now(): return datetime.now(timezone.utc).isoformat()
def req(x,m):
 if not x: raise RuntimeError(m)
def read(p): return json.loads(Path(p).read_text())
def git(*a): return subprocess.check_output(['git','-C',str(R),*a]).decode()
def verify(pins):
 for p,h in pins.items(): req(Path(p).is_file() and sha(p)==h,'identity changed: '+p)
def group_members(pgid):
 found=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit(): continue
  try:
   st=(proc/'stat').read_text().rsplit(')',1)[1].split()
   if int(st[2])==pgid and st[0]!='Z': found.append(int(proc.name))
  except (OSError,ValueError,IndexError): pass
 return found

def cleanup(pgid):
 before=group_members(pgid)
 for sig in [signal.SIGTERM,signal.SIGKILL]:
  if not group_members(pgid): break
  try: os.killpg(pgid,sig)
  except ProcessLookupError: pass
  for _ in range(100):
   if not group_members(pgid): break
   time.sleep(.1)
 return {'before':before,'remaining':group_members(pgid),'utc':now()}

def configuration():
 env={'HOME':'/home/riscv','USER':'riscv','LOGNAME':'riscv','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
 'PATH':'/opt/graalvm-jdk-21/bin:/usr/local/llvm/bin:/usr/local/bin:/usr/bin:/bin',
 'JAVA_HOME':'/opt/graalvm-jdk-21','CHISEL_FIRTOOL_PATH':'/home/riscv/.cache/llvm-firtool/1.62.1/bin',
 'NOOP_HOME':str(C),'DESIGN_DIR':str(C),'MILL_WORKSPACE_ROOT':str(C),
 'VDOT_O2_ELASTIC':'1','VDOT_T14_FUSED_INPUT':'1','VDOT_O1_HANDOFF':'0','VDOT_O1_TRACE':'0',
 'VDOT_T12_TRACE':'0','VDOT_T13_TRACE':'1','VDOT_P4_ONE_CYCLE':'1','VDOT_O2_TRACE':'0','VDOT_SP1_TRACE':'1'}
 cmd=['/usr/bin/make','emu','CONFIG=MinimalConfig','NUM_CORES=1','EMU_THREADS=1','JVM_XMX=12G','JVM_XSS=16m','OPT_FAST=-O3','OPT_SLOW=-O0','-j2',
 'NOOP_HOME='+str(C),'DESIGN_DIR='+str(C),'REMOTE=localhost','PGO_WORKLOAD=',
 'WITH_DRAMSIM3=0','WITH_RESETGEN=0','EMU_TRACE=0','EMU_COVERAGE=0','EMU_SNAPSHOT=0']
 return env,cmd

def freeze():
 req(not (O/'FREEZE.json').exists(),'already frozen'); req(not (C/'build').exists(),'candidate build already exists')
 pins={}; derived={}
 for f in ['source-manifest-v1.json','evidence/fullcore-build-support.json']:
  for x in read(A/f)['files']: pins[str(C/x['path'])]=x['sha256']
 deps=read(A/'dependencies-final.json')
 for p,v in deps['files'].items(): pins[str(C/p)]=v['sha256']
 for x in read(A/'build-inputs-final.json')['files']:
  target=derived if Path(x['path']).is_relative_to(C/'out') else pins
  target[x['path']]=x['sha256']
 for f in ['source-manifest-v1.json','evidence/fullcore-build-support.json','dependencies-final.json','build-inputs-final.json','candidate.patch']:
  pins[str(A/f)]=sha(A/f)
 for p in [Path(__file__),Path('/usr/bin/make'),Path('/usr/bin/python3'),Path('/usr/bin/git'),Path('/usr/bin/bash'),Path('/usr/bin/perl'),Path('/usr/bin/ld'),Path('/usr/bin/ar')]: pins[str(p)]=sha(p)
 # Actual Verilator support sources, compiler builtin/system headers and startup objects.
 for directory in ['/usr/local/share/verilator/include','/usr/lib/llvm-19/lib/clang/19/include','/usr/include','/usr/lib/gcc/x86_64-linux-gnu/11/include']:
  req(Path(directory).is_dir(),'missing compiler input directory '+directory)
  for q in sorted(Path(directory).rglob('*')):
   if q.is_file(): pins[str(q)]=sha(q)
 for pattern in ['crt*.o','libc.so','libstdc++.so*']:
  for q in Path('/usr/lib/x86_64-linux-gnu').glob(pattern):
   if q.is_file(): pins[str(q)]=sha(q)
 for q in [C/'.git/HEAD',C/'.git/config',C/'.git/shallow',C/'.git/objects/info/alternates']:
  if q.is_file(): pins[str(q)]=sha(q)
 for q in (C/'.git/refs').rglob('*'):
  if q.is_file(): pins[str(q)]=sha(q)
 modules=[]
 for m in deps['modules']:
  head=subprocess.check_output(['git','-C',str(C/m['path']),'rev-parse','HEAD']).decode().strip()
  req(head==m['commit'],'dependency HEAD '+m['path']); modules.append({'path':m['path'],'head':head})
 save(O/'MODULE_HEADS_BEFORE.json',modules)
 protected={str(R/'build/emu'):'2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8'}
 for f in ['src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala','src/main/scala/xiangshan/backend/fu/wrapper/VDotO2.scala']: protected[str(R/f)]=sha(R/f)
 verify(pins); verify(derived); verify(protected)
 env,cmd=configuration()
 lock={'schema':'sp1-c-explicit-build-v1','frozen_at':now(),'candidate':str(C),'cwd':str(C),'cpu_affinity':[4,5],
 'command':cmd,'environment':env,'immutable_pins':pins,'protected':protected,'derived_cache_before':derived,
 'note':'Derived C/out metadata may change in build; immutable inputs and protected baseline must not. Build preparation is outside target 7200 second campaign. No target executed.'}
 save(O/'FREEZE.json',lock)
 save(O/'ROOT_BEFORE.json',{'head':git('rev-parse','HEAD').strip(),'branch':git('branch','--show-current').strip(),'tracked_status':git('status','--short','--untracked-files=no')})
 print('BUILD_INPUT_FREEZE_PASS',len(pins),len(derived),sha(O/'FREEZE.json'),flush=True)

def run():
 lock=read(O/'FREEZE.json'); req(not (O/'STATE.json').exists(),'build already attempted'); req(not (C/'build').exists(),'build directory exists')
 verify(lock['immutable_pins']); verify(lock['protected'])
 state={'status':'BUILDING','started_utc':now(),'supervisor_pid':os.getpid(),'freeze_sha256':sha(O/'FREEZE.json'),'target_processes':0}
 save(O/'STATE.json',state); child=None
 try:
  def child_setup(): os.setsid(); os.sched_setaffinity(0,set(lock['cpu_affinity']))
  with (O/'stdout.log').open('xb') as out,(O/'stderr.log').open('xb') as err:
   child=subprocess.Popen(lock['command'],cwd=C,env=lock['environment'],stdout=out,stderr=err,preexec_fn=child_setup)
   state.update(child_pid=child.pid,child_starttime=Path('/proc/%d/stat'%child.pid).read_text().split()[21]); save(O/'STATE.json',state)
   rc=child.wait()
  state.update(returncode=rc,build_ended_utc=now(),cleanup=cleanup(child.pid)); save(O/'STATE.json',state)
  req(not state['cleanup']['remaining'],'build process group not empty')
  req(rc==0,'build command failed; no automatic retry')
  verify(lock['immutable_pins']); verify(lock['protected'])
  for m in read(O/'MODULE_HEADS_BEFORE.json'):
   req(subprocess.check_output(['git','-C',str(C/m['path']),'rev-parse','HEAD']).decode().strip()==m['head'],'dependency HEAD changed')
  emu=C/'build/emu'; req(emu.is_file(),'missing new EMU')
  generated=[]
  for p in sorted((C/'build').rglob('*')):
   if p.is_file() and 'emu-compile' not in p.parts:
    generated.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
  save(O/'GENERATED.json',generated)
  ldd=subprocess.run(['/usr/bin/ldd',str(emu)],text=True,capture_output=True); (O/'ldd.txt').write_text(ldd.stdout+ldd.stderr); req(ldd.returncode==0,'ldd failed')
  libs={}
  for line in ldd.stdout.splitlines():
   for part in line.split():
    if part.startswith('/') and Path(part).is_file(): libs[part]=sha(part)
  save(O/'RUNTIME.json',{'emu':{'path':str(emu),'bytes':emu.stat().st_size,'sha256':sha(emu)},'libraries':libs,'generated_manifest_sha256':sha(O/'GENERATED.json')})
  state.update(status='SP1_C_BUILD_PASS',finished_utc=now(),emu_sha256=sha(emu),generated_files=len(generated)); save(O/'STATE.json',state)
  print(state['status'],sha(emu),flush=True)
 except BaseException as e:
  if child is not None:
   state['cleanup_on_error']=cleanup(child.pid)
   try: child.wait(10)
   except subprocess.TimeoutExpired: state['cleanup_wait_timeout']=True
  state.update(status='FAILED',error=repr(e),finished_utc=now()); save(O/'STATE.json',state); raise

if __name__=='__main__':
 O.mkdir(parents=True,exist_ok=True)
 {'freeze':freeze,'run':run}[sys.argv[1]]()
