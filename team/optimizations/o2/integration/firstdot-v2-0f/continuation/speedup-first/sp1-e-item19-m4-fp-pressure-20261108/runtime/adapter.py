"""New image binding around unchanged normal selector and strict negative mechanism."""
from pathlib import Path
import hashlib,json,re,struct
from common import need,read
import normal_adapter,negative_group,runtime_gate
from o2_cancel_selector import base
ROOT=Path(__file__).resolve().parent.parent
C=read(ROOT/'CONTRACT.json')
PC=read(ROOT/'runtime/PC_CONTRACT.json')
M=read(C['software_manifest']['path'])
ELF=Path(C['runtime']['elf']['path']).read_bytes()

def validate_pc_binding(pc, manifest):
    need(pc['software_manifest']==C['software_manifest'], 'PC manifest identity')
    need(pc['pc_roles']=={str(r['pc']):r for r in manifest['pc_roles']}, 'actual ELF manifest PC binding')
    need(pc['expected_retired_pc_sequence']==manifest['expected_retired_pc_sequence'], 'retired PC binding')
    need(pc['call_plan']==manifest['call_plan'] and pc['uart_protocol']==manifest['uart_protocol'], 'call/UART binding')
validate_pc_binding(PC,M)


def elf_read(pc,size):
    need(ELF[:6]==b'\x7fELF\x02\x01','ELF64 little endian')
    phoff=struct.unpack_from('<Q',ELF,32)[0];ents,n=struct.unpack_from('<HH',ELF,54)
    for i in range(n):
        typ,flags,off,addr,phy,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',ELF,phoff+i*ents)
        if typ==1 and addr<=pc and pc+size<=addr+filesz:return ELF[off+pc-addr:off+pc-addr+size]
    raise ValueError('PC outside ELF load bytes')

def image_gate(text,role):
    plain=runtime_gate.normalize_console(text)
    ref=C['runtime'][C['roles'][0 if role=='bit100' else 1]['reference']]['path']
    need(re.findall(r'^The image is ([^\n]+)$',plain,re.M)==[C['runtime']['bin']['path']],'exact image banner')
    need(re.findall(r'^The reference model is ([^\n]+)$',plain,re.M)==[ref],'exact role reference banner')
    need(plain.count('The first instruction of core 0 has commited. Difftest enabled.')==1,'live DiffTest banner')
    need(not re.search(r'O2_(?:STATE|SCHEMA|ACCEPT|RESPONSE|COMMIT)\b',plain),'foreign O2 hardware observer')
    return plain

def collect(text,role,exit_code):
    need(role in ('bit100','candidate-normal'),'two roles only')
    plain=image_gate(text,role)
    if role=='bit100':
        audit=base.analyze(plain,require_complete=False,local=False)
        events,uart=base.extract_events_and_uart(plain)
        fault=negative_group.validate_negative_group(plain,exit_code,C['guard'],elf_read,events)
        trigger=fault['trigger_commit']
        need((trigger['vs1'],trigger['vs2'])==(M['vs1_low64'],M['vs2_low64']),'guard frozen effective inputs')
        need(trigger['result']==int.from_bytes(bytes.fromhex(M['expected_dot128']),'little'),'guard full128 expected')
        need(len([e for e in events if e[2]=='COMMIT'])==1,'guard is unique first committed custom')
        need('OC19_SUMMARY' not in uart and 'OC19_FAIL' not in uart,'reject before completion')
        return {'status':'NEW_GUARD_BIT100_LOG_PASS','fault':fault,'observer':audit['counts'],'scope':'OFFLINE_LOG_REQUIRES_RUNTIME_RECEIPT','target_run_qualified':False}
    runtime_gate.validate_failure_markers(plain,False)
    result=normal_adapter.collect_normal(plain,PC,exit_code,require_hit=False)
    guest=re.findall(r'Guest cycle spent:[ \t]*([0-9]+)',plain)
    instr=re.findall(r'Core-0 instrCnt = ([0-9]+), cycleCnt = ([0-9]+)',plain)
    need(len(guest)==len(instr)==1,'one complete guest/instruction counter')
    result.update(guest_cycles=int(guest[0]),instruction_count=int(instr[0][0]),cycle_count=int(instr[0][1]),scope='OFFLINE_LOG_REQUIRES_RUNTIME_RECEIPT')
    return result
