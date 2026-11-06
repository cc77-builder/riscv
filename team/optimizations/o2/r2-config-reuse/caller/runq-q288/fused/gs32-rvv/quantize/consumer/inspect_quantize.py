"""Final-ELF identity checks for the bounded G/GQ consumer experiment."""
from pathlib import Path
import json
import re
import struct

def inspect(b, elf, dis, qualified):
    need=b.need
    qualified=Path(qualified)
    old=b.c.base.f.g.ELF((qualified/'quantize-gs32-check.elf').read_bytes())
    qname='r2_quantize_gs32_rvv'
    start,size,*_=elf.symbols[qname]
    previous,old_size,*_=old.symbols[qname]
    need(size==old_size==248,'complete qualified quantize function extent')
    word=lambda pc:struct.unpack('<I',elf.read(pc,4))[0]
    def pair(pc,reg,opcode,rd):
        hi,lo=word(pc),word(pc+4)
        need(hi&0xfff==(reg<<7)|0x17,'actual AUIPC source register')
        need(lo&0xfffff==(reg<<15)|(rd<<7)|opcode,'actual paired opcode/registers')
        return (pc+b.signed(hi&0xfffff000,32)+b.signed(lo>>20,12))&((1<<64)-1)
    calls=b.g.calls(dis)
    tail=[(pc,target) for pc,target in calls if start<=pc<start+size]
    need(len(tail)==1 and tail[0][1]=='quantize','only original scalar fallback call')
    gs=[int(m[1],16) for m in re.finditer(r'\b([0-9a-f]+):\s+R_RISCV_PCREL_HI20\s+GS\b',dis) if start<=int(m[1],16)<start+size]
    need(len(gs)==1,'one actual shared GS relocation')
    need(pair(gs[0],5,0x13,5)==elf.symbols['GS'][0],'quantize uses shared GS definition')
    need(pair(tail[0][0],6,0x67,0)==elf.symbols['quantize'][0],'fallback tails to original scalar')
    allowed={gs[0]-start:0xfff,gs[0]-start+4:0xfffff,tail[0][0]-start:0xfff,tail[0][0]-start+4:0xfffff}
    need(set(allowed)=={24,28,240,244},'same external relocation positions as qualified quantize')
    changes=[]
    for offset in range(0,size,4):
        lhs=struct.unpack('<I',old.read(previous+offset,4))[0]
        rhs=word(start+offset);mask=allowed.get(offset,0xffffffff)
        need(lhs&mask==rhs&mask,'qualified quantize instruction identity at '+str(offset))
        if lhs!=rhs:changes.append(offset)
    routes={}
    for caller,wanted in (('consumer_gs32_cache','quantize'),('consumer_gs32_quantize_cache',qname)):
        pc,length,*_=elf.symbols[caller]
        found=[(p,t) for p,t in calls if pc<=p<pc+length and t in ('quantize',qname)]
        need(len(found)==5 and all(t==wanted for _,t in found),'five exact quantize sites in '+caller)
        rows=[]
        for site,target in found:
            need(pair(site,1,0x67,1)==elf.symbols[target][0],'actual quantize JALR target')
            rows.append(dict(pc=hex(site),target=target,target_address=hex(elf.symbols[target][0]),bytes=elf.read(site,8).hex()))
        routes[caller]=rows
    checker=b.load('gsq_original_quantize_checker',qualified/'source/verify.py')
    oracle=json.loads((qualified/'source/oracle.json').read_text())['readback']
    original={}
    for name in ('quantize','__round','__fabs'):
        pc,length,*_=elf.symbols[name]
        lines=[]
        for line in dis.splitlines():
            m=re.match(r'^\s*([0-9a-f]+):',line)
            if m and pc<=int(m[1],16)<pc+length:lines.append(line)
        text='\n'.join(lines)
        original[name]=checker.original_code_equal(name,text,oracle)
        if name=='quantize':
            need(text.count('<__fabs>')==text.count('<__round>')==text.count('<GS>')==1,'same scalar call/global targets')
            constants=re.findall(r'flw\s+fs1,[^\n]+#\s+([0-9a-fA-F]+)',text)
            need(len(constants)==1 and elf.read(int(constants[0],16),4)==bytes.fromhex('0000fe42'),'same scalar denominator')
        elif name=='__round':
            constants=re.findall(r'fld\s+[^\n]+#\s+([0-9a-fA-F]+)',text)
            need(len(constants)==1 and elf.read(int(constants[0],16),8)==bytes.fromhex('0000000000004043'),'same round threshold')
    return dict(status='GSQ_QUANTIZE_ACTUAL_ELF_IDENTITY_PASS',bytes=size,qualified_elf_sha256=b.digest(qualified/'quantize-gs32-check.elf'),relocated_word_offsets=changes,allowed_external_relocations=sorted(allowed),shared_gs_address=hex(elf.symbols['GS'][0]),fallback_address=hex(elf.symbols['quantize'][0]),call_sites=routes,original_scalar_and_math=original,scope='bounded final ELF machine-word identity and call binding; no dynamic call count claim')
