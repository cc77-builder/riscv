"""Pure-host B3 functional collectors. Never execute target code or load reference libraries."""
from pathlib import Path
import hashlib, importlib, json, re, struct, sys
HERE=Path(__file__).resolve().parent
CONTRACT=json.loads((HERE/'CONTRACT.json').read_text())
DEPS=Path(CONTRACT['dependency_dir'])

def need(ok,message):
    if not ok: raise ValueError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def verify_pin(pin):
    need(Path(pin['path']).stat().st_size==pin['bytes'] and sha(pin['path'])==pin['sha256'],'frozen file drift: '+pin['path'])
for pin in CONTRACT['dependency_pins']: verify_pin(pin)
sys.path.insert(0,str(DEPS))
import legacy_adapter, legacy_workload, legacy_windows, runtime_gate, analyze, legacy_o2
for mod in (legacy_adapter,legacy_workload,legacy_windows,runtime_gate,analyze,legacy_o2):
    need(Path(mod.__file__).resolve().parent==DEPS,'foreign collector dependency')
REPLAY_KEYS=('architectural_commit','source','result','observer','uart_checks','csr_contract','div_events','completion')
SCOPES=('HOST_FIXTURE','HISTORICAL_LOG','TARGET_LOG_REQUIRES_RUNTIME_RECEIPT')

def descriptor(case_id):
    need(case_id in CONTRACT['cases'],'unknown case identity')
    c=CONTRACT['cases'][case_id]
    for k in ('elf','bin','manifest'): verify_pin(c[k])
    for pin in c['source_pins']:verify_pin(pin)
    return c

def check_coverage(case_id,counts,fu_counts):
    all_pairs_manifest=json.loads(Path(CONTRACT['cases']['o2-all-pairs']['manifest']['path']).read_text())
    div_minimum=sum(x['counts'].get('vidiv',0)+x['counts'].get('vfdiv',0) for x in all_pairs_manifest['cases'])
    need(div_minimum>0,'nonempty manifest DIV workload')
    obligations={
      'legacy-control':{'ACCEPTED_YOUNGER_SQUASHED':1,'KILL':1,'VFEX4_WAIT':1,'STALL':1,'ROB_WRAP':8,'FTQ_WRAP':8},
      'o2-all-pairs':{'COMMIT':all_pairs_manifest['expected_vdot_commits'],'DIV_RESPONSE':div_minimum},
      'o2-control':{'KILL_P':1,'KILL_R':1,'PARTIAL_KILL':1,'COMMIT':1208}}
    need(case_id in obligations,'unknown coverage case')
    checks={k:counts.get(k,0)>=v for k,v in obligations[case_id].items()}
    required_fu=[1<<35,1<<22]+([1<<26] if case_id=='o2-all-pairs' else [])
    checks['required_fu_classes']=all(fu_counts.get(hex(f),0)>0 for f in required_fu)
    need(all(checks.values()),'required functional coverage missing: '+str(checks))
    return checks

def decode_observer(text,mode,complete=True):
    need(mode in ('candidate','baseline'),'explicit observer mode')
    plain=runtime_gate.normalize_console(text)
    forbidden='O2' if mode=='candidate' else 'SP1'
    # O2_DIAG/CONTROL are UART program tags and remain valid for SP1.
    fields='|'.join(sorted(legacy_o2.FIELDS if forbidden=='O2' else analyze.FIELDS,key=len,reverse=True))
    need(re.search(forbidden+r'_(?:'+fields+r')[ \t]',plain) is None,'mixed observer schema')
    obs=analyze if mode=='candidate' else legacy_o2
    a=obs.analyze(plain,require_complete=complete)
    events,uart=obs.extract_events_and_uart(plain)
    need(not re.search(r'T13_(?:COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)',plain),'functional image must not carry micro counter/retire windows')
    return plain,obs,a,events,uart

def image_gate(plain,c,reference,negative):
    want=c['negative_reference'] if negative else CONTRACT['normal_reference']
    verify_pin(want)
    need(str(reference)==want['path'],'reference must match frozen case/role')
    need(re.findall(r'^The image is ([^\n]+)$',plain,re.M)==[c['bin']['path']],'exact image path')
    need(re.findall(r'^The reference model is ([^\n]+)$',plain,re.M)==[str(reference)],'exact reference path')
    need(plain.count('The first instruction of core 0 has commited. Difftest enabled.')==1,'one live DiffTest banner')
    legacy_workload.reject_fatal_output(plain)

