"""Streaming form of the pinned team O2 auditor; official/frozen code stays unchanged.

The cycle state machine below is derived from fullcore/analyze.py. The changed
storage policy retains one cycle, live ROB slots and unfinished transactions.
It checks every original protocol/arithmetic predicate and emits an ordered
canonical transaction digest. Synthetic compatibility mode collects results
only for testing; production audit_files never retains the full event stream.
"""
from __future__ import annotations
from collections import Counter,defaultdict,deque
from functools import cmp_to_key
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import re

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[8]
ORIGINAL=REPO/'team/optimizations/o2/fullcore/analyze.py'
ORIGINAL_SHA='27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496'
if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()!=ORIGINAL_SHA:
    raise ValueError('stream auditor requires its exact original team checker')
spec=importlib.util.spec_from_file_location('original_o2_auditor',ORIGINAL)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
FIELDS,VDOT,FU_TYPES=old.FIELDS,old.VDOT,old.FU_TYPES
require,parse_fields,flushed,dot_result,o2_coverage=old.require,old.parse_fields,old.flushed,old.dot_result,old.o2_coverage
NAMES='|'.join(sorted(FIELDS,key=len,reverse=True))
O2_PATTERN=re.compile(r'O2_('+NAMES+r')[ \t]+([^\n]*)\n')
T13_PATTERN=re.compile(r'T13_(COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+([^\n]*)\n')
MAX_LINE=65536
MAX_RESIDUAL=16*1024*1024

class Reader:
    """Preserve stderr+stdout order, universal-newline identity and UART splices."""
    def __init__(self,sources):
        self.sources=sources;self.sha=hashlib.sha256();self.schema=None
        self.residual=io.StringIO();self.residual_bytes=0;self.counter_rows=[]
        self.uart=None;self.event_count=0;self.max_cycle_records=0

    def lines(self):
        pending=''
        for source in self.sources:
            while True:
                part=source.readline(MAX_LINE+1)
                if not part:break
                self.sha.update(part.encode())
                pending+=part
                require(len(pending)<=MAX_LINE,'observer physical line exceeds explicit 64 KiB profile')
                if pending.endswith('\n'):
                    yield pending;pending=''
        if pending:yield pending

    def events(self):
        for line in self.lines():
            emitted=[]
            def take(match):
                kind,body=match.groups();fields=parse_fields(kind,body,FIELDS[kind],self.schema)
                if kind=='SCHEMA':
                    require(self.schema is None and self.event_count==0,'duplicate or late O2 schema')
                    fixed=dict(version=1,clock='global',latency=2,slots=2,rob_size=48,ftq_size=8,vlen=128,vpu_width=195,perf_width=577)
                    require(all(fields[k]==v for k,v in fixed.items()),'unsupported O2 schema')
                    require(all(0<fields[k]<=4096 for k in ('vpu_width','perf_width')),'invalid bundle width')
                    self.schema=fields;emitted.append((-1,-1,kind,fields))
                else:
                    require(self.schema is not None,'missing initial O2 schema')
                    require(kind!='RESET','runtime reset/multiple epochs unsupported by G3 audit')
                    emitted.append((fields['cycle'],self.event_count,kind,fields));self.event_count+=1
                return ''
            # Raw T13 matches stay distinct from the later O2-stripped UART view,
            # exactly as in the original target counter auditor.
            self.counter_rows.extend(m.group(0) for m in T13_PATTERN.finditer(line))
            require(len(self.counter_rows)<=4096,'counter record count exceeds explicit consumer profile')
            residue=O2_PATTERN.sub(take,line);self.residual_bytes+=len(residue.encode())
            require(self.residual_bytes<=MAX_RESIDUAL,'non-O2 residue exceeds explicit 16 MiB profile')
            self.residual.write(residue)
            yield from emitted
        require(self.schema is not None,'missing initial O2 schema')
        header='O2_SCHEMA '+' '.join(k+'='+str(self.schema[k]) for k in FIELDS['SCHEMA'])+'\n'
        remaining_events,self.uart=old.extract_events_and_uart(header+self.residual.getvalue())
        require(len(remaining_events)==1,'observer survived exact streaming extraction')

    def groups(self,events):
        current=None;items=[];seen=set()
        for cycle,_,kind,fields in events:
            require(kind!='SCHEMA' and (current is None or cycle>=current),'global observer cycles are out of order')
            if current is not None and cycle!=current:
                self.max_cycle_records=max(self.max_cycle_records,len(items));yield current,items;items=[];seen=set()
            current=cycle;signature=(kind,tuple(fields.items()))
            require(signature not in seen,'duplicate observer record');seen.add(signature);items.append((kind,fields))
            require(len(items)<=4096,'cycle record count exceeds explicit 4096-record profile')
        if current is not None:
            self.max_cycle_records=max(self.max_cycle_records,len(items));yield current,items

