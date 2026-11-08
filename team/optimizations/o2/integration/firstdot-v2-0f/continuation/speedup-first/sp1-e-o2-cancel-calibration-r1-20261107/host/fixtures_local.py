"""Synthetic tests only. Shared old fixture transitions with new exact image banners."""
from pathlib import Path
from o2_cancel_fixtures import Fixture
from normal_adapter import expected_uart
from adapter import C as RC,PC as C,M,elf_read
class RealInputsFixture(Fixture):
    def request(self,rob,illegal=0,vl=8):
        return super().request(rob,illegal,vl,vs1=M['vs1_low64'],vs2=M['vs2_low64'])

def emit_call(f,seq,c):
    num=seq*3
    ptr=lambda k:f'{((num+k)//48)%2}:{(num+k)%48}'
    rows=[v for v in C['pc_roles'].values() if v['stage']==c['stage'] and v['phase']==c['phase']]
    rows.sort(key=lambda x:x['pc'])
    def enter(rob,row):
        f.enqueue(rob,pdest=5+row['vd'],vd=row['vd'])
        f.entries[rob]['pc']=row['pc']
        f.rows[-1]=f.rows[-1].split(' pc=')[0]+f" pc={hex(row['pc'])} ftq=0:1 word={hex(row['word'])}"
    enter(ptr(0),rows[0])
    if c['stage']=='prelude':f.tick(ptr(0));f.drain();return
    enter(ptr(2),rows[1]);f.tick(ptr(0));f.tick(ptr(2),ready=0 if c['stage']=='S0' or c['probe'] else 1)
    if c['probe']:f.tick(ready=1,flush=(ptr(1),0))
    f.drain()

def full_fixture():
    f=RealInputsFixture()
    for c in C['call_plan']:emit_call(f,c['seq'],c)
    return f.text()+'\n'.join(expected_uart(C))+'\nHIT GOOD TRAP\n'

def banners(role):
    ref=RC['runtime']['negative_reference' if role=='bit100' else 'normal_reference']['path']
    return 'The image is '+RC['runtime']['bin']['path']+'\nThe reference model is '+ref+'\nThe first instruction of core 0 has commited. Difftest enabled.\n'

def normal():
    return banners('candidate-normal')+full_fixture()+'Guest cycle spent: 20000\nCore-0 instrCnt = 9000, cycleCnt = 19900\n'

def negative(before=0,after=0,tail=31,raw_dst=32):
    f=RealInputsFixture();rob='0:5';f.enqueue(rob,pdest=5,vd=0);pc=RC['guard']['pc'];word=RC['guard']['word']
    f.entries[rob]['pc']=pc;f.rows[-1]=f.rows[-1].split(' pc=')[0]+f" pc={hex(pc)} ftq=0:1 word={hex(word)}"
    f.tick(rob);f.drain()
    result=int.from_bytes(bytes.fromhex(M['expected_dot128']),'little');head=pc-before*4;count=before+1+after
    selected={((tail-count+1+i)%32):(head+4*i) for i in range(count)}
    lines=['==============  In the last commit group  ==============',f'the first commit instr pc of DUT is {head:#018x}',f'the first commit instr pc of REF is {head:#018x}','','============== Commit Group Trace (Core 0) ==============']
    for i in range(16):lines.append(f'commit group [{i:02d}]: pc {head:010x} cmtcnt '+(str(count)+' <--' if i==15 else '1'))
    lines+=['','============== Commit Instr Trace ==============']
    for i in range(32):
        loc=selected.get(i,pc);w=int.from_bytes(elf_read(loc,4),'little');current=i in selected
        dst=((w>>7)&31) if current else raw_dst
        idx=5+(loc-pc)//4 if current else i
        data=result if loc==pc else 0
        lines.append(f'[{i:02d}] commit pc {loc:016x} inst {w:08x} wen 1 dst {dst:02d} data {data:016x} idx {idx:03x}'+(' <--' if i==tail else ''))
    lines+=['','==============  REF Regs  ==============',f'v0: 0x{result>>64:016x}_{result&((1<<64)-1):016x}','vtype: 0x0000000000000000 vstart: 0x0000000000000000 vxsat: 0x0000000000000000','vxrm: 0x0000000000000000 vl: 0x0000000000000008 vcsr: 0x0000000000000000',f'v0_high different at pc = {hex(head)}, right= 0x0000001000000000, wrong = 0x0000000000000000','Core 0: ABORT at pc = 0x8000027c']
    return banners('bit100')+f.text()+'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=0 pc=0x80000278 instruction=0x0294000b\n'+'\n'.join(lines)+'\n'
