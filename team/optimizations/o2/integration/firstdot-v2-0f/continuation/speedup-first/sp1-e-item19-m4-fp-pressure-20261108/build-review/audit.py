#!/usr/bin/env python3
"""Read GNU objects/ELF only; no target/library execution. Callable ABI validator."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
def pin(path):
    path=Path(path); data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def require(condition,message):
    if not condition: raise ValueError(message)
def elf_sections(data):
    require(data[:6]==b'\x7fELF\x02\x01','not ELF64 little endian')
    off=struct.unpack_from('<Q',data,40)[0]
    entsize,count=struct.unpack_from('<HH',data,58)
    return [struct.unpack_from('<IIQQQQIIQQ',data,off+i*entsize) for i in range(count)]
def elf_bytes(data,pc,size):
    for section in elf_sections(data):
        _,typ,_,address,offset,length,*_=section
        if typ==1 and address<=pc and pc+size<=address+length:
            return data[offset+pc-address:offset+pc-address+size]
    raise ValueError('PC not inside ELF PROGBITS')
def parse_disassembly(text):
    result={}
    for line in text.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{4,8})\s+([^\s]+)\s*(.*)',line)
        if m: result[int(m[1],16)]={'pc':int(m[1],16),'word':int(m[2],16),'width':len(m[2])//2,'mnemonic':m[3],'operands':m[4]}
    return result
def audit_kernel_words(words):
    """Reject unknown encodings and standard scalar/FP callee-save/link/SP writes."""
    protected={1,2,3,4,8,9,*range(18,28)}
    intwrites=[]; fpwrites=[]; vectorwrites=[]
    for index,w in enumerate(words):
        require(w&3==3,'compressed instruction inside audited leaf')
        op=w&127; rd=(w>>7)&31; f3=(w>>12)&7; f7=w>>25
        integer=False; fp=False; vector=False
        if op in (0x13,0x33,0x03,0x37,0x17,0x73): integer=True
        elif op==0x67:
            require(w==0x00008067 and index==len(words)-1,'non-return control transfer')
        elif op==0x53:
            if f7==0x70: integer=True
            elif f7 in (0x78,0x0c,0x08,0x10): fp=True
            else: raise ValueError('unapproved FP instruction')
        elif op==0x57:
            if f3==7: integer=True
            else: vector=True
        elif op in (0x07,0x0b): vector=True
        elif op not in (0x23,0x27,0x63): raise ValueError('unknown leaf opcode')
        if integer:
            require(rd not in protected,f'forbidden scalar ABI destination x{rd}')
            intwrites.append(rd)
        if fp:
            require(rd not in {8,9,*range(18,28)},f'forbidden FP ABI destination f{rd}')
            fpwrites.append(rd)
        if vector: vectorwrites.append(rd)
    return {'integer_destinations':sorted(set(intwrites)),'fp_destinations':sorted(set(fpwrites)),
            'vector_destinations':sorted(set(vectorwrites)),'protected_writes':0,'leaf_no_calls':True}
def audit_m1_sequence(text, function, symbols, ins):
    """Actual decoded sequence/RAW contract; no architectural/target execution."""
    name=function['name'];stage=function['stage'];phase=function['phase']
    if stage=='prelude': return
    def unique(token):
        require(text.count(token)==1,'M1 unique instruction '+token)
        return text.index(token)
    fp=unique('fdiv.s ft0,ft1,ft2,rne')
    early=unique('fmv.x.w t6,ft0')
    delay1=unique('fmul.s ft3,ft0,ft2,rne')
    delay2=unique('fsgnj.s ft3,ft3,ft3')
    first=unique('vfmv.v.f v24,ft3')
    last=unique('vfmv.v.f v31,ft3')
    vadd=unique('vadd.vx v8,v8,t6')
    require(fp<early<delay1<delay2<first<last<vadd,'M1 release/pressure/vadd order')
    require(text[fp+1:first]==['fmv.x.w t6,ft0','fmul.s ft3,ft0,ft2,rne','fsgnj.s ft3,ft3,ft3','fmul.s ft3,ft3,ft2,rne','fmul.s ft3,ft3,ft2,rne','fmul.s ft3,ft3,ft2,rne','vsetivli zero,4,e32,m1,tu,mu'],'M1 release must precede pressure with exact configuration')
    require(not any(i.startswith('vle8.v ') or i=='add t6,a0,t6' for i in text),'M1 forbidden repeated input reload')
    require([i for i in text if i.startswith('vl1re8.v ')]==['vl1re8.v v8,(a0)','vl1re8.v v9,(t3)','vl1re8.v v17,(t3)'],'M1 full input/sentinel preload')
    start=symbols[name];apos=(symbols[name+'_A']-start)//4;bpos=(symbols[name+'_B']-start)//4
    require(vadd+1==apos,'M1 zero-add immediately before A')
    if stage=='S0':
        require(text[last+1:apos]==['vsetivli zero,8,e8,m1,tu,mu']+['xori t6,t6,1']*(2*phase)+['vadd.vx v8,v8,t6'],'M1 S0 exact phase')
        require(bpos==apos+1,'M1 S0 adjacent A/B')
        require(not any(i.startswith('divu ') or i.startswith('andi t6') for i in text),'M1 S0 no extra DIV/mask')
    else:
        div=unique('divu t0,t0,t1')
        expected=['ld t0,0(a2)','ld t1,8(a2)','ld t2,16(a2)','divu t0,t0,t1','andi t4,t0,2','lui t3,0x40e00','add t3,t3,t4','fmv.w.x ft1,t3','lui t3,0x40000','fmv.w.x ft2,t3','fdiv.s ft0,ft1,ft2,rne']
        require(text[div-3:fp+1]==expected,'M1 quotient-before-FP real RAW chain')
        require(text[last+1:apos]==['vsetivli zero,8,e8,m1,tu,mu','vadd.vx v8,v8,t6'],'M1 S1 v8 phase isolation')
        branch=symbols[name+'_branch'];skip=symbols[name+'_skip_B'];brpos=(branch-start)//4
        require(symbols[name+'_A']<branch<symbols[name+'_B']<skip,'M1 A/branch/B age order')
        require(text[apos+1:brpos]==['andi t4,t6,255']+['xori t4,t4,1']*(2*phase)+['add t0,t0,t4'],'M1 independent branch phase RAW')
        require(brpos+1==bpos and symbols[name+'_B']+4==skip,'M1 branch B skip layout')
        require(ins[branch]['mnemonic']=='bne' and ins[branch]['operands'].startswith('t0,t2,') and f'{skip:x}' in ins[branch]['operands'],'M1 branch condition/target')
        require(not any(i=='sub t4,t6,a0' for i in text),'M1 old address dependency forbidden')

def audit(build):
    build=Path(build)
    manifest=json.loads((ROOT/'software/manifest.source.json').read_text())
    symbols={}
    for line in (build/'o2-cancel.elf.nm.stdout').read_text().splitlines():
        parts=line.split()
        if len(parts)>=3: symbols[parts[-1]]=int(parts[0],16)
    elf=(build/'o2-cancel.elf').read_bytes()
    ins=parse_disassembly((build/'o2-cancel.elf.objdump.stdout').read_text())
    audits=[]
    for function in manifest['functions']:
        name=function['name']; start=symbols[name]; end=symbols[name+'_end']
        raw=elf_bytes(elf,start,end-start)
        require(len(raw)%4==0,'leaf is not 4-byte instruction aligned')
        words=list(struct.unpack('<'+'I'*(len(raw)//4),raw))
        seq=[ins[pc] for pc in range(start,end,4)]
        require([i['word'] for i in seq]==words,'objdump vs ELF mismatch')
        abi=audit_kernel_words(words)
        text=[i['mnemonic']+' '+i['operands'].split('#')[0].strip() for i in seq]
        expected_prefix=['csrrs a3,vl,zero','csrrs a4,vtype,zero','csrrs a5,vstart,zero','csrrs a6,vcsr,zero','csrrs a7,fcsr,zero',
                         'sd a3,32(a1)','sd a4,40(a1)','sd a5,48(a1)','sd a6,56(a1)','sd a7,64(a1)']
        require(text[:10]==expected_prefix,'CSR save/source layout mismatch')
        expected_suffix=['csrrwi zero,vstart,0','vsetvl zero,a3,a4','csrrw zero,vstart,a5','csrrw zero,vcsr,a6','csrrw zero,fcsr,a7',
                         'csrrs t3,vl,zero','sd t3,72(a1)','csrrs t3,vtype,zero','sd t3,80(a1)',
                         'csrrs t3,vstart,zero','sd t3,88(a1)','csrrs t3,vcsr,zero','sd t3,96(a1)',
                         'csrrs t3,fcsr,zero','sd t3,104(a1)','jalr zero,0(ra)']
        require(text[-16:]==expected_suffix,'final CSR restore/readback mismatch')
        vector_stores=[i['operands'] for i in seq if i['mnemonic']=='vs1r.v']
        require(vector_stores==(['v0,(a1)','v17,(t3)'] if function['stage']=='prelude' else ['v16,(a1)','v17,(t3)']),'full-register store mismatch')
        require(abi['vector_destinations']==([0,8,9,17] if function['stage']=='prelude' else [8,9,16,17,24,25,26,27,28,29,30,31]),'unexpected vector clobber')
        customs=[i for i in seq if (i['word']&0xfe00707f)==0x0200000b]
        if function['stage']=='prelude':
            require(len(customs)==1 and not abi['fp_destinations'],'guard FP isolation')
        else:
            require(len(customs)==2,'wrong custom count')
            require([i['operands'] for i in seq if i['mnemonic']=='vfmv.v.f']==[f'v{v},ft3' for v in range(24,32)],'scratch F2v mismatch')
            require('vsetivli zero,4,e32,m1,tu,mu' in text,'missing legal F2v config')
            pressure=symbols[name+'_pressure']
            restore=ins[pressure+8*4]
            require(restore['mnemonic']=='vsetivli' and restore['operands']=='zero,8,e8,m1,tu,mu','custom configuration restore mismatch')
            audit_m1_sequence(text,function,symbols,ins)
            if function['stage']=='S1':
                function.update(branch_pc=symbols[name+'_branch'],skip_b_pc=symbols[name+'_skip_B'])
        if function['stage']!='prelude':
            critical_count=(symbols[name+'_B']-symbols[name+'_pressure'])//4+1
            function.update(critical_arch_instructions=critical_count,critical_f2v_and_vadd_uop_estimate=critical_count+9,rob_capacity=48,rob_fit_status='STATIC_ESTIMATE_NOT_DYNAMIC_PROOF')
            require(critical_count+9<=48,'critical-region lower-bound expansion exceeds ROB48')
        function.update(start_pc=start,end_pc=end,instruction_count=len(words),sha256=hashlib.sha256(raw).hexdigest())
        audits.append({'function':name,**abi,'csr_save_restore_readback':True,'full128_stores':True})
    for role in manifest['pc_roles']:
        role['pc']=symbols[role['symbol']]
        require(ins[role['pc']]['word']==role['word'],'custom PC/word mismatch')
        role.update(vs1_low64=manifest['vs1_low64'],vs2_low64=manifest['vs2_low64'])
    roles_by_pc={r['pc']:r for r in manifest['pc_roles']}
    all_custom=[pc for pc,i in ins.items() if i['width']==4 and (i['word']&0xfe00707f)==0x0200000b]
    require(set(all_custom)==set(roles_by_pc),'unmanifested linked custom instruction')
    manifest['expected_retired_pc_sequence']=[symbols[s] for p in manifest['call_plan'] for s in p['retired_symbols']]
    for p in manifest['call_plan']:
        p['expected_retired_pcs']=[symbols[s] for s in p['retired_symbols']]
        p['expected_a128']=manifest['expected_dot128']
        p['expected_b128']=manifest['sentinel128'] if p['probe'] or p['stage']=='prelude' else manifest['expected_dot128']
    require(len(manifest['expected_retired_pc_sequence'])==77,'retired sequence count mismatch')
    manifest['images']={suffix:pin(build/('o2-cancel.'+suffix)) for suffix in ('elf','bin')}
    manifest['build_result']=pin(build/'RESULT.json')
    manifest['sources']=[pin(p) for p in sorted((ROOT/'software').iterdir()) if p.is_file() and p.name not in ('manifest.json','README.md')]
    manifest['guard']={**manifest['pc_roles'][0], 'bit100_injection':'EXTERNAL_INTERPOSER_NOT_PART_OF_IMAGE','first_custom':True,'before_fp_pressure':True}
    manifest['abi']={'standard_riscv_calling_convention':True,'vector_calling_convention_variant':False,
        'callee_saved_scalar_fp_untouched':True,'leaf_stack_unchanged':True,'full_dynamic_register_sentinel':False}
    manifest['static_custom_count']=17
    manifest['uart_protocol']={'begin':'OC19_BEGIN calls=41 custom=77 phases=0,1,2,4',
        'call':'OC19_CALL seq={seq} phase={phase_or_0} stage={stage} probe={0_or_1}',
        'pass':'OC19_PASS seq={seq}','failure':'OC19_FAIL seq={seq} error={bitmask}',
        'summary':'OC19_SUMMARY calls=41 custom=77','failure_exit_code':1,'success_main_return':0,
        'not_a_cycle_boundary':True}
    (ROOT/'software/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result={'status':'PASS_OBJECT_AND_LINK_AUDIT','target_executed':False,'manifest':pin(ROOT/'software/manifest.json'),
        'functions':audits,'static_custom_instructions':17,'expected_calls':41,'expected_retired_customs':77,
        'no_undefined_symbols':not any(' U ' in line for line in (build/'o2-cancel.elf.nm.stdout').read_text().splitlines()),
        'known_boundary':'Static ordering and dependencies do not establish actual P/R occupancy, arbitration or redirect.'}
    require(result['no_undefined_symbols'],'unresolved symbol')
    (build/'OBJECT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
    return result
if __name__=='__main__': audit(sys.argv[1])
