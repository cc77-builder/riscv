"""Frozen raw-evidence engine adapted to the complete-Q fusion contract."""
import argparse
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fused_target_archive_run',HERE/'run.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);g=e.g
previous=sys.modules.get('run');sys.modules['run']=e.base.base
try:helper=g.load('fused_target_archive_helper',e.Q.parent/'fixed-weight/archive.py')
finally:
    if previous is None:sys.modules.pop('run',None)
    else:sys.modules['run']=previous
BASE_TOOLS=helper.tools()
CONTEXT=SimpleNamespace(**vars(e));CONTEXT.gen=SimpleNamespace(NEW=('q_fault_probe',))


def tools():
    for rel,pin in BASE_TOOLS.items():g.require(g.sha(e.ROOT/rel)==pin,'unchanged archive helper')
    return dict(BASE_TOOLS,**{Path(__file__).resolve().relative_to(e.ROOT).as_posix():g.sha(__file__)})


def audit(repo,build,run):
    with e.adapt(helper.engine,e=CONTEXT,g=g):result=helper.BASE_AUDIT(repo,build,run)
    manifest=e.read(build/'source/manifest.json')
    g.require(len(manifest['plan'])==12 and manifest['full_q_calls']==28,'fused audit plan counts')
    result.update(status='FUSED_TARGET_RAW_EVIDENCE_AUDIT_PASS',windows_per_normal_run=12,replay_windows=12,
        functional_calls_per_normal_run=28,warm_calls_per_normal_run=12,extra_functional_calls=4,
        formal_method_windows=12,formal_anchor_windows=4,method_anchor_overlap_windows=4,pack_windows=0,
        integer_leaf_calls_per_normal_run=5184,fused_calls_per_normal_run=12,
        probe_dots_per_normal_run=1,committed_vdot_per_normal_run=103681,judge_fault_controls=5,audit_tool_sources=tools())
    return result


def pack(build,run,out):
    with e.adapt(helper,e=CONTEXT,tools=tools,audit=audit):result=helper.pack(build,run,out)
    result['status']='FUSED_TARGET_EVIDENCE_PACKED';return result


def unpack(archive,out):
    with e.adapt(helper,e=CONTEXT,tools=tools):return helper.unpack(archive,out)


def audit_snapshot(archive,out):
    with e.adapt(helper,e=CONTEXT,tools=tools,__file__=__file__):result=helper.audit_snapshot(archive,out)
    result['status']='FUSED_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS';g.save(out/'result.json',result);return result


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
