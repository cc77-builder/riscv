"""Build a complete memory-only RISC-V consumer from unchanged source/fixture."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import shutil
import signal
import struct
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[8]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('full_memory_commands',HERE.parent/'check.py')
g=load('full_memory_elf_reader',REPO/'team/optimizations/o2/r2-safe-tail/linked_gate.py')
need,save,sha,command=h.need,h.save,h.sha,h.command
CONTRACT='r2-s3-forward-memory-v1'
Q=h.Q
FILES=('build.py','state_layout.h','export.c','forward_main.c','entry.S','Makefile.target','CONTRACT.md')

def read(p):return json.loads(Path(p).read_text())
def digest(p):return sha(Path(p).read_bytes())

def executable(elf_path,bin_path,metadata,errno_offset):
    elf=g.ELF(elf_path.read_bytes());need(elf.kind==2 and elf.entry==0x80000000,'actual static entry')
    need(all(p[0] not in (2,3) for p in elf.segments),'no dynamic runtime')
    need('_trm_init' not in elf.symbols and '_putc' not in elf.symbols and 'team_forward_main' in elf.symbols,'memory-only entry; no official startup or UART linked')
    need(not any((v[3]&15)==10 or (v[2]==0 and v[3]>>4==1) for v in elf.symbols.values()),'no IFUNC or unresolved strong symbol')
    for s in elf.sections:
        if s[1] in (4,9) and s[2]&2:need(s[1]==4 and s[9]==24 and s[5]%24==0 and elf.section(s)==bytes(s[5]),'no live runtime relocation')
    tls=[p for p in elf.segments if p[0]==7];need(len(tls)==1 and tls[0][5:8]==(0,4,4),'exact zero errno TLS template')
    symbols={n:v for n,v in elf.symbols.items() if v[3]&15==6}
    need('errno' in symbols and symbols['errno'][0:2]==(errno_offset,4),'actual TLS offset unchanged')
    # -fdata-sections can retain a zero-size LOCAL .LANCHOR for this same object.
    aliases={n:v for n,v in symbols.items() if n!='errno'}
    need(all(v[0]==errno_offset and v[1]==0 and v[2]==symbols['errno'][2] and v[3]>>4==0 for v in aliases.values()),
         'only zero-size local aliases of the same errno object')
    need('__tls_get_addr' not in elf.symbols and not any(n in metadata.read_text() for n in ('TLS_GD','TLSDESC','IRELATIVE')),'bounded static TLS model')
    sites=[]
    for line in metadata.read_text().splitlines():
        if 'R_RISCV_TLS_GOT_HI20' not in line:continue
        need('errno' in line,'only errno IE site');pc=int(line.split()[0],16)
        hi,lo=struct.unpack('<II',elf.read(pc,8))
        need(hi&127==0x17 and lo&0x707f==0x3003 and (lo>>15)&31==(hi>>7)&31,'resolved AUIPC/LD TLS pair')
        high=hi&0xfffff000;high=high-(1<<32) if high&(1<<31) else high
        low=lo>>20;low=low-4096 if low&2048 else low;got=pc+high+low
        need(struct.unpack('<q',elf.read(got,8))[0]==errno_offset,'actual IE offset')
        sites.append(dict(pc=hex(pc),got=hex(got),offset=errno_offset))
    need(len(sites)==2,'same two libm TLS accesses')
    sections=sorted((s for s in elf.sections if s[2]&2 and s[5] and not s[2]&0x400),key=lambda s:s[3])
    need(sections[0][3]==0x80000000,'raw base')
    for s in sections:need(0x80000000<=s[3]<s[3]+s[5]<=0x88000000,'ordinary section in RAM')
    for a,b in zip(sections,sections[1:]):need(a[3]+a[5]<=b[3],'ordinary sections disjoint')
    raw=bytearray(max(s[3]+s[5] for s in sections)-0x80000000)
    for s in sections:
        if s[1]!=8:raw[s[3]-0x80000000:s[3]-0x80000000+s[5]]=elf.section(s)
    need(bytes(raw)==bin_path.read_bytes(),'complete raw image equals actual ELF')
    area,length,_,_=elf.symbols['team_tls_area']
    stacktop=elf.symbols['_stack_top'][0];stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(length==96 and area%16==0 and area+length<=stacktop<=stack<heap<0x88000000,'TLS, stack and heap bounds')
    return elf,dict(status='FULL_MEMORY_STATIC_ELF_PASS_NOT_RUNTIME',tls_errno_offset=errno_offset,
                    tls_sites=sites,tls_local_aliases=aliases,image_bytes=len(raw),heap_start=hex(heap))

def build(output,math_build):
    need(not output.exists() and not output.is_relative_to(REPO) and not output.is_relative_to(math_build),'new isolated build')
    math=read(math_build/'result.json');need(math['status']=='MATH_SMOKE_STATIC_ELF_PASS_NOT_RUNTIME','fixed math closure build')
    am=Path(math['am_home']);need(not output.is_relative_to(am),'official AM protected')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','original AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM remains unchanged')
    external=dict(math['external_pins'])
    for p,value in external.items():need(digest(p)==value,'fixed external: '+p)
    archives=[Path(p) for p in external if Path(p).name=='libm.a'];need(len(archives)==1,'fixed libm archive')
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=h.now(),target_runtime_ready=False)
    save(output/'state.json',state)
    try:
        pins=h.identity(REPO)
        pins.update({str(p.relative_to(REPO)):digest(p) for p in [*(HERE/n for n in FILES),REPO/'team/optimizations/o2/r2-safe-tail/linked_gate.py']})
        source=output/'source';source.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest)
            need(digest(dest)==value,'exact build source snapshot')
        save(output/'source-pins.json',pins);save(output/'external-pins.json',external)
        local=source/'repo'/HERE.relative_to(REPO);forward=source/'repo'/Q/'forward-host'
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf')}
        tools.update(host_gcc=shutil.which('gcc'),make=shutil.which('make'))
        need(all(tools.values()),'native installed toolchain')
        toolpins={n:dict(path=p,sha256=digest(p),resolved=str(Path(p).resolve())) for n,p in tools.items()};save(output/'tools.json',toolpins)
        flags=['-std=gnu11','-O2','-fno-builtin','-ffp-contract=off','-fno-fast-math','-fno-lto','-fno-tree-vectorize','-fno-tree-slp-vectorize']
        command([tools['host_gcc'],*flags,local/'export.c',source/'repo'/Q/'acc8/q288.c','-I'+str(forward),'-I'+str(forward.parent),
                 '-I'+str(source/'repo'/Q.parent/'split'),'-I'+str(source/'repo'/Q.parent),'-lm','-o',output/'export-fixture'],output,'host-compile')
        fixture=output/'fixture';fixture.mkdir();command([output/'export-fixture',fixture],output,'host-export',timeout=180)
        need((output/'host-export.stdout.log').read_text()=='FULL_EXPORT_PASS positions=3 weights=17101440 embedding=36864000 state=3691424\n','complete native host reference export')
        command(['ldd',output/'export-fixture'],output,'host-libraries')
        hostlibs={str(Path(p).resolve()):digest(p) for p in re.findall(r'(/[^\s()]+)',(output/'host-libraries.stdout.log').read_text()) if Path(p).is_file()}
        for name in ('forward_main.c','entry.S','state_layout.h'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(local/'Makefile.target',source/'Makefile')
        (source/'upstream').mkdir();shutil.copyfile(forward/'upstream/runq.c',source/'upstream/runq.c')
        generator=load('snapshot_forward_generator',forward/'stages/generate.py')
        generated=generator.generate(source/'upstream/runq.c',source/'forward.inc');save(output/'generated.json',generated)
        asm=['.section .rodata.fixture,"a"','.balign 16']
        for label,name in (('weights','weights.bin'),('embedding','embedding.bin')):
            asm += [f'.global fixture_{label}',f'fixture_{label}:',f'.incbin "{fixture/name}"',f'.global fixture_{label}_end',f'fixture_{label}_end:','.balign 16']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual_sources={n:digest(source/n) for n in ('forward_main.c','entry.S','state_layout.h','Makefile','upstream/runq.c','forward.inc','fixture.S')}
        fixture_pins={p.name:digest(p) for p in fixture.iterdir() if p.is_file()}
        need(actual_sources['forward.inc']==generated['generated_sha256'],'actual generated fragment bound to source restoration proof')
        save(output/'actual-source-pins.json',actual_sources)
        clean_keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        clean=['env',*[v for k in clean_keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
                 'CROSS_COMPILE='+tools['gcc'][:-3],'FORWARD_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'forward-memory'),
                 'MATH_ARCHIVE='+str(archives[0]),'FULL_ERRNO_OFFSET='+str(math['errno_offset']),'-o','am','-o','klib','-j1','image'],output,'target-build',timeout=240)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'forward-memory.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'forward-memory.elf'],output,'disassembly')
        elf,inspection=executable(output/'forward-memory.elf',output/'forward-memory.bin',output/'metadata.stdout.log',math['errno_offset'])
        plans=[]
        for symbol,name,expected_bytes in (('full_report','report.bin',256),('full_snapshots','snapshots.bin',6*3691424),('full_events','events.bin',3*120*8)):
            address,size,_,_=elf.symbols[symbol];need(size==expected_bytes,'full data symbol extent');plans.append((name,address,size))
        for symbol,name,expected_bytes in (('fixture_weights','weights-after.bin',17101440),('fixture_embedding','embedding-after.bin',36864000)):
            address=elf.symbols[symbol][0];end=elf.symbols[symbol+'_end'][0];need(end-address==expected_bytes,'embedded full fixture extent')
            original='weights.bin' if 'weights' in symbol else 'embedding.bin'
            need(elf.read(address,expected_bytes)==(fixture/original).read_bytes(),'exact compiled complete fixture')
            plans.append((name,address,expected_bytes))
        (output/'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name,address,size in plans))
        image=(output/'forward-memory.bin').read_bytes();offset=elf.symbols['full_control'][0]-0x80000000
        need(image[offset:offset+4]==bytes(4),'normal data control')
        damaged=bytearray(image);damaged[offset:offset+4]=struct.pack('<I',1);(output/'bad-state.bin').write_bytes(damaged)
        for p,value in external.items():need(digest(p)==value,'external input remains unchanged')
        for rel,value in pins.items():need(digest(REPO/rel)==value and digest(source/'repo'/rel)==value,'source remains unchanged')
        for p,value in hostlibs.items():need(digest(p)==value,'native host library remains unchanged')
        for tool in toolpins.values():need(digest(tool['path'])==tool['sha256'],'tool remains unchanged')
        for n,value in actual_sources.items():need(digest(source/n)==value,'actual compiled source remains unchanged: '+n)
        for n,value in fixture_pins.items():need(digest(fixture/n)==value,'actual host fixture/golden remains unchanged: '+n)
        inspection.update(contract=CONTRACT,source_pins=pins,external_pins=external,host_libraries=hostlibs,
                          artifacts={n:digest(output/n) for n in ('forward-memory.elf','forward-memory.bin','bad-state.bin','dump-plan.txt')},
                          fixtures=fixture_pins,actual_source_pins=actual_sources,dump_plan=plans,
                          normal_control_offset=offset,source_generated=generated,am_home=str(am),reference_runs=0,
                          target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'))
        return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=h.now();save(output/'state.json',state)

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('full build signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--math-build',type=Path,required=True)
    args=p.parse_args();os.sched_setaffinity(0,[sorted(os.sched_getaffinity(0))[min(1,len(os.sched_getaffinity(0))-1)]])
    result=build(args.output.resolve(),args.math_build.resolve());print(json.dumps({k:result[k] for k in ('status','image_bytes','heap_start','reference_runs','performance_qualified')},indent=2))
