"""Close the current T12 gate only; keep all failed attempts and pending stages."""
import datetime,gzip,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv');cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
out=repo/'team/out/james-fullcore-20261016';root=Path((out/'build-copy.txt').read_text().strip());runs=cache/'runs';work=cache/'workloads'
def require(ok,message):
    if not ok:raise ValueError(message)
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def module(n):
    spec=importlib.util.spec_from_file_location(n,repo/'team/scripts'/n);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
suite=load(runs/'t12-suite/result.json');retry=load(runs/'negative-vdot-retry/result.json');pressure=load(runs/'control-pressure-v2/result.json')
require(len(suite['runs'])==11 and suite['status']=='T12_FULLCORE_SUITE_FAILED','incomplete original suite')
require(all(r['status']!='FAILED' for r in suite['runs'] if r['name'] not in ('negative-vdot','control')),'other suite failure')
require(pressure['status']=='T12_CONTROL_REGRESSION_PASS','pressure gate incomplete')
old=next(r for r in suite['runs'] if r['name']=='negative-vdot')
require(old['status']=='FAILED' and old['exit_code']==-6,'unexpected setup attempt')
require(load(runs/'control-recheck.json')['status']=='T12_COVERAGE_INCOMPLETE','original coverage record changed')
negative=module('check-vdot-negative.py').check((runs/'negative-vdot-retry/run.log').read_text(),retry['exit_code'])
control=module('check-vdot-regression.py').check((runs/'control-pressure-v2/run.log').read_text(),load(work/'control-pressure-v2/data/manifest.json'),pressure['exit_code'])
require(control['status']=='T12_CONTROL_REGRESSION_PASS','pressure replay')
for n,h in load(work/'control-pressure-v2/source.json')['after'].items():
    require(hashlib.sha256((repo/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,'promoted source differs '+n)
pins=load(runs/'hardware-inputs.json')
for mapping in (pins['files'],pins['dependency_files']):
    for n,h in mapping.items():require(sha(root/n)==h,'frozen hardware source changed '+n)
require(sha(root/'build/emu')==pins['emu_sha256'],'EMU changed')
for record in suite['runs']+[retry,pressure]:
    require(all(sha(Path(n))==h for n,h in record['files'].items()),'runtime files changed')
accepted=runs/'t12-accepted';accepted.mkdir(exist_ok=False);records=[]
for p in (runs/'t12-suite').iterdir():
    if p.is_file() and p.name not in ('progress.json','result.json'):shutil.copyfile(p,accepted/p.name)
for r in suite['runs']:
    name=r['name'];original=runs/'t12-suite'/name
    if name=='negative-vdot':original=runs/'negative-vdot-retry'
    if name=='control':original=runs/'control-pressure-v2'
    shutil.copytree(original,accepted/name)
    record=load(original/'result.json')
    if name=='negative-vdot':
        shutil.copyfile(original/'result.json',accepted/name/'original-result.json')
        record.update(negative);record.pop('error',None)
        record['recheck']=dict(original_result_sha256=sha(original/'result.json'),reason='DiffTest mismatch PC is commit group start; injected instruction is bound to group trace',checker_sha256=sha(repo/'team/scripts/check-vdot-negative.py'))
        save(accepted/name/'result.json',record)
    records.append(record)
summary=dict(suite,status='T12_FULLCORE_SUITE_PASS',runs=records,aggregation='original 9 positive runs + corrected negative fixture recheck + separately executed pressure workload; all original attempts retained')
save(accepted/'result.json',summary)
compat=runs/'t12-phase-archive';compat.mkdir();shutil.copytree(accepted,compat/'suite')
for p in list((compat/'suite').rglob('*.log'))+[compat/'suite/hardware-pins.json']:
    p.with_name(p.name+'.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0))
(compat/'control').mkdir();(compat/'control/manifest.json.gz').write_bytes(gzip.compress((work/'control-pressure-v2/data/manifest.json').read_bytes(),mtime=0))
(compat/'matrix').mkdir()
for i in range(8):shutil.copytree(work/f'matrix/data-{i}',compat/f'matrix/data-{i}')
save(compat/'archive-manifest.json',dict(files={p.relative_to(compat).as_posix():sha(p) for p in compat.rglob('*') if p.is_file()},raw_log_sha256={p.relative_to(compat).as_posix():hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest() for p in compat.rglob('*.log.gz')}))
ref=cache/'nemu/reference/build/riscv64-nemu-interpreter-so';flash=work/'boot-flash.bin'
result=module('check-t12-archive.py').validate(compat,pins['source_commit'],pins['emu_sha256'],sha(ref),sha(flash))
save(runs/'t12-phase-recheck.json',result)
review_names=['team/scripts/'+n for n in ('check-vdot-regression.py','check-vdot-negative.py','run-t12-suite.py','check-t12-archive.py')]
review_names+=['team/tests/test_t12_regression.py','team/tests/test_vdot_negative.py','team/workloads/vdot-regression/generate.py']
save(runs/'reviewer-inputs.json',{n:hashlib.sha256((repo/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for n in review_names})
save(runs/'t12-phase-completion.json',dict(status='CURRENT_T12_GATE_PASS',execution_source=pins['source_commit'],emu_sha256=pins['emu_sha256'],reference_sha256=sha(ref),actual_fullcore_runs=15,accepted_runs=13,excluded_attempts={'fixture_load_abort':1,'original_control_coverage_incomplete':1},calibration_windows=13,matrix_unique=117,matrix_executed=124,t12_control=control,full_revalidation_complete=False,pending=['T12 software original190/lean199','T13 126 accepted runs / 1404 windows'],finished=datetime.datetime.now().astimezone().isoformat()))
print('CURRENT_T12_GATE_PASS',flush=True)
