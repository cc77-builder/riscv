"""Link API/target harnesses with the already qualified, unchanged consumer.o."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import shutil
import struct
import subprocess

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('consumer_aux_parent',HERE/'build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
need,read,save,digest,command=b.need,b.read,b.save,b.digest,b.command
CONTRACT='r2-s3-forward-consumer-target-v1'

def uart_executable(path,binary,metadata,errno_offset):
    """Explicit new TLS+UART profile; the earlier memory-only gate is unchanged."""
    elf=b.f.g.ELF(path.read_bytes());need(elf.kind==2 and elf.entry==0x80000000,'static team entry')
    need(all(p[0] not in (2,3) for p in elf.segments),'no dynamic runtime')
    need('_trm_init' not in elf.symbols and all(n in elf.symbols for n in ('_putc','printf_','team_forward_main')),
         'team TLS entry and original AM UART/klib linked')
    need(not any((v[3]&15)==10 or (v[2]==0 and v[3]>>4==1) for v in elf.symbols.values()),'no IFUNC or unresolved strong symbol')
    for s in elf.sections:
        if s[1] in (4,9) and s[2]&2:need(s[1]==4 and s[9]==24 and s[5]%24==0 and elf.section(s)==bytes(s[5]),'no live runtime relocation')
    tls=[p for p in elf.segments if p[0]==7];need(len(tls)==1 and tls[0][5:8]==(0,4,4),'same zero errno TLS template')
    symbols={n:v for n,v in elf.symbols.items() if v[3]&15==6}
    need('errno' in symbols and symbols['errno'][0:2]==(errno_offset,4),'same actual TLS offset')
    aliases={n:v for n,v in symbols.items() if n!='errno'}
    need(all(v[0]==errno_offset and v[1]==0 and v[2]==symbols['errno'][2] and v[3]>>4==0 for v in aliases.values()),'only local aliases of same errno')
    need('__tls_get_addr' not in elf.symbols and not any(n in metadata.read_text() for n in ('TLS_GD','TLSDESC','IRELATIVE')),'bounded static TLS model')
    sites=[]
    for line in metadata.read_text().splitlines():
        if 'R_RISCV_TLS_GOT_HI20' not in line:continue
        need('errno' in line,'only errno IE site');pc=int(line.split()[0],16)
        hi,lo=struct.unpack('<II',elf.read(pc,8))
        need(hi&127==0x17 and lo&0x707f==0x3003 and (lo>>15)&31==(hi>>7)&31,'actual AUIPC/LD TLS pair')
        high=hi&0xfffff000;high=high-(1<<32) if high&(1<<31) else high
        low=lo>>20;low=low-4096 if low&2048 else low;got=pc+high+low
        need(struct.unpack('<q',elf.read(got,8))[0]==errno_offset,'actual IE offset');sites.append(dict(pc=hex(pc),got=hex(got),offset=errno_offset))
    need(len(sites)==2,'same two libm TLS sites')
    sections=sorted((s for s in elf.sections if s[2]&2 and s[5] and not s[2]&0x400),key=lambda s:s[3])
    need(sections[0][3]==0x80000000,'raw base')
    for s in sections:need(0x80000000<=s[3]<s[3]+s[5]<=0x88000000,'whole section in RAM')
    for a,c in zip(sections,sections[1:]):need(a[3]+a[5]<=c[3],'disjoint sections')
    raw=bytearray(max(s[3]+s[5] for s in sections)-0x80000000)
    for s in sections:
        if s[1]!=8:raw[s[3]-0x80000000:s[3]-0x80000000+s[5]]=elf.section(s)
    need(bytes(raw)==binary.read_bytes(),'complete ELF/raw image equality')
    area,length,_,_=elf.symbols['team_tls_area'];top=elf.symbols['_stack_top'][0]
    stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(length==96 and area%16==0 and area+length<=top<=stack<heap<0x88000000 and stack%16==0,'TLS/stack/heap bounds')
    start,size,_,_=elf.symbols['team_forward_main'];pc=start;counters=[]
    while pc<start+size:
        low=struct.unpack('<H',elf.read(pc,2))[0]
        if low&3!=3:pc+=2;continue
        word=struct.unpack('<I',elf.read(pc,4))[0]
        if word&0x707f==0x2073 and (word>>15)&31==0 and word>>20 in (0xc00,0xc02):
            need(elf.read(pc-4,4)==elf.read(pc+4,4)==struct.pack('<I',0x0ff0000f),'IORW fence around each actual counter read')
            counters.append(dict(pc=hex(pc),csr=hex(word>>20)))
        pc+=4
    need([x['csr'] for x in counters]==['0xc00','0xc02','0xc02','0xc00'],'exact actual four-read measurement order')
    return elf,dict(tls_errno_offset=errno_offset,tls_sites=sites,tls_local_aliases=aliases,
                    counter_sites=counters,image_bytes=len(raw),heap_start=hex(heap))

def build(output,parent,campaign,kind):
    record=read(parent/'result.json');qualified=read(campaign/'results.json');state=read(campaign/'state.json')
    need(record['contract']==b.CONTRACT and record['status']=='PURE_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME','fixed pure consumer')
    need(qualified['status']==state['status']=='PURE_FORWARD_REFERENCE_CAMPAIGN_PASS' and not state['active'] and not state.get('cleanup_unknown'),'completed pure-reference qualification')
    am=Path(record['am_home']);need(not output.exists() and not any(output.is_relative_to(p) for p in (b.REPO,parent,campaign,am)),'fresh isolated harness output')
    runtime=read(campaign/'runtime-inputs.json');external=dict(record['external_pins'])
    if kind=='target':
        for folder in ('am/include','am/src/nemu/include','am/src/xs/include','libs/klib/include'):
            for header in (am/folder).rglob('*.h'):external[str(header)]=digest(header)
    for name,value in record['artifacts'].items():
        path=parent/name;need(digest(path)==value==runtime[str(path)],'same actually qualified consumer artifact');external[str(path)]=value
    for name,value in record['fixtures'].items():external[str(parent/'fixture'/name)]=value
    for name,value in record['actual_source_pins'].items():external[str(parent/'source'/name)]=value
    for p in (parent/'result.json',campaign/'results.json',campaign/'state.json',campaign/'runtime-inputs.json'):
        external[str(p)]=digest(p)
    pins=dict(record['source_pins'])
    for p in (HERE/'aux_build.py',HERE/(kind+'_main.c'),HERE/'TARGET-CONTRACT.md'):pins[str(p.relative_to(b.REPO))]=digest(p)
    for rel,value in pins.items():need(digest(b.REPO/rel)==value,'unchanged inherited source')
    for path,value in external.items():need(digest(path)==value,'fixed external input')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','original AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM unchanged')
    output.mkdir(parents=True);status=dict(contract=CONTRACT,kind=kind,status='BUILDING',started=b.f.h.now());save(output/'state.json',status)
    try:
        source=output/'source';source.mkdir();fixture=output/'fixture';fixture.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b.REPO/rel,dest);need(digest(dest)==value,'exact source snapshot')
        for name,value in record['fixtures'].items():shutil.copyfile(parent/'fixture'/name,fixture/name);need(digest(fixture/name)==value,'exact frozen model/gold copy')
        for name in ('entry.S','fused.S','q288.c','q288.h','split.h','caller.h','consumer.h'):
            shutil.copyfile(parent/'source'/name,source/name)
        shutil.copyfile(parent/'consumer.o',source/'consumer.o')
        shutil.copyfile(source/'repo'/HERE.relative_to(b.REPO)/(kind+'_main.c'),source/'main.c')
        make=(parent/'source/Makefile').read_text().replace('NAME = forward-consumer','NAME = consumer-'+kind).replace('SRCS = main.c consumer.c','SRCS = main.c')
        make=make.replace('LINK_FILES += $(MATH_ARCHIVE)','LINK_FILES += $(CURDIR)/consumer.o $(MATH_ARCHIVE)')
        need('consumer.c' not in make and '$(CURDIR)/consumer.o $(MATH_ARCHIVE)' in make,'link actual qualified object without recompilation')
        (source/'Makefile').write_text(make)
        asm=['.section .rodata.fixture,"a"','.balign 16'];embedded=[('weights','weights.bin'),('embedding','embedding.bin'),('packed','packed.bin'),('tail_scales','tail-scales.bin')]
        if kind=='target':embedded.append(('gold','host-state-p0.bin'))
        for label,name in embedded:
            asm += [f'.global fixture_{label}',f'fixture_{label}:',f'.incbin "{fixture/name}"',f'.global fixture_{label}_end',f'fixture_{label}_end:','.balign 16']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file() and not p.is_relative_to(source/'repo')}
        save(output/'actual-source-pins.json',actual);save(output/'source-pins.json',pins);save(output/'external-pins.json',external)
        tools=read(parent/'tools.json');save(output/'tools.json',tools)
        for tool in tools.values():need(digest(tool['path'])==tool['sha256'],'same qualified tool')
        keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        clean=['env',*[v for k in keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        archives=[n for n in external if Path(n).name=='libm.a'];need(len(archives)==1,'same libm archive')
        name='consumer-'+kind
        command([*clean,tools['make']['path'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc']['path'][:-3],'FORWARD_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/name),
            'MATH_ARCHIVE='+archives[0],'FULL_ERRNO_OFFSET='+str(record['tls_errno_offset']),'-o','am','-o','klib','-j1','image'],output,'target-build',timeout=300)
        command([tools['readelf']['path'],'-W','-h','-A','-l','-s','-r',output/(name+'.elf')],output,'metadata')
        command([tools['objdump']['path'],'-drwC',output/(name+'.elf')],output,'disassembly')
        inspect=uart_executable if kind=='target' else b.f.executable
        elf,inspection=inspect(output/(name+'.elf'),output/(name+'.bin'),output/'metadata.stdout.log',record['tls_errno_offset'])
        funcs=b.p.kernel_bytes(output/(name+'.elf'),record['kernel_identity']['functions'])
        for function,raw in funcs.items():need(len(raw)==record['kernel_identity']['functions'][function]['bytes'] and b.f.h.sha(raw)==record['kernel_identity']['functions'][function]['sha256'],'same whole FR/TA function')
        need(digest(source/'consumer.o')==record['artifacts']['consumer.o'] and not list((output/'objects').rglob('consumer.o')),'actual shared object not rebuilt')
        plans=[];image=(output/(name+'.bin')).read_bytes()
        observed=[('api_report','report.bin',512),('api_states','states.bin',2*(b.STATE_BYTES+32)),('api_snapshots','snapshots.bin',12*b.STATE_BYTES)] if kind=='api' else [('target_report','report.bin',512),('target_state','state.bin',b.STATE_BYTES)]
        for symbol,filename,size in observed:
            address,length,_,_=elf.symbols[symbol];need(length==size and image[address-0x80000000:address-0x80000000+size]==bytes(size),'complete zero initialized storage');plans.append((filename,address,size))
        for label,filename in embedded:
            address=elf.symbols['fixture_'+label][0];raw=(fixture/filename).read_bytes()
            need(elf.symbols['fixture_'+label+'_end'][0]-address==len(raw) and elf.read(address,len(raw))==raw,'complete actual linked model/gold')
            if label!='gold':plans.append((filename.replace('.bin','-after.bin'),address,len(raw)))
        if kind=='target':
            offset=elf.symbols['target_control'][0]-0x80000000
            need(elf.symbols['target_control'][1]==12 and image[offset:offset+12]==struct.pack('<3I',4,0,1),'only explicit target controls')
            inspection['control_offset']=offset
        (output/'dump-plan.txt').write_text(''.join(f'{n} {a:x} {s}\n' for n,a,s in plans))
        for path,value in external.items():need(digest(path)==value,'unchanged external input')
        for rel,value in pins.items():need(digest(b.REPO/rel)==value and digest(source/'repo'/rel)==value,'unchanged source identity')
        for n,value in actual.items():need(digest(source/n)==value,'unchanged actual input')
        for n,value in record['fixtures'].items():need(digest(fixture/n)==value,'unchanged fixture')
        for tool in tools.values():need(digest(tool['path'])==tool['sha256'],'unchanged tool')
        inspection.update(status='SHARED_CONSUMER_HARNESS_STATIC_PASS_NOT_RUNTIME',contract=CONTRACT,kind=kind,source_pins=pins,
            actual_source_pins=actual,external_pins=external,fixtures=record['fixtures'],kernel_identity=record['kernel_identity'],
            qualified_consumer_object_sha256=record['artifacts']['consumer.o'],am_home=str(am),dump_plan=plans,
            qualified_build=str(parent),qualified_campaign=str(campaign),
            artifacts={n:digest(output/n) for n in (name+'.elf',name+'.bin','dump-plan.txt','metadata.stdout.log','disassembly.stdout.log')},
            reference_runs=0,target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);status.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:status.update(status='FAILED',error=repr(error));raise
    finally:status['finished']=b.f.h.now();save(output/'state.json',status)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('output','parent','campaign'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--kind',choices=('api','target'),required=True);args=parser.parse_args()
    os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    result=build(args.output.resolve(),args.parent.resolve(),args.campaign.resolve(),args.kind)
    print(json.dumps({n:result[n] for n in ('status','kind','image_bytes','heap_start','qualified_consumer_object_sha256')},indent=2))
