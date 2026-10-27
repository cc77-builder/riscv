"""Build a new real W2 boundary without changing any frozen input."""
from pathlib import Path
import argparse, importlib.util, json, os, re, shutil, signal, struct, subprocess, sys, types

HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('w2_boundary_support',HERE.parent/'projection/target/build.py')
gen=load('w2_generator',HERE/'generate.py')
REPO=old.REPO
need,save,read,digest,command=old.need,old.save,old.read,old.digest,old.command
CONTRACT=gen.CONTRACT
FILES=('build.py','generate.py','w2.h','scalar.c','main.c','export.c','Makefile.target','CONTRACT.md')
BASE=0x80000000

def executable(path,binary):
    elf=old.g.ELF(path.read_bytes());need(elf.kind==2 and elf.entry==BASE,'static original AM entry')
    need('_trm_init' not in elf.symbols and all(n in elf.symbols for n in ('_start','team_forward_main','_putc','q768_fr','q768_ta','w2_scalar')),'team entry with real original AM UART and kernels')
    reject_pc,reject_size,*_=elf.symbols['reject'];reject_bytes=elf.read(reject_pc,reject_size)
    need(reject_size%4==0,'fixed uncompressed rejection function')
    trap_sites=[i for i in range(0,reject_size,4) if struct.unpack('<I',reject_bytes[i:i+4])[0]&127==0x6b]
    need(len(trap_sites)==2 and all(i>=4 and reject_bytes[i-4:i+4]==struct.pack('<2I',0x05b00513,0x0005006b) for i in trap_sites),
         'both UART paths encode rs1=a0 after loading code91, as original AM')
    need(not any(p[0] in (2,3,7) for p in elf.segments),'no dynamic runtime/TLS dependency')
    need(not any((v[3]&15)==10 or (v[2]==0 and v[3]>>4==1) for v in elf.symbols.values()),'no IFUNC/unresolved strong symbol')
    for s in elf.sections:
        if s[1] in (4,9) and s[2]&2:need(s[1]==4 and s[9]==24 and s[5]%24==0 and elf.section(s)==bytes(s[5]),'no live runtime relocation')
    sections=sorted((s for s in elf.sections if s[2]&2 and s[5]),key=lambda s:s[3]);need(sections[0][3]==BASE,'RAM base')
    for s in sections:need(BASE<=s[3]<s[3]+s[5]<=0x88000000,'whole allocation inside RAM')
    for a,z in zip(sections,sections[1:]):need(a[3]+a[5]<=z[3],'disjoint allocated sections')
    raw=bytearray(max(s[3]+s[5] for s in sections)-BASE)
    for s in sections:
        if s[1]!=8:raw[s[3]-BASE:s[3]-BASE+s[5]]=elf.section(s)
    need(bytes(raw)==binary.read_bytes(),'whole final ELF/raw BIN identity')
    top=elf.symbols['_stack_top'][0];stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(stack%16==0 and max(s[3]+s[5] for s in sections)<=top<=stack<heap<0x88000000,'data/stack/heap bounds')
    pc,size,*_=elf.symbols['team_forward_main'];end=pc+size;sites=[]
    while pc<end:
        low=struct.unpack('<H',elf.read(pc,2))[0]
        if low&3!=3:pc+=2;continue
        word=struct.unpack('<I',elf.read(pc,4))[0]
        if word&0x707f==0x2073 and (word>>15)&31==0 and word>>20 in (0xc00,0xc02):
            need(elf.read(pc-4,4)==elf.read(pc+4,4)==struct.pack('<I',0x0ff0000f),'actual fences surround each counter')
            sites.append(dict(pc=hex(pc),csr=hex(word>>20)))
        pc+=4
    need([x['csr'] for x in sites]==['0xc00','0xc02','0xc02','0xc00'],'four actual ordered counter sites')
    return elf,dict(image_bytes=len(raw),heap_start=hex(heap),counter_sites=sites,
        failure_traps=[dict(pc=hex(reject_pc+i),word='0x0005006b',rs1='a0',code=91) for i in trap_sites])

