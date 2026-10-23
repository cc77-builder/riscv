from pathlib import Path
import subprocess,json,hashlib,sys,time
base=Path('/home/amesotten/.cache/codex-rvinno/merge-reg-20261023')
source=Path('/mnt/c/Code/RVInno/riscv');donor=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021/repo')
revision='bc9e5ae46'
revision=subprocess.check_output(['git','-C',str(source),'rev-parse',revision],text=True).strip()
base.mkdir(exist_ok=False);root=base/'repo';logs=(base/'prepare.log').open('xb')
def run(cmd):subprocess.run(list(map(str,cmd)),stdout=logs,stderr=subprocess.STDOUT,check=True)
def git(p,*a):return subprocess.check_output(['git','-C',str(p),*a],text=True)
run(['git','clone','--shared','--no-checkout','-c','core.autocrlf=false',source,root]);run(['git','-C',root,'checkout','--detach',revision])
modules={}
def restore(parent,old,prefix=''):
 if not (parent/'.gitmodules').exists():return
 for line in git(parent,'config','-f','.gitmodules','--get-regexp','path').splitlines():
  name=line.split(None,1)[1];pin=git(parent,'ls-tree','HEAD',name).split()[2]
  run(['git','clone','--shared','--no-checkout','-c','core.autocrlf=false',old/name,parent/name])
  run(['git','-C',parent/name,'checkout','--detach',pin]);modules[prefix+name]=pin
  restore(parent/name,old/name,prefix+name+'/')
 run(['git','-C',parent,'submodule','init'])
restore(root,donor)
sys.path.insert(0,str(root/'team/optimizations/o1'));import build_inputs
build_inputs.verify_dependencies(root);files=build_inputs.hardware_files(root)
if any(b'\r\n' in (root/p).read_bytes() for p in files):raise ValueError('non-LF hardware input')
if git(root,'status','--porcelain'):raise ValueError('dirty checkout')
old=donor.parent
env=json.loads((old/'native-environment.json').read_text());env['PATH']=str(old/'tools')+':/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
(base/'native-environment.json').write_text(json.dumps(env,indent=2)+'\n')
(base/'preparation.json').write_text(json.dumps(dict(status='LINUX_LF_CURRENT_SOURCE_READY',revision=revision,modules=modules,hardware_files=files,source=str(source),donor=str(donor),prepared=time.time(),old_inputs_modified=False),indent=2)+'\n')
print('LINUX_LF_CURRENT_SOURCE_READY',revision,len(modules),len(files),flush=True)