def bind_architecture(events,c):
    _,read=legacy_windows.elf_data(c['elf']['path'])
    allocations={};accepts={};responses={};committed=[]
    for _,_,kind,f in events:
        if kind=='ENQUEUE':
            need(int.from_bytes(read(f['pc'],4),'little')==f['word'],'custom PC/word not in frozen ELF')
            allocations[f['rob']]=dict(f)
        elif kind=='ACCEPT':
            need(f['rob'] in allocations,'accept allocation absent')
            enq=allocations[f['rob']]
            need(enq['cycle']<=f['cycle'],'accept precedes allocation')
            accepts[f['seq']]=dict(f,allocation=dict(enq))
            allocations[f['rob']]['accepted_seq']=f['seq']
        elif kind=='RESPONSE': responses[f['seq']]=f
        elif kind=='COMMIT':
            enq=allocations.get(f['rob']);need(enq is not None and enq.get('accepted_seq') in accepts,'commit lacks accepted allocation')
            a=accepts[enq['accepted_seq']];out=responses.get(a['seq'])
            need(out is not None and out['cycle']<=f['cycle'],'commit lacks response')
            need(f['pc']==enq['pc'] and a['vl']==8 and a['illegal']==0 and out['exception']==0,'committed identity/config')
            committed.append({'pc':enq['pc'],'word':enq['word'],'vd':(enq['word']>>7)&31,'vs1':a['vs1'],'vs2':a['vs2'],'vl':a['vl'],'result':out['data'],'exception':out['exception']})
    need(committed,'nonempty architectural sequence')
    first=c['bit100'];need(committed[0]['pc']==first['pc'] and committed[0]['word']==first['word'] and committed[0]['vd']==first['vd'],'first committed custom binding')
    return committed

def collect(text,case_id,mode,reference,exit_code,run_id,scope='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT'):
    """Return log qualification only; real runner must separately verify identity/resource receipts."""
    need(scope in SCOPES and isinstance(run_id,str) and bool(run_id),'explicit scope/run id')
    c=descriptor(case_id);plain,obs,a,events,uart=decode_observer(text,mode)
    image_gate(plain,c,reference,False)
    m=json.loads(Path(c['manifest']['path']).read_text())
    work=legacy_adapter.check(plain,m,exit_code,mode,c['kind'],reference)
    coverage=check_coverage(case_id,a['counts'],a['vfex4_fu_counts'])
    arch=bind_architecture(events,c)
    need(len(arch)==c['expected_commits'],'exact architectural commit count')
    need(work['workload']['checked_register_bytes']==c['checked_register_bytes'],'complete target register checks')
    guest=re.findall(r'Guest cycle spent:\s*([0-9]+)',uart)
    instr=re.findall(r'Core-0 instrCnt = ([0-9]+), cycleCnt = ([0-9]+)',uart)
    need(len(guest)==len(instr)==1,'single completion counter receipt')
    markers=[s for s in uart.splitlines() if re.match(r'^(?:T12_|O2_DIAG_|O2_CONTROL_)',s)]
    need(markers,'nonempty ordered workload checks')
    dividends=[(kind,f) for _,_,kind,f in events if kind.startswith('DIV_')]
    need(dividends,'required DIV records')
    material={
      'architectural_commit':[{'pc':x['pc'],'word':x['word'],'vd':x['vd'],'vl':x['vl']} for x in arch],
      'source':[[x['vs1'],x['vs2']] for x in arch],
      'result':[[x['result'],x['exception']] for x in arch],
      'observer':events,'uart_checks':markers,
      'csr_contract':{'frozen_image':c['bin']['sha256'],'target_checks':c['csr_contract'],'workload_markers':markers},
      'div_events':dividends,'completion':{'guest_cycles':int(guest[0]),'instr_count':int(instr[0][0]),'cycle_count':int(instr[0][1])}}
    return {'status':'B3_FUNCTIONAL_LOG_PASS','case_id':case_id,'mode':mode,'scope':scope,'run_id':run_id,
      'bin_sha256':c['bin']['sha256'],'elf_sha256':c['elf']['sha256'],'manifest_sha256':c['manifest']['sha256'],'reference_sha256':CONTRACT['normal_reference']['sha256'],
      'raw_sha256':hashlib.sha256(text.encode()).hexdigest(),'observer_status':a['status'],'counts':a['counts'],'coverage':coverage,'fu_counts':a['vfex4_fu_counts'],
      'commits':len(arch),'checked_register_bytes':c['checked_register_bytes'],'csr_contract':c['csr_contract'],
      'accepted_source_arithmetic_full128_count':a['counts']['ACCEPT'],'workload':work['workload'],
      'functional_replay':{k:digest(material[k]) for k in REPLAY_KEYS},'cross_hardware_architecture':digest(arch),
      'samples':{'status':'NOT_APPLICABLE_FUNCTIONAL_IMAGE','event_count':0},'counter_events':{'status':'NOT_APPLICABLE_FUNCTIONAL_IMAGE','event_count':0},
      'guest_cycles':int(guest[0]),'performance_measured':False,'performance_2_percent_qualified':False,
      'target_run_qualified':False,'requires_runtime_receipt':True,
      'numeric_scope':'Observer recomputes accepted-source dot full128; complete registers/CSR rely on frozen target self-check plus mandatory live DiffTest, not printed numeric dumps.'}

