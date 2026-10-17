"""Diagnostic workload: move Vidiv after VDot to avoid draining delayed F2v first."""
import datetime,hashlib,importlib.util,json,os,shutil,subprocess
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016');repo=Path('/mnt/c/Code/RVInno/riscv')
root=Path((repo/'team/out/james-fullcore-20261016/build-copy.txt').read_text().strip())
dest=cache/'workloads/control-pressure-v2';dest.mkdir(exist_ok=False);source=dest/'source'
names=['team/workloads/vdot-regression/'+n for n in ('generate.py','main.c','Makefile')]+['team/models/vdot/model.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
for n in names:
    target=source/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/n,target)
gen=source/names[0];text=gen.read_text();old='                    divide(16+(j%4),8,9)\n                    dot(10+(j%4),8,9)'
if text.count(old)!=1:raise ValueError('probe target drift')
gen.write_text(text.replace(old,'                    dot(10+(j%4),8,9)\n                    divide(16+(j%4),8,9)'))
save(dest/'source.json',dict(parent='d3706f0b86ecfdfbb24cb34cbcf2c18a0314f7f9',experiment='swap independent vdot/vidiv in group2 only',before={n:sha(root/n) for n in names},after={n:sha(source/n) for n in names}))
env=dict(os.environ,AM_HOME=str(cache/'nexus-am'),LINUX_GNU_TOOLCHAIN='1',PYTHONDONTWRITEBYTECODE='1')
commands=[['python3','-B',str(gen),'--output',str(dest/'data')],['make','-C',str(source/'team/workloads/vdot-regression'),'ARCH=riscv64-xs','MARCH=rv64gcv','T12_DATA='+str(dest/'data'),'T12_OBJ_ROOT='+str(dest/'objects'),'BINARY='+str(dest/'vdot-regression'),'-j1']]
for i,cmd in enumerate(commands):
    with (dest/f'build-{i}.log').open('wb') as log:p=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    save(dest/f'build-{i}.json',dict(command=cmd,exit_code=p.returncode))
    if p.returncode:raise RuntimeError('build failed')
folder=cache/'runs/control-pressure-v2';folder.mkdir(exist_ok=False)
emu=root/'build/emu';ref=cache/'nemu/reference/build/riscv64-nemu-interpreter-so';flash=cache/'workloads/boot-flash.bin';image=dest/'vdot-regression.bin'
cmd=['timeout','120m','stdbuf','-o0','-e0',str(emu),'-i',str(image),'--flash='+str(flash),'--ram-size=128MB','--diff='+str(ref),'--max-cycles=2000000']
record=dict(name='control',status='RUNNING',command=cmd,files={str(p):sha(p) for p in (emu,ref,flash,image)},started=datetime.datetime.now().astimezone().isoformat())
save(folder/'runtime.json',record)
with (folder/'stdout.log').open('wb') as o,(folder/'stderr.log').open('wb') as e:p=subprocess.run(cmd,cwd=root,env=env,stdout=o,stderr=e)
(folder/'run.log').write_bytes((folder/'stderr.log').read_bytes()+(folder/'stdout.log').read_bytes());(folder/'exit-code.txt').write_text(str(p.returncode)+'\n')
record.update(exit_code=p.returncode,finished=datetime.datetime.now().astimezone().isoformat(),raw_logs_sha256={n:sha(folder/n) for n in ('stdout.log','stderr.log')},log_format='separate-streams-v1; derived run.log = stderr.log + stdout.log')
try:
    if not all(sha(Path(n))==h for n,h in record['files'].items()):raise ValueError('artifact drift')
    spec=importlib.util.spec_from_file_location('checker',repo/'team/scripts/check-vdot-regression.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    result=m.check((folder/'run.log').read_text(),json.loads((dest/'data/manifest.json').read_text()),p.returncode)
    save(folder/'control-result.json',result);record['status']=result['status']
except Exception as error:record.update(status='FAILED',error=repr(error))
save(folder/'result.json',record);print(json.dumps(record),flush=True)
