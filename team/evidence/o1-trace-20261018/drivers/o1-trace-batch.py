"""One frozen batch128 image: observe handoff, without T13 timing acceptance."""
import datetime, hashlib, importlib.util, json, os, re, subprocess, sys, tarfile
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv')
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018')
core=cache/'source-0d8e5ae781e51a3c'
out=cache/'batch-01';out.mkdir()
sys.path.insert(0,str(repo/'team/optimizations/o1'))
from check_trace import audit, require
from run_trace_core import ARCHIVE_SHA256
sys.path.insert(0,str(repo/'team/scripts'))
import artifact_guard
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def now():return datetime.datetime.now().astimezone().isoformat()
pins=json.loads((cache/'core-runs-01/inputs.json').read_text())['files']
require(all(sha(p)==h for p,h in pins.items()),'changed build/runtime inputs')
archive=repo/'team/evidence/james-fullcore-20261016/workloads.tar.gz'
require(sha(archive)==ARCHIVE_SHA256,'frozen images changed')
prefix='t13-images/performance-d0-s06/'
with tarfile.open(archive,'r:gz') as source:
    for name in ('vdot-perf.bin','vdot-perf.elf','data/manifest.json'):
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        member=source.getmember(prefix+name)
        require(member.isfile(),'invalid archive member')
        target.write_bytes(source.extractfile(member).read())
manifest=json.loads((out/'data/manifest.json').read_text())
require(manifest['compact'] and len(manifest['plan'])==12 and
        {(r['scenario'],r['dots']) for r in manifest['rows']}=={('batch',128)},'unexpected batch plan')
checker_path=repo/'team/workloads/vdot-perf/check.py'
spec=importlib.util.spec_from_file_location('compiled_cases',checker_path)
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
checker.check_compiled_cases(out/'vdot-perf.elf',manifest)
expected=sum(manifest['rows'][entry['index']]['dots'] for entry in manifest['plan'] if manifest['rows'][entry['index']]['method']=='vdot')
require(expected==768,'unexpected architectural dot count')
refroot=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016/nemu/reference')
reference=refroot/'build/riscv64-nemu-interpreter-so'
save(out/'reference-before.json',artifact_guard.verify_nemu(refroot,reference,'reference'))
image=out/'vdot-perf.bin';flash=cache/'core-runs-01/images/boot-flash.bin';emu=core/'build/emu'
for path in (image,out/'vdot-perf.elf',out/'data/manifest.json',Path(__file__),checker_path):pins[str(path)]=sha(path)
command=['timeout','30m','stdbuf','-o0','-e0',str(emu),'-i',str(image),'--flash='+str(flash),'--ram-size=128MB','--diff='+str(reference),'--max-cycles=2000000','--seed=1']
record=dict(command=command,cwd=str(core),started=now(),files=pins,status='RUNNING',expected_vdot_commits=expected)
save(out/'runtime.json',record)
env=dict(os.environ);env.pop('XS_NEGATIVE_VECTOR_TARGET',None)
with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
    process=subprocess.Popen(command,cwd=core,env=env,stdout=stdout,stderr=stderr)
    record['pid']=process.pid;save(out/'runtime.json',record)
    rc=process.wait()
record.update(exit_code=rc,finished=now(),raw_sha256={n:sha(out/n) for n in ('stdout.log','stderr.log')})
save(out/'runtime.json',record)
try:
    require(rc==0 and all(sha(p)==h for p,h in pins.items()),'runtime failure or input drift')
    stdout=(out/'stdout.log').read_text();stderr=(out/'stderr.log').read_text()
    require(stdout.count('Difftest enabled.')==1 and 'The reference model is '+str(reference) in stdout+stderr,
            'live reference not bound')
    require(stdout.count('HIT GOOD TRAP')==1 and not re.search(r'T13_FAIL|BAD TRAP|Assertion failed|different at pc',stdout+stderr),'runtime failure')
    lines=[s for s in stdout.splitlines() if s.startswith('T13_')]
    require(len(lines)==16 and lines[0]==f"T13_BEGIN suite={manifest['suite']} dataset={manifest['dataset']} plan=12 contract={manifest['contract']}", 'bad program envelope')
    require(lines[-1]=='T13_SUMMARY executed=12 failures=0 scratch_control=1' and
            lines.count('T13_CONTROLS detected=6 expected=6')==1 and lines.count('T13_SCRATCH_CONTROL allowed=1')==1,'state/negative checks missing')
    samples=[s for s in lines if s.startswith('T13_P ')]
    require(len(samples)==12,'missing program sample')
    for i,s in enumerate(samples):
        match=re.fullmatch(r'T13_P seq=([0-9]+) c=([0-9]+) i=([0-9]+)',s)
        require(match is not None and int(match[1])==i and int(match[2])>0 and int(match[3])>0,'invalid/reordered sample')
    require(stdout.index('HIT GOOD TRAP')>stdout.index('T13_SUMMARY'),'premature trap')
    trace=audit(stderr.splitlines(),2,'fullcore');save(out/'trace.json',trace)
    require(trace['rob']['committed']==expected and trace['overlap']>0,'batch failed to exercise full-core handoff')
    record.update(status='O1_BATCH128_HANDOFF_OBSERVATION_PASS',overlap=trace['overlap'],vdot_committed=expected,performance_accepted=False,
                  counter_scope='UART shape/order only; no independent T13 counter-window or speedup claim')
    save(out/'reference-after.json',artifact_guard.verify_nemu(refroot,reference,'reference'))
except Exception as error:record.update(status='FAILED',error=repr(error))
save(out/'result.json',record);print(record['status'],record.get('error',''),flush=True)
raise SystemExit(0 if record['status']!='FAILED' else 1)
