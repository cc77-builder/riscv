#!/usr/bin/env python3
"""Run a separately identified dot16 FU campaign using the frozen O2 runner.

The repository runner and its checker are retained byte for byte. An explicit,
reversible copy adds the feature flag, isolated Mill output and new C++ test.
This command neither applies the production patch nor changes Git state.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

RUNNER_SHA256 = '125cd5a308fa0253c7bd0dbc6d9ea7593afea6e7a118e3b544bfd1dab0fd7922'
EXPECTED_HEAD = 'c981529dc6e493fb7deee8429b9ce05fd197497b'
PATCH_SHA256 = '5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416'
IN_TREE_MILL_CACHE = Path('out/dot16-fu-20261106-pro2')
EXTRA_ON = dict(schema=1, paired_vectors=10022, directed_inputs=40,
                legal_compared=20124, illegal_compared=40,
                mixed_ii1_intervals=20043, first_latency=2,
                mixed_cancel_pairs=96, additional_reset_cases=16)
EXTRA_OFF = dict(schema=1, new_op_rejected=8, unknown_op_rejected=8)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def stop_group(proc):
    if group_exists(proc.pid):
        os.killpg(proc.pid, signal.SIGTERM)
    until = time.monotonic() + 10
    while group_exists(proc.pid) and time.monotonic() < until:
        proc.poll()
        time.sleep(0.1)
    if group_exists(proc.pid):
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait(timeout=10)
    return not group_exists(proc.pid)


def derive_runner(raw, repo, cpp, cache, feature, mill):
    if hashlib.sha256(raw).hexdigest() != RUNNER_SHA256:
        raise ValueError('frozen O2 runner identity mismatch')
    text = raw.decode()
    edits = [
        ('ROOT = Path(__file__).resolve().parents[3]', 'ROOT = Path(' + repr(str(repo)) + ')'),
        ('    env.update(VDOT_O2_TRACE="0",',
         '    env.update(VDOT_DOT16=' + repr(str(feature)) + ', MILL_OUTPUT_DIR=' + repr(str(cache)) + ', VDOT_O2_TRACE="0",'),
        ('selected = {k: env[k] for k in ("VDOT_O2_TRACE",',
         'selected = {k: env[k] for k in ("VDOT_DOT16", "MILL_OUTPUT_DIR", "VDOT_O2_TRACE",'),
        ('    def run(log, args, expected=0):\n        start = stamp()',
         '    def run(log, args, expected=0):\n'
         '        if str(args[0]) == "mill":\n'
         '            args = ["bash", ' + repr(str(mill)) + ', "--no-server", *[a for a in args[1:] if a != "-i"]]\n'
         '        start = stamp()'),
        ('ROOT/"team/optimizations/o2"/stage/(stage+"_test.cpp")', 'Path(' + repr(str(cpp)) + ')'),
    ]
    for before, after in edits:
        if text.count(before) != 1:
            raise ValueError('ambiguous frozen runner anchor')
        text = text.replace(before, after, 1)
    restored = text
    for before, after in reversed(edits):
        if restored.count(after) != 1:
            raise ValueError('ambiguous inverse runner edit')
        restored = restored.replace(after, before, 1)
    if restored.encode() != raw:
        raise ValueError('runner derivation did not preserve complete original')
    return text, dict(edits=len(edits), original_reconstructed_byte_exact=True,
                     original_sha256=RUNNER_SHA256,
                     derived_sha256=hashlib.sha256(text.encode()).hexdigest())


def completion_gate(text, feature, runner_status):
    if runner_status.get('passed') is not True or runner_status.get('stage') != 'fu':
        raise ValueError('underlying runner did not finish successfully')
    lines = text.splitlines()
    prefix = 'DOT16_FU_EXTRA_PASS' if feature else 'DOT16_FU_DISABLED_EXTRA_PASS'
    extra = [x for x in lines if x.startswith(prefix)]
    final = [x for x in lines if x.startswith('O2_FU_PASS ')]
    if len(extra) != 1 or len(final) != 1:
        raise ValueError('missing or duplicate completion marker')
    if any(x in text for x in ('_FAIL', '_INJECT', '_FAULT_ESCAPED')):
        raise ValueError('failure marker in positive log')
    fields = dict(re.findall(r'(\w+)=(\d+)', extra[0]))
    expected = EXTRA_ON if feature else EXTRA_OFF
    if fields != {k: str(v) for k, v in expected.items()}:
        raise ValueError('extra coverage inventory mismatch')
    final_fields = dict(re.findall(r'(\w+)=(\d+)', final[0]))
    if final_fields.get('vectors') != '10022' or final_fields.get('reset_cases') != ('24' if feature else '8'):
        raise ValueError('original FU completion inventory mismatch')
    if lines.index(extra[0]) >= lines.index(final[0]):
        raise ValueError('final completion does not follow extra coverage')
    return dict(extra=expected, final=final_fields)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mill-output', type=Path, required=True)
    p.add_argument('--feature', type=int, choices=(0, 1), required=True)
    p.add_argument('--expected-head', default=EXPECTED_HEAD)
    p.add_argument('--cpu', type=int, choices=range(4), default=1)
    p.add_argument('--budget-seconds', type=int, default=900)
    a = p.parse_args()
    repo, out, cache = a.repo.resolve(), a.output.resolve(), a.mill_output.resolve()
    if not a.output.is_absolute() or out.exists() or out.is_relative_to(repo) or repo.is_relative_to(out):
        p.error('output must be new, absolute, and separate from the checkout')
    if not a.mill_output.is_absolute() or repo.is_relative_to(cache) or cache.is_relative_to(out) or out.is_relative_to(cache):
        p.error('Mill output must be absolute, not contain the checkout, and be separate from run output')
    if Path(os.path.abspath(a.mill_output)) != cache:
        p.error('Mill output and its parents must not be symbolic links')
    if cache.is_relative_to(repo):
        if cache != repo / IN_TREE_MILL_CACHE:
            p.error('only the reviewed out/dot16-fu-20261106-pro2 cache is allowed inside the checkout')
        ignored = subprocess.run(['git', '-C', str(repo), 'check-ignore', '-q', '--', str(IN_TREE_MILL_CACHE)])
        if ignored.returncode != 0:
            p.error('the in-tree Mill cache must already be ignored by Git')
    if not 30 <= a.budget_seconds <= 3600:
        p.error('budget must be 30..3600 seconds; longer work needs a reviewed new run')
    if not re.fullmatch(r'[0-9a-f]{40}', a.expected_head):
        p.error('expected HEAD must be a complete commit ID')
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    sys.dont_write_bytecode = True
    os.sched_setaffinity(0, {a.cpu})
    here = Path(__file__).resolve().parent
    out.mkdir(parents=True)
    status = dict(schema=1, started=stamp(), passed=False, feature=a.feature,
                  cpu_affinity=sorted(os.sched_getaffinity(0)), budget_seconds=a.budget_seconds,
                  repo=str(repo), output=str(out), mill_output=str(cache),
                  decode_qualified=False, parent_qualified=False,
                  fullcore_qualified=False, ppa_qualified=False)
    proc = None
    try:
        head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        status['head'] = head
        if head != a.expected_head:
            raise ValueError('checkout HEAD differs from expected pin')
        manifest = json.loads((here/'source-manifest.json').read_text())
        if digest(here/'candidate.patch') != PATCH_SHA256 or manifest['patch_sha256'] != PATCH_SHA256:
            raise ValueError('production patch identity mismatch')
        guards = manifest['apply_result'] | manifest['unchanged_dependency_sha256']
        if any(digest(repo/n) != h for n, h in guards.items()):
            raise ValueError('production candidate is not the exact reviewed source')
        source_paths = [here/n for n in ('run_fu.py', 'derive_fu_test.py', 'source-manifest.json', 'candidate.patch')]
        source_paths += [repo/'team/optimizations/o2/run_rtl.py', repo/'team/optimizations/o2/fu/fu_test.cpp']
        input_hashes = {str(n): digest(n) for n in source_paths}
        save(out/'inputs.json', input_hashes)
        snap = out/'source-snapshot'
        snap.mkdir()
        mill_options = snap/'mill-jvm-opts'
        mill_options.write_text('-Xmx4G\n-Xss8m\n-XX:ActiveProcessorCount=1\n')
        status['mill_jvm_options'] = dict(path=str(mill_options), sha256=digest(mill_options))
        for path in source_paths:
            shutil.copyfile(path, snap/path.name)
            if digest(snap/path.name) != input_hashes[str(path)]:
                raise ValueError('copied source differs from its recorded input')
        sys.path.insert(0, str(snap))
        from derive_fu_test import derive
        cpp = snap/'dot16_fu_test.cpp'
        derivation = derive(snap/'fu_test.cpp', cpp, a.feature)
        save(out/'test-derivation.json', derivation)
        activated = subprocess.check_output(['bash', '-c', 'source team/scripts/activate.sh >/dev/null && command -v mill'], cwd=repo, text=True).strip()
        mill = Path(activated)
        if not mill.is_absolute() or not mill.is_file():
            raise ValueError('activate.sh did not resolve a real Mill launcher')
        status['mill_launcher'] = dict(path=str(mill), sha256=digest(mill))
        derived, proof = derive_runner((snap/'run_rtl.py').read_bytes(), repo, cpp, cache, a.feature, mill)
        shadow = snap/'dot16_run_rtl.py'
        shadow.write_text(derived)
        save(out/'runner-derivation.json', proof)
        snapshots = {p.name: digest(p) for p in snap.iterdir() if p.is_file()}
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE='1', VDOT_RTL_JOBS='1',
                   VDOT_RTL_JAVA_OPTS='-Xmx4G -Xss8m -XX:ActiveProcessorCount=1',
                   MILL_JVM_OPTS_PATH=str(mill_options),
                   JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=1')
        env.pop('_JAVA_OPTIONS', None)
        command = [sys.executable, '-B', str(shadow), 'fu', str(out/'campaign')]
        status['command'] = command
        save(out/'status.json', status)
        with (out/'runner.log').open('wb') as log:
            proc = subprocess.Popen(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            status['pid'] = proc.pid
            try:
                status['exit_code'] = proc.wait(timeout=a.budget_seconds)
            except subprocess.TimeoutExpired:
                status['timed_out'] = True
                status['timeout_cleanup_complete'] = stop_group(proc)
                raise RuntimeError('explicit run budget exhausted; inspect preserved logs before continuing')
        if proc.returncode != 0:
            raise RuntimeError('underlying O2 runner returned ' + str(proc.returncode))
        if group_exists(proc.pid):
            status['unexpected_children_cleanup_complete'] = stop_group(proc)
            raise RuntimeError('underlying runner left a live process group')
        campaign = out/'campaign'
        status['coverage'] = completion_gate((campaign/'result.log').read_text(), a.feature,
                                             json.loads((campaign/'runner.status.json').read_text()))
        if (campaign/'source-after.status').read_text() != 'SOURCE_AND_DEPENDENCIES_UNCHANGED\n':
            raise ValueError('underlying input stability proof absent')
        if input_hashes != {str(n): digest(n) for n in source_paths} or snapshots != {p.name: digest(p) for p in snap.iterdir() if p.is_file()}:
            raise ValueError('campaign controller or derived input changed during execution')
        if any(digest(repo/n) != h for n, h in guards.items()) or subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() != head:
            raise ValueError('production candidate identity changed during execution')
        status['passed'] = True
        status['qualification'] = 'DOT16_FU_FEATURE_' + str(a.feature) + '_PASS'
        print(status['qualification'], flush=True)
    except Exception as e:
        status['error'] = type(e).__name__ + ': ' + str(e)
        raise
    finally:
        status['finished'] = stamp()
        if proc is not None:
            status['process_returncode'] = proc.poll()
            if group_exists(proc.pid):
                status['final_cleanup_complete'] = stop_group(proc)
            status['process_group_absent'] = not group_exists(proc.pid)
        save(out/'status.json', status)


if __name__ == '__main__':
    main()
