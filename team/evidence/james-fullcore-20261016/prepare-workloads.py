import importlib.util,json,os,subprocess,sys,time
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
output=Path('/mnt/c/Code/RVInno/riscv/team/out/james-fullcore-20261016')
root=Path((output/'build-copy.txt').read_text().strip())
work=cache/'workloads';work.mkdir(exist_ok=False)
am=cache/'nexus-am'
records=[]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1',BUILD_JOBS='1')
def save(path,obj):path.write_bytes((json.dumps(obj,indent=2)+'\n').encode())
def run(name,cmd,extra=None,cwd=root):
    start=time.time();record=dict(name=name,argv=[str(x) for x in cmd],cwd=str(cwd),started=start,status='RUNNING',environment=extra or {})
    records.append(record);save(output/'workload-progress.json',records)
    with (work/(name+'.log')).open('wb') as f:
        p=subprocess.run(record['argv'],cwd=cwd,env=dict(env,**(extra or {})),stdout=f,stderr=subprocess.STDOUT)
    record.update(status='FINISHED',exit_code=p.returncode,seconds=round(time.time()-start,3));save(output/'workload-progress.json',records)
    print(name,p.returncode,flush=True)
    if p.returncode:raise RuntimeError(name)
run('clone-am',['git','clone','--shared','--no-checkout','/home/amesotten/.cache/codex-t05/nexus-am-086a238',am])
run('checkout-am',['git','-C',am,'checkout','--detach','086a238062fdfb3281b745a537b361983d0154b5'])
sys.path.insert(0,str(root/'team/workloads/vdot-perf'))
import campaign as campaign
import check as checker
import generate
software=campaign.software_inputs();am_before=campaign.am_inputs(am)
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
# A fresh calibration image uses the same source/generation/artifact gates as campaign builds.
d=work/'calibration';d.mkdir();campaign.snapshot_sources(d,software)
manifest=generate.generate(d/'data','smoke',0)
cmd=['make','-C','team/workloads/vdot-perf','ARCH=riscv64-xs','MARCH=rv64gcv','T13_DATA='+str(d/'data'),'T13_OBJ_ROOT='+str(d/'objects'),'BINARY='+str(d/'vdot-perf'),'-j1']
run('calibration-build',cmd)
save(d/'build.json',dict(source=source,command=cmd,exit_code=0,am_revision=checker.AM_REVISION,am_source=am_before,software=software,artifacts={p.name:campaign.digest(p) for p in (d/'vdot-perf.bin',d/'vdot-perf.elf',d/'data/manifest.json')}))
campaign.unchanged_software(source,software)
checker.require(campaign.am_inputs(am)==am_before,'AM changed')
checker.verify_build_record(d);checker.verify_generation(d,manifest);checker.check_compiled_cases(d/'vdot-perf.elf',manifest)
save(work/'calibration-images.json',{'source':source,'images':[dict(name='calibration',path=str(d),replays=1)]})
cal_inventory=work/'calibration-inventory';cal_inventory.mkdir();save(cal_inventory/'images.json',json.loads((work/'calibration-images.json').read_text()))
# Build flash and hello/vadd independently from the current source.
hello=root/'team/workloads/hello-vadd'
(hello/'identity.h').write_text('#define TEAM_ID "James_Hotten-current"\n#define HOST_IP "local-validation"\n')
run('hello-build',['make','-C',hello,'ARCH=riscv64-xs','MARCH=rv64gcv','BINARY='+str(work/'hello-vadd'),'-j1'])
run('flash-assemble',['riscv64-linux-gnu-gcc','-c','-march=rv64gc','-mabi=lp64d',hello/'boot-flash.S','-o',work/'boot-flash.o'])
run('flash-objcopy',['riscv64-linux-gnu-objcopy','-O','binary','-j','.text',work/'boot-flash.o',work/'boot-flash.bin'])
# t12-regression.sh sources activate.sh, so provide a local xs-env layout for its AM lookup.
xsenv=cache/'xs-env';xsenv.mkdir();(xsenv/'nexus-am').symlink_to(am,target_is_directory=True)
run('control-build',['bash','team/scripts/t12-regression.sh','build-workload'],dict(T12_RUN_ROOT=str(work/'control'),TEAM_XS_ENV_ROOT=str(xsenv)))
matrix=work/'matrix';matrix.mkdir()
for i in range(8):
    run('matrix-build-'+str(i),['bash','team/scripts/vdot-tests.sh','build-xs','full'],dict(VDOT_DATA=str(matrix/f'data-{i}'),TEAM_EVIDENCE_DIR=str(matrix/f'build-{i}'),VDOT_COVERAGE_PROFILE='legacy',VDOT_RANDOM_COUNT='32',VDOT_SMOKE_RANDOM_COUNT='32',VDOT_SHARD_INDEX=str(i),VDOT_SHARD_COUNT='8',VDOT_LOG_COMPACT='1'))
# Preserve the historical trace-off profile; build this current-source software profile separately.
spec=importlib.util.spec_from_file_location('guard',root/'team/scripts/artifact_guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
for baseline in ('original','lean'):
    d=work/('software-'+baseline);d.mkdir()
    cmd=['python3','-B','team/tests/generate_t12.py','--output',d/'data','--baseline',baseline]
    if baseline=='lean':cmd+=['--include-chain']
    run(baseline+'-generate',cmd)
    manifest=json.loads((d/'data/manifest.json').read_text());limit=len(manifest['schedule'])
    run(baseline+'-build',['make','-C','team/workloads/t12-perf','ARCH=riscv64-xs','MARCH=rv64gcv','T12_START=0','T12_COUNT='+str(limit),'T12_DATA='+str(d/'data'),'VDOT_OBJ_ROOT='+str(d/'objects'),'BINARY='+str(d/'test'),'-j1'])
    for name,paths in [('source.sha256',[root/n for n in ('team/workloads/t12-perf/main.c','team/workloads/t12-perf/Makefile','team/workloads/t12-perf/sites.S','team/tests/generate_t12.py')]),('inputs.sha256',list((d/'data').iterdir())),('workload.sha256',[d/'test.bin',d/'test.elf'])]:
        (d/name).write_text(''.join(campaign.digest(p)+'  '+str(p)+'\n' for p in paths))
    guard.capture_build(d,d/'data','t12','riscv64-xs','full',am)
    save(d/'current-profile.json',dict(source=source,baseline=baseline,start=0,limit=limit))
ref=cache/'nemu/reference/build/riscv64-nemu-interpreter-so'
run('negative-fixture-build',['gcc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-DREF_SO="'+str(ref)+'"',root/'team/evidence/t12-regression-20261014/negative-fixture.c','-ldl','-o',work/'negative-reference.so'])
run('t13-images-build',['python3','-B','team/workloads/vdot-perf/campaign.py','build','--output',work/'t13-images','--am',am])
run('t13-stream-build',['python3','-B','team/workloads/vdot-perf/campaign.py','build','--output',work/'t13-stream','--am',am,'--stream-only'])
save(work/'assets.json',dict(source=source,reference=str(ref),files={str(p):campaign.digest(p) for p in (work/'hello-vadd.bin',work/'boot-flash.bin',work/'negative-reference.so',ref)},software=software,am_source=am_before))
checker.require(campaign.am_inputs(am)==am_before,'AM changed during workload builds')
print('CURRENT_WORKLOADS_READY',flush=True)
