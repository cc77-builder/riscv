"""Preserve the frozen fused audit while bounding its host process durably.

Only the fixed helper's one 180-second isolated Python invocation is adapted.
All guest evidence, source pins, child arguments and acceptance checks remain
those of the original frozen archive engine. No EMU is launched.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace

CONTRACT='r2-s3-fused-offline-audit-host-budget-v1'
TARGET=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target')
HELPER=Path('team/optimizations/o2/r2-config-reuse/caller/fixed-weight/archive.py')
ARCHIVE_SHA='09bfd02664d17d04364876abd5ab8cd3cd17ce5e48d2d3c69f2e64977d9e495d'
HELPER_SHA='2d7f69fc4b99d2f83ee276c7acc24f9a8db16e21b3a0521b7102aecd6cbba578'
HOST_SECONDS=900

def need(condition,message):
    if not condition:raise ValueError(message)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def durable_child(argv,*,cwd,env,seconds,out,diagnostics=()):
    """One owned process group, original exit semantics, logs before acceptance."""
    out.mkdir(parents=True,exist_ok=False)
    receipt=dict(status='RUNNING',command=argv,cwd=str(cwd),started=now(),
                 wall_seconds=seconds,new_emu_runs=0,stdout='stdout.log',stderr='stderr.log')
    save(out/'command.json',receipt)
    child=None
    try:
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
            child=subprocess.Popen(argv,cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            receipt['pid']=child.pid;receipt['owned_process_group']=child.pid;save(out/'command.json',receipt)
            try:
                code=child.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                receipt['timed_out']=True
                try:os.killpg(child.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                raise
        receipt.update(status='EXITED',exit_code=code,timed_out=False)
        return subprocess.CompletedProcess(argv,code,(out/'stdout.log').read_bytes(),(out/'stderr.log').read_bytes())
    except BaseException as error:
        receipt.update(status='TIMED_OUT' if receipt.get('timed_out') else 'FAILED',error=repr(error),
                       exit_code=child.returncode if child is not None else None)
        raise
    finally:
        receipt['finished']=now()
        receipt['raw_sha256']={name:sha(out/name) for name in ('stdout.log','stderr.log') if (out/name).exists()}
        copied={}
        for label,path in diagnostics:
            path=Path(path)
            copied[label]=dict(exists=path.is_file())
            if path.is_file():
                raw=path.read_bytes();(out/label).write_bytes(raw);copied[label].update(bytes=len(raw),sha256=sha(out/label))
        receipt['diagnostics_present_at_exit']=copied
        save(out/'command.json',receipt)

def self_test(out):
    need(not out.exists(),'fresh self-test output');out.mkdir(parents=True)
    cases=[]
    for label,code,delay in (('success',0,0),('failure',7,0),('timeout',0,2)):
        directory=out/label
        script="from pathlib import Path;import sys,time;Path(sys.argv[1]).write_text('guard-original\\n');Path(sys.argv[2]).write_text('audit-original\\n');print('audit-out',flush=True);print('audit-err',file=sys.stderr,flush=True);time.sleep(%s);sys.exit(%s)"%(delay,code)
        with tempfile.TemporaryDirectory(prefix='control-source-',dir=out) as temp:
            source=Path(temp);guard=source/'guard.json';audit_report=source/'audit.json'
            argv=[sys.executable,'-I','-B','-c',script,str(guard),str(audit_report)]
            try:
                result=durable_child(argv,cwd=source,env=dict(os.environ),
                                     seconds=.25 if label=='timeout' else 5,out=directory,
                                     diagnostics=(('guard-at-exit.json',guard),('audit-at-exit.json',audit_report),('missing.json',source/'missing')))
                need(label!='timeout' and result.returncode==code and result.args==argv,'exit semantics preserved')
                need(result.stdout==b'audit-out\n' and result.stderr==b'audit-err\n','original CompletedProcess bytes')
            except subprocess.TimeoutExpired:
                need(label=='timeout','only expected timeout')
        need(not source.exists(),'temporary source actually removed')
        need((directory/'guard-at-exit.json').read_text()=='guard-original\n' and
             (directory/'audit-at-exit.json').read_text()=='audit-original\n','diagnostics survive temporary source removal')
        record=json.loads((directory/'command.json').read_text())
        need((directory/'stdout.log').read_text()=='audit-out\n' and
             (directory/'stderr.log').read_text()=='audit-err\n','all original streams retained')
        need(record['status']==('TIMED_OUT' if label=='timeout' else 'EXITED'),'accurate terminal status')
        need(record['exit_code']==code if label!='timeout' else record['exit_code']<0,'accurate exit code')
        need(record['diagnostics_present_at_exit']['missing.json']==dict(exists=False),'missing diagnostics not invented')
        cases.append(dict(name=label,receipt_sha256=sha(directory/'command.json')))
    result=dict(status='DURABLE_AUDIT_SUCCESS_FAILURE_TIMEOUT_CONTROLS_PASS',contract=CONTRACT,
                adapter_sha256=sha(__file__),cases=cases,new_emu_runs=0)
    save(out/'result.json',result);return result

def audit(repo,archive,out):
    need(not out.exists(),'fresh audit output');need(not out.is_relative_to(repo) and not out.is_relative_to(archive),'output outside inputs')
    need(sha(repo/TARGET/'archive.py')==ARCHIVE_SHA and sha(repo/HELPER)==HELPER_SHA,'unchanged frozen audit engines')
    spec=importlib.util.spec_from_file_location('fused_host_budget_frozen_archive',repo/TARGET/'archive.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    e=module.e;helper=module.helper
    original_pins=e.sources(repo)
    need(len(original_pins)==98,'complete frozen runtime source inventory')
    # Retain exactly the original launcher checks, including physical identity.
    identity=repo/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    cfg=e.parent.parent_identity(repo,identity)['configuration']
    e.parent.outside_inputs(out,[repo,identity.parent,archive]+[cfg[k] for k in ('am_home','hardware_source','build_record')])
    out.mkdir(parents=True);resource=out/'host-resource';resource.mkdir()
    calls=[];real_run=helper.subprocess.run
    frozen_python_sha=sha(sys.executable)
    record=dict(status='RUNNING',contract=CONTRACT,started=now(),adapter_sha256=sha(__file__),
                contract_sha256=sha(Path(__file__).with_name('HOST_AUDIT_CONTRACT.md')),
                frozen_archive_sha256=ARCHIVE_SHA,frozen_helper_sha256=HELPER_SHA,
                original_host_timeout=180,effective_host_timeout=HOST_SECONDS,
                archive_manifest_sha256=sha(archive/'archive-manifest.json'),source_files=original_pins,
                cpu_affinity=sorted(os.sched_getaffinity(0)),new_emu_runs=0)
    save(out/'host-resource.json',record)
    def run(argv,**kwargs):
        if kwargs.get('timeout')!=180:return real_run(argv,**kwargs)
        need(not calls,'exactly one isolated audit child')
        need(set(kwargs)=={'cwd','capture_output','timeout','env'} and kwargs['capture_output'] is True,'exact frozen child invocation')
        source=Path(kwargs['cwd']).resolve()
        need(argv[:3]==[sys.executable,'-I','-B'] and Path(argv[3])==source/helper.GUARD,'exact isolated guard')
        need(sha(source/helper.GUARD)==helper.GUARD_SHA and sha(sys.executable)==frozen_python_sha,'fixed guard and Python')
        need(Path(argv[argv.index('--script')+1])==source/TARGET/'archive.py' and
             sha(source/TARGET/'archive.py')==ARCHIVE_SHA,'exact child audit script')
        need(argv[argv.index('--action')+1]=='audit' and argv.count('--deny-root')==8,'original audit and all denied roots')
        need(all(sha(source/name)==pin for name,pin in original_pins.items()),'archived 98 source bytes unchanged')
        calls.append(dict(command=argv,cwd=str(source),original_timeout=180,effective_timeout=HOST_SECONDS))
        save(resource/'intercept.json',calls)
        diagnostics=[('guard-at-exit.json',Path(argv[argv.index('--report')+1])),
                     ('audit-at-exit.json',Path(argv[argv.index('--output')+1]))]
        return durable_child(argv,cwd=source,env=kwargs['env'],seconds=HOST_SECONDS,
                             out=resource/'child',diagnostics=diagnostics)
    proxy=SimpleNamespace(run=run)
    try:
        with e.adapt(helper,subprocess=proxy):
            result=module.audit_snapshot(archive,out/'fresh-source-audit')
        need(len(calls)==1,'one and only one resource-adjusted child')
        need(e.sources(repo)==original_pins,'all original sources unchanged after audit')
        need(result['status']=='FUSED_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS','original frozen acceptance')
        record.update(status='FROZEN_FUSED_AUDIT_WITH_DURABLE_HOST_BUDGET_PASS',finished=now(),
                      original_result_sha256=sha(out/'fresh-source-audit/result.json'),
                      child_receipt_sha256=sha(resource/'child/command.json'),frozen_sources_unchanged=True)
        save(out/'host-resource.json',record);return record
    except BaseException as error:
        record.update(status='FAILED',finished=now(),error=repr(error),
                      frozen_sources_unchanged=e.sources(repo)==original_pins)
        save(out/'host-resource.json',record);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action',choices=('self-test','audit'),required=True)
    parser.add_argument('--repo',type=Path);parser.add_argument('--archive',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if args.action=='self-test':result=self_test(args.output.resolve())
    else:
        need(args.repo is not None and args.archive is not None,'repo and archive required')
        result=audit(args.repo.resolve(),args.archive.resolve(),args.output.resolve())
    print(json.dumps(result,indent=2))