def analyze_reader(reader, *, require_complete=True, transaction_sink=None, commit_sink=None):
    events=reader.events();first=next(events,None)
    require(first is not None and first[2]=='SCHEMA','missing initial O2 schema')
    schema=first[3]
    counts = Counter({k: 0 for k in FIELDS if k not in ('SCHEMA', 'RESET')})
    counts.update({k: 0 for k in (
        'MULTI_INFLIGHT', 'OVERLAP', 'TRIPLE_OVERLAP', 'FULL_STALL', 'KILL_P', 'KILL_R',
        'PARTIAL_KILL', 'BOTH_KILL', 'R_KILL_P_SURVIVES', 'P_KILL_R_SURVIVES',
        'UNRELATED_FLUSH', 'ROB_WRAP', 'FTQ_WRAP', 'DIV_RESPONSE',
        'ACCEPTED_THEN_SQUASHED', 'ACCEPTED_YOUNGER_SQUASHED')})
    kinds = Counter()
    live, transactions = {}, deque()
    response_hist, gap_hist = Counter(), Counter()
    last_accept_cycle = None
    transaction_hash=hashlib.sha256();transaction_count=0
    max_live=max_transactions=0

    def fold_entry(entry):
        counts['ACCEPTED_THEN_SQUASHED'] += int(entry['accepted'] and entry['cancelled'])
        counts['ACCEPTED_YOUNGER_SQUASHED'] += int(entry['accepted'] and entry['cancelled'] and entry.get('cancel_is_younger',False))

    def emit_transaction(transaction):
        nonlocal transaction_count
        public={k:v for k,v in transaction.items() if k not in ('entry','snapshot','stalls','cycle')}
        public['writeback_stall_events']=transaction['stalls']
        transaction_hash.update((json.dumps(public,sort_keys=True,separators=(',',':'))+'\n').encode())
        transaction_count+=1
        if transaction.get('outcome')=='response':response_hist[transaction['elapsed_cycles']]+=1
        if transaction_sink is not None:transaction_sink(public)
    p_slot = r_slot = active_div = last_div = None
    parent_seq, previous_cycle = 0, None
    previous_activity = False
    redirect_pending = None
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

    last_cycle = -1
    for cycle, items in reader.groups(events):
        last_cycle=cycle
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
        if redirect_pending is not None:
            prior_cycle,prior=redirect_pending
            require(cycle==prior_cycle+1 and pf is not None and
                    (pf['rob'],pf['self'])==(prior['rob'],prior['self']),
                    'missing next-cycle parent redirect')
        if pf:
            require(redirect_pending is not None and redirect_pending[0]==cycle-1,
                    'parent redirect differs from prior-cycle ROB redirect')
            require(pa is None and accept is None and da is None, 'accept during real parent flush')
        redirect_pending=(cycle,redirect) if redirect is not None else None
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
            if commit_sink is not None:commit_sink(f)
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
            if old is not None:fold_entry(old)
            live[f['rob']] = e
            max_live=max(max_live,len(live))

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
                t['stalls'] += 1
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
            new_request = dict(accept, accept_cycle=cycle, entry=e, stalls=0, expected_data=expected)
            transactions.append(new_request)
            require(len(transactions)<=4096,'transaction completion backlog exceeds explicit consumer profile')
            max_transactions=max(max_transactions,len(transactions))
            if last_accept_cycle is not None:gap_hist[cycle-last_accept_cycle]+=1
            last_accept_cycle=cycle
        counts['OVERLAP'] += int(response is not None and accept is not None)
        counts['TRIPLE_OVERLAP'] += int(response is not None and move is not None and accept is not None)
        r_slot = old_p if move else old_r if live_r and response is None else None
        p_slot = new_request if accept else old_p if live_p and move is None else None
        require(p_slot is None or r_slot is None or p_slot['seq'] != r_slot['seq'], 'same transaction occupies both slots')
        pending = int(p_slot is not None) + int(r_slot is not None)
        require(counts['ACCEPT'] == counts['RESPONSE'] + counts['KILL'] + pending, 'prefix request conservation violated')
        require(counts['DIV_ACCEPT'] == counts['DIV_RESPONSE'] + counts['DIV_KILL'] + int(active_div is not None),
                'prefix DIV conservation violated')
        while transactions and transactions[0].get('outcome') in ('response','kill'):
            emit_transaction(transactions.popleft())
    if redirect_pending is not None:
        require(not require_complete and redirect_pending[0]==last_cycle,'missing next-cycle parent redirect')
    unfinished = [e for e in live.values() if not e['done'] and not e['cancelled']]
    pending = int(p_slot is not None) + int(r_slot is not None)
    if require_complete:
        require(counts['STATE'] > 0, 'missing initial state observation')
        require(not previous_activity, 'missing final inactive state observation')
        require(pending == 0, 'unfinished FU requests')
        require(active_div is None, 'unfinished DIV request')
        require(not unfinished, 'unfinished ROB allocations')
    for entry in live.values():fold_entry(entry)
    require(counts['ACCEPT'] == counts['RESPONSE'] + counts['KILL'] + pending, 'final request conservation violated')
    while transactions:emit_transaction(transactions.popleft())
    return dict(status='O2_TRACE_PASS' if require_complete else 'O2_PARTIAL_TRACE_AUDIT',
                input_sha256=reader.sha.hexdigest(), schema=schema,
                counts=dict(counts), vfex4_fu_counts=dict(kinds), pending_count=pending,
                pending_div_count=int(active_div is not None), unfinished_rob_count=len(unfinished),
                transaction_count=transaction_count,transaction_sha256=transaction_hash.hexdigest(),
                storage=dict(max_live_rob=max_live,max_pending_transactions=max_transactions,max_cycle_records=reader.max_cycle_records),
                o2_coverage=o2_coverage(counts),
                response_latency_histogram={str(k):v for k,v in sorted(response_hist.items())},
                observed_accept_gap_histogram={str(k):v for k,v in sorted(gap_hist.items())},
                clock_mapping='direct ungated VFEX4/ROB global cycle; independent P/R transition audit',
                scope='trace and accepted-source full128 arithmetic audit; ISA legality/architectural state require workload and DiffTest',
                runtime_reset_audited=False, performance_measured=False)


def analyze(text, *, require_complete=True):
    """Small-fixture compatibility helper; production callers use audit_files."""
    transactions=[]
    result=analyze_reader(Reader([io.StringIO(text)]),require_complete=require_complete,transaction_sink=transactions.append)
    for key in ('transaction_count','transaction_sha256','storage'):result.pop(key)
    result['transactions']=transactions
    return result

def audit_files(paths, *, require_complete=True, transaction_sink=None, commit_sink=None):
    from contextlib import ExitStack
    with ExitStack() as stack:
        streams=[stack.enter_context(Path(p).open('r',encoding='utf-8')) for p in paths]
        reader=Reader(streams)
        result=analyze_reader(reader,require_complete=require_complete,transaction_sink=transaction_sink,commit_sink=commit_sink)
        return result,reader.uart,''.join(reader.counter_rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs',nargs='+',type=Path);parser.add_argument('--partial',action='store_true')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(not args.output.exists(),'fresh audit output')
    result,uart,counters=audit_files(args.logs,require_complete=not args.partial)
    args.output.mkdir(parents=True)
    (args.output/'protocol.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'uart.txt').write_text(uart)
    (args.output/'counter-source.txt').write_text(counters)
    print(json.dumps(result,indent=2))
