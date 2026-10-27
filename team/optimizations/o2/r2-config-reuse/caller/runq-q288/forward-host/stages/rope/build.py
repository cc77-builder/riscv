"""Capture actual original boundaries and build one bounded RoPE stage image."""
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
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('rope_math_build',HERE.parent/'target/build_smoke.py')
h,g=b.h,b.g
need,save,command=h.need,h.save,h.command
CONTRACT='r2-s3-rope-stage-v1'
FILES=('CONTRACT.md','rope.h','export.c','main.c','Makefile.target','build.py')
POSITIONS=[0,1,2,31,127,255]
def read(path):return json.loads(Path(path).read_text())
def digest(path):return h.sha(Path(path).read_bytes())
def fnv(raw):
    value=14695981039346656037
    for byte in raw:value=((value^byte)*1099511628211)&((1<<64)-1)
    return value

def kernels(upstream,output):
    source=h.gen.original(upstream)
    begin=source.index('        // RoPE relative positional encoding:')
    end=source.index('        // save key,value at this time step',begin)
    block=source[begin:end]
    need(block.count(h.gen.ANGLE)==1,'exact complete original angle expression')
    cached=block.replace(h.gen.ANGLE,h.gen.CACHED)
    need(cached.replace(h.gen.CACHED,h.gen.ANGLE)==block,'cached loop restores exact original bytes')
    prepare=h.gen.PREPARE.replace('    STAGE_TEST_CACHE(rope_cos, pos);\n','')
    text='#include "rope.h"\n#include <math.h>\n'
    for name,body in (('rope_original',block),('rope_cached',cached)):
        text+='__attribute__((noinline,noclone)) void '+name+'(struct rope_case *data,int pos) {\n'
        text+='    const int dim=ROPE_D,kv_dim=ROPE_D,head_size=48;\n'
        if name=='rope_cached':text+=h.gen.DECLARATION+prepare
        text+='    for(int l=0;l<ROPE_LAYERS;++l) {\n        struct rope_layer *s=&data->layer[l];\n'+body+'    }\n}\n'
    output.write_text(text)
    return dict(original_block_sha256=h.sha(block.encode()),source_block=block,
        restored_original_loop_equal=True,generated_sha256=digest(output),
        original_source_angle_evaluations=864,cached_source_angle_evaluations=24,table_logical_bytes=192)

def callsites(elf,metadata):
    rows={}
    for name in ('rope_original','rope_cached'):
        start,size,_,_=elf.symbols[name];found=[]
        for line in metadata.splitlines():
            parts=line.split()
            kinds=[x for x in ('R_RISCV_CALL','R_RISCV_CALL_PLT') if x in parts]
            if not kinds:continue
            pc=int(parts[0],16);index=parts.index(kinds[0])
            if start<=pc<start+size:
                symbol=parts[index+2];hi,lo=struct.unpack('<II',elf.read(pc,8))
                need(hi&127==0x17 and lo&0x707f==0x67 and (lo>>15)&31==(hi>>7)&31,'actual unrelaxed AUIPC/JALR call')
                high=hi&0xfffff000;high=high-(1<<32) if high&(1<<31) else high
                low=lo>>20;low=low-4096 if low&2048 else low
                need(pc+high+low==elf.symbols[symbol][0],'actual linked math call destination')
                found.append(dict(pc=hex(pc),symbol=symbol,target=hex(pc+high+low)))
        need({r['symbol'] for r in found}=={'powf','sinf','cosf'},'actual non-folded angle library call sites: '+name)
        need(len(found)==3,'one static angle call site per math function: '+name)
        rows[name]=dict(address=hex(start),bytes=size,calls=found)
    return rows

