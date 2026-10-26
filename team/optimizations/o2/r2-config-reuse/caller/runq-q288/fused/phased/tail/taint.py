"""Conservative byte dependency proof: every agnostic tail may be arbitrary."""
from collections import Counter
import hashlib,struct

OLD_BODY_SHA='78893b4754e0e1f5b0d2599d29e9ad50ff675cae088797ea7207eedfd5b78d9b'
NEW_CONFIG=0xc4047057
OFFSETS=(60,336)

def need(ok,message):
    if not ok:raise ValueError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def exact_delta(original,candidate):
    need(sha(original)==OLD_BODY_SHA and len(original)==len(candidate)==764,'fixed original phased function')
    expected=bytearray(original)
    for offset in OFFSETS:
        need(struct.unpack_from('<I',original,offset)[0]==0xc0047057,'original core phase word')
        struct.pack_into('<I',expected,offset,NEW_CONFIG)
    need(bytes(expected)==candidate,'exactly two vta bits; no other function change')
    return dict(changed_function_offsets=list(OFFSETS),old_word='0xc0047057',new_word=hex(NEW_CONFIG),
                original_sha256=sha(original),candidate_sha256=sha(candidate))

def prove(candidate):
    """One group from arbitrary scratch registers, with a defined FP accumulator.

    True denotes any dependence on unknown entry state or an arbitrary agnostic
    tail byte. Full-register dot writes remove all such dependencies. Proving
    the loop from arbitrary scratch state is inductive across all 324 groups.
    The unchanged scalar/control/prefix bytes are bound by exact_delta separately.
    """
    need(len(candidate)==764,'bounded full function')
    words=list(struct.unpack('<191I',candidate));v=[[True]*16 for _ in range(32)]
    v[8]=[False]*16;v[9]=[False]*16;mode=None;counts=Counter();read_checks=0;writes=[]
    def get(reg,size):
        need(reg+size//16<=32,'vector source range');return sum(v[reg:reg+(size+15)//16],[])[:size]
    def defined(reg,size,why):
        nonlocal read_checks
        need(not any(get(reg,size)),why);read_checks+=1
    def put(reg,values,at):
        need(len(values)%16==0 and reg+len(values)//16<=32,'vector destination range')
        if 15<=at<146:need(not set(range(reg,reg+len(values)//16))&{8,9},'integer core preserves FP accumulator')
        for i in range(len(values)//16):v[reg+i]=values[16*i:16*i+16]
        writes.append((at,reg,len(values)))
    for at,w in enumerate(words[15:],15):
        op=w&127;f3=(w>>12)&7;f6=w>>26;rd,a,b=(w>>7)&31,(w>>15)&31,(w>>20)&31
        if w in (NEW_CONFIG,0xc1027057,0xc1147057,0xc0047057):
            mode={NEW_CONFIG:(8,8,1,1),0xc1027057:(4,32,1,0),0xc1147057:(8,32,2,0),0xc0047057:(8,8,1,0)}[w]
            counts['vsetivli']+=1
        elif w&0xfff0707f==0x02000007:
            need(mode==(8,8,1,1),'all integer loads use exactly ta e8 vl8')
            put(rd,[False]*8+[True]*8,at);counts['agnostic_loads']+=1
        elif w&0xfe00707f==0x0200000b:
            need(mode==(8,8,1,1),'dot mode accepts vta')
            defined(a,8,'dot source low bytes may not depend on tail')
            defined(b,8,'dot source low bytes may not depend on tail')
            put(rd,[False]*16,at);counts['full_register_dot_writes']+=1
        elif op==0x57 and (w>>25)&1 and (f6,f3)==(0,0):
            need(mode==(4,32,1,0),'full e32 integer add')
            defined(a,16,'integer add source may not depend on tail');defined(b,16,'integer add source may not depend on tail')
            put(rd,[False]*16,at);counts['integer_adds']+=1
        elif op==0x57 and (w>>25)&1 and (f6,f3)==(0x17,0) and b==0:
            need(mode==(4,32,1,0),'full gather move')
            defined(a,16,'FP gather move may not read tail');put(rd,get(a,16),at);counts['gather_moves']+=1
        elif op==0x57 and (w>>25)&1 and (f6,f3)==(0x0e,3):
            need(mode==(4,32,1,0) and 0<a<4 and rd!=b,'bounded gather slide')
            before=get(rd,16);source=get(b,16);combined=before[:4*a]+source[:16-4*a]
            need(not any(combined),'FP gather slide may not read tail');put(rd,combined,at);counts['gather_slides']+=1
        elif op==7 and f3==6 and (w>>25)&1 and (w>>26)&3==2 and w>>28==0:
            need(mode==(8,32,2,0) and rd%2==0,'full FP scale load')
            put(rd,[False]*32,at);counts['scale_loads']+=1
        elif op==0x57 and (w>>25)&1 and (f6,f3)==(0x12,1):
            need(mode==(8,32,2,0) and a==3,'full signed FP conversion')
            defined(b,32,'FP conversion may not read tail');put(rd,[False]*32,at);counts['FP_convert']+=1
        elif op==0x57 and (w>>25)&1 and (f6,f3) in ((0x24,1),(0x24,5),(0,1)):
            need(mode==(8,32,2,0),'full FP arithmetic')
            defined(b,32,'FP arithmetic may not read tail')
            if f3==1:defined(a,32,'FP arithmetic second vector may not read tail')
            put(rd,[False]*32,at);counts['FP_arithmetic']+=1
        elif op==0x27 and f3==6 and w>>20==0x20:
            need(mode==(8,32,2,0),'full output store');defined(rd,32,'stored output may not depend on tail');counts['output_stores']+=1
        elif op==0x27 and w&0xfff0707f==0x02800027:
            need(mode==(8,8,1,0),'final tu restoration');defined(rd,16,'complete 128-bit slot may not depend on tail');counts['slot_stores']+=1
        elif (op==0x13 and f3==0) or (op==0x63 and f3==1) or (op==7 and f3==2) or w==0x00008067:
            # Integer addresses/branches and scalar FP input cannot expose a vector tail.
            pass
        else:raise ValueError('unclassified tail-flow instruction '+hex(w))
        if at==145:
            need(all(not any(v[r]) for r in range(8)),'all integer outputs defined in full width')
    need(mode==(8,8,1,0),'exact final vector configuration')
    need(counts==Counter(vsetivli=6,agnostic_loads=36,full_register_dot_writes=32,integer_adds=24,
                        gather_moves=2,gather_slides=6,scale_loads=1,FP_convert=1,FP_arithmetic=3,output_stores=1,slot_stores=8),
         'complete exact vector flow inventory')
    return dict(status='TAIL_ARBITRARY_BYTE_NONINTERFERENCE_PASS',counts=dict(counts),source_checks=read_checks,
        scratch_entry_state='arbitrary',agnostic_tail_model='every tail byte arbitrary; strict superset of legal retain/all-ones choices',
        all_dot_low64_defined=True,all_integer_slots_full128_defined=True,FP_outputs_defined=True,
        group_induction='any scratch entry, defined v8/v9 -> defined v8/v9; repeated groups and tile zeroing preserve property',
        final_vta=0,new_emu_runs=0)

def controls(original,candidate):
    results=[]
    def rejected(name,raw,check):
        need(raw!=candidate,'nonempty flow mutant')
        try:check(bytes(raw))
        except ValueError as error:results.append(dict(name=name,error=str(error),sha256=sha(raw)))
        else:raise ValueError('tail-flow mutant accepted: '+name)
    # Feed a partially defined load register into a full-width add.
    w=list(struct.unpack('<191I',candidate));i=next(i for i,x in enumerate(w[15:146],15) if x&127==0x57 and x>>26==0 and (x>>12)&7==0)
    raw=bytearray(candidate);struct.pack_into('<I',raw,4*i,(w[i]&~(31<<15))|(20<<15));rejected('load-tail-used-as-active-add',raw,prove)
    i=146;need((w[i]>>26,(w[i]>>12)&7)==(0x17,0),'first gather move')
    raw=bytearray(candidate);struct.pack_into('<I',raw,4*i,(w[i]&~(31<<15))|(20<<15));rejected('gather-reads-load-tail',raw,prove)
    i=next(i for i in range(146,len(w)) if w[i]==0xc0047057)
    raw=bytearray(candidate);struct.pack_into('<I',raw,4*i,NEW_CONFIG);rejected('final-restoration-is-ta',raw,prove)
    raw=bytearray(candidate);raw[100]^=1;rejected('unrelated-machine-byte-change',raw,lambda r:exact_delta(original,r))
    return dict(status='TAIL_FLOW_CONTROLS_PASS',controls=results,new_emu_runs=0)
