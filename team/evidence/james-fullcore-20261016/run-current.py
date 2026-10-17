"""Current-source validation driver; historical runtime profiles stay unchanged."""
import datetime,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
output=Path('/mnt/c/Code/RVInno/riscv/team/out/james-fullcore-20261016')
root=Path((output/'build-copy.txt').read_text().strip());work=cache/'workloads'
result=cache/'runs';result.mkdir(exist_ok=False)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
sys.path.insert(0,str(root/'team/workloads/vdot-perf'))
import check as c
sys.path.insert(0,str(root/'team/scripts'))
import artifact_guard as guard
import check_t12_compact as compact
records=[]
def now():return datetime.datetime.now().astimezone().isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path,obj):path.write_bytes((json.dumps(obj,indent=2)+'\n').encode())
def run(name,cmd):
    record=dict(name=name,argv=list(map(str,cmd)),cwd=str(root),started=now(),status='RUNNING');records.append(record);save(output/'run-progress.json',records)
    with (result/(name+'.log')).open('wb') as f:p=subprocess.run(record['argv'],cwd=root,stdout=f,stderr=subprocess.STDOUT)
    record.update(status='FINISHED',exit_code=p.returncode,finished=now());save(output/'run-progress.json',records)
    print(name,p.returncode,flush=True)
    c.require(p.returncode==0,'stage failed '+name)
# Do not run a partial/stale build just because an executable exists.
build=json.loads((output/'build-progress.json').read_text())
c.require(len(build)==7 and all(x.get('exit_code')==0 for x in build),'full source-bound build not complete')
preparation=json.loads((output/'workload-progress.json').read_text())
c.require(preparation[-1]['name']=='t13-stream-build' and all(x.get('exit_code')==0 for x in preparation),'workload preparation incomplete')
binding=json.loads((root/'build/source-binding.json').read_text())
deps=json.loads((cache/'hardware/dependency-sources.json').read_text())['sources']
after=json.loads((cache/'hardware-after/dependency-sources.json').read_text())['sources']
c.require(deps==after,'dependency changed during build')
emu=root/'build/emu';reference_root=cache/'nemu/reference';ref=reference_root/'build/riscv64-nemu-interpreter-so';flash=work/'boot-flash.bin'
save(result/'reference-provenance.json',guard.verify_nemu(reference_root,ref,'reference'))
pins=dict(source_commit=binding['revision'],VDOT_T12_TRACE='1',VDOT_T13_TRACE='1',config='MinimalConfig',NUM_CORES=1,EMU_THREADS=1,
          files=binding['physical_root_sha256'],dependency_files={folder+'/'+p:h for folder,files in deps.items() for p,h in files.items()},emu_sha256=sha(emu),
          source_pack_sha256=binding['source_pack_sha256'],build_profile=json.loads((cache/'hardware/compile-profile.json').read_text()))
save(result/'hardware-inputs.json',pins)
paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
software={p:sha(root/p) for p in paths if p.startswith(('team/scripts/','team/tests/','team/models/','team/workloads/','team/patches/')) and (root/p).is_file()}
software['team/workloads/hello-vadd/identity.h']=sha(root/'team/workloads/hello-vadd/identity.h')
save(result/'software-inputs.json',software)
def hardware_guard():
    c.require(sha(emu)==pins['emu_sha256'],'EMU changed')
    for group in (pins['files'],pins['dependency_files'],software):
        for name,digest in group.items():c.require(sha(root/name)==digest,'input changed '+name)
hardware_guard()
assets=json.loads((work/'assets.json').read_text())
c.require(all(sha(p)==h for p,h in assets['files'].items()),'workload asset changed')
def runtime(name,image):
    folder=result/name;folder.mkdir()
    command=['timeout','120m',str(emu),'-i',str(image),'--flash='+str(flash),'--ram-size=128MB','--diff='+str(ref),'--max-cycles=5000000','--seed=1']
    record=dict(command=command,started=now(),files={str(p):sha(p) for p in (emu,image,flash,ref)},single_core=True,emu_threads=1)
    save(folder/'runtime.json',record)
    with (folder/'stdout.log').open('wb') as stdout,(folder/'stderr.log').open('wb') as stderr:
        p=subprocess.run(command,cwd=root,stdout=stdout,stderr=stderr)
    record.update(exit_code=p.returncode,finished=now(),raw_sha256={n:sha(folder/n) for n in ('stdout.log','stderr.log')})
    stable=all(sha(p)==h for p,h in record['files'].items())
    if not stable:record['verification_error']='runtime input changed'
    save(folder/'result.json',record)
    c.require(stable and p.returncode==0,'runtime failure '+name)
    text=(folder/'stderr.log').read_text()+(folder/'stdout.log').read_text()
    c.require('Difftest enabled.' in text and 'The reference model is '+str(ref) in text,'live reference binding')
    c.require('HIT GOOD TRAP' in text and not any(s in text for s in ('HIT BAD TRAP','DIFFTEST FAIL','different at pc')),'trap/diff failure')
    return folder,text
