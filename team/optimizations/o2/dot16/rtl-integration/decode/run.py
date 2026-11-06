#!/usr/bin/env python3
"""Validate the production decoders through a new read-only operation probe."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HELPER_SHA256 = 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'
HARNESS_SHA256 = 'c4b275bbc5e8f63f189ad55fc646b15d27d9216fd4497537c5c4bec66e3f3204'
# Mill exports these optional source-resource roots even when they do not exist.
# This exact list comes from the retained decode-flag0-01 runClasspath export.
# Keep their positions and absence in the identity; missing jars/classes still fail.
OPTIONAL_RESOURCE_PATHS = frozenset((
    'rocket-chip/cde/cde/compile-resources',
    'rocket-chip/cde/cde/resources',
    'rocket-chip/hardfloat/hardfloat/compile-resources',
    'rocket-chip/hardfloat/hardfloat/src/main/resources',
    'rocket-chip/macros/compile-resources',
    'rocket-chip/macros/src/main/resources',
    'rocket-chip/compile-resources',
    'difftest/compile-resources',
    'difftest/src/main/resources',
    'utility/compile-resources',
    'utility/src/main/resources',
    'huancun/compile-resources',
    'coupledL2/compile-resources',
    'openLLC/openNCB/compile-resources',
    'openLLC/openNCB/src/main/resources',
    'openLLC/compile-resources',
    'openLLC/src/main/resources',
    'yunsuan/compile-resources',
    'fudian/compile-resources',
    'fudian/src/main/resources',
    'macros/compile-resources',
    'macros/resources',
    'compile-resources',
))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def parse_classpath(text):
    values = json.loads(text)
    if not isinstance(values, list) or not values or not all(isinstance(x, str) for x in values):
        raise ValueError('Mill single-target runClasspath must be a nonempty JSON string array')
    paths = []
    for value in values:
        parts = value.split(':', 3)
        if len(parts) != 4 or parts[0] not in ('ref', 'qref') or parts[1] not in ('v0', 'v1', 'vn') or not re.fullmatch(r'[0-9a-fA-F]{8}', parts[2]):
            raise ValueError('unexpected Mill 0.12.3 PathRef encoding')
        p = Path(parts[3])
        if not p.is_absolute():
            raise ValueError('exported classpath path is not absolute')
        paths.append(str(p))
    return paths


def classpath_identity(paths, repo):
    result = []
    optional = {repo/name for name in OPTIONAL_RESOURCE_PATHS}
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            result.append(dict(path=raw, type='file', bytes=path.stat().st_size,
                               sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        elif path.is_dir():
            files = [dict(path=p.relative_to(path).as_posix(), bytes=p.stat().st_size,
                          sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                     for p in sorted(path.rglob('*')) if p.is_file()]
            result.append(dict(path=raw, type='directory', files=files))
        elif not path.exists() and not path.is_symlink() and path in optional:
            result.append(dict(path=raw, type='missing-resource'))
        else:
            raise ValueError('unsupported or unexpected missing exported classpath entry: ' + raw)
    return result


def dependencies(repo, prefix=''):
    result = []
    entries = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '-rz', 'HEAD']).split(b'\0')
    for entry in filter(None, entries):
        meta, name = entry.split(b'\t', 1)
        mode, _, pin = meta.decode().split()
        if mode != '160000':
            continue
        name = name.decode()
        sub = repo/name
        head = subprocess.check_output(['git', '-C', str(sub), 'rev-parse', 'HEAD'], text=True).strip()
        status = subprocess.check_output(['git', '-C', str(sub), 'status', '--porcelain=v1', '--untracked-files=normal'], text=True)
        if head != pin or status:
            raise ValueError('dirty or unpinned dependency: ' + prefix+name)
        result.append(dict(path=prefix+name, pin=pin, head=head, status=status))
        result.extend(dependencies(sub, prefix+name+'/'))
    return result


def positive_gate(text, feature):
    lines = text.splitlines()
    if len(lines) != 2 or not lines[0].startswith('DOT16_DECODE_EXTRA_PASS '):
        raise ValueError('missing/extra decode completion record')
    pairs = [p.split('=', 1) for p in lines[0].split()[1:]]
    if any(len(p) != 2 or not p[1].isdigit() for p in pairs) or len(dict(pairs)) != len(pairs):
        raise ValueError('malformed decode completion fields')
    got = {k: int(v) for k, v in pairs}
    expected = dict(schema=1, feature=feature, old_transactions=131109,
                    new_transactions=131109 if feature else 0,
                    classification_rejects=0 if feature else 131072,
                    neighbours=17 if feature else 0,
                    simple_op0=131109, complex_op0=131373,
                    simple_op1=131109 if feature else 0,
                    complex_op1=131373 if feature else 0)
    if got != expected or lines[1] != f'VDOT_DECODE_PASS transactions={131109*(1+feature)} (decoder RTL only)':
        raise ValueError('decode observed coverage inventory mismatch')
    return expected


def negative_gate(text, feature, which):
    case = 131109 if feature else 0
    word = 'e00000b' if feature else '200000b'
    expected = [f'DOT16_DECODE_INJECT {which}_op',
                f'VDOT_DECODE_FAIL case={case} word=0x{word} reason={which} operation mismatch']
    if text.splitlines() != expected:
        raise ValueError('operation-observation negative rejected for unexpected reason')


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
        p.error('reviewed process helper identity changed')
    util = module(helper, 'frozen_dot16_execution_helper')
    repo, out, cache = a.repo.resolve(), a.output.resolve(), a.mill_output.resolve()
    if not a.output.is_absolute() or out.exists() or out.is_relative_to(repo) or repo.is_relative_to(out):
        p.error('output must be new, absolute and outside the checkout')
    if not a.mill_output.is_absolute() or Path(os.path.abspath(a.mill_output)) != cache:
        p.error('core Mill cache must be an absolute path without symbolic-link components')
    if cache != repo/util.IN_TREE_MILL_CACHE or not cache.is_dir() or subprocess.run(
            ['git', '-C', str(repo), 'check-ignore', '-q', '--', str(util.IN_TREE_MILL_CACHE)]).returncode:
        p.error('reuse only the reviewed, already ignored core Mill cache')
    if a.expected_head != util.EXPECTED_HEAD or not 30 <= a.budget_seconds <= 900:
        p.error('new pin or budget above 900 seconds needs a new reviewed contract')
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    os.sched_setaffinity(0, {a.cpu})
    out.mkdir(parents=True)
    deadline = time.monotonic()+a.budget_seconds
    status = dict(schema=1, started=util.stamp(), passed=False, feature=a.feature,
                  cpu_affinity=sorted(os.sched_getaffinity(0)), budget_seconds=a.budget_seconds,
                  repo=str(repo), output=str(out), core_mill_output=str(cache),
                  decode_qualified=False, fullcore_qualified=False, performance_measured=False)
    records, proc = [], None

    def run_step(name, command, cwd, env, expected=0, separate_stderr=False):
        nonlocal proc
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            status['timed_out'] = True
            raise RuntimeError('15-minute campaign budget exhausted before ' + name)
        record = dict(name=name, command=list(map(str, command)), cwd=str(cwd),
                      started=util.stamp(), expected_exit_code=expected)
        status['active_step'] = name
        util.save(out/'status.json', status)
        stderr = (out/(name+'.stderr')).open('wb') if separate_stderr else subprocess.STDOUT
        try:
            with (out/(name+'.log')).open('wb') as stdout:
                proc = subprocess.Popen(record['command'], cwd=cwd, env=env,
                                        stdout=stdout, stderr=stderr, start_new_session=True)
                status['last_pid'] = proc.pid
                try:
                    record['exit_code'] = proc.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    status['timed_out'] = True
                    record['timed_out'] = True
                    record['cleanup_complete'] = util.stop_group(proc)
                    raise RuntimeError('15-minute campaign budget exhausted in ' + name)
            if util.group_exists(proc.pid):
                record['cleanup_complete'] = util.stop_group(proc)
                raise RuntimeError('command left a live process group: ' + name)
            record['process_group_absent'] = True
            if record['exit_code'] != expected:
                raise RuntimeError(name+' exit '+str(record['exit_code'])+', expected '+str(expected))
        finally:
            if separate_stderr:
                stderr.close()
            record['finished'] = util.stamp()
            records.append(record)
            util.save(out/'commands.json', records)

    try:
        head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        if head != a.expected_head:
            raise ValueError('HEAD differs from pinned source')
        status['head'] = head
        manifest = json.loads((here.parent/'source-manifest.json').read_text())
        if util.digest(here.parent/'candidate.patch') != util.PATCH_SHA256 or manifest['patch_sha256'] != util.PATCH_SHA256:
            raise ValueError('production patch identity mismatch')
        guards = manifest['apply_result'] | manifest['unchanged_dependency_sha256']
        if any(util.digest(repo/n) != h for n, h in guards.items()):
            raise ValueError('production candidate changed')
        frozen = ('build.sc', 'team/rtl/vdot/GenerateVDotDecode.scala',
                  'team/rtl/vdot/decode_test.cpp', 'team/scripts/check-vdot-decode.sh',
                  'team/optimizations/o1/build_inputs.py')
        for name in frozen:
            if subprocess.check_output(['git', '-C', str(repo), 'show', head+':'+name]) != (repo/name).read_bytes():
                raise ValueError('frozen decode/build input changed: ' + name)
        if util.digest(repo/frozen[1]) != HARNESS_SHA256:
            raise ValueError('original harness identity mismatch')
        inputs_module = module(repo/frozen[-1], 'frozen_hardware_inputs')
        hardware = inputs_module.hardware_files(repo)
        inputs_module.verify_hardware_files(repo, hardware)
        util.save(out/'compiler-inputs.json', hardware)
        deps = dependencies(repo)
        util.save(out/'dependencies.json', deps)
        source_paths = [here/n for n in ('run.py', 'derive_test.py', 'extra_cases.cpp.inc',
                         'GenerateVDot16DecodeProbe.scala', 'build.sc', 'CONTRACT.md')]
        source_paths += [here.parent/n for n in ('run_fu.py', 'source-manifest.json', 'candidate.patch')]
        source_paths += [repo/n for n in frozen]
        inputs = {str(path): util.digest(path) for path in source_paths}
        util.save(out/'inputs.json', inputs)
        snap = out/'source-snapshot'
        snap.mkdir()
        for path in source_paths:
            name = 'original-build.sc' if path == repo/'build.sc' else path.name
            target = snap/name
            if target.exists():
                raise ValueError('snapshot basename collision')
            shutil.copyfile(path, target)
            if util.digest(target) != inputs[str(path)]:
                raise ValueError('source snapshot mismatch')
        mill_options = snap/'mill-jvm-opts'
        mill_options.write_text('-Xmx4G\n-Xss8m\n-XX:ActiveProcessorCount=1\n')
        cpp = snap/'dot16_decode_test.cpp'
        deriver = module(snap/'derive_test.py', 'new_decode_deriver')
        util.save(out/'test-derivation.json', deriver.derive(
            snap/'decode_test.cpp', snap/'extra_cases.cpp.inc', cpp, a.feature))
        frozen_snapshot = {x.name: util.digest(x) for x in snap.iterdir() if x.is_file()}
        activated = subprocess.check_output(['bash', '-c',
            'source team/scripts/activate.sh >/dev/null && env -0'], cwd=repo)
        env = dict(item.decode().split('=', 1) for item in activated.split(b'\0') if item)
        env.update(VDOT_DOT16=str(a.feature), VDOT_O2_ELASTIC='1', VDOT_T14_FUSED_INPUT='1',
                   VDOT_O2_TRACE='0', VDOT_O1_HANDOFF='0', VDOT_T12_TRACE='0',
                   VDOT_T13_TRACE='0', VDOT_O1_TRACE='0', MILL_OUTPUT_DIR=str(cache),
                   MILL_JVM_OPTS_PATH=str(mill_options), JAVA_OPTS='-Xmx4G -Xss8m -XX:ActiveProcessorCount=1',
                   JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=1', PYTHONDONTWRITEBYTECODE='1')
        env.pop('_JAVA_OPTIONS', None)
        mill = shutil.which('mill', path=env['PATH'])
        if not mill or not Path(mill).is_file():
            raise ValueError('Mill launcher not found')
        selected = ('VDOT_DOT16', 'VDOT_O2_ELASTIC', 'VDOT_T14_FUSED_INPUT', 'VDOT_O2_TRACE',
                    'VDOT_O1_HANDOFF', 'VDOT_T12_TRACE', 'VDOT_T13_TRACE', 'VDOT_O1_TRACE',
                    'MILL_OUTPUT_DIR', 'MILL_JVM_OPTS_PATH', 'JAVA_HOME', 'JAVA_OPTS',
                    'JAVA_TOOL_OPTIONS', 'CHISEL_FIRTOOL_PATH', 'PATH')
        util.save(out/'run.env.json', {k: env[k] for k in selected})
        status['mill_launcher'] = dict(path=mill, sha256=util.digest(mill))
        for name, command in [('java-version', ['java', '-version']),
                              ('mill-version', ['bash', mill, '--no-server', '--version']),
                              ('verilator-version', ['verilator', '--version']),
                              ('firtool-version', [str(Path(env['CHISEL_FIRTOOL_PATH'])/'firtool'), '--version'])]:
            run_step(name, command, repo, env)
        run_step('core-classpath', ['bash', mill, '--no-server', '-j', '1', 'show',
                 'xiangshan.runClasspath'], repo, env, separate_stderr=True)
        paths = parse_classpath((out/'core-classpath.log').read_text())
        if any('vdotDecode/compile.dest' in path or 'vdotElasticParent/compile.dest' in path for path in paths):
            raise ValueError('export included a separately compiled harness')
        cp_identity = classpath_identity(paths, repo)
        util.save(out/'classpath-before.json', cp_identity)
        workspace = out/'probe-workspace'
        (workspace/'src').mkdir(parents=True)
        for name in ('GenerateVDotDecode.scala', 'GenerateVDot16DecodeProbe.scala'):
            shutil.copyfile(snap/name, workspace/'src'/name)
        shutil.copyfile(snap/'build.sc', workspace/'build.sc')
        util.save(workspace/'classpath-paths.json', paths)
        probe_inputs = {p.relative_to(workspace).as_posix(): util.digest(p)
                        for p in workspace.rglob('*') if p.is_file()}
        util.save(out/'probe-inputs.json', probe_inputs)
        probe_env = env.copy()
        probe_env['MILL_OUTPUT_DIR'] = str(out/'probe-output')
        run_step('elaboration', ['bash', mill, '--no-server', '-j', '1', 'probe.runMain',
                 'team.vdot.GenerateVDot16DecodeProbe', str(out/'rtl')], workspace, probe_env)
        rtl = out/'rtl'
        sources = sorted({p.resolve() for pattern in ('*.sv', '*.v') for p in rtl.rglob(pattern)})
        top = 'VDot16DecodeProbe'
        if rtl/(top+'.sv') not in sources or any(not p.is_relative_to(rtl) or
                b'// ----- 8< ----- FILE "' in p.read_bytes() for p in sources):
            raise ValueError('missing, virtual or external generated RTL')
        generated = [dict(path=p.relative_to(out).as_posix(), bytes=p.stat().st_size,
                          sha256=util.digest(p)) for p in sources]
        util.save(out/'generated-files.json', generated)
        run_step('lint', ['verilator', '--lint-only', '--assert', '--top-module', top, *sources], repo, env)
        run_step('verilator', ['verilator', '--cc', '--exe', '--build', '--assert', '--top-module', top,
                 '--Mdir', str(out/'obj'), '-j', '1', '-CFLAGS', '-std=c++17 -O2', *sources, cpp], repo, env)
        binary = out/'obj'/('V'+top)
        run_step('result', [binary], repo, env)
        status['coverage'] = positive_gate((out/'result.log').read_text(), a.feature)
        for which in ('simple', 'complex'):
            run_step('inject-'+which, [binary, '--fault-'+which+'-op'], repo, env, expected=1)
            negative_gate((out/('inject-'+which+'.log')).read_text(), a.feature, which)
        status['observation_negatives'] = ['simple_op', 'complex_op']
        status['active_step'] = 'final-input-identity'
        util.save(out/'status.json', status)
        if classpath_identity(paths, repo) != cp_identity:
            raise ValueError('exported core classes/resources changed during probe run')
        if inputs != {str(p): util.digest(p) for p in source_paths} or frozen_snapshot != {
                x.name: util.digest(x) for x in snap.iterdir() if x.is_file()}:
            raise ValueError('source/snapshot identity changed during decode campaign')
        if probe_inputs != {name: util.digest(workspace/name) for name in probe_inputs}:
            raise ValueError('independent probe inputs changed during execution')
        inputs_module.verify_hardware_files(repo, hardware)
        if deps != dependencies(repo) or any(util.digest(repo/n) != h for n, h in guards.items()) or subprocess.check_output(
                ['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() != head:
            raise ValueError('production/dependency identity changed during decode campaign')
        if time.monotonic() >= deadline:
            status['timed_out'] = True
            raise RuntimeError('15-minute campaign budget exhausted during final identity checks')
        util.save(out/'artifact.json', dict(path=str(binary), bytes=binary.stat().st_size, sha256=util.digest(binary)))
        (out/'source-after.status').write_text('SOURCE_DEPENDENCIES_CLASSPATH_AND_PROBE_UNCHANGED\n')
        status.update(passed=True, decode_qualified=True, active_step=None,
                      qualification=f'DOT16_DECODE_FEATURE_{a.feature}_PASS')
        print(status['qualification'], flush=True)
    except Exception as error:
        status.update(passed=False, decode_qualified=False)
        status['error'] = type(error).__name__+': '+str(error)
        raise
    finally:
        status['finished'] = util.stamp()
        if proc is not None:
            status['last_process_returncode'] = proc.poll()
            if util.group_exists(proc.pid):
                status['final_cleanup_complete'] = util.stop_group(proc)
            status['process_group_absent'] = not util.group_exists(proc.pid)
        util.save(out/'status.json', status)


if __name__ == '__main__':
    main()
