"""Recheck a pinned T14 archive without executing archived commands.

Default --level trace requires BOTH original streams and the existing O0 mapper.
Explicit --level program is a useful smaller check, NEVER a hardware-trace pass.
Only the selected pilot is pinned; this is not the whole O0 diagnostic matrix.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import zlib
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEFAULT_PINS = HERE / 'pilot-t14-batch128.json'
ANSI = re.compile(r'\x1b\[[0-9;]*m')
LIMIT = 256 * 1024 * 1024


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def integer(value: Any, name: str, minimum: int = 0, maximum: int | None = None) -> int:
    require(type(value) is int and value >= minimum, f'invalid integer: {name}')
    require(maximum is None or value <= maximum, f'integer out of range: {name}')
    return value


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def strict_json(data: bytes) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'duplicate JSON key: {key}')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('non-finite JSON constant: ' + value)
    result = json.loads(data.decode('utf-8'), object_pairs_hook=unique, parse_constant=constant)
    require(type(result) is dict, 'JSON root must be an object')
    return result


def contained(root: Path, relative: str) -> Path:
    require(type(relative) is str and relative and not Path(relative).is_absolute(), 'expected repository-relative path')
    require('..' not in Path(relative).parts, 'parent traversal rejected')
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), 'path escapes repository')
    return path


def pinned_file(root: Path, item: dict[str, str]) -> tuple[bytes, dict[str, str]]:
    path = contained(root, item['path'])
    require(path.is_file(), 'missing pinned file: ' + item['path'])
    require(path.stat().st_size <= LIMIT, 'stored file too large')
    data = path.read_bytes()
    require(blob(data) == item['git_blob'], 'Git blob mismatch: ' + item['path'])
    return data, {'path': item['path'], 'git_blob': blob(data), 'sha256': sha256(data)}


def decode_gzip(data: bytes, expected: str) -> str:
    import io
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT, 'uncompressed stream too large')
    require(sha256(raw) == expected, 'uncompressed stream digest mismatch')
    return raw.decode('utf-8')


def option(command: list[str], name: str) -> str:
    values = []
    for i, word in enumerate(command):
        if word == name:
            require(i + 1 < len(command), 'missing option argument')
            values.append(command[i + 1])
        elif word.startswith(name + '='):
            values.append(word[len(name) + 1:])
    require(len(values) == 1, 'missing/duplicate command option: ' + name)
    return values[0]


def check_metadata(analysis: dict, run: dict, pin: dict) -> None:
    require(type(pin['schema']) is int and pin['schema'] == 1, 'unsupported pilot schema')
    require(type(pin['fu_latency']) is int and pin['fu_latency'] == 2, 'unsupported pilot mode')
    require(type(pin['source_commit']) is str and re.fullmatch('[0-9a-f]{40}', pin['source_commit']) is not None, 'invalid source commit')
    require(pin['scenario'] == 'batch' and integer(pin['n'], 'n', 1) * 4 == integer(pin['dots'], 'dots', 1), 'pilot must use batch4 workload')
    require(analysis['status'] == 'PASS', 'archive analysis did not pass')
    require(analysis['scope'] == 'full-core DiffTest, exact state and calibrated CSR windows', 'wrong archive scope')
    require(run['image'] == pin['image'] and run['replay'] == 0, 'wrong image/replay')
    require(type(run['replay']) is int, 'replay is not integer')
    require(type(run['exit_code']) is int and run['exit_code'] == 0, 'run did not exit successfully')
    require(run['single_core'] is True and type(run['emu_threads']) is int and run['emu_threads'] == 1, 'wrong core/thread setting')
    require(analysis['raw_sha256'] == run['raw_sha256'], 'analysis/run refer to different raw logs')
    for key in ('stdout.log', 'stderr.log'):
        require(re.fullmatch('[0-9a-f]{64}', run['raw_sha256'][key]) is not None, 'invalid raw digest')
    cmd = run['command']
    require(type(cmd) is list and len(cmd) > 4 and all(type(s) is str for s in cmd), 'bad archived command')
    require(cmd[:2] == ['timeout', '120m'], 'unexpected runner prefix')
    roles = {'emu': cmd[2], 'image': option(cmd, '-i'), 'reference': option(cmd, '--diff'), 'flash': option(cmd, '--flash')}
    for role, path in roles.items():
        require(run['files'][path] == pin['runtime_sha256'][role], 'runtime identity changed: ' + role)
    require(roles['image'] == run['build'] + '/vdot-perf.bin', 'build/image mismatch')
    require(analysis['image_sha256'] == pin['runtime_sha256']['image'], 'analysis image mismatch')
    require(option(cmd, '--ram-size') == '128MB' and option(cmd, '--seed') == '1', 'runtime configuration mismatch')
    samples = analysis['samples']
    require(type(samples) is list and len(samples) == 12, 'missing/extra sample')
    previous_tick = -1
    for seq, s in enumerate(samples):
        repeat = seq // 2
        method = ('vdot', 'rvv')[seq % 2] if repeat % 2 == 0 else ('rvv', 'vdot')[seq % 2]
        phase = 'first' if repeat == 0 else 'warmup' if repeat == 1 else 'measured'
        for key, value in {'seq': seq, 'repeat': repeat, 'dataset': 0, 'n': pin['n'], 'dots': pin['dots']}.items():
            require(integer(s[key], key) == value, 'sample identity mismatch: ' + key)
        require(s['scenario'] == pin['scenario'] and s['method'] == method and s['phase'] == phase, 'sample ordering/scope mismatch')
        require(s['id'] == f"{pin['scenario']}-{pin['n']}-{method}", 'sample id mismatch')
        c, t = s['counter_values'], s['sample_ticks']
        require(len(c) == len(t) == 4, 'counter layout mismatch')
        for value in c: integer(value, 'counter', maximum=2**64-1)
        for value in t: integer(value, 'sample tick')
        require(previous_tick < t[0] < t[1] < t[2] < t[3], 'counter/window ordering mismatch')
        previous_tick = t[3]
        require(integer(s['cycles'], 'cycles', 1) == c[2] - c[1] == t[2] - t[1], 'cycle arithmetic mismatch')
        require(integer(s['instructions'], 'instructions', 1) == c[3] - c[0], 'retirement arithmetic mismatch')
    fu = analysis['fu']
    for key in ('accepted', 'responses', 'killed', 'stalls', 'committed', 'response_latency_min', 'response_latency_max', 'acceptance_interval_min'):
        integer(fu[key], 'fu.' + key)
    require(fu['accepted'] == fu['responses'] + fu['killed'], 'archived FU conservation mismatch')
    require(fu['committed'] == 6 * pin['dots'], 'archived retired dot count mismatch')
    hist = fu['response_latency_histogram']
    require(type(hist) is dict and hist, 'missing latency histogram')
    for key, value in hist.items():
        require(re.fullmatch('[0-9]+', key) is not None and str(int(key)) == key, 'invalid histogram key')
        integer(value, 'histogram count', 1)
    require(sum(hist.values()) == fu['responses'], 'histogram count mismatch')
    require(min(map(int, hist)) == fu['response_latency_min'] and max(map(int, hist)) == fu['response_latency_max'], 'histogram endpoints mismatch')
    require(fu['response_latency_min'] >= 2 and fu['acceptance_interval_min'] >= 3, 'not the frozen non-overlap mode')


def check_stdout(text: str, analysis: dict, run: dict) -> None:
    text = ANSI.sub('', text).replace('\r\n', '\n')
    require(not re.search(r'HIT BAD TRAP|Assertion failed|different at pc|T13_FAIL|T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)', text), 'failure in program stream')
    require('T12_ACCEPT ' not in text and 'T12_VFEX4_' not in text, 'mixed hardware/program streams')
    for banner in ('The first instruction of core 0 has commited. Difftest enabled.', 'The reference model is ' + option(run['command'], '--diff'), 'The image is ' + option(run['command'], '-i')):
        require(banner in text, 'missing/mismatched runtime banner')
    pattern = r'^T13_P seq=([0-9]+) c=([0-9]+) i=([0-9]+)$'
    actual = list(re.finditer(pattern, text, re.M))
    expected = [(s['seq'], s['cycles'], s['instructions']) for s in analysis['samples']]
    require([tuple(map(int, m.groups())) for m in actual] == expected, 'program samples do not match archived analysis')
    begin = list(re.finditer(r'^T13_BEGIN suite=performance dataset=0 plan=12 contract=vdot-s8x8-r32-v0.1$', text, re.M))
    summary = list(re.finditer(r'^T13_SUMMARY executed=12 failures=0 scratch_control=1$', text, re.M))
    controls = list(re.finditer(r'^T13_CONTROLS detected=6 expected=6$', text, re.M))
    scratch = list(re.finditer(r'^T13_SCRATCH_CONTROL allowed=1$', text, re.M))
    require(len(begin) == len(summary) == len(controls) == len(scratch) == 1, 'missing/duplicate program guards')
    require(begin[0].start() < controls[0].start() < actual[0].start() < scratch[0].start() < actual[1].start() and actual[-1].end() < summary[0].start(), 'program guard order mismatch')
    traps = list(re.finditer('HIT GOOD TRAP', text))
    require(len(traps) == 1 and traps[0].start() > summary[0].end(), 'missing/early/duplicate GOOD TRAP')
    # Reject extra malformed T13 lines, not just well-formed duplicate matches.
    tags = re.findall(r'T13_[A-Z0-9_]+', text)
    require(Counter(tags) == Counter({'T13_P': 12, 'T13_BEGIN': 1, 'T13_CONTROLS': 1, 'T13_SCRATCH_CONTROL': 1, 'T13_SUMMARY': 1}), 'unknown/extra program records')


def load_diagnostics(root: Path):
    path = contained(root, 'team/optimizations/o0/analyze.py')
    require(blob(path.read_bytes()) == '3cbed275724ce17393c8a3855a5824e3ca01bfd8', 'O0 analyzer changed; review adapter before reuse')
    spec = importlib.util.spec_from_file_location('o0_frozen_diagnostics', path)
    require(spec is not None and spec.loader is not None, 'cannot import analyzer')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay(root: Path, pin: dict, level: str) -> dict:
    require(level in ('program', 'trace'), 'invalid replay level')
    require(pin['schema'] == 1, 'unknown pin schema')
    materialized = {}
    provenance = {}
    for role in ('analysis', 'result', 'stdout'):
        data, record = pinned_file(root, pin['files'][role])
        materialized[role] = data
        provenance[role] = record
    analysis = strict_json(materialized['analysis'])
    run = strict_json(materialized['result'])
    check_metadata(analysis, run, pin)
    stdout = decode_gzip(materialized['stdout'], run['raw_sha256']['stdout.log'])
    check_stdout(stdout, analysis, run)
    result = {
        'schema': 1, 'status': 'O0_PROGRAM_LOG_RECHECK_PASS_TRACE_PENDING',
        'source_commit': pin['source_commit'], 'run': pin['image'] + '-r0',
        'source_files': provenance,
        'program_windows_checked': 12,
        'measured_cycles_from_original_stdout': {
            m: [s['cycles'] for s in analysis['samples'] if s['method'] == m and s['phase'] == 'measured']
            for m in ('vdot', 'rvv')},
        'archived_fu_summary_NOT_REPLAYED': analysis['fu'],
        'raw_hardware_trace_replayed': False,
        'new_hardware_run': False, 'o0_complete': False, 'o1_implemented': False,
        'limits': ['One dataset and one replay of the T14 batch128 pilot, not the newer unified benchmark.',
                   'Program-output and archive consistency checks do not recreate hardware event evidence.',
                   'No new speedup, parent busy attribution, PPA or full-ISA acceptance is claimed.'],
    }
    if level == 'program':
        return result
    raw, record = pinned_file(root, pin['files']['stderr'])
    stderr = decode_gzip(raw, run['raw_sha256']['stderr.log'])
    module = load_diagnostics(root)
    diagnosis = module.analyze(stderr, fu_latency=2)
    fu = analysis['fu']
    for current, archived in [('accepted', 'accepted'), ('responded', 'responses'), ('killed', 'killed'), ('writeback_stall_events', 'stalls')]:
        require(diagnosis['counts'][current] == fu[archived], 'replayed FU count mismatch: ' + current)
    require(diagnosis['response_latency_histogram'] == fu['response_latency_histogram'], 'replayed latency histogram mismatch')
    gaps = diagnosis['observed_accept_gap_histogram']
    require(gaps and min(map(int, gaps)) == fu['acceptance_interval_min'], 'replayed accept interval mismatch')
    require(diagnosis['counts']['pending'] == 0, 'unfinished replay')
    result['source_files']['stderr'] = record
    result['status'] = 'O0_PILOT_TRACE_REPLAY_PASS_NOT_FULL_O0'
    result['raw_hardware_trace_replayed'] = True
    result.pop('archived_fu_summary_NOT_REPLAYED')
    result['replayed_diagnostics'] = diagnosis
    result['window_observations'] = []
    for sample in analysis['samples']:
        start, end = sample['sample_ticks'][1:3]
        accepted = [t for t in diagnosis['transactions'] if start <= t['accept_cycle'] < end]
        result['window_observations'].append({
            'seq': sample['seq'], 'method': sample['method'], 'phase': sample['phase'],
            'start_inclusive': start, 'end_exclusive': end, 'declared_dots': sample['dots'],
            'observed_FU_accepts_including_speculation': len(accepted),
            'response_coincident_busy_wait_cycles': [c for c in diagnosis['response_coincident_busy_wait_cycles'] if start <= c < end],
            'internal_accept_gaps': [b['accept_cycle'] - a['accept_cycle'] for a, b in zip(accepted, accepted[1:])],
        })
    result['limits'][1] = 'Full raw streams were replayed for this one pilot only; application completion and all ISA state still rely on the original acceptance.'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--pins', type=Path, default=DEFAULT_PINS)
    parser.add_argument('--level', choices=('program', 'trace'), default='trace')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        require(not args.output.exists(), 'output already exists')
        require(not args.output.resolve().is_relative_to((args.repository / 'team/evidence').resolve()),
                'write to a fresh work directory, not sealed historical evidence')
        pin = strict_json(args.pins.read_bytes())
        result = replay(args.repository, pin, args.level)
        result['pins_sha256'] = sha256(args.pins.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps({'status': result['status'], 'raw_hardware_trace_replayed': result['raw_hardware_trace_replayed']}))
        return 0
    except (ValueError, OSError, EOFError, KeyError, TypeError, IndexError, zlib.error) as exc:
        print('O0_ARCHIVE_RECHECK_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
