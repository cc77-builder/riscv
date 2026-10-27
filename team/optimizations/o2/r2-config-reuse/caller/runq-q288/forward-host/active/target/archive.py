"""Unchanged raw archive engine adapted to the new complete QKV contract."""
import argparse
import json
import os
from pathlib import Path
import sys
import zipfile
from types import SimpleNamespace
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tail_target_archive_run',HERE/'run.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);g=e.g
previous=sys.modules.get('run');sys.modules['run']=e.tail.base.base
try:helper=g.load('tail_target_archive_helper',e.Q.parent/'fixed-weight/archive.py')
finally:
    if previous is None:sys.modules.pop('run',None)
    else:sys.modules['run']=previous
BASE_TOOLS=helper.tools()
HOST=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/host_audit.py')
HOST_SHA='0fa2f707274aa90a8e45839966e0caf849a2d80ec370292ffee75020d9239d91'
HOST_SECONDS=900
CONTEXT=SimpleNamespace(**vars(e.tail));CONTEXT.__dict__.update(vars(e));CONTEXT.gen=SimpleNamespace(NEW=('q_fault_probe',))


def tools():
    for rel,pin in BASE_TOOLS.items():g.require(g.sha(e.ROOT/rel)==pin,'unchanged archive helper')
    g.require(g.sha(e.ROOT/HOST)==HOST_SHA,'unchanged durable-child helper')
    return dict(BASE_TOOLS,**{Path(__file__).resolve().relative_to(e.ROOT).as_posix():g.sha(__file__),
                             HOST.as_posix():HOST_SHA})


def audit(repo,build,run):
    with e.adapt(helper.engine,e=CONTEXT,g=g):result=helper.BASE_AUDIT(repo,build,run)
    manifest=e.read(build/'source/manifest.json')
    g.require(len(manifest['plan'])==6 and manifest['full_q_calls']==42,'QKV audit plan counts')
    result.update(status='ACTUAL_QKV_TARGET_RAW_EVIDENCE_AUDIT_PASS',windows_per_normal_run=6,replay_windows=6,
        functional_calls_per_normal_run=42,boundary_calls_per_normal_run=14,
        warm_calls_per_normal_run=18,extra_functional_calls=6,timed_projection_calls_per_normal_run=18,
        warm_boundaries_per_normal_run=6,extra_functional_boundaries_per_normal_run=2,
        formal_method_windows=6,formal_anchor_windows=4,method_anchor_overlap_windows=4,pack_windows=0,
        integer_leaf_calls_per_normal_run=0,inline_calls_per_normal_run=42,
        probe_dots_per_normal_run=1,committed_vdot_per_normal_run=155521,judge_fault_controls=6,audit_tool_sources=tools())
    return result


def pack(build,run,out):
    with e.adapt(helper,e=CONTEXT,tools=tools,audit=audit):result=helper.pack(build,run,out)
    result['status']='ACTUAL_QKV_TARGET_EVIDENCE_PACKED';return result


def unpack(archive,out):
    with e.adapt(helper,e=CONTEXT,tools=tools):return helper.unpack(archive,out)


