"""Reuse frozen raw-audit and fresh-source engines for the ten-Q target contract."""
import argparse
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
# The old archive helpers use an unqualified 'import run'. Bind that import to
# their actual Q288 parent while loading; every target call uses CONTEXT below.
import importlib.util
spec = importlib.util.spec_from_file_location('acc8_target_archive_run', HERE/'run.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
g = e.g
previous = sys.modules.get('run')
sys.modules['run'] = e.base
try:
    helper = g.load('acc8_target_archive_helper', e.Q.parent/'fixed-weight/archive.py')
finally:
    if previous is None: sys.modules.pop('run', None)
    else: sys.modules['run'] = previous
BASE_TOOLS = helper.tools()
CONTEXT = SimpleNamespace(**vars(e))
CONTEXT.gen = SimpleNamespace(NEW=('q_fault_probe',))


def tools():
    for rel, pin in BASE_TOOLS.items():
        g.require(g.sha(e.ROOT/rel) == pin, 'unchanged target archive helper')
    return dict(BASE_TOOLS, **{Path(__file__).resolve().relative_to(e.ROOT).as_posix():g.sha(__file__)})


def audit(repo, build, run):
    with e.adapt(helper.engine, e=CONTEXT, g=g):
        result = helper.BASE_AUDIT(repo, build, run)
    manifest = e.read(build/'source/manifest.json')
    result.update(status='ACC8_TARGET_RAW_EVIDENCE_AUDIT_PASS',
        windows_per_normal_run=11, replay_windows=11, formal_method_windows=0, formal_anchor_windows=0,
        pack_windows=1, cost_observation_windows=10, functional_calls_per_normal_run=10,
        full_q_calls_per_normal_run=10, integer_leaf_calls_per_normal_run=3240,
        probe_dots_per_normal_run=1, committed_vdot_per_normal_run=51841,
        performance_qualified=False, audit_tool_sources=tools())
    g.require(len(manifest['plan']) == 11 and manifest['full_q_calls'] == 10, 'target audit plan counts')
    return result


def pack(build, run, out):
    with e.adapt(helper, e=CONTEXT, tools=tools, audit=audit):
        result = helper.pack(build, run, out)
    result['status'] = 'ACC8_TARGET_EVIDENCE_PACKED'
    return result


def unpack(archive, out):
    with e.adapt(helper, e=CONTEXT, tools=tools):
        return helper.unpack(archive, out)


def audit_snapshot(archive, out):
    # Reuse the unchanged parent's dependency-denied child launcher. Its file
    # locator selects this adapter as the child, so the new contract is audited.
    with e.adapt(helper, e=CONTEXT, tools=tools, __file__=__file__):
        result = helper.audit_snapshot(archive, out)
    result['status'] = 'ACC8_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS'
    g.save(out/'result.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action', choices=('audit','pack','unpack','audit-snapshot'), required=True)
    for name in ('build','run','archive'): p.add_argument('--'+name, type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); out = args.output.resolve()
    g.require(not out.exists(), 'fresh target audit output')
    identity = e.ROOT/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    cfg = e.parent.parent_identity(e.ROOT, identity)['configuration']
    roots = [e.ROOT, identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    roots += [v.resolve() for v in (args.build,args.run,args.archive) if v]
    e.parent.outside_inputs(out, roots)
    if os.name == 'posix': os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    if args.action in ('unpack','audit-snapshot'):
        g.require(args.archive is not None, 'archive required')
        result = (unpack if args.action == 'unpack' else audit_snapshot)(args.archive.resolve(), out)
    else:
        g.require(args.build and args.run, 'build/run required')
        if args.action == 'pack': result = pack(args.build.resolve(), args.run.resolve(), out)
        else:
            result = audit(e.ROOT, args.build.resolve(), args.run.resolve()); g.save(out, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
