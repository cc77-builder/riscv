"""O2 companion to frozen O1 frames: FTQ ownership and actual CSR windows.

No legacy T12/T13 records are enabled or accepted. Conversion to the reviewed
T13 *pure window algorithm* happens only after strict O2 identity validation.
"""
from collections import Counter, defaultdict
import re

from check_trace import audit, record as base_record, require, killed

FIELDS = {
    'O2_ROB_BEGIN': 'schema cycle mode robsize ftqsize predictwidth renamewidth commitwidth hart',
    'O2_CSR_BEGIN': 'schema cycle mode hart',
    'O2_CSR_OWNER_BEGIN': 'schema cycle mode hart',
    'O2_FTQ_ENQ': 'cycle slot rf rv ftf ftv fto',
    'O2_FTQ_COMMIT': 'cycle slot rf rv ftf ftv fto',
    'O2_FTQ_REDIRECT': 'cycle rf rv self ftf ftv fto',
    'O2_COUNTER_ENQ': 'cycle slot rf rv pc word empty wait block',
    'O2_COUNTER_COMMIT': 'cycle slot rf rv pc word data',
    'O2_CSR_ISSUE': 'cycle rf rv addr wen',
    'O2_CSR_SAMPLE': 'cycle addr data wen',
    'O2_RETIRE': 'cycle slot rf rv pc word count data',
}
FIELDS = {k:set(v.split()) for k,v in FIELDS.items()}
HEX = {'pc','word','data','addr'}
BOUNDS = dict(cycle=2**64, schema=3, mode=3, hart=1, rf=2, rv=48, ftf=2,
              ftv=8, fto=16, slot=8, pc=2**64, word=2**32, data=2**64,
              addr=4096, empty=2, wait=2, block=2, wen=2, self=2, count=9,
              robsize=49, ftqsize=9, predictwidth=17, renamewidth=7, commitwidth=9)
START, STOP = 0x51300013, 0x51400013


def record(line):
    require(len(line) <= 4096, 'oversized O2 record')
    tokens = re.sub(r'=\s+', '=', line.strip()).split()
    require(bool(tokens) and tokens[0] in FIELDS, 'unknown O2 record')
    tag, row = tokens[0], {}
    for token in tokens[1:]:
        pair = token.split('=')
        require(len(pair) == 2, 'malformed O2 field')
        key,value = pair
        require(key in FIELDS[tag] and key not in row, 'unknown/duplicate O2 field')
        require(re.fullmatch(r'0x[0-9a-fA-F]+' if key in HEX else r'[0-9]+', value), 'invalid O2 number')
        row[key] = int(value, 16 if key in HEX else 10)
        require(row[key] < BOUNDS[key], 'O2 field out of range: '+key)
    require(row.keys() == FIELDS[tag], 'missing O2 field')
    if tag.endswith('_ENQ'):
        require(row['slot'] < 6, 'invalid rename slot')
    if tag == 'O2_RETIRE':
        require(row['count'] > 0, 'empty retirement')
    return tag,row


def key(row):
    return row['rf'],row['rv']


def identity(row):
    return row['cycle'],row.get('slot',0),*key(row)


def collect(lines, mode):
    rows = defaultdict(list)
    headers = {}
    last = {}
    for raw in lines:
        line = raw.strip()
        require(not line.startswith('T13_'), 'legacy observer mixed with O2')
        if not line.startswith('O2_'):
            require(re.search(r'\bO2_', line) is None, 'damaged O2 prefix')
            continue
        tag,row = record(line)
        if tag.endswith('_BEGIN'):
            require(tag not in headers and row['cycle']==0 and row['schema']==2 and row['mode']==mode
                    and row['hart']==0, 'duplicate/invalid O2 epoch')
            if tag=='O2_ROB_BEGIN':
                require((row['robsize'],row['ftqsize'],row['predictwidth'],row['renamewidth'],row['commitwidth'])
                        ==(48,8,16,6,8), 'unsupported O2 profile')
            headers[tag]=row
        else:
            origin = 'O2_CSR_BEGIN' if tag=='O2_CSR_SAMPLE' else 'O2_CSR_OWNER_BEGIN' if tag=='O2_CSR_ISSUE' else 'O2_ROB_BEGIN'
            require(origin in headers, 'O2 event before header')
            order = row['cycle'], row.get('slot',0)
            require(tag not in last or order>last[tag], 'duplicate/reversed O2 event')
            last[tag]=order
            rows[tag].append(row)
    require(set(headers)=={'O2_ROB_BEGIN','O2_CSR_BEGIN','O2_CSR_OWNER_BEGIN'}, 'incomplete O2 headers')
    return rows


def ftq_audit(lines, rows):
    # Every extension record must correspond to exactly one base event, and vice
    # versa. This prevents deleting a complete FTQ lifecycle while keeping EXU.
    base = defaultdict(list)
    for line in lines:
        if line.startswith(('O1_ROB_ENQ ', 'O1_ROB_COMMIT ', 'O1_ROB_REDIRECT ')):
            tag,row=base_record(line)
            base[tag].append(row)
    groups=defaultdict(list)
    for suffix in ('ENQ','COMMIT','REDIRECT'):
        old, new=base['O1_ROB_'+suffix],rows['O2_FTQ_'+suffix]
        require(len(old)==len(new), 'FTQ/base event cardinality mismatch')
        for a,b in zip(old,new):
            require(identity(a)==identity(b) and (suffix!='REDIRECT' or a['self']==b['self']), 'FTQ/base identity mismatch')
            groups[b['cycle']].append((suffix,b))
    live={}; count=Counter(); last_flag=None
    for cycle, group in sorted(groups.items()):
        for tag,row in sorted(group,key=lambda x:({'COMMIT':0,'REDIRECT':1,'ENQ':2}[x[0]],x[1].get('slot',0))):
            ptr=key(row)
            if tag=='ENQ':
                require(ptr not in live,'duplicate FTQ ROB owner')
                live[ptr]=row; count['allocated']+=1
            elif tag=='COMMIT':
                require(ptr in live,'FTQ commit without owner')
                enq=live.pop(ptr)
                require(all(row[k]==enq[k] for k in ('ftf','ftv','fto')), 'FTQ commit identity mismatch')
                count['committed']+=1
                if last_flag is not None and last_flag != row['ftf']: count['wraps']+=1
                last_flag=row['ftf']
            else:
                for p in list(live):
                    if killed(p,(*ptr,row['self']),48):
                        del live[p]; count['squashed']+=1
    require(not live,'unfinished FTQ owners')
    return dict(count)