def geometry_proof(elf,parent_path,output):
    parent=old.g.ELF(parent_path.read_bytes());records={};path=[]
    # Exact addi encodings; all other words including branches/FP remain equal.
    def addi(rd,rs,value):return ((value&4095)<<20)|(rs<<15)|(rd<<7)|0x13
    changes={addi(28,0,36):addi(28,0,96),addi(6,0,9):addi(6,0,24),addi(14,14,252):addi(14,14,672)}
    for name,original in (('q768_fr','q288_fused_rvv4'),('q768_ta','q288_tail_vdot')):
        a,n,*_=elf.symbols[name];pa,pn,*_=parent.symbols[original];need(n==pn and n%4==0,'same complete function extent')
        before=list(struct.unpack('<'+str(n//4)+'I',parent.read(pa,n)));after=list(struct.unpack('<'+str(n//4)+'I',elf.read(a,n)))
        diffs=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
        need(len(diffs)==3 and {before[i]:after[i] for i in diffs}==changes,'only three exact actual geometry instruction changes')
        need(sum(1 for w in before if w in changes)==3,'each parent geometry word is unique')
        custom=[a+4*i for i,w in enumerate(after) if w&0xfe00707f==0x0200000b]
        need(len(custom)==(32 if name=='q768_ta' else 0),'unchanged custom sites')
        if custom:path=custom*(36*24)
        records[name]=dict(parent=original,address=hex(a),bytes=n,sha256=gen.sha(elf.read(a,n)),
            parent_sha256=gen.sha(parent.read(pa,n)),changed_offsets=[i*4 for i in diffs],
            changed_words=[dict(offset=i*4,before=hex(before[i]),after=hex(after[i])) for i in diffs],
            all_other_machine_words_equal=True)
    need(len(path)==27648,'full K768 TA custom PC plan')
    (output/'ta-custom-pcs.bin').write_bytes(struct.pack('<27648Q',*path));return records

def select_w2(raw):
    cursor=(2*6*288+288)*4
    def tensor(n):
        nonlocal cursor
        q=raw[cursor:cursor+n];cursor+=n;s=raw[cursor:cursor+n//32*4];cursor+=n//32*4;return q,s
    tensor(32000*288);chosen=None
    for kind in range(7):
        for layer in range(6):
            pair=tensor(288*288 if kind<4 else 288*768)
            if kind==5 and layer==5:chosen=pair
    need(cursor==len(raw) and chosen is not None,'exact original tensor inventory');return chosen

def build(output,full_build,kernel_build):
    need(not output.exists() and not output.is_relative_to(REPO),'fresh isolated build')
    full=read(full_build/'result.json');need(full['status']=='FULL_MEMORY_STATIC_ELF_PASS_NOT_RUNTIME','original full fixture identity')
    kb=read(kernel_build/'result.json');need(kb['status']=='PROJECTION_BOUNDARY_STATIC_ELF_AND_MODELS_PASS_NOT_RUNTIME','qualified parent kernel build')
    am=Path(full['am_home']);need(not output.is_relative_to(am),'outside official AM')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','original AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM unmodified')
    pins=dict(kb['source_pins'])
    for p in (HERE/n for n in FILES):pins[str(p.relative_to(REPO))]=digest(p)
    for p in (REPO/gen.Q/'fused/generate.py',REPO/gen.Q/'fused/phased/candidate.py',REPO/gen.Q/'fused/phased/tail/candidate.py'):
        pins[str(p.relative_to(REPO))]=digest(p)
    external=dict(full['external_pins']);external.update({str(p):digest(p) for p in (full_build/'result.json',kernel_build/'result.json',kernel_build/'projection-boundaries.elf')})
    for name,value in full['fixtures'].items():external[str(full_build/'fixture'/name)]=value
    for rel,value in pins.items():need(digest(REPO/rel)==value,'unchanged inherited source')
    for p,value in external.items():need(digest(p)==value,'unchanged external input')
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=old.h.now());save(output/'state.json',state)
    try:
        source=output/'source';source.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest);need(digest(dest)==value,'source snapshot')
        local=source/'repo'/HERE.relative_to(REPO);forward=source/'repo'/gen.Q/'forward-host'
        for name in ('main.c','scalar.c','w2.h','export.c'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(local/'Makefile.target',source/'Makefile');shutil.copyfile(forward/'stages/full/state_layout.h',source/'state_layout.h')
        shutil.copyfile(forward/'stages/projection/entry.S',source/'entry.S')
        (source/'upstream').mkdir();shutil.copyfile(forward/'upstream/runq.c',source/'upstream/runq.c')
        generated=gen.generate(source/'repo',output/'generated');shutil.copyfile(output/'generated/w2.S',source/'w2.S')
        proof=old.h.gen.generate(forward/'upstream/runq.c',source/'forward.inc');save(output/'forward-generation.json',proof)
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf','nm')}
        tools.update(host_gcc=shutil.which('gcc'),make=shutil.which('make'));need(all(tools.values()),'installed toolchain')
        toolpins={n:dict(path=p,resolved=str(Path(p).resolve()),sha256=digest(p)) for n,p in tools.items()};save(output/'tools.json',toolpins)
        flags=['-std=gnu11','-O2','-fno-builtin','-ffp-contract=off','-fno-fast-math','-frounding-math','-fno-lto','-fno-tree-vectorize','-fno-tree-slp-vectorize']
        command([tools['host_gcc'],*flags,source/'export.c',source/'repo'/gen.Q/'acc8/q288.c','-I'+str(source),'-I'+str(forward),
            '-I'+str(forward.parent),'-I'+str(source/'repo'/gen.Q.parent/'split'),'-I'+str(source/'repo'/gen.Q.parent),'-lm','-o',output/'export-fixture'],output,'host-compile')
        fixture=output/'fixture';fixture.mkdir();command([output/'export-fixture',fixture],output,'host-export',timeout=180)
        need((output/'host-export.stdout.log').read_text()=='W2_EXPORT_PASS positions=3 full_state_bytes=3691424 position=2 layer=5 rows=288 k=768\n','complete capture transcript')
        for pos in range(3):need(digest(fixture/f'host-state-p{pos}.bin')==full['fixtures'][f'host-state-p{pos}.bin'],'whole captured original state equals frozen host gold')
        final_state=(full_build/'fixture/host-state-p2.bin').read_bytes()
        need((fixture/'input.bin').read_bytes()==final_state[11040:11808] and
             (fixture/'input-scales.bin').read_bytes()==final_state[11808:11904] and
             (fixture/'gold.bin').read_bytes()==final_state[1152:2304],
             'independent last-layer live-state slices equal actual pre/post capture')
        weight,scales=select_w2((full_build/'fixture/weights.bin').read_bytes())
        need((fixture/'weight.bin').read_bytes()==weight and (fixture/'scales.bin').read_bytes()==scales,'captured exact original W2 model')
        packed=b''.join(weight[(t*8+r)*768+g*32:(t*8+r)*768+g*32+32] for t in range(36) for g in range(24) for r in range(8))
        need(len(packed)==221184,'full new pack');(fixture/'packed.bin').write_bytes(packed)
        signed=lambda b:b if b<128 else b-256
        x=(fixture/'input.bin').read_bytes();slot=[]
        for row in range(280,288):
            value=sum(signed(weight[row*768+k])*signed(x[k]) for k in range(736,768));slot.extend([value&0xffffffff,0,0,0])
        (fixture/'slot-gold.bin').write_bytes(struct.pack('<32I',*slot))
        need((fixture/'expected-flags.bin').read_bytes()==struct.pack('<I',1),'original isolated NX flags')
        sizes={'input':768,'input-scales':96,'weight':221184,'packed':221184,'scales':27648,'gold':1152,'slot-gold':128}
        asm=['.section .rodata.w2_fixture,"a"','.balign 64']
        for name,size in sizes.items():
            need((fixture/(name+'.bin')).stat().st_size==size,'exact fixture span '+name);symbol='w2_'+name.replace('-','_')
            asm += [f'.global {symbol}',f'{symbol}:',f'.incbin "{fixture/(name+".bin")}"',f'.global {symbol}_end',f'{symbol}_end:','.balign 64']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file() and not p.is_relative_to(source/'repo')}
        fixtures={p.name:digest(p) for p in fixture.iterdir() if p.is_file()}
        save(output/'source-pins.json',pins);save(output/'actual-source-pins.json',actual);save(output/'external-pins.json',external)
        keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        clean=['env',*[v for k in keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc'][:-3],'W2_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'real-w2'),'-o','am','-o','klib','-j1','image'],output,'target-build',timeout=180)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'real-w2.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'real-w2.elf'],output,'disassembly')
        elf,inspection=executable(output/'real-w2.elf',output/'real-w2.bin')
        kernels=geometry_proof(elf,kernel_build/'projection-boundaries.elf',output);save(output/'kernel-identity.json',kernels)
        dumps=[]
        for symbol,size,name in (('w2_report',512,'report.bin'),('w2_samples',576,'samples.bin'),('output',1184,'output.bin'),('slots',160,'slots.bin')):
            address,length,*_=elf.symbols[symbol];need(length==size,'complete guarded object extent '+symbol);dumps.append((name,address,size))
        for name,size in sizes.items():
            symbol='w2_'+name.replace('-','_');address=elf.symbols[symbol][0];raw=(fixture/(name+'.bin')).read_bytes()
            need(elf.symbols[symbol+'_end'][0]-address==size and elf.read(address,size)==raw,'linked complete fixture '+name)
            dumps.append((name+'-after.bin',address,size))
        (output/'dump-plan.txt').write_text(''.join(f'{n} {a:x} {s}\n' for n,a,s in dumps))
        image=(output/'real-w2.bin').read_bytes();offset=elf.symbols['w2_control'][0]-BASE
        need(image[offset:offset+8]==struct.pack('<2I',0,1),'normal controls');bad=bytearray(image);bad[offset:offset+4]=struct.pack('<I',1);(output/'negative.bin').write_bytes(bad)
        for p,value in external.items():need(digest(p)==value,'external unchanged')
        for rel,value in pins.items():need(digest(REPO/rel)==value and digest(source/'repo'/rel)==value,'source unchanged')
        for n,v in actual.items():need(digest(source/n)==v,'compiled source unchanged')
        for n,v in fixtures.items():need(digest(fixture/n)==v,'fixture unchanged')
        for tool in toolpins.values():need(digest(tool['path'])==tool['sha256'],'tool unchanged')
        inspection.update(status='W2_STATIC_GEOMETRY_AND_CAPTURE_PASS_NOT_RUNTIME',contract=CONTRACT,source_pins=pins,actual_source_pins=actual,
            external_pins=external,fixtures=fixtures,kernel_identity=kernels,generated=generated,am_home=str(am),control_offset=offset,dump_plan=dumps,
            golden_fnv=f'{old.fnv((fixture/"gold.bin").read_bytes()):016x}',expected_normal_custom=221184,expected_negative_custom=55296,
            artifacts={n:digest(output/n) for n in ('real-w2.elf','real-w2.bin','negative.bin','dump-plan.txt','kernel-identity.json','ta-custom-pcs.bin','forward-generation.json')},
            target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=old.h.now();save(output/'state.json',state)

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('W2 build signal')))
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','full-build','kernel-build'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))]);r=build(a.output.resolve(),a.full_build.resolve(),a.kernel_build.resolve())
    print(json.dumps({k:r[k] for k in ('status','image_bytes','counter_sites','kernel_identity')},indent=2))
