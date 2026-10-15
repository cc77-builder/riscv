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
mill='/home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3'
os.environ.update(JAVA_OPTS='-Xmx3g -Xss8m -XX:ActiveProcessorCount=2',JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2',COURSIER_REPOSITORIES='https://repo.maven.apache.org/maven2',CHISEL_FIRTOOL_PATH='/home/amesotten/.cache/llvm-firtool/1.62.1/bin')
run('fu-invalid-vlen',['bash',mill,'-i','-j','2','vdotFu.runMain','team.vdot.GenerateVDotFu',work/'invalid-vlen','--invalid-vlen'],expected=1)
assert 'VDot requires VLEN=128' in (output/'fu-invalid-vlen.log').read_text()
for name,marker in [('datapath-inject-bit-0','VDOT_DATAPATH_MISMATCH'),('datapath-inject-bit-127','VDOT_DATAPATH_MISMATCH'),('fu-inject-identity','VDOT_FU_FAIL case='),('fu-inject-cancel-leak','VDOT_FU_FAIL case=')]:
 if marker not in (output/(name+'.log')).read_text():raise RuntimeError('negative control failed for wrong reason')
os.environ['VDOT_T12_TRACE']='1'
out=work/'fu-trace';out.mkdir()
run('fu-trace-elaborate',['bash',mill,'-i','-j','2','vdotFu.runMain','team.vdot.GenerateVDotFu',out/'rtl'])
rtl=out/'rtl/VDotFuTestTop.sv'
run('fu-trace-lint',['verilator','--lint-only','--assert','--top-module','VDotFuTestTop',rtl])
run('fu-trace-build',['verilator','--cc','--exe','--build','--assert','--top-module','VDotFuTestTop','--Mdir',out/'obj_dir','-j','2','-CFLAGS','-std=c++17 -O2',rtl,root/'team/rtl/vdot/fu_test.cpp'])
run('fu-trace-simulation',[out/'obj_dir/VVDotFuTestTop',work/'vectors.tsv'])
# Save exact input/generated RTL hashes, dependency commits and clean production tree status.
paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
selected=[p for p in paths if p.startswith(('src/','team/scripts/','team/tests/','team/rtl/','team/models/','team/workloads/')) or p in ('build.sc','.gitmodules')]
binding={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in selected if (root/p).is_file()}
rtl_binding={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob('*.sv')}
(output/'validation-source.json').write_text(json.dumps(dict(source=git(root,'rev-parse','HEAD').decode().strip(),files=binding,rtl=rtl_binding,status=git(root,'status','--porcelain','--untracked-files=no').decode()),indent=2)+'\n')
print('SUPPLEMENT_COMPLETE',flush=True)