def counter_audit(rows):
    issues,samples=rows['O2_CSR_ISSUE'],rows['O2_CSR_SAMPLE']
    require(len(issues)==len(samples),'CSR owner/sample cardinality mismatch')
    paired={}
    for issue,sample in zip(issues,samples):
        require(all(issue[k]==sample[k] for k in ('cycle','addr','wen')), 'CSR sample/owner mismatch')
        require(issue['addr'] in (0xc00,0xc02), 'not an observed counter')
        paired[issue['cycle']]=sample
    groups=defaultdict(list)
    for tag in ('O2_COUNTER_ENQ','O2_COUNTER_COMMIT','O2_FTQ_REDIRECT','O2_CSR_ISSUE'):
        for row in rows[tag]: groups[row['cycle']].append((tag,row))
    live={}; completed={}; counts=Counter()
    priority={'O2_COUNTER_COMMIT':0,'O2_FTQ_REDIRECT':1,'O2_COUNTER_ENQ':2,'O2_CSR_ISSUE':3}
    for cycle,group in sorted(groups.items()):
        canceled={}
        if any(tag=='O2_FTQ_REDIRECT' for tag,_ in group):
            require(not any(tag in ('O2_COUNTER_ENQ','O2_COUNTER_COMMIT') for tag,_ in group),
                    'counter allocation/commit during ROB redirect')
        for tag,row in sorted(group,key=lambda x:(priority[x[0]],x[1].get('slot',0))):
            ptr=key(row)
            if tag=='O2_COUNTER_ENQ':
                require(ptr not in live and row['word']&127==0x73 and row['word']>>20 in (0xc00,0xc02),'bad counter allocation')
                live[ptr]=(row,None); counts['allocated']+=1
            elif tag=='O2_CSR_ISSUE':
                owner=live if ptr in live else canceled
                require(ptr in owner,'CSR sample without allocated owner')
                enq,prior=owner[ptr]
                require(prior is None and enq['cycle']<cycle and enq['word']>>20==row['addr'], 'counter issue identity/time mismatch')
                owner[ptr]=(enq,paired[cycle]); counts['sampled']+=1
            elif tag=='O2_COUNTER_COMMIT':
                require(ptr in live,'counter commit without allocation')
                enq,sample=live.pop(ptr)
                require(sample is not None and sample['cycle']<cycle and row['data']==sample['data']
                        and all(enq[k]==row[k] for k in ('pc','word')), 'counter retirement/sample mismatch')
                require(sample['wen']==0 and (row['word']>>12)&7 in (1,2,3,5,6,7),
                        'invalid committed read-only counter access')
                completed[identity(row)]=(enq,sample,row); counts['committed']+=1
            else:
                for p in list(live):
                    if killed(p,(*ptr,row['self']),48):
                        canceled[p]=live.pop(p); counts['squashed']+=1
    require(not live,'unfinished counter allocations')
    return dict(counts),completed


def window_events(rows, completed, lines):
    """Build validated inputs for trace_windows; values never come from UART."""
    active=False; windows=0; events=dict(RETIRE=[],COUNTER_ENQUEUE=[],CSR_SAMPLE=[])
    base_commits={identity(r):r for t,r in (base_record(x) for x in lines if x.startswith('O1_ROB_COMMIT '))}
    for row in rows['O2_RETIRE']:
        word=row['word']
        if word==START:
            require(not active,'nested counter window'); active=True
        require(active,'retirement outside window')
        if word&0xfe00707f==0x0200000b:
            require(identity(row) in base_commits and all(base_commits[identity(row)][k]==row[k] for k in ('pc','word')), 'window VDot/base commit mismatch')
        item={('flag' if k=='rf' else 'rob' if k=='rv' else k):v for k,v in row.items()}
        events['RETIRE'].append(item)
        if word&127==0x73 and word>>20 in (0xc00,0xc02):
            require(identity(row) in completed,'window counter lacks full lifecycle')
            enq,sample,commit=completed[identity(row)]
            require(all(commit[k]==row[k] for k in ('pc','word','data')), 'window counter commit mismatch')
            events['COUNTER_ENQUEUE'].append({('flag' if k=='rf' else 'rob' if k=='rv' else k):v for k,v in enq.items() if k!='slot'})
            events['CSR_SAMPLE'].append(sample)
        if word==STOP:
            active=False; windows+=1
    require(not active,'unterminated counter window')
    return windows,events


def extended_audit(lines, mode=2, *, vdot=True):
    lines=[x.strip() for x in lines]
    protocol=audit(lines,mode,'fullcore') if vdot else None
    rows=collect(lines,mode)
    ftq=ftq_audit(lines,rows)
    counters,completed=counter_audit(rows)
    windows,events=window_events(rows,completed,lines)
    return dict(status='O1_EXTENDED_PROTOCOL_PASS',protocol=protocol,ftq=ftq,counters=counters,windows=windows),events
