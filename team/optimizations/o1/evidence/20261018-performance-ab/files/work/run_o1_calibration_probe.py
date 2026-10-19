from pathlib import Path
import importlib.util,subprocess,hashlib,json,datetime,sys
repo=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
w=Path('/home/riscv/riscv-lab/o1-performance-20261018')
out=w/'o1-calibration-probe-01'
out.mkdir()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
cmp=load('paired',repo/'team/optimizations/o1/performance/compare.py')
check=cmp.load_module('probe_check',repo/'team/workloads/unified-vdot/check.py')
observer=cmp.load_module('probe_observer',repo/'team/optimizations/o1/fullcore/analyze.py')
gate=cmp.load_module('probe_gate',repo/'team/optimizations/o1/audit/runtime_gate.py')
emu=repo/'build/emu'
build=cmp.IMAGE_ROOT/'smoke-d0-s00'
files={str(p):cmp.sha(p) for p in [emu,cmp.REFERENCE,cmp.FLASH,build/'vdot-perf.bin']}
record={'status':'RUNNING','started_utc':cmp.now(),'files':files,'command':['timeout','120m','stdbuf','-o0','-e0',str(emu),'-i',str(build/'vdot-perf.bin'),'--flash='+str(cmp.FLASH),'--ram-size=128MB','--diff='+str(cmp.REFERENCE),'--max-cycles=2000000','--seed=1'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'role':'additional preflight probe, excluded from formal paired statistics'}
cmp.save(out/'runtime.json',record)
with (out/'stdout.log').open('wb') as so,(out/'stderr.log').open('wb') as se:
 record['exit_code']=subprocess.run(record['command'],cwd=repo,stdout=so,stderr=se).returncode
record['raw_sha256']={n:cmp.sha(out/n) for n in ['stdout.log','stderr.log']}
cmp.save(out/'result.json',record)
try:
 cmp.require(record['exit_code']==0,'probe exit failure')
 for n in ['stdout.log','stderr.log']: gate.validate_failure_markers((out/n).read_text())
 windows=check.verify(build,out)
 analysis=observer.analyze((out/'stderr.log').read_text()+(out/'stdout.log').read_text())
 cmp.require(analysis['status']=='O1_TRACE_PASS' and analysis['schema']['handoff']==1,'observer mismatch')
 cmp.require(analysis['counts']['COMMIT']==cmp.expected_commits(json.loads((build/'data/manifest.json').read_text())),'commit count mismatch')
 cmp.verify_hashes(files)
 cmp.save(out/'window-result.json',windows);cmp.save(out/'observation.json',analysis)
 record.update(status='O1_UNIFIED_CALIBRATION_PROBE_PASS',windows=len(windows['samples']),counts=analysis['counts'])
except Exception as exc:
 record.update(status='FAILED',error=repr(exc))
record['finished_utc']=cmp.now()
cmp.save(out/'result.json',record)
print(json.dumps({k:record[k] for k in ['status','exit_code','finished_utc']}))
if 'error' in record: print(record['error'])
sys.exit(0 if record['status']=='O1_UNIFIED_CALIBRATION_PROBE_PASS' else 1)
