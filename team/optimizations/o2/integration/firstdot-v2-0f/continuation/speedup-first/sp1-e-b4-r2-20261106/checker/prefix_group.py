"""Exact frozen o2-control prefix extension; no general disassembler and no target execution."""
import re
from types import FunctionType
# Diagnostic raw dest is uint8_t, printed with minimum width two; current semantics stay below.
INSTR_ROW = re.compile(r'^\[(\d{2})\] commit pc ([0-9a-fA-F]{16}) inst ([0-9a-fA-F]{8}) wen ([01]) dst (\d{2,3}) data ([0-9a-fA-F]{16}) idx ([0-9a-fA-F]{3})(?: \([0-9a-fA-F]{2}\))?( <--)?$')
PREFIX = {
    0x800002e4: {"word": 0xc1027057, "vd": None, "vtype": 16, "vl": 4},
    0x800002e8: {"word": 0x5e00de57, "vd": 28},
    0x800002ec: {"word": 0xc0047057, "vd": None, "vtype": 0, "vl": 8},
    0x800002fc: {"word": 0x8284a9d7, "vd": 19},
}

def validate_prefix_context(selected, ring, elf_read):
    evidence = []
    extra_words = {p["word"] for pc, p in PREFIX.items() if pc != 0x800002ec}
    def exact(row, pc):
        expected = int.from_bytes(elf_read(pc, 4), "little")
        need(row["pc"] == pc and row["word"] == expected, "o2-control prefix contiguous retired PC/word context")
        if pc in PREFIX:
            need(expected == PREFIX[pc]["word"], "frozen prefix opcode changed")
    for row in selected:
        if row["word"] in extra_words or row["pc"] in PREFIX:
            need(row["pc"] in PREFIX and row["word"] == PREFIX[row["pc"]]["word"], "exact prefix PC/opcode footprint")
            desc = PREFIX[row["pc"]]
            if desc["vd"] is not None:
                need(row["dst"] == desc["vd"] == ((row["word"] >> 7) & 31), "prefix encoded vector destination mismatch")
            slot = row["slot"]
            context = []
            if row["pc"] == 0x800002e8:
                previous = ring[(slot - 1) % 32]; exact(previous, 0x800002e4)
                context = [previous, row]
                evidence.append({"writer_pc": row["pc"], "vd": 28, "sew": 32, "lmul": 1, "vl": 4, "configuration_scope": "immediately preceding actual retired ring instruction", "context": context})
            elif row["pc"] == 0x800002fc:
                pcs = [0x800002ec, 0x800002f0, 0x800002f4, 0x800002f8]
                context = [ring[(slot - 4 + i) % 32] for i in range(4)]
                for prior, pc in zip(context, pcs): exact(prior, pc)
                evidence.append({"writer_pc": row["pc"], "vd": 19, "sew": 8, "lmul": 1, "vl": 8, "configuration_scope": "exact adjacent retired e8 config then three scalar loads", "context": context + [row]})
            elif row["pc"] == 0x800002e4:
                exact(ring[(slot + 1) % 32], 0x800002e8)
                exact(ring[(slot + 2) % 32], 0x800002ec)
    return evidence

def vector_destination(word):
    for pc, desc in PREFIX.items():
        if word == desc["word"]:
            return desc["vd"]
    return strict_vector_destination(word)

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
        need(not any((row['word']&0x7f)==0x57 and row['word']!=0xc0047057 and not (row['pc'] in PREFIX and row['word']==PREFIX[row['pc']]['word']) for row in selected[:config_positions[0]]),'vector arithmetic before in-group configuration has ambiguous LMUL footprint')
    prefix_context = validate_prefix_context(selected, instructions, elf_read)
    return {'group_ring_slot':group['slot'],'group_head_pc':group['pc'],'cmtcnt':count,'instruction_ring_tail':end,'instructions':selected,'prefix_context':prefix_context}

def configure(strict):
    # Clone only globals of the immutable validator; the original module/whitelist is untouched.
    for name in ("need", "GROUP_HEADER", "INSTR_HEADER", "REGS_HEADER", "GROUP_ROW"):
        globals()[name] = getattr(strict, name)
    globals()["strict_vector_destination"] = strict.vector_destination
    context = dict(strict.validate_negative_group.__globals__)
    context.update(current_group=current_group, vector_destination=vector_destination)
    return FunctionType(strict.validate_negative_group.__code__, context, "validate_o2_control_negative_group", strict.validate_negative_group.__defaults__)
