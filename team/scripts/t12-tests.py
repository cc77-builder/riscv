"""Historical trace-off VFEX4 profile (fcb16a8 / fixed EMU pins).
The integrated trace-enabled VFEX4 uses t12-regression.sh. Reproduce this
software profile in a separate worktree at its recorded source; never remove
the hardware guard to reuse its binary for a different production tree.
Offline, finite T12 build/run driver, adapted from the preserved intake driver.
Reuses the accepted EMU and reference; requires committed source and fresh paths.
"""
import argparse,datetime,gzip,hashlib,importlib.util,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PARENT='6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3'
HARDWARE='fcb16a8764d342339670df0bbf1bc67ef2028b86'
AM='086a238062fdfb3281b745a537b361983d0154b5'
SOURCES=('team/workloads/t12-perf/main.c','team/workloads/t12-perf/Makefile','team/workloads/t12-perf/sites.S',
 'team/workloads/vdot-exceptions/harness.S','team/workloads/vdot-exceptions/harness.h','team/workloads/vdot-exceptions/layout.h','team/workloads/vdot-exceptions/judge.c',
 'team/tests/generate_t12.py','team/scripts/t12-tests.py','team/scripts/check_t12_compact.py','team/scripts/artifact_guard.py')
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('t12_guard','team/scripts/artifact_guard.py');checker=module('t12_checker','team/scripts/check_t12_compact.py')
def now():return datetime.datetime.now().astimezone().isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def require(v,m):
 if not v:raise ValueError(m)
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.PIPE,text=True).strip()
def source(rev):
 require(git('rev-parse','HEAD')==rev,'HEAD differs from fixed implementation SHA')
 require(not git('status','--porcelain=v1','--untracked-files=all'),'committed clean source required')
 subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',PARENT,rev],check=True)
 require(not git('diff',HARDWARE,rev,'--','src','build.sc'),'production differs from accepted hardware')
 return {n:sha(ROOT/n) for n in SOURCES}
def child(cmd,log,timeout=300,cwd=ROOT):
 log=Path(log);m=dict(argv=list(map(str,cmd)),cwd=str(cwd),started_at=now(),timeout_seconds=timeout);start=time.monotonic()
 with log.open('wb') as f:
  p=subprocess.Popen(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);m['pid']=p.pid;write(log.with_suffix('.process.json'),m)
  try:rc=p.wait(timeout=timeout);m['timed_out']=False
  except subprocess.TimeoutExpired:
   m['timed_out']=True;os.killpg(p.pid,signal.SIGTERM)
   try:rc=p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
  except BaseException:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   raise
 m.update(exit_code=rc,finished_at=now(),elapsed_host_seconds=time.monotonic()-start);write(log.with_suffix('.process.json'),m)
 return m
def success(m):require(m['exit_code']==0 and not m['timed_out'],'child failed: '+str(m))
def fresh(path):path=path.resolve();path.mkdir(parents=True,exist_ok=False);return path

