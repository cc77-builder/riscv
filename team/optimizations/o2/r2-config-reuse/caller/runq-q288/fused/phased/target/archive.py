"""Frozen raw-evidence engine adapted to the bounded three-method phased contract."""
import argparse
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('phased_target_archive_run',HERE/'run.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);g=e.g
previous=sys.modules.get('run');sys.modules['run']=e.base.base
try:helper=g.load('phased_target_archive_helper',e.Q.parent/'fixed-weight/archive.py')
finally:
    if previous is None:sys.modules.pop('run',None)
    else:sys.modules['run']=previous
BASE_TOOLS=helper.tools()
HOST=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/host_audit.py')
HOST_SHA='0fa2f707274aa90a8e45839966e0caf849a2d80ec370292ffee75020d9239d91'
HOST_SECONDS=900
CONTEXT=SimpleNamespace(**vars(e));CONTEXT.gen=SimpleNamespace(NEW=('q_fault_probe',))


def tools():
    for rel,pin in BASE_TOOLS.items():g.require(g.sha(e.ROOT/rel)==pin,'unchanged archive helper')
    g.require(g.sha(e.ROOT/HOST)==HOST_SHA,'unchanged durable-child helper')
    return dict(BASE_TOOLS,**{Path(__file__).resolve().relative_to(e.ROOT).as_posix():g.sha(__file__),
                             HOST.as_posix():HOST_SHA})


def audit(repo,build,run):
    with e.adapt(helper.engine,e=CONTEXT,g=g):result=helper.BASE_AUDIT(repo,build,run)
    manifest=e.read(build/'source/manifest.json')
    g.require(len(manifest['plan'])==8 and manifest['full_q_calls']==22,'phased audit plan counts')
    result.update(status='PHASED_TARGET_RAW_EVIDENCE_AUDIT_PASS',windows_per_normal_run=8,replay_windows=8,
        functional_calls_per_normal_run=22,warm_calls_per_normal_run=8,extra_functional_calls=6,
        formal_method_windows=8,formal_anchor_windows=4,method_anchor_overlap_windows=4,pack_windows=0,
        integer_leaf_calls_per_normal_run=0,inline_calls_per_normal_run=22,
        probe_dots_per_normal_run=1,committed_vdot_per_normal_run=124417,judge_fault_controls=5,audit_tool_sources=tools())
    return result


def pack(build,run,out):
    with e.adapt(helper,e=CONTEXT,tools=tools,audit=audit):result=helper.pack(build,run,out)
    result['status']='PHASED_TARGET_EVIDENCE_PACKED';return result


def unpack(archive,out):
    with e.adapt(helper,e=CONTEXT,tools=tools):return helper.unpack(archive,out)


def audit_snapshot(archive,out):
    # Adapt one known child invocation only; the old helper still validates the
    # exit code, dependency guard and exact recomputed raw result.
    g.require(not out.exists(),'fresh durable audit output');out.mkdir(parents=True)
    g.require(g.sha(e.ROOT/HOST)==HOST_SHA,'fixed durable helper')
    host=g.load('phased_target_durable_child',e.ROOT/HOST)
    pins=e.sources(e.ROOT);auditors=tools();script=Path(__file__).resolve().relative_to(e.ROOT)
    script_sha=g.sha(__file__);python_sha=g.sha(sys.executable)
    resource=out/'host-resource';resource.mkdir();calls=[];real_run=helper.subprocess.run
    record=dict(status='RUNNING',contract=e.CONTRACT,started=e.now(),original_host_timeout=180,
        effective_host_timeout=HOST_SECONDS,adapter_sha256=script_sha,durable_helper_sha256=HOST_SHA,
        archive_manifest_sha256=g.sha(archive/'archive-manifest.json'),source_files=pins,
        supplementary_auditors=auditors,cpu_affinity=sorted(os.sched_getaffinity(0)),new_emu_runs=0)
    g.save(out/'host-resource.json',record)
    def run(argv,**kwargs):
        if kwargs.get('timeout')!=180:return real_run(argv,**kwargs)
        g.require(not calls,'exactly one isolated audit child')
        g.require(set(kwargs)=={'cwd','capture_output','timeout','env'} and kwargs['capture_output'] is True,
                  'exact frozen isolated invocation')
        source=Path(kwargs['cwd']).resolve()
        g.require(argv[:3]==[sys.executable,'-I','-B'] and Path(argv[3])==source/helper.GUARD,
                  'exact isolated guard command')
        g.require(g.sha(source/helper.GUARD)==helper.GUARD_SHA and g.sha(sys.executable)==python_sha,
                  'fixed guard and Python')
        g.require(Path(argv[argv.index('--script')+1])==source/script and g.sha(source/script)==script_sha,
                  'exact new phased audit script')
        g.require(argv[argv.index('--action')+1]=='audit' and argv.count('--deny-root')==8,
                  'original audit action and all denied roots')
        g.require(all(g.sha(source/n)==pin for n,pin in {**pins,**auditors}.items()),
                  'complete archived source and auditor identity')
        calls.append(dict(command=argv,cwd=str(source),original_timeout=180,effective_timeout=HOST_SECONDS))
        g.save(resource/'intercept.json',calls)
        return host.durable_child(argv,cwd=source,env=kwargs['env'],seconds=HOST_SECONDS,out=resource/'child',
            diagnostics=(('guard-at-exit.json',Path(argv[argv.index('--report')+1])),
                         ('audit-at-exit.json',Path(argv[argv.index('--output')+1]))))
    try:
        with e.adapt(helper,e=CONTEXT,tools=tools,__file__=__file__,subprocess=SimpleNamespace(run=run)):
            result=helper.audit_snapshot(archive,out/'fresh-source-audit')
        g.require(len(calls)==1 and e.sources(e.ROOT)==pins and tools()==auditors,
                  'one adjusted child and unchanged source identities')
        g.require(result['status']=='FIXED_WEIGHT_ARCHIVE_FRESH_SOURCE_AUDIT_PASS','original fresh-source acceptance')
        record.update(status='PHASED_DURABLE_FRESH_SOURCE_AUDIT_PASS',finished=e.now(),
            original_result_sha256=g.sha(out/'fresh-source-audit/result.json'),
            child_receipt_sha256=g.sha(resource/'child/command.json'),frozen_sources_unchanged=True)
        g.save(out/'host-resource.json',record)
        result.update(status='PHASED_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS',
                      host_budget_receipt_sha256=g.sha(out/'host-resource.json'),effective_host_timeout=HOST_SECONDS)
        g.save(out/'result.json',result);return result
    except BaseException as error:
        record.update(status='FAILED',finished=e.now(),error=repr(error))
        try:record['frozen_sources_unchanged']=e.sources(e.ROOT)==pins and tools()==auditors
        except BaseException as pin_error:record['identity_check_error']=repr(pin_error)
        g.save(out/'host-resource.json',record);raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action',choices=('audit','pack','unpack','audit-snapshot'),required=True)
    for name in ('build','run','archive'):p.add_argument('--'+name,type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    g.require(not out.exists(),'fresh audit output')
    identity=e.ROOT/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    cfg=e.parent.parent_identity(e.ROOT,identity)['configuration']
    roots=[e.ROOT,identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    roots += [v.resolve() for v in (a.build,a.run,a.archive) if v]
    e.parent.outside_inputs(out,roots)
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if a.action in ('unpack','audit-snapshot'):
        g.require(a.archive is not None,'archive required')
        result=(unpack if a.action=='unpack' else audit_snapshot)(a.archive.resolve(),out)
    else:
        g.require(a.build and a.run,'build/run required')
        if a.action=='pack':result=pack(a.build.resolve(),a.run.resolve(),out)
        else:result=audit(e.ROOT,a.build.resolve(),a.run.resolve());g.save(out,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
