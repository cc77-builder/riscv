"""Recompute archived current-source results; never launches a DUT."""
import argparse,gzip,hashlib,importlib.util,json,shutil,sys,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
a=p.parse_args();archive=a.archive.resolve();repo=a.repo.resolve()
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(path.read_text())
def save(path,value):path.write_bytes((json.dumps(value,indent=2)+'\n').encode())
seal=load(archive/'file-manifest.json')['files']
require({p.name for p in archive.iterdir() if p.is_file()}==set(seal)|{'file-manifest.json'},'archive inventory')
for name,digest in seal.items():
    require(Path(name).name==name,'unsafe archive filename')
    require(sha((archive/name).read_bytes())==digest,'archive hash '+name)
for name,info in load(archive/'raw-build-logs.json').items():
    data=gzip.decompress((archive/(name+'.gz')).read_bytes())
    require(sha(data)==info['sha256'] and len(data)==info['bytes'],'raw build log '+name)
require(not a.output.exists(),'use a new output directory')
a.output.mkdir(parents=True)
sys.path.insert(0,str(repo/'team/workloads/vdot-perf'))
sys.path.insert(0,str(repo/'team/scripts'))
import check as c
import analyze
import check_t12_compact as compact
spec=importlib.util.spec_from_file_location('t12archive',repo/'team/scripts/check-t12-archive.py')
t12=importlib.util.module_from_spec(spec);spec.loader.exec_module(t12)
with tempfile.TemporaryDirectory(prefix='james-fullcore-replay-') as temp:
    root=Path(temp)
    inventories=load(archive/'bundle-files.json')
    for bundle,entries in inventories.items():
        require(Path(bundle).name==bundle,'unsafe bundle name')
        base=root/bundle;base.mkdir()
        with tarfile.open(archive/(bundle+'.tar.gz'),'r:gz') as tar:
            members=tar.getmembers()
            require(len(members)==len(entries) and {m.name for m in members}==set(entries),'bundle inventory '+bundle)
            for member in members:
                target=(base/member.name).resolve()
                require(member.isfile() and target.is_relative_to(base),'unsafe tar member')
                data=tar.extractfile(member).read();expected=entries[member.name]
                require(len(data)==expected['bytes'] and sha(data)==expected['sha256'],'bundle member hash '+member.name)
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    runs=root/'runs';work=root/'workloads'
    completion=load(runs/'completion.json');pins=load(runs/'hardware-inputs.json')
    require(completion['source']==pins['source_commit'] and completion['emu_sha256']==pins['emu_sha256'],'source/hardware binding')
    # Execution sources remain frozen at d370. The separately bound reviewer
    # overlay includes fixes established by replay; never relabel it as RTL.
    reviewer=load(runs/'reviewer-inputs.json')
    for name,digest in reviewer.items():
        require(sha((repo/name).read_bytes().replace(b'\r\n',b'\n'))==digest,'reviewer source changed '+name)
    software=load(runs/'software-inputs.json')
    for name,digest in software.items():
        if name.endswith(('.py','.jsonl')) and not name.startswith('team/workloads/vdot-perf/test_'):
            data=(repo/name).read_bytes().replace(b'\r\n',b'\n')
            require(sha(data)==reviewer.get(name,digest),'checker/model source changed '+name)
    external={}
    smoke=load(runs/'smoke-hello-vadd/result.json')
    roles=c.runtime_roles(smoke['command'])
    for role in ('emu','reference','flash'):external[roles[role]]=smoke['files'][roles[role]]
    require(external[roles['emu']]==completion['emu_sha256'] and external[roles['reference']]==completion['reference_sha256'],'runtime pins')
    require(set(smoke['files'])==set(roles.values()) and set(smoke['raw_sha256'])=={'stdout.log','stderr.log'},'smoke bindings')
    require(smoke['files'][roles['image']]==sha((work/'hello-vadd.bin').read_bytes()),'smoke image')
    for name,digest in smoke['raw_sha256'].items():require(sha((runs/'smoke-hello-vadd'/name).read_bytes())==digest,'smoke log')
    text=c.read_text(runs/'smoke-hello-vadd/stdout.log')+c.read_text(runs/'smoke-hello-vadd/stderr.log')
    require(smoke['exit_code']==0 and 'HELLO_VADD_PASS cases=3 lanes=24' in text and 'HIT GOOD TRAP' in text and 'Difftest enabled.' in text,'smoke result')
    cal=c.verify(work/'calibration',runs/'calibration/calibration-r0',external)
    require(cal==load(runs/'calibration-check.json') and len(cal['samples'])==13,'calibration result')
    save(a.output/'calibration.json',cal)
    current=analyze.analyze(work/'t13-images',runs/'t13-main',work/'t13-stream',runs/'t13-stream',a.output/'t13',external)
    require(current==load(runs/'analysis/result.json'),'T13 result changed')
    # Adapt losslessly to the existing T12 archive reader; no historical pins are bypassed.
    compat=root/'t12-compat';compat.mkdir();shutil.copytree(runs/completion.get('t12_suite_directory','t12-suite'),compat/'suite')
    for path in list((compat/'suite').rglob('*.log'))+[(compat/'suite/hardware-pins.json')]:
        path.with_name(path.name+'.gz').write_bytes(gzip.compress(path.read_bytes(),mtime=0))
    control_workload=work/completion['t12_control_workload']
    (compat/'control').mkdir();(compat/'control/manifest.json.gz').write_bytes(gzip.compress((control_workload/'data/manifest.json').read_bytes(),mtime=0))
    (compat/'matrix').mkdir()
    for i in range(8):shutil.copytree(work/f'matrix/data-{i}',compat/f'matrix/data-{i}')
    save(compat/'archive-manifest.json',dict(files={p.relative_to(compat).as_posix():sha(p.read_bytes()) for p in compat.rglob('*') if p.is_file()},raw_log_sha256={p.relative_to(compat).as_posix():sha(gzip.decompress(p.read_bytes())) for p in compat.rglob('*.log.gz')}))
    control=t12.validate(compat,completion['source'],completion['emu_sha256'],completion['reference_sha256'],external[roles['flash']])
    save(a.output/'t12.json',control)
    # Successful aggregation must not hide a failed original or count copies
    # as new DUT executions. Check the raw attempts and both reclassifications.
    original=load(runs/'t12-suite/result.json')
    require(original['status']=='T12_FULLCORE_SUITE_FAILED' and len(original['runs'])==11,'original suite history')
    expected_failures={'negative-vdot','control'}
    require({r['name'] for r in original['runs'] if r['status']=='FAILED'}==expected_failures,'unexpected original failure')
    for record in original['runs']:
        directory=runs/'t12-suite'/record['name']
        require(record==load(directory/'result.json'),'original summary drift')
        raw={n:(directory/n).read_bytes() for n in ('stdout.log','stderr.log')}
        require(all(sha(b)==record['raw_logs_sha256'][n] for n,b in raw.items()),'original attempt log changed')
        require((directory/'run.log').read_bytes()==raw['stderr.log']+raw['stdout.log'],'original streams changed')
    require(load(runs/'t12-suite/negative-vdot/result.json')['exit_code']==-6,'lost setup abort')
    original_control=t12.control.check(c.read_text(runs/'t12-suite/control/run.log'),load(work/'control/data/manifest.json'),0)
    require(original_control==load(runs/'control-recheck.json') and original_control['status']=='T12_COVERAGE_INCOMPLETE','original coverage failure changed')
    retry=load(runs/'negative-vdot-retry/result.json')
    require(retry['status']=='FAILED' and retry['exit_code']==1,'negative checker history lost')
    require((runs/'negative-vdot-retry/run.log').read_bytes()==(runs/'t12-accepted/negative-vdot/run.log').read_bytes(),'negative recheck used another run')
    require((runs/'control-pressure-v2/run.log').read_bytes()==(runs/'t12-accepted/control/run.log').read_bytes(),'pressure run changed in aggregation')
    for name,digest in load(control_workload/'source.json')['after'].items():
        require(sha((control_workload/'source'/name).read_bytes())==digest,'pressure source snapshot changed')
        require(sha((repo/name).read_bytes().replace(b'\r\n',b'\n'))==digest,'promoted pressure source changed')
    for baseline in ('original','lean'):
        folder=runs/('software-'+baseline);receipt=load(folder/'result.json');image=work/('software-'+baseline)
        profile=load(folder/'profile.json');selected=c.runtime_roles(receipt['command'])
        require(set(receipt['files'])==set(selected.values()) and receipt['exit_code']==0,'software runtime binding')
        require(all(receipt['files'][selected[k]]==external[roles[k]] for k in ('emu','reference','flash')),'software runtime pins')
        require(receipt['files'][selected['image']]==sha((image/'test.bin').read_bytes()),'software image')
        require(set(receipt['raw_sha256'])=={'stdout.log','stderr.log'},'software transcript inventory')
        for name,digest in receipt['raw_sha256'].items():require(sha((folder/name).read_bytes())==digest,'software log')
        text=c.read_text(folder/'stderr.log')+c.read_text(folder/'stdout.log')
        checked=compact.check(text,image/'data',0,profile['limit'],receipt['exit_code'])
        require(checked==load(folder/'checked.json'),'software result changed')
        plan=compact.aggregate([checked],image/'data')
        require(plan==load(folder/'plan.json') and plan['executed']==(190 if baseline=='original' else 199),'software plan/pairs changed')
        save(a.output/('software-'+baseline+'.json'),checked)
        save(a.output/('software-'+baseline+'-plan.json'),plan)
    attempt_dirs=[runs/'smoke-hello-vadd',runs/'calibration/calibration-r0',runs/'negative-vdot-retry',runs/'control-pressure-v2',runs/'software-original',runs/'software-lean']
    attempt_dirs += [runs/'t12-suite'/r['name'] for r in original['runs']]
    attempt_dirs += [p.parent for label in ('t13-main','t13-stream') for p in (runs/label).glob('*/runtime.json')]
    require(len(attempt_dirs)==len(set(attempt_dirs))==143 and completion['actual_fullcore_runs']==143 and completion['accepted_runs']==141,'actual execution count')
    require(all((p/'result.json').exists() for p in attempt_dirs),'unfinished actual run')
    receipt=dict(status='CURRENT_FULLCORE_ARCHIVE_RECHECK_PASS',source=completion['source'],archived_fullcore_runs=completion['actual_fullcore_runs'],hardware_rerun=False,T13_accepted_runs=126,T13_windows=1404,calibration_windows=13,matrix_unique=117)
    save(a.output/'receipt.json',receipt);print(json.dumps(receipt))
