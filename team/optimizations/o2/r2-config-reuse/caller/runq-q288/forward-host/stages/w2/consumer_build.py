"""Build the separate pure full-forward consumer with six real K768 W2s."""
from pathlib import Path
import argparse,importlib.util,json,os,shutil,signal,struct,subprocess
HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('w2_consumer_parent',HERE.parent/'consumer/build.py')
integration=load('w2_consumer_derivation',HERE/'integrate.py')
boundary=load('w2_consumer_boundary',HERE/'build.py')
REPO=old.REPO;CONTRACT=integration.CONTRACT
need,save,read,digest,command=old.need,old.save,old.read,old.digest,old.command
STATE_BYTES=old.STATE_BYTES

def pack_w2(raw):
    cursor=(2*6*288+288)*4
    def tensor(n):
        nonlocal cursor
        q=raw[cursor:cursor+n];cursor+=n+n//32*4;return q
    tensor(32000*288);out=[]
    for kind in range(7):
        for layer in range(6):
            q=tensor(288*288 if kind<4 else 288*768)
            if kind==5:
                out.append(b''.join(q[(tile*8+row)*768+group*32:(tile*8+row)*768+group*32+32]
                    for tile in range(36) for group in range(24) for row in range(8)))
    need(cursor==len(raw) and len(out)==6 and all(len(v)==221184 for v in out),'complete original six W2 tensors')
    return b''.join(out)

