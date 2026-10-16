import subprocess,json,os,time,hashlib
from pathlib import Path
origin=Path('/mnt/c/Code/RVInno/riscv')
root=Path('/home/amesotten/.cache/codex-rvinno/integration-t13-20261016')
old=Path('/home/amesotten/.cache/codex-rvinno/integration-20261015')
output=Path('/mnt/c/Code/RVInno/integration-james-t13-20261016/team/out/t13-integration-20261016')
records=[]
def run(name,cmd,cwd=None,expected=0):
 start=time.monotonic()
 with (output/(name+'.log')).open('wb') as f:
  p=subprocess.run(list(map(str,cmd)),cwd=cwd or root,stdout=f,stderr=subprocess.STDOUT)
 row=dict(name=name,argv=list(map(str,cmd)),cwd=str(cwd or root),exit_code=p.returncode,expected_exit_code=expected,seconds=round(time.monotonic()-start,3))
 records.append(row);(output/'runs.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode!=expected:raise RuntimeError(name+' failed')
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
run('clone',['git','clone','--shared','--no-checkout',origin,root],cwd=origin)
run('checkout',['git','checkout','--detach','46b6715da'])
modules={}
def children(repo,rel=Path()):
 for rec in git(repo,'ls-tree','-r','-z','HEAD').split(b'\0'):
  if not rec:continue
  meta,path=rec.split(b'\t');mode,kind,sha=meta.decode().split()
  if mode!='160000':continue
  name=rel/path.decode();target=root/name;src=old/name
  target.parent.mkdir(parents=True,exist_ok=True)
  subprocess.run(['git','clone','--shared','--no-checkout',str(src),str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  subprocess.run(['git','-C',str(target),'checkout','--detach',sha],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  modules[str(name)]=sha;children(target,name)
children(root)
(output/'modules.json').write_text(json.dumps(modules,indent=2)+'\n');print('modules',len(modules),flush=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
run('host-tests',['python3','-B','-m','unittest','discover','-s','team/tests','-p','test_*.py'])
run('model-tests',['python3','-B','-m','unittest','discover','-s','team/models/vdot/tests','-p','test_*.py'])
for opt in ('0','1','2'):
 os.environ['PYTHONOPTIMIZE']=opt
 run('t13-tests-opt'+opt,['python3','-B','-m','unittest','discover','-s','team/workloads/vdot-perf','-p','test_*.py'])
os.environ['PYTHONOPTIMIZE']='2'
run('host-judge-opt2',['python3','-B','team/workloads/vdot-perf/host_judge.py','--output',root/'team/out/t13-host-judge'])
run('archive-replay-opt2',['python3','-B','team/workloads/vdot-perf/verify_archive.py','--archive','team/evidence/t13-performance-20261015','--output',root/'team/out/t13-replay'])
os.environ['PYTHONOPTIMIZE']='0'
run('fresh-stream-build',['python3','-B','team/workloads/vdot-perf/campaign.py','build','--output',root/'team/out/t13-fresh-stream','--am','/home/amesotten/.cache/codex-t05/nexus-am-086a238','--stream-only'])
# Check actual newly compiled ABI/kernel data, not only a mocked build fixture.
run('fresh-elf-verification',['python3','-B','-c',"import sys,json;from pathlib import Path;sys.path.insert(0,'team/workloads/vdot-perf');import check as c;root=Path('team/out/t13-fresh-stream');images=json.loads((root/'images.json').read_text())['images'];[(c.verify_build_record(Path(x['path'])),c.check_compiled_cases(Path(x['path'])/'vdot-perf.elf',json.loads((Path(x['path'])/'data/manifest.json').read_text()))) for x in images];print('FRESH_BUILD_ELF_PASS images='+str(len(images)))"])
mill='/home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3'
os.environ.update(JAVA_OPTS='-Xmx3g -Xss8m -XX:ActiveProcessorCount=2',JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2',COURSIER_REPOSITORIES='https://repo.maven.apache.org/maven2',CHISEL_FIRTOOL_PATH='/home/amesotten/.cache/llvm-firtool/1.62.1/bin')
run('scala-compile',['bash',mill,'-i','-j','2','xiangshan.compile'])
paths=git(root,'ls-files','-z').decode().split('\0')
selected=[p for p in paths if p.startswith(('src/','team/scripts/','team/tests/','team/workloads/vdot-perf/')) or p in ('build.sc','.gitmodules')]
binding={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in selected if (root/p).is_file()}
(output/'source-binding.json').write_text(json.dumps(dict(source=git(root,'rev-parse','HEAD').decode().strip(),files=binding,status=git(root,'status','--porcelain','--untracked-files=no').decode()),indent=2)+'\n')
print('T13_INTEGRATION_VALIDATION_COMPLETE',flush=True)
