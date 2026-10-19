"""Strict O2 two-slot global-clock audit; existing O1 observers remain immutable.

The arithmetic oracle recomputes signed low-eight-byte products from accepted
sources. ISA legality and architectural state still require the frozen workload
and independent NEMU DiffTest. Debug sequences never stand in for real identity.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from functools import cmp_to_key
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

VDOT = 1 << 35
FU_TYPES = {VDOT, 1 << 22, 1 << 26}
FIELDS = {
    'SCHEMA': 'version clock latency slots rob_size ftq_size vlen vpu_width perf_width',
    'STATE': 'cycle pvalid pseq prob ppdest rvalid rseq rrob rpdest occupancy invalid inready vready outvalid outready move killp killr divactive divseq divoccupied busy',
    'VFEX4_ACCEPT': 'cycle seq rob fu pdest',
    'VFEX4_WAIT': 'cycle rob fu busy',
    'VFEX4_REDIRECT': 'cycle rob self',
    'ACCEPT': 'cycle seq rob pdest vl illegal vecwen v0wen vpu perf vs1 vs2',
    'MOVE': 'cycle seq rob pdest illegal vecwen v0wen exception vpu perf',
    'RESPONSE': 'cycle seq rob pdest illegal data vecwen v0wen exception vpu perf',
    'STALL': 'cycle seq rob pdest illegal data vecwen v0wen exception vpu perf',
    'KILL': 'cycle seq slot rob pdest redirect self',
    'DIV_ACCEPT': 'cycle seq rob fu pdest',
    'DIV_KILL': 'cycle seq rob fu pdest redirect self',
    'DIV_OUTPUT': 'cycle seq rob fu pdest ready cancelled',
    'ENQUEUE': 'cycle rob pc ftq word',
    'COMMIT': 'cycle rob pc ftq',
    'REDIRECT': 'cycle rob ftq self',
    'RESET': 'cycle pvalid pseq rvalid rseq divactive divseq',
}
FIELDS = {k: v.split() for k, v in FIELDS.items()}
POINTERS = {'rob', 'redirect', 'ftq', 'prob', 'rrob'}
HEXES = {'fu', 'data', 'exception', 'pc', 'word', 'vpu', 'perf', 'vs1', 'vs2', 'addr'}
BITS = {'pvalid', 'rvalid', 'invalid', 'inready', 'vready', 'outvalid', 'outready',
        'move', 'killp', 'killr', 'divactive', 'divoccupied', 'busy',
        'illegal', 'vecwen', 'v0wen', 'self', 'ready', 'cancelled', 'wen', 'empty', 'wait', 'block'}
T13_FIELDS = {
    'COUNTER_ENQUEUE': 'cycle rob pc word empty wait block',
    'CSR_SAMPLE': 'cycle addr data wen',
    'RETIRE': 'cycle slot rob pc word count data',
}
UART_TAGS = {
    'T12_BEGIN', 'T12_GROUP_PASS', 'T12_SUMMARY', 'T12_MISMATCH', 'T12_CSR_FAIL', 'T12_SPEC_FAIL',
    'T13_BEGIN', 'T13_P', 'T13_CASE', 'T13_SUMMARY', 'T13_CONTROLS', 'T13_SCRATCH_CONTROL', 'T13_FAIL',
}
O2_UART_TAGS = {
    'DIAG_BEGIN', 'DIAG_CHECKER_CONTROL', 'DIAG_CASE_PASS', 'DIAG_SUMMARY', 'DIAG_FAIL',
    'CONTROL_BEGIN', 'CONTROL_GROUP_PASS', 'CONTROL_SUMMARY', 'CONTROL_FAIL',
}
REQUIRED_O2_COVERAGE = ('multi_inflight', 'triple_overlap', 'full_stall', 'kill_p', 'kill_r', 'partial_kill')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_fields(kind, body, fields, schema=None, t13=False):
    patterns = []
    for key in fields:
        pat = (r'[01]\s*:\s*[0-9]+' if key in POINTERS else
               r'global' if key == 'clock' else
               r'[PR]' if key == 'slot' and not t13 else
               r'0x[0-9a-fA-F]+' if key in HEXES else r'[0-9]+')
        patterns.append(key + r'=\s*(' + pat + ')')
    match = re.fullmatch(r'\s+'.join(patterns) + r'\s*', body)
    require(match is not None, 'malformed observer event: ' + kind)
    out = {}
    for key, raw in zip(fields, match.groups()):
        value = re.sub(r'\s', '', raw)
        if key in POINTERS:
            _, index = map(int, value.split(':'))
            # Empty P/R registers are not reset data: Verilator may expose
            # any six-bit raw index there, including 48..63. Their valid bit,
            # checked after the entire row is parsed, determines whether the
            # stricter 48-entry ROB domain applies.
            raw_slot = kind == 'STATE' and key in ('prob', 'rrob')
            limit = 64 if raw_slot else 8 if key == 'ftq' else 48
            require(index < limit, 'pointer outside pinned configuration')
        elif key not in ('clock',) and not (key == 'slot' and not t13):
            value = int(value, 16 if key in HEXES else 10)
            width = (schema[key + '_width'] if key in ('vpu', 'perf') and schema else
                     128 if key in ('vs1', 'vs2') or key == 'data' and not t13 else
                     32 if key == 'word' else 64)
            require(value < 1 << width, 'observer field overflow: ' + key)
            if key in BITS:
                require(value in (0, 1), 'invalid bit field: ' + key)
            if key == 'occupancy':
                require(value <= 2, 'invalid occupancy')
        out[key] = value
    if kind == 'STATE':
        for prefix in ('p', 'r'):
            if out[prefix + 'valid']:
                index = int(out[prefix + 'rob'].split(':')[1])
                require(index < 48, 'active slot pointer outside pinned ROB configuration')
    return out


def extract_events_and_uart(text):
    """Records can interrupt UART bytes; same-cycle printf ordering is irrelevant."""
    events, schemas = [], []
    def take(match):
        kind, body = match.groups()
        require(kind in FIELDS, 'unknown O2 observer event: ' + kind)
        f = parse_fields(kind, body, FIELDS[kind], schemas[0] if schemas else None)
        if kind == 'SCHEMA':
            require(not schemas and not events, 'duplicate or late O2 schema')
            fixed = dict(version=1, clock='global', latency=2, slots=2, rob_size=48, ftq_size=8, vlen=128,
                         vpu_width=195, perf_width=577)
            require(all(f[k] == v for k, v in fixed.items()), 'unsupported O2 schema')
            require(all(0 < f[k] <= 4096 for k in ('vpu_width', 'perf_width')), 'invalid bundle width')
            schemas.append(f)
        else:
            require(schemas, 'missing initial O2 schema')
            require(kind != 'RESET', 'runtime reset/multiple epochs unsupported by G3 audit')
            events.append((f['cycle'], len(events), kind, f))
        return ''
    # Match known observer starts first. A UART token can itself begin O2_ and
    # be interrupted mid-token by an observer printf; matching arbitrary O2_
    # greedily would consume both prefixes and misclassify valid UART bytes.
    observer_names = '|'.join(sorted(FIELDS, key=len, reverse=True))
    uart = re.sub(r'O2_(' + observer_names + r')[ \t]+([^\n]*)\n', take, text)
    remaining = re.findall(r'O2_([A-Z0-9_]*)', uart)
    require(len(schemas) == 1 and all(tag in O2_UART_TAGS for tag in remaining),
            'missing, unknown, malformed or truncated O2 record')
    require('O1_' not in uart, 'legacy O1 trace cannot substitute for O2')
    def take_t13(match):
        kind, body = match.groups()
        parse_fields('T13_' + kind, body, T13_FIELDS[kind].split(), t13=True)
        return ''
    uart = re.sub(r'T13_(COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+([^\n]*)\n', take_t13, uart)
    require(all(tag in UART_TAGS for tag in re.findall(r'T(?:12|13)_[A-Z0-9_]*', uart)),
            'unknown, legacy, malformed or truncated observer record')
    require(all(a[0] <= b[0] for a, b in zip(events, events[1:])), 'global observer cycles are out of order')
    return [(-1, -1, 'SCHEMA', schemas[0])] + events, uart


def flushed(rob, origin, self_flush):
    flag, index = map(int, rob.split(':'))
    origin_flag, origin_index = map(int, origin.split(':'))
    return (bool(flag ^ origin_flag) ^ (index > origin_index)) or (rob == origin and self_flush == 1)


def histogram(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


def dot_result(left, right):
    def signed_byte(x):
        return x - 256 if x & 128 else x
    return sum(signed_byte((left >> (i * 8)) & 255) *
               signed_byte((right >> (i * 8)) & 255) for i in range(8)) & 0xffffffff


def o2_coverage(counts):
    return {
        'multi_inflight': counts.get('MULTI_INFLIGHT', 0) > 0,
        'triple_overlap': counts.get('TRIPLE_OVERLAP', 0) > 0,
        'full_stall': counts.get('FULL_STALL', 0) > 0,
        'kill_p': counts.get('KILL_P', 0) > 0,
        'kill_r': counts.get('KILL_R', 0) > 0,
        'partial_kill': counts.get('PARTIAL_KILL', 0) > 0,
    }


def analyze(text, *, require_complete=True):
    all_events, _ = extract_events_and_uart(text)
    schema, events = all_events[0][3], all_events[1:]
    groups = defaultdict(list)
    seen = set()
    for cycle, _, kind, f in events:
        signature = (kind, tuple(f.items()))
        require(signature not in seen, 'duplicate observer record')
        seen.add(signature)
        groups[cycle].append((kind, f))
    counts = Counter({k: 0 for k in FIELDS if k not in ('SCHEMA', 'RESET')})
    counts.update({k: 0 for k in (
        'MULTI_INFLIGHT', 'OVERLAP', 'TRIPLE_OVERLAP', 'FULL_STALL', 'KILL_P', 'KILL_R',
        'PARTIAL_KILL', 'BOTH_KILL', 'R_KILL_P_SURVIVES', 'P_KILL_R_SURVIVES',
        'UNRELATED_FLUSH', 'ROB_WRAP', 'FTQ_WRAP', 'DIV_RESPONSE',
        'ACCEPTED_THEN_SQUASHED', 'ACCEPTED_YOUNGER_SQUASHED')})
    kinds = Counter()
    live, history, transactions = {}, [], []
    p_slot = r_slot = active_div = last_div = None
    parent_seq, previous_cycle = 0, None
    previous_activity = False
    redirects, parent_redirects = {}, {}
    last_rob = last_ftq = None

    def identity(f, t, message):
        require(t is not None and all(f[k] == t[k] for k in ('seq', 'rob', 'pdest')), message)

    def packet(f, t, *, data=False):
        identity(f, t, 'slot packet sequence/ROB/pdest mismatch')
        require(f['illegal'] == t['illegal'], 'packet illegal identity changed')
        require(f['exception'] == (4 if t['illegal'] else 0), 'packet exception mismatch')
        expected_wen = (0, 0) if t['illegal'] else (t['vecwen'], t['v0wen'])
        require((f['vecwen'], f['v0wen']) == expected_wen, 'packet destination write enables changed')
        require((f['vpu'], f['perf']) == (t['vpu'], t['perf']), 'packet vpu/perf identity changed')
        if data:
            require(f['data'] == t['expected_data'], 'complete 128-bit result differs from accepted-source oracle')
            snapshot = tuple(f[k] for k in FIELDS['RESPONSE'] if k != 'cycle')
            require(t.get('snapshot', snapshot) == snapshot, 'stalled packet changed')
            t['snapshot'] = snapshot

    last_cycle = max(groups, default=-1)
    for cycle, items in sorted(groups.items()):
        by = defaultdict(list)
        for kind, f in items:
            by[kind].append(f)
            counts[kind] += 1
        for name in FIELDS.keys() - {'SCHEMA', 'RESET', 'KILL', 'ENQUEUE', 'COMMIT'}:
            require(len(by[name]) <= 1, 'multiple ' + name + ' events in one cycle')
        require(len(by['KILL']) <= 2, 'more than two kills')
        one = lambda k: by[k][0] if by[k] else None
        st, pa, wait, pf = [one(k) for k in ('STATE', 'VFEX4_ACCEPT', 'VFEX4_WAIT', 'VFEX4_REDIRECT')]
        accept, move, response, stall = [one(k) for k in ('ACCEPT', 'MOVE', 'RESPONSE', 'STALL')]
        da, dk, do = [one(k) for k in ('DIV_ACCEPT', 'DIV_KILL', 'DIV_OUTPUT')]
        redirect = one('REDIRECT')
        old_p, old_r, old_div = p_slot, r_slot, active_div
        active = old_p is not None or old_r is not None or old_div is not None
        if (active or previous_activity) and previous_cycle is not None:
            require(cycle == previous_cycle + 1, 'missing active-cycle observation')
        previous_cycle = cycle
        require(not (pa and wait), 'parent simultaneously accepted and waited')
        if pa:
            require(pa['seq'] == parent_seq, 'parent sequence not contiguous from zero')
            parent_seq += 1
            require(pa['fu'] in FU_TYPES, 'unexpected VFEX4 functional unit')
            kinds[hex(pa['fu'])] += 1
        if wait:
            require(wait['fu'] in FU_TYPES, 'unexpected waiting functional unit')
        if pf:
            parent_redirects[cycle] = pf
            prior = redirects.get(cycle - 1)
            require(prior is not None and (pf['rob'], pf['self']) == (prior['rob'], prior['self']),
                    'parent redirect differs from prior-cycle ROB redirect')
            require(pa is None and accept is None and da is None, 'accept during real parent flush')
        if redirect:
            redirects[cycle] = redirect
        # ROB retirement binds the old allocation before same-cycle redirects/reuse.
        def commit_age(left, right):
            if left['rob'] == right['rob']:
                return 0
            left_after = flushed(left['rob'], right['rob'], 0)
            right_after = flushed(right['rob'], left['rob'], 0)
            require(left_after != right_after, 'ambiguous half-ring commit ordering')
            return 1 if left_after else -1
        for f in sorted(by['COMMIT'], key=cmp_to_key(commit_age)):
            e = live.get(f['rob'])
            require(e is not None and not e['done'] and not e['cancelled'], 'unbound/cancelled/duplicate commit')
            require(e.get('response_cycle') is not None and e['response_cycle'] < cycle,
                    'commit without preceding FU response')
            require((e['pc'], e['ftq']) == (f['pc'], f['ftq']), 'commit PC/FTQ identity mismatch')
            require(e['illegal'] == 0, 'illegal vdot retired normally')
            e.update(done=True, commit_cycle=cycle)
            rb, fq = int(f['rob'][0]), int(f['ftq'][0])
            counts['ROB_WRAP'] += int(last_rob is not None and rb != last_rob)
            counts['FTQ_WRAP'] += int(last_ftq is not None and fq != last_ftq)
            last_rob, last_ftq = rb, fq
        if redirect:
            for e in live.values():
                if not e['done'] and not e['cancelled'] and flushed(e['rob'], redirect['rob'], redirect['self']):
                    e.update(cancelled=True, cancel_cycle=cycle, cancel_is_younger=e['rob'] != redirect['rob'])
        for f in by['ENQUEUE']:
            require(redirect is None, 'enqueue contradicts ROB redirect gate')
            old = live.get(f['rob'])
            require(old is None or old['done'] or old['cancelled'], 'reallocated live ROB identity')
            require(not any(t is not None and t['entry'] is old for t in (old_p, old_r)),
                    'reallocated pending slot identity')
            require(f['word'] & 0xfe00707f == 0x0200000b, 'enqueued non-vdot instruction')
            e = dict(f, done=False, cancelled=False, accepted=False)
            live[f['rob']] = e
            history.append(e)

        fu_events = any(by[k] for k in ('VFEX4_ACCEPT', 'VFEX4_WAIT', 'VFEX4_REDIRECT',
                    'ACCEPT', 'MOVE', 'RESPONSE', 'STALL', 'KILL', 'DIV_ACCEPT', 'DIV_KILL', 'DIV_OUTPUT'))
        require(st is not None or not (active or fu_events or previous_activity), 'missing STATE for functional activity')
        if st is None:
            continue
        previous_activity = bool(st['pvalid'] or st['rvalid'] or st['divoccupied'] or st['invalid'] or pf)
        for prefix, t in (('p', old_p), ('r', old_r)):
            require(st[prefix + 'valid'] == int(t is not None), 'slot validity differs from prior transition')
            if t is not None:
                require((st[prefix + 'seq'], st[prefix + 'rob'], st[prefix + 'pdest']) ==
                        (t['seq'], t['rob'], t['pdest']), 'slot identity differs from prior transition')
        occupancy = int(old_p is not None) + int(old_r is not None)
        require(st['occupancy'] == occupancy, 'occupancy differs from slots')
        counts['MULTI_INFLIGHT'] += int(occupancy == 2)
        require(st['divactive'] == int(old_div is not None), 'DIV active state differs from transition')
        if old_div:
            require(st['divseq'] == old_div['seq'] and st['divoccupied'], 'DIV state identity/occupancy mismatch')
        require(not (occupancy and st['divoccupied']), 'vdot and DIV overlap')
        require(st['busy'] == int(bool(occupancy or st['divoccupied'])), 'parent busy differs from actual occupancy')
        if wait:
            require(wait['busy'] == st['busy'], 'WAIT busy disagrees with state')
        require(st['invalid'] == int(pa is not None or wait is not None), 'parent input valid/event mismatch')
        require(bool(pa) == bool(st['invalid'] and st['inready']), 'parent handshake/event mismatch')
        require(bool(wait) == bool(st['invalid'] and not st['inready']), 'parent wait/event mismatch')
        kp = bool(old_p and pf and flushed(old_p['rob'], pf['rob'], pf['self']))
        kr = bool(old_r and pf and flushed(old_r['rob'], pf['rob'], pf['self']))
        require((st['killp'], st['killr']) == (int(kp), int(kr)), 'slot kill differs from independent ROB age')
        live_p, live_r = old_p is not None and not kp, old_r is not None and not kr
        expected_move = live_p and (not live_r or st['outready'])
        expected_out = live_r
        expected_vready = (not live_p or not live_r or st['outready']) and not pf
        require(st['move'] == int(expected_move), 'P to R movement equation violated')
        require(st['outvalid'] == int(expected_out), 'R output valid equation violated')
        require(st['vready'] == int(bool(expected_vready)), 'vdot ready equation violated')
        selected_input = pa or wait
        if selected_input:
            expected_parent_ready = (not st['divoccupied'] and not pf and
                (st['vready'] if selected_input['fu'] == VDOT else occupancy == 0))
            require(st['inready'] == int(bool(expected_parent_ready)), 'parent selected-ready equation violated')
        require(bool(move) == bool(expected_move), 'missing or unexpected MOVE')
        require(bool(response) == bool(expected_out and st['outready']), 'missing or unexpected RESPONSE')
        require(bool(stall) == bool(expected_out and not st['outready']), 'missing or unexpected STALL')
        counts['FULL_STALL'] += int(occupancy == 2 and stall is not None)
        expected_kills = {slot: t for slot, t, killed in (('P', old_p, kp), ('R', old_r, kr)) if killed}
        require(len(by['KILL']) == len(expected_kills), 'missing or unexpected slot KILL')
        observed_kill_slots = set()
        for k in by['KILL']:
            require(k['slot'] not in observed_kill_slots and k['slot'] in expected_kills, 'duplicate or wrong killed slot')
            observed_kill_slots.add(k['slot'])
            t = expected_kills[k['slot']]
            identity(k, t, 'killed slot identity mismatch')
            require((k['redirect'], k['self']) == (pf['rob'], pf['self']), 'kill redirect identity mismatch')
            require(t['entry']['cancelled'], 'FU kill lacks preceding ROB cancellation')
            t.update(outcome='kill', end_cycle=cycle, elapsed_cycles=cycle - t['accept_cycle'], kill_slot=k['slot'])
            counts['KILL_' + k['slot']] += 1
        counts['BOTH_KILL'] += int(kp and kr)
        counts['PARTIAL_KILL'] += int(occupancy == 2 and kp != kr)
        counts['R_KILL_P_SURVIVES'] += int(occupancy == 2 and kr and not kp)
        counts['P_KILL_R_SURVIVES'] += int(occupancy == 2 and kp and not kr)
        counts['UNRELATED_FLUSH'] += int(bool(pf and occupancy and not kp and not kr))
        if move:
            packet(move, old_p)
            require(cycle > old_p['accept_cycle'], 'new input moved combinationally into R')
            old_p['move_cycle'] = cycle
        if response or stall:
            f, t = response or stall, old_r
            packet(f, t, data=True)
            require(cycle > t['move_cycle'] and cycle - t['accept_cycle'] >= 2, 'response precedes registered two-stage latency')
            if stall:
                t['stalls'].append(cycle)
            else:
                t['entry']['response_cycle'] = cycle
                t.update(outcome='response', end_cycle=cycle, elapsed_cycles=cycle - t['accept_cycle'])
        require(not (da and accept), 'multiple child acceptance')
        if pa:
            child = accept if pa['fu'] == VDOT else da
            require(child is not None and all(pa[k] == child[k] for k in ('seq', 'rob', 'pdest')),
                    'parent/child acceptance identity mismatch')
            if pa['fu'] == VDOT:
                require(not st['divoccupied'] and st['vready'], 'vdot accepted while blocked')
            else:
                require(occupancy == 0 and not st['divoccupied'], 'DIV accepted before vdot/DIV drained')
                require(da['fu'] == pa['fu'], 'DIV functional type differs from parent')
        require(accept is None or pa is not None and pa['fu'] == VDOT, 'orphan child vdot accept')
        require(da is None or pa is not None and pa['fu'] != VDOT, 'orphan child DIV accept')
        # Logical DIV lifecycle; cancelled physical output may persist afterwards.
        expected_dk = bool(old_div and pf and flushed(old_div['rob'], pf['rob'], pf['self']))
        require(bool(dk) == expected_dk, 'missing or unexpected DIV kill')
        if dk:
            identity(dk, old_div, 'DIV kill identity mismatch')
            require(dk['fu'] == old_div['fu'] and (dk['redirect'], dk['self']) == (pf['rob'], pf['self']), 'DIV kill binding mismatch')
            old_div.update(cancelled=True, end_cycle=cycle)
            active_div = None
        if do:
            require(st['divoccupied'] == 1, 'physical DIV output missing functional occupancy')
            require(do['ready'] == st['outready'], 'DIV output ready differs from shared parent ready')
            identity(do, last_div, 'DIV output identity mismatch')
            require(do['fu'] == last_div['fu'], 'DIV output functional type changed')
            require(do['cancelled'] == int(last_div.get('cancelled', False)), 'DIV cancelled-output classification mismatch')
            if not do['cancelled']:
                require(active_div is not None, 'duplicate DIV response')
                if do['ready']:
                    counts['DIV_RESPONSE'] += 1
                    active_div = None
        if da:
            require(old_div is None and not st['divoccupied'], 'DIV accepted over existing DIV')
            active_div = last_div = dict(da, cancelled=False)
        new_request = None
        if accept:
            require(accept['vecwen'] + accept['v0wen'] == 1, 'input destination class is not one-hot')
            require(accept['vl'] < 256 and (accept['vl'] == 8 or accept['illegal']), 'invalid renamed VL legality')
            e = live.get(accept['rob'])
            require(e is not None and not e['done'] and not e['accepted'], 'unbound or duplicate FU accept')
            require(not e['cancelled'] or e.get('cancel_cycle') == cycle, 'accept after prior ROB cancellation')
            vd = (e['word'] >> 7) & 31
            require((accept['vecwen'], accept['v0wen']) == (int(vd != 0), int(vd == 0)), 'input write enables disagree with decoded destination')
            e.update(accepted=True, seq=accept['seq'], illegal=accept['illegal'], pdest=accept['pdest'])
            expected = 0 if accept['illegal'] else dot_result(accept['vs1'], accept['vs2'])
            new_request = dict(accept, accept_cycle=cycle, entry=e, stalls=[], expected_data=expected)
            transactions.append(new_request)
        counts['OVERLAP'] += int(response is not None and accept is not None)
        counts['TRIPLE_OVERLAP'] += int(response is not None and move is not None and accept is not None)
        r_slot = old_p if move else old_r if live_r and response is None else None
        p_slot = new_request if accept else old_p if live_p and move is None else None
        require(p_slot is None or r_slot is None or p_slot['seq'] != r_slot['seq'], 'same transaction occupies both slots')
        pending = int(p_slot is not None) + int(r_slot is not None)
        require(counts['ACCEPT'] == counts['RESPONSE'] + counts['KILL'] + pending, 'prefix request conservation violated')
        require(counts['DIV_ACCEPT'] == counts['DIV_RESPONSE'] + counts['DIV_KILL'] + int(active_div is not None),
                'prefix DIV conservation violated')
    for cycle, f in redirects.items():
        if not require_complete and cycle == last_cycle:
            continue
        pf = parent_redirects.get(cycle + 1)
        require(pf is not None and (f['rob'], f['self']) == (pf['rob'], pf['self']), 'missing next-cycle parent redirect')
    unfinished = [e for e in history if not e['done'] and not e['cancelled']]
    pending = int(p_slot is not None) + int(r_slot is not None)
    if require_complete:
        require(counts['STATE'] > 0, 'missing initial state observation')
        require(not previous_activity, 'missing final inactive state observation')
        require(pending == 0, 'unfinished FU requests')
        require(active_div is None, 'unfinished DIV request')
        require(not unfinished, 'unfinished ROB allocations')
    counts['ACCEPTED_THEN_SQUASHED'] = sum(e['accepted'] and e['cancelled'] for e in history)
    counts['ACCEPTED_YOUNGER_SQUASHED'] = sum(e['accepted'] and e['cancelled'] and e.get('cancel_is_younger', False) for e in history)
    require(counts['ACCEPT'] == counts['RESPONSE'] + counts['KILL'] + pending, 'final request conservation violated')
    public = [{k: v for k, v in t.items() if k not in ('entry', 'snapshot', 'stalls', 'cycle')} |
              {'writeback_stall_events': len(t['stalls'])} for t in transactions]
    return dict(status='O2_TRACE_PASS' if require_complete else 'O2_PARTIAL_TRACE_AUDIT',
                input_sha256=hashlib.sha256(text.encode()).hexdigest(), schema=schema,
                counts=dict(counts), vfex4_fu_counts=dict(kinds), pending_count=pending,
                pending_div_count=int(active_div is not None), unfinished_rob_count=len(unfinished),
                transactions=public, o2_coverage=o2_coverage(counts),
                response_latency_histogram=histogram(t['elapsed_cycles'] for t in public if t.get('outcome') == 'response'),
                observed_accept_gap_histogram=histogram(b['accept_cycle'] - a['accept_cycle'] for a, b in zip(public, public[1:])),
                clock_mapping='direct ungated VFEX4/ROB global cycle; independent P/R transition audit',
                scope='trace and accepted-source full128 arithmetic audit; ISA legality/architectural state require workload and DiffTest',
                runtime_reset_audited=False, performance_measured=False)


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
        print('O2_TRACE_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
