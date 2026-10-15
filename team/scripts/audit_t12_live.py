"""Independent live-artifact audit for the T12 source-bound build/run format.

Never executes an emulator, compiler, or an executable named by a receipt.
Explicit --repo/--build/--run select the inspected project artifacts. Hashes bind
content, not the truth of an adversarially fabricated run. This is an additional
review gate, not a replacement for original process observation or DiffTest.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

U64_MAX = (1 << 64) - 1
HARDWARE = 'fcb16a8764d342339670df0bbf1bc67ef2028b86'
REQUIRED_SOURCES = {
    'team/workloads/t12-perf/main.c', 'team/workloads/t12-perf/Makefile',
    'team/workloads/t12-perf/sites.S', 'team/workloads/vdot-exceptions/harness.S',
    'team/workloads/vdot-exceptions/harness.h', 'team/workloads/vdot-exceptions/layout.h',
    'team/workloads/vdot-exceptions/judge.c', 'team/tests/generate_t12.py',
    'team/scripts/t12-tests.py', 'team/scripts/check_t12_compact.py',
    'team/scripts/artifact_guard.py',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique_object)


def check_counter_window(cycle_begin, cycle_end, instret_begin, instret_end, dots):
    for value in (cycle_begin, cycle_end, instret_begin, instret_end, dots):
        require(type(value) is int and 0 <= value <= U64_MAX,
                'counter/count is not an unsigned 64-bit integer')
    require(cycle_end > cycle_begin and instret_end > instret_begin,
            'nonpositive or wrapped uncalibrated measurement window')
    require(instret_end - instret_begin >= dots,
            'retired instruction count smaller than declared dot operations')
    # This necessary lower bound does not prove exact loop execution, serialize
    # rdcycle, or turn a raw window into a precise FU latency measurement.


def option(argv, name):
    require(isinstance(argv, list) and all(isinstance(v, str) for v in argv),
            'command must be a string argv array')
    indexes = [i for i, value in enumerate(argv) if value == name]
    require(len(indexes) == 1 and indexes[0] + 1 < len(argv),
            'missing/duplicate command argument: ' + name)
    return argv[indexes[0] + 1]


def check_recorded_process(record):
    require(type(record.get('exit_code')) is int and record['exit_code'] == 0,
            'nonzero/missing recorded process exit')
    require(record.get('timed_out') is False, 'timeout or unknown timeout status')
    require(type(record.get('pid')) is int and record['pid'] > 0,
            'missing process PID')
    begin, end = (datetime.datetime.fromisoformat(record[k])
                  for k in ('started_at', 'finished_at'))
    require(begin.tzinfo is not None and end.tzinfo is not None and end >= begin,
            'invalid recorded process timestamps')


def git(repo, *arguments):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(repo),
                                    *arguments], stderr=subprocess.PIPE)


def load_checker(repo):
    spec = importlib.util.spec_from_file_location(
        'independent_t12_checker', repo / 'team/scripts/check_t12_compact.py')
    require(spec is not None and spec.loader is not None, 'checker unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(repo, build, run, expected_source):
    repo, build, run = (Path(p).resolve() for p in (repo, build, run))
    require(re.fullmatch('[0-9a-f]{40}', expected_source or '') is not None,
            'explicit full tested source SHA required')
    require(git(repo, 'cat-file', '-t', expected_source).strip() == b'commit',
            'tested source is not a commit')
    require(not git(repo, 'diff', '--name-only', HARDWARE, expected_source,
                    '--', 'src', 'build.sc').strip(),
            'tested production hardware differs from the accepted EMU source')
    meta = read_json(run / 'receipt.json')
    compiled = read_json(build / 'build.json')
    process = read_json(run / 'run.process.json')
    check_recorded_process(process)
    require(meta.get('completed') is True, 'run did not complete')
    for key in ('argv', 'pid', 'cwd', 'started_at', 'finished_at', 'exit_code', 'timed_out'):
        require(meta.get(key) == process.get(key), 'receipt/process mismatch: ' + key)
    require(Path(process['cwd']).resolve() == run, 'wrong process output directory')
    require(meta['source'] == compiled['source'] == expected_source, 'wrong tested source')
    require(Path(meta['build']).resolve() == build, 'wrong selected build')
    require(meta['build_sha256'] == digest(build / 'build.json'), 'build record changed')
    require(meta['run_log_sha256'] == digest(run / 'run.log'), 'raw run log changed')
    require(compiled['tools_sha256'] == digest(build / 'tools.json'), 'tool manifest changed')
    require(compiled['image_sha256'] == meta['image_sha256'] == digest(build / 'test.bin'),
            'image changed')
    require(compiled['elf_sha256'] == digest(build / 'test.elf'), 'ELF changed')
    data = build / 'data'
    require(compiled['manifest_sha256'] == meta['manifest_sha256'] == digest(data / 'manifest.json'),
            'input manifest changed')
    require(meta['start'] == compiled['start'] and meta['limit'] == compiled['limit'],
            'wrong compiled slice')
    check_recorded_process(compiled['process'])
    for assignment in (f'T12_START={compiled["start"]}', f'T12_COUNT={compiled["limit"]}',
                       'T12_DATA=' + str(data), 'BINARY=' + str(build / 'test')):
        require(compiled['process']['argv'].count(assignment) == 1,
                'build command does not bind slice/image/data: ' + assignment)
    sources = compiled['sources']
    require(set(sources) >= REQUIRED_SOURCES, 'incomplete source manifest')
    for name, sha in sources.items():
        p = PurePosixPath(name)
        require(not p.is_absolute() and '..' not in p.parts and name.startswith('team/'),
                'unsafe source entry')
        content = git(repo, 'show', expected_source + ':' + name)
        require(hashlib.sha256(content).hexdigest() == sha, 'Git/source digest mismatch: ' + name)
    require(digest(repo / 'team/scripts/check_t12_compact.py') == sources['team/scripts/check_t12_compact.py'],
            'selected parser differs from the tested source; select a matching snapshot')
    checker = load_checker(repo)
    require(meta.get('difftest') is True and meta.get('ram') == '128MB', 'wrong runtime mode')
    require(meta.get('runtime_pins') == checker.PINS, 'wrong runtime pins')
    argv = process['argv']
    require('--no-diff' not in argv and '--ram-size=128MB' in argv,
            'unsupported runtime command')
    require(Path(option(argv, '-i')).resolve() == build / 'test.bin', 'wrong invoked image')
    for key, path in (('emu', argv[0]), ('reference', option(argv, '--diff')),
                      ('flash', option(argv, '--flash'))):
        require(digest(path) == checker.PINS[key], 'actual runtime binary changed: ' + key)
    checker.bind(meta, data, expected_source)
    result = checker.check((run / 'run.log').read_text(), data,
                           meta['start'], meta['limit'], process['exit_code'])
    for metric in result['metrics']:
        check_counter_window(metric['cycle_begin'], metric['cycle_end'],
                             metric['instret_begin'], metric['instret_end'], metric['dots'])
    return {'status': 'PASS_LIVE_ARTIFACT_AUDIT', 'source': expected_source,
            'start': meta['start'], 'limit': meta['limit'], 'executed': result['executed'],
            'metrics_checked': len(result['metrics']),
            'identities': result.get('identities', []), 'metrics': result['metrics'],
            'run_log_sha256': meta['run_log_sha256'],
            'receipt_sha256': digest(run / 'receipt.json'),
            'build_sha256': meta['build_sha256'],
            'checker_sha256': digest(repo / 'team/scripts/check_t12_compact.py'),
            'auditor_sha256': digest(__file__),
            'audited_at': datetime.datetime.now().astimezone().isoformat(),
            'scope': 'independent live artifact/source/counter bounds; not full microarchitectural coverage, precise counter calibration, STA, or adversarial log authentication'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'build', 'run', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-source', required=True)
    args = parser.parse_args()
    try:
        result = audit(args.repo, args.build, args.run, args.expected_source)
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write('\n')
        print(json.dumps({k: result[k] for k in ('status', 'source', 'start', 'executed', 'metrics_checked')}))
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        raise SystemExit('T12_INDEPENDENT_AUDIT_REJECTED: ' + str(error))


if __name__ == '__main__':
    main()
