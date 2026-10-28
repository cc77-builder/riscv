"""Build a new complete RMSNorm experiment; preserve all original inputs."""
from pathlib import Path
import argparse,importlib.util,json,os,re,shutil,signal,struct,subprocess
HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('norm_build_support',HERE.parent/'projection/target/build.py')
gen=load('norm_derivation',HERE/'generate.py')
REPO=old.REPO
need,save,read,digest,command=old.need,old.save,old.read,old.digest,old.command
CONTRACT='r2-s3-rmsnorm-output-v1'
FILES=('build.py','generate.py','norm.h','norm.S','scalar.c','main.c','export.c','Makefile.target','CONTRACT.md')
BASE=0x80000000
def executable(path,binary):
    elf=old.g.ELF(path.read_bytes())
    need(elf.kind==2 and elf.entry==BASE,'static actual entry')
    need('_trm_init' not in elf.symbols and all(n in elf.symbols for n in
        ('team_forward_main','_putc','rmsnorm','r2_rmsnorm_rvv','r2_norm_output_rvv')),'original scalar, vector candidate and team entry')
    need(not any(p[0] in (2,3) for p in elf.segments),'no dynamic runtime')
    need(not any((v[3]&15)==10 or (v[2]==0 and v[3]>>4==1) for v in elf.symbols.values()),'no IFUNC/unresolved strong symbol')
    for s in elf.sections:
        if s[1] in (4,9) and s[2]&2:need(s[1]==4 and s[9]==24 and elf.section(s)==bytes(s[5]),'no live runtime relocation')
    tls=[p for p in elf.segments if p[0]==7]
    need(len(tls)==1 and tls[0][5:8]==(0,4,4),'same zero errno TLS template')
    need(elf.symbols['errno'][0:2]==(0,4),'same fixed errno offset')
    need('__tls_get_addr' not in elf.symbols,'no dynamic TLS resolver')
    sections=sorted((s for s in elf.sections if s[2]&2 and s[5] and not s[2]&0x400),key=lambda s:s[3])
    need(sections[0][3]==BASE,'RAM base')
    for s in sections:need(BASE<=s[3]<s[3]+s[5]<=0x88000000,'all static data within RAM')
    for a,z in zip(sections,sections[1:]):need(a[3]+a[5]<=z[3],'ordinary sections disjoint')
    raw=bytearray(max(s[3]+s[5] for s in sections)-BASE)
    for s in sections:
        if s[1]!=8:raw[s[3]-BASE:s[3]-BASE+s[5]]=elf.section(s)
    need(bytes(raw)==binary.read_bytes(),'complete actual ELF/BIN identity')
    top=elf.symbols['_stack_top'][0];stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(stack%16==0 and max(s[3]+s[5] for s in sections)<=top<=stack<heap<0x88000000,'data stack heap bounds')
    pc,size,*_=elf.symbols['team_forward_main'];end=pc+size;sites=[]
    while pc<end:
        low=struct.unpack('<H',elf.read(pc,2))[0]
        if low&3!=3:pc+=2;continue
        word=struct.unpack('<I',elf.read(pc,4))[0]
        if word&0x707f==0x2073 and (word>>15)&31==0 and word>>20 in (0xc00,0xc02):
            need(elf.read(pc-4,4)==elf.read(pc+4,4)==struct.pack('<I',0x0ff0000f),'actual four IORW fenced CSR sites')
            sites.append(dict(pc=hex(pc),csr=hex(word>>20)))
        pc+=4
    need([x['csr'] for x in sites]==['0xc00','0xc02','0xc02','0xc00'],'whole counter order')
    pc,size,*_=elf.symbols['reject'];code=elf.read(pc,size);traps=[]
    for offset in range(0,size-3,4):
        word=struct.unpack('<I',code[offset:offset+4])[0]
        if word&127==0x6b:
            need(offset>=4 and code[offset-4:offset+4]==struct.pack('<2I',0x05c00513,0x0005006b),'actual BAD trap takes a0=92')
            traps.append(hex(pc+offset))
    need(traps,'at least one exact rejection trap')
    need(elf.read(elf.symbols['full_success_trap'][0],4)==struct.pack('<I',0x0005006b),'success trap also consumes a0')
    return elf,dict(image_bytes=len(raw),heap_start=hex(heap),counter_sites=sites,failure_traps=traps,tls_errno_offset=0)
