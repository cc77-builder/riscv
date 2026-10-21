"""Independent current-build identity audit; does not change frozen build tools."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shlex,subprocess,sys
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo'
build=base/'build-04';pins=json.loads((build/'hardware-inputs-before.json').read_text())
state=json.loads((build/'build-state.json').read_text());contract=pins['native_build_contract']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
revision='f44d8b1ba73d8f210f55e0818cec05a2681c3481'
if pins['source_commit']!=revision or state['source_commit']!=revision:raise ValueError('wrong build04 source revision')
tools={}
for name,expected in pins['build_tools'].items():
    blob=subprocess.check_output(['git','show',revision+':'+name],cwd=root)
    gitsha=hashlib.sha256(blob).hexdigest();actual=sha(root/name)
    if expected!=gitsha or expected!=actual:raise ValueError('build tool differs from committed source: '+name)
    tools[name]=dict(recorded_sha256=expected,git_sha256=gitsha,current_sha256=actual)
sys.path.insert(0,str(root/'team/optimizations/o1'));import build_recipe,split_recipe
native_env=json.loads((base/'native-environment.json').read_text())
os.environ.clear();os.environ.update(native_env)
clean=build_recipe.environment()
envsha=hashlib.sha256(json.dumps(clean,sort_keys=True).encode()).hexdigest()
if envsha!=contract['environment_sha256']:raise ValueError('native bootstrap environment differs')
command='source team/scripts/activate.sh\nexport '+shlex.join([key+'='+value for key,value in state['flags'].items()])+'\n'
command+='export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"\n'
command+='python3 -c '+shlex.quote('import os,json; print(json.dumps(dict(os.environ)))')
activated=json.loads(subprocess.check_output(['bash','-c',command],cwd=root,env=clean,text=True))
running=[]
for process in Path('/proc').glob('[0-9]*'):
    try:
        args=(process/'cmdline').read_bytes().split(b'\0')
        if str(root/'team/optimizations/o1/split_recipe.py').encode() in args:
            actual=dict(value.split('=',1) for value in (process/'environ').read_bytes().decode().split('\0') if value)
            running.append((process.name,actual))
    except (FileNotFoundError,PermissionError,ProcessLookupError):pass
if len(running)!=1:raise ValueError('expected one actual running split executor, found '+str(len(running)))
pid,actual=running[0]
os.environ.clear();os.environ.update(activated);expected_runtime=split_recipe.environment(pins)
os.environ.clear();os.environ.update(actual);actual_runtime=split_recipe.environment(pins)
if expected_runtime!=actual_runtime:raise ValueError('actual split environment differs from restricted launch')
python=Path(subprocess.check_output(['bash','-c','command -v python3'],cwd=root,env=actual_runtime,text=True).strip()).resolve()
selected=contract['compilers']['python']
if str(python)!=selected['path'] or sha(python)!=selected['sha256']:raise ValueError('PATH python differs from bound interpreter')
report=dict(status='BUILD04_EXTERNAL_IDENTITY_AUDIT_PASS',created=datetime.now(timezone.utc).isoformat(),
    source_commit=revision,actual_split_pid=int(pid),build_tools=tools,bootstrap_environment_sha256=envsha,
    actual_runtime_environment_sha256=hashlib.sha256(json.dumps(actual_runtime,sort_keys=True).encode()).hexdigest(),
    compared_environment_keys=sorted(actual_runtime),python=dict(path=str(python),sha256=sha(python)),
    pins_sha256=sha(build/'hardware-inputs-before.json'),auditor_sha256=sha(__file__),
    scope='Independent read-only audit of this running f44 build; f44 does not contain the later generic Git/PATH prelaunch gates',
    hardware_build_completed=False,new_emu_run=False)
with (base/'build04-external-identity-audit-02.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
print(report['status'],revision,'pid',pid)
