"""Build/test the isolated dot16 arithmetic and flow prototype in a fresh output.

This does not compile or test the production XiangShan FU, parent or processor.
External tools are supplied by the caller's explicit environment; at most two
CPU affinity slots and two build jobs are used. Every variant has separate files.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone

PARAM = Path('team/rtl/vdot/param/VDotParam.scala')
PARAM_SHA = '617292743d0e9515ffc18b6099f87c706099a12385e42f0ef60b6cc9b0680c39'
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(repo, out, variant, jobs):
    if out.exists() or out.is_relative_to(repo):
        raise ValueError('fresh output outside repository required')
    if jobs not in (1, 2):
        raise ValueError('prototype budget is one or two CPUs')
    if os.name == 'posix':
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:jobs])
    if sha(repo / PARAM) != PARAM_SHA:
        raise ValueError('frozen parameter arithmetic changed')
    tools = {name: shutil.which(name) for name in ('bash', 'mill', 'verilator', 'clang++')}
    if not all(tools.values()):
        raise ValueError('required tools absent from explicit PATH: ' + repr(tools))
    out.mkdir(parents=True)
    snap = out / 'source-snapshot'
    snap.mkdir()
    source_files = [HERE / name for name in ('Dot16.scala', 'prototype_test.cpp', 'run_prototype.py', 'build.sc', '.mill-version', 'CONTRACT.md')]
    source_files.append(repo / PARAM)
    pins = {}
    for source in source_files:
        raw = source.read_bytes()
        (snap / source.name).write_bytes(raw)
        pins[str(source)] = hashlib.sha256(raw).hexdigest()
    if any(sha(Path(path)) != digest for path, digest in pins.items()):
        raise RuntimeError('source changed while taking the snapshot')
    for name in ('build.sc', '.mill-version'):
        shutil.copyfile(snap / name, out / name)
    env = os.environ.copy()
    env.update(DOT16_SOURCE_ROOT=str(snap), DOT16_PARAM_SOURCE=str(snap / 'VDotParam.scala'),
               MILL_WORKSPACE_ROOT=str(out), JAVA_OPTS='-Xmx4G -Xss8m -XX:ActiveProcessorCount=' + str(jobs))
    result = dict(contract='r3-dot16-v0.1', variant=variant, started=datetime.now(timezone.utc).isoformat(),
                  status='RUNNING', source_files=pins, tools=tools,
                  tool_sha256={name: sha(Path(path)) for name, path in tools.items()}, jobs=jobs,
                  environment={key: env.get(key) for key in ('PATH', 'JAVA_HOME', 'JAVA_OPTS', 'CHISEL_FIRTOOL_PATH', 'COURSIER_CACHE', 'CXX')},
                  production_fu_tested=False, parent_tested=False, target_tested=False,
                  application_performance_qualified=False, commands=[])

    def command(args, label, expected=0):
        args = [str(a) for a in args]
        start = datetime.now(timezone.utc).isoformat()
        with (out / (label + '.log')).open('wb') as log:
            process = subprocess.run(args, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
        entry = dict(args=args, label=label, started=start, finished=datetime.now(timezone.utc).isoformat(), exit_code=process.returncode)
        result['commands'].append(entry)
        if process.returncode != expected:
            raise RuntimeError(label + ' exit=' + str(process.returncode))
        return (out / (label + '.log')).read_text(errors='replace')

    try:
        # The installed Mill launcher is a shell/Windows polyglot, without a
        # Unix shebang. Invoke it through Bash; do not alter the shared launcher.
        command([tools['bash'], tools['mill'], '-i', '-j', jobs, 'dot16.runMain', 'team.vdot.dot16.GenerateDot16', variant, out / 'rtl'], 'elaboration')
        rtl = out / 'rtl' / 'Dot16Prototype.sv'
        if not rtl.is_file():
            raise RuntimeError('missing generated SystemVerilog')
        result['rtl_sha256'] = sha(rtl)
        text = rtl.read_text()
        if re.search(r'always[^\n]*posedge\s+reset', text):
            raise RuntimeError('prototype requires synchronous reset')
        command([tools['verilator'], '--cc', '--exe', '--build', '--assert', '--top-module', 'Dot16Prototype',
                 '--Mdir', out / 'obj', '-j', jobs, '-CFLAGS', '-std=c++17 -O2', rtl, snap / 'prototype_test.cpp'], 'verilator')
        executable = out / 'obj' / 'VDot16Prototype'
        log = command([executable, variant], 'test')
        if not re.search(r'^DOT16_PROTOTYPE_PASS variant=' + re.escape(variant) + r' ', log, re.M):
            raise RuntimeError('missing prototype PASS marker')
        result['test_summary'] = log.strip()
        negative = command([executable, variant, '--inject-result'], 'checker-injection', expected=1)
        if 'DOT16_PROTOTYPE_CHECKER_INJECTION result' not in negative or 'DOT16_PROTOTYPE_FAIL' not in negative:
            raise RuntimeError('missing checker fault rejection')
        result['checker_injection'] = 'result observation corrupted, comparator rejected; not a live DiffTest test'
        if any(sha(Path(path)) != digest for path, digest in pins.items()):
            raise RuntimeError('source changed during prototype test')
        result['status'] = 'INDEPENDENT_DOT16_PROTOTYPE_PASS'
    except BaseException as error:
        result.update(status='FAILED', error=repr(error))
        raise
    finally:
        result['finished'] = datetime.now(timezone.utc).isoformat()
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--variant', choices=('baseline8', 'direct16', 'split16'), required=True)
    p.add_argument('--jobs', type=int, default=2)
    a = p.parse_args()
    print(json.dumps(run(a.repo.resolve(), a.output.resolve(), a.variant, a.jobs), indent=2))
