#!/usr/bin/env python3
"""Build and reference-check N/P K768 using the frozen real W2 fixture."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = 'dot16-w2-np-reference-v1'
BASE = 0x80000000
ORDER = [0,1,2,2,1,2,1,1,2]
OLD_SHA = '279ceb03bcba0dcb5a2300e590952cb5e9b2acd8157ae55c804a053c1e1bca54'
GNU_SHA = '55aeba703f9f2f95c1c706ede993a9779b2e7e8966b2ce6678100ce750bedfc5'
ASM_SHA = 'fbe3a93f642ec3468da92ae776e1b547c29c527d4dffc30456191b437d1272c5'
MODEL_SHA = '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82'
HELPER_SHA = 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'
CHECKER_SHA = '9bc23d73550f0de16b2816fc732031f53dd81f6c9a483ce233ac2d2c4a7f41fa'
HW_SHA = 'e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f'
REF_SHA = 'cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae'
ABI = dict(bytes=1400,regs_int=0,regs_fp=256,csr=512,pc=656,hcsr=664,regs_vec=800,vcsr=1312,fcsr=1368,triggercsr=1376)
FLAGS = dict(VDOT_DOT16='1',VDOT_O2_ELASTIC='1',VDOT_T14_FUSED_INPUT='1',
             VDOT_O1_HANDOFF='0',VDOT_O1_TRACE='0',VDOT_O2_TRACE='0',VDOT_T12_TRACE='0',VDOT_T13_TRACE='0')
SIZES = {'input':768,'input-scales':96,'weight':221184,'packed':221184,
         'scales':27648,'gold':1152,'slot-gold':128,'expected-flags':4}
KERNELS = {'q768_dot16_whole8_narrow':(312,'b4a0e512feafd3ae8ea7e4531e13e1a23b12f97d80b3b007be6c52c3bdea56be'),
           'q768_paired16_rvv':(1096,'26f972751fb9882f92118ac30b98f2d0b4d1df9225be5d9cd136e7ed5c4629d3')}


def need(ok, message):
    if not ok: raise ValueError(message)


def read(path): return json.loads(Path(path).read_bytes())
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def stamp(): return datetime.now(timezone.utc).isoformat()
def save(path, value): Path(path).write_text(json.dumps(value,indent=2)+'\n')


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj)
    return obj


def fnv(raw):
    h=14695981039346656037
    for b in raw:h=((h^b)*1099511628211)&((1<<64)-1)
    return h


def replace_exact(text,before,after,count=1):
    need(text.count(before)==count and after not in text,'unique derivation '+before[:50])
    return text.replace(before,after)


def derive_main(raw):
    text=raw.decode();edits=[
        ('#include "w2.h"','#include "w2.h"\nextern const uint32_t w2_expected_flags[1];\nvoid q768_paired16_rvv(struct w2_context*);\nvoid q768_dot16_whole8_narrow(struct w2_context*);'),
        ('which==1?q768_fr:q768_ta','which==1?q768_paired16_rvv:q768_dot16_whole8_narrow'),
        ('check(fcsr()==1,"warm_flags")','check(fcsr()==w2_expected_flags[0],"warm_flags")'),
        ('check(flags==1,"flags")','check(flags==w2_expected_flags[0],"flags")')]
    for before,after in edits:text=replace_exact(text,before,after)
    restored=text
    for before,after in reversed(edits):restored=restored.replace(after,before,1)
    need(restored.encode()==raw,'exact original main recovered')
    return text,edits


def derive_checker(raw):
    text=raw.decode();tree=ast.parse(text)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate']
    need(len(nodes)==1,'one original complete validator')
    original=ast.get_source_segment(text,nodes[0])+'\n';changed=original
    edits=[("('input','input-scales','weight','packed','scales','gold','slot-gold')",
            "('input','input-scales','weight','packed','scales','gold','slot-gold','expected-flags')"),
           ('flags==1 and fnv==','flags==record[\'expected_flags\'] and fnv==')]
    for before,after in edits:changed=replace_exact(changed,before,after)
    restored=changed
    for before,after in reversed(edits):restored=restored.replace(after,before,1)
    need(restored==original,'original complete comparator recovered')
    namespace=dict(Path=Path,struct=struct,need=need,read=read,digest=digest,ORDER=ORDER)
    exec(compile(changed,'derived-original-w2-validator.py','exec'),namespace)
    return namespace['validate'],changed,edits


def inspect(elf, raw):
    data=elf.raw
    kind,entry=struct.unpack_from('<H',data,16)[0],struct.unpack_from('<Q',data,24)[0]
    need(kind==2 and entry==BASE,'static RV64 original AM entry')
    phoff=struct.unpack_from('<Q',data,32)[0];phsize,phnum=struct.unpack_from('<HH',data,54)
    segments=[struct.unpack_from('<IIQQQQQQ',data,phoff+i*phsize) for i in range(phnum)]
    need(not any(x[0] in (2,3,7) for x in segments),'no dynamic interpreter or TLS segment')
    alloc=sorted((s for s in elf.sections if s[2]&2 and s[5]),key=lambda s:s[3])
    need(alloc and alloc[0][3]==BASE,'RAM base')
    need(all(BASE<=s[3]<s[3]+s[5]<=0x88000000 for s in alloc),'whole allocation in RAM')
    need(all(a[3]+a[5]<=b[3] for a,b in zip(alloc,alloc[1:])),'disjoint sections')
    need(not any(s[1] in (4,9) and s[2]&2 and any(data[s[4]:s[4]+s[5]]) for s in elf.sections),'no live allocated relocations')
    image=bytearray(max(s[3]+s[5] for s in alloc)-BASE)
    for s in alloc:
        if s[1]!=8:image[s[3]-BASE:s[3]-BASE+s[5]]=data[s[4]:s[4]+s[5]]
    need(bytes(image)==raw,'complete actual ELF/BIN identity including BSS')
    for name in ('_start','team_forward_main','_putc','w2_scalar','full_success_trap','reject',*KERNELS):
        need(name in elf.symbols,'actual required symbol '+name)
    need('_trm_init' not in elf.symbols and 'q768_fr' not in elf.symbols and 'q768_ta' not in elf.symbols,'exact new executable routes')
    for name,(length,pin) in KERNELS.items():
        addr,size,_=elf.symbols[name];body=elf.symbol_data(name)
        need(size==length and sha(body)==pin,'complete linked GNU kernel identity '+name)
        need(any(s[0]==1 and s[1]&5==5 and s[3]<=addr<addr+size<=s[3]+s[5] for s in segments),'whole kernel in RX PT_LOAD')
    top=elf.symbols['_stack_top'][0];stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(stack%16==0 and len(image)+BASE<=top<=stack<heap<0x88000000,'data/stack/heap bounds')
    failure=elf.symbol_data('reject');addr=elf.symbols['reject'][0]
    need(len(failure)%4==0,'uncompressed exact reject extent')
    traps=[i for i in range(0,len(failure),4) if struct.unpack_from('<I',failure,i)[0]&127==0x6b]
    need(len(traps)==2 and all(i>=4 and failure[i-4:i+4]==struct.pack('<2I',0x05b00513,0x0005006b) for i in traps),'both exact rs1=a0 code91 traps')
    success=elf.symbols['full_success_trap'][0]
    need(raw[success-BASE:success-BASE+4]==struct.pack('<I',0x0000006b),'actual good trap')
    main=elf.symbol_data('team_forward_main');counters=[]
    for at in range(0,len(main)-3,4):
        w=struct.unpack_from('<I',main,at)[0]
        if w&0x707f==0x2073 and (w>>15)&31==0 and w>>20 in (0xc00,0xc02):
            need(at>=4 and main[at-4:at]==main[at+4:at+8]==struct.pack('<I',0x0ff0000f),'actual fenced counter sites')
            counters.append(w>>20)
    need(counters==[0xc00,0xc02,0xc02,0xc00],'ordered whole-kernel counter window')
    return dict(image_bytes=len(raw),failure_pcs=[addr+i for i in traps],success_pc=success,kernels={n:dict(address=elf.symbols[n][0],bytes=l,sha256=h) for n,(l,h) in KERNELS.items()})


def run(a):
    deadline=time.monotonic()+a.budget_seconds;os.sched_setaffinity(0,{a.cpu});os.setpriority(os.PRIO_PROCESS,0,5)
    here=Path(__file__).resolve().parent
    old,gnu,out,adapter,hwpath,template,support=(getattr(a,n).resolve() for n in ('old_build','gnu','output','adapter','hardware','reference_template','support_adapter_source'))
    need(not out.exists() and 180<=a.budget_seconds<=1800,'fresh output and finite budget')
    for p in (old,gnu,adapter,here,hwpath.parent,template.parent,support.parent):
        need(out!=p and not out.is_relative_to(p) and not p.is_relative_to(out),'separate source/output scopes')
    pins={}
    def pin(path,expected=None):
        p=Path(path).absolute();h=digest(p)
        need(expected is None or expected==h,'fixed input '+str(p))
        need(str(p) not in pins or pins[str(p)]==h,'consistent pin')
        pins[str(p)]=h;return p
    pin(old/'result.json',OLD_SHA);original=read(old/'result.json')
    need(original['status']=='W2_STATIC_GEOMETRY_AND_CAPTURE_PASS_NOT_RUNTIME','frozen real W2 origin')
    pin(gnu/'result.json',GNU_SHA);gr=read(gnu/'result.json')
    need(gr['status']=='K768_N_P_GNU_GEOMETRY_VERIFIED' and gr['all_pins_unchanged'] and gr['all_children_reaped'],'closed GNU geometry stage')
    pin(gnu/'w2_np.S',ASM_SHA);pin(gnu/'w2_np.elf','82497a4b17533ede1484ef88c9ccd27ea00dd0259586e7fb23925155acfe8591')
    pin(gnu/'inputs/model.py',MODEL_SHA);pin(gnu/'inputs/process_helper.py',HELPER_SHA)
    pin(template,CHECKER_SHA);pin(Path(__file__));pin(here/'REFERENCE_CONTRACT.md')
    for n in ('Makefile','entry.S','scalar.c','w2.h','main.c','upstream/runq.c'):pin(old/'source'/n,original['actual_source_pins'][n])
    for n,size in SIZES.items():
        p=pin(old/'fixture'/(n+'.bin'),original['fixtures'][n+'.bin']);need(p.stat().st_size==size,'fixture span '+n)
    need(128 not in (old/'fixture/input.bin').read_bytes(),'real fixture exercises P fast path')
    am=Path(original['am_home'])
    need(out!=am and not out.is_relative_to(am) and not am.is_relative_to(out),'output outside official AM')
    for p,h in original['external_pins'].items():
        if Path(p).is_relative_to(am):pin(p,h)
    for p in (am/'am').rglob('*.h'):pin(p)
    for p in (am/'libs/klib/include').rglob('*.h'):pin(p)
    pin(old/'tools.json');toolrec=read(old/'tools.json')
    for name in ('gcc','ld','ar','objcopy','objdump','readelf','nm','make'):pin(toolrec[name]['path'],toolrec[name]['sha256'])
    tools={k:v['path'] for k,v in toolrec.items()}
    pin('/usr/bin/riscv64-linux-gnu-as','30ab46dce94fa2120f9465dd2965784af831363f75fac42ea9999819f6d15953')
    pin(hwpath,HW_SHA);hw=read(hwpath)
    need(hw['status']=='DOT16_FULLCORE_SMOKE_PASS' and hw['qualification']['fixed_six_legal_case_fullcore_difftest'] is True
         and hw['abi']['actual_dynamic_difftest_passed'] is True and hw['abi']['layout']==ABI and hw['source_identity']['flags']==FLAGS,'actual fixed dot16 runtime ABI')
    for p,h in hw['runtime_inputs'].items():pin(p,h)
    refs=[p for p,h in hw['runtime_inputs'].items() if h==REF_SHA];need(len(refs)==1,'unique exact dot16 reference');reference=refs[0]
    pin(adapter/'build.json','afc535c9b4eaf64ca6c7ba3dafd5b7f93ac8b56d2f280060e892f2816a56669f')
    ar=read(adapter/'build.json');pin(adapter/'inputs.json',ar['inputs_sha256'])
    need(ar['status']=='REFERENCE_ADAPTER_BUILD_PASS','existing qualified adapter')
    for p,h in read(adapter/'inputs.json')['files'].items():pin(p,h)
    for n,h in ar['artifacts'].items():pin(adapter/n,h)
    pin(support,'6ea9a43ddfa4420f00c7e62f101035e1e7fbf85610e607c4d7762b96c803bd2b')
    need((adapter/'reference_runner.c').read_bytes()==support.read_bytes(),'same frozen support adapter source')
    compile_record=read(adapter/'compile.command.json')
    need(compile_record.get('exit_code')==0 and compile_record.get('status')=='exited' and compile_record.get('process_group_absent_after_exit') is True,'completed original adapter compile')
    out.mkdir(parents=True);source=out/'source';source.mkdir();snap=out/'inputs';snap.mkdir()
    snapshots={}
    def copy(p,dest):
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
        need(digest(dest)==pins[str(p.absolute())],'exact source snapshot');snapshots[str(dest)]=digest(dest)
    for n in ('Makefile','entry.S','scalar.c','w2.h','upstream/runq.c'):copy(old/'source'/n,source/n)
    for p,n in ((gnu/'inputs/model.py','model.py'),(gnu/'inputs/process_helper.py','process_helper.py'),(template,'original-reference.py'),
                (old/'source/main.c','original-main.c'),(Path(__file__),'qualify_np.py'),(here/'REFERENCE_CONTRACT.md','REFERENCE_CONTRACT.md')):copy(p,snap/n)
    copy(gnu/'w2_np.S',source/'w2.S')
    model=module(snap/'model.py','np_reference_elf');helper=module(snap/'process_helper.py','np_reference_process')
    main,main_edits=derive_main((snap/'original-main.c').read_bytes());(source/'main.c').write_text(main)
    validate,check_text,check_edits=derive_checker((snap/'original-reference.py').read_bytes());(out/'derived-validator.py').write_text(check_text)
    save(out/'derivation.json',dict(main_edits=main_edits,checker_edits=check_edits,original_reconstructed=True))
    result=dict(contract=CONTRACT,status='RUNNING',started=stamp(),commands=[],reference_runs=0,target_emu_runs=0,
        reference_qualified=False,target_runtime_qualified=False,performance_qualified=False,production_routes_modified=False,
        cpu_affinity=[a.cpu],nice=5,budget_seconds=a.budget_seconds,original_inputs=pins,snapshots=snapshots)
    save(out/'inputs.json',dict(originals=pins,snapshots=snapshots));save(out/'result.json',result)
    pending=[None]
    def interrupt(s,f):
        if pending[0] is None:pending[0]=s
    def check():
        if pending[0] is not None:raise InterruptedError('received signal '+str(pending[0]))
    signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
    env={**os.environ,'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
         'MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(out),'GIT_OPTIONAL_LOCKS':'0'}
    for k in ('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','MAKEFILES','MAKEOVERRIDES',
              'CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD','GIT_DIR','GIT_WORK_TREE'):env.pop(k,None)
    env.update(AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1',MAKEFLAGS='-j1')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=32*1024*1024
    need(hard==resource.RLIM_INFINITY or hard>=limit,'32MiB output file cap');resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    def command(label,argv,cwd=out,budget=120,expected=0,guest=False):
        check();remaining=deadline-time.monotonic();need(remaining>0,'total deadline before '+label)
        rec=dict(label=label,command=list(map(str,argv)),cwd=str(cwd),started=stamp(),budget_seconds=min(budget,remaining),
                 process_started=False,exit_code=None,cpu_affinity=sorted(os.sched_getaffinity(0)))
        result['commands'].append(rec);proc=None
        try:
            with (cwd/(('stdout' if guest else label)+'.log')).open('wb') as stdout,(cwd/(('stderr' if guest else label+'.stderr')+'.log')).open('wb') as stderr:
                proc=subprocess.Popen(rec['command'],cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
                rec.update(pid=proc.pid,process_started=True)
                if guest:result['reference_runs']+=1
                save(out/'result.json',result);until=time.monotonic()+rec['budget_seconds']
                while True:
                    check();left=until-time.monotonic()
                    if left<=0:rec['timed_out']=True;raise subprocess.TimeoutExpired(rec['command'],rec['budget_seconds'])
                    try:rec['exit_code']=proc.wait(timeout=min(.25,left));break
                    except subprocess.TimeoutExpired:continue
            need(rec['exit_code']==expected,label+' exit mismatch')
            need(not helper.group_exists(proc.pid),label+' residual process group')
        finally:
            if proc is not None:
                if helper.group_exists(proc.pid):rec['cleanup_complete']=helper.stop_group(proc)
                rec['direct_child_reaped']=proc.poll() is not None
                rec['process_group_absent_after_exit']=not helper.group_exists(proc.pid)
                rec['residual_process_group']=not rec['process_group_absent_after_exit']
            rec['finished']=stamp();save(out/'result.json',result)
            if guest:save(cwd/'result.json',rec)
        return rec
    generated={}
    try:
        views={};fixtures={}
        for kind in ('normal','edge'):
            view=out/'images'/kind;folder=view/'fixture';folder.mkdir(parents=True);views[kind]=view
            values={n:(old/'fixture'/(n+'.bin')).read_bytes() for n in SIZES}
            if kind=='edge':
                x=bytearray(768);w=bytearray(221184);x[751]=x[767]=128;w[287*768+751]=w[287*768+767]=128
                packed=b''.join(w[(t*8+r)*768+g*32:(t*8+r)*768+g*32+32] for t in range(36) for g in range(24) for r in range(8))
                gold=bytes(287*4)+struct.pack('<I',0x47000000);slots=bytes(7*16)+struct.pack('<4I',32768,0,0,0)
                need(packed.count(128)==2 and packed[221167]==packed[221183]==128,'last packed boundary pair')
                values=dict(input=bytes(x),weight=bytes(w),packed=packed,scales=struct.pack('<6912f',*([1.0]*6912)),
                    gold=gold,**{'input-scales':struct.pack('<24f',*([1.0]*24)),'slot-gold':slots,'expected-flags':bytes(4)})
            fixtures[kind]={}
            for n,size in SIZES.items():
                need(len(values[n])==size,'complete selected fixture '+kind+'/'+n)
                p=folder/(n+'.bin');p.write_bytes(values[n]);fixtures[kind][n+'.bin']=digest(p);generated[str(p)]=digest(p)
        asm=['.section .rodata.w2_fixture,"a"','.balign 64']
        for name in SIZES:
            symbol='w2_'+name.replace('-','_');p=views['normal']/'fixture'/(name+'.bin')
            asm += [f'.global {symbol}',f'{symbol}:',f'.incbin "{p}"',f'.global {symbol}_end',f'{symbol}_end:','.balign 64']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        for p in source.rglob('*'):
            if p.is_file():generated[str(p)]=digest(p)
        generated[str(out/'derived-validator.py')]=digest(out/'derived-validator.py')
        command('build',[tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc'][:-3],'W2_OBJ_ROOT='+str(out/'objects'),'BINARY='+str(out/'w2-np'),'-o','am','-o','klib','-j1','image'],budget=180)
        command('metadata',[tools['readelf'],'-W','-h','-A','-l','-s','-r',out/'w2-np.elf'],budget=30)
        command('disassembly',[tools['objdump'],'-drwC',out/'w2-np.elf'],budget=30)
        elf=model.ELF((out/'w2-np.elf').read_bytes());raw=(out/'w2-np.bin').read_bytes();inspection=inspect(elf,raw)
        offset,size,_=elf.symbols['w2_control'];offset-=BASE
        need(size==8 and raw[offset:offset+8]==struct.pack('<2I',0,1),'exact original control ABI')
        dumps=[]
        for name,size,file in (('w2_report',512,'report.bin'),('w2_samples',576,'samples.bin'),('output',1184,'output.bin'),('slots',160,'slots.bin')):
            addr,length,_=elf.symbols[name];need(length==size,'complete guarded object '+name);dumps.append((file,addr,size))
        fixture_ranges=[]
        for name,size in SIZES.items():
            symbol='w2_'+name.replace('-','_');addr=elf.symbols[symbol][0]
            need(elf.symbols[symbol+'_end'][0]-addr==size and raw[addr-BASE:addr-BASE+size]==(views['normal']/'fixture'/(name+'.bin')).read_bytes(),'linked full fixture '+name)
            dumps.append((name+'-after.bin',addr,size));fixture_ranges.append((name,addr-BASE,size))
        ordered=sorted((lo,lo+n) for _,lo,n in fixture_ranges)
        need(all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:])) and all(not (lo<offset+8 and offset<hi) for lo,hi in ordered),'nonoverlapping exact fixture/control ranges')
        plan=out/'dump-plan.txt';plan.write_text(''.join(f'{n} {addr:x} {size}\n' for n,addr,size in dumps))
        records={}
        for kind,view in views.items():
            image=bytearray(raw)
            for name,lo,n in fixture_ranges:image[lo:lo+n]=(view/'fixture'/(name+'.bin')).read_bytes()
            (view/'real-w2.bin').write_bytes(image)
            records[kind]=dict(contract=CONTRACT,fixture_kind=kind,fixtures=fixtures[kind],dump_plan=dumps,control_offset=offset,
                golden_fnv=f"{fnv((view/'fixture/gold.bin').read_bytes()):016x}",expected_flags=1 if kind=='normal' else 0)
            save(view/'record.json',records[kind]);generated[str(view/'real-w2.bin')]=digest(view/'real-w2.bin');generated[str(view/'record.json')]=digest(view/'record.json')
        for p in (out/'w2-np.elf',out/'w2-np.bin',plan):generated[str(p)]=digest(p)
        save(out/'static.json',dict(contract=CONTRACT,status='W2_NP_FROZEN_FIXTURE_STATIC_PASS_NOT_RUNTIME',inspection=inspection,
            records=records,fixture_ranges=fixture_ranges,source_identity=generated,reference=reference,reference_sha256=REF_SHA,
            abi=ABI,target_emu_runs=0,performance_qualified=False))
        validations={}
        for label,kind,negative in (('negative','normal',True),('normal','normal',False),('replay','normal',False),('edge','edge',False)):
            check();dest=out/'reference'/label;dest.mkdir(parents=True);view=views[kind];record=records[kind]
            image=bytearray((view/'real-w2.bin').read_bytes());image[offset:offset+8]=struct.pack('<2I',int(negative),0)
            (dest/'image.bin').write_bytes(image);image_sha=digest(dest/'image.bin')
            rec=command(label,[adapter/'reference-runner',reference,dest/'image.bin',dest,'builtin','100000000','180',plan,'1'],
                        cwd=dest,budget=210,expected=2 if negative else 0,guest=True)
            need(digest(dest/'image.bin')==image_sha,'exact selected deterministic image unchanged')
            actual=read(dest/'reference-result.json')
            need(actual['halt_pc'] in (inspection['failure_pcs'] if negative else [inspection['success_pc']])
                 and actual['pc']==actual['halt_pc']+4 and all(actual[x]==0 for x in ('mcause','mepc','mtval')),'actual intended trap and no exception')
            checked=validate(view,dest,record,rec,negative);checked.update(contract=CONTRACT,fixture_kind=kind)
            save(dest/'validation.json',checked);validations[label]=checked
            for p,h in {**pins,**snapshots,**generated}.items():need(digest(p)==h,'stable campaign input '+p)
            print(label,checked['status'],flush=True)
        need(validations['normal']==validations['replay'],'independent full exact reference replay')
        check();need(time.monotonic()<deadline,'total budget including final identity audit')
        need(result['reference_runs']==4 and all(x['direct_child_reaped'] and x['process_group_absent_after_exit'] for x in result['commands']),'all exact owned processes reaped')
        result.update(status='K768_N_P_REAL_FIXTURE_AND_EDGE_REFERENCE_PASS',reference_qualified=True,
            static_inspection=inspection,validations=validations,all_inputs_unchanged=True,all_children_reaped=True,
            application_performance_qualified=False)
    except BaseException as exc:
        result.update(status='FAILED',error=repr(exc));raise
    finally:
        result['finished']=stamp();save(out/'result.json',result)
    print(json.dumps({k:result[k] for k in ('status','reference_runs','reference_qualified','target_emu_runs','performance_qualified','started','finished')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('old-build','gnu','output','adapter','hardware','reference-template','support-adapter-source'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,choices=range(4),default=1)
    p.add_argument('--budget-seconds',type=int,default=1200)
    run(p.parse_args())