def build(output,full_build):
    need(not output.exists() and not output.is_relative_to(REPO),'fresh isolated build')
    full=read(full_build/'result.json')
    need(full['status']=='FULL_MEMORY_STATIC_ELF_PASS_NOT_RUNTIME','fixed original full build')
    am=Path(full['am_home']);need(not output.is_relative_to(am),'outside official AM')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','official AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM unmodified')
    pins=dict(full['source_pins'])
    for p in (HERE/n for n in FILES):pins[str(p.relative_to(REPO))]=digest(p)
    for p in (HERE.parent/'projection/entry.S',HERE.parent/'projection/target/build.py',HERE.parent/'projection/build.py'):
        pins[str(p.relative_to(REPO))]=digest(p)
    external=dict(full['external_pins']);external[str(full_build/'result.json')]=digest(full_build/'result.json')
    for name,value in full['fixtures'].items():external[str(full_build/'fixture'/name)]=value
    for p,v in pins.items():need(digest(REPO/p)==v,'original inherited source '+p)
    for p,v in external.items():need(digest(p)==v,'original external input '+p)
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=old.h.now());save(output/'state.json',state)
    try:
        source=output/'source';source.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest)
            need(digest(dest)==value,'exact source snapshot')
        local=source/'repo'/HERE.relative_to(REPO);forward=source/'repo'/old.h.Q/'forward-host'
        for name in ('main.c','scalar.c','norm.h','norm.S','export.c'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(local/'Makefile.target',source/'Makefile')
        entry=(forward/'stages/projection/entry.S').read_text()
        need(entry.count('.word 0x0000006b')==1,'one inherited success trap')
        (source/'entry.S').write_text(entry.replace('.word 0x0000006b','.word 0x0005006b'))
        shutil.copyfile(forward/'stages/full/state_layout.h',source/'state_layout.h')
        (source/'upstream').mkdir();shutil.copyfile(forward/'upstream/runq.c',source/'upstream/runq.c')
        generation=gen.generate(source/'upstream/runq.c',source/'candidate.c');save(output/'generation.json',generation)
        old.h.gen.generate(source/'upstream/runq.c',source/'forward.inc')
        base=(source/'forward.inc').read_text();need(base.count('rmsnorm(')==9,'three norm sites in each of three exact derived forward functions')
        captured=base.replace('rmsnorm(','capture_norm(');need(captured.replace('capture_norm(','rmsnorm(')==base,'exact passive capture reversal')
        (source/'capture.inc').write_text(captured)
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf','nm')}
        tools.update(host_gcc=shutil.which('gcc'),make=shutil.which('make'));need(all(tools.values()),'installed real toolchain')
        toolpins={n:dict(path=p,resolved=str(Path(p).resolve()),sha256=digest(p)) for n,p in tools.items()};save(output/'tools.json',toolpins)
        flags=['-std=gnu11','-O2','-fno-builtin','-ffp-contract=off','-fno-fast-math','-frounding-math','-fno-lto','-fno-tree-vectorize','-fno-tree-slp-vectorize']
        command([tools['host_gcc'],*flags,source/'export.c',source/'repo'/old.h.Q/'acc8/q288.c',
            '-I'+str(source),'-I'+str(forward),'-I'+str(forward.parent),'-I'+str(source/'repo'/old.h.Q.parent/'split'),
            '-I'+str(source/'repo'/old.h.Q.parent),'-lm','-o',output/'export-fixture'],output,'host-compile')
        command(['ldd',output/'export-fixture'],output,'host-libraries')
        hostlibs={str(Path(p).resolve()):digest(p) for p in re.findall(r'(/[^\s()]+)',(output/'host-libraries.stdout.log').read_text()) if Path(p).is_file()}
        need(any(Path(p).name.startswith('libm.so') for p in hostlibs) and any(Path(p).name.startswith('libc.so') for p in hostlibs),'actual dynamic host math and C libraries')
        external.update(hostlibs)
        fixture=output/'fixture';fixture.mkdir();command([output/'export-fixture',fixture],output,'host-export',timeout=180)
        need((output/'host-export.stdout.log').read_text()=='NORM_EXPORT_PASS real_cases=39 synthetic_cases=9 full_states=3 size=288\n','complete host capture')
        for pos in range(3):need(digest(fixture/f'host-state-p{pos}.bin')==full['fixtures'][f'host-state-p{pos}.bin'],'complete captured state equals frozen original host gold')
        sizes={'input':55296,'weight':55296,'gold':55296,'flags':192}
        asm=['.section .rodata.norm_fixture,"a"','.balign 64']
        for name,size in sizes.items():
            need((fixture/(name+'.bin')).stat().st_size==size,'whole fixture geometry')
            symbol='norm_expected_flags' if name=='flags' else 'norm_'+name
            asm += [f'.global {symbol}',f'{symbol}:',f'.incbin "{fixture/(name+".bin")}"',f'.global {symbol}_end',f'{symbol}_end:','.balign 64']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file() and not p.is_relative_to(source/'repo')}
        fixtures={p.name:digest(p) for p in fixture.iterdir() if p.is_file()}
        save(output/'source-pins.json',pins);save(output/'actual-source-pins.json',actual);save(output/'external-pins.json',external)
        keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        clean=['env',*[v for k in keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        archives=[p for p in external if Path(p).name=='libm.a'];need(len(archives)==1,'same original libm')
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc'][:-3],'NORM_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'real-norm'),
            'MATH_ARCHIVE='+archives[0],'FULL_ERRNO_OFFSET=0','-o','am','-o','klib','-j1','image'],output,'target-build',timeout=240)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'real-norm.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'real-norm.elf'],output,'disassembly')
        elf,inspection=executable(output/'real-norm.elf',output/'real-norm.bin')
        functions={}
        for name in ('rmsnorm','r2_rmsnorm_rvv','r2_norm_output_rvv'):
            address,length,*_=elf.symbols[name];raw=elf.read(address,length)
            need(length%4==0 and not any((w&127) in (0x43,0x47,0x4b,0x4f) for w in struct.unpack('<'+str(length//4)+'I',raw)),'no actual contracted FP instruction')
            functions[name]=dict(address=hex(address),bytes=length,sha256=gen.sha(raw))
        dis=(output/'disassembly.stdout.log').read_text()
        address,length,*_=elf.symbols['r2_norm_output_rvv']
        body='\n'.join(line for line in dis.splitlines()
            if (m:=re.match(r'^\s*([0-9a-f]+):\s+[0-9a-f]+\s+\S+',line)) and address<=int(m[1],16)<address+length)
        need(body.count('vfmul.vf')==body.count('vfmul.vv')==1 and body.count('vle32.v')==2 and body.count('vse32.v')==1,'actual two-stage vector output only')
        need('e32,m8,ta,ma' in body and 'vsetvl' in body and 'fa0' in body,'actual finite vector geometry, scalar FP ABI and restoration')
        objects={}
        for basename in ('candidate.o','norm.o'):
            found=list((output/'objects').rglob(basename));need(len(found)==1,'one exact candidate object')
            shutil.copyfile(found[0],output/basename);objects[basename]=digest(output/basename)
        save(output/'kernel-identity.json',dict(functions=functions,objects=objects,derivation=generation,no_fma=True))
        plans=[]
        for symbol,size,name in (('norm_report',512,'report.bin'),('norm_samples',512,'samples.bin'),('norm_flags',3072,'observed-flags.bin'),('norm_results',442368,'outputs.bin'),
                ('input',1184,'working-input.bin'),('output',1184,'working-output.bin'),
                ('batch_x',15392,'batch-input.bin'),('batch_y',15392,'batch-output.bin'),('team_tls_area',96,'tls.bin'),('norm_control',8,'control.bin')):
            address,length,*_=elf.symbols[symbol];need(length==size,'complete harness object');plans.append((name,address,size))
        for name,size in sizes.items():
            symbol='norm_expected_flags' if name=='flags' else 'norm_'+name
            address=elf.symbols[symbol][0];raw=(fixture/(name+'.bin')).read_bytes()
            need(elf.symbols[symbol+'_end'][0]-address==size and elf.read(address,size)==raw,'entire linked fixture '+name)
            plans.append((name+'-after.bin',address,size))
        (output/'dump-plan.txt').write_text(''.join(f'{n} {a:x} {s}\n' for n,a,s in plans))
        image=(output/'real-norm.bin').read_bytes();offset=elf.symbols['norm_control'][0]-BASE
        need(image[offset:offset+8]==struct.pack('<2I',0,1),'normal control')
        bad=bytearray(image);bad[offset:offset+4]=struct.pack('<I',1);(output/'negative.bin').write_bytes(bad)
        gold=(fixture/'gold.bin').read_bytes();batch=gold[26*1152:39*1152]
        inspection.update(contract=CONTRACT,status='NORM_STATIC_CAPTURE_AND_ELF_PASS_NOT_RUNTIME',
            source_pins=pins,external_pins=external,actual_source_pins=actual,fixtures=fixtures,functions=functions,
            artifacts={n:digest(output/n) for n in ('real-norm.elf','real-norm.bin','negative.bin','dump-plan.txt','candidate.o','norm.o','kernel-identity.json','generation.json')},
            dump_plan=plans,control_offset=offset,am_home=str(am),host_libraries=hostlibs,batch_fnv=f'{old.fnv(batch):016x}',
            batch_flags=__import__('functools').reduce(lambda x,y:x|y,struct.unpack('<48I',(fixture/'flags.bin').read_bytes())[26:39],0),
            reference_runs=0,target_emu_runs=0,performance_qualified=False)
        for p,v in external.items():need(digest(p)==v,'external input unchanged')
        for p,v in pins.items():need(digest(REPO/p)==v and digest(source/'repo'/p)==v,'source unchanged')
        for n,v in actual.items():need(digest(source/n)==v,'compiled source unchanged')
        for n,v in fixtures.items():need(digest(fixture/n)==v,'captured fixture unchanged')
        for v in toolpins.values():need(digest(v['path'])==v['sha256'],'tool unchanged')
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=old.h.now();save(output/'state.json',state)
if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('norm build signal')))
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('output','full-build'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    r=build(a.output.resolve(),a.full_build.resolve());print(json.dumps({k:r[k] for k in ('status','image_bytes','batch_fnv','batch_flags','performance_qualified')},indent=2))
