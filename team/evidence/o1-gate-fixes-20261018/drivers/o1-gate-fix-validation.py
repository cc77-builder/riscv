import argparse,hashlib,importlib.util,json,pathlib,runpy,subprocess,sys
ROOT=pathlib.Path('/mnt/c/Code/RVInno/riscv')
parser=argparse.ArgumentParser()
parser.add_argument('--output',required=True,type=pathlib.Path)
OUT=parser.parse_args().output
OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(ROOT/'team/optimizations/o1'))
from check_extended import extended_audit,record
from check_trace import require
from check_parent_negative import check as parent_check
from recheck_extended_run import recheck
from audit_extended_negatives import check as audit_mutations
from evidence_output import write_new_json

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def load(path):
    spec=importlib.util.spec_from_file_location('frozen_archive',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

old=ROOT/'team/evidence/o1-complete-20261018'
archive=load(old/'recheck.py')
require(sha(old/'validation.tar.gz')=='ebfb0b7302017699c50a106988944be8038a9c4d8cbdb68f67bbfc3889d84a2c','wrong archive')
raw=OUT/'archive-current-check'
archive.extract('validation.tar.gz',raw)
result=recheck(raw/'runs-01')
require(result==read(old/'recheck.json'),'hardened protocol changed accepted original results')
write_new_json(OUT/'raw-recheck.json',result)
negative=audit_mutations(raw/'runs-01/control/stderr.log',raw/'runs-01/calibration/stderr.log',
                        raw/'runs-01/images/calibration',OUT/'original-15-negatives.json')
require(negative==read(old/'negatives.json'),'prior corruption checks changed')
print('ORIGINAL_13_RUNS_AND_15_NEGATIVES_PASS',flush=True)

mutations=[]
review_targets=read(ROOT/'team/evidence/o1-publication-review-20261018/publication-spec-ftq-redirect.json')
for index in range(8):
    path=raw/f'runs-01/matrix-{index}/stderr.log';lines=path.read_text().splitlines()
    for i,text in enumerate(lines):
        if text.startswith('O2_FTQ_REDIRECT '):
            tag,row=record(text)
            original=next(x['original'] for x in review_targets if x['run']==f'matrix-{index}')
            if text==original:
                require(row['self']==1,'review target is not a self-flush')
                for field in ('ftf','ftv','fto'):
                    changed=dict(row);changed[field]^=1
                    replacement=tag+' '+' '.join(f'{k}={v}' for k,v in changed.items())
                    bad=lines.copy();bad[i]=replacement
                    try:extended_audit(bad)
                    except ValueError as error:
                        require('FTQ self-flush target identity mismatch' in str(error),'wrong rejection: '+str(error))
                        mutations.append(dict(run=f'matrix-{index}',field=field,original=text,mutated=replacement,
                                              status='REJECTED',reason=str(error),source_sha256=sha(path)))
                    else:raise ValueError('FTQ corruption escaped')
                break
    else:raise ValueError('no target self-flush')
write_new_json(OUT/'ftq-24-negatives.json',dict(count=len(mutations),tests=mutations))
print('REAL_FTQ_24_NEGATIVES_PASS',flush=True)

# Real raw input cannot be selected as the result path, even after authentication.
log=raw/'runs-01/control/stderr.log';before=sha(log)
command=[sys.executable,'-OO','-B',str(ROOT/'team/optimizations/o1/recheck_extended_run.py'),
         '--run',str(raw/'runs-01'),'--output',str(log)]
run=subprocess.run(command,capture_output=True,text=True)
(OUT/'clobber-rejected.log').write_text(run.stdout+run.stderr)
require(run.returncode!=0 and 'Use a new evidence output' in run.stderr and sha(log)==before,'clobber not prevented')
write_new_json(OUT/'clobber-rejected.json',dict(command=command,exit_code=run.returncode,input_sha256=before,unchanged=True))

# Replay already frozen real parent binaries, then apply the new exact reason gate.
command=[sys.executable,'-OO','-B',str(ROOT/'team/evidence/o1-parent-20261018/replay.py'),
         '--output',str(OUT/'parent-replay')]
with (OUT/'parent-replay-launch.log').open('wb') as log:
    run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
require(run.returncode==0,'real parent replay failed')
checks=[]
for fault in ('identity','wen','high','cancel'):
    log=OUT/'parent-replay'/f'inject-{fault}.log'
    checks.append(dict(parent_check(fault,1,log.read_text()),log_sha256=sha(log)))
write_new_json(OUT/'parent-strict-negatives.json',dict(real_archived_parent_modes=3,real_fault_runs=4,
                old_clock_defect_replayed=True,checks=checks,new_cpu_runs=0))
print('REAL_PARENT_REPLAY_STRICT_NEGATIVES_PASS',flush=True)

# Current native build remains valid under the stronger dependency-only gate.
binding=read(raw/'core-build/source-binding.json')
helper=runpy.run_path(str(ROOT/'team/scripts/prepare-core-baseline.py'))
helper['verify_dependencies'](pathlib.Path(binding['build_copy']),binding['modules'])
write_new_json(OUT/'native-dependencies.json',dict(status='STRICT_DEPENDENCIES_PASS',modules=len(binding['modules']),
    source_binding_sha256=sha(raw/'core-build/source-binding.json'),native_copy=binding['build_copy']))
print('NATIVE_DEPENDENCIES_PASS',len(binding['modules']),flush=True)

# A separate real yunsuan fixture from the review now fails at verification.
repro=read(ROOT/'team/evidence/o1-publication-review-20261018/standards-repro/dependency.json')
fixture=pathlib.Path(repro['output'])
# build-copy.txt is authoritative; do not reconstruct a destructive path.
target=pathlib.Path((fixture/'pack/build-copy.txt').read_text().strip())
try:helper['verify'](fixture/'source',fixture/'pack',target)
except RuntimeError as error:
    require('Untracked dependency inputs' in str(error),'wrong dependency rejection')
    write_new_json(OUT/'original-dependency-repro-rejected.json',dict(status='REJECTED',reason=str(error),fixture=str(fixture)))
else:raise ValueError('dependency reproduction still accepted')
write_new_json(OUT/'completion.json',dict(status='O1_GATE_FIX_VALIDATION_PASS',new_cpu_runs=0,archived_cpu_runs_rechecked=13,
    real_parent_binary_runs=8,ftq_mutations=24,prior_mutations=15,default_o1=False))
print('O1_GATE_FIX_VALIDATION_PASS',flush=True)
