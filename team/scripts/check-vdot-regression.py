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

def check(text, manifest, exit_code):
    require(exit_code == 0, 'emulator exit code is not zero')
    require('The first instruction of core 0 has commited. Difftest enabled.' in text and 'The reference model is ' in text, 'missing DiffTest runtime banner')
    require(not re.search(r'T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)|HIT BAD TRAP|Assertion failed|different at pc', text), 'failure in raw log')
    uart = re.sub(r'T12_(?:ENQUEUE|ACCEPT|RESPONSE|KILL|STALL|COMMIT|REDIRECT|VFEX4_ACCEPT|VFEX4_WAIT)\s+[^\n]*\n', '', text)
    summaries=list(re.finditer(r'T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0',uart))
    require(len(summaries)==1,'missing or duplicate successful workload summary')
    require('HIT GOOD TRAP' in uart[summaries[0].end():], 'no GOOD TRAP after complete summary')
    require(re.findall(r'T12_GROUP_PASS id=(\d+) checkpoints=32 bytes=16384',uart)==['0','1','2','3'], 'missing/reordered group result')
    events=[]
    for line in text.splitlines():
        m=re.search(r'T12_(ENQUEUE|ACCEPT|RESPONSE|KILL|STALL|COMMIT|REDIRECT|VFEX4_ACCEPT|VFEX4_WAIT)\s+(.*)',line)
        if not m: continue
        fields=dict(re.findall(r'(\w+)\s*=\s*(0x[0-9a-fA-F]+|[0-9]+\s*:\s*[0-9]+|[0-9]+)',m[2]))
        require('cycle' in fields and 'rob' in fields,'malformed observer event')
        fields={k:re.sub(r'\s','',v) for k,v in fields.items()}
        events.append((int(fields['cycle']),len(events),m[1],fields))
    require(events,'missing RTL observer events')
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
            require(key not in entries or entries[key]['done'] or entries[key]['cancelled'], 'reallocated live ROB identity')
            require(int(f['word'],16)&0xfe00707f==0x0200000b,'observer enqueued a non-vdot instruction')
            entries[key]={'done':False,'cancelled':False,'accepted':False,'responded':False,'pc':f['pc'],'pdest':None}
        elif kind=='ACCEPT':
            require(key in entries,'accept without observed enqueue')
            require(pending is None,'two outstanding FU requests')
            e=entries[key]
            require(not e['accepted'],'duplicate FU accept')
            e['accepted']=True;e['pdest']=f['pdest'];pending=key
            require(f['vl']=='8' and f['illegal']=='0','unexpected illegal stress request')
        elif kind=='RESPONSE':
            require(pending==key,'response without matching accepted request')
            require(entries[key]['pdest']==f['pdest'],'response identity changed')
            require(int(f['data'],16)>>32==0,'high 96 result bits are nonzero')
            require(f['illegal']=='0','unexpected stress exception')
            entries[key]['responded']=True;pending=None
        elif kind=='KILL':
            require(pending==key,'kill without matching accepted request')
            require(ptr(f['redirect'])!=key,'self-flush does not prove younger cancellation')
            entries[key]['cancelled']=True;pending=None
        elif kind=='STALL':
            require(pending==key,'stall without matching accepted request')
        elif kind=='REDIRECT':
            for k,e in entries.items():
                # isAfter with wrap bits; at most one ROB capacity is in flight.
                delta=(k-key)%(2*ROB_SIZE)
                if not e['done'] and not e['cancelled'] and 0<delta<ROB_SIZE:
                    if e['accepted']: counts['ACCEPTED_THEN_SQUASHED']+=1
                    e['cancelled']=True
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
