"""Fresh input preparation; every subprocess and source artifact is retained."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
root=base/'repo'; assets=base/'inputs';assets.mkdir(exist_ok=False)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
am=assets/'nexus-am'; t12=assets/'t12'; t14=assets/'t14';dense=assets/'dense'
env={k:v for k,v in os.environ.items() if k in ('HOME','PATH')}
env.update(LANG='C.UTF-8',LC_ALL='C.UTF-8',TZ='UTC',PYTHONDONTWRITEBYTECODE='1',AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1',BUILD_JOBS='2',TEAM_XS_ENV_ROOT=str(assets/'xs-env'))
records=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
def run(name,cmd,extra=None,cwd=root):
    command=list(map(str,cmd));record=dict(name=name,command=command,cwd=str(cwd),started=time.time(),status='RUNNING',environment=env| (extra or {}))
    records.append(record);save(assets/'progress.json',records)
    with (assets/(name+'.log')).open('wb') as log:
        rc=subprocess.run(command,cwd=cwd,env=env | (extra or {}),stdout=log,stderr=subprocess.STDOUT).returncode
    record.update(exit_code=rc,finished=time.time(),status='PASS' if rc==0 else 'FAILED');save(assets/'progress.json',records)
    print(name,rc,flush=True)
    if rc:raise RuntimeError(name+' failed; keep original log')
    return command
run('am-clone',['git','clone','--shared','--no-checkout','/home/amesotten/.cache/codex-rvinno/fullcore-20261016/nexus-am',am])
run('am-checkout',['git','-C',am,'checkout','--detach','086a238062fdfb3281b745a537b361983d0154b5'])
(assets/'xs-env').mkdir();(assets/'xs-env/nexus-am').symlink_to(am,target_is_directory=True)
run('nemu-build',['bash','team/scripts/prepare-nemu-vdot.sh','reference'],dict(TEAM_NEMU_VDOT_ROOT=str(t12/'nemu'),TEAM_NEMU_BASE_ROOT='/home/amesotten/.cache/codex-rvinno/fullcore-20261016/nemu/reference',TEAM_EVIDENCE_DIR=str(assets/'nemu-build')))
reference=t12/'nemu/reference/build/riscv64-nemu-interpreter-so'
spec=importlib.util.spec_from_file_location('guard',root/'team/scripts/artifact_guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
guard.verify_nemu(reference.parents[1],reference,'reference')
tools={}
for name in ('gcc','riscv64-linux-gnu-gcc','riscv64-linux-gnu-as','riscv64-linux-gnu-ld','riscv64-linux-gnu-objcopy','make'):
    path=Path(shutil.which(name)).resolve();tools[str(path)]=sha(path)
for compiler in ('gcc','riscv64-linux-gnu-gcc'):
    for program in ('cc1','collect2'):
        path=Path(subprocess.check_output([compiler,'-print-prog-name='+program],text=True).strip()).resolve()
        if path.is_file():tools[str(path)]=sha(path)
fixture=root/'team/evidence/t12-regression-20261014/negative-fixture.c'
negative=t12/'build-evidence/negative-reference.so';negative.parent.mkdir(parents=True)
cmd=run('negative-build',[Path(shutil.which('gcc')).resolve(),'-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-DREF_SO="'+str(reference)+'"',fixture,'-ldl','-Wl,--no-as-needed',reference,'-o',negative])
negative_receipt=assets/'negative-build.json'
save(negative_receipt,dict(status='BUILD_PASS',source_commit=revision,command=cmd,reference_sha256=sha(reference),files={str(p):sha(p) for p in (fixture,reference,negative)},tools=tools))
hello_dir=root/'team/workloads/hello-vadd';(hello_dir/'identity.h').write_text('#define TEAM_ID "James_Hotten-O5"\n#define HOST_IP "local-validation"\n')
hello_out=t12/'repo/team/workloads/hello-vadd/build';hello_out.mkdir(parents=True)
hello=hello_out/'hello-vadd-riscv64-xs.bin';flash=hello_out/'boot-flash.bin'
hello_commands=[run('hello-build',['make','-C',hello_dir,'ARCH=riscv64-xs','MARCH=rv64gcv','BINARY='+str(hello.with_suffix('')),'-j1'])]
hello_commands.append(run('flash-assemble',['riscv64-linux-gnu-gcc','-c','-march=rv64gc','-mabi=lp64d',hello_dir/'boot-flash.S','-o',hello_out/'boot-flash.o']))
hello_commands.append(run('flash-objcopy',['riscv64-linux-gnu-objcopy','-O','binary','-j','.text',hello_out/'boot-flash.o',flash]))
am_source=guard.audit_repo(am,'086a238062fdfb3281b745a537b361983d0154b5',source_roots=('am/src','am/include','libs/klib/src','libs/klib/include'))
hello_files={str(p):sha(p) for p in [*(hello_dir/n for n in ('main.c','vadd.S','Makefile','identity.h','boot-flash.S')),hello,hello.with_suffix('.elf'),flash,hello_out/'boot-flash.o',am/'am/build/am-riscv64-xs.a',am/'libs/klib/build/klib-riscv64-xs.a']}
hello_files.update({str(am/n):digest for n,digest in am_source.items()})
hello_receipt=assets/'hello-build.json'
save(hello_receipt,dict(status='BUILD_PASS',source_commit=revision,commands=hello_commands,files=hello_files,tools=tools,am_home=str(am),am_revision='086a238062fdfb3281b745a537b361983d0154b5',am_source_sha256=am_source))
matrix=t12/'runs/t11-matrix-canonical';matrix.mkdir(parents=True)
for index in range(8):
    run('matrix-'+str(index),['bash','team/scripts/vdot-tests.sh','build-xs','full'],dict(VDOT_DATA=str(matrix/f'data-{index}'),TEAM_EVIDENCE_DIR=str(matrix/f'build-{index}'),VDOT_COVERAGE_PROFILE='legacy',VDOT_RANDOM_COUNT='32',VDOT_SMOKE_RANDOM_COUNT='32',VDOT_SHARD_INDEX=str(index),VDOT_SHARD_COUNT='8',VDOT_LOG_COMPACT='1'))
    guard.verify_build(matrix/f'build-{index}',matrix/f'build-{index}/vdot-exceptions.bin',matrix/f'data-{index}','vdot','full')
sys.path.insert(0,str(root/'team/workloads/vdot-perf'));import check as perf
control_src=root/'team/evidence/t14-optimization-20261016/control-sweep/build';control=t14/'runs/control-sweep-02'
control_receipt=json.loads((control_src/'build.json').read_text())
for name in ['build.json',*control_receipt['files']]:
    target=control/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(perf.raw_bytes(control_src/name))
for name,digest in control_receipt['files'].items():assert sha(control/name)==digest
dense_src=root/'team/evidence/t13-performance-20261015/images-v3/performance-d0-s06'
for name in ('build.json','vdot-perf.bin','vdot-perf.elf','data/manifest.json','data/kernels.S','data/cases.h','source/generate.py','source/main.c','source/Makefile'):
    target=dense/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(perf.raw_bytes(dense_src/name))
perf.verify_build_record(dense);perf.verify_generation(dense,json.loads((dense/'data/manifest.json').read_text()));perf.check_compiled_cases(dense/'vdot-perf.elf',json.loads((dense/'data/manifest.json').read_text()))
save(assets/'prepared.json',dict(status='INPUT_COMPONENTS_PREPARED',source_commit=revision,t12=str(t12),t14=str(t14),dense=str(dense),reference=str(reference),negative=str(negative),hello=str(hello),flash=str(flash),negative_receipt=str(negative_receipt),hello_receipt=str(hello_receipt),tools=tools,preparer_sha256=sha(Path(__file__))))
print('INPUT_COMPONENTS_PREPARED',flush=True)
