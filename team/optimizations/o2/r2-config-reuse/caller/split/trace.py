"""Bounded scalar control-flow execution for this caller's actual RV64 ELF.

This is a path checker, not a replacement arithmetic model or an ISA emulator.
Derived from the frozen caller/pathcheck.py. New complete machine-word
certificates qualify arithmetic; this checker independently tracks actual
VL/EEW, both address spaces, no-copy footprint, and generic timer calls.
Arithmetic results require independent C oracles and live DiffTest. Values written by vector stores
are deliberately unknown here; an unknown value may never select a branch.
"""
from collections import Counter
import struct

START, STOP = 0x51300013, 0x51400013
COUNTERS = (0xc0202773, 0xc0002873, 0xc00028f3, 0xc02027f3)
MASK = (1 << 64) - 1

def need(ok, message):
    if not ok:
        raise ValueError(message)

def signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value

def path(elf, row, packed, offsets=(96,32)):
    mode, method = row["mode"], row["method"]
    timer, leaf, wrapper = "split_measure", row["leaf"], row["wrapper"]
    allowed = (timer, wrapper, leaf)
    words, owners = {}, {}
    for name in allowed:
        start, size = elf.symbols[name][:2]
        raw = elf.symbol_data(name)
        need(start % 4 == size % 4 == 0 and len(raw) == size, "caller non-RV32 encoding alignment")
        for i, (word,) in enumerate(struct.iter_unpack("<I", raw)):
            need(word & 3 == 3, "compressed caller instruction")
            words[start + i * 4], owners[start + i * 4] = word, name
    begin = [pc for pc, word in words.items() if word == START]
    stop = [pc for pc, word in words.items() if word == STOP]
    need(len(begin) == len(stop) == 1 and begin[0] < stop[0], "unique caller markers")
    addr = lambda n: elf.symbols[n][0]
    a, b, y = addr("split_arena") + offsets[0], addr("split_arena") + offsets[1], addr("caller_y") + 16
    work, ctx, metrics = addr("caller_workspace"), addr("split_context" if mode=="split" else "caller_context"), addr("caller_measurement")
    inputs, output, slots = work + 16, y, work + 320
    memory, accesses = {}, []
    def seed(address, raw):
        for i, value in enumerate(raw): memory[address + i] = value
    seed(a, packed[:256]); seed(b, packed[256:])
    seed(ctx, struct.pack("<5Q", a, b, y, slots if mode=="split" else work, addr(leaf)))
    seed(work, bytes([0xa6]) * 464)
    seed(y, bytes([0xa6]) * 32)
    stack_top = 0x87fff000
    initial_sp = stack_top - 48
    registers = [None] * 32
    registers[0], registers[2] = 0, initial_sp
    registers[8], registers[9] = ctx, metrics
    registers[10], registers[11], registers[20] = ctx, metrics, addr(wrapper)
    def known(value, why):
        need(value is not None, "unknown scalar value controls " + why)
        return value
    def read(address, n, signed_load=False):
        known(address, "memory address")
        need(mode!="split" or address+n<=inputs or address>=inputs+288,
             "split scalar load intersects old packed input")
        need(all(address+i in memory for i in range(n)), "load outside initialized caller memory")
        accesses.append(("load", address, n))
        raw = [memory[address+i] for i in range(n)]
        if None in raw: return None
        value = int.from_bytes(bytes(raw), "little")
        return (signed(value, n*8) if signed_load else value) & MASK
    def write(address, n, value):
        known(address, "store address")
        need((initial_sp-4096 <= address and address+n <= stack_top) or
             (mode=="packed" and inputs <= address and address+n <= inputs+288) or
             (slots <= address and address+n <= slots+128) or
             (y <= address and address+n <= y+32), "caller store outside permitted buffers")
        accesses.append(("store", address, n))
        for i in range(n): memory[address+i] = None if value is None else (value >> (i*8)) & 255
    def binary(left, right, fn):
        return None if left is None or right is None else fn(left, right) & MASK
    result, calls, entered = [], [], Counter()
    branches = 0
    vector_state = None
    pc = begin[0]
    for _ in range(30000):
        need(pc in words, "caller path escaped allowed functions")
        w = words[pc]
        result.append((pc, w))
        if pc == stop[0]: break
        op, rd, rs1, rs2, f3, f7 = w & 127, (w >> 7) & 31, (w >> 15) & 31, (w >> 20) & 31, (w >> 12) & 7, w >> 25
        left, right, immediate = registers[rs1], registers[rs2], signed(w >> 20, 12)
        next_pc, value, sets = pc + 4, None, False
        if w in (START, STOP) or op == 0x0f:
            need(w in (START, STOP, 0x0330000f), "unsupported caller fence")
        elif op in (0x37, 0x17):
            value, sets = (signed(w & 0xfffff000, 32) + (pc if op == 0x17 else 0)) & MASK, True
        elif op in (0x13, 0x1b):
            sets = True
            bits = 32 if op == 0x1b else 64
            if f3 == 0: value = binary(left, immediate, lambda a,b: a+b)
            elif f3 == 1:
                need(w >> (25 if bits == 32 else 26) == 0, "unsupported left shift encoding")
                value = binary(left, (w >> 20) & (bits-1), lambda a,b:a << b)
            elif f3 == 5:
                arithmetic = (w >> 30) & 1
                need(w >> (25 if bits == 32 else 26) in ((0,32) if bits == 32 else (0,16)), "unsupported right shift encoding")
                value = binary(left, (w >> 20) & (bits-1), lambda a,b:(signed(a,bits) if arithmetic else a & ((1<<bits)-1)) >> b)
            elif op == 0x13 and f3 in (2,3,4,6,7):
                fun = {2:lambda a,b:int(signed(a,64)<b), 3:lambda a,b:int(a<(b&MASK)),
                       4:lambda a,b:a^(b&MASK),6:lambda a,b:a|(b&MASK),7:lambda a,b:a&(b&MASK)}[f3]
                value = binary(left, immediate, fun)
            else: raise ValueError("unsupported scalar immediate")
            if bits == 32 and value is not None: value = signed(value,32) & MASK
        elif op in (0x33,0x3b):
            need(f7 in (0,32), "unsupported scalar register instruction")
            bits = 32 if op == 0x3b else 64
            fun = {0:(lambda a,b:a-b) if f7==32 else (lambda a,b:a+b),
                   1:lambda a,b:a << (b&(bits-1)),
                   2:lambda a,b:int(signed(a,bits)<signed(b,bits)),3:lambda a,b:int(a<b),
                   4:lambda a,b:a^b,5:(lambda a,b:signed(a,bits) >> (b&(bits-1))) if f7==32 else (lambda a,b:(a & ((1<<bits)-1)) >> (b&(bits-1))),
                   6:lambda a,b:a|b,7:lambda a,b:a&b}[f3]
            value, sets = binary(left,right,fun), True
            if bits == 32 and value is not None: value = signed(value,32) & MASK
        elif op == 0x03:
            need(f3 in (0,1,2,3,4,5,6), "unsupported scalar load")
            n = 1 << (f3 & 3)
            value, sets = read((known(left,"load base")+immediate)&MASK, n, f3<4), True
        elif op == 0x23:
            need(f3 in (0,1,2,3), "unsupported scalar store")
            imm = signed(((w>>25)<<5)|((w>>7)&31),12)
            write((known(left,"store base")+imm)&MASK,1<<f3,right)
        elif op == 0x63:
            need(f3 in (0,1,4,5,6,7), "unsupported scalar branch")
            left, right = known(left,"branch"), known(right,"branch")
            cond={0:left==right,1:left!=right,4:signed(left,64)<signed(right,64),
                  5:signed(left,64)>=signed(right,64),6:left<right,7:left>=right}[f3]
            imm=((w>>31)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1)
            if cond: next_pc=pc+signed(imm,13)
            branches += 1
        elif op in (0x6f,0x67):
            if op==0x6f:
                imm=((w>>31)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1)
                target=pc+signed(imm,21)
            else:
                need(f3==0,"unsupported jalr")
                target=(known(left,"indirect jump")+immediate)&~1
            if rd == 1:
                need(registers[2]%16==0 and target in (addr(wrapper),addr(leaf)), "invalid call target/stack alignment")
                calls.append(pc+4); entered[owners[target]]+=1
            elif rd == 0:
                if op==0x67 and rs1==1:
                    need(calls and target==calls.pop(),"mismatched caller return")
                elif target==addr(leaf) and False:
                    need(calls and registers[2]%16==0,"invalid leaf tail call")
                    entered[leaf]+=1
                else:
                    need(op==0x6f and target in words and owners[target]==owners[pc],"unapproved caller jump")
            else: raise ValueError("unapproved link register")
            value, sets, next_pc=pc+4,True,target
        elif op == 0x73:
            need(w in COUNTERS or (owners[pc]==leaf and rd==0 and f3==5 and w>>20 in (0x008,0x00f)), "unsupported caller CSR")
            value, sets=None,True
        elif op in (0x07,0x27,0x57,0x0b):
            need(owners[pc]==leaf,"vector/custom operation outside qualified leaf")
            if op==0x07:
                address=known(left,"vector load")
                need(vector_state is not None and f3==0 and w>>26==0 and rs2==0 and (w>>25)&1,
                     "unsupported vector memory encoding/state")
                vl,sew,lmul=vector_state
                need(sew==8 and lmul==1 and vl in (8,16),"load uses actual byte VL")
                regions=((a,256),(b,32)) if mode=="split" else ((inputs,256),(inputs+256,32))
                need(any(start<=address and address+vl<=start+size for start,size in regions),
                     "vector load outside its complete A/x region")
                need(all(address+i in memory and memory[address+i] is not None for i in range(vl)),
                     "vector reads uninitialized input")
                accesses.append(("vload",address,vl))
            elif op==0x27:
                address=known(left,"whole vector store")
                need(f3==0 and w>>26==0 and rs2==8 and (w>>25)&1,"whole-register store encoding")
                need(slots<=address and address+16<=slots+128,"vector store outside complete slots")
                write(address,16,None)
            elif op==0x57 and f3==7:
                need(rd==0 and w>>30==3,"immediate vset x0 required")
                avl=rs1;vt=(w>>20)&1023
                need(vt in (0,9,16),"supported exact vtype")
                sew=8<<((vt>>3)&7);lmul=1<<(vt&7)
                need(0<avl<=128*lmul//sew,"exact immediate VL")
                vector_state=(avl,sew,lmul)
            elif op==0x57 and f3==2 and w>>26==0b010000 and rs1==0 and (w>>25)&1:
                # vmv.x.s returns arithmetic data, never an old address fact.
                value,sets=None,True
        else: raise ValueError(f"unsupported caller opcode {w:08x} at {pc:08x}")
        if sets and rd: registers[rd] = value
        registers[0]=0
        pc=next_pc
    else: raise ValueError("caller path exceeded finite budget")
    need(not calls and registers[2]==initial_sp and registers[8]==ctx and registers[9]==metrics and registers[20]==addr(wrapper),"caller stack/register balance")
    need(vector_state==(8,8,1),"return vector state")
    need(entered[wrapper]==1 and entered[leaf]==1,"caller call cardinality")
    def covered(kind,start,size):
        counts=Counter()
        for access,address,n in accesses:
            if access==kind and start<=address<start+size:
                need(address+n<=start+size,"partial buffer crossing")
                counts.update(range(address-start,address-start+n))
        return counts
    wanted=lambda size:Counter({i:1 for i in range(size)})
    for address,size in ((a,256),(b,32)):
        need(covered("load",address,size)==(wanted(size) if mode=="packed" else Counter()),"scalar pack read coverage")
    need(covered("store",inputs,288)==(wanted(288) if mode=="packed" else Counter()),"pack write coverage")
    source_a,source_x=(a,b) if mode=="split" else (inputs,inputs+256)
    need(covered("vload",source_a,256)==wanted(256),"complete A vector read coverage")
    multiplicity=8 if row["algorithm"] in (1,3) else 1
    need(covered("vload",source_x,32)==Counter({i:multiplicity for i in range(32)}),"complete X vector read coverage")
    need(covered("store",slots,128)==wanted(128),"complete vector output coverage")
    need(covered("store",y,32)==wanted(32),"scalar output coverage")
    need([w for _,w in result if w in COUNTERS]==list(COUNTERS),"counter order")
    dots=sum(w&0xfe00707f==0x0200000b for _,w in result)
    need(dots==(32 if method=="vdot" else 0),"custom instruction count")
    return result,dict(instructions=len(result),branches=branches,calls=dict(entered),vdot=dots,
                       pack_bytes=288 if mode=="packed" else 0,output_bytes=32,
                       vector_reads=[dict(region="A" if source_a<=a<source_a+256 else "X",
                           offset=a-(source_a if source_a<=a<source_a+256 else source_x),bytes=n)
                           for kind,a,n in accesses if kind=="vload"],
                       actual_vl_eew_checked=True,split_packed_region_untouched=mode=="split")
