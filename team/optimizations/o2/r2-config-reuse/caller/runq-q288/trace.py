"""Bounded actual-ELF control/address checker derived from split/trace.py.

FP and vector arithmetic stay unknown. They cannot select an address or branch.
The checker proves call arguments, widths, footprints and strict FP encodings;
the independent row-major oracle, binary32 goldens and live DiffTest prove values.
"""
from collections import Counter
import hashlib
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

def path(elf, row, fixture, dataset=0):
    mode, method = row["kind"], row["method"]
    timer, leaf, wrapper = "split_measure", row["leaf"], row["wrapper"]
    allowed = (timer, wrapper) if mode == 'pack' else (timer, wrapper, leaf)
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
    a, b, y = addr('q_packed')+16, addr('q_inputs')+288*dataset, addr('q_output')+16
    weight, ws, xs = addr('q_weights'), addr('q_weight_scale'), addr('q_input_scale')+36*dataset
    ctx = addr('q_pack_context' if mode == 'pack' else 'q_context')
    metrics, slots = addr('q_measurement'), addr('q_slots')+16
    memory, accesses = {}, []
    def seed(address, raw):
        for i, value in enumerate(raw): memory[address + i] = value
    seed(weight, bytes(v&255 for v in fixture['weight']))
    seed(a, bytes(v&255 for v in fixture['packed']))
    seed(b, bytes(v&255 for v in fixture['inputs'][dataset]))
    seed(ws, struct.pack('<2592I', *fixture['weight_scale']))
    seed(xs, struct.pack('<9I', *fixture['input_scale'][dataset]))
    seed(ctx, struct.pack('<2Q',weight,a) if mode == 'pack' else struct.pack('<7Q',a,b,ws,xs,y,slots,addr(leaf)))
    seed(slots, bytes([0xa6])*128); seed(y,bytes([0xa6])*1152)
    stack_top = 0x87fff000
    initial_sp = stack_top - 48
    registers = [None] * 32
    registers[0], registers[2] = 0, initial_sp
    registers[8], registers[9] = ctx, metrics
    registers[10], registers[11], registers[20] = ctx, metrics, addr(wrapper)
    saved = (8,9,18,19,20,21,22,23,24,25,26,27)
    for i in (21,22,23,24,25,26,27): registers[i] = 0x83000000+i*16
    preserved = {i:registers[i] for i in saved}
    floating = [0x3ff0000000000000+i for i in range(32)]
    fp_preserved = {i:floating[i] for i in saved}
    fp_counts = Counter()
    weight_scale_load_sites=set()
    weight_scale_reads=0
    input_scale_reads=0
    leaf_arguments = []
    def known(value, why):
        need(value is not None, "unknown scalar value controls " + why)
        return value
    def read(address, n, signed_load=False):
        known(address, "memory address")
        need(all(address+i in memory for i in range(n)), "load outside initialized caller memory")
        accesses.append(("load", address, n))
        raw = [memory[address+i] for i in range(n)]
        if None in raw: return None
        value = int.from_bytes(bytes(raw), "little")
        return (signed(value, n*8) if signed_load else value) & MASK
    def write(address, n, value):
        known(address, "store address")
        need((initial_sp-4096 <= address and address+n <= stack_top) or
             (mode=='pack' and a <= address and address+n <= a+82944) or
             (mode=='Q' and slots <= address and address+n <= slots+128) or
             (mode=='Q' and y <= address and address+n <= y+1152), "caller store outside permitted buffers")
        accesses.append(("store", address, n))
        for i in range(n): memory[address+i] = None if value is None else (value >> (i*8)) & 255
    def binary(left, right, fn):
        return None if left is None or right is None else fn(left, right) & MASK
    result, calls, entered = [], [], Counter()
    branches = 0
    vector_state = (8,8,1)
    pc = begin[0]
    for _ in range(2000000):
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
            need(f7 in (0,32) or (f7==1 and f3==0), "unsupported scalar register instruction")
            bits = 32 if op == 0x3b else 64
            fun = {0:(lambda a,b:a-b) if f7==32 else (lambda a,b:a+b),
                   1:lambda a,b:a << (b&(bits-1)),
                   2:lambda a,b:int(signed(a,bits)<signed(b,bits)),3:lambda a,b:int(a<b),
                   4:lambda a,b:a^b,5:(lambda a,b:signed(a,bits) >> (b&(bits-1))) if f7==32 else (lambda a,b:(a & ((1<<bits)-1)) >> (b&(bits-1))),
                   6:lambda a,b:a|b,7:lambda a,b:a&b}[f3]
            value, sets = binary(left,right,(lambda a,b:a*b) if f7==1 else fun), True
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
                targets=(addr(wrapper),) if mode=='pack' else (addr(wrapper),addr(leaf))
                need(registers[2]%16==0 and target in targets, "invalid call target/stack alignment")
                calls.append(pc+4); entered[owners[target]]+=1
                if mode=='Q' and target==addr(leaf):
                    index=len(leaf_arguments)
                    args=(registers[10],registers[11],registers[12])
                    need(index<324 and args==(a+256*index,b+32*(index%9),slots), 'exact tile/group leaf arguments')
                    leaf_arguments.append(args)
            elif rd == 0:
                if op==0x67 and rs1==1:
                    need(calls and target==calls.pop(),"mismatched caller return")
                else:
                    need(op==0x6f and target in words and owners[target]==owners[pc],"unapproved caller jump")
            else: raise ValueError("unapproved link register")
            value, sets, next_pc=pc+4,True,target
        elif op == 0x73:
            need(w in COUNTERS or (owners[pc]==leaf and rd==0 and f3==5 and w>>20 in (0x008,0x00f)), "unsupported caller CSR")
            value, sets=None,True
        elif op in (0x07,0x27) and f3 in (2,3):
            need(owners[pc]==wrapper and mode=='Q','FP memory outside Q wrapper')
            n=4 if f3==2 else 8
            if op==0x07:
                address=(known(left,'FP load base')+immediate)&MASK
                value=read(address,n)
                floating[rd]=None if value is None else value | (0xffffffff00000000 if n==4 else 0)
                accesses.append(('fload',address,n))
                if ws<=address<ws+10368:
                    index=len(leaf_arguments)-1
                    need(index>=0 and weight_scale_reads//8==index and n==4 and
                         address==ws+4*((8*(index//9)+weight_scale_reads%8)*9+index%9),
                         'exact weight scale index after its tile/group leaf')
                    weight_scale_reads+=1;weight_scale_load_sites.add(pc)
                if xs<=address<xs+36:
                    index=len(leaf_arguments)-1
                    need(index==input_scale_reads and n==4 and address==xs+4*(index%9),
                         'exact input scale index after its tile/group leaf')
                    input_scale_reads+=1
            else:
                imm=signed(((w>>25)<<5)|((w>>7)&31),12)
                address=(known(left,'FP store base')+imm)&MASK
                write(address,n,floating[rs2]); accesses.append(('fstore',address,n))
        elif op==0x53:
            need(owners[pc]==wrapper and mode=='Q','FP arithmetic outside Q wrapper')
            if f7 in (0x00,0x08):
                need(f3 in (0,7),'FP rounding mode encoding')
                fp_counts['add' if f7==0 else 'mul']+=1; floating[rd]=None
            elif f7==0x68:
                need(rs2==0 and f3 in (0,7),'signed fcvt.s.w required')
                fp_counts['convert']+=1; floating[rd]=None
            elif f7==0x78:
                need(rs2==0 and f3==0,'fmv.w.x encoding')
                floating[rd]=None if left is None else 0xffffffff00000000|(left&0xffffffff)
            elif f7==0x10:
                need(f3==0 and rs1==rs2,'only exact fmv.s is permitted')
                floating[rd]=floating[rs1]
            else: raise ValueError(f'unsupported or fused FP word {w:08x}')
        elif op in (0x07,0x27,0x57,0x0b):
            need(owners[pc]==leaf,"vector/custom operation outside qualified leaf")
            if op==0x07:
                address=known(left,"vector load")
                need(vector_state is not None and f3==0 and w>>26==0 and rs2==0 and (w>>25)&1,
                     "unsupported vector memory encoding/state")
                vl,sew,lmul=vector_state
                need(sew==8 and lmul==1 and vl in (8,16),"load uses actual byte VL")
                regions=((a,82944),(b,288))
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
    need(not calls and registers[2]==initial_sp and all(registers[i]==v for i,v in preserved.items()),'caller stack/register balance')
    need(all(floating[i]==v for i,v in fp_preserved.items()),'FP callee-saved registers balanced')
    need(vector_state==(8,8,1),"return vector state")
    need(entered[wrapper]==1 and (mode=='pack' or entered[leaf]==324),'caller call cardinality')
    def covered(kind,start,size):
        counts=Counter()
        for access,address,n in accesses:
            if access==kind and start<=address<start+size:
                need(address+n<=start+size,"partial buffer crossing")
                counts.update(range(address-start,address-start+n))
        return counts
    wanted=lambda size,n=1:Counter({i:n for i in range(size)})
    need(covered('load',weight,82944)==(wanted(82944) if mode=='pack' else Counter()),'raw weight scalar reads')
    need(covered('store',a,82944)==(wanted(82944) if mode=='pack' else Counter()),'exact one-time pack footprint')
    if mode=='Q':
        need(covered('load',a,82944)==Counter() and covered('load',b,288)==Counter(),'no scalar quantized input copies')
        need(covered('vload',a,82944)==wanted(82944),'complete packed weight vector reads')
        multiplicity=8 if row['algorithm'] in (1,3) else 1
        need(covered('vload',b,288)==wanted(288,36*multiplicity),'complete input vector reads')
        need(covered('store',slots,128)==wanted(128,324),'all intermediate slots written')
        need(covered('store',y,1152)==wanted(1152),'all float outputs written once')
        need(covered('fload',ws,10368)==wanted(10368),'every row/group weight scale exactly once')
        need(covered('fload',xs,36)==wanted(36,36),'each group input scale per tile')
        need(fp_counts==Counter(convert=2592,mul=5184,add=2592),'strict FP operation cardinality')
    else:
        need(not fp_counts and not leaf_arguments,'pack contains no arithmetic consumer')
    need([w for _,w in result if w in COUNTERS]==list(COUNTERS),"counter order")
    dots=sum(w&0xfe00707f==0x0200000b for _,w in result)
    need(dots==(10368 if method=='vdot' else 0),'custom instruction count')
    return result,dict(instructions=len(result),branches=branches,calls=dict(entered),vdot=dots,
                       pack_bytes=82944 if mode=='pack' else 0,output_bytes=1152 if mode=='Q' else 82944,
                       fp_operations=dict(fp_counts),leaf_calls=len(leaf_arguments),
                       weight_scale_load_sites=sorted(weight_scale_load_sites),
                       exact_tile_group_arguments=True,exact_scale_footprints=True,
                       footprint_sha256=hashlib.sha256(repr(accesses).encode()).hexdigest(),
                       actual_vl_eew_checked=True,fp_values='unknown; checked by independent oracle and DiffTest')