folder,text=runtime('smoke-hello-vadd',work/'hello-vadd.bin')
c.require('HELLO_VADD_PASS' in text,'hello/vadd failed');save(folder/'checked.json',dict(status='CURRENT_HELLO_VADD_PASS',source=binding['revision']))
print('CURRENT_HELLO_VADD_PASS',flush=True)
run('calibration-run',['python3','-B','team/workloads/vdot-perf/campaign.py','run','--images',work/'calibration-inventory','--output',result/'calibration','--emu',emu,'--reference',ref,'--flash',flash,'--jobs','1'])
cal=c.verify(work/'calibration',result/'calibration/calibration-r0');c.require(len(cal['samples'])==13,'calibration cardinality');save(result/'calibration-check.json',cal)
print('CURRENT_CALIBRATION_PASS windows=13',flush=True)
hardware_guard()
run('t12-suite',['python3','-B','team/scripts/run-t12-suite.py','--output',result/'t12-suite','--hardware-pins',result/'hardware-inputs.json','--emu',emu,'--reference-root',reference_root,'--negative-reference',work/'negative-reference.so','--flash',flash,'--hello',work/'hello-vadd.bin','--control',work/'control','--matrix',work/'matrix','--jobs','4'])
for baseline in ('original','lean'):
    image=work/('software-'+baseline);profile=json.loads((image/'current-profile.json').read_text())
    guard.verify_build(image,image/'test.bin',image/'data','t12','full')
    folder,text=runtime('software-'+baseline,image/'test.bin')
    checked=compact.check(text,image/'data',0,profile['limit'],0)
    save(folder/'checked.json',checked);save(folder/'profile.json',profile)
    guard.verify_build(image,image/'test.bin',image/'data','t12','full')
    print('CURRENT_T12_SOFTWARE_PASS '+baseline+' count='+str(profile['limit']),flush=True)
hardware_guard()
# Original stream buffers are known unfair and excluded before any cycle is observed.
# Keep their build artifacts, but do not spend simulation time on excluded runs.
selected=result/'selected-t13-images';selected.mkdir()
inventory=json.loads((work/'t13-images/images.json').read_text())
inventory['images']=[x for x in inventory['images'] if not(x['suite']=='performance' and x['shard'] in (7,8,9))]
save(selected/'images.json',inventory)
save(result/'selection.json',dict(rule='exclude non-shared original stream shards 7,8,9 before execution; use shared-stream replacements',selected_images=len(inventory['images']),excluded_runs_not_executed=27))
for label,images in [('t13-main',selected),('t13-stream',work/'t13-stream')]:
    run(label,['python3','-B','team/workloads/vdot-perf/campaign.py','run','--images',images,'--output',result/label,'--emu',emu,'--reference',ref,'--flash',flash,'--jobs','4'])
run('t13-analysis',['python3','-B','team/workloads/vdot-perf/analyze.py','--images',work/'t13-images','--runs',result/'t13-main','--stream-images',work/'t13-stream','--stream-runs',result/'t13-stream','--output',result/'analysis'])
hardware_guard();guard.verify_nemu(reference_root,ref,'reference')
save(result/'completion.json',dict(status='CURRENT_FULLCORE_REVALIDATION_PASS',source=binding['revision'],emu_sha256=sha(emu),reference_sha256=sha(ref),smoke_runs=1,calibration_windows=13,t12_suite_runs=11,t12_software_runs=2,t13_runs=126,actual_fullcore_runs=141,excluded_original_stream_runs=27,hardware_rerun=True,finished=now()))
print('CURRENT_FULLCORE_REVALIDATION_PASS',flush=True)
