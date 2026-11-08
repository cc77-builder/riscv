"""Frozen strict B3 group algorithms; only explicit R2 raw-dst fix and new guard interface. No target launch."""
import re
import runtime_gate
from common import need

GROUP_HEADER='============== Commit Group Trace (Core 0) =============='

INSTR_HEADER='============== Commit Instr Trace =============='

REGS_HEADER='==============  REF Regs  =============='

GROUP_ROW=re.compile(r'^commit group \[(\d{2})\]: pc ([0-9a-fA-F]{1,16}) cmtcnt (\d+)( <--)?$')

INSTR_ROW=re.compile(r'^\[(\d{2})\] commit pc ([0-9a-fA-F]{16}) inst ([0-9a-fA-F]{8}) wen ([01]) dst (\d{2,3}) data ([0-9a-fA-F]{16}) idx ([0-9a-fA-F]{3})(?: \([0-9a-fA-F]{2}\))?( <--)?$')

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
        slot,pc,word,wen,dst,data,rob,arrow=match.groups();need(int(slot)==index and 0<=int(dst)<=255,'instruction ring slots/raw uint8 destination')
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
        need(row['dst']<32,'current group architectural destination')
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
    gate=runtime_gate
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
