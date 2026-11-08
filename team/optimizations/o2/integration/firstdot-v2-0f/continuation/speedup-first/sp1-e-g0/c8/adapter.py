"""SP1-E original-C8 offline gates. Never launches or loads a target/reference."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import hashlib, importlib.util, json, re, struct
HERE = Path(__file__).resolve().parent
POLICY = 'SP1-E-C8-FROZEN-ELF-MOVE-VALID-DATA-v1'

def need(ok, message):
    if not ok:
        raise ValueError('C8: ' + message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def objsha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())

def load(name):
    spec = importlib.util.spec_from_file_location('c8_' + name, HERE / 'frozen_host' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

windows, sp1, o2, failure = (load(n) for n in ('legacy_windows', 'analyze', 'legacy_o2', 'runtime_gate'))
START, STOP = 0x51300013, 0x51400013
COUNTERS = (0xc0202773, 0xc0002873, 0xc00028f3, 0xc02027f3)
PAIR_WORDS = ((0x00060513, 0x00068593), (0x00050613, 0x00058693), (0x10000f13, 0x00068f93))

def walk(words):
    starts = [pc for pc,w in words.items() if w == START]
    stops = [pc for pc,w in words.items() if w == STOP]
    need(len(starts) == len(stops) == 1 and starts[0] < stops[0], 'exact marker pair')
    pc, stop, ret = starts[0], stops[0], None
    path, visited, calls, returns = [], set(), 0, 0
    while True:
        need(pc in words and pc not in visited and len(path) < 20000, 'bounded exact C ABI path')
        visited.add(pc); word = words[pc]; path.append((pc, word))
        if pc == stop:
            break
        op, rd = word & 127, (word >> 7) & 31
        if op == 0x6f:
            need(rd == 1 and calls == 0, 'exactly one direct leaf call')
            imm = ((word >> 31) << 20) | (((word >> 21) & 1023) << 1) | (((word >> 20) & 1) << 11) | (word & 0xff000)
            target = pc + windows.signed(imm, 21)
            need(target > stop and target in words and target % 4 == 0, 'leaf target frozen ELF')
            ret = pc + 4; pc = target; calls += 1
        elif word == 0x00008067:
            need(calls == 1 and returns == 0 and ret is not None, 'single balanced ret')
            pc = ret; returns += 1
        else:
            need(op not in (0x63, 0x67), 'no branch/unknown indirect control')
            need(not (rd == 1 and op in (0x03,0x13,0x1b,0x33,0x3b,0x37,0x17,0x73)), 'ra clobber')
            pc += 4
    need(calls == returns == 1 and [w for _,w in path if w in COUNTERS] == list(COUNTERS), 'call/counters contract')
    return path

windows.walk = walk

def check_pin(pin):
    raw = Path(pin['path']).read_bytes()
    need(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'artifact pin ' + pin['path'])
    return raw

def case_manifest(case):
    for pin in case['artifacts'].values():
        check_pin(pin)
    return json.loads(check_pin(case['artifacts']['manifest']))

def model_slots(data, m, k):
    need(len(data) == m*k+k, 'packed A||x length')
    a = [x if x < 128 else x-256 for x in data]
    return [struct.pack('<I',sum(a[r*k+j]*a[m*k+j] for j in range(k)) & 0xffffffff).hex()+'00'*12 for r in range(m)]

def validate_static(case):
    m = case_manifest(case)
    symbols, read = windows.elf_data(Path(case['artifacts']['elf']['path']))
    if case['kind'] == 'performance':
        need(m['dataset'] == case['dataset'] and len(m['rows']) == 4 and len(m['plan']) == 24, 'frozen dataset/four rows/24 windows')
        need(m['boundary'] == 'pinned-XiangShan-fence-serialized-v2' and m['contract'] == 'r4-gemv-c-abi-entry-v1', 'frozen boundary')
        windows.check_compiled_cases(Path(case['artifacts']['elf']['path']), m)
        kernels = windows.elf_kernels(Path(case['artifacts']['elf']['path']))
        for i,row in enumerate(m['rows']):
            need((row['m'],row['k']) == (8,32), 'only C8 8x32')
            need((row['software'], row['method']) == [('basic','vdot'),('basic','rvv'),('reuse','vdot'),('reuse','rvv')][i], 'fixed four-cell order')
            raw = bytes.fromhex(''.join(row['stream']))
            need(model_slots(raw,8,32) == row['outputs'], 'independent full128 output model')
            walk(kernels[i])
        first = next((pc,w) for pc,w in walk(kernels[m['plan'][0]['index']]) if w&m['custom_mask'] == m['custom_match'])
        need((hex(first[0]),hex(first[1]),(first[1]>>7)&31) == tuple(case['negative_binding'][k] for k in ('pc','word','vd')), 'first custom negative binding')
        return {'status':'STATIC_PASS','dataset':m['dataset'],'windows':24,'outputs':96,'full128':True}
    need(len(m['cases']) == 48 and m['expected_dots'] == 1008 and not m['performance_measured'], 'original 48-call functional coverage')
    for c in m['cases']:
        raw = bytes(m['inputs'][c['input_symbol']]); address,size = symbols[c['input_symbol']]
        need(read(address,len(raw)) == raw, 'compiled input exact')
        slots=model_slots(raw,c['m'],c['k']);h=14695981039346656037
        for byte in bytes.fromhex(''.join(slots)):h=((h^byte)*1099511628211)&((1<<64)-1)
        need(h==c['expected_hash'],'independent full128 C output hash')
    expected=b''.join(struct.pack('<8Q',symbols[c['api_symbol']][0],symbols[c['input_symbol']][0],*(c[k] for k in ('m','k','size','dataset','api_index','expected_hash'))) for c in m['cases'])
    need(read(*symbols['r4_c_cases'])==expected,'all48 linked function/input/shape/hash bindings')
    a,n = symbols['config_reuse_gemv_8x32_reuse_vdot']
    words = [(a+i,struct.unpack('<I',read(a+i,4))[0]) for i in range(0,n,4)]
    first = next((pc,w) for pc,w in words if w&0xfe00707f == 0x0200000b)
    need((hex(first[0]),hex(first[1]),(first[1]>>7)&31) == tuple(case['negative_binding'][k] for k in ('pc','word','vd')), 'ordinary C first custom binding')
    return {'status':'STATIC_PASS','calls':48,'custom_commits':1008,'c8_calls':12,'windows':0,'performance_measured':False}

def canonicalize(events, manifest, kernels, elf):
    symbols, read = windows.elf_data(Path(elf))
    need('sink' in symbols and symbols['sink'][0] == 0x80131000, 'frozen output address')
    output = symbols['sink'][0] + 16
    proof = json.loads((HERE/'MOVE_ELIMINATION_PROOF.json').read_text())
    allowed = {(x['row'],int(x['pc'],0),int(x['word'],0)) for x in proof['whitelisted_eliminated_moves']['c8-performance-d'+str(manifest['dataset'])]}
    grouped, trailing, current = [], [], None
    for event in events['RETIRE']:
        need(all(type(event[k]) is int for k in ('pc','word','count','data')) and 0 <= event['data'] < 1<<64, 'retirement field type/range')
        if event['word'] == START:
            need(current is None,'nested start'); current=[]
        if current is None:
            need(grouped and event['cycle']==grouped[-1][-1]['cycle'] and event['count']==1 and event['word'] not in COUNTERS, 'bounded trailing retirement')
            trailing.append({k:event[k] for k in ('pc','word','count','data')});continue
        current.append(event)
        if event['word']==STOP:
            grouped.append(current);current=None
    need(current is None and len(grouped)==24,'complete 24 envelopes')
    canon, observed, summaries = [], [], []
    for seq,(group,entry) in enumerate(zip(grouped,manifest['plan'])):
        index=entry['index'];path=walk(kernels[index]); pos=j=0;local=[];pairs=[]
        stream=struct.unpack('<Q',read(symbols['cases'][0]+index*1104+56,8))[0]
        need(stream==0x80100000,'frozen shared stream pointer')
        while j<len(group):
            e=group[j];need(pos<len(path) and (e['pc'],e['word'])==path[pos],'exact expanded ELF path')
            count=e['count'];need(count in (1,2),'unknown compression size')
            pair=tuple(w for _,w in path[pos:pos+2])
            if pair in PAIR_WORDS:
                need(all((index,pc,w) in allowed for pc,w in path[pos:pos+2] if w != 0x10000f13),'pair PCs in exact whitelist')
                need(path[pos+1][0]==path[pos][0]+4,'independent pair contiguous')
                expected=[256,output] if pair==PAIR_WORDS[2] else [stream,output]
                if count==2:
                    need(pair != PAIR_WORDS[2] or e['data'] == 256,'compressed li256/move effective data')
                    vals=[e['data']];j+=1
                else:
                    need(j+1<len(group),'missing pair singleton')
                    other=group[j+1]
                    need((other['pc'],other['word'],other['count'])==(*path[pos+1],1),'pair second exact identity')
                    need(pair != PAIR_WORDS[2] or e['data'] == 256,'singleton li256 effective data')
                    vals=[e['data'],other['data']];j+=2
                local.append({'pc_words':path[pos:pos+2],'kind':'ELIMINATED_MOVE_EXPECTATIONS_NOT_OBSERVED_WRITEBACKS','expected':expected})
                pairs.append({'pos':pos,'count':count,'observed':vals});pos+=2;continue
            need(count==1,'nonwhitelisted compressed group')
            local.append({'pc':e['pc'],'word':e['word'],'data':('COUNTER' if e['word'] in COUNTERS else 'ELIMINATED_MOVE_NO_WB' if (index,e['pc'],e['word']) in allowed else e['data'])})
            pos+=1;j+=1
        need(pos==len(path) and len(pairs)==3,'complete path and exactly three independent pairs')
        canon.append(local);observed.append(pairs);summaries.append({'seq':seq,'logical':pos,'compressed_pairs':sum(p['count']==2 for p in pairs)})
    return {'policy':POLICY,'cross_control_sha256':objsha([canon,trailing]),'pair_observations_sha256':objsha(observed),'window_summaries':summaries,'trailing_records':len(trailing),'raw_retirement_sha256':objsha(events['RETIRE'])}

def committed_vectors(events):
    allocations={}; accepts={};responses={};used=set();sources=[];packets=[]
    for cycle,index,kind,f in events:
        if kind=='ENQUEUE': allocations.setdefault(f['rob'],[]).append((cycle,index,f))
    def epoch(f):
        rows=[r for r in allocations.get(f['rob'],[]) if r[0]<=f['cycle']]
        need(rows,'prior allocation epoch');cycle,index,e=max(rows,key=lambda r:(r[0],r[1]));return (f['rob'],cycle,index),e
    for _,_,kind,f in events:
        if kind=='ACCEPT':
            key,_=epoch(f);need(key not in accepts,'one accept per allocation');accepts[key]=f
        elif kind=='RESPONSE':
            need(f['seq'] not in responses,'one response per seq');responses[f['seq']]=f
    for _,_,kind,f in events:
        if kind!='COMMIT':continue
        key,e=epoch(f);need(key not in used and key in accepts,'unique committed accepted epoch');used.add(key);a=accepts[key]
        need(a['seq'] in responses,'committed response');r=responses[a['seq']]
        need(r['rob']==f['rob'] and a['cycle']<r['cycle']<f['cycle'] and e['pc']==f['pc'],'lifetime/PC identity')
        ident={k:e[k] for k in ('pc','word')}
        sources.append(ident|{k:a[k] for k in ('vl','illegal','vecwen','v0wen','vpu','vs1','vs2')})
        packets.append(ident|{k:r[k] for k in ('illegal','data','vecwen','v0wen','exception','vpu')})
    return sources,packets

def log_gate(case, stdout, stderr, exit_code, reference, mode, negative=False, context='CURRENT_CONTEXT'):
    need(mode in ('candidate','baseline'),'explicit hardware schema')
    need(context in ('CURRENT_CONTEXT','HISTORICAL_CONTEXT','SYNTHETIC_HOST_ONLY'),'explicit log context')
    if context=='CURRENT_CONTEXT':
        validate_runtime_context(case)
        common=json.loads((HERE.parent/'COMMON_CONTRACT.json').read_text())
        if not negative:need(str(reference)==common['runtime']['normal_reference']['path'],'current normal reference identity')
    elif context=='HISTORICAL_CONTEXT':
        need(mode=='baseline' and any(h['normal_reference_path']==str(reference) and h['negative']==negative for h in case['history_budget_facts']),'explicit pinned historical reference')
    else:need(str(reference)=='/FAKE_HOST_FIXTURE_NOT_A_LIBRARY','synthetic fixture not real reference')
    m=case_manifest(case);plain=failure.normalize_console(stderr+'\n'+stdout)
    need(plain.count('The first instruction of core 0 has commited. Difftest enabled.')==1,'live DiffTest exactly once')
    need(re.findall(r'The reference model is ([^\r\n]+)',plain)==[str(reference)],'exact reference path')
    need(('O2_' not in plain) if mode=='candidate' else ('SP1_' not in plain),'mixed/wrong observer schema')
    need(not re.search(r'CRITICAL\s+ERROR|double\s+trap|PMA\s+check\s+failed|R4C_FAIL',plain,re.I),'fatal runtime diagnostic')
    obs=sp1 if mode=='candidate' else o2
    if negative:
        fault=failure.validate_negative(plain,exit_code);binding=case['negative_binding']
        need((int(fault['pc'],0),int(fault['word'],0),fault['vd'],fault['bit'])==(int(binding['pc'],0),int(binding['word'],0),binding['vd'],100),'exact negative PC/word/vd/bit')
        events,_=obs.extract_events_and_uart(plain)
        enq=[f for _,_,k,f in events if k=='ENQUEUE'];commit=[f for _,_,k,f in events if k=='COMMIT']
        need(enq and commit and enq[0]['pc']==commit[0]['pc']==int(binding['pc'],0) and enq[0]['word']==int(binding['word'],0),'negative first real custom retirement')
        return {'status':'NEGATIVE_PASS','context':context,'qualification':'LOG_PARSE_ONLY_REQUIRES_PINNED_EXECUTION_RECEIPT','fault':fault,'observation':obs.analyze(plain,require_complete=False)}
    need(exit_code==0,'normal zero exit');failure.validate_failure_markers(plain)
    observation=obs.analyze(plain);all_events,uart=obs.extract_events_and_uart(plain)
    need(observation['counts']['COMMIT']==case['expected_custom_commits'],'all committed customs')
    sources,packets=committed_vectors(all_events)
    need(len(sources)==len(packets)==case['expected_custom_commits'],'all committed full128 source/result packets')
    result={'status':'NORMAL_PASS','context':context,'qualification':'LOG_PARSE_ONLY_REQUIRES_PINNED_EXECUTION_RECEIPT','case_id':case['case_id'],'mode':mode,'bin_sha256':case['artifacts']['bin']['sha256'],'manifest_sha256':case['artifacts']['manifest']['sha256'],'observer_events_sha256':objsha(all_events),'full128_packets_sha256':objsha(packets),'accepted_sources_sha256':objsha(sources),'custom_commits':len(packets),'observation':observation}
    if case['kind']=='performance':
        kernels=windows.elf_kernels(Path(case['artifacts']['elf']['path']))
        t13=''.join(x.group(0) for x in re.finditer(r'T13_(?:COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+[^\n]*\n',plain))
        events=windows.parse_events(t13);samples=windows.trace_windows(events,m,kernels);windows.check_uart(uart,m,samples)
        committed=Counter((f['cycle'],f['rob'],f['pc']) for _,_,k,f in all_events if k=='COMMIT')
        retired=Counter((e['cycle'],f"{e['flag']}:{e['rob']}",e['pc']) for e in events['RETIRE'] if e['word']&m['custom_mask']==m['custom_match'])
        need(committed==retired,'T13/observer complete custom binding')
        need(all(e['count']==1 for e in events['RETIRE'] if e['word']&m['custom_mask']==m['custom_match']),'uncompressed custom retirement')
        result.update(samples=samples,retirement_audit=canonicalize(events,m,kernels,case['artifacts']['elf']['path']),counter_events_sha256=objsha([events['CSR_SAMPLE'],events['COUNTER_ENQUEUE']]))
        result['cross_control_sha256']=result['retirement_audit']['cross_control_sha256']
    else:
        lines=[line for line in uart.splitlines() if line.startswith('R4C_')]
        expected=[f"R4C_BEGIN cases=48 contract={m['contract']}",'R4C_CONTROLS detected=5 expected=5']+[f"R4C_CASE seq={i} hash={c['expected_hash']}" for i,c in enumerate(m['cases'])]+['R4C_END executed=48 failures=0']
        need(lines==expected and uart.count('HIT GOOD TRAP')==1,'48 complete C ABI/CSR/full-result call checks and trap')
        result.update(calls=48,c8_calls=12,performance_measured=False,application_uart_sha256=objsha(lines))
    return result

def compare(baseline, candidate, replay=False):
    need(baseline.get('status')==candidate.get('status')=='NORMAL_PASS','both complete normal gates')
    if not replay:need((baseline.get('mode'),candidate.get('mode'))==('baseline','candidate'),'explicit cross-hardware roles')
    known=[c for c in json.loads((HERE/'CASES.json').read_text())['cases'] if c['case_id']==baseline.get('case_id')]
    need(len(known)==1,'known frozen comparison case')
    for r in (baseline,candidate):
        need(r['bin_sha256']==known[0]['artifacts']['bin']['sha256'] and r['manifest_sha256']==known[0]['artifacts']['manifest']['sha256'] and r['custom_commits']==known[0]['expected_custom_commits'],'exact known case images/cardinality')
    for key in ('case_id','bin_sha256','manifest_sha256','custom_commits','accepted_sources_sha256','full128_packets_sha256'):
        need(baseline[key]==candidate[key],'paired identity/full128 '+key)
    if replay:
        need(baseline['mode']==candidate['mode'],'same hardware replay')
        for key in ('samples','observer_events_sha256','counter_events_sha256','retirement_audit','application_uart_sha256'):
            need(baseline.get(key)==candidate.get(key),'exact replay '+key)
    if 'samples' not in baseline:
        need(baseline.get('application_uart_sha256')==candidate.get('application_uart_sha256'),'functional all48 hashes')
        return {'status':'FUNCTIONAL_PAIR_PASS','performance_measured':False}
    need(baseline['cross_control_sha256']==candidate['cross_control_sha256'],'all ordinary data/control across hardware')
    need([(x['seq'],x['id'],x['phase'],x['repeat'],x['instructions']) for x in baseline['samples']]==[(x['seq'],x['id'],x['phase'],x['repeat'],x['instructions']) for x in candidate['samples']],'all24 control/window work')
    cells=[]
    for ident in sorted({x['id'] for x in baseline['samples']}):
        a=[x['cycles'] for x in baseline['samples'] if x['id']==ident and x['phase']=='measured'];b=[x['cycles'] for x in candidate['samples'] if x['id']==ident and x['phase']=='measured']
        need(len(a)==len(b)==4,'four measured percell')
        need(Fraction(sum(b),sum(a))<=Fraction(102,100),'2% percell nonregression '+ident)
        cells.append({'id':ident,'baseline_mean':sum(a)/4,'candidate_mean':sum(b)/4,'candidate_over_baseline':str(Fraction(sum(b),sum(a)))})
    selected=next(x for x in cells if x['id'].endswith('reuse-vdot'))
    rvv=min(x['candidate_mean'] for x in cells if x['id'].endswith('-rvv'))
    return {'status':'PERFORMANCE_PROTECTION_PASS','cells':cells,'same_image_qualified_rvv_over_c8':rvv/selected['candidate_mean'],'anchor_1percent_applied':False,'new_global_adoption':False}


def validate_runtime_context(case, common=None):
    """Required before any future target receipt acceptance; no executable loading."""
    proof=json.loads((HERE/'MOVE_ELIMINATION_PROOF.json').read_text())
    raw=check_pin(proof['common_contract']); frozen=json.loads(raw)
    if common is not None:
        need(common==frozen,'runtime/config cannot drift from common freeze')
    for pin in proof['runtime_pins'].values():check_pin(pin)
    for entry in proof['source_pins']:check_pin(entry['artifact'])
    validate_static(case)
    return {'status':'PHYSICAL_CONTEXT_PASS','conditional_execution':'normal reset, no debug/singlestep, exact frozen workload; fresh live DiffTest mandatory','target_qualification':'NOT_TESTED'}


def receipt_header(case, record, annex):
    roles=['candidate-bit100','candidate-normal-recovery','baseline-normal-calibration','candidate-replay','baseline-replay']
    role=record.get('role')
    need(role in roles and role==annex.get('role'),'exact role binding')
    need(annex.get('case_id')==case['case_id'],'exact case binding')
    need(annex.get('execution_mode')=={'reset':'fresh','checkpoint':False,'debug':False,'singlestep':False},'fresh non-debug execution only')
    need(record.get('resource_ok') is True and record.get('cleanup_ok') is True and record.get('limit') is None,'resource/cleanup/no-limit receipt')
    need(type(record.get('guest_cycles')) is int and 0<record['guest_cycles']<=annex['max_guest_cycles'],'actual guest cap')
    need(type(record.get('elapsed_seconds')) in (int,float) and 0<record['elapsed_seconds']<=annex['max_wall_seconds'],'actual monotonic wall cap')
    need(annex['max_wall_seconds']<= (300 if role=='candidate-bit100' else 1500),'common per-role hard cap')
    need(annex.get('same_runtime_knobs')=={'seed':1,'ram':'128MB','cpu_affinity':[4],'group_threads_max':4,'rss_cap_bytes':12884901888,'logs_cap_bytes':2147483648},'frozen execution knobs')
    return role

def validate_role(case_id, run_dir, annex):
    """Future required receipt entry. log_gate alone is never target qualification.

    No execution occurs here. New runner/source closure and annex must be frozen
    and authorized separately. This entry does not approve or launch any process.
    """
    cases=json.loads((HERE/'CASES.json').read_text())['cases']
    found=[x for x in cases if x['case_id']==case_id];need(len(found)==1,'known case')
    case=found[0];run_dir=Path(run_dir)
    record=json.loads((run_dir/'record.json').read_text());role=receipt_header(case,record,annex)
    validate_runtime_context(case)
    need(annex.get('execution_source_pins') and type(annex['execution_source_pins']) is list,'frozen supervisor source closure required')
    for pin in annex['execution_source_pins']:check_pin(pin)
    need(record.get('execution_source_pins_sha256')==objsha(annex['execution_source_pins']),'receipt sourced from frozen supervisor closure')
    common=json.loads((HERE.parent/'COMMON_CONTRACT.json').read_text())
    need(annex.get('common_contract_sha256')==sha((HERE.parent/'COMMON_CONTRACT.json').read_bytes()),'common contract identity')
    mode='baseline' if role.startswith('baseline-') else 'candidate'
    emu=common['runtime'][mode+'_emu'];reference=annex['negative_reference'] if role=='candidate-bit100' else common['runtime']['normal_reference']
    check_pin(reference)
    if role=='candidate-bit100':
        fixtures=json.loads((HERE/'negative/RESULT.json').read_text())
        group='c8-perf' if case['kind']=='performance' else 'c8-functional'
        need(reference==fixtures['products'][group]['production'],'exact case bit100 wrapper')
    need(record.get('emu_sha256')==emu['sha256'] and record.get('reference_sha256')==reference['sha256'],'receipt real executable/reference identity')
    need(record.get('bin_sha256')==case['artifacts']['bin']['sha256'],'receipt frozen image')
    need(record.get('execution_mode')==annex['execution_mode'] and record.get('same_runtime_knobs')==annex['same_runtime_knobs'],'receipt actual execution config')
    raw={k:(run_dir/(k+'.log')).read_bytes() for k in ('stdout','stderr')}
    need(record.get('raw_sha256')=={k:sha(v) for k,v in raw.items()},'raw receipt hashes')
    need(sum(map(len,raw.values()))<=2147483648,'combined logs cap')
    plain=failure.normalize_console(raw['stdout'].decode()+'\n'+raw['stderr'].decode())
    need(re.findall(r'Guest cycle spent:\s*(\d+)',plain)==[str(record['guest_cycles'])],'actual complete guest receipt')
    need(re.findall(r'The image is ([^\r\n]+)',plain)==[case['artifacts']['bin']['path']],'actual image path')
    result=log_gate(case,raw['stdout'].decode(),raw['stderr'].decode(),record['exit_code'],reference['path'],mode,role=='candidate-bit100')
    result['qualification']='PINNED_RECEIPT_ROLE_PASS_NOT_CAMPAIGN_ADOPTION'
    result['role']=role
    return result


def compare_roles(case_id, baseline_dir, candidate_dir, baseline_annex, candidate_annex, replay=False):
    """Formal comparator: re-read both actual pinned receipts/logs; no dict shortcut."""
    baseline=validate_role(case_id,baseline_dir,baseline_annex)
    candidate=validate_role(case_id,candidate_dir,candidate_annex)
    need(Path(baseline_dir).resolve()!=Path(candidate_dir).resolve(),'fresh distinct run receipts')
    expected=('baseline-normal-calibration','candidate-normal-recovery')
    if not replay:
        need((baseline['role'],candidate['role']) in (expected,('baseline-replay','candidate-replay')),'formal paired roles')
    else:
        need((baseline['role'],candidate['role']) in (('baseline-normal-calibration','baseline-replay'),('candidate-normal-recovery','candidate-replay')),'formal distinct replay roles')
    result=compare(baseline,candidate,replay)
    result['qualification']='CURRENT_PINNED_PAIRED_RECEIPTS_PASS_NOT_DEFAULT_ADOPTION'
    return result
