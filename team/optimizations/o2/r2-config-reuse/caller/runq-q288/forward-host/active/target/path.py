"""Bounded actual-word wrapper/quantizer address proof; frozen Q value models.

Scalar FP results remain unknown here and cannot drive branches or addresses.
Target golden comparisons and unchanged DiffTest validate those values.
"""
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import hashlib,struct
MASK=(1<<64)-1
START,STOP=0x51300013,0x51400013
COUNTERS=(0xc0202773,0xc0002873,0xc00028f3,0xc02027f3)
def need(ok,why):
    if not ok:raise ValueError(why)
def signed(v,bits):
    v&=(1<<bits)-1;return v-(1<<bits) if v>>(bits-1) else v
def sha(raw):return hashlib.sha256(raw).hexdigest()

def path(repo,elf,row,fixture,dataset,tail,model):
    addr=lambda n:elf.symbols[n][0]
    timer_raw=elf.symbol_data('split_measure')
    timer=[(addr('split_measure')+4*i,w) for i,(w,) in enumerate(struct.iter_unpack('<I',timer_raw))]
    need([i for i,(_,w) in enumerate(timer) if w==START]==[11] and
         [i for i,(_,w) in enumerate(timer) if w==STOP]==[26] and timer[20][1]==0x000a00e7,
         'exact common timer call interval')
    words,owners={},{}
    for name in ('qkv_boundary','qkv_quantize'):
        body=elf.symbol_data(name);need(addr(name)%4==len(body)%4==0,'aligned uncompressed function')
        for i,(w,) in enumerate(struct.iter_unpack('<I',body)):
            need(w&3==3,'uncompressed wrapper and quantizer');words[addr(name)+4*i]=w;owners[addr(name)+4*i]=name
    fp=addr('qkv_fp')+1152*dataset;x=addr('qkv_x')+16;xs=addr('qkv_xs')+16
    ctx=addr('qkv_context');qctx=addr('qkv_projection');y=addr('qkv_y')+16;slots=addr('qkv_slots')+16
    kernel=addr(row['kernel']);halt=timer[21][0];initial_sp=0x87fff000-48
    memory={};reads=Counter();writes=Counter();fp_counts=Counter();path=[];calls=[];q_details=[]
    def seed(address,raw):memory.update({address+i:b for i,b in enumerate(raw)})
    seed(ctx,struct.pack('<7Q',fp,x,xs,qctx,qctx+56,qctx+112,kernel))
    seed(fp,fixture['raw'][f'fp-{dataset}.bin'])
    for i in range(3):seed(qctx+56*i,struct.pack('<7Q',addr('qkv_packed')+82944*i,x,
        addr('qkv_weight_scale')+10368*i,xs,y+1152*i,slots+128*i,addr(row['leaf'])))
    def known(v,why):need(v is not None,'unknown FP data controls '+why);return v
    def read(address,size,quantizer=False):
        need(all(address+i in memory for i in range(size)),'wrapper/quantizer read outside initialized region')
        if quantizer:
            need(fp<=address and address+size<=fp+1152,'quantizer reads only FP32 input')
            reads.update(range(address-fp,address-fp+size))
        raw=[memory[address+i] for i in range(size)]
        return None if None in raw else int.from_bytes(bytes(raw),'little')
    def write(address,size,value,quantizer=False):
        if quantizer:
            region='x' if x<=address and address+size<=x+288 else 'xs' if xs<=address and address+size<=xs+36 else None
            need(region is not None,'quantizer writes only exact q/scales')
            need((region=='x' and size==1) or (region=='xs' and size==4),'quantized write widths')
            base=x if region=='x' else xs;writes.update((region,i) for i in range(address-base,address-base+size))
        else:need(initial_sp-16<=address and address+size<=initial_sp and size==8,'wrapper exact 16-byte stack')
        for i in range(size):memory[address+i]=None if value is None else (value>>(8*i))&255
    registers=[0x9345678900000000+i*257 for i in range(32)];registers[0]=0
    registers[1]=halt;registers[2]=initial_sp;registers[8]=registers[10]=ctx
    registers[9]=addr('qkv_measurement');registers[20]=addr('qkv_boundary')
    saved={i:registers[i] for i in (1,*model.SAVED)}
    floating=[0x3ff1234500000000+i*257 for i in range(32)];saved_fp={i:floating[i] for i in model.FP_SAVED}
    machine_path=repo/'team/optimizations/o2/r2-safe-tail/machine_model.py'
    cls=tail.checker_class(model,machine_path) if row['method']=='vdot' else model.machine_class(machine_path)
    pc=addr('qkv_boundary');lowest_sp=initial_sp
    for step in range(10000):
        if pc==halt:break
        if pc==kernel:
            index=len(q_details);need(index<3 and calls==['quantize']+[row['kernel']]*index,'one quantization before three ordered projections')
            need(registers[10]==qctx+56*index,'actual projection context and order')
            need(writes==Counter({**{('x',i):1 for i in range(288)},**{('xs',i):1 for i in range(36)}}),
                 'Q consumes one complete already-written quantization')
            f=fixture['projections'][index];m=cls(f,dataset,poison=0x514b56+index)
            m.addresses=dict(packed=addr('qkv_packed')+82944*index,x=x,ws=addr('qkv_weight_scale')+10368*index,
                xs=xs,y=y+1152*index,slots=slots+128*index,context=qctx+56*index)
            m.regions['context']=bytearray(struct.pack('<7Q',*(m.addresses[n] for n in ('packed','x','ws','xs','y','slots')),addr(row['leaf'])))
            m.original['context']=bytes(m.regions['context'])
            m.x=[v if v is not None else 0x1234abcd00000000+i for i,v in enumerate(registers)]
            m.halt=m.x[1];m.saved={i:m.x[i] for i in m.saved}
            view=SimpleNamespace(symbols={row['kernel']:(*elf.symbols[row['kernel']][:2],0)},symbol_data=elf.symbol_data)
            m.execute_function(view,row['kernel'])
            detail=m.check(f['golden'][dataset]) if row['method']=='vdot' else m.check_full('rvv4',f['golden'][dataset])
            path.extend(m.path);q_details.append(detail);calls.append(row['kernel'])
            registers=m.x[:];pc=m.halt;continue
        need(pc in words,'new path escaped wrapper/quantizer and named Q')
        w=words[pc];owner=owners[pc];quantizer=owner=='qkv_quantize'
        if pc==addr('qkv_quantize'):
            need(not calls and (registers[10],registers[11],registers[12])==(fp,x,xs),'unique quantize arguments')
            calls.append('quantize')
        path.append((pc,w));next_pc=pc+4
        op,rd,a,b,f3,f7=w&127,(w>>7)&31,(w>>15)&31,(w>>20)&31,(w>>12)&7,w>>25
        imm=signed(w>>20,12);left,right=registers[a],registers[b];sets=False;value=None
        if op in (0x37,0x17):value=(signed(w&0xfffff000,32)+(pc if op==0x17 else 0))&MASK;sets=True
        elif op==0x13 and f3==0:value=(known(left,'addi')+imm)&MASK;sets=True
        elif op==3 and f3==3:
            need(not quantizer,'no integer quantizer loads');value=read((known(left,'load')+imm)&MASK,8);sets=True
        elif op==0x23:
            offset=signed(((w>>25)<<5)|((w>>7)&31),12)
            need(f3==(0 if quantizer else 3),'exact integer store width')
            write((known(left,'store')+offset)&MASK,1<<f3,right,quantizer)
        elif op==0x63 and f3==1:
            need(quantizer,'only fixed quantizer loops branch')
            offset=((w>>31)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1)
            if known(left,'branch')!=known(right,'branch'):next_pc=pc+signed(offset,13)
        elif op==0x67 and f3==0:
            next_pc=(known(left,'jalr')+imm)&MASK&~1;value=pc+4;sets=True
        elif op==0x6f:
            offset=((w>>31)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1)
            next_pc=pc+signed(offset,21);value=pc+4;sets=True
        elif op==7 and f3==2:
            need(quantizer,'FP load only in quantizer');read(known(left,'FP load')+imm,4,True);floating[rd]=None;fp_counts['load']+=1
        elif op==0x27 and f3==2:
            need(quantizer,'FP store only in quantizer');offset=signed(((w>>25)<<5)|((w>>7)&31),12)
            write(known(left,'FP store')+offset,4,floating[b],True);fp_counts['scale_store']+=1
        elif op==0x53:
            need(quantizer,'scalar FP only in quantizer')
            if f7==0x78:
                need(b==0 and f3==0,'fmv.w.x');floating[rd]=None if left is None else 0xffffffff00000000|(left&0xffffffff);fp_counts['move']+=1
            elif f7==0x10:
                need(f3==2 and a==b,'same-source absolute value');floating[rd]=None;fp_counts['abs']+=1
            elif f7==0x14:
                need(f3==1,'fmax.s');floating[rd]=None;fp_counts['max']+=1
            elif f7==0x0c:
                need(f3==0,'explicit RNE FP32 division');floating[rd]=None;fp_counts['divide']+=1
            elif f7==0x60:
                need(b==0 and f3==4,'explicit signed RMM integer conversion');sets=True;value=None;fp_counts['round']+=1
            else:raise ValueError('unsupported quantizer FP instruction '+hex(w))
        else:raise ValueError('unsupported new wrapper/quantizer word '+hex(w))
        if sets and rd:registers[rd]=value
        registers[0]=0;lowest_sp=min(lowest_sp,known(registers[2],'stack'));pc=next_pc
    else:raise ValueError('wrapper/quantizer finite path budget exceeded')
    need(calls==['quantize',row['kernel'],row['kernel'],row['kernel']],'complete consumer call inventory')
    need(all(registers[i]==v for i,v in saved.items()) and all(floating[i]==v for i,v in saved_fp.items()),'wrapper full ABI preservation')
    need(lowest_sp==initial_sp-16,'exact wrapper stack depth')
    need(reads==Counter({i:2 for i in range(1152)}),'each FP32 input read exactly twice')
    need(writes==Counter({**{('x',i):1 for i in range(288)},**{('xs',i):1 for i in range(36)}}),'each output q/scale byte written once')
    need(fp_counts==Counter(load=576,move=10,abs=288,max=288,divide=297,round=288,scale_store=9),'complete fixed quantizer operation inventory')
    stream=timer[11:21]+path+timer[21:27]
    counters=[i for i,(_,w) in enumerate(stream) if w in COUNTERS]
    need([stream[i][1] for i in counters]==list(COUNTERS),'same four CSR counter sites')
    dots=sum(w&0xfe00707f==0x0200000b for _,w in stream);need(dots==row['dots'],'complete QKV custom count')
    detail=dict(instructions=len(stream),expected_csr_instret=counters[3]-counters[0],vdot=dots,
        calls=calls,quantize_fp_operations=dict(fp_counts),q_details=q_details,stack_bytes=16,
        actual_elf_addresses=True,quantize_values='unknown here; original golden and target DiffTest',
        shared_quantization=True,quantize_input_reads=2304,quantize_output_bytes=324,
        path_sha256=sha(b''.join(struct.pack('<QI',pc,w) for pc,w in stream)))
    return stream,detail
