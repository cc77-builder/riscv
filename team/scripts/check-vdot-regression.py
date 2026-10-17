"""Strict T12 full-core trace checker; missing event coverage is NOT a pass."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

ROB_SIZE = 48  # The pinned MinimalConfig; record and reject other configurations.

def require(ok, message):
    if not ok:
        raise ValueError(message)

EVENT_FIELDS = {
    'ENQUEUE': ('cycle', 'rob', 'pc', 'ftq', 'word'),
    'ACCEPT': ('cycle', 'rob', 'pdest', 'vl', 'illegal'),
    'RESPONSE': ('cycle', 'rob', 'pdest', 'illegal', 'data'),
    'KILL': ('cycle', 'rob', 'redirect', 'state'),
    'STALL': ('cycle', 'rob'),
    'COMMIT': ('cycle', 'rob', 'pc', 'ftq'),
    'REDIRECT': ('cycle', 'rob', 'ftq'),
    'VFEX4_ACCEPT': ('cycle', 'rob', 'fu'),
    'VFEX4_WAIT': ('cycle', 'rob', 'fu', 'busy'),
}


def extract_events(text):
    """Remove only complete observer records. UART may surround a whole record.

    The final runner captures hardware and UART streams separately. Partial
    records must fail, never be guessed, dropped, or treated as missing coverage.
    """
    events = []
    kinds = '|'.join(EVENT_FIELDS)
    pattern = re.compile(r'T12_(' + kinds + r') +([^\n]*)\n')
    def take(match):
        kind, body = match.groups()
        values = []
        for field in EVENT_FIELDS[kind]:
            value = r'[01]\s*:\s*[0-9]+' if field in ('rob', 'ftq', 'redirect') else (
                r'0x[0-9a-fA-F]+' if field in ('pc', 'word', 'data', 'fu') else r'[0-9]+')
            values.append(field + r'=\s*(' + value + ')')
        parsed = re.fullmatch(r'\s+'.join(values) + r'\s*', body)
        require(parsed is not None, 'malformed observer event: ' + kind)
        fields = {key: re.sub(r'\s', '', value)
                  for key, value in zip(EVENT_FIELDS[kind], parsed.groups())}
        events.append((int(fields['cycle']), len(events), kind, fields))
        return ''
    uart = pattern.sub(take, text)
    allowed = {'T12_BEGIN', 'T12_GROUP_PASS', 'T12_SUMMARY',
               'T12_MISMATCH', 'T12_CSR_FAIL', 'T12_SPEC_FAIL'}
    require(all(tag in allowed for tag in re.findall(r'T12_[A-Z0-9_]*', uart)),
            'malformed or truncated observer event')
    return events, uart


VDOT_FU_TYPE = 0x800000000  # pinned FuType.vdot (bit 35)
FU_EVENTS = {'ACCEPT', 'RESPONSE', 'KILL', 'STALL'}


def normalize_fu_cycles(events):
    """Anchor gated FU ticks to the *same* parent VFEX4 handshake.

    ExeUnit's Dispatcher connects in/out ready-valid without a register. Its
    uncer_en_reg holds the FU gate open from in.fire through out.fire (including
    backpressure and cancellation). Thus ticks within an outstanding transaction
    advance each core cycle, but idle gaps do not. Never compare raw FU ticks to
    ROB cycles. Match every parent accept one-to-one and check the resulting time
    against surrounding un-gated records in the original stderr stream.
    """
    parent = sorted((e for e in events if e[2]=='VFEX4_ACCEPT'
                     and int(e[3]['fu'],16)==VDOT_FU_TYPE), key=lambda e:e[0])
    child = sorted((e for e in events if e[2] in FU_EVENTS), key=lambda e:(e[0],e[1]))
    require(len(parent)==sum(e[2]=='ACCEPT' for e in child), 'parent/FU acceptance count mismatch')
    mapped = {}; active = None; index = 0; last_end = -1
    for tick, order, kind, fields in child:
        if kind=='ACCEPT':
            require(active is None, 'two outstanding FU requests')
            anchor = parent[index]; index += 1
            require(anchor[3]['rob']==fields['rob'], 'parent/FU acceptance identity mismatch')
            require(anchor[0]>last_end, 'overlapping parent/FU transactions')
            active = (tick,anchor[0],fields['rob'])
        require(active is not None and active[2]==fields['rob'], 'FU event without matching accepted request')
        cycle = active[1]+tick-active[0]
        if kind in ('RESPONSE','STALL'):
            require(tick-active[0]>=3, 'FU response precedes E3')
        mapped[order] = (cycle,order,kind,fields)
        if kind in ('RESPONSE','KILL'):
            last_end = cycle; active = None
    require(active is None, 'unfinished FU request at end of run')
    # Buffering may delay a stream, but cannot reorder bytes within stderr.
    # This guard also rejects an incorrect clock mapping instead of hiding it.
    global_events = [e for e in events if e[2] not in FU_EVENTS]
    require(all(a[0]<=b[0] for a,b in zip(global_events,global_events[1:])),
            'un-gated observer cycles are out of order')
    before = -1
    for event in events:
        if event[2] in FU_EVENTS:
            require(mapped[event[1]][0]>=before, 'FU clock mapping precedes surrounding global event')
        else: before=event[0]
    after = float('inf')
    for event in reversed(events):
        if event[2] in FU_EVENTS:
            require(mapped[event[1]][0]<=after, 'FU clock mapping follows surrounding global event')
        else: after=event[0]
    return [mapped.get(e[1],e) for e in events]


def check(text, manifest, exit_code):
    require(exit_code == 0, 'emulator exit code is not zero')
    require('The first instruction of core 0 has commited. Difftest enabled.' in text and 'The reference model is ' in text, 'missing DiffTest runtime banner')
    require(not re.search(r'T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)|HIT BAD TRAP|Assertion failed|different at pc', text), 'failure in raw log')
    events, uart = extract_events(text)
    summaries=list(re.finditer(r'^T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0$',uart,re.MULTILINE))
    require(len(summaries)==1 and uart.count('T12_SUMMARY')==1,'missing or duplicate successful workload summary')
    require('HIT GOOD TRAP' in uart[summaries[0].end():], 'no GOOD TRAP after complete summary')
    groups=list(re.finditer(r'^T12_GROUP_PASS id=(\d+) checkpoints=32 bytes=16384$',uart,re.MULTILINE))
    require([m[1] for m in groups]==['0','1','2','3'], 'missing/reordered group result')
    begins=list(re.finditer(r'^T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1$',uart,re.MULTILINE))
    require(len(begins)==1 and uart.count('T12_BEGIN')==1 and begins[0].start()<groups[0].start()
            and groups[-1].end()<summaries[0].start(), 'invalid begin/group/summary order')
    require(events,'missing RTL observer events')
    events = normalize_fu_cycles(events)
    # Rob.scala observes canEnqueue, while both the entry write and valid-bit
    # allocation additionally require !io.redirect.valid. Such prints describe
    # suppressed attempts, irrespective of pointer age or printf ordering.
    redirect_cycles = {e[0] for e in events if e[2] == 'REDIRECT'}
    # Verilog printf order across modules is not a hardware ordering. Stable cycle
    # order with retire/redirect before re-allocation models the queue boundaries.
    rank={'COMMIT':0,'REDIRECT':1,'ENQUEUE':2,'ACCEPT':3,'STALL':4,'RESPONSE':5,'KILL':6,'VFEX4_ACCEPT':7,'VFEX4_WAIT':8}
    events.sort(key=lambda e:(e[0],rank[e[2]],e[1]))
    entries={}; pending=None; counts=Counter(); kinds=Counter(); last_rob=None;last_ftq=None
    def ptr(s):
        flag,value=map(int,s.split(':'))
        require(flag in (0,1) and 0<=value<ROB_SIZE,'invalid ROB pointer')
        return flag*ROB_SIZE+value
    for cycle,_,kind,f in events:
        key=ptr(f['rob']);counts[kind]+=1
        if kind=='ENQUEUE':
            require(int(f['word'],16)&0xfe00707f==0x0200000b,'observer enqueued a non-vdot instruction')
            if cycle in redirect_cycles:
                counts['SUPPRESSED_ENQUEUE'] += 1
                continue
            require(key not in entries or entries[key]['done'] or entries[key]['cancelled'], 'reallocated live ROB identity')
            entries[key]={'done':False,'cancelled':False,'cancel_cycle':None,'accepted':False,'responded':False,'pc':f['pc'],'pdest':None}
        elif kind=='ACCEPT':
            require(key in entries,'accept without observed enqueue')
            require(pending is None,'two outstanding FU requests')
            e=entries[key]
            # CtrlBlock sends s1_s3_redirect to ROB and its one-cycle registered
            # s2_s4_redirect to ExuBlock/FU. ROB cancellation is immediate, but
            # same-cycle FU handshakes precede that flush. Retirement stays banned.
            require((not e['cancelled'] or e['cancel_cycle']==cycle) and not e['done'],'cancelled or retired instruction accepted')
            require(not e['accepted'],'duplicate FU accept')
            if e['cancelled']: counts['ACCEPTED_THEN_SQUASHED']+=1
            e['accepted']=True;e['pdest']=f['pdest'];pending=key
            require(f['vl']=='8' and f['illegal']=='0','unexpected illegal stress request')
        elif kind=='RESPONSE':
            require(pending==key,'response without matching accepted request')
            require(not entries[key]['cancelled'] or entries[key]['cancel_cycle']==cycle,'cancelled request produced a response')
            require(entries[key]['pdest']==f['pdest'],'response identity changed')
            require(int(f['data'],16)>>32==0,'high 96 result bits are nonzero')
            require(f['illegal']=='0','unexpected stress exception')
            entries[key]['responded']=True;pending=None
        elif kind=='KILL':
            require(pending==key,'kill without matching accepted request')
            require(0<(key-ptr(f['redirect']))%(2*ROB_SIZE)<ROB_SIZE,'kill does not prove younger cancellation')
            entries[key]['cancelled']=True
            if entries[key]['cancel_cycle'] is None: entries[key]['cancel_cycle']=cycle-1
            pending=None
        elif kind=='STALL':
            require(pending==key,'stall without matching accepted request')
        elif kind=='REDIRECT':
            for k,e in entries.items():
                # isAfter with wrap bits; at most one ROB capacity is in flight.
                delta=(k-key)%(2*ROB_SIZE)
                if not e['done'] and not e['cancelled'] and 0<delta<ROB_SIZE:
                    if e['accepted']: counts['ACCEPTED_THEN_SQUASHED']+=1
                    e['cancelled']=True
                    e['cancel_cycle']=cycle
        elif kind=='COMMIT':
            require(key in entries,'commit without observed enqueue')
            e=entries[key]
            require(not e['done'] and not e['cancelled'],'cancelled or duplicate commit')
            require(e['accepted'] and e['responded'],'commit without accepted FU response')
            require(e['pc']==f['pc'],'ROB identity bound to the wrong PC')
            e['done']=True
            rb=int(f['rob'].split(':')[0]);fq=int(f['ftq'].split(':')[0])
            if last_rob is not None and last_rob!=rb: counts['ROB_WRAP']+=1
            if last_ftq is not None and last_ftq!=fq: counts['FTQ_WRAP']+=1
            last_rob,last_ftq=rb,fq
        elif kind=='VFEX4_ACCEPT': kinds[f['fu']]+=1
    require(pending is None,'unfinished FU request at end of run')
    require(counts['ACCEPT']==counts['RESPONSE']+counts['KILL'],'FU request conservation violated')
    expected=sum(g['vdot_count'] for g in manifest['groups'])+manifest['speculation']['expected_architectural_vdot']
    require(counts['COMMIT']==expected,f'vdot retirement count {counts["COMMIT"]} != {expected}')
    obligations={'accepted_younger_squashed':counts['ACCEPTED_THEN_SQUASHED']>0,
                 'inflight_fu_killed':counts['KILL']>0,
                 'shared_vfex4_fu_kinds':len(kinds)>=2,
                 'shared_vfex4_backpressure':counts['VFEX4_WAIT']>0,
                 'vdot_writeback_backpressure':counts['STALL']>0,
                 'rob_wrap_repeated':counts['ROB_WRAP']>=8,
                 'ftq_wrap_repeated':counts['FTQ_WRAP']>=8}
    complete=all(obligations.values())
    return {'status':'T12_CONTROL_REGRESSION_PASS' if complete else 'T12_COVERAGE_INCOMPLETE',
            'clock_mapping':'gated FU ticks anchored one-to-one to parent VFEX4 accepts; checked against surrounding global records',
            'architectural_checks':'PASS','coverage':obligations,'counts':dict(counts),
            'vfex4_fu_counts':dict(kinds),'expected_vdot_commits':expected,
            'scope':'pinned MinimalConfig M-mode; not virtualization/PPA/performance acceptance'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--exit-code',required=True,type=int)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=check(args.log.read_text(errors='replace'),json.loads(args.manifest.read_text()),args.exit_code)
    encoded=json.dumps(result,indent=2)+'\n'
    if args.output: args.output.write_text(encoded)
    print(encoded,end='')
    raise SystemExit(0 if result['status']=='T12_CONTROL_REGRESSION_PASS' else 2)