def support(root,stage,out):
    """Keep failed/pre-final inputs and ELF controls apart from qualified runs."""
    g.require(not out.exists(),'fresh support archive')
    labels=('target-input-01','target-input-02','target-input-03',
            'target-build-01','target-build-02','target-elf-controls-01')
    selected=[];directories=[]
    for label in labels:
        directory=root/label;g.require(directory.is_dir(),'retained diagnostic directory '+label)
        files=[]
        for p in sorted(directory.rglob('*')):
            g.require(not p.is_symlink(),'no support evidence symlinks')
            if p.is_file() and '__pycache__' not in p.parts:files.append(p)
        directories.append(dict(path=label,files=len(files),raw_bytes=sum(p.stat().st_size for p in files)))
        selected.extend(('run/'+p.relative_to(root).as_posix(),p) for p in files)
    for p in sorted(root.iterdir()):
        if p.is_file() and p.name.startswith(('target-input-','target-build-','target-elf-controls-',
                                             'target-campaign-01.')):
            selected.append(('run/'+p.name,p))
    for name in ('prepare-reviewed.py',*(f'target-files-{i:02}.json' for i in range(1,6))):
        p=stage/name;g.require(p.is_file(),'retained exact transport source '+name)
        selected.append(('staging/'+name,p))
    selected.append(('auditor/archive.py',Path(__file__).resolve()))
    g.require(len({name for name,_ in selected})==len(selected),'unique support members')
    out.mkdir(parents=True);rows=[]
    with zipfile.ZipFile(out/'raw.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(selected):
            g.require(not p.is_symlink(),'regular support evidence')
            raw=p.read_bytes();info=zipfile.ZipInfo(name,(2026,10,26,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw,compresslevel=9)
            rows.append(dict(path=name,bytes=len(raw),sha256=e.digest(raw)))
    manifest=dict(format='active-qkv-support-raw-v1',contract=e.CONTRACT,files=rows,directories=directories,
        original_run_root=str(root),transport_root=str(stage),auditor_sha256=g.sha(__file__),
        raw_bytes=sum(row['bytes'] for row in rows),stored_bytes=(out/'raw.zip').stat().st_size,
        payload_sha256=g.sha(out/'raw.zip'),new_emu_runs=0,original_evidence_retained=True,
        scope='failed preparation/build, unmeasured intermediate build, final input preparation and ELF/selector controls')
    with zipfile.ZipFile(out/'raw.zip') as z:
        g.require(len(z.namelist())==len(rows) and set(z.namelist())=={r['path'] for r in rows},'support ZIP inventory')
        for row in rows:
            raw=z.read(row['path'])
            g.require(len(raw)==row['bytes'] and e.digest(raw)==row['sha256'],'support member identity '+row['path'])
    g.require(all(g.sha(p)==row['sha256'] for (_,p),row in zip(sorted(selected),rows)),
              'support source bytes unchanged during seal')
    g.save(out/'manifest.json',manifest)
    result=dict(status='ACTUAL_QKV_SUPPORT_EVIDENCE_SEALED',files=len(rows),
        raw_bytes=manifest['raw_bytes'],stored_bytes=manifest['stored_bytes'],payload_sha256=manifest['payload_sha256'],
        manifest_sha256=g.sha(out/'manifest.json'),new_emu_runs=0)
    g.save(out/'result.json',result);return result


def audit_snapshot(archive,out):
    # Adapt one known child invocation only; the old helper still validates the
    # exit code, dependency guard and exact recomputed raw result.
    g.require(not out.exists(),'fresh durable audit output');out.mkdir(parents=True)
    g.require(g.sha(e.ROOT/HOST)==HOST_SHA,'fixed durable helper')
    host=g.load('tail_target_durable_child',e.ROOT/HOST)
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
                  'exact new QKV audit script')
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
        record.update(status='QKV_DURABLE_FRESH_SOURCE_AUDIT_PASS',finished=e.now(),
            original_result_sha256=g.sha(out/'fresh-source-audit/result.json'),
            child_receipt_sha256=g.sha(resource/'child/command.json'),frozen_sources_unchanged=True)
        g.save(out/'host-resource.json',record)
        result.update(status='ACTUAL_QKV_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS',
                      host_budget_receipt_sha256=g.sha(out/'host-resource.json'),effective_host_timeout=HOST_SECONDS)
        g.save(out/'result.json',result);return result
    except BaseException as error:
        record.update(status='FAILED',finished=e.now(),error=repr(error))
        try:record['frozen_sources_unchanged']=e.sources(e.ROOT)==pins and tools()==auditors
        except BaseException as pin_error:record['identity_check_error']=repr(pin_error)
        g.save(out/'host-resource.json',record);raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action',choices=('audit','pack','unpack','audit-snapshot','support'),required=True)
    for name in ('build','run','archive','support-root','stage'):p.add_argument('--'+name,type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    g.require(not out.exists(),'fresh audit output')
    identity=e.ROOT/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    cfg=e.parent.parent_identity(e.ROOT,identity)['configuration']
    roots=[e.ROOT,identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    roots += [v.resolve() for v in (a.build,a.run,a.archive,a.support_root,a.stage) if v]
    e.parent.outside_inputs(out,roots)
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if a.action=='support':
        g.require(a.support_root is not None and a.stage is not None,'support input roots required')
        result=support(a.support_root.resolve(),a.stage.resolve(),out)
    elif a.action in ('unpack','audit-snapshot'):
        g.require(a.archive is not None,'archive required')
        result=(unpack if a.action=='unpack' else audit_snapshot)(a.archive.resolve(),out)
    else:
        g.require(a.build and a.run,'build/run required')
        if a.action=='pack':result=pack(a.build.resolve(),a.run.resolve(),out)
        else:result=audit(e.ROOT,a.build.resolve(),a.run.resolve());g.save(out,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

