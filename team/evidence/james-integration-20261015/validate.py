import subprocess,json,os,time,hashlib
from pathlib import Path
origin=Path('/mnt/c/Code/RVInno/riscv')
root=Path('/home/amesotten/.cache/codex-rvinno/integration-20261015')
old=Path('/home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9')
output=Path('/mnt/c/Code/RVInno/integration-james-20261015/team/out/integration-20261015')
records=[]
def run(name,cmd,cwd=None,expected=0):
 start=time.monotonic()
 with (output/(name+'.log')).open('wb') as f:
  p=subprocess.run(list(map(str,cmd)),cwd=cwd or root,stdout=f,stderr=subprocess.STDOUT)
 row=dict(name=name,argv=list(map(str,cmd)),cwd=str(cwd or root),exit_code=p.returncode,expected_exit_code=expected,seconds=round(time.monotonic()-start,3))
 records.append(row);(output/'runs.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode!=expected: raise RuntimeError(name+' failed; see log')
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
run('clone',['git','clone','--shared','--no-checkout',origin,root],cwd=origin)
run('checkout',['git','checkout','--detach','e5df93c7b'],cwd=root)
(root/'.git').joinpath('config').write_text((root/'.git/config').read_text()+'\n[core]\n\tautocrlf = false\n')
# Clone all pinned dependency repositories locally without downloads or edits to the old source copy.
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
(output/'modules.json').write_text(json.dumps(modules,indent=2)+'\n');print('dependencies',len(modules),flush=True)
os.environ['PYTHONDONTWRITEBYTECODE']='1'
run('host-tests',['python3','-B','-m','unittest','discover','-s','team/tests','-p','test_*.py'])
run('independent-model-tests',['python3','-B','-m','unittest','discover','-s','team/models/vdot/tests','-p','test_*.py'])
run('source-and-oracles',['python3','-B','team/scripts/check-vdot-integration-source.py'])
run('archive-recheck',['python3','-B','team/scripts/check-t12-archive.py','team/evidence/t12-regression-20261014','--expected-source','117ecbf40e107872e046311f556cc4fdf3f733d7','--expected-emu','e879356c4f3ad027a708de3adbabb7285ab6e36196426854040460d1e394b4de','--expected-reference','efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4','--expected-flash','a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994'])
work=root/'team/out/integration';work.mkdir(parents=True)
for test in ('exception','t12'):
 for suffix,flags in [('normal',[]),('ubsan',['-fsanitize=undefined','-fno-sanitize-recover=all'])]:
  name=test+'-judge-'+suffix;exe=work/name
  run(name+'-build',['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',*flags,'-Iteam/workloads/vdot-exceptions','team/tests/test_'+test+'_judge.c','team/workloads/vdot-exceptions/judge.c','-o',exe])
  run(name,[exe])
# Use cached project tools; individual commands mirror the checked-in test entries.
mill='/home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3'
os.environ.update(JAVA_OPTS='-Xmx3g -Xss8m -XX:ActiveProcessorCount=2',JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2',COURSIER_REPOSITORIES='https://repo.maven.apache.org/maven2',CHISEL_FIRTOOL_PATH='/home/amesotten/.cache/llvm-firtool/1.62.1/bin')
for name,cmd in [('java-version',['java','-version']),('mill-version',[mill,'--version']),('verilator-version',['verilator','--version']),('gcc-version',['gcc','--version'])]:run(name,cmd)
run('prepare-vectors',['python3','-B','team/rtl/vdot/prepare_vectors.py','team/models/vdot/data',work/'vectors.tsv'])
for component,mod,emit,top,harness in [('datapath','vdotDatapath','GenerateVDot','VDotDatapath','datapath_test.cpp'),('fu','vdotFu','GenerateVDotFu','VDotFuTestTop','fu_test.cpp'),('decode','vdotDecode','GenerateVDotDecode','VDotDecodeTestTop','decode_test.cpp')]:
 out=work/component;out.mkdir()
 run(component+'-elaborate',[mill,'-i','-j','2',mod+'.runMain','team.vdot.'+emit,out/'rtl'])
 rtl=out/'rtl'/(top+'.sv')
 run(component+'-lint',['verilator','--lint-only','--assert','--top-module',top,rtl])
 run(component+'-build',['verilator','--cc','--exe','--build','--assert','--top-module',top,'--Mdir',out/'obj_dir','-j','2','-CFLAGS','-std=c++17 -O2',rtl,root/'team/rtl/vdot'/harness])
 exe=out/'obj_dir'/('V'+top);args=[exe] if component=='decode' else [exe,work/'vectors.tsv']
 run(component+'-simulation',args)
 for fault in (['bit=0','bit=127'] if component=='datapath' else ['identity','cancel-leak'] if component=='fu' else []):
  run(component+'-inject-'+fault.replace('=','-'),args+['--inject-'+fault],expected=1)
print('INTEGRATION_VALIDATION_COMPLETE',flush=True)
