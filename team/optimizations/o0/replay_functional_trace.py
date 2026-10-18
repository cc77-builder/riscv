"""Replay the identified T14 functional trace; never label it batch throughput.

This is a pinned read-only companion to analyze.py. It preserves the old
performance pilot and never executes archived build or simulator commands.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
SOURCE_COMMIT = 'a877e0575ea91392edc7816637e51ae8d1689b36'
PREFIX = 'team/evidence/t14-optimization-20261016/fullcore/'
RUN = 'functional-d0-s06-r0'
FILES = {
    'stderr': (PREFIX + 'performance/' + RUN + '/stderr.log.gz', '0b3030b5e51d1619b705db1ab73fc2f10805db8e'),
    'stdout': (PREFIX + 'performance/' + RUN + '/stdout.log.gz', 'e51ef02edb2159a22bcc60236d0c652034736036'),
    'result': (PREFIX + 'performance/' + RUN + '/result.json', '621d7b0a72d65eccf7cff8644e465d59a6d6ef17'),
    'analysis': (PREFIX + 'analysis/' + RUN + '.json', 'f3105ae1c70a64359f5dd2344d97c8c9487981c5'),
    # Reviewed integrated tools; historical input/archive identities stay fixed.
    'analyzer': ('team/optimizations/o0/analyze.py', '3cbed275724ce17393c8a3855a5824e3ca01bfd8'),
    'parser': ('team/scripts/check-vdot-regression.py', '4093e685388f915dd78a15729889631999dba74d'),
}
EXPECTED_PERFORMANCE_BLOB = '757ff41dae73226efc6670e6b7c68ccc2a5d7b5d'
LIMIT = 64 * 1024 * 1024
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def read_verified(path, expected):
    with path.open('rb') as stream:
        data = stream.read(LIMIT + 1)
    require(len(data) <= LIMIT, 'stored file size limit exceeded')
    actual = blob(data)
    require(actual == expected, f'wrong file identity: {path.name}; expected {expected}, got {actual}')
    return data


def unpack(data, expected_sha256):
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT, 'uncompressed file size limit exceeded')
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'raw stream digest mismatch')
    return raw.decode('utf-8')


def load_analyzer():
    for role in ('analyzer', 'parser'):
        rel, sha = FILES[role]
        read_verified(ROOT / rel, sha)
    spec = importlib.util.spec_from_file_location('functional_frozen_o0', ROOT / FILES['analyzer'][0])
    require(spec is not None and spec.loader is not None, 'cannot load frozen analyzer')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review(stderr, stdout, analysis, run):
    require(run['image'] == 'functional-d0-s06' and run['replay'] == 0, 'wrong archived run')
    require(type(run['exit_code']) is int and run['exit_code'] == 0, 'unsuccessful archived runtime')
    require(run['single_core'] is True and run['emu_threads'] == 1, 'wrong runtime configuration')
    require(analysis['raw_sha256'] == run['raw_sha256'], 'mixed archived streams')
    require(analysis['status'] == 'PASS', 'original analysis did not pass')
    samples = analysis['samples']
    require(len(samples) == 12, 'expected twelve functional calls')
    text = ANSI.sub('', stdout).replace('\r\n', '\n')
    require(not re.search(r'HIT BAD TRAP|Assertion failed|different at pc|T13_FAIL', text + stderr), 'runtime failure marker')
    require('The first instruction of core 0 has commited. Difftest enabled.' in text, 'missing DiffTest banner')
    for option, banner in (('-i', 'The image is '), ('--diff', 'The reference model is ')):
        cmd = run['command']
        value = cmd[cmd.index(option) + 1] if option in cmd else next(s.split('=', 1)[1] for s in cmd if s.startswith(option + '='))
        require(banner + value in text, 'runtime banner does not match archive')
    begin = 'T13_BEGIN suite=functional dataset=0 plan=12 contract=vdot-s8x8-r32-v0.1'
    summary = 'T13_SUMMARY executed=12 failures=0 scratch_control=1'
    require(text.count(begin) == text.count(summary) == text.count('HIT GOOD TRAP') == 1, 'missing/duplicate completion markers')
    require(text.index(begin) < text.index(summary) < text.index('HIT GOOD TRAP'), 'invalid completion ordering')
    records = []
    pattern = (r'^T13_CASE seq=(\d+) id=(\S+) phase=functional repeat=0 result=PASS '
               r'cycles=(\d+),(\d+) instret=(\d+),(\d+) iterations=1 '
               r'csr=(\d+(?:/\d+){6}) dest=([0-9a-f]{32}) checked_regs=(\d+) stream_checked=0$')
    matches = list(re.finditer(pattern, text, re.M))
    require(len(matches) == 12 and text.count('T13_CASE') == 12, 'invalid functional record set')
    tags = Counter(re.findall(r'T13_[A-Z0-9_]+', text))
    require(tags == Counter(T13_CASE=12, T13_BEGIN=1, T13_CONTROLS=1, T13_SCRATCH_CONTROL=1, T13_SUMMARY=1), 'unknown program record')
    controls = 'T13_CONTROLS detected=6 expected=6'
    scratch = 'T13_SCRATCH_CONTROL allowed=1'
    require(text.count(controls) == text.count(scratch) == 1, 'missing program self-checks')
    require(text.index(begin) < text.index(controls) < matches[0].start() < text.index(scratch) < matches[1].start(), 'invalid self-check ordering')
    require(matches[-1].end() < text.index(summary), 'summary precedes final case')
    # Compare UART counters to the recorded full-core CSR sampling events, using
    # integers throughout; these absolute counters are larger than 2**53.
    csr_events = list(re.finditer(r'^T13_CSR_SAMPLE cycle=\s*(\d+) addr=(0x[0-9a-f]+) data=(0x[0-9a-f]+) wen=0$', stderr, re.M))
    require(len(csr_events) == 48 and stderr.count('T13_CSR_SAMPLE') == 48, 'invalid counter-event set')
    for seq, (match, sample) in enumerate(zip(matches, samples)):
        number, ident, c0, c1, i0, i1, csr, dest, regs = match.groups()
        method = 'vdot' if seq % 2 == 0 else 'rvv'
        require(int(number) == sample['seq'] == seq and ident == sample['id'], 'sample identity mismatch')
        require(sample['scenario'] == 'equivalence' and sample['phase'] == 'functional' and sample['method'] == method, 'functional/performance scope mismatch')
        require(sample['n'] == sample['dots'] == 1 and sample['repeat'] == sample['dataset'] == 0, 'workload scope mismatch')
        counters = [int(i0), int(c0), int(c1), int(i1)]
        require(counters == sample['counter_values'], 'UART/archive counter mismatch')
        require(all(type(v) is int and 0 <= v < 2**64 for v in sample['counter_values']), 'invalid 64-bit counter')
        ticks = sample['sample_ticks']
        require(len(ticks) == 4 and all(a < b for a, b in zip(ticks, ticks[1:])), 'invalid counter ordering')
        require(int(c1)-int(c0) == sample['cycles'] == ticks[2]-ticks[1], 'cycle delta mismatch')
        require(int(i1)-int(i0) == sample['instructions'], 'instruction delta mismatch')
        for j, event in enumerate(csr_events[4*seq:4*seq+4]):
            tick, addr, data = event.groups()
            require(int(tick) == ticks[j] and int(data, 16) == counters[j], 'hardware/UART counter mismatch')
            require(int(addr, 16) == (0xc02, 0xc00, 0xc00, 0xc02)[j], 'wrong counter CSR address')
        require(int(regs) == (32 if method == 'vdot' else 30), 'unexpected declared scratch/register scope')
        require(int(dest, 16) < 2**32, 'nonzero high 96 result bits')
        records.append({'seq': seq, 'id': ident, 'method': method, 'dest': dest, 'csr': csr, 'sample_ticks': ticks})
    for a, b in zip(records[::2], records[1::2]):
        require(a['dest'] == b['dest'] and a['csr'] == b['csr'], 'vdot/RVV recorded result mismatch')
    analyzer = load_analyzer()
    diagnosis = analyzer.analyze(stderr, fu_latency=2)
    checker = analyzer.load_parser()
    events, _ = checker.extract_events(stderr)
    mapped = checker.normalize_fu_cycles(events, min_response_latency=2)
    counts = Counter(e[2] for e in mapped)
    archived = analysis['fu']
    for now, old in (('accepted','accepted'), ('responded','responses'), ('killed','killed'), ('writeback_stall_events','stalls')):
        require(diagnosis['counts'][now] == archived[old], 'FU summary count mismatch')
    require(diagnosis['response_latency_histogram'] == archived['response_latency_histogram'], 'FU latency summary mismatch')
    require(min(map(int, diagnosis['observed_accept_gap_histogram'])) == archived['acceptance_interval_min'], 'accept-gap summary mismatch')
    require(counts['ENQUEUE'] == counts['COMMIT'] == archived['committed'] == 6, 'incomplete functional lifetime set')
    rows = []
    for transaction in diagnosis['transactions']:
        rob = transaction['rob']
        def one(kind):
            found = [e for e in mapped if e[2] == kind and e[3]['rob'] == rob]
            require(len(found) == 1, 'missing/duplicate event for this functional lifetime: ' + kind)
            return found[0]
        enqueue, response, commit = one('ENQUEUE'), one('RESPONSE'), one('COMMIT')
        require(enqueue[3]['pc'] == commit[3]['pc'], 'enqueue/commit PC mismatch')
        word = int(enqueue[3]['word'], 16)
        require(word & 0xfe00707f == 0x0200000b, 'non-vdot encoding')
        ac, rc = transaction['accept_cycle'], transaction['end_cycle']
        require(enqueue[0] <= ac < rc <= commit[0], 'invalid functional lifetime ordering')
        sample = [r for r in records if r['method'] == 'vdot' and r['sample_ticks'][1] <= enqueue[0] and commit[0] < r['sample_ticks'][2]]
        require(len(sample) == 1, 'lifetime not bound to exactly one vdot window')
        record = sample[0]
        require(int(response[3]['data'], 16) == int(record['dest'], 16), 'FU/program full128 result mismatch')
        rows.append(dict(case_id=record['id'], rob=rob, vd=(word >> 7) & 31,
                         pdest=transaction['pdest'], pc=enqueue[3]['pc'], word=enqueue[3]['word'],
                         result128=record['dest'], enqueue_cycle=enqueue[0], accept_cycle=ac,
                         response_cycle=rc, commit_cycle=commit[0], raw_accept_tick=transaction['raw_accept_tick'],
                         accept_to_response=rc-ac, accept_to_commit=commit[0]-ac))
    require(len({r['case_id'] for r in rows}) == 6, 'reused functional window')
    return {
        'status': 'O0_FUNCTIONAL_TRACE_REPLAY_PASS_NOT_THROUGHPUT',
        'source_commit': SOURCE_COMMIT, 'run': RUN, 'scope': 'existing functional trace, not the performance pilot',
        'raw_hardware_trace_replayed': True, 'new_hardware_run': False, 'o0_complete': False, 'o1_implemented': False,
        'checked_program_calls': 12, 'matched_CSR_sample_events': 48,
        'matched_vdot_lifetimes': len(rows), 'event_counts': dict(sorted(counts.items())),
        'diagnosis': diagnosis, 'lifetime_table': rows,
        'limits': [
            'Six isolated functional vdot calls, not a sustained throughput test.',
            'No VFEX4_WAIT/STALL observations does not prove absence of bottlenecks in other workloads.',
            'FU raw ticks advance on a gated clock; raw accept spacing is not hardware II.',
            'Full128 FU values and UART recorded destinations/CSR snapshots were correlated; ELF, golden inputs and all register state were not rerun.',
            'No new speedup, RTL test, timing/PPA, human ACK, or O1 adoption is claimed.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stderr', type=Path, help='uploaded original gzip; default is the identified repository trace')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        require(not args.output.exists(), 'output already exists')
        require(not args.output.resolve().is_relative_to((ROOT / 'team/evidence').resolve()), 'do not overwrite historical evidence')
        data = {}; provenance = {}
        for role, (rel, sha) in FILES.items():
            path = args.stderr if role == 'stderr' and args.stderr else ROOT / rel
            data[role] = read_verified(path, sha)
            provenance[role] = {'path': rel, 'git_blob': sha, 'sha256': hashlib.sha256(data[role]).hexdigest()}
        run = json.loads(data['result']); analysis = json.loads(data['analysis'])
        stderr = unpack(data['stderr'], run['raw_sha256']['stderr.log'])
        stdout = unpack(data['stdout'], run['raw_sha256']['stdout.log'])
        result = review(stderr, stdout, analysis, run)
        result['source_files'] = provenance
        result['uploaded_stderr_matches_performance_pilot'] = blob(data['stderr']) == EXPECTED_PERFORMANCE_BLOB
        result['raw_sha256'] = run['raw_sha256']
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
        print(json.dumps({k: result[k] for k in ('status','matched_vdot_lifetimes','raw_hardware_trace_replayed','o0_complete')}))
        return 0
    except (ValueError, OSError, EOFError, KeyError, TypeError, StopIteration) as exc:
        print('O0_FUNCTIONAL_REPLAY_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
