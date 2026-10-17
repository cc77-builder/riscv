"""Join independently checked successful attempts, preserving failed originals."""
import datetime,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
output=Path('/mnt/c/Code/RVInno/riscv/team/out/james-fullcore-20261016')
root=Path((output/'build-copy.txt').read_text().strip());work=cache/'workloads';runs=cache/'runs'
sys.path.insert(0,str(root/'team/workloads/vdot-perf'));sys.path.insert(0,str(root/'team/scripts'))
import check as c
import artifact_guard as guard
import check_t12_compact as compact
os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):p.write_bytes((json.dumps(value,indent=2)+'\n').encode())
def now():return datetime.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text())
suite=load(runs/'t12-suite/result.json');retry=load(runs/'negative-vdot-retry/result.json')
c.require(len(suite['runs'])==11 and suite['status']=='T12_FULLCORE_SUITE_FAILED','expected completed initial suite')
c.require(all(r['status']!='FAILED' for r in suite['runs'] if r['name']!='negative-vdot'),'another suite failure')
c.require(retry['status']=='EXPECTED_VDOT_HIGHBIT_REJECTION' and retry['exit_code']==1,'retry not accepted')
old=next(r for r in suite['runs'] if r['name']=='negative-vdot')
c.require(old['status']=='FAILED' and old['exit_code']==-6 and 'undefined symbol: difftest_raise_intr' in (runs/'t12-suite/negative-vdot/stdout.log').read_text(),'unexpected initial failure')
accepted=runs/'t12-accepted';accepted.mkdir(exist_ok=False)
for p in (runs/'t12-suite').iterdir():
    if p.is_file() and p.name not in ('progress.json','result.json'):shutil.copyfile(p,accepted/p.name)
for r in suite['runs']:
    source=runs/'negative-vdot-retry' if r['name']=='negative-vdot' else runs/'t12-suite'/r['name']
    shutil.copytree(source,accepted/r['name'])
summary=dict(suite,status='T12_FULLCORE_SUITE_PASS',runs=[retry if r['name']=='negative-vdot' else r for r in suite['runs']],finished=now(),aggregation='successful original positive runs plus separately executed corrected negative fixture; no results overwritten')
save(accepted/'result.json',summary)
save(accepted/'recovery.json',dict(original_result_sha256=sha(runs/'t12-suite/result.json'),replacement_result_sha256=sha(runs/'negative-vdot-retry/result.json'),replaced='negative-vdot',original_directory=str(runs/'t12-suite'),retry_directory=str(runs/'negative-vdot-retry'),new_dut_runs_for_aggregation=0))
emu=root/'build/emu';refroot=cache/'nemu/reference';ref=refroot/'build/riscv64-nemu-interpreter-so';flash=work/'boot-flash.bin'
pins=load(runs/'hardware-inputs.json');software=load(runs/'software-inputs.json')
def hardware_guard():
    c.require(sha(emu)==pins['emu_sha256'],'EMU changed')
    for files in (pins['files'],pins['dependency_files'],software):
        for name,digest in files.items():c.require(sha(root/name)==digest,'source changed '+name)