def executable(path,binary,metadata):
    """This smaller selected libm closure has one IE site, not smoke's two."""
    elf=g.ELF(path.read_bytes());need(elf.kind==2 and elf.entry==0x80000000,'static AM entry')
    need(all(n in elf.symbols for n in ('_start','main','_trm_init','_halt','_putc','team_math_main','rope_original','rope_cached')),'actual AM and both complete methods')
    need(not any(p[0] in (2,3) for p in elf.segments),'no dynamic runtime')
    need(not any((v[3]&15)==10 or (v[2]==0 and v[3]>>4==1) for v in elf.symbols.values()),'no IFUNC or unresolved strong symbol')
    for s in elf.sections:
        if s[1] in (4,9) and s[2]&2:need(s[1]==4 and s[9]==24 and s[5]%24==0 and elf.section(s)==bytes(s[5]),'only zero R_NONE runtime placeholders')
    tls=[p for p in elf.segments if p[0]==7]
    need(len(tls)==1 and tls[0][5:8]==(0,4,4),'exact zero errno TLS template')
    symbols={n:v for n,v in elf.symbols.items() if v[3]&15==6}
    need(set(symbols)=={'errno'} and symbols['errno'][0:2]==(0,4),'only four-byte errno at tp')
    index=symbols['errno'][2];need(elf.sections[index][1]==8 and elf.sections[index][2]&0x400,'actual errno TLS NOBITS')
    text=metadata.read_text()
    need('__tls_get_addr' not in elf.symbols and not any(x in text for x in ('TLS_GD','TLSDESC','IRELATIVE')),'static TLS only')
    sites=[]
    for line in text.splitlines():
        if 'R_RISCV_TLS_GOT_HI20' not in line:continue
        need('errno' in line,'only errno IE symbol');pc=int(line.split()[0],16);hi,lo=struct.unpack('<II',elf.read(pc,8))
        need(hi&127==0x17 and lo&0x707f==0x3003 and (lo>>15)&31==(hi>>7)&31,'actual AUIPC/LD IE pair')
        high=hi&0xfffff000;high=high-(1<<32) if high&(1<<31) else high
        low=lo>>20;low=low-4096 if low&2048 else low;got=pc+high+low
        need(struct.unpack('<q',elf.read(got,8))[0]==0,'actual final GOT errno offset')
        sites.append(dict(pc=hex(pc),got=hex(got),offset=0))
    need(len(sites)==1,'one actual errno IE site in the selected pow/sin/cos closure')
    sections=sorted((s for s in elf.sections if s[2]&2 and s[5] and not s[2]&0x400),key=lambda s:s[3])
    need(sections[0][3]==0x80000000,'raw RAM base')
    for s in sections:need(0x80000000<=s[3]<s[3]+s[5]<=0x88000000,'ordinary allocated section in RAM')
    for a,z in zip(sections,sections[1:]):need(a[3]+a[5]<=z[3],'ordinary allocated sections disjoint')
    raw=bytearray(max(s[3]+s[5] for s in sections)-0x80000000)
    for s in sections:
        if s[1]!=8:raw[s[3]-0x80000000:s[3]-0x80000000+s[5]]=elf.section(s)
    need(bytes(raw)==binary.read_bytes(),'complete raw BIN equals final ELF')
    area,length,_,_=elf.symbols['team_tls_area'];top=elf.symbols['_stack_top'][0]
    stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(length==96 and area%16==0 and stack%16==0 and area+length<=top<=stack<heap<0x88000000,'TLS, aligned stack and heap bounds')
    start,size,_,_=elf.symbols['team_math_main'];pc=start;counters=[]
    while pc<start+size:
        low=struct.unpack('<H',elf.read(pc,2))[0]
        if low&3!=3:pc+=2;continue
        insn=struct.unpack('<I',elf.read(pc,4))[0]
        if insn&0x707f==0x2073 and (insn>>15)&31==0 and insn>>20 in (0xc00,0xc02):
            need(struct.unpack('<I',elf.read(pc-4,4))[0]==0x0330000f and struct.unpack('<I',elf.read(pc+4,4))[0]==0x0330000f,'actual FENCE RW,RW before and after every counter')
            counters.append(dict(pc=hex(pc),csr=hex(insn>>20)))
        pc+=4
    need([x['csr'] for x in counters]==['0xc00','0xc02','0xc02','0xc00'],'actual complete cycle/retirement measurement sequence')
    return elf,dict(errno_offset=0,ie_sites=sites,counter_sites=counters,image_bytes=len(raw),stack_pointer=hex(stack),heap_start=hex(heap))

