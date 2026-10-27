"""Build one pure-consumer object and its memory validation harness."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import shutil
import signal
import struct
import subprocess

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=load('consumer_projection_inputs',HERE.parent/'projection/build.py')
f=p.f
REPO=f.REPO
need,save,read,digest,command=f.need,f.save,f.read,f.digest,f.command
CONTRACT='r2-s3-forward-consumer-v1'
FILES=('build.py','consumer.c','consumer.h','main.c','generate.py','CONTRACT.md')
STATE_BYTES=3691424

def build(output,full_build,kernel_build):
    need(not output.exists() and not output.is_relative_to(REPO),'fresh isolated consumer build')
    full=read(full_build/'result.json')
    need(full['status']=='FULL_MEMORY_STATIC_ELF_PASS_NOT_RUNTIME','frozen full fixture build')
    for name,value in full['fixtures'].items():need(digest(full_build/'fixture'/name)==value,'original full fixture')
    for rel,value in full['source_pins'].items():need(digest(REPO/rel)==value,'original inherited source')
    old=read(kernel_build/'build.json');old_elf=kernel_build/'vdot-perf.elf';old_asm=kernel_build/'source/fused.S'
    need(old['accepted'] is True and old['contract']=='r2-s3-runq-active-qkv-target-v1','accepted original kernel build')
    need(digest(old_elf)==p.KERNEL_ELF_SHA and digest(old_asm)==p.KERNEL_ASM_SHA and old['artifacts']['vdot-perf.elf']==p.KERNEL_ELF_SHA,'whole fixed kernel inputs')
    functions=p.kernel_bytes(old_elf,('q288_fused_rvv4','q288_tail_vdot'))
    am=Path(full['am_home']);external=dict(full['external_pins'])
    need(not any(output.is_relative_to(root) for root in (REPO,full_build,kernel_build,am)),
         'consumer build is outside every source and inherited input tree')
    external.update({str(v):digest(v) for v in (full_build/'result.json',kernel_build/'build.json',old_elf,old_asm)})
    external.update({str(full_build/'fixture'/n):v for n,v in full['fixtures'].items()})
    for name,value in external.items():need(digest(name)==value,'fixed external build input')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','original AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM unchanged')
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=f.h.now(),cpu_affinity=sorted(os.sched_getaffinity(0)))
    save(output/'state.json',state)
    try:
        q=f.Q;pins=dict(full['source_pins'])
        paths=[*(HERE/n for n in FILES),HERE.parent/'projection/build.py',HERE.parent/'projection/Makefile.target',
               HERE.parent/'projection/entry.S',REPO/q/'q288.h',REPO/q/'acc8/q288.c',REPO/q.parent/'split/split.h',REPO/q.parent/'caller.h']
        pins.update({str(v.relative_to(REPO)):digest(v) for v in paths})
        source=output/'source';source.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest);need(digest(dest)==value,'exact source snapshot')
        save(output/'source-pins.json',pins);save(output/'external-pins.json',external)
        local=source/'repo'/HERE.relative_to(REPO);forward=source/'repo'/q/'forward-host'
        fixture=output/'fixture';fixture.mkdir()
        for name,value in full['fixtures'].items():
            shutil.copyfile(full_build/'fixture'/name,fixture/name);need(digest(fixture/name)==value,'frozen fixture copy')
        packed,scales,layout=p.expected_pack((fixture/'weights.bin').read_bytes())
        (fixture/'packed.bin').write_bytes(packed);(fixture/'tail-scales.bin').write_bytes(scales);save(fixture/'matrix-layout.json',layout)
        for name in ('main.c','consumer.c','consumer.h'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(forward/'stages/projection/entry.S',source/'entry.S')
        mk=(forward/'stages/projection/Makefile.target').read_text().replace('NAME = forward-projection','NAME = forward-consumer').replace('SRCS = main.c','SRCS = main.c consumer.c')
        (source/'Makefile').write_text(mk)
        for rel,name in ((q/'q288.h','q288.h'),(q/'acc8/q288.c','q288.c'),(q.parent/'split/split.h','split.h'),(q.parent/'caller.h','caller.h')):
            shutil.copyfile(source/'repo'/rel,source/name)
        (source/'upstream').mkdir();shutil.copyfile(forward/'upstream/runq.c',source/'upstream/runq.c');shutil.copyfile(old_asm,source/'fused.S')
        gen=load('consumer_snapshot_generator',local/'generate.py');generated=gen.generate(source/'upstream/runq.c',source/'consumer.inc');save(output/'generated.json',generated)
        asm=['.section .rodata.fixture,"a"','.balign 16']
        for label,name in (('weights','weights.bin'),('embedding','embedding.bin'),('packed','packed.bin'),('tail_scales','tail-scales.bin')):
            asm += [f'.global fixture_{label}',f'fixture_{label}:',f'.incbin "{fixture/name}"',f'.global fixture_{label}_end',f'fixture_{label}_end:','.balign 16']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={str(v.relative_to(source)):digest(v) for v in source.rglob('*') if v.is_file() and not v.is_relative_to(source/'repo')}
        fixtures={v.name:digest(v) for v in fixture.iterdir() if v.is_file()};save(output/'actual-source-pins.json',actual)
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf','nm')};tools['make']=shutil.which('make');need(all(tools.values()),'native installed tools')
        toolpins={n:dict(path=v,sha256=digest(v),resolved=str(Path(v).resolve())) for n,v in tools.items()};save(output/'tools.json',toolpins)
        clean_keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        archives=[v for v in external if Path(v).name=='libm.a'];need(len(archives)==1,'same static libm')
        clean=['env',*[v for k in clean_keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
                 'CROSS_COMPILE='+tools['gcc'][:-3],'FORWARD_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'forward-consumer'),
                 'MATH_ARCHIVE='+archives[0],'FULL_ERRNO_OFFSET='+str(full['tls_errno_offset']),'-o','am','-o','klib','-j1','image'],output,'target-build',timeout=300)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'forward-consumer.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'forward-consumer.elf'],output,'disassembly')
        elf,inspection=f.executable(output/'forward-consumer.elf',output/'forward-consumer.bin',output/'metadata.stdout.log',full['tls_errno_offset'])
        need(p.kernel_bytes(output/'forward-consumer.elf',functions)==functions,'whole original strong FR and TA machine code')
        objects=list((output/'objects').rglob('consumer.o'));need(len(objects)==1,'single independently compiled pure consumer object')
        pure=objects[0];shutil.copyfile(pure,output/'consumer.o')
        command([tools['objdump'],'-drwC',pure],output,'consumer-object-disassembly')
        command([tools['nm'],'-u',pure],output,'consumer-object-undefined')
        dis=(output/'consumer-object-disassembly.stdout.log').read_text()
        need(not any(v in dis for v in ('rdcycle','rdinstret','consumer_report','consumer_times','consumer_snapshots','consumer_control','checked_matmul','checked_quantize')),'pure object has no observation or oracle dependency')
        identity=dict(reference_elf_sha256=p.KERNEL_ELF_SHA,assembly_sha256=p.KERNEL_ASM_SHA,
                      functions={n:dict(bytes=len(v),sha256=f.h.sha(v)) for n,v in functions.items()},whole_function_bytes_equal=True,
                      consumer_object_sha256=digest(output/'consumer.o'),pure_object_has_no_observer_dependency=True)
        save(output/'kernel-identity.json',identity)
        image=(output/'forward-consumer.bin').read_bytes();plans=[]
        for symbol,name,size in (('consumer_report','report.bin',512),('consumer_snapshots','snapshots.bin',6*STATE_BYTES),
                                ('consumer_state','live-state.bin',STATE_BYTES),('consumer_flags','flags.bin',256*8),('consumer_times','times.bin',256*4*8)):
            address,length,_,_=elf.symbols[symbol];need(length==size,'complete consumer symbol extent');plans.append((name,address,size))
            need(image[address-0x80000000:address-0x80000000+size]==bytes(size),'initial observed storage is entirely zero')
        for label,name in (('weights','weights.bin'),('embedding','embedding.bin'),('packed','packed.bin'),('tail_scales','tail-scales.bin')):
            symbol='fixture_'+label;address=elf.symbols[symbol][0];raw=(fixture/name).read_bytes()
            need(elf.symbols[symbol+'_end'][0]-address==len(raw) and elf.read(address,len(raw))==raw,'complete actual linked model')
            plans.append((name.replace('.bin','-after.bin'),address,len(raw)))
        (output/'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name,address,size in plans))
        image=(output/'forward-consumer.bin').read_bytes();offset=elf.symbols['consumer_control'][0]-0x80000000
        need(elf.symbols['consumer_control'][1]==16 and image[offset:offset+16]==struct.pack('<4I',4,3,0,1),'normal data-only controls')
        for path,value in external.items():need(digest(path)==value,'unchanged external input')
        for rel,value in pins.items():need(digest(REPO/rel)==value and digest(source/'repo'/rel)==value,'unchanged source input')
        for name,value in actual.items():need(digest(source/name)==value,'unchanged actual compiled source')
        for name,value in fixtures.items():need(digest(fixture/name)==value,'unchanged full fixture')
        for tool in toolpins.values():need(digest(tool['path'])==tool['sha256'],'unchanged actual tool')
        inspection.update(status='PURE_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME',contract=CONTRACT,source_pins=pins,external_pins=external,
                          actual_source_pins=actual,fixtures=fixtures,kernel_identity=identity,generated=generated,dump_plan=plans,
                          artifacts={n:digest(output/n) for n in ('forward-consumer.elf','forward-consumer.bin','consumer.o','dump-plan.txt','kernel-identity.json','generated.json')},
                          control_offset=offset,am_home=str(am),reference_runs=0,target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=f.h.now();save(output/'state.json',state)

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('consumer build signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('output','full-build','kernel-build'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    result=build(args.output.resolve(),args.full_build.resolve(),args.kernel_build.resolve())
    print(json.dumps({k:result[k] for k in ('status','image_bytes','heap_start','reference_runs','performance_qualified')},indent=2))