hardware_guard();guard.verify_nemu(refroot,ref,'reference')
# Reuse the established full archive checker with the new, explicitly supplied pins.
compat=runs/'t12-accepted-compat';compat.mkdir();shutil.copytree(accepted,compat/'suite')
for p in list((compat/'suite').rglob('*.log'))+[compat/'suite/hardware-pins.json']:
    p.with_name(p.name+'.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0))
(compat/'control').mkdir();(compat/'control/manifest.json.gz').write_bytes(gzip.compress((work/'control/data/manifest.json').read_bytes(),mtime=0))
(compat/'matrix').mkdir()
for i in range(8):shutil.copytree(work/f'matrix/data-{i}',compat/f'matrix/data-{i}')
save(compat/'archive-manifest.json',dict(files={p.relative_to(compat).as_posix():sha(p) for p in compat.rglob('*') if p.is_file()},raw_log_sha256={p.relative_to(compat).as_posix():hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest() for p in compat.rglob('*.log.gz')}))
records=[]
def run(name,cmd):
    record=dict(name=name,argv=list(map(str,cmd)),cwd=str(root),started=now(),status='RUNNING');records.append(record);save(output/'continuation-progress.json',records)
    with (runs/(name+'.log')).open('wb') as f:p=subprocess.run(record['argv'],cwd=root,stdout=f,stderr=subprocess.STDOUT)
    record.update(status='FINISHED',exit_code=p.returncode,finished=now());save(output/'continuation-progress.json',records)
    print(name,p.returncode,flush=True);c.require(p.returncode==0,'stage failed '+name)
run('t12-recovery-check',['python3','-B','team/scripts/check-t12-archive.py',compat,'--expected-source',pins['source_commit'],'--expected-emu',sha(emu),'--expected-reference',sha(ref),'--expected-flash',sha(flash)])
for baseline in ('original','lean'):
    image=work/('software-'+baseline);profile=load(image/'current-profile.json')
    guard.verify_build(image,image/'test.bin',image/'data','t12','full')
    folder=runs/('software-'+baseline);folder.mkdir(exist_ok=False)
    command=['timeout','120m',str(emu),'-i',str(image/'test.bin'),'--flash='+str(flash),'--ram-size=128MB','--diff='+str(ref),'--max-cycles=5000000','--seed=1']
    record=dict(command=command,started=now(),files={str(p):sha(p) for p in (emu,image/'test.bin',flash,ref)},single_core=True,emu_threads=1)
    save(folder/'runtime.json',record)
    with (folder/'stdout.log').open('wb') as o,(folder/'stderr.log').open('wb') as e:p=subprocess.run(command,cwd=root,stdout=o,stderr=e)
    record.update(exit_code=p.returncode,finished=now(),raw_sha256={n:sha(folder/n) for n in ('stdout.log','stderr.log')})
    stable=all(sha(p)==h for p,h in record['files'].items())
    if not stable:record['verification_error']='runtime input changed'
    save(folder/'result.json',record)
    c.require(stable and p.returncode==0,'software runtime failure')
    text=(folder/'stderr.log').read_text()+(folder/'stdout.log').read_text()
    c.require('Difftest enabled.' in text and 'The reference model is '+str(ref) in text,'live reference binding')
    checked=compact.check(text,image/'data',0,profile['limit'],p.returncode)
    save(folder/'checked.json',checked);save(folder/'profile.json',profile)
    guard.verify_build(image,image/'test.bin',image/'data','t12','full')
    print('CURRENT_T12_SOFTWARE_PASS '+baseline+' count='+str(profile['limit']),flush=True)
hardware_guard()
selected=runs/'selected-t13-images';selected.mkdir();inventory=load(work/'t13-images/images.json')
inventory['images']=[x for x in inventory['images'] if not(x['suite']=='performance' and x['shard'] in (7,8,9))]
save(selected/'images.json',inventory);save(runs/'selection.json',dict(rule='exclude non-shared original stream shards 7,8,9 before execution; use shared-stream replacements',selected_images=len(inventory['images']),excluded_runs_not_executed=27))
for label,images in [('t13-main',selected),('t13-stream',work/'t13-stream')]:
    run(label,['python3','-B','team/workloads/vdot-perf/campaign.py','run','--images',images,'--output',runs/label,'--emu',emu,'--reference',ref,'--flash',flash,'--jobs','4'])
run('t13-analysis',['python3','-B','team/workloads/vdot-perf/analyze.py','--images',work/'t13-images','--runs',runs/'t13-main','--stream-images',work/'t13-stream','--stream-runs',runs/'t13-stream','--output',runs/'analysis'])
hardware_guard();guard.verify_nemu(refroot,ref,'reference')
save(runs/'completion.json',dict(status='CURRENT_FULLCORE_REVALIDATION_PASS',source=pins['source_commit'],emu_sha256=sha(emu),reference_sha256=sha(ref),smoke_runs=1,calibration_windows=13,t12_suite_runs=11,t12_suite_directory='t12-accepted',t12_software_runs=2,t13_runs=126,actual_fullcore_runs=142,accepted_runs=141,excluded_setup_failure_runs=1,excluded_original_stream_runs=27,hardware_rerun=True,finished=now()))
print('CURRENT_FULLCORE_REVALIDATION_PASS',flush=True)