def build(output,math_build):
    need(not output.exists() and not output.is_relative_to(REPO) and not output.is_relative_to(math_build),'fresh isolated build')
    math=read(math_build/'result.json');need(math['status']=='MATH_SMOKE_STATIC_ELF_PASS_NOT_RUNTIME','fixed proven math closure')
    am=Path(math['am_home']);need(not output.is_relative_to(am),'official AM remains outside output')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','fixed official AM')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM unchanged')
    external=dict(math['external_pins'])
    for p,value in external.items():need(digest(p)==value,'frozen external dependency')
    archives=[p for p in external if Path(p).name=='libm.a'];need(len(archives)==1,'one fixed libm')
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=h.now())
    save(output/'state.json',state)
    try:
        paths=[*(HERE/n for n in FILES),HERE.parent/'full/state_layout.h',HERE.parent/'target/tls_main.S',
               HERE.parent/'target/build_smoke.py',REPO/'team/optimizations/o2/r2-safe-tail/linked_gate.py']
        pins=h.identity(REPO);pins.update({str(p.relative_to(REPO)):digest(p) for p in paths})
        source=output/'source';source.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest);need(digest(dest)==value,'frozen source snapshot')
        save(output/'source-pins.json',pins);save(output/'external-pins.json',external)
        forward=source/'repo'/h.Q/'forward-host';local=source/'repo'/HERE.relative_to(REPO)
        for name in ('export.c','main.c','rope.h'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(local/'Makefile.target',source/'Makefile')
        shutil.copyfile(forward/'stages/full/state_layout.h',source/'state_layout.h')
        shutil.copyfile(forward/'stages/target/tls_main.S',source/'tls_main.S')
        proof=h.gen.generate(forward/'upstream/runq.c',source/'forward.inc');save(output/'forward-generation.json',proof)
        crop=kernels(forward/'upstream/runq.c',source/'kernels.c');save(output/'kernel-generation.json',crop)
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf')}
        tools.update(host_gcc=shutil.which('gcc'),make=shutil.which('make'));need(all(tools.values()),'installed native tools')
        toolpins={n:dict(path=p,resolved=str(Path(p).resolve()),sha256=digest(p)) for n,p in tools.items()};save(output/'tools.json',toolpins)
        flags=['-std=gnu11','-O2','-fno-builtin','-ffp-contract=off','-fno-fast-math','-fno-lto','-fno-ipa-cp','-fno-ipa-icf','-fno-tree-vectorize','-fno-tree-slp-vectorize']
        command([tools['host_gcc'],*flags,source/'export.c',source/'kernels.c',source/'repo'/h.Q/'acc8/q288.c',
            '-I'+str(source),'-I'+str(forward),'-I'+str(forward.parent),'-I'+str(source/'repo'/h.Q.parent/'split'),
            '-I'+str(source/'repo'/h.Q.parent),'-lm','-o',output/'export-fixture'],output,'host-compile')
        fixture=output/'fixture';fixture.mkdir();command([output/'export-fixture',fixture],output,'host-export',timeout=180)
        lines=(output/'host-export.stdout.log').read_text().splitlines()
        need(len(lines)==7 and lines[-1]=='ROPE_EXPORT_PASS positions=256 captured=6 state_spans=16 bytes=165888','complete original boundary export')
        before=(fixture/'before.bin').read_bytes();after=(fixture/'after.bin').read_bytes()
        need(len(before)==len(after)==6*13824 and (fixture/'positions.bin').read_bytes()==struct.pack('<6I',*POSITIONS),'exact captured schema')
        cases=[]
        for i,p in enumerate(POSITIONS):
            a,z=before[i*13824:(i+1)*13824],after[i*13824:(i+1)*13824]
            need(lines[i]==f'ROPE_CAPTURE {i} {p} {fnv(a):016x} {fnv(z):016x}','independent complete host digest')
            cases.append(dict(index=i,position=p,before_sha256=h.sha(a),after_sha256=h.sha(z),after_fnv=f'{fnv(z):016x}'))
        command(['ldd',output/'export-fixture'],output,'host-libraries')
        hostlibs={str(Path(p).resolve()):digest(p) for p in re.findall(r'(/[^\s()]+)',(output/'host-libraries.stdout.log').read_text()) if Path(p).is_file()}
        asm=['.section .rodata.rope_fixture,"a"','.balign 64']
        for label in ('before','after','positions'):
            asm += [f'.global rope_{label}',f'rope_{label}:',f'.incbin "{fixture/(label+".bin")}"',f'.global rope_{label}_end',f'rope_{label}_end:','.balign 64']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={n:digest(source/n) for n in ('export.c','main.c','rope.h','Makefile','state_layout.h','tls_main.S','forward.inc','kernels.c','fixture.S')}
        need(actual['forward.inc']==proof['generated_sha256'] and actual['kernels.c']==crop['generated_sha256'],'actual compiled generated source identity')
        fixture_pins={p.name:digest(p) for p in fixture.iterdir()}
        save(output/'actual-source-pins.json',actual)
        keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        clean=['env',*[v for k in keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc'][:-3],'ROPE_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'rope-stage'),
            'MATH_ARCHIVE='+archives[0],'-o','am','-o','klib','-j1','image'],output,'target-build',timeout=180)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'rope-stage.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'rope-stage.elf'],output,'disassembly')
        elf,inspection=executable(output/'rope-stage.elf',output/'rope-stage.bin',output/'metadata.stdout.log')
        need(not any(v[2]==0 and v[3]>>4==1 for v in elf.symbols.values()),'no strong unresolved symbol')
        calls=callsites(elf,(output/'metadata.stdout.log').read_text())
        for label in ('before','after','positions'):
            address=elf.symbols['rope_'+label][0];end=elf.symbols['rope_'+label+'_end'][0];raw=(fixture/(label+'.bin')).read_bytes()
            need(end-address==len(raw) and elf.read(address,len(raw))==raw,'exact actual ELF boundary data')
        image=(output/'rope-stage.bin').read_bytes();offset=elf.symbols['rope_control'][0]-0x80000000
        need(image[offset:offset+4]==bytes(4),'normal immutable control')
        bad=bytearray(image);bad[offset:offset+4]=struct.pack('<I',1);(output/'bad-output.bin').write_bytes(bad)
        for p,value in external.items():need(digest(p)==value,'external remains fixed')
        for rel,value in pins.items():need(digest(REPO/rel)==value and digest(source/'repo'/rel)==value,'source remains fixed')
        for n,value in actual.items():need(digest(source/n)==value,'compiled source remains fixed')
        for n,value in fixture_pins.items():need(digest(fixture/n)==value,'capture remains fixed')
        for p,value in hostlibs.items():need(digest(p)==value,'host library remains fixed')
        for v in toolpins.values():need(digest(v['path'])==v['sha256'] and str(Path(v['path']).resolve())==v['resolved'],'tool remains fixed')
        inspection.update(status='ROPE_STAGE_STATIC_ELF_PASS_NOT_RUNTIME',contract=CONTRACT,source_pins=pins,
            actual_source_pins=actual,external_pins=external,host_libraries=hostlibs,fixtures=fixture_pins,cases=cases,
            artifacts={n:digest(output/n) for n in ('rope-stage.elf','rope-stage.bin','bad-output.bin','metadata.stdout.log','disassembly.stdout.log','forward-generation.json','kernel-generation.json')},
            actual_angle_calls=calls,selected_case=2,normal_control_offset=offset,am_home=str(am),target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=h.now();save(output/'state.json',state)

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('rope build interrupted')))
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--math-build',type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    r=build(a.output.resolve(),a.math_build.resolve());print(json.dumps({k:r[k] for k in ('status','cases','actual_angle_calls')},indent=2))
