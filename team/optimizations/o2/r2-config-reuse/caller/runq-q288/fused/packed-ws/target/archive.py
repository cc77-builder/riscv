"""New contract summary over the unchanged raw-evidence and durable audit engines."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import importlib.util
import json
import os

HERE = Path(__file__).resolve().parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
e = load('ws_archive_run',HERE/'run.py'); g = e.g
frozen = load('ws_frozen_tail_archive',e.Q/'fused/phased/tail/target/archive.py')
helper = frozen.helper
CONTEXT = SimpleNamespace(**vars(e)); CONTEXT.gen = SimpleNamespace(NEW=('q_fault_probe',))


def tools():
    for relative,pin in frozen.BASE_TOOLS.items():
        g.require(g.sha(e.ROOT/relative) == pin, 'unchanged archive helper')
    g.require(g.sha(e.ROOT/frozen.HOST) == frozen.HOST_SHA, 'unchanged durable-child helper')
    own = Path(__file__).resolve().relative_to(e.ROOT).as_posix()
    return dict(frozen.BASE_TOOLS,**{own:g.sha(__file__),frozen.HOST.as_posix():frozen.HOST_SHA})


def audit(repo, build, run):
    with e.adapt(helper.engine,e=CONTEXT,g=g):
        result = helper.BASE_AUDIT(repo,build,run)
    manifest = e.read(build/'source/manifest.json')
    g.require(len(manifest['plan']) == 12 and manifest['full_q_calls'] == 32, 'packed-scale audit plan counts')
    result.update(status='PACKED_WS_TARGET_RAW_EVIDENCE_AUDIT_PASS',windows_per_normal_run=12,replay_windows=12,
        functional_calls_per_normal_run=32,warm_calls_per_normal_run=12,extra_functional_calls=8,
        formal_method_windows=12,formal_anchor_windows=8,method_anchor_overlap_windows=8,pack_windows=0,
        integer_leaf_calls_per_normal_run=0,inline_calls_per_normal_run=32,
        probe_dots_per_normal_run=1,committed_vdot_per_normal_run=124417,judge_fault_controls=10,
        scale_pack_calls_per_normal_run=1,scale_pack_controls=3,scale_pack_cost_measured=False,audit_tool_sources=tools())
    return result


def pack(build, run, out):
    with e.adapt(helper,e=CONTEXT,tools=tools,audit=audit):
        result = helper.pack(build,run,out)
    result['status'] = 'PACKED_WS_TARGET_EVIDENCE_PACKED'
    return result


def unpack(archive, out):
    with e.adapt(helper,e=CONTEXT,tools=tools):
        return helper.unpack(archive,out)


def audit_snapshot(archive, out):
    # Reuse the existing 900-second durable child, eight denied original roots,
    # exact dependency guard and raw-result equality without editing that tool.
    with e.adapt(frozen,e=e,CONTEXT=CONTEXT,tools=tools,__file__=__file__):
        result = frozen.audit_snapshot(archive,out)
    result.update(status='PACKED_WS_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS',
        reused_durable_adapter='team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/tail/target/archive.py')
    g.save(out/'result.json',result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action',choices=('audit','pack','unpack','audit-snapshot'),required=True)
    for name in ('build','run','archive'): parser.add_argument('--'+name,type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); out = args.output.resolve()
    g.require(not out.exists(), 'fresh audit output')
    identity = e.ROOT/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    cfg = e.parent.parent_identity(e.ROOT,identity)['configuration']
    roots = [e.ROOT,identity.parent] + [cfg[k] for k in ('am_home','hardware_source','build_record')]
    roots += [v.resolve() for v in (args.build,args.run,args.archive) if v]
    e.parent.outside_inputs(out,roots)
    if os.name == 'posix': os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if args.action in ('unpack','audit-snapshot'):
        g.require(args.archive is not None, 'archive required')
        result = (unpack if args.action == 'unpack' else audit_snapshot)(args.archive.resolve(),out)
    else:
        g.require(args.build and args.run, 'build/run required')
        if args.action == 'pack': result = pack(args.build.resolve(),args.run.resolve(),out)
        else: result = audit(e.ROOT,args.build.resolve(),args.run.resolve()); g.save(out,result)
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
