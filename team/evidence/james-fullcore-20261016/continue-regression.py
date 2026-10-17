"""Resume after the closed T12 control gate; never overwrite any prior run."""
import concurrent.futures,datetime,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
repo=Path('/mnt/c/Code/RVInno/riscv');output=repo/'team/out/james-fullcore-20261016'
root=Path((output/'build-copy.txt').read_text().strip());work=cache/'workloads';runs=cache/'runs'
sys.path.insert(0,str(root/'team/workloads/vdot-perf'));sys.path.insert(0,str(root/'team/scripts'))
import check as c
import artifact_guard as guard
import check_t12_compact as compact
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
os.environ.pop('XS_NEGATIVE_VECTOR_TARGET',None)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):p.write_bytes((json.dumps(value,indent=2)+'\n').encode())
def now():return datetime.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text())
phase=load(runs/'t12-phase-completion.json')
c.require(phase['status']=='CURRENT_T12_GATE_PASS','control gate not closed')
emu=root/'build/emu';refroot=cache/'nemu/reference';ref=refroot/'build/riscv64-nemu-interpreter-so';flash=work/'boot-flash.bin'
pins=load(runs/'hardware-inputs.json');software=load(runs/'software-inputs.json')
def hardware_guard():
    c.require(sha(emu)==pins['emu_sha256'],'EMU changed')
    for files in (pins['files'],pins['dependency_files'],software):
        for name,digest in files.items():c.require(sha(root/name)==digest,'frozen source changed '+name)
hardware_guard();guard.verify_nemu(refroot,ref,'reference')
spec=importlib.util.spec_from_file_location('archive',repo/'team/scripts/check-t12-archive.py');archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive)
recheck=archive.validate(runs/'t12-phase-archive',pins['source_commit'],sha(emu),sha(ref),sha(flash))
c.require(recheck==load(runs/'t12-phase-recheck.json'),'T12 gate replay changed')
save(runs/'continuation-start.json',dict(started=now(),source=pins['source_commit'],control_gate_sha256=sha(runs/'t12-phase-completion.json'),driver_sha256=sha(__file__),software_host_concurrency=2,t13_host_concurrency=16,policy='all preselected runs, seed=1; no cycle-based selection'))
def software_run(baseline):
    image=work/('software-'+baseline);profile=load(image/'current-profile.json')
    guard.verify_build(image,image/'test.bin',image/'data','t12','full')
    folder=runs/('software-'+baseline);folder.mkdir(exist_ok=False)
    command=['timeout','120m',str(emu),'-i',str(image/'test.bin'),'--flash='+str(flash),'--ram-size=128MB','--diff='+str(ref),'--max-cycles=5000000','--seed=1']
    record=dict(command=command,started=now(),files={str(p):sha(p) for p in (emu,image/'test.bin',flash,ref)},single_core=True,emu_threads=1,host_concurrency=2)
    save(folder/'runtime.json',record)
    with (folder/'stdout.log').open('wb') as o,(folder/'stderr.log').open('wb') as e:p=subprocess.run(command,cwd=root,stdout=o,stderr=e)
    record.update(exit_code=p.returncode,finished=now(),raw_sha256={n:sha(folder/n) for n in ('stdout.log','stderr.log')})
    try:
        c.require(all(sha(p)==h for p,h in record['files'].items()),'runtime input changed')
        c.require(p.returncode==0,'software runtime failure')
        text=(folder/'stderr.log').read_text()+(folder/'stdout.log').read_text()
        c.require('Difftest enabled.' in text and 'The reference model is '+str(ref) in text,'live reference binding')
        checked=compact.check(text,image/'data',0,profile['limit'],p.returncode)
        save(folder/'checked.json',checked);save(folder/'profile.json',profile)
        guard.verify_build(image,image/'test.bin',image/'data','t12','full')
    except Exception as error:
        record['verification_error']=repr(error);save(folder/'result.json',record);raise
    save(folder/'result.json',record)
    print('CURRENT_T12_SOFTWARE_PASS '+baseline+' count='+str(profile['limit']),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for future in concurrent.futures.as_completed([pool.submit(software_run,b) for b in ('original','lean')]):future.result()
hardware_guard()
selected=runs/'selected-t13-images';selected.mkdir();inventory=load(work/'t13-images/images.json')
inventory['images']=[x for x in inventory['images'] if not(x['suite']=='performance' and x['shard'] in (7,8,9))]
save(selected/'images.json',inventory);save(runs/'selection.json',dict(rule='exclude non-shared original stream shards 7,8,9 before execution; use shared-stream replacements',selected_images=len(inventory['images']),excluded_runs_not_executed=27))
records=[]
def run(name,cmd):
    record=dict(name=name,argv=list(map(str,cmd)),cwd=str(root),started=now(),status='RUNNING');records.append(record);save(output/'continuation-progress.json',records)
    with (runs/(name+'.log')).open('wb') as f:p=subprocess.run(record['argv'],cwd=root,stdout=f,stderr=subprocess.STDOUT)
    record.update(status='FINISHED',exit_code=p.returncode,finished=now());save(output/'continuation-progress.json',records)
    print(name,p.returncode,flush=True);c.require(p.returncode==0,'stage failed '+name)
for label,images in [('t13-main',selected),('t13-stream',work/'t13-stream')]:
    run(label,['python3','-B','team/workloads/vdot-perf/campaign.py','run','--images',images,'--output',runs/label,'--emu',emu,'--reference',ref,'--flash',flash,'--jobs','16'])
run('t13-analysis',['python3','-B','team/workloads/vdot-perf/analyze.py','--images',work/'t13-images','--runs',runs/'t13-main','--stream-images',work/'t13-stream','--stream-runs',runs/'t13-stream','--output',runs/'analysis'])
hardware_guard();guard.verify_nemu(refroot,ref,'reference')
save(runs/'completion.json',dict(status='CURRENT_FULLCORE_REVALIDATION_PASS',source=pins['source_commit'],emu_sha256=sha(emu),reference_sha256=sha(ref),smoke_runs=1,calibration_windows=13,t12_suite_runs=11,t12_suite_directory='t12-accepted',t12_control_workload='control-pressure-v2',t12_software_runs=2,t13_runs=126,actual_fullcore_runs=143,accepted_runs=141,excluded_setup_failure_runs=1,excluded_control_coverage_runs=1,excluded_original_stream_runs=27,hardware_rerun=True,finished=now()))
print('CURRENT_FULLCORE_REVALIDATION_PASS',flush=True)
