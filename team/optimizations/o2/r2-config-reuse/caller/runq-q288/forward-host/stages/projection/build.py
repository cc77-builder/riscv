"""Build the full projection consumer using frozen full fixtures and TA/FR bytes."""
from pathlib import Path
import argparse
import json
import os
import shutil
import signal
import struct
import subprocess
import importlib.util

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f=load('projection_full_build',HERE.parent/'full/build.py')
REPO=f.REPO
need,save,read,digest,command=f.need,f.save,f.read,f.digest,f.command
CONTRACT='r2-s3-forward-projection-v1'
FILES=('build.py','CONTRACT.md','main.c','entry.S','Makefile.target')
KERNEL_ELF_SHA='be7412fdc3d9c1f0dac167f6bbc61fac03eed2454f04652cd3ca321d9296d7d6'
KERNEL_ASM_SHA='f7cd8ae5a9b206f42ef94bc803a6b67e0ccfc588ec763906b79e57e168ff37b4'

def expected_pack(raw):
    """Independent byte mapping from unchanged full model, no target code call."""
    cursor=(2*6*288+288)*4
    def tensor(elements):
        nonlocal cursor
        q=raw[cursor:cursor+elements];cursor+=elements
        scales=raw[cursor:cursor+elements//32*4];cursor+=elements//32*4
        need(len(q)==elements and len(scales)==elements//32*4,'complete original tensor')
        return q,scales
    classifier=tensor(32000*288);arrays=[]
    for kind in range(7):arrays.append([tensor(288*288 if kind<4 else 288*768) for _ in range(6)])
    need(cursor==len(raw)==17101440,'complete original model layout')
    matrices=[(q,s,288 if kind<4 else 768) for kind in (0,1,2,3,4,6) for q,s in arrays[kind]]
    matrices.append((*classifier,32000));packed=[];tails=[];layout=[]
    for identity,(q,scales,rows) in enumerate(matrices):
        first=len(packed)
        for row in range(0,rows,288):
            valid=min(rows-row,288);block=q[row*288:(row+valid)*288]+bytes((288-valid)*288)
            packed.append(b''.join(block[(t*8+r)*288+g*32:(t*8+r)*288+g*32+32]
                                  for t in range(36) for g in range(9) for r in range(8)))
            if valid<288:tails.append(scales[row*9*4:(row+valid)*9*4]+struct.pack('<f',1.0)*((288-valid)*9))
        layout.append(dict(id=identity,rows=rows,k=288,first_block=first,blocks=len(packed)-first))
    need(len(packed)==172 and len(tails)==13,'complete block/tail layout')
    return b''.join(packed),b''.join(tails),layout

def kernel_bytes(elf_path,names):
    elf=f.g.ELF(elf_path.read_bytes());out={}
    for name in names:
        address,size,section,info=elf.symbols[name];need(size>0 and (info&15)==2,'whole named function')
        out[name]=elf.read(address,size)
    return out

def build(output,full_build,kernel_build):
    need(not output.exists() and not output.is_relative_to(REPO),'new isolated projection build')
    full=read(full_build/'result.json');need(full['status']=='FULL_MEMORY_STATIC_ELF_PASS_NOT_RUNTIME','qualified full fixture build')
    for name,value in full['fixtures'].items():need(digest(full_build/'fixture'/name)==value,'frozen full fixture')
    for rel,value in full['source_pins'].items():need(digest(REPO/rel)==value,'unchanged reused full source')
    old=read(kernel_build/'build.json');need(old['accepted'] is True and old['contract']=='r2-s3-runq-active-qkv-target-v1','old accepted exact kernel source')
    old_elf=kernel_build/'vdot-perf.elf';old_asm=kernel_build/'source/fused.S'
    need(digest(old_elf)==KERNEL_ELF_SHA and digest(old_asm)==KERNEL_ASM_SHA,'fixed previous ELF and complete assembly')
    need(old['artifacts']['vdot-perf.elf']==KERNEL_ELF_SHA,'previous receipt binds exact ELF')
    reference_functions=kernel_bytes(old_elf,('q288_fused_rvv4','q288_tail_vdot'))
    am=Path(full['am_home']);external=dict(full['external_pins'])
    external.update({str(p):digest(p) for p in (full_build/'result.json',kernel_build/'build.json',old_elf,old_asm)})
    for name,value in full['fixtures'].items():external[str(full_build/'fixture'/name)]=value
    for p,value in external.items():need(digest(p)==value,'fixed external build input')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','original AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM unchanged')
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=f.h.now(),target_runtime_ready=False)
    save(output/'state.json',state)
    try:
        pins=dict(full['source_pins']);q=f.Q
        paths=[*(HERE/n for n in FILES),REPO/q/'q288.h',REPO/q/'acc8/q288.c',REPO/q.parent/'split/split.h',REPO/q.parent/'caller.h']
        pins.update({str(p.relative_to(REPO)):digest(p) for p in paths})
        source=output/'source';source.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest)
            need(digest(dest)==value,'exact source snapshot')
        save(output/'source-pins.json',pins);save(output/'external-pins.json',external)
        local=source/'repo'/HERE.relative_to(REPO);forward=source/'repo'/q/'forward-host'
        fixture=output/'fixture';fixture.mkdir()
        for name,value in full['fixtures'].items():
            shutil.copyfile(full_build/'fixture'/name,fixture/name)
            need(digest(fixture/name)==value,'actual copied fixture equals frozen original')
        expected_packed,expected_scales,layout=expected_pack((fixture/'weights.bin').read_bytes())
        (fixture/'expected-packed.bin').write_bytes(expected_packed);(fixture/'expected-tail-scales.bin').write_bytes(expected_scales)
        save(fixture/'matrix-layout.json',layout)
        for name in ('main.c','entry.S'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(local/'Makefile.target',source/'Makefile')
        shutil.copyfile(forward/'stages/full/state_layout.h',source/'state_layout.h')
        for rel,name in ((q/'q288.h','q288.h'),(q/'acc8/q288.c','q288.c'),(q.parent/'split/split.h','split.h'),(q.parent/'caller.h','caller.h')):
            shutil.copyfile(source/'repo'/rel,source/name)
        (source/'upstream').mkdir();shutil.copyfile(forward/'upstream/runq.c',source/'upstream/runq.c')
        shutil.copyfile(old_asm,source/'fused.S')
        original=f.h.gen.original(source/'upstream/runq.c')
        generated=original.replace('float* forward(','static float* projection_forward(',1).replace('quantize(','checked_quantize(').replace('matmul(','checked_matmul(')
        restored=generated.replace('static float* projection_forward(','float* forward(',1).replace('checked_quantize(','quantize(').replace('checked_matmul(','matmul(')
        need(restored==original and generated.count('checked_matmul(')==8 and generated.count('checked_quantize(')==5,'entire source reverse restoration')
        (source/'projection.inc').write_text(generated+'\n')
        save(output/'generated.json',dict(upstream_sha256=f.h.gen.UPSTREAM_SHA,original_forward_sha256=f.h.sha(original.encode()),
            generated_sha256=digest(source/'projection.inc'),restored_entire_source_equal=True,changes=['function name','quantize callback','matmul callback']))
        asm=['.section .rodata.fixture,"a"','.balign 16']
        for label,name in (('weights','weights.bin'),('embedding','embedding.bin')):
            asm += [f'.global fixture_{label}',f'fixture_{label}:',f'.incbin "{fixture/name}"',f'.global fixture_{label}_end',f'fixture_{label}_end:','.balign 16']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file() and not p.is_relative_to(source/'repo')}
        fixture_pins={p.name:digest(p) for p in fixture.iterdir() if p.is_file()}
        for name,value in full['fixtures'].items():need(fixture_pins[name]==value,'inherited fixture identity is never rebound')
        save(output/'actual-source-pins.json',actual)
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf')};tools['make']=shutil.which('make')
        need(all(tools.values()),'native installed tools')
        toolpins={n:dict(path=p,sha256=digest(p),resolved=str(Path(p).resolve())) for n,p in tools.items()};save(output/'tools.json',toolpins)
        clean_keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        archives=[p for p in external if Path(p).name=='libm.a'];need(len(archives)==1,'same static libm')
        clean=['env',*[v for k in clean_keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc'][:-3],'FORWARD_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'forward-projection'),
            'MATH_ARCHIVE='+archives[0],'FULL_ERRNO_OFFSET='+str(full['tls_errno_offset']),'-o','am','-o','klib','-j1','image'],output,'target-build',timeout=300)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'forward-projection.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'forward-projection.elf'],output,'disassembly')
        elf,inspection=f.executable(output/'forward-projection.elf',output/'forward-projection.bin',output/'metadata.stdout.log',full['tls_errno_offset'])
        actual_functions=kernel_bytes(output/'forward-projection.elf',reference_functions)
        need(actual_functions==reference_functions,'whole TA and strong FR function bytes unchanged')
        (output/'kernel-reference').mkdir()
        for name,raw in reference_functions.items():(output/'kernel-reference'/f'{name}.bin').write_bytes(raw)
        kernel_identity=dict(reference_elf_sha256=KERNEL_ELF_SHA,assembly_sha256=KERNEL_ASM_SHA,
            functions={name:dict(bytes=len(raw),sha256=f.h.sha(raw)) for name,raw in reference_functions.items()},whole_function_bytes_equal=True)
        save(output/'kernel-identity.json',kernel_identity)
        plans=[]
        for symbol,name,size in (('projection_report','report.bin',256),('projection_snapshots','snapshots.bin',9*3691424),
            ('storage','live-states.bin',3*3691424),
            ('projection_counts','counts.bin',9*8*8),('projection_packed','packed-after.bin',172*82944),
            ('projection_tail_scales','tail-scales-after.bin',13*288*9*4)):
            address,length,_,_=elf.symbols[symbol];need(length==size,'whole projection symbol extent');plans.append((name,address,size))
        for symbol,name,size in (('fixture_weights','weights-after.bin',17101440),('fixture_embedding','embedding-after.bin',36864000)):
            address=elf.symbols[symbol][0];need(elf.symbols[symbol+'_end'][0]-address==size,'whole fixture extent')
            original_name='weights.bin' if 'weights' in symbol else 'embedding.bin'
            need(elf.read(address,size)==(fixture/original_name).read_bytes(),'exact complete linked fixture')
            plans.append((name,address,size))
        (output/'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name,address,size in plans))
        image=(output/'forward-projection.bin').read_bytes();offset=elf.symbols['projection_control'][0]-0x80000000
        need(image[offset:offset+4]==bytes(4),'normal data control')
        damaged=bytearray(image);damaged[offset:offset+4]=struct.pack('<I',1);(output/'bad-tail.bin').write_bytes(damaged)
        for p,value in external.items():need(digest(p)==value,'external remains unchanged')
        for rel,value in pins.items():need(digest(REPO/rel)==value and digest(source/'repo'/rel)==value,'source remains unchanged')
        for name,value in actual.items():need(digest(source/name)==value,'compiled source remains unchanged')
        for name,value in fixture_pins.items():need(digest(fixture/name)==value,'complete fixture remains unchanged')
        for tool in toolpins.values():need(digest(tool['path'])==tool['sha256'],'tool remains unchanged')
        inspection.update(status='PROJECTION_STATIC_ELF_PASS_NOT_RUNTIME',contract=CONTRACT,source_pins=pins,external_pins=external,
            artifacts={n:digest(output/n) for n in ('forward-projection.elf','forward-projection.bin','bad-tail.bin','dump-plan.txt','kernel-identity.json','generated.json')},
            fixtures=fixture_pins,actual_source_pins=actual,kernel_identity=kernel_identity,dump_plan=plans,
            normal_control_offset=offset,am_home=str(am),reference_runs=0,target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=f.h.now();save(output/'state.json',state)

if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('projection build signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','full-build','kernel-build'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();os.sched_setaffinity(0,[3])
    result=build(args.output.resolve(),args.full_build.resolve(),args.kernel_build.resolve());print(json.dumps({k:result[k] for k in ('status','image_bytes','heap_start','reference_runs','performance_qualified')},indent=2))