def negative(text,case_id,mode,reference,exit_code,run_id,scope='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT'):
    need(scope in SCOPES and isinstance(run_id,str) and bool(run_id),'explicit scope/run id')
    c=descriptor(case_id);plain,obs,a,events,uart=decode_observer(text,mode,False)
    image_gate(plain,c,reference,True);fault=runtime_gate.validate_negative(plain,exit_code);want=c['bit100']
    need([int(fault['pc'],0),int(fault['word'],0),fault['vd'],fault['bit']]==[want[k] for k in ('pc','word','vd','bit')],'case-bound bit100 fault identity')
    arch=bind_architecture(events,c)
    need(arch[0]['pc']==want['pc'],'first actual custom fault')
    need(not re.search(r'T12_SUMMARY|O2_DIAG_SUMMARY|O2_CONTROL_SUMMARY',uart),'negative must stop before successful completion')
    return {'status':'B3_BIT100_LOG_PASS','case_id':case_id,'mode':mode,'run_id':run_id,'scope':scope,'fault':fault,'reference_sha256':c['negative_reference']['sha256'],'raw_sha256':hashlib.sha256(text.encode()).hexdigest(),'target_run_qualified':False,'requires_runtime_receipt':True}

def compare(candidate,baseline,replay_candidate,replay_baseline):
    rows=[candidate,baseline,replay_candidate,replay_baseline]
    need([r.get('mode') for r in rows]==['candidate','baseline','candidate','baseline'],'normal role order')
    need(all(r.get('status')=='B3_FUNCTIONAL_LOG_PASS' for r in rows),'four complete log results')
    need(len({r.get('run_id') for r in rows})==4 and all(r.get('run_id') for r in rows),'four distinct role receipts')
    for key in ('case_id','bin_sha256','elf_sha256','manifest_sha256','reference_sha256'):
        need(all(r.get(key) for r in rows) and len({r[key] for r in rows})==1,'same frozen identity '+key)
    for r in rows:
        need(set(r.get('functional_replay',{}))==set(REPLAY_KEYS),'exact eight functional replay keys')
        need(all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in r['functional_replay'].values()),'nonempty functional replay digests')
        for key in ('samples','counter_events'):need(r.get(key)=={'status':'NOT_APPLICABLE_FUNCTIONAL_IMAGE','event_count':0},'typed inapplicable evidence '+key)
    for a,b in [(candidate,replay_candidate),(baseline,replay_baseline)]:
        need(a['scope']==b['scope'],'replay scope cannot change')
        for key in REPLAY_KEYS:need(a['functional_replay'][key]==b['functional_replay'][key],'exact functional replay '+key)
    for a,b in [(candidate,baseline),(replay_candidate,replay_baseline)]:
        need(a.get('cross_hardware_architecture') and a['cross_hardware_architecture']==b['cross_hardware_architecture'],'cross-hardware architectural/source/full128 equality')
        for key in ('uart_checks','csr_contract'):need(a['functional_replay'][key]==b['functional_replay'][key],'cross-hardware workload checks '+key)
    return {'status':'B3_FUNCTIONAL_COMPARISON_LOG_PASS','case_id':candidate['case_id'],'functional_replay_keys':list(REPLAY_KEYS),'performance_measured':False,'performance_2_percent_qualified':False,'target_run_qualified':False,'requires_four_distinct_verified_runtime_receipts':True}
