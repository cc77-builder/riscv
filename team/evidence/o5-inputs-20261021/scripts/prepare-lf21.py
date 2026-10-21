from pathlib import Path
import subprocess,json,hashlib,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
source=Path('/mnt/c/Code/RVInno/riscv')
target=base/'repo'
base.mkdir(exist_ok=False)
def run(cmd):
    subprocess.run([str(x) for x in cmd],check=True)
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True)
rev=git(source,'rev-parse','HEAD').strip()
run(['git','clone','--shared','--no-checkout','-c','core.autocrlf=false',source,target])
run(['git','-C',target,'checkout','--detach',rev])
donor=Path('/home/amesotten/.cache/codex-rvinno/sync20/source-d13def17dc8de4b8')
modules={}
def restore(parent,donor_parent,prefix=''):
    if not (parent/'.gitmodules').exists():return
    for line in git(parent,'config','-f','.gitmodules','--get-regexp','path').splitlines():
        name=line.split(None,1)[1]
        item=git(parent,'ls-tree','HEAD',name).split()
        pin=item[2]
        child=parent/name; donor_child=donor_parent/name
        run(['git','clone','--shared','--no-checkout','-c','core.autocrlf=false',donor_child,child])
        run(['git','-C',child,'checkout','--detach',pin])
        modules[prefix+name]=pin
        restore(child,donor_child,prefix+name+'/')
    run(['git','-C',parent,'submodule','init'])
restore(target,donor)
import sys
sys.path.insert(0,str(target/'team/optimizations/o1'))
import build_inputs
build_inputs.verify_dependencies(target)
status=git(target,'status','--porcelain=v1')
assert not status,status
files=build_inputs.hardware_files(target)
assert not any(b'\r\n' in (target/n).read_bytes() for n in files)
(base/'checkout.json').write_text(json.dumps(dict(source=str(source),revision=rev,target=str(target),modules=modules,hardware_files=files,git_status=status,lf_verified=True),indent=2)+'\n')
print('LINUX_LF_CHECKOUT_PASS',len(files),len(modules),flush=True)
