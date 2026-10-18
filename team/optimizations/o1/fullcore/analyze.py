"""Strict O1 global-clock observer audit; not a workload or DiffTest verdict.

Legacy T12/T13/O0 parsers remain unchanged. O1 events are grouped by actual
ungated cycle, so old-response/new-accept printf order cannot change identity.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

VDOT = 1 << 35
FU_TYPES = {VDOT, 1 << 22, 1 << 26}
FIELDS = {
    'SCHEMA': 'version clock latency rob_size ftq_size vlen handoff',
    'VFEX4_ACCEPT': 'cycle seq rob fu pdest',
    'VFEX4_WAIT': 'cycle rob fu busy',
    'VFEX4_REDIRECT': 'cycle rob self',
    'ACCEPT': 'cycle seq rob pdest vl illegal vecwen v0wen',
    'RESPONSE': 'cycle seq rob pdest illegal data vecwen v0wen exception',
    'STALL': 'cycle seq rob pdest illegal data vecwen v0wen exception',
    'KILL': 'cycle seq rob pdest redirect self state',
    'HANDOFF': 'cycle oldseq newseq oldrob newrob oldpdest newpdest busy',
    'ENQUEUE': 'cycle rob pc ftq word',
    'COMMIT': 'cycle rob pc ftq',
    'REDIRECT': 'cycle rob ftq self',
}
FIELDS = {k: v.split() for k, v in FIELDS.items()}
POINTERS = {'rob', 'redirect', 'ftq', 'oldrob', 'newrob'}
HEXES = {'fu', 'data', 'exception', 'pc', 'word'}
BITS = {'illegal', 'vecwen', 'v0wen', 'self', 'busy', 'handoff', 'wen', 'empty', 'wait', 'block'}
T13_FIELDS = {
    'COUNTER_ENQUEUE': 'cycle rob pc word empty wait block',
    'CSR_SAMPLE': 'cycle addr data wen',
    'RETIRE': 'cycle slot rob pc word count data',
}
UART_TAGS = {
    'T12_BEGIN', 'T12_GROUP_PASS', 'T12_SUMMARY', 'T12_MISMATCH',
    'T12_CSR_FAIL', 'T12_SPEC_FAIL', 'T13_BEGIN', 'T13_P', 'T13_CASE',
    'T13_SUMMARY', 'T13_CONTROLS', 'T13_SCRATCH_CONTROL', 'T13_FAIL',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_fields(kind, body, fields, *, t13=False):
    parts = []
    for key in fields:
        pattern = (r'[01]\s*:\s*[0-9]+' if key in POINTERS else
                   r'global' if key == 'clock' else
                   r'0x[0-9a-fA-F]+' if key in HEXES or key == 'addr' else r'[0-9]+')
        parts.append(key + r'=\s*(' + pattern + ')')
    match = re.fullmatch(r'\s+'.join(parts) + r'\s*', body)
    require(match is not None, 'malformed observer event: ' + kind)
    result = {}
    for key, raw in zip(fields, match.groups()):
        value = re.sub(r'\s', '', raw)
        if key in POINTERS:
            flag, index = map(int, value.split(':'))
            require(index < (8 if key == 'ftq' else 48), 'pointer outside pinned configuration')
        elif key != 'clock':
            value = int(value, 16 if key in HEXES or key == 'addr' else 10)
            width = 128 if key == 'data' and not t13 else 32 if key == 'word' else 64
            require(value < 1 << width, 'observer field overflow: ' + key)
            if key in BITS:
                require(value in (0, 1), 'invalid bit field: ' + key)
        result[key] = value
    return result


def extract_events_and_uart(text):
    """Strip complete observed records, including records embedded in UART bytes.

    T13 records keep their existing schema and must still be checked by the
    existing calibrated-window checker when a caller claims performance.
    """
    events, schemas = [], []
    def take_o1(match):
        kind, body = match.groups()
        require(kind in FIELDS, 'unknown O1 observer event: ' + kind)
        fields = parse_fields(kind, body, FIELDS[kind])
        if kind == 'SCHEMA':
            require(not events and not schemas, 'duplicate or late O1 schema')
            expected = dict(version=1, clock='global', latency=2, rob_size=48,
                            ftq_size=8, vlen=128, handoff=fields['handoff'])
            require(fields == expected, 'unsupported O1 schema')
            schemas.append(fields)
        else:
            require(schemas, 'missing initial O1 schema')
            events.append((fields['cycle'], len(events), kind, fields))
        return ''
    uart = re.sub(r'O1_([A-Z0-9_]+)[ \t]+([^\n]*)\n', take_o1, text)
    require(len(schemas) == 1 and 'O1_' not in uart, 'missing, malformed or truncated O1 record')
    def take_t13(match):
        kind, body = match.groups()
        parse_fields('T13_' + kind, body, T13_FIELDS[kind].split(), t13=True)
        return ''
    uart = re.sub(r'T13_(COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+([^\n]*)\n', take_t13, uart)
    require(all(tag in UART_TAGS for tag in re.findall(r'T(?:12|13)_[A-Z0-9_]*', uart)),
            'unknown, legacy, malformed or truncated observer record')
    require(all(a[0] <= b[0] for a, b in zip(events, events[1:])),
            'global observer cycles are out of order')
    # Keep the established tuple interface and a schema event at index zero.
    return [(-1, -1, 'SCHEMA', schemas[0])] + events, uart


def ptr(value):
    flag, index = map(int, value.split(':'))
    return flag * 48 + index


def flushed(rob, origin, self_flush):
    delta = (ptr(rob) - ptr(origin)) % 96
    return 0 < delta < 48 or (delta == 0 and self_flush == 1)


def histogram(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


def analyze(text, *, require_complete=True):
    events, _ = extract_events_and_uart(text)
    schema = events[0][3]
    events = events[1:]
    groups = defaultdict(list)
    seen = set()
    for cycle, order, kind, fields in events:
        signature = (kind, tuple(fields.items()))
        require(signature not in seen, 'duplicate observer record')
        seen.add(signature)
        groups[cycle].append((kind, fields))
    counts = Counter({k: 0 for k in FIELDS if k != 'SCHEMA'})
    kinds = Counter()
    live, history, transactions = {}, [], []
    pending = None
    parent_seq = 0
    redirects = {}
    parent_redirects = {}
    last_rob = last_ftq = None
    for cycle, items in sorted(groups.items()):
        by_kind = defaultdict(list)
        for kind, f in items:
            by_kind[kind].append(f)
            counts[kind] += 1
        for name in ('VFEX4_ACCEPT', 'VFEX4_WAIT', 'VFEX4_REDIRECT', 'ACCEPT',
                     'RESPONSE', 'STALL', 'KILL', 'HANDOFF', 'REDIRECT'):
            require(len(by_kind[name]) <= 1, 'multiple ' + name + ' events in one cycle')
        one = lambda name: by_kind[name][0] if by_kind[name] else None
        pa, wait, pf = one('VFEX4_ACCEPT'), one('VFEX4_WAIT'), one('VFEX4_REDIRECT')
        accept, response, stall, kill = [one(k) for k in ('ACCEPT', 'RESPONSE', 'STALL', 'KILL')]
        handoff, redirect = one('HANDOFF'), one('REDIRECT')
        require(not (pa and wait), 'parent simultaneously accepted and waited')
        require(sum(x is not None for x in (response, stall, kill)) <= 1,
                'mutually exclusive old-response events')
        if pa:
            require(pa['seq'] == parent_seq, 'parent sequence is not contiguous from zero')
            parent_seq += 1
            require(pa['fu'] in FU_TYPES, 'unexpected VFEX4 functional unit')
            kinds[hex(pa['fu'])] += 1
        if wait:
            require(wait['fu'] in FU_TYPES, 'unexpected waiting VFEX4 functional unit')
        if pf:
            parent_redirects[cycle] = pf
            earlier = redirects.get(cycle - 1)
            require(earlier is not None and (pf['rob'], pf['self']) == (earlier['rob'], earlier['self']),
                    'parent redirect differs from prior-cycle ROB redirect')
            require(pa is None and accept is None and handoff is None,
                    'accept during real parent flush')
        if redirect:
            redirects[cycle] = redirect
        # Architectural retirement sees the allocation already present before
        # this edge; redirects/reallocation must never retroactively rebind it.
        for f in by_kind['COMMIT']:
            e = live.get(f['rob'])
            require(e is not None and not e['done'] and not e['cancelled'], 'unbound, cancelled or duplicate commit')
            require(e.get('response_cycle') is not None and e['response_cycle'] < cycle,
                    'commit without preceding FU response')
            require(e['pc'] == f['pc'] and e['ftq'] == f['ftq'], 'commit PC/FTQ identity mismatch')
            require(e['illegal'] == 0, 'illegal vdot retired normally')
            e['done'] = True
            e['commit_cycle'] = cycle
            rb, fq = int(f['rob'][0]), int(f['ftq'][0])
            if last_rob is not None and rb != last_rob:
                counts['ROB_WRAP'] += 1
            if last_ftq is not None and fq != last_ftq:
                counts['FTQ_WRAP'] += 1
            last_rob, last_ftq = rb, fq
        if redirect:
            for e in live.values():
                if not e['done'] and not e['cancelled'] and flushed(e['rob'], redirect['rob'], redirect['self']):
                    e['cancelled'] = True
                    e['cancel_cycle'] = cycle
                    e['cancel_is_younger'] = e['rob'] != redirect['rob']
        for f in by_kind['ENQUEUE']:
            require(redirect is None, 'enqueue observer contradicts ROB redirect gate')
            old = live.get(f['rob'])
            require(old is None or old['done'] or old['cancelled'], 'reallocated live ROB identity')
            require(pending is None or pending['entry'] is not old, 'reallocated pending ROB identity')
            require(f['word'] & 0xfe00707f == 0x0200000b, 'enqueued non-vdot instruction')
            e = dict(f, done=False, cancelled=False, accepted=False)
            live[f['rob']] = e
            history.append(e)
        old_pending = pending
        if old_pending is not None and wait:
            require(wait['busy'] == 1, 'parent reports idle with pending vdot')
        if old_pending is not None and pf and flushed(old_pending['rob'], pf['rob'], pf['self']):
            require(kill is not None, 'missing kill at matching parent redirect')
        if response or stall or kill:
            f = response or stall or kill
            require(pending is not None, 'old event without pending request')
            require((f['seq'], f['rob'], f['pdest']) == (pending['seq'], pending['rob'], pending['pdest']),
                    'old event sequence/ROB/pdest identity mismatch')
            age = cycle - pending['accept_cycle']
            if kill:
                require(pf is not None and (f['redirect'], f['self']) == (pf['rob'], pf['self']),
                        'kill without matching parent redirect')
                require(flushed(f['rob'], f['redirect'], f['self']), 'kill does not target this request')
                require(age >= 1 and f['state'] in (2, 3), 'invalid fused-state kill')
                expected_state = 2 if age == 1 else 3
                require(f['state'] == expected_state, 'kill state disagrees with age')
                require(pending['entry']['cancelled'], 'kill missing earlier ROB cancellation')
                expected_stalls = max(0, age - schema['latency'])
                require(len(pending['stalls']) == expected_stalls,
                        'kill missing preceding response stall history')
            else:
                require(age >= schema['latency'], 'response precedes fixed latency')
                require(f['illegal'] == pending['illegal'], 'response exception identity mismatch')
                require(f['exception'] == (4 if pending['illegal'] else 0), 'unexpected exception bits')
                require(f['data'] < 1 << 32, 'nonzero high 96 result bits')
                require(not pending['illegal'] or f['data'] == 0, 'illegal response data is not zero')
                require((f['vecwen'], f['v0wen']) ==
                        ((0, 0) if pending['illegal'] else (pending['vecwen'], pending['v0wen'])),
                        'response write enables changed')
                snapshot = tuple(f[k] for k in ('seq', 'rob', 'pdest', 'illegal', 'data', 'vecwen', 'v0wen', 'exception'))
                require(pending.get('snapshot', snapshot) == snapshot, 'stalled response changed')
                pending['snapshot'] = snapshot
                require(pending['stalls'] == list(range(pending['accept_cycle'] + schema['latency'], cycle)),
                        'response/stall history disagrees with fixed latency')
                if stall:
                    pending['stalls'].append(cycle)
                else:
                    pending['entry']['response_cycle'] = cycle
            if response or kill:
                pending['end_cycle'] = cycle
                pending['outcome'] = 'response' if response else 'kill'
                pending['elapsed_cycles'] = age
                pending['writeback_stall_events'] = len(pending['stalls'])
                pending = None
        if old_pending is not None and pa:
            require(response is not None and accept is not None and pa['fu'] == VDOT,
                    'new parent request overlaps unfinished/non-vdot handoff')
        if accept:
            require(pending is None, 'two outstanding vdot requests')
            require(pa is not None and pa['fu'] == VDOT and
                    all(pa[k] == accept[k] for k in ('seq', 'rob', 'pdest')),
                    'parent/child acceptance identity mismatch')
            require(accept['vecwen'] + accept['v0wen'] == 1, 'input destination class is not one-hot')
            require(accept['vl'] < 256 and (accept['vl'] == 8 or accept['illegal'] == 1),
                    'invalid renamed VL legality')
            e = live.get(accept['rob'])
            require(e is not None and not e['done'] and not e['accepted'], 'unbound or duplicate FU accept')
            # ROB redirects arrive one cycle before the real EXU flush. A
            # same-cycle younger accept remains possible and is killed next tick.
            require(not e['cancelled'] or e.get('cancel_cycle') == cycle,
                    'accept after prior ROB cancellation')
            vd = (e['word'] >> 7) & 31
            require((accept['vecwen'], accept['v0wen']) == (int(vd != 0), int(vd == 0)),
                    'input write enables disagree with decoded destination')
            e.update(accepted=True, seq=accept['seq'], illegal=accept['illegal'], pdest=accept['pdest'])
            pending = dict(accept, accept_cycle=cycle, stalls=[], entry=e)
            transactions.append(pending)
        if pa and pa['fu'] == VDOT:
            require(accept is not None, 'parent vdot acceptance has no child acceptance')
        if handoff or (response and accept):
            require(schema['handoff'] == 1 and handoff is not None and response is not None and accept is not None,
                    'missing or forbidden handoff event')
            expected = dict(cycle=cycle, oldseq=response['seq'], newseq=accept['seq'],
                            oldrob=response['rob'], newrob=accept['rob'],
                            oldpdest=response['pdest'], newpdest=accept['pdest'], busy=1)
            require(handoff == expected, 'handoff old/new identity mismatch')
        require(not (kill and accept), 'kill cannot hand off')
    last_cycle = max(groups, default=-1)
    if pending is not None and not require_complete:
        # The final tick may be cut between printf sites by an expected assertion,
        # but every fully observed earlier tick still needs its stalled response.
        required = list(range(pending['accept_cycle'] + schema['latency'], last_cycle))
        require(pending['stalls'][:len(required)] == required,
                'partial trace misses already-observed response stall history')
    for cycle, f in redirects.items():
        if not require_complete and cycle == last_cycle:
            continue
        pf = parent_redirects.get(cycle + 1)
        require(pf is not None and (f['rob'], f['self']) == (pf['rob'], pf['self']),
                'missing next-cycle real parent redirect')
    unfinished = [e for e in history if not e['done'] and not e['cancelled']]
    if require_complete:
        require(pending is None, 'unfinished FU request')
        require(not unfinished, 'unfinished ROB allocations')
    counts['ACCEPTED_THEN_SQUASHED'] = sum(e['accepted'] and e['cancelled'] for e in history)
    counts['ACCEPTED_YOUNGER_SQUASHED'] = sum(e['accepted'] and e['cancelled'] and e.get('cancel_is_younger', False) for e in history)
    require(counts['ACCEPT'] == counts['RESPONSE'] + counts['KILL'] + (pending is not None),
            'FU request conservation violated')
    public = [{k: v for k, v in t.items() if k not in ('entry', 'snapshot', 'stalls', 'cycle')}
              for t in transactions]
    responses = [t for t in public if t.get('outcome') == 'response']
    return dict(status='O1_TRACE_PASS' if require_complete else 'O1_PARTIAL_TRACE_AUDIT',
                input_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                schema=schema, counts=dict(counts), vfex4_fu_counts=dict(kinds),
                pending_count=int(pending is not None), unfinished_rob_count=len(unfinished),
                transactions=public,
                response_latency_histogram=histogram(t['elapsed_cycles'] for t in responses),
                observed_accept_gap_histogram=histogram(b['accept_cycle'] - a['accept_cycle']
                    for a, b in zip(public, public[1:])),
                clock_mapping='direct ungated VFEX4/ROB global cycle; no gated-clock reconstruction',
                scope='observer consistency only; workload/DiffTest verdict supplied separately',
                performance_measured=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        raw = gzip.decompress(args.log.read_bytes()) if args.log.suffix == '.gz' else args.log.read_bytes()
        result = analyze(raw.decode('utf-8'), require_complete=not args.partial)
        encoded = json.dumps(result, indent=2) + '\n'
        if args.output:
            require(not args.output.exists(), 'output already exists')
            args.output.write_text(encoded, encoding='utf-8')
        print(encoded, end='')
        return 0
    except (ValueError, OSError, EOFError) as exc:
        print('O1_TRACE_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
