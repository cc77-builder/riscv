#!/usr/bin/env python3
"""Run a new dot16 parent campaign, retaining the frozen O2 runner/checkers."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HELPER_SHA256 = 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mill-output', type=Path, required=True)
    p.add_argument('--feature', type=int, choices=(0, 1), required=True)
    p.add_argument('--expected-head', required=True)
    p.add_argument('--cpu', type=int, choices=range(4), default=1)
    p.add_argument('--budget-seconds', type=int, default=900)
    a = p.parse_args()
    sys.dont_write_bytecode = True
    here = Path(__file__).resolve().parent
    helper = here.parent/'run_fu.py'
    if hashlib.sha256(helper.read_bytes()).hexdigest() != HELPER_SHA256:
        p.error('reviewed FU execution helper changed')
    util = module(helper, 'frozen_dot16_execution_helper')
    repo, out, cache = a.repo.resolve(), a.output.resolve(), a.mill_output.resolve()
    if not a.output.is_absolute() or out.exists() or out.is_relative_to(repo) or repo.is_relative_to(out):
        p.error('run output must be new, absolute and outside the checkout')
    if not a.mill_output.is_absolute() or Path(os.path.abspath(a.mill_output)) != cache:
        p.error('Mill cache must be an absolute path with no symbolic-link component')
    if cache != repo/util.IN_TREE_MILL_CACHE or not cache.is_dir():
        p.error('reuse only the reviewed real, ignored Mill cache')
    if subprocess.run(['git', '-C', str(repo), 'check-ignore', '-q', '--', str(util.IN_TREE_MILL_CACHE)]).returncode:
        p.error('Mill cache is not already ignored')
    if a.expected_head != util.EXPECTED_HEAD or not 30 <= a.budget_seconds <= 900:
        p.error('new source pin or budget over 900 seconds needs a new reviewed contract')
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    os.sched_setaffinity(0, {a.cpu})
    out.mkdir(parents=True)
    status = dict(schema=1, started=util.stamp(), passed=False, feature=a.feature,
                  cpu_affinity=sorted(os.sched_getaffinity(0)), budget_seconds=a.budget_seconds,
                  repo=str(repo), output=str(out), mill_output=str(cache),
                  parent_qualified=False, decode_qualified=False,
                  fullcore_qualified=False, ppa_qualified=False)
    proc = None
    try:
        head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        status['head'] = head
        if head != a.expected_head:
            raise ValueError('checkout HEAD differs from expected pin')
        manifest = json.loads((here.parent/'source-manifest.json').read_text())
        if util.digest(here.parent/'candidate.patch') != util.PATCH_SHA256 or manifest['patch_sha256'] != util.PATCH_SHA256:
            raise ValueError('production patch identity mismatch')
        guards = manifest['apply_result'] | manifest['unchanged_dependency_sha256']
        if any(util.digest(repo/n) != h for n, h in guards.items()):
            raise ValueError('production candidate differs from reviewed six-path patch')
        frozen = ['team/optimizations/o2/run_rtl.py',
                  *['team/optimizations/o2/parent/'+n for n in (
                      'GenerateVDotElasticParent.scala', 'parent_test.cpp', 'check_negative.py',
                      'test_negative.py', 'check_trace.py', 'test_trace.py')],
                  'team/optimizations/o4/perf/audit.py']
        for name in frozen:
            original = subprocess.check_output(['git', '-C', str(repo), 'show', head+':'+name])
            if original != (repo/name).read_bytes():
                raise ValueError('frozen parent input differs from pinned commit: ' + name)
        source_paths = [here/n for n in ('run.py', 'derive_test.py', 'extra_cases.cpp.inc',
                                       'check_coverage.py', 'CONTRACT.md')]
        source_paths += [here.parent/n for n in ('run_fu.py', 'source-manifest.json', 'candidate.patch')]
        source_paths += [repo/n for n in frozen]
        inputs = {str(n): util.digest(n) for n in source_paths}
        util.save(out/'inputs.json', inputs)
        snap = out/'source-snapshot'
        snap.mkdir()
        for path in source_paths:
            target = snap/path.name
            if target.exists():
                raise ValueError('snapshot basename collision')
            shutil.copyfile(path, target)
            if util.digest(target) != inputs[str(path)]:
                raise ValueError('snapshot differs from recorded source')
        mill_options = snap/'mill-jvm-opts'
        mill_options.write_text('-Xmx4G\n-Xss8m\n-XX:ActiveProcessorCount=1\n')
        status['mill_jvm_options'] = dict(path=str(mill_options), sha256=util.digest(mill_options))
        deriver = module(snap/'derive_test.py', 'new_parent_deriver')
        cpp = snap/'dot16_parent_test.cpp'
        util.save(out/'test-derivation.json', deriver.derive(
            snap/'parent_test.cpp', snap/'extra_cases.cpp.inc', cpp, a.feature))
        activated = subprocess.check_output(['bash', '-c',
            'source team/scripts/activate.sh >/dev/null && command -v mill'], cwd=repo, text=True).strip()
        mill = Path(activated)
        if not mill.is_absolute() or not mill.is_file():
            raise ValueError('activate.sh did not identify a real Mill launcher')
        status['mill_launcher'] = dict(path=str(mill), sha256=util.digest(mill))
        derived, proof = util.derive_runner((snap/'run_rtl.py').read_bytes(), repo, cpp, cache, a.feature, mill)
        shadow = snap/'dot16_run_rtl.py'
        shadow.write_text(derived)
        util.save(out/'runner-derivation.json', proof)
        snapshots = {x.name: util.digest(x) for x in snap.iterdir() if x.is_file()}
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE='1', VDOT_RTL_JOBS='1',
                   VDOT_RTL_JAVA_OPTS='-Xmx4G -Xss8m -XX:ActiveProcessorCount=1',
                   MILL_JVM_OPTS_PATH=str(mill_options), JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=1')
        env.pop('_JAVA_OPTIONS', None)
        command = [sys.executable, '-B', str(shadow), 'parent', str(out/'campaign')]
        status['command'] = command
        util.save(out/'status.json', status)
        with (out/'runner.log').open('wb') as log:
            proc = subprocess.Popen(command, cwd=repo, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            status['pid'] = proc.pid
            try:
                status['exit_code'] = proc.wait(timeout=a.budget_seconds)
            except subprocess.TimeoutExpired:
                status['timed_out'] = True
                status['timeout_cleanup_complete'] = util.stop_group(proc)
                raise RuntimeError('15-minute budget exhausted; inspect preserved evidence before continuing')
        if proc.returncode != 0:
            raise RuntimeError('frozen parent runner returned ' + str(proc.returncode))
        if util.group_exists(proc.pid):
            status['unexpected_children_cleanup_complete'] = util.stop_group(proc)
            raise RuntimeError('parent runner left a live process group')
        campaign = out/'campaign'
        old_status = json.loads((campaign/'runner.status.json').read_text())
        if old_status.get('passed') is not True or old_status.get('stage') != 'parent':
            raise ValueError('original runner did not complete all replay and negative checks')
        coverage = module(snap/'check_coverage.py', 'new_parent_coverage')
        report = coverage.check(campaign/'result.log', campaign/'metadata.log', a.feature)
        util.save(out/'additional-coverage.json', report)
        status['coverage'] = {k: v for k, v in report.items() if k not in ('cases', 'original_summary')}
        status['original_summary'] = report['original_summary']
        if (campaign/'source-after.status').read_text() != 'SOURCE_AND_DEPENDENCIES_UNCHANGED\n':
            raise ValueError('original source/dependency stability check missing')
        if inputs != {str(n): util.digest(n) for n in source_paths} or snapshots != {
                x.name: util.digest(x) for x in snap.iterdir() if x.is_file()}:
            raise ValueError('campaign source or frozen snapshot changed during execution')
        if any(util.digest(repo/n) != h for n, h in guards.items()) or subprocess.check_output(
                ['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() != head:
            raise ValueError('production source identity changed during execution')
        status.update(passed=True, parent_qualified=True,
                      qualification=f'DOT16_PARENT_FEATURE_{a.feature}_PASS')
        print(status['qualification'], flush=True)
    except Exception as error:
        status['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        status['finished'] = util.stamp()
        if proc is not None:
            status['process_returncode'] = proc.poll()
            if util.group_exists(proc.pid):
                status['final_cleanup_complete'] = util.stop_group(proc)
            status['process_group_absent'] = not util.group_exists(proc.pid)
        util.save(out/'status.json', status)


if __name__ == '__main__':
    main()
