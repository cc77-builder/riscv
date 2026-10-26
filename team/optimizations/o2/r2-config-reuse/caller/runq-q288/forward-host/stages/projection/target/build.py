"""Capture real W1/classifier inputs and bind a bounded final target ELF."""
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
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('boundary_projection_build',HERE.parent/'build.py')
REPO=b.REPO
h,g=b.f.h,b.f.g
need,save,read,digest,command=b.need,b.save,b.read,b.digest,b.command
CONTRACT='r2-s3-projection-boundaries-v1'
FILES=('CONTRACT.md','main.c','export.c','Makefile.target','build.py')

def fnv(raw):
    value=14695981039346656037
    for byte in raw:value=((value^byte)*1099511628211)&((1<<64)-1)
    return value

def select_weights(raw):
    cursor=(2*6*288+288)*4
    def tensor(n):
        nonlocal cursor
        q=raw[cursor:cursor+n];cursor+=n;scales=raw[cursor:cursor+n//32*4];cursor+=n//32*4;return q,scales
    cls=tensor(32000*288);arrays=[]
    for kind in range(7):arrays.append([tensor(288*288 if kind<4 else 288*768) for _ in range(6)])
    need(cursor==len(raw),'whole original tensor inventory')
    result=[]
    for q,scales,rows,start in ((cls[0],cls[1],320,31680),(arrays[4][5][0],arrays[4][5][1],768,0)):
        for row in range(0,rows,288):
            valid=min(288,rows-row);offset=start+row
            result.append(scales[offset*36:(offset+valid)*36]+struct.pack('<f',1.0)*((288-valid)*9))
    need(len(result)==5 and all(len(x)==10368 for x in result),'five full scale windows');return b''.join(result)

def executable(path,binary):
    elf=g.ELF(path.read_bytes());need(elf.kind==2 and elf.entry==0x80000000,'actual static AM entry')
    need(all(n in elf.symbols for n in ('_start','main','_trm_init','_halt','_putc','q288_tail_vdot','q288_fused_rvv4')),'original AM and both whole kernels')
    need(not any(p[0] in (2,3,7) for p in elf.segments),'no dynamic runtime or TLS dependency')
    need(not any((v[3]&15)==10 or (v[2]==0 and v[3]>>4==1) for v in elf.symbols.values()),'no IFUNC or unresolved strong symbol')
    for s in elf.sections:
        if s[1] in (4,9) and s[2]&2:need(s[1]==4 and s[9]==24 and s[5]%24==0 and elf.section(s)==bytes(s[5]),'no live runtime relocation')
    sections=sorted((s for s in elf.sections if s[2]&2 and s[5]),key=lambda s:s[3]);need(sections[0][3]==0x80000000,'raw RAM base')
    for s in sections:need(0x80000000<=s[3]<s[3]+s[5]<=0x88000000,'whole allocated section in RAM')
    for a,z in zip(sections,sections[1:]):need(a[3]+a[5]<=z[3],'disjoint ordinary sections')
    raw=bytearray(max(s[3]+s[5] for s in sections)-0x80000000)
    for s in sections:
        if s[1]!=8:raw[s[3]-0x80000000:s[3]-0x80000000+s[5]]=elf.section(s)
    need(bytes(raw)==binary.read_bytes(),'whole ELF/raw BIN equality')
    top=elf.symbols['_stack_top'][0];stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(stack%16==0 and max(s[3]+s[5] for s in sections)<=top<=stack<heap<0x88000000,'static data stack heap bounds')
    start,size,_,_=elf.symbols['main'];pc=start;counters=[]
    while pc<start+size:
        low=struct.unpack('<H',elf.read(pc,2))[0]
        if low&3!=3:pc+=2;continue
        word=struct.unpack('<I',elf.read(pc,4))[0]
        if word&0x707f==0x2073 and (word>>15)&31==0 and word>>20 in (0xc00,0xc02):
            need(elf.read(pc-4,4)==elf.read(pc+4,4)==struct.pack('<I',0x0ff0000f),'actual IORW fences around every cycle/instret read')
            counters.append(dict(pc=hex(pc),csr=hex(word>>20)))
        pc+=4
    need([x['csr'] for x in counters]==['0xc00','0xc02','0xc02','0xc00'],'whole actual CSR measurement sequence')
    return elf,dict(image_bytes=len(raw),heap_start=hex(heap),counter_sites=counters)

def model_paths(output,source,fixture):
    q=h.Q;tail=load('boundary_tail_checker',source/'repo'/q/'fused/phased/tail/screen.py')
    # Existing independent exact-binary32 and integer models; no new ISA engine.
    model,helpers=tail.phased.support(source/'repo')
    elf=model.ELF((output/'projection-boundaries.elf').read_bytes())
    ta=tail.checker_class(model,source/'repo/team/optimizations/o2/r2-safe-tail/machine_model.py')
    fr=model.machine_class(source/'repo/team/optimizations/o2/r2-safe-tail/machine_model.py')
    packed=(fixture/'packed.bin').read_bytes();scales=(fixture/'scales.bin').read_bytes()
    x=(fixture/'input-q.bin').read_bytes();xs=(fixture/'input-scales.bin').read_bytes();gold=(fixture/'gold.bin').read_bytes()
    records=[];path=None
    for block,(case,row,valid) in enumerate(((0,0,288),(0,288,32),(1,0,288),(1,288,288),(1,576,192))):
        raw=packed[block*82944:(block+1)*82944];weight=bytearray(82944)
        for t in range(36):
            for group in range(9):
                for lane in range(8):weight[(t*8+lane)*288+group*32:(t*8+lane)*288+group*32+32]=raw[(t*9+group)*256+lane*32:(t*9+group)*256+lane*32+32]
        signed=lambda data:[v if v<128 else v-256 for v in data]
        fixture_case=dict(weight=signed(weight),packed=signed(raw),inputs=[signed(x[case*288:(case+1)*288])],
            weight_scale=list(struct.unpack('<2592I',scales[block*10368:(block+1)*10368])),
            input_scale=[list(struct.unpack('<9I',xs[case*36:(case+1)*36]))])
        expected=gold[(case*768+row)*4:(case*768+row+valid)*4]+bytes((288-valid)*4)
        golden=list(struct.unpack('<288I',expected))
        for name,cls in (('q288_tail_vdot',ta),('q288_fused_rvv4',fr)):
            m=cls(fixture_case);m.execute_function(elf,name)
            checked=m.check(golden) if name=='q288_tail_vdot' else m.check_full('rvv4',golden)
            pcs=[pc for pc,word in m.path if word&0xfe00707f==0x0200000b]
            need(len(m.path)==(49602 if name=='q288_tail_vdot' else 35670),'same complete Q function dynamic instructions')
            if name=='q288_tail_vdot':
                need(len(pcs)==10368 and (path is None or path==pcs),'identical complete TA control path on all five real blocks');path=pcs
            else:need(not pcs,'strong FR has no custom instruction')
            records.append(dict(case=case,block=block,row=row,valid=valid,function=name,**checked))
    (output/'ta-custom-pcs.bin').write_bytes(struct.pack('<10368Q',*path))
    save(output/'model-results.json',dict(status='REAL_BOUNDARIES_FINAL_ELF_MODELS_PASS',records=records,
        expected_custom_per_q=10368,expected_normal_custom=207360,expected_negative_custom=41472,
        ta_custom_pc_sha256=digest(output/'ta-custom-pcs.bin'),target_emu_runs=0))

def build(output,projection_build,projection_campaign):
    need(not output.exists() and not output.is_relative_to(REPO),'fresh isolated target build')
    parent=read(projection_build/'result.json');need(parent['status']=='PROJECTION_STATIC_ELF_PASS_NOT_RUNTIME','fixed complete consumer build')
    campaign=read(projection_campaign/'results.json');state=read(projection_campaign/'state.json')
    need(campaign['status']==state['status']=='FULL_PROJECTION_REFERENCE_CAMPAIGN_PASS' and state['active_pid'] is None,'completed full consumer reference qualification')
    run_inputs=read(projection_campaign/'runtime-inputs.json')
    for name,value in parent['artifacts'].items():need(digest(projection_build/name)==run_inputs[str(projection_build/name)]==value,'same actual complete consumer qualified artifact')
    for rel,value in parent['source_pins'].items():need(digest(REPO/rel)==value,'unchanged full consumer source')
    am=Path(parent['am_home']);need(not output.is_relative_to(am),'official AM outside output')
    need(subprocess.check_output(['git','-C',am,'rev-parse','HEAD'],text=True).strip()=='086a238062fdfb3281b745a537b361983d0154b5','same official AM revision')
    need(not subprocess.check_output(['git','-C',am,'status','--porcelain','--untracked-files=no'],text=True).strip(),'official AM unchanged')
    tail=load('boundary_frozen_tail',REPO/h.Q/'fused/phased/tail/screen.py')
    pins=dict(parent['source_pins']);pins.update(tail.source_files(REPO))
    for p in [*(HERE/n for n in FILES),HERE.parent/'build.py']:
        rel=str(p.relative_to(REPO));value=digest(p);need(rel not in pins or pins[rel]==value,'no rebinding inherited source identity');pins[rel]=value
    external=dict(parent['external_pins'])
    for p in (projection_build/'result.json',projection_build/'source/fused.S',projection_campaign/'results.json',projection_campaign/'state.json',projection_campaign/'runtime-inputs.json'):
        external[str(p)]=digest(p)
    for name,value in parent['fixtures'].items():external[str(projection_build/'fixture'/name)]=value
    for p,value in external.items():need(digest(p)==value,'fixed external input')
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='BUILDING',started=h.now());save(output/'state.json',state)
    try:
        source=output/'source';source.mkdir()
        for rel,value in pins.items():
            dest=source/'repo'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,dest);need(digest(dest)==value,'exact source snapshot')
        save(output/'source-pins.json',pins);save(output/'external-pins.json',external)
        local=source/'repo'/HERE.relative_to(REPO);forward=source/'repo'/h.Q/'forward-host'
        for name in ('main.c','export.c'):shutil.copyfile(local/name,source/name)
        shutil.copyfile(local/'Makefile.target',source/'Makefile');shutil.copyfile(forward/'stages/full/state_layout.h',source/'state_layout.h')
        for rel,name in ((h.Q/'q288.h','q288.h'),(h.Q.parent/'split/split.h','split.h'),(h.Q.parent/'caller.h','caller.h')):shutil.copyfile(source/'repo'/rel,source/name)
        shutil.copyfile(projection_build/'source/fused.S',source/'fused.S')
        proof=h.gen.generate(forward/'upstream/runq.c',source/'forward.inc');save(output/'forward-generation.json',proof)
        tools={n:shutil.which('riscv64-linux-gnu-'+n) for n in ('gcc','ld','ar','objcopy','objdump','readelf')}
        tools.update(host_gcc=shutil.which('gcc'),make=shutil.which('make'));need(all(tools.values()),'native installed tools')
        toolpins={n:dict(path=p,resolved=str(Path(p).resolve()),sha256=digest(p)) for n,p in tools.items()};save(output/'tools.json',toolpins)
        flags=['-std=gnu11','-O2','-fno-builtin','-ffp-contract=off','-fno-fast-math','-frounding-math','-fno-lto','-fno-tree-vectorize','-fno-tree-slp-vectorize']
        command([tools['host_gcc'],*flags,source/'export.c',source/'repo'/h.Q/'acc8/q288.c','-I'+str(source),
            '-I'+str(forward),'-I'+str(forward.parent),'-I'+str(source/'repo'/h.Q.parent/'split'),'-I'+str(source/'repo'/h.Q.parent),'-lm','-o',output/'export-fixture'],output,'host-compile')
        fixture=output/'fixture';fixture.mkdir();command([output/'export-fixture',fixture],output,'host-export',timeout=180)
        need((output/'host-export.stdout.log').read_text()=='PROJECTION_BOUNDARY_EXPORT_PASS positions=3 full_state_bytes=3691424 cases=2 rows=320,768\n','exact full call-site capture')
        for name in ('weights.bin','embedding.bin',*(f'host-state-p{p}.bin' for p in range(3))):
            need(digest(fixture/name)==parent['fixtures'][name],'new capture equals frozen complete original reference: '+name)
        packed,tail_scales,layout=b.expected_pack((fixture/'weights.bin').read_bytes())
        need(h.sha(packed)==parent['fixtures']['expected-packed.bin'] and h.sha(tail_scales)==parent['fixtures']['expected-tail-scales.bin'],'same independently reconstructed full pack')
        selected=(170,171,39,40,41);(fixture/'packed.bin').write_bytes(b''.join(packed[i*82944:(i+1)*82944] for i in selected))
        (fixture/'scales.bin').write_bytes(select_weights((fixture/'weights.bin').read_bytes()))
        need((fixture/'expected-flags.bin').read_bytes()==struct.pack('<2I',1,1),'host original matrix NX-only flags')
        state2=(fixture/'host-state-p2.bin').read_bytes()
        need((fixture/'input-q.bin').read_bytes()[:288]==state2[9600:9888] and
             (fixture/'input-scales.bin').read_bytes()[:36]==state2[9888:9924],'classifier input equals final actual quantizer output')
        sizes={'input-q':576,'input-scales':72,'packed':5*82944,'scales':5*10368,'gold':2*768*4}
        asm=['.section .rodata.boundary_fixture,"a"','.balign 64']
        for name,size in sizes.items():
            need((fixture/(name+'.bin')).stat().st_size==size,'exact whole fixture size')
            symbol='tile_'+name.replace('-','_');symbol='tile_input_scales' if name=='input-scales' else symbol
            asm += [f'.global {symbol}',f'{symbol}:',f'.incbin "{fixture/(name+".bin")}"',f'.global {symbol}_end',f'{symbol}_end:','.balign 64']
        (source/'fixture.S').write_text('\n'.join(asm)+'\n')
        actual={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file() and not p.is_relative_to(source/'repo')}
        fixture_pins={p.name:digest(p) for p in fixture.iterdir() if p.is_file()};save(output/'actual-source-pins.json',actual)
        command(['ldd',output/'export-fixture'],output,'host-libraries')
        hostlibs={str(Path(p).resolve()):digest(p) for p in re.findall(r'(/[^\s()]+)',(output/'host-libraries.stdout.log').read_text()) if Path(p).is_file()}
        keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        clean=['env',*[v for k in keys for v in ('-u',k)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        command([*clean,tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
            'CROSS_COMPILE='+tools['gcc'][:-3],'BOUNDARY_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'projection-boundaries'),
            '-o','am','-o','klib','-j1','image'],output,'target-build',timeout=180)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'projection-boundaries.elf'],output,'metadata')
        command([tools['objdump'],'-drwC',output/'projection-boundaries.elf'],output,'disassembly')
        elf,inspection=executable(output/'projection-boundaries.elf',output/'projection-boundaries.bin')
        functions=b.kernel_bytes(output/'projection-boundaries.elf',parent['kernel_identity']['functions'])
        for name,raw in functions.items():need(len(raw)==parent['kernel_identity']['functions'][name]['bytes'] and h.sha(raw)==parent['kernel_identity']['functions'][name]['sha256'],'whole qualified function bytes unchanged')
        for name in sizes:
            symbol='tile_'+name.replace('-','_');address=elf.symbols[symbol][0];end=elf.symbols[symbol+'_end'][0];raw=(fixture/(name+'.bin')).read_bytes()
            need(end-address==len(raw) and elf.read(address,len(raw))==raw,'actual linked complete fixture identity')
        image=(output/'projection-boundaries.bin').read_bytes();offset=elf.symbols['tile_control'][0]-0x80000000
        need(image[offset:offset+4]==bytes(4),'normal immutable control');bad=bytearray(image);bad[offset:offset+4]=struct.pack('<I',1);(output/'bad-tail.bin').write_bytes(bad)
        model_paths(output,source,fixture)
        for p,value in external.items():need(digest(p)==value,'external unchanged after build')
        for rel,value in pins.items():need(digest(REPO/rel)==value and digest(source/'repo'/rel)==value,'source unchanged after build')
        for name,value in actual.items():need(digest(source/name)==value,'compiled source unchanged')
        for name,value in fixture_pins.items():need(digest(fixture/name)==value,'captured fixture unchanged')
        for tool in toolpins.values():need(digest(tool['path'])==tool['sha256'],'tool unchanged')
        for path,value in hostlibs.items():need(digest(path)==value,'host library unchanged')
        golden=(fixture/'gold.bin').read_bytes()
        inspection.update(status='PROJECTION_BOUNDARY_STATIC_ELF_AND_MODELS_PASS_NOT_RUNTIME',contract=CONTRACT,source_pins=pins,
            actual_source_pins=actual,external_pins=external,host_libraries=hostlibs,fixtures=fixture_pins,kernel_identity=parent['kernel_identity'],
            cases=[dict(id=0,name='classifier-last320',position=2,rows=320,first_row=31680,blocks=2,golden_fnv=f'{fnv(golden[:1280]):016x}'),
                   dict(id=1,name='layer5-w1',position=2,layer=5,rows=768,blocks=3,golden_fnv=f'{fnv(golden[3072:6144]):016x}')],
            artifacts={n:digest(output/n) for n in ('projection-boundaries.elf','projection-boundaries.bin','bad-tail.bin','metadata.stdout.log','disassembly.stdout.log','forward-generation.json','model-results.json','ta-custom-pcs.bin')},
            normal_control_offset=offset,am_home=str(am),target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=digest(output/'result.json'));return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished']=h.now();save(output/'state.json',state)

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(InterruptedError('boundary build interrupted')))
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','projection-build','projection-campaign'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();os.sched_setaffinity(0,[3])
    result=build(args.output.resolve(),args.projection_build.resolve(),args.projection_campaign.resolve());print(json.dumps({k:result[k] for k in ('status','image_bytes','cases','counter_sites')},indent=2))
