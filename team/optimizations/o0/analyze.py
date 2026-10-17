"""O0 diagnostics for the existing single-outstanding T12/T14 observer protocol.

Read-only: reuse the pinned parser/clock mapper; never infer speedup or hardware
II from a workload's acceptance gaps. This is not full-core acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PARSER = ROOT / 'team/scripts/check-vdot-regression.py'
PARSER_BLOB = '4093e685388f915dd78a15729889631999dba74d'
# Reviewed integration: same event parser/clock mapping; retained James ROB fixes.
BASE_COMMIT = '3d051f0d870945215724bcc579496403e8884aee'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def load_parser() -> Any:
    # This adapter deliberately refuses a changed mapper or an O1/O2 protocol.
    # Review a new schema instead of weakening the frozen T12 acceptance tool.
    require(git_blob(PARSER.read_bytes()) == PARSER_BLOB, 'T12 parser source drift')
    spec = importlib.util.spec_from_file_location('o0_t12_parser', PARSER)
    require(spec is not None and spec.loader is not None, 'cannot load T12 parser')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def histogram(values: list[int]) -> dict[str, int]:
    return {str(k): v for k, v in sorted(Counter(values).items())}


def analyze(stderr: str, *, fu_latency: int) -> dict[str, Any]:
    require(fu_latency in (2, 3), 'explicit baseline/T14 latency must be 3/2')
    checker = load_parser()
    require(not re.search(r'Assertion failed|different at pc|HIT BAD TRAP', stderr),
            'failure marker in hardware stream')
    events, _ = checker.extract_events(stderr)
    require(events, 'no observer records')
    seen = set()
    parent_slots = set()
    for cycle, _, kind, fields in events:
        signature = (kind, tuple(sorted(fields.items())))
        require(signature not in seen, 'duplicate observer record')
        seen.add(signature)
        for key in ('rob', 'redirect'):
            if key in fields:
                flag, value = map(int, fields[key].split(':'))
                require(flag in (0, 1) and 0 <= value < checker.ROB_SIZE,
                        'ROB outside pinned MinimalConfig')
        if kind.startswith('VFEX4_'):
            require(cycle not in parent_slots, 'multiple VFEX4 records in one cycle')
            parent_slots.add(cycle)
        if kind == 'VFEX4_WAIT':
            require(fields['busy'] in ('0', '1'), 'invalid busy bit')
        if kind in ('ACCEPT', 'RESPONSE'):
            require(fields['illegal'] in ('0', '1'), 'invalid illegal bit')
    normalized = checker.normalize_fu_cycles(events, min_response_latency=fu_latency)
    # Parent cycles are un-gated. The imported mapper anchors *each* FU lifetime
    # and validates surrounding global events; raw FU ticks are not CPU cycles.
    normalized.sort(key=lambda event: (event[0], event[1]))
    pending = None
    transactions = []
    waits = Counter()
    parent_accepts = Counter()
    busy_wait_cycles = set()
    redirects = set()
    for cycle, _, kind, fields in normalized:
        if kind == 'VFEX4_ACCEPT':
            parent_accepts[fields['fu']] += 1
        elif kind == 'VFEX4_WAIT':
            is_vdot = int(fields['fu'], 16) == checker.VDOT_FU_TYPE
            label = ('vdot' if is_vdot else 'other') + ('_busy' if fields['busy'] == '1' else '_not_busy')
            waits[label] += 1
            if is_vdot and fields['busy'] == '1':
                busy_wait_cycles.add(cycle)
        elif kind == 'REDIRECT':
            redirects.add(cycle)
        elif kind == 'ACCEPT':
            require(pending is None, 'multiple outstanding requests; O1/O2 needs a new mapper')
            pending = {'index': len(transactions), 'rob': fields['rob'],
                       'pdest': int(fields['pdest']), 'illegal': int(fields['illegal']),
                       'accept_cycle': cycle, 'raw_accept_tick': int(fields['cycle']),
                       'stall_cycles': []}
        elif kind in ('STALL', 'RESPONSE', 'KILL'):
            require(pending is not None and pending['rob'] == fields['rob'], 'unbound FU event')
            if kind == 'STALL':
                pending['stall_cycles'].append(cycle)
                continue
            if kind == 'RESPONSE':
                require(pending['pdest'] == int(fields['pdest']), 'response pdest mismatch')
                require(pending['illegal'] == int(fields['illegal']), 'response exception mismatch')
                data = int(fields['data'], 16)
                require(data < (1 << 32), 'nonzero high 96 result bits')
                if pending['illegal']:
                    require(data == 0, 'illegal response data is not zero')
                first_stall = pending['accept_cycle'] + fu_latency
                stalls = pending['stall_cycles']
                require(len(stalls) == cycle - first_stall
                        and all(tick == first_stall + i for i, tick in enumerate(stalls)),
                        'response/stall history disagrees with frozen latency')
            pending['end_cycle'] = cycle
            pending['outcome'] = 'response' if kind == 'RESPONSE' else 'kill'
            pending['elapsed_cycles'] = cycle - pending['accept_cycle']
            pending['writeback_stall_events'] = len(pending.pop('stall_cycles'))
            transactions.append(pending)
            pending = None
    require(pending is None and transactions, 'empty or unfinished vdot lifetimes')
    responses = [t for t in transactions if t['outcome'] == 'response']
    killed = len(transactions) - len(responses)
    accept_gaps = []
    release_gaps = []
    for previous, current in zip(transactions, transactions[1:]):
        gap = current['accept_cycle'] - previous['accept_cycle']
        release_gap = current['accept_cycle'] - previous['end_cycle']
        require(release_gap >= 1, 'overlap is outside this frozen diagnostic schema')
        accept_gaps.append(gap)
        release_gaps.append(release_gap)
        previous['next_accept_cycle'] = current['accept_cycle']
        previous['release_to_next_accept_cycles'] = release_gap
    response_cycles = {t['end_cycle'] for t in responses}
    coincident = response_cycles & busy_wait_cycles
    return {
        'schema': 1, 'status': 'O0_DIAGNOSTICS_ONLY', 'base_commit': BASE_COMMIT,
        'parser_blob': PARSER_BLOB, 'fu_latency_contract': fu_latency,
        'counts': {'accepted': len(transactions), 'responded': len(responses),
                   'killed': killed, 'pending': 0,
                   'writeback_stall_events': sum(t['writeback_stall_events'] for t in transactions)},
        'response_latency_histogram': histogram([t['elapsed_cycles'] for t in responses]),
        'observed_accept_gap_histogram': histogram(accept_gaps),
        'release_to_next_accept_histogram': histogram(release_gaps),
        'parent_wait_event_counts': dict(sorted(waits.items())),
        'parent_accept_fu_counts': dict(sorted(parent_accepts.items())),
        'response_coincident_busy_wait_cycles': sorted(coincident),
        'coincident_with_observed_redirect': sorted(coincident & redirects),
        'transactions': transactions,
        'limits': [
            'Single-core pinned baseline/T14 only; no reset-in-flight or O1/O2 mapping.',
            'Counters include speculative transactions; they are not retired dot counts.',
            'Observed acceptance gaps are workload-dependent, not a measured hardware II.',
            'Busy-wait coincidence is not proof that same-cycle handoff would be legal.',
            'No samples of upstream valid/arbiter grant or idle cycles: causal attribution is incomplete.',
            'This does not validate arithmetic inputs, all ISA state, workload completion or speedup.',
        ],
    }


def read_stream(path: Path, limit: int) -> tuple[str, str]:
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rb') as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, 'log exceeds --max-log-mib')
    return data.decode('utf-8'), hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stderr', required=True, type=Path)
    parser.add_argument('--stdout', required=True, type=Path)
    parser.add_argument('--exit-code', required=True, type=int)
    parser.add_argument('--fu-latency', required=True, type=int, choices=(2, 3))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--max-log-mib', type=int, default=256)
    args = parser.parse_args()
    try:
        require(args.exit_code == 0, 'runtime did not exit successfully')
        require(args.max_log_mib > 0, '--max-log-mib must be positive')
        require(not args.output.exists(), 'output directory already exists')
        require(args.stderr.resolve() != args.stdout.resolve(), 'use separate original streams')
        stderr, err_hash = read_stream(args.stderr, args.max_log_mib * 1024 * 1024)
        stdout, out_hash = read_stream(args.stdout, args.max_log_mib * 1024 * 1024)
        require('The first instruction of core 0 has commited. Difftest enabled.' in stdout
                and 'The reference model is ' in stdout and 'HIT GOOD TRAP' in stdout,
                'missing DiffTest/normal termination banner in stdout')
        require('T12_VFEX4_' not in stdout and 'T12_ACCEPT ' not in stdout,
                'hardware records found in stdout; original streams required')
        require(not re.search(r'HIT BAD TRAP|Assertion failed|different at pc|T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)',
                              stderr + stdout), 'failure marker in run')
        result = analyze(stderr, fu_latency=args.fu_latency)
        result['inputs'] = {'stderr_sha256_uncompressed': err_hash,
                            'stdout_sha256_uncompressed': out_hash, 'exit_code': args.exit_code}
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / 'diagnosis.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        fields = ['index', 'rob', 'pdest', 'illegal', 'accept_cycle', 'raw_accept_tick',
                  'end_cycle', 'outcome', 'elapsed_cycles', 'writeback_stall_events',
                  'next_accept_cycle', 'release_to_next_accept_cycles']
        with (args.output / 'timeline.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(result['transactions'])
        print(json.dumps({'status': result['status'], 'counts': result['counts']}))
        return 0
    except (ValueError, OSError, EOFError) as exc:
        print(f'O0_DIAGNOSTIC_REJECTED: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
