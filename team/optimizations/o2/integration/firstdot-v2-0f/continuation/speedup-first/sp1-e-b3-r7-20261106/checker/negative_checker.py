"""Pure-host negative adaptation. Normal collect/compare remain in frozen old collector."""
from pathlib import Path
import hashlib,importlib.util,json,re
HERE=Path(__file__).resolve().parent
CONTRACT_PATH=HERE/'CHECKER_CONTRACT.json'
CONTRACT_SHA='4a4946d3b401cc4ab52470948b719cfeb2a690951977ac16d3a42d393b7c5161'
OLD_COLLECTOR_PIN={'path': '/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-protection-host-20261105/collector/collector.py', 'bytes': 11795, 'sha256': 'a2e35990c4b6253263c61f08ae9f9c681d05dddf72989df07af70f198e9e2384'}
OLD_CONTRACT_PIN={'path': '/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-protection-host-20261105/collector/CONTRACT.json', 'bytes': 21888, 'sha256': '1f24a6b584434b1403ec6fa22dd95b93229baa743c26e7c9990ef71e580dde70'}
CASE_IDS=('legacy-control','o2-all-pairs')

def need(ok,message):
    if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def check_pin(pin):
    path=Path(pin['path'])
    need(path.is_absolute() and path.resolve()==path and path.is_file(),'canonical input path')
    need(path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256'],'frozen checker input changed '+str(path))
need(sha(CONTRACT_PATH)==CONTRACT_SHA,'checker contract changed')
CONTRACT=json.loads(CONTRACT_PATH.read_text())
need(CONTRACT['case_ids']==list(CASE_IDS),'exact checker case whitelist')
need(CONTRACT['old_collector']==OLD_COLLECTOR_PIN and CONTRACT['old_contract']==OLD_CONTRACT_PIN,'historical collector identity')
for dependency in CONTRACT['dependency_pins']:check_pin(dependency)
check_pin(OLD_COLLECTOR_PIN);check_pin(OLD_CONTRACT_PIN)
spec=importlib.util.spec_from_file_location('b3_r2_frozen_original_collector',OLD_COLLECTOR_PIN['path'])
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
GROUP_HEADER='============== Commit Group Trace (Core 0) =============='
INSTR_HEADER='============== Commit Instr Trace =============='
REGS_HEADER='==============  REF Regs  =============='
GROUP_ROW=re.compile(r'^commit group \[(\d{2})\]: pc ([0-9a-fA-F]{1,16}) cmtcnt (\d+)( <--)?$')
INSTR_ROW=re.compile(r'^\[(\d{2})\] commit pc ([0-9a-fA-F]{16}) inst ([0-9a-fA-F]{8}) wen ([01]) dst (\d{2}) data ([0-9a-fA-F]{16}) idx ([0-9a-fA-F]{3})(?: \([0-9a-fA-F]{2}\))?( <--)?$')

def vector_destination(word):
    """Closed supported group subset. Unknown vector register footprints fail closed."""
    opcode=word&0x7f
    if opcode==0x0b:
        need(word&0xfe00707f==0x0200000b,'unknown custom vector instruction in current group')
        return (word>>7)&31
    need(opcode not in (0x2b,0x5b,0x7b),'unsupported custom register footprint in current group')
    if opcode==0x57:
        if word==0xc0047057:return None  # exact vsetivli zero,8,e8,m1; REF config is checked.
        need((word>>12)&7!=7,'vector configuration changes inside diagnostic group are unsupported')
        need((word>>26)==0 and ((word>>12)&7)==0,'unsupported vector arithmetic footprint in current group')
        return (word>>7)&31  # vadd.vv under checked e8,m1 has one vector destination.
    if opcode==0x07 and ((word>>12)&7) in (0,5,6,7):
        known=((word>>29)==0 and ((word>>28)&1)==0 and ((word>>26)&3)==0 and ((word>>25)&1)==1 and ((word>>12)&7)==0 and ((word>>20)&31)==8)
        need(known,'unsupported vector load/segment register footprint in current group')
        return (word>>7)&31  # vl1re8.v: exactly one whole vector register, independent of vtype.

    return None

def bind_current_custom(group,events,trigger):
    """Rebuild accepted-source math and full response for each current custom commit."""
    allocations={};accepts={};responses={};committed=[]
    for _,_,kind,f in events:
        if kind=='ENQUEUE':allocations[f['rob']]=dict(f)
        elif kind=='ACCEPT':
            need(f['rob'] in allocations,'accepted custom requires allocation')
            accepts[f['seq']]=dict(f,allocation=dict(allocations[f['rob']]))
            allocations[f['rob']]['seq']=f['seq']
        elif kind=='RESPONSE':responses[f['seq']]=dict(f)
        elif kind=='COMMIT':
            enq=allocations.get(f['rob']);need(enq is not None and enq.get('seq') in accepts,'custom commit lacks allocated accepted identity')
            accept=accepts[enq['seq']];out=responses.get(enq['seq'])
            need(out is not None and enq['pc']==f['pc'] and enq['cycle']<=accept['cycle']<=out['cycle']<=f['cycle'],'custom PC/accept/response/retirement order')
            need(accept['rob']==out['rob']==f['rob'] and accept['pdest']==out['pdest'],'custom response ROB/destination binding')
            need(accept['vl']==8 and accept['illegal']==0 and out['exception']==0,'legal e8 custom complete result')
            def signed_byte(source,lane):
                value=(source>>(8*lane))&255
                return value-256 if value>=128 else value
            expected=sum(signed_byte(accept['vs1'],i)*signed_byte(accept['vs2'],i) for i in range(8))&0xffffffff
            need(out['data']==expected,'independent accepted-source full128 arithmetic mismatch')
            committed.append({'pc':f['pc'],'word':enq['word'],'rob':f['rob'],'rob_index':int(f['rob'].split(':')[1]),'cycle':f['cycle'],'seq':accept['seq'],'vs1':accept['vs1'],'vs2':accept['vs2'],'result':out['data'],'response_cycle':out['cycle']})
    triggered=[x for x in committed if x['pc']==trigger['pc'] and x['word']==trigger['word'] and x['rob_index']==trigger['rob_index']]
    need(len(triggered)==1,'unique observer-bound trigger commit')
    current=[x for x in committed if x['cycle']==triggered[0]['cycle']]
    rows=[x for x in group['instructions'] if x['word']&0xfe00707f==0x0200000b]
    need([(x['pc'],x['word'],x['rob_index']) for x in rows]==[(x['pc'],x['word'],x['rob_index']) for x in current],'current group custom sequence equals exact observer retirement group')
    for row,bound in zip(rows,current):
        need(row['dst']==(row['word']>>7)&31,'custom trace destination differs from encoded vd')
        need(row['data']==bound['result']&((1<<64)-1),'diagnostic low64 differs from observer full128 result')
    return triggered[0],current

def current_group(plain,elf_read):
    need(plain.count(GROUP_HEADER)==plain.count(INSTR_HEADER)==plain.count(REGS_HEADER)==1,'one complete diagnostic ring dump')
    need(len(re.findall(r'Commit Group Trace',plain))==len(re.findall(r'Commit Instr Trace',plain))==1,'no duplicate or foreign diagnostic dump')
    first=plain.index(GROUP_HEADER);middle=plain.index(INSTR_HEADER);last=plain.index(REGS_HEADER)
    need(first<middle<last,'ordered diagnostic sections')
    g_lines=[x for x in plain[first+len(GROUP_HEADER):middle].splitlines() if x.strip()]
    i_lines=[x for x in plain[middle+len(INSTR_HEADER):last].splitlines() if x.strip()]
    need(len(g_lines)==16 and len(i_lines)==32,'complete initialized 16/32 diagnostic rings required')
    groups=[];instructions=[]
    for index,line in enumerate(g_lines):
        match=GROUP_ROW.fullmatch(line);need(match is not None,'malformed commit group row')
        slot,pc,count,arrow=match.groups();need(int(slot)==index,'group ring slots unique and ordered')
        groups.append({'slot':index,'pc':int(pc,16),'count':int(count),'tail':bool(arrow)})
    for index,line in enumerate(i_lines):
        match=INSTR_ROW.fullmatch(line);need(match is not None,'malformed or ambiguous instruction ring row')
        slot,pc,word,wen,dst,data,rob,arrow=match.groups();need(int(slot)==index and int(dst)<32,'instruction ring slots/destination')
        instructions.append({'slot':index,'pc':int(pc,16),'word':int(word,16),'wen':int(wen),'dst':int(dst),'data':int(data,16),'rob_index':int(rob,16),'tail':bool(arrow)})
    tails=[x for x in groups if x['tail']];ends=[x for x in instructions if x['tail']]
    need(len(tails)==len(ends)==1,'exact one current group and instruction tail')
    group=tails[0];end=ends[0]['slot'];count=group['count']
    need(1<=count<=32,'current group cmtcnt must fit instruction ring')
    selected=[instructions[(end-count+1+i)%32] for i in range(count)]
    need(selected[0]['pc']==group['pc'],'cmtcnt/ring tail does not yield declared group head')
    dut=re.findall(r'^the first commit instr pc of DUT is (0x[0-9a-fA-F]+)$',plain,re.M)
    ref=re.findall(r'^the first commit instr pc of REF is (0x[0-9a-fA-F]+)$',plain,re.M)
    need(len(dut)==len(ref)==1 and int(dut[0],16)==int(ref[0],16)==group['pc'],'DUT/REF diagnostic group head agreement')
    need(len({x['rob_index'] for x in selected})==len(selected),'ambiguous reused ROB index within current group')
    for row in selected:
        need(row['pc']%2==0,'unaligned committed PC')
        size=4 if row['word']&3==3 else 2
        need(int.from_bytes(elf_read(row['pc'],size),'little')==row['word'],'current group instruction differs from frozen ELF')
    vtype=re.findall(r'^[ \t]*vtype: (0x[0-9a-fA-F]+) vstart: (0x[0-9a-fA-F]+)[ \t]+vxsat: (0x[0-9a-fA-F]+)$',plain,re.M)
    vl=re.findall(r'^[ \t]*vxrm: (0x[0-9a-fA-F]+)[ \t]+vl: (0x[0-9a-fA-F]+)[ \t]+vcsr: (0x[0-9a-fA-F]+)$',plain,re.M)
    need(len(vtype)==len(vl)==1 and int(vtype[0][0],16)==0 and int(vtype[0][1],16)==0 and int(vl[0][1],16)==8,'single e8,m1 VL8 architectural group context')
    config_positions=[i for i,row in enumerate(selected) if row['word']==0xc0047057]
    if config_positions:
        need(not any((row['word']&0x7f)==0x57 and row['word']!=0xc0047057 for row in selected[:config_positions[0]]),'vector arithmetic before in-group configuration has ambiguous LMUL footprint')
    return {'group_ring_slot':group['slot'],'group_head_pc':group['pc'],'cmtcnt':count,'instruction_ring_tail':end,'instructions':selected}

def validate_negative_group(text,exit_code,want,elf_read,events):
    gate=legacy.runtime_gate
    need(type(exit_code) is int and exit_code==1,'negative run must exit exactly 1')
    plain=gate.normalize_console(text)
    need(gate.COMMON_FAILURES.search(plain) is None,'unrelated runtime failure marker')
    need('HIT GOOD TRAP' not in plain.upper(),'negative run unexpectedly reached GOOD TRAP')
    injected=list(gate.INJECTION.finditer(plain))
    need(len(injected)==1 and len(re.findall('DIFFTEST_HIGHBIT_NEGATIVE_INJECTED',plain,re.I))==1,'exactly one complete bit100 injection')
    vd_text,pc_text,word_text=injected[0].groups();vd,pc,word=int(vd_text),int(pc_text,16),int(word_text,16)
    need(0<=vd<32 and pc<1<<64 and word<1<<32 and word&0xfe00707f==0x0200000b and (word>>7)&31==vd,'valid encoded injection identity')
    need([pc,word,vd,100]==[want[k] for k in ('pc','word','vd','bit')],'frozen case injection PC/word/vd/bit')
    mismatches=list(gate.MISMATCH.finditer(plain))
    need(len(mismatches)==1 and len(re.findall('different at pc',plain,re.I))==1,'exactly one complete vector high-half mismatch')
    diff_vd,diff_pc,right_text,wrong_text=mismatches[0].groups();right,wrong=int(right_text,16),int(wrong_text,16)
    need(int(diff_vd)==vd,'mismatch register equals injection destination')
    need(right<1<<64 and wrong<1<<64 and right^wrong==1<<36,'exact sole vector bit100 XOR')
    aborted=list(gate.ABORT.finditer(plain))
    need(len(aborted)==1 and len(re.findall('ABORT',plain,re.I))==1,'exactly one canonical Core 0 ABORT')
    abort_pc=int(aborted[0][1],16);need(abort_pc<1<<64,'ABORT event PC range')
    need(mismatches[0].end()<aborted[0].start() and not plain[mismatches[0].end():aborted[0].start()].strip(),'terminal ABORT immediately follows mismatch')
    group=current_group(plain,elf_read)
    need(int(diff_pc,16)==group['group_head_pc'],'mismatch PC must be current commit group head')
    matches=[x for x in group['instructions'] if x['pc']==pc and x['word']==word]
    need(len(matches)==1,'frozen injection occurs exactly once in current group; no historical fallback')
    selected=matches[0]
    writers=[x for x in group['instructions'] if vector_destination(x['word'])==vd]
    need(writers and selected in writers,'trigger is an encoded vd writer in current group')
    final=writers[-1]
    need(final['word']&0xfe00707f==0x0200000b,'last vd writer must be supported fully observed custom')
    trigger_bound,current=bind_current_custom(group,events,selected)
    final_matches=[x for x in current if (x['pc'],x['word'],x['rob_index'])==(final['pc'],final['word'],final['rob_index'])]
    need(len(final_matches)==1,'unique observer-bound final vd writer')
    final_bound=final_matches[0]
    register_dump=plain[plain.index(REGS_HEADER):mismatches[0].start()]
    dumped=re.findall(r'\bv'+str(vd)+r'\s*:\s*0x([0-9a-fA-F]{16})_([0-9a-fA-F]{16})(?=\s|$)',register_dump)
    need(len(dumped)==1,'exact one final reference vector register dump')
    ref_full=(int(dumped[0][0],16)<<64)|int(dumped[0][1],16)
    need(ref_full==final_bound['result'],'reference full128 register dump differs from current final vd writer')
    expected_high=final_bound['result']>>64
    need(wrong==expected_high and right==expected_high^(1<<36),'bit100 XOR must apply to current final vd writer full128 result')
    return {'vd':vd,'pc':hex(pc),'word':f'0x{word:08x}','bit':100,'abort_event_pc':hex(abort_pc),'abort_count':1,'mismatch_pc':hex(int(diff_pc,16)),'right_high':hex(right),'wrong_high':hex(wrong),'fault_pc_binding':'unique frozen trigger in exact current cmtcnt/ring-tail group; mismatch equals group head','abort_pc_scope':'XSTrap event field, not required to equal injection/group head','current_group':group,'trigger_commit':trigger_bound,'ordered_vd_writers':writers,'final_vd_writer':final_bound,'group_custom_full128':current,'injection_semantics':'pending trigger; XOR copied architectural state at group-end regcpy; original NEMU state unchanged'}

def negative(text,case_id,mode,reference,exit_code,run_id,scope='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT'):
    need(case_id in CASE_IDS,'only two eligible B3 cases; o2-control HOLD')
    need(mode=='candidate','negative role uses candidate hardware')
    need(scope in legacy.SCOPES and isinstance(run_id,str) and bool(run_id),'explicit scope/run id')
    c=legacy.descriptor(case_id)
    plain,obs,a,events,uart=legacy.decode_observer(text,mode,False)
    legacy.image_gate(plain,c,reference,True)
    _,elf_read=legacy.legacy_windows.elf_data(c['elf']['path'])
    fault=validate_negative_group(plain,exit_code,c['bit100'],elf_read,events)
    arch=legacy.bind_architecture(events,c)
    need(arch[0]['pc']==c['bit100']['pc'],'first actual custom fault')
    need(not re.search(r'T12_SUMMARY|O2_DIAG_SUMMARY|O2_CONTROL_SUMMARY',uart),'negative must stop before successful completion')
    return {'status':'B3_BIT100_LOG_PASS','case_id':case_id,'mode':mode,'run_id':run_id,'scope':scope,'fault':fault,'reference_sha256':c['negative_reference']['sha256'],'raw_sha256':hashlib.sha256(text.encode()).hexdigest(),'target_run_qualified':False,'requires_runtime_receipt':True,'checker_contract_sha256':CONTRACT_SHA,'qualification':'strict offline log gate; actual process/resource receipts remain mandatory; exact trigger and final-vd-writer full128 provenance required'}
