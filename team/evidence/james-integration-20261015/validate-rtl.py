import subprocess,json,os,time,hashlib
from pathlib import Path
origin=Path('/mnt/c/Code/RVInno/riscv')
root=Path('/home/amesotten/.cache/codex-rvinno/integration-20261015')
old=Path('/home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9')
output=Path('/mnt/c/Code/RVInno/integration-james-20261015/team/out/integration-20261015')
records=json.loads((output/'runs.json').read_text())
def run(name,cmd,cwd=None,expected=0):
 start=time.monotonic()
 with (output/(name+'.log')).open('wb') as f:
  p=subprocess.run(list(map(str,cmd)),cwd=cwd or root,stdout=f,stderr=subprocess.STDOUT)
 row=dict(name=name,argv=list(map(str,cmd)),cwd=str(cwd or root),exit_code=p.returncode,expected_exit_code=expected,seconds=round(time.monotonic()-start,3))
 records.append(row);(output/'runs.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode!=expected: raise RuntimeError(name+' failed; see log')
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
work=root/'team/out/integration'
# Use cached project tools; individual commands mirror the checked-in test entries.
mill='/home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3'
os.environ.update(JAVA_OPTS='-Xmx3g -Xss8m -XX:ActiveProcessorCount=2',JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2',COURSIER_REPOSITORIES='https://repo.maven.apache.org/maven2',CHISEL_FIRTOOL_PATH='/home/amesotten/.cache/llvm-firtool/1.62.1/bin')
for name,cmd in [('java-version',['java','-version']),('mill-version',['bash',mill,'--version']),('verilator-version',['verilator','--version']),('gcc-version',['gcc','--version'])]:run(name,cmd)
run('prepare-vectors',['python3','-B','team/rtl/vdot/prepare_vectors.py','team/models/vdot/data',work/'vectors.tsv'])
for component,mod,emit,top,harness in [('datapath','vdotDatapath','GenerateVDot','VDotDatapath','datapath_test.cpp'),('fu','vdotFu','GenerateVDotFu','VDotFuTestTop','fu_test.cpp'),('decode','vdotDecode','GenerateVDotDecode','VDotDecodeTestTop','decode_test.cpp')]:
 out=work/component;out.mkdir()
 run(component+'-elaborate',['bash',mill,'-i','-j','2',mod+'.runMain','team.vdot.'+emit,out/'rtl'])
 rtl=out/'rtl'/(top+'.sv')
 run(component+'-lint',['verilator','--lint-only','--assert','--top-module',top,rtl])
 run(component+'-build',['verilator','--cc','--exe','--build','--assert','--top-module',top,'--Mdir',out/'obj_dir','-j','2','-CFLAGS','-std=c++17 -O2',rtl,root/'team/rtl/vdot'/harness])
 exe=out/'obj_dir'/('V'+top);args=[exe] if component=='decode' else [exe,work/'vectors.tsv']
 run(component+'-simulation',args)
 for fault in (['bit=0','bit=127'] if component=='datapath' else ['identity','cancel-leak'] if component=='fu' else []):
  run(component+'-inject-'+fault.replace('=','-'),args+['--inject-'+fault],expected=1)
print('INTEGRATION_VALIDATION_COMPLETE',flush=True)