def build(a):
 sources=source(a.expected_source);out=fresh(a.output);am=a.am.resolve()
 g.audit_repo(am,AM,source_roots=('am/src','am/include','libs/klib/src','libs/klib/include'))
 os.environ.update(AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1')
 if a.toolchain:
  tool=a.toolchain.resolve();os.environ['PATH']=str(tool/'usr/bin')+':'+os.environ['PATH'];os.environ['LD_LIBRARY_PATH']=str(tool/'usr/lib/x86_64-linux-gnu')
 toolinfo={}
 import shutil
 for name in ('gcc','as','ld','ar','objcopy','objdump'):
  path=Path(shutil.which('riscv64-linux-gnu-'+name) or '/nonexistent')
  toolinfo[name]=dict(path=str(path),resolved=str(path.resolve()),sha256=sha(path),version=subprocess.check_output([str(path),'--version'],text=True).splitlines()[0])
 # Record the portable loader libraries and GCC backend actually resolved.
 gcc=toolinfo['gcc']['path']
 for name in ('cc1','libgcc.a'):
  path=Path(subprocess.check_output([gcc,'-print-file-name='+name],text=True).strip()).resolve()
  if path.is_file():toolinfo[name]=dict(path=str(path),sha256=sha(path))
 if a.toolchain:
  for path in sorted((a.toolchain/'usr/lib/x86_64-linux-gnu').glob('*.so*')):
   if path.is_file():toolinfo[str(path)]=dict(sha256=sha(path))
 write(out/'tools.json',toolinfo)
 generate_cmd=[sys.executable,'-B',str(ROOT/'team/tests/generate_t12.py'),'--output',str(out/'data'),'--baseline',a.baseline]
 if a.include_chain:generate_cmd+=['--include-chain']
 success(child(generate_cmd,out/'generate.log'))
 m,rows=checker.load(out/'data');limit=a.count if a.count is not None else len(m['schedule'])-a.start
 require(0<=a.start<len(m['schedule']) and 0<limit<=len(m['schedule'])-a.start,'invalid exact slice')
 cmd=['make','-C',str(ROOT/'team/workloads/t12-perf'),'ARCH=riscv64-xs','MARCH=rv64gcv',f'T12_START={a.start}',f'T12_COUNT={limit}',
  'T12_DATA='+str(out/'data'),'VDOT_OBJ_ROOT='+str(out/'obj'),'BINARY='+str(out/'test'),'-j1']
 if a.diagnose:cmd+=['CPPFLAGS=-DT12_DIAG=1']
 buildprocess=child(cmd,out/'build.log');success(buildprocess)
 require(source(a.expected_source)==sources,'source changed during build')
 def sums(name,paths):(out/name).write_text(''.join(sha(p)+'  '+str(p)+'\n' for p in paths))
 sums('source.sha256',[ROOT/n for n in SOURCES]);sums('inputs.sha256',sorted((out/'data').iterdir()));sums('workload.sha256',[out/'test.bin',out/'test.elf'])
 g.capture_build(out,out/'data','t12','riscv64-xs','full',am)
 write(out/'build.json',dict(source=a.expected_source,sources=sources,start=a.start,limit=limit,image_sha256=sha(out/'test.bin'),elf_sha256=sha(out/'test.elf'),manifest_sha256=sha(out/'data/manifest.json'),tools_sha256=sha(out/'tools.json'),process=buildprocess))
 print('T12_BUILD_DONE '+str(out),flush=True)

def run(a):
 sources=source(a.expected_source);build=a.build.resolve();b=json.loads((build/'build.json').read_text())
 require(b['source']==a.expected_source and b['sources']==sources,'source/binary mismatch')
 g.verify_build(build,build/'test.bin',build/'data','t12','full')
 require(sha(build/'test.bin')==b['image_sha256'] and sha(build/'data/manifest.json')==b['manifest_sha256'],'build image/data changed')
 out=fresh(a.output)
 assets={k:getattr(a,k).resolve() for k in ('emu','reference','flash')}
 pins={k:sha(v) for k,v in assets.items()};require(pins==checker.PINS,'accepted runtime pins mismatch')
 write(out/'reference-verification.json',g.verify_nemu(a.nemu.resolve(),assets['reference'],'reference'))
 write(out/'reuse.json',dict(hardware_source=HARDWARE,production_diff='',production_rebuilt=False,assets={k:dict(path=str(v),sha256=pins[k]) for k,v in assets.items()}))
 cmd=[str(assets['emu']),'-i',str(build/'test.bin'),'--flash',str(assets['flash']),'--ram-size=128MB','--diff',str(assets['reference']),'-C',str(a.cycles),'--no-snapshot']
 process=child(cmd,out/'run.log',timeout=a.timeout,cwd=out)
 receipt=dict(source=a.expected_source,start=b['start'],limit=b['limit'],build=str(build),build_sha256=sha(build/'build.json'),image_sha256=b['image_sha256'],manifest_sha256=b['manifest_sha256'],runtime_pins=pins,difftest=True,ram='128MB',completed=not process['timed_out'],run_log_sha256=sha(out/'run.log'),**process)
 write(out/'receipt.json',receipt)
 with (out/'run.log').open('rb') as src,(out/'run.log.gz').open('wb') as dst:
  with gzip.GzipFile(fileobj=dst,mode='wb',mtime=0,filename='') as z:
   while chunk:=src.read(1024*1024):z.write(chunk)
 require(source(a.expected_source)==sources,'source changed during run')
 g.verify_build(build,build/'test.bin',build/'data','t12','full')
 checker.bind(receipt,build/'data',a.expected_source)
 result=checker.check((out/'run.log').read_text(),build/'data',b['start'],b['limit'],process['exit_code'])
 write(out/'checked.json',result);print(json.dumps({k:result[k] for k in ('status','start','limit','executed')}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('build','run'));p.add_argument('--expected-source',required=True);p.add_argument('--output',type=Path,required=True)
 for name in ('am','toolchain','build','emu','nemu','reference','flash'):p.add_argument('--'+name,type=Path)
 p.add_argument('--baseline',choices=('original','lean'),default='original');p.add_argument('--include-chain',action='store_true')
 p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int);p.add_argument('--diagnose',action='store_true');p.add_argument('--cycles',type=int,default=2000000);p.add_argument('--timeout',type=int,default=1200)
 a=p.parse_args()
 try:
  for name in (('am',) if a.action=='build' else ('build','emu','nemu','reference','flash')):require(getattr(a,name) is not None,'missing --'+name)
  build(a) if a.action=='build' else run(a)
 except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as e:raise SystemExit('T12_REJECTED: '+str(e))