def build(output,parent_build,w2_build):
    parent=read(parent_build/'result.json');w2=read(w2_build/'result.json')
    need(parent['status']=='PURE_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME' and parent['contract']==old.CONTRACT,'exact original consumer build')
    need(w2['status']=='W2_STATIC_GEOMETRY_AND_CAPTURE_PASS_NOT_RUNTIME' and w2['contract']==boundary.CONTRACT,'qualified W2 boundary build')
    am=Path(parent['am_home']);need(not output.exists() and not any(output.is_relative_to(p) for p in (REPO,parent_build,w2_build,am)),'new isolated consumer-W2 build')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','original AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'original AM unchanged')
    pins=dict(parent['source_pins']);pins.update({str((HERE/name).relative_to(REPO)):digest(HERE/name)
        for name in ('consumer_build.py','integrate.py','consumer_w2.h','consumer-CONTRACT.md','w2.h')})
    external=dict(parent['external_pins'])
    for root,record in ((parent_build,parent),(w2_build,w2)):
        external[str(root/'result.json')]=digest(root/'result.json')
        for group,folder in (('artifacts',root),('fixtures',root/'fixture'),('actual_source_pins',root/'source')):
            external.update({str(folder/name):value for name,value in record[group].items()})
    for rel,value in pins.items():need(digest(REPO/rel)==value,'fixed source '+rel)
    for name,value in external.items():need(digest(name)==value,'fixed inherited artifact '+name)
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=old.f.h.now());save(output/'state.json',state)
    try:
        source=output/'source';source.mkdir();fixture=output/'fixture';fixture.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest);need(digest(dest)==value,'exact source snapshot')
        for name,value in parent['actual_source_pins'].items():
            dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(parent_build/'source'/name,dest)
        for name,value in parent['fixtures'].items():shutil.copyfile(parent_build/'fixture'/name,fixture/name)
        local=source/'repo'/HERE.relative_to(REPO)
        proof=integration.generate(local.parent/'consumer',source);save(output/'integration.json',proof)
        for name in ('consumer_w2.h','w2.h'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(w2_build/'source/w2.S',source/'w2.S')
        mk=(source/'Makefile').read_text();need(mk.count('NAME = forward-consumer')==1 and mk.count('main.c consumer.c')==1,'fixed parent makefile sites')
        mk=mk.replace('NAME = forward-consumer','NAME = forward-consumer-w2').replace('main.c consumer.c','main.c consumer.c w2.S')
        (source/'Makefile').write_text(mk)
        packed=pack_w2((fixture/'weights.bin').read_bytes());(fixture/'w2-packed.bin').write_bytes(packed)
        need(packed[-221184:]==(w2_build/'fixture/packed.bin').read_bytes(),'last layer exactly equals independently captured boundary pack')
        asm=['.section .rodata.fixture,"a"','.balign 16']
        model=[('weights','weights.bin'),('embedding','embedding.bin'),('packed','packed.bin'),('tail_scales','tail-scales.bin'),('w2_packed','w2-packed.bin')]
        for label,name in model:
            asm += [f'.global fixture_{label}',f'fixture_{label}:',f'.incbin "{fixture/name}"',f'.global fixture_{label}_end',f'fixture_{label}_end:','.balign 16']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file() and not p.is_relative_to(source/'repo')}
        fixtures={p.name:digest(p) for p in fixture.iterdir() if p.is_file()}
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf','nm')};tools['make']=shutil.which('make');need(all(tools.values()),'installed GNU tools')
        toolpins={n:dict(path=p,sha256=digest(p),resolved=str(Path(p).resolve())) for n,p in tools.items()};save(output/'tools.json',toolpins)
        keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        archives=[p for p in external if Path(p).name=='libm.a'];need(len(archives)==1,'same original static libm')
        clean=['env',*[v for k in keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc'][:-3],'FORWARD_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'forward-consumer-w2'),
            'MATH_ARCHIVE='+archives[0],'FULL_ERRNO_OFFSET='+str(parent['tls_errno_offset']),'-o','am','-o','klib','-j1','image'],output,'target-build',timeout=300)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'forward-consumer-w2.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'forward-consumer-w2.elf'],output,'disassembly')
        elf,inspection=old.f.executable(output/'forward-consumer-w2.elf',output/'forward-consumer-w2.bin',output/'metadata.stdout.log',parent['tls_errno_offset'])
        names=('q288_fused_rvv4','q288_tail_vdot');functions=old.p.kernel_bytes(parent_build/'forward-consumer.elf',names)
        functions.update(old.p.kernel_bytes(w2_build/'real-w2.elf',('q768_fr','q768_ta')))
        need(old.p.kernel_bytes(output/'forward-consumer-w2.elf',functions)==functions,'all four complete kernel functions retain actual bytes')
        objects=list((output/'objects').rglob('consumer.o'));need(len(objects)==1,'one pure consumer object');pure=objects[0];shutil.copyfile(pure,output/'consumer-w2.o')
        command([tools['objdump'],'-drwC',pure],output,'consumer-object-disassembly');command([tools['nm'],'-u',pure],output,'consumer-object-undefined')
        dis=(output/'consumer-object-disassembly.stdout.log').read_text()
        need(not any(v in dis for v in ('rdcycle','rdinstret','consumer_report','consumer_times','consumer_snapshots','consumer_control','checked_matmul','checked_quantize')),'pure W2 consumer has no observer/oracle dependency')
        need(all(v in dis for v in ('q768_fr','q768_ta','r2_w2_init','r2_w2_forward')),'actual new routing and public object symbols')
        identity=dict(functions={n:dict(bytes=len(v),sha256=old.f.h.sha(v)) for n,v in functions.items()},whole_function_bytes_equal=True,
            parent_elf_sha256=digest(parent_build/'forward-consumer.elf'),w2_elf_sha256=digest(w2_build/'real-w2.elf'),consumer_object_sha256=digest(output/'consumer-w2.o'),pure_object_has_no_observer_dependency=True)
        save(output/'kernel-identity.json',identity);image=(output/'forward-consumer-w2.bin').read_bytes();plans=[]
        for symbol,name,size in (('consumer_report','report.bin',512),('consumer_snapshots','snapshots.bin',6*STATE_BYTES),
            ('consumer_state','live-state.bin',STATE_BYTES),('consumer_flags','flags.bin',256*8),('consumer_times','times.bin',256*4*8)):
            address,length,*_=elf.symbols[symbol];need(length==size and image[address-0x80000000:address-0x80000000+size]==bytes(size),'complete initially zero harness object')
            plans.append((name,address,size))
        for label,name in model:
            symbol='fixture_'+label;address=elf.symbols[symbol][0];raw=(fixture/name).read_bytes()
            need(elf.symbols[symbol+'_end'][0]-address==len(raw) and elf.read(address,len(raw))==raw,'complete actual linked model '+label)
            plans.append((name.replace('.bin','-after.bin'),address,len(raw)))
        (output/'dump-plan.txt').write_text(''.join(f'{n} {a:x} {s}\n' for n,a,s in plans))
        offset=elf.symbols['consumer_control'][0]-0x80000000
        need(elf.symbols['consumer_control'][1]==16 and image[offset:offset+16]==struct.pack('<4I',4,3,0,1),'actual independent data controls')
        for p,value in external.items():need(digest(p)==value,'inherited input unchanged')
        for rel,value in pins.items():need(digest(REPO/rel)==value and digest(source/'repo'/rel)==value,'source unchanged')
        for p,value in actual.items():need(digest(source/p)==value,'actual source unchanged')
        for p,value in fixtures.items():need(digest(fixture/p)==value,'fixture unchanged')
        for v in toolpins.values():need(digest(v['path'])==v['sha256'],'tool unchanged')
        inspection.update(contract=CONTRACT,status='PURE_W2_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME',source_pins=pins,external_pins=external,
            actual_source_pins=actual,fixtures=fixtures,kernel_identity=identity,integration=proof,dump_plan=plans,
            artifacts={n:digest(output/n) for n in ('forward-consumer-w2.elf','forward-consumer-w2.bin','consumer-w2.o','dump-plan.txt','kernel-identity.json','integration.json')},
            control_offset=offset,w2_packed_offset=elf.symbols['fixture_w2_packed'][0]-0x80000000,am_home=str(am),reference_runs=0,target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=old.f.h.now();save(output/'state.json',state)

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('W2 consumer build signal')))
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('output','parent-build','w2-build'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))]);r=build(a.output.resolve(),a.parent_build.resolve(),a.w2_build.resolve())
    print(json.dumps({k:r[k] for k in ('status','image_bytes','heap_start','performance_qualified')},indent=2))
