"""Source-bound T14 batch128 pilot diagnosis, not an O1 speedup prediction."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
# Retain the integrated gate and its reviewed parser; never restore old tools.
GATE_BLOB = '788166f389116d3bea876ed62086e6ddb045314e'
PIN_BLOB = 'f11914ad9b4811a48e651c49e058f4d411e0fd3e'
BASE = '91b94073a06c7e81c1abb1f8e2e4a926e183f780'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def load_gate():
    path = HERE / 'replay_archive.py'
    require(blob(path.read_bytes()) == GATE_BLOB, 'archive gate source changed')
    spec = importlib.util.spec_from_file_location('o0_pilot_gate', path)
    require(spec is not None and spec.loader is not None, 'cannot load gate')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hist(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


def bind_retirements(events, transactions):
    """Bind each dynamic ROB allocation, including reuse after redirects.

    Redirect-cycle ENQUEUE prints are suppressed attempts, not allocations,
    matching the reviewed T12 checker. This helper remains limited to the
    no-accepted-cancellation pilot; it is not a general control-regression gate.
    """
    rank = {'COMMIT': 0, 'REDIRECT': 1, 'ENQUEUE': 2, 'ACCEPT': 3,
            'STALL': 4, 'RESPONSE': 5, 'KILL': 6, 'VFEX4_ACCEPT': 7, 'VFEX4_WAIT': 8}
    live, history, by_accept = {}, [], {}
    redirect_cycles = {e[0] for e in events if e[2] == 'REDIRECT'}
    for t in transactions:
        key = (t['accept_cycle'], t['rob'])
        require(key not in by_accept, 'duplicate transaction identity')
        by_accept[key] = t
    for cycle, order, kind, fields in sorted(events, key=lambda e: (e[0], rank[e[2]], e[1])):
        rob = fields['rob']
        if kind == 'ENQUEUE':
            require(int(fields['word'], 16) & 0xfe00707f == 0x0200000b, 'non-vdot allocation')
            if cycle in redirect_cycles:
                continue
            old = live.get(rob)
            require(old is None or old.get('commit_cycle') is not None or old['cancelled'], 'live ROB overwritten')
            word = int(fields['word'], 16)
            require(word & 0xfe00707f == 0x0200000b, 'non-vdot allocation')
            entry = dict(rob=rob, pc=fields['pc'], word=fields['word'], vd=(word >> 7) & 31,
                         enqueue_cycle=cycle, cancelled=False)
            live[rob] = entry
            history.append(entry)
        elif kind == 'REDIRECT':
            flag, index = map(int, rob.split(':'))
            origin = flag * 48 + index
            for key, entry in live.items():
                f, i = map(int, key.split(':'))
                if entry.get('commit_cycle') is None and not entry['cancelled'] and 0 < (f*48+i-origin) % 96 < 48:
                    entry['cancelled'] = True
        elif kind == 'ACCEPT':
            e = live.get(rob)
            require(e is not None and not e['cancelled'] and 'accept_cycle' not in e, 'unbound/duplicate accept')
            t = by_accept.get((cycle, rob))
            require(t is not None and int(fields['pdest']) == t['pdest'], 'accept identity mismatch')
            e.update(accept_cycle=cycle, pdest=t['pdest'], index=t['index'])
        elif kind == 'RESPONSE':
            e = live.get(rob)
            require(e is not None and not e['cancelled'] and 'accept_cycle' in e and 'response_cycle' not in e, 'unbound response')
            t = by_accept[(e['accept_cycle'], rob)]
            require(t['outcome'] == 'response' and cycle == t['end_cycle'] and int(fields['pdest']) == e['pdest'], 'response identity mismatch')
            e.update(response_cycle=cycle, result128=fields['data'])
        elif kind == 'KILL':
            raise ValueError('FU kill outside the selected pilot contract')
        elif kind == 'COMMIT':
            e = live.get(rob)
            require(e is not None and not e['cancelled'] and 'response_cycle' in e and 'commit_cycle' not in e, 'unbound/cancelled/duplicate commit')
            require(e['pc'] == fields['pc'] and cycle >= e['response_cycle'], 'commit PC/time mismatch')
            e['commit_cycle'] = cycle
    accepted = sorted((e for e in history if 'accept_cycle' in e), key=lambda e: e['index'])
    require(len(accepted) == len(transactions), 'missing accepted lifetimes')
    require(all('commit_cycle' in e and not e['cancelled'] for e in accepted), 'uncommitted accepted instruction')
    require(all(e['cancelled'] or 'commit_cycle' in e for e in history), 'unfinished ROB entry')
    return accepted, sum(e['cancelled'] for e in history)


def correlate(stderr, analysis, diagnosis, checker):
    events, _ = checker.extract_events(stderr)
    events = checker.normalize_fu_cycles(events, min_response_latency=2)
    lifetimes, preaccept_cancelled = bind_retirements(events, diagnosis['transactions'])
    require(len(lifetimes) == analysis['fu']['committed'], 'commit total differs from archive')
    # Recheck all 48 raw samples, not just arithmetic on archived counter values.
    pattern = re.compile(r'^T13_CSR_SAMPLE cycle=\s*(\d+) addr=(0x[0-9a-fA-F]+) data=(0x[0-9a-fA-F]+) wen=(\d+)\s*$', re.M)
    sampled = [tuple(int(v, 0) if v.startswith('0x') else int(v) for v in m.groups()) for m in pattern.finditer(stderr)]
    expected = [(tick, addr, value, 0) for s in analysis['samples']
                for tick, addr, value in zip(s['sample_ticks'], (0xc02, 0xc00, 0xc00, 0xc02), s['counter_values'])]
    require(len(re.findall(r'\bT13_CSR_SAMPLE\b', stderr)) == len(sampled), 'malformed CSR observation')
    require(sampled == expected, 'raw CSR samples differ from archived windows')
    waits = {cycle: f for cycle, _, kind, f in events if kind == 'VFEX4_WAIT'}
    redirects = {cycle for cycle, _, kind, _ in events if kind == 'REDIRECT'}
    rows, matches = [], []
    within_gaps = []
    for s in analysis['samples']:
        lo, hi = s['sample_ticks'][1:3]
        tx = [e for e in lifetimes if lo <= e['accept_cycle'] < hi]
        require(len(tx) == (s['dots'] if s['method'] == 'vdot' else 0), 'pilot workload/accept count mismatch')
        require(all(lo <= e['enqueue_cycle'] <= e['accept_cycle'] < e['response_cycle'] <= e['commit_cycle'] < hi for e in tx), 'lifetime crosses window')
        local_waits = [(c, f) for c, f in waits.items() if lo <= c < hi]
        response_busy = [e for e in tx if e['response_cycle'] in waits and waits[e['response_cycle']]['busy'] == '1' and int(waits[e['response_cycle']]['fu'],16) == checker.VDOT_FU_TYPE]
        pair_matches = []
        gaps = []
        for previous, following in zip(tx, tx[1:]):
            c = previous['response_cycle']; w = waits.get(c)
            gaps.append(following['accept_cycle'] - previous['accept_cycle'])
            if w and w['busy'] == '1' and int(w['fu'],16) == checker.VDOT_FU_TYPE and w['rob'] == following['rob'] and following['accept_cycle'] == c+1:
                pair_matches.append(dict(seq=s['seq'], phase=s['phase'], response_cycle=c,
                    old_rob=previous['rob'], old_pdest=previous['pdest'], old_vd=previous['vd'],
                    waiting_rob=w['rob'], next_accept_cycle=following['accept_cycle'],
                    next_pdest=following['pdest'], next_vd=following['vd'], observed_redirect_same_cycle=c in redirects))
        matches.extend(pair_matches)
        within_gaps.extend(gaps)
        rows.append(dict(seq=s['seq'], phase=s['phase'], method=s['method'], cycles=s['cycles'],
            declared_dots=s['dots'], accepted=len(tx), committed=len(tx),
            busy_wait_events=sum(f['busy']=='1' for _,f in local_waits),
            nonbusy_wait_events=sum(f['busy']=='0' for _,f in local_waits),
            response_busy_coincidences=len(response_busy),
            same_waiter_accepted_next_cycle=len(pair_matches),
            within_window_accept_gaps=hist(gaps)))
    require(sum(x['accepted'] for x in rows) == len(lifetimes), 'accepts outside declared windows')
    require(sum(x['busy_wait_events']+x['nonbusy_wait_events'] for x in rows) == len(waits), 'waits outside declared windows')
    return dict(status='O0_BATCH128_DIAGNOSIS_PASS_NOT_FULL_MATRIX',
        development_base=BASE, raw_csr_samples_checked=len(sampled),
        accepted_responded_committed=len(lifetimes), preaccept_cancelled_allocations=preaccept_cancelled,
        total_busy_wait_events=sum(r['busy_wait_events'] for r in rows),
        total_nonbusy_wait_events=sum(r['nonbusy_wait_events'] for r in rows),
        response_busy_coincidences=sum(r['response_busy_coincidences'] for r in rows),
        same_waiter_accepted_next_cycle=len(matches),
        matched_with_redirect_same_cycle=sum(m['observed_redirect_same_cycle'] for m in matches),
        within_window_gap_histogram=hist(within_gaps), inter_window_gaps_excluded=len(lifetimes)-1-len(within_gaps),
        windows=rows, lifetimes=lifetimes, matched_waiters=matches,
        o0_full_matrix_complete=False, o1_rtl_implemented=False, new_hardware_run=False,
        interpretation='This pilot directly observes the parent busy guard delaying ready work at response. It supports an O1 handoff prototype, but does not measure its legality, achievable II or speedup.',
        limits=['One fixed T14 batch128 dataset/replay; not the newer unified benchmark or full O0 matrix.',
                'Same-waiter next-cycle admission is observation, not a counterfactual saved-cycle count.',
                'No writeback stalls in this run; no inference that other workloads cannot stall.',
                'Remaining gaps cannot be labelled cache/issue/wakeup bottlenecks from these signals alone.',
                'Not a rerun of the CPU, ELF golden verification, new DiffTest or physical timing analysis.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        require(not output.exists(), 'output already exists')
        require(not output.is_relative_to((ROOT/'team/evidence').resolve()), 'do not write historical evidence')
        gate = load_gate()
        pins_bytes=(HERE/'pilot-t14-batch128.json').read_bytes()
        require(blob(pins_bytes)==PIN_BLOB, 'pilot pins changed')
        pins=gate.strict_json(pins_bytes)
        replay=gate.replay(ROOT,pins,'trace')
        a,_=gate.pinned_file(ROOT,pins['files']['analysis'])
        analysis=gate.strict_json(a)
        raw,_=gate.pinned_file(ROOT,pins['files']['stderr'])
        text=gate.decode_gzip(raw,analysis['raw_sha256']['stderr.log'])
        checker=gate.load_diagnostics(ROOT).load_parser()
        result=correlate(text,analysis,replay['replayed_diagnostics'],checker)
        result['source_files']=replay['source_files']
        result['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'replay_archive.py',HERE/'analyze.py',ROOT/'team/scripts/check-vdot-regression.py')}
        output.mkdir(parents=True,exist_ok=False)
        (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        for name, rows in [('windows',result['windows']),('lifetimes',result['lifetimes']),('matched-waiters',result['matched_waiters'])]:
            require(rows, 'empty diagnostic table')
            with (output/(name+'.csv')).open('w',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader()
                for row in rows: writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,dict) else v for k,v in row.items()})
        print(json.dumps({k:v for k,v in result.items() if k not in ('windows','lifetimes','matched_waiters','source_files','source_sha256','limits','interpretation')}))
        return 0
    except (ValueError, OSError, EOFError, KeyError, TypeError) as exc:
        print('O0_BATCH128_DIAGNOSIS_REJECTED: '+str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
