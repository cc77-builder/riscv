#!/usr/bin/env python3
"""Audit additional parent requests from actual acceptance and terminal records.

The frozen strict control and 577-bit metadata checkers remain mandatory. This
gate adds an exact request inventory; it does not replace their arithmetic,
protocol, clock, metadata, or observation-negative checks.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

LABEL = re.compile(r'dot16-([a-z]+[0-9]+[a-z]*)-k([0-9]+)-o([0-9]+)-l([0-9]+)'
                   r'-z([01])-t([01])-m([01])-e([0-9]+)-u([0-9]+)-s([0-9]+)'
                   r'-v([01])-w([01])-x([01])')
REQUEST_KEYS = ('kind', 'op', 'vl', 'v0', 'ta', 'ma', 'sew', 'lmul',
                'start', 'vill', 'vm', 'illegal')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def fields(line):
    pairs = [x.split('=', 1) for x in line.split()[1:]]
    need(all(len(x) == 2 for x in pairs), 'malformed record')
    result = dict(pairs)
    need(len(result) == len(pairs), 'duplicate record key')
    return result


def expected_inventory(feature):
    # (kind, operation, VL, terminal reason); DIV op varies in the frozen oracle.
    # reason 0=response, 1=cancel, 2=reset, matching original metadata contract.
    result = {}
    if not feature:
        for i in range(16):
            result['off' + str(i)] = (0, 2 if i % 2 else 1, 8 if i % 2 else 16, 0)
        return result
    for i in range(64):
        result['stream' + str(i)] = (0, i % 2, 16 if i % 2 else 8, 0)
    for i in range(8):
        result['directed' + str(i)] = (0, i % 2, 16 if i % 2 else 8, 0)
    for i in range(4):
        for side in ('a', 'b'):
            op = i // 2 if side == 'a' else 1 - i // 2
            result[f'blocked{i}{side}'] = (0, op, 16 if op else 8, 0)
    for i in range(8):
        kind, reverse = 1 + i // 4, (i // 2) % 2
        for side in ('a', 'b'):
            is_dot = (side == 'a') != bool(reverse)
            result[f'switch{i}{side}'] = (0, 1, 16, 0) if is_dot else (kind, None, 4, 0)
    masks = (2, 1, 3, 0)
    for i in range(16):
        order, mask = i // 8, masks[(i // 2) % 4]
        for side in ('a', 'b'):
            op = order if side == 'a' else 1 - order
            killed = bool(mask & (1 if side == 'a' else 2))
            result[f'pair{i}{side}'] = (0, op, 16 if op else 8, int(killed))
    for i in range(4):
        result[f'single{i}a'] = (0, 1, 16, 1)
    for i in range(8):
        phase, flush = i // 2, i % 2
        if phase in (1, 2):
            result[f'reset{i}a'] = (0, 1, 16, 2)
        elif phase == 3:
            a = 1 - flush
            result[f'reset{i}a'] = (0, a, 16 if a else 8, 2)
            result[f'reset{i}b'] = (0, 1-a, 8 if a else 16, 2)
        result[f'reset{i}recovery'] = (0, 1, 16, 0)
    for i in range(18):
        which = i // 2
        op = 0 if which == 1 else 2 if which == 2 else 1
        vl = 8 if which == 0 else 0 if which == 3 else 16
        result['illegal' + str(i)] = (0, op, vl, 0)
    return result


def check(result_log, metadata_log, feature):
    need(feature in (0, 1), 'feature must be 0 or 1')
    expected = expected_inventory(feature)
    accepted, ends, stream_cycles, tags, resets = {}, {}, [], set(), {}
    final = None
    extra_finished = False
    def end(seq, reason, cycle):
        if seq in accepted:
            need(seq not in ends, 'additional request has duplicate terminal')
            ends[seq] = (reason, cycle)
    with Path(result_log).open() as stream:
        for line in stream:
            if line.startswith('O2_PARENT_PASS '):
                need(final is None, 'duplicate parent completion')
                final = fields(line)
            if not line.startswith('O2_PARENT_CYCLE '):
                continue
            need(final is None, 'cycle after completion')
            r = fields(line)
            n = lambda key: int(r[key])
            cycle = n('cycle')
            if r['case'] == 'clock-recovery' and accepted:
                extra_finished = True
            if n('reset'):
                for key in ('pseq', 'rseq', 'divseq'):
                    if n(key):
                        end(n(key), 2, cycle)
            else:
                for flag, key in (('kill_p', 'pseq'), ('kill_r', 'rseq'), ('kill_div', 'divseq')):
                    if n(flag):
                        end(n(key), 1, cycle)
                if n('response'):
                    end(n('response_seq'), 0, cycle)
            if not r['case'].startswith('dot16-'):
                continue
            need(not extra_finished, 'additional campaign resumed after final recovery')
            label = LABEL.fullmatch(r['case'])
            need(label is not None, 'malformed additional request label')
            tag = label.group(1)
            q = dict(zip(REQUEST_KEYS, map(int, label.groups()[1:])))
            need(q['kind'] == n('kind'), 'label disagrees with driven request kind')
            legal_op = (q['op'] == 0 and q['vl'] == 8) or (
                feature and q['op'] == 1 and q['vl'] == 16)
            illegal = q['kind'] == 0 and (q['vill'] or not q['vm'] or q['sew'] or
                       q['lmul'] or q['start'] or not legal_op)
            need(q['illegal'] == bool(illegal), 'request legality label disagrees with contract')
            reset_match = re.fullmatch(r'reset([0-7])edge', tag)
            if reset_match:
                idx = int(reset_match.group(1))
                phase = idx // 2
                need(idx not in resets, 'duplicate reset edge case')
                need(n('reset') == 1 and n('te') == 0 and n('redirect') == idx % 2 and
                     n('reset_drop') == (2 if phase == 3 else int(phase != 0)) and
                     not n('accept') and not n('response') and
                     not any(n(x) for x in ('kill_p', 'kill_r', 'kill_div')),
                     'TE0 reset/redirect priority coverage mismatch')
                resets[idx] = cycle
            if not n('accept'):
                continue
            need(tag in expected and tag not in tags, 'unexpected or duplicate additional acceptance: ' + tag)
            tags.add(tag)
            kind, op, vl, reason = expected[tag]
            need(q['kind'] == kind and (op is None or q['op'] == op) and q['vl'] == vl,
                 'operation or VL inventory mismatch: ' + tag)
            want_illegal = tag.startswith(('illegal', 'off'))
            need(bool(q['illegal']) == want_illegal, 'legality inventory mismatch: ' + tag)
            if tag.startswith('stream'):
                idx = int(tag.removeprefix('stream'))
                need((q['v0'], q['ta'], q['ma']) == ((idx >> 1) & 1, (idx >> 2) & 1, (idx >> 3) & 1),
                     'mixed operation/v0/tail/mask policy matrix mismatch')
                stream_cycles.append((idx, cycle, n('accept_seq')))
            if tag.startswith('off'):
                policy = int(tag.removeprefix('off')) // 2
                need((q['v0'], q['ta'], q['ma']) == (policy & 1, (policy >> 1) & 1, (policy >> 2) & 1),
                     'disabled policy matrix mismatch')
            if tag.startswith('illegal'):
                need(q['v0'] == int(tag.removeprefix('illegal')) % 2, 'illegal v0 matrix mismatch')
            seq = n('accept_seq')
            need(seq > 0 and seq not in accepted, 'duplicate additional sequence')
            accepted[seq] = dict(case=tag, request=q, accept_cycle=cycle, expected_terminal=reason)
    need(final is not None and extra_finished, 'missing original terminal/recovery after extension')
    need(tags == set(expected), 'missing additional request inventory: ' + ','.join(sorted(set(expected)-tags)))
    need(set(ends) == set(accepted), 'additional requests do not all terminate')
    metadata_ends = {}
    with Path(metadata_log).open() as stream:
        for line in stream:
            if line.startswith('E '):
                f = fields(line)
                seq = int(f['seq'])
                if seq in accepted:
                    need(seq not in metadata_ends, 'duplicate metadata terminal')
                    metadata_ends[seq] = (int(f['reason']), int(f['cycle']))
    need(metadata_ends == ends, 'control/metadata additional terminal records disagree')
    reasons = Counter()
    for seq, item in accepted.items():
        reason, cycle = ends[seq]
        need(reason == item['expected_terminal'], 'unexpected terminal for ' + item['case'])
        reasons[reason] += 1
        item.update(terminal_reason=reason, terminal_cycle=cycle,
                    latency=cycle-item['accept_cycle'])
    expected_counts = {0: 138, 1: 20, 2: 8} if feature else {0: 16}
    need(dict(reasons) == expected_counts, 'additional terminal counts mismatch')
    if feature:
        need(set(resets) == set(range(8)), 'incomplete TE0 reset states')
        need([x[0] for x in stream_cycles] == list(range(64)), 'mixed stream order mismatch')
        need(all(b[1]-a[1] == 1 for a, b in zip(stream_cycles, stream_cycles[1:])), 'mixed stream II != 1')
        need(all(accepted[s]['latency'] == 2 and ends[s][0] == 0 for _, _, s in stream_cycles),
             'mixed stream first/last response latency != 2')
    else:
        need(not resets and not stream_cycles, 'enabled coverage in disabled campaign')
    for key, value in (('groups', 14), ('perf_contract', 2), ('perf_bits', 577),
                       ('perf_walk_one', 577), ('perf_walk_zero', 577),
                       ('parent_tested', 1), ('fullcore_tested', 0), ('performance_measured', 0)):
        need(int(final[key]) == value, 'frozen terminal contract changed: ' + key)
    return dict(schema=1, status=f'DOT16_PARENT_FEATURE_{feature}_COVERAGE_PASS', feature=feature,
                additional_accepted=len(accepted), additional_responses=reasons[0],
                additional_cancelled=reasons[1], additional_reset_dropped=reasons[2],
                mixed_ii1_intervals=63 if feature else 0,
                mixed_latency=2 if feature else None, reset_state_cases=len(resets),
                cases={str(k): v for k, v in accepted.items()},
                original_summary=final,
                inputs={str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                        for p in (result_log, metadata_log)},
                decode_qualified=False, fullcore_qualified=False, performance_measured=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result-log', required=True, type=Path)
    parser.add_argument('--metadata-log', required=True, type=Path)
    parser.add_argument('--feature', type=int, choices=(0, 1), required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    need(not args.output.exists(), 'coverage output already exists')
    report = check(args.result_log, args.metadata_log, args.feature)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'])
