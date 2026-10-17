"""Correct a missing DT_NEEDED in the test fixture; preserve the first attempt."""
import ctypes,datetime,hashlib,json,os,re,subprocess
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
out=Path('/mnt/c/Code/RVInno/riscv/team/out/james-fullcore-20261016')
root=Path((out/'build-copy.txt').read_text().strip());work=cache/'workloads'
ref=cache/'nemu/reference/build/riscv64-nemu-interpreter-so'
fixture=work/'negative-reference-v2.so';folder=cache/'runs/negative-vdot-retry';folder.mkdir(exist_ok=False)
def save(name,value):(folder/name).write_bytes((json.dumps(value,indent=2)+'\n').encode())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now().astimezone().isoformat()
cmd=['gcc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-DREF_SO="'+str(ref)+'"',str(root/'team/evidence/t12-regression-20261014/negative-fixture.c'),'-Wl,--no-as-needed',str(ref),'-ldl','-o',str(fixture)]
with (folder/'fixture-build.log').open('wb') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
save('fixture-build.json',dict(command=cmd,exit_code=p.returncode,reason='First fixture omitted original reference DT_NEEDED; do not treat load abort as successful injection.'))
if p.returncode:raise RuntimeError('fixture build')
env=dict(os.environ,XS_NEGATIVE_VECTOR_TARGET='vdot')
symbol_cmd=['python3','-c','import ctypes,sys; p=ctypes.CDLL(sys.argv[1]); names=["difftest_raise_intr","difftest_init","difftest_regcpy","difftest_exec","difftest_memcpy"]; [getattr(p,n) for n in names]; print("FIXTURE_SYMBOLS_PASS",names)',str(fixture)]
with (folder/'fixture-symbols.log').open('wb') as log:p=subprocess.run(symbol_cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
if p.returncode:raise RuntimeError('fixture symbols')
emu=root/'build/emu';image=work/'matrix/build-0/vdot-exceptions.bin';flash=work/'boot-flash.bin'
command=['timeout','120m','stdbuf','-o0','-e0',str(emu),'-i',str(image),'--flash='+str(flash),'--ram-size=128MB','--diff='+str(fixture),'--max-cycles=5000000']
record=dict(name='negative-vdot',status='RUNNING',started=now(),command=command,files={str(p):sha(p) for p in (emu,ref,fixture,flash,image)})
save('runtime.json',record)
with (folder/'stdout.log').open('wb') as o,(folder/'stderr.log').open('wb') as e:p=subprocess.run(command,cwd=root,env=env,stdout=o,stderr=e)
(folder/'run.log').write_bytes((folder/'stderr.log').read_bytes()+(folder/'stdout.log').read_bytes())
(folder/'exit-code.txt').write_text(str(p.returncode)+'\n')
record.update(exit_code=p.returncode,log_format='separate-streams-v1; derived run.log = stderr.log + stdout.log',raw_logs_sha256={n:sha(folder/n) for n in ('stdout.log','stderr.log')},finished=now())
try:
    text=(folder/'run.log').read_text()
    def require(ok,message):
        if not ok:raise ValueError(message)
    require(all(sha(p)==h for p,h in record['files'].items()),'runtime input changed')
    require('The first instruction of core 0 has commited. Difftest enabled.' in text,'missing live DiffTest')
    require('The reference model is '+str(fixture) in text,'wrong reference')
    inj=re.search(r'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=(\d+) pc=(0x[0-9a-f]+) instruction=(0x[0-9a-f]+)',text)
    require(inj is not None and p.returncode==1,'missing injection/wrong exit')
    mismatch=re.search(r'v'+inj[1]+r'_high different at pc = (0x[0-9a-fA-F]+), right=\s*(0x[0-9a-fA-F]+), wrong =\s*(0x[0-9a-fA-F]+)',text)
    require(mismatch is not None and int(inj[2],16)==int(mismatch[1],16),'wrong mismatch PC/register')
    require(int(mismatch[2],16)^int(mismatch[3],16)==1<<36,'wrong bit')
    require(int(inj[3],16)&0xfe00707f==0x0200000b,'wrong instruction')
    record.update(status='EXPECTED_VDOT_HIGHBIT_REJECTION',vd=int(inj[1]),pc=inj[2],word=inj[3])
except Exception as error:record.update(status='FAILED',error=repr(error))
save('result.json',record);print(record['status'],flush=True)
if record['status']=='FAILED':raise RuntimeError(record['error'])
