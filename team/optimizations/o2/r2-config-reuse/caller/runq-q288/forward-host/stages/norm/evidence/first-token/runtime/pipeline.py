from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, os, signal, sys, time, traceback
sys.dont_write_bytecode = True
REPO=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source')
PREV=REPO.parents[1]/'runs/norm-resume-20261027-2000'
OUT=REPO.parents[1]/'runs/first-token-close-20261028-1127'
REL=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/norm/target')
spec=importlib.util.spec_from_file_location('first_token_evidence',REPO/REL/'evidence.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
assert e.sha(REPO/REL/'evidence.py')=='a4dcff0588ae8947a3c46df56506e8b4d9e27906082e3d14e7e15869ba5bb4b9'
assert set(os.sched_getaffinity(0))=={0,1,2,3}
signal.signal(signal.SIGTERM,e.interrupted);signal.signal(signal.SIGINT,e.interrupted)
def deadline(signum,frame):raise TimeoutError('declared offline stage deadline')
signal.signal(signal.SIGALRM,deadline)
state=dict(operation_id='20261028-LiZufan001-first-token-close-1127',status='RUNNING',started=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),cpu_affinity=sorted(os.sched_getaffinity(0)),steps={},new_emu_runs=0,new_reference_runs=0,performance_qualified=False)
def save():e.save(OUT/'pipeline-state.json',state)
def step(name,seconds,action):
    state['active']=name;state['steps'][name]=dict(status='RUNNING',started=time.time(),deadline_seconds=seconds);save()
    signal.alarm(seconds)
    try:
        result=action();state['steps'][name].update(status='PASS',finished=time.time(),result=result);save();return result
    finally:signal.alarm(0)
save()
try:
    seal=OUT/'evidence-01'
    extra=['profile='+str(PREV/'first-token-pc-profile-02'),'profile-failed='+str(PREV/'first-token-pc-profile-01'),'offline-mechanisms='+str(PREV/'offline-parallel-mechanism-01'),'diagnostics='+str(PREV/'first-token-diagnostics-01'),'prior-build-01='+str(PREV/'first-token-build-01'),'prior-build-02='+str(PREV/'first-token-build-02'),'prior-reference-01='+str(PREV/'first-token-reference-01'),'prior-reference-02='+str(PREV/'first-token-reference-02'),'prior-freeze-source='+str(PREV/'first-token-freeze-01-source')]
    args=argparse.Namespace(repo=REPO,build=PREV/'first-token-build-03',norm_build=REPO.parents[1]/'runs/forward-norm-20261027-1536/build-04',reference=PREV/'first-token-reference-03',target=PREV/'first-token-target-01',parent_evidence=PREV/'norm-evidence-01',output=seal,extra=extra)
    archive=step('seal',3600,lambda:e.seal(args))
    restored=OUT/'restored-01'
    report=step('restore',3600,lambda:e.t.verify(seal/'archive/payload.zip',restored,archive['archive_sha256']))
    e.save(OUT/'restore-verification.json',report)
    manifest=seal/'archive/manifest.json'
    audit_args=argparse.Namespace(root=restored,output=OUT/'audit-01',manifest=manifest,expected_manifest_sha256=e.sha(manifest),jobs=4)
    final=step('raw-recheck',21600,lambda:e.recheck(audit_args))
    assert final['status']=='FIRST_TOKEN_ARCHIVE_RAW_RECHECK_PASS'
    state.update(status='PASS',active=None,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),target_correctness_qualified=True,full_retirement_window_audited=False)
    save()
    print(json.dumps(dict(status=state['status'],archive=archive,recheck=final),indent=2))
except BaseException as error:
    state.update(status='FAILED',error=repr(error),traceback=traceback.format_exc(),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save();raise
