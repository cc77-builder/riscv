import hashlib,json,os,subprocess,time
from pathlib import Path
source=Path('/home/amesotten/.cache/codex-rvinno/integration-t13-20261016')
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
output=Path('/mnt/c/Code/RVInno/riscv/team/out/james-fullcore-20261016')
cache.mkdir(exist_ok=False)
pack=cache/'source-pack'
records=[]
def run(name,cmd,cwd=source,env=None):
    started=time.time()
    record=dict(name=name,argv=[str(x) for x in cmd],cwd=str(cwd),started=started,status='RUNNING')
    records.append(record)
    (output/'build-progress.json').write_text(json.dumps(records,indent=2)+'\n')
    with (output/(name+'.log')).open('wb') as f:
        result=subprocess.run(record['argv'],cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
    record.update(status='FINISHED',exit_code=result.returncode,seconds=round(time.time()-started,3))
    (output/'build-progress.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode:raise RuntimeError(name)
run('checkout',['git','checkout','--detach','d3706f0b86ecfdfbb24cb34cbcf2c18a0314f7f9'])
modules=json.loads((output.parent/'t13-unused.json').read_text()) if False else json.loads((source/'team/evidence/james-t13-integration-20261016/modules.json').read_text())
for repo in (source,*(source/n for n in modules)):
    if (repo/'.gitmodules').exists():
        subprocess.run(['git','submodule','init'],cwd=repo,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
run('source-pack',['python3','-B','team/scripts/prepare-core-baseline.py','pack','--source',source,'--pack',pack])
run('materialize',['python3','-B','team/scripts/prepare-core-baseline.py','materialize','--source',source,'--pack',pack,'--cache',cache])
target=Path((pack/'build-copy.txt').read_text().strip())
(output/'build-copy.txt').write_text(str(target)+'\n')
run('dependencies',['python3','-B','team/scripts/audit-core-dependencies.py','--target',target,'--evidence',cache/'hardware'],cwd=target)
wrapper=cache/'mill'
wrapper.write_text('#!/bin/bash\nexec bash /home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3 "$@"\n')
wrapper.chmod(0o755)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',VDOT_T12_TRACE='1',VDOT_T13_TRACE='1',
    TEAM_EVIDENCE_DIR=str(cache/'hardware'),CORE_SOURCE_PACK=str(pack),CORE_MILL=str(wrapper),
    CORE_FIRTOOL='/home/amesotten/.cache/llvm-firtool/1.62.1/bin/firtool',
    JAVA_OPTS='-Xmx1g -XX:ActiveProcessorCount=2',JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2',
    COURSIER_REPOSITORIES='https://repo.maven.apache.org/maven2',
    CHISEL_FIRTOOL_PATH='/home/amesotten/.cache/llvm-firtool/1.62.1/bin',
    NEMU_HOME='/home/amesotten/.cache/codex-rvinno/t08/delivered/reference',
    AM_HOME='/home/amesotten/.cache/codex-t05/nexus-am-086a238',
    CORE_OPT_FAST='-O3',CORE_COMPILE_JOBS='2')
(output/'build-environment.json').write_text(json.dumps({k:v for k,v in env.items() if k not in os.environ or os.environ.get(k)!=v},indent=2)+'\n')
run('core-split-build',['bash','team/scripts/core-baseline-split.sh'],cwd=target,env=env)
run('source-after',['python3','-B','team/scripts/prepare-core-baseline.py','verify','--source',source,'--pack',pack,'--target',target],cwd=target)
run('dependencies-after',['python3','-B','team/scripts/audit-core-dependencies.py','--target',target,'--evidence',cache/'hardware-after'],cwd=target)
print('CURRENT_FULLCORE_BUILD_FINISHED',flush=True)
