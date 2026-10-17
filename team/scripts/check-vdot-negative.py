"""Bind a bit100 negative control to the actual failing DiffTest commit group."""
import re

def require(ok,message):
    if not ok: raise ValueError(message)

def one(pattern,text,message):
    matches=list(re.finditer(pattern,text,re.MULTILINE))
    require(len(matches)==1,message)
    return matches[0]

def check(text,exit_code):
    require(exit_code==1,'negative fixture did not reject with exit 1')
    require('The first instruction of core 0 has commited. Difftest enabled.' in text
            and 'The reference model is ' in text,'missing live DiffTest')
    require(text.count('DIFFTEST_HIGHBIT_NEGATIVE_INJECTED')==1,'missing/duplicate injection')
    inj=one(r'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=(\d+) pc=(0x[0-9a-fA-F]+) instruction=(0x[0-9a-fA-F]+)',text,'invalid injection')
    vd=int(inj[1]);pc=int(inj[2],16);word=int(inj[3],16)
    require(0<=vd<32 and word&0xfe00707f==0x0200000b and (word>>7)&31==vd,'negative instruction/destination is not vdot')
    require(text.count('different at pc')==1,'missing or multiple register mismatches')
    mismatch=one(r'v(\d+)_high different at pc = (0x[0-9a-fA-F]+), right=\s*(0x[0-9a-fA-F]+), wrong =\s*(0x[0-9a-fA-F]+)',text,'missing high-half mismatch')
    require(int(mismatch[1])==vd,'negative register mismatch')
    require(int(mismatch[3],16)^int(mismatch[4],16)==1<<36,'negative bit mismatch')
    # RefProxy::display uses dut->commit[0].pc after the entire commit batch.
    # DiffState marks the newest group and newest slot in its 32-entry ring.
    group=one(r'^commit group \[\d+\]: pc ([0-9a-fA-F]+) cmtcnt (\d+) <--\s*$',text,'missing/ambiguous latest commit group')
    group_pc=int(group[1],16);count=int(group[2])
    require(group_pc==int(mismatch[2],16),'negative mismatch belongs to another group')
    for side in ('DUT','REF'):
        first=one(r'^the first commit instr pc of '+side+r' is (0x[0-9a-fA-F]+)\s*$',text,'missing/ambiguous '+side+' group PC')
        require(int(first[1],16)==group_pc,'negative '+side+' group PC differs')
    rows={};ends=[]
    pattern=r'^\[(\d+)\] commit pc ([0-9a-fA-F]+) inst ([0-9a-fA-F]+) wen ([01]) dst (\d+) data [0-9a-fA-F]+ idx [0-9a-fA-F]+([^\n]*)$'
    for m in re.finditer(pattern,text,re.MULTILINE):
        slot=int(m[1]);require(0<=slot<32 and slot not in rows,'invalid/duplicate instruction trace slot')
        rows[slot]=(int(m[2],16),int(m[3],16),int(m[4]),int(m[5]))
        if '<--' in m[6]: ends.append(slot)
    require(len(ends)==1 and 0<count<=32,'missing latest instruction or unrepresentable commit group')
    slots=[(ends[0]-count+1+i)%32 for i in range(count)]
    require(all(i in rows for i in slots),'incomplete latest commit group')
    batch=[rows[i] for i in slots]
    # Fail closed if a fused/exception trace cannot be reconstructed exactly.
    require(batch[0][0]==group_pc,'commit count does not bind the displayed group')
    require(batch.count((pc,word,1,vd))==1,'injected vdot not uniquely present in failing group')
    return dict(status='EXPECTED_VDOT_HIGHBIT_REJECTION',vd=vd,pc=inj[2],word=inj[3],
                group_pc=hex(group_pc),group_instructions=count,bit=100)
