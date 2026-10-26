"""Build the bounded libm/TLS smoke using unchanged prebuilt AM libraries."""
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
h=load('math_smoke_commands',HERE.parent/'check.py')
g=load('math_smoke_elf_reader',REPO/'team/optimizations/o2/r2-safe-tail/linked_gate.py')
need,sha,save,command=h.need,h.sha,h.save,h.command
CONTRACT='r2-s3-forward-math-smoke-v1'
FILES=('build_smoke.py','math_eval.h','math_eval.c','smoke_gold.c','math_smoke.c','guard_control.c',
       'tls_main.S','smoke_makefile','SMOKE-CONTRACT.md')


def f(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def d(value):return struct.unpack('<Q',struct.pack('<d',value))[0]


def inputs():
    # kind, NaN mask, required/allowed RISC-V fflags, raw argument a,b
    normal=[(0,f(10000),f(.5)),(0,f(10000),0x3d2aaaab),(1,f(0),0),(1,f(.5),0),
            (2,f(.5),0),(3,f(1),0),(4,f(1),0),(5,f(48),0),(6,f(-.5),0),(6,f(.5),0),
            (7,d(-2.5),0),(7,d(2.5),0),(8,0x80000000,0),(9,d(-2),0),(4,f(-1),0),(5,f(4),0)]
    rows=[(kind,0,0,1,a,b) for kind,a,b in normal]
    rows += [(5,1,16,16,f(-1),0),(1,1,16,16,0x7f800000,0),(2,1,16,16,0x7f800000,0),
             (3,3,16,16,0x7f800000,0),(0,1,16,16,f(-1),f(.5)),(0,0,8,8,f(0),f(-1)),
             (4,0,5,5,f(1000),0),(4,0,3,3,f(-1000),0)]
    need(len(rows)==24 and set(r[0] for r in rows)==set(range(10)),'complete fixed math cases')
    need(rows[0][1]==0 and all(0<=r[0]<10 and r[1] in (0,1,3) and
         (r[1]==0 or r[0] not in (7,9)) and (r[1]!=3 or r[0]==3) and r[2]&~r[3]==0
         for r in rows),'valid types, NaN masks, controls and exception policy')
    return rows


def executable(path,binary,metadata):
    elf=g.ELF(path.read_bytes());need(elf.kind==2 and elf.entry==0x80000000,'static AM executable entry')
    need(all(n in elf.symbols for n in ('_start','main','_trm_init','_halt','_putc','team_math_main')),'actual AM runtime')
    need(not any(p[0] in (2,3) for p in elf.segments),'no dynamic linker')
    inert_relocations=0
    for section in elf.sections:
        if section[1] not in (4,9) or not section[2]&2:continue
        need(section[1]==4 and section[9]==24 and section[5]%24==0,'explicit RELA layout')
        raw=elf.section(section)
        need(raw==bytes(len(raw)),'no runtime relocation; only all-zero R_RISCV_NONE placeholders')
        inert_relocations+=section[5]//24
    need(not any((v[3]&15)==10 for v in elf.symbols.values()),'no IFUNC')
    need('__tls_get_addr' not in elf.symbols,'no dynamic TLS getter')
    tls=[p for p in elf.segments if p[0]==7]
    need(len(tls)==1,'one TLS template')
    _,_,offset,address,physical,filesz,memsz,align=tls[0]
    need(filesz==0 and 0<memsz<=64 and 0<align<=16 and align&(align-1)==0 and address%align==0,'zero-only small aligned TLS template')
    symbols={n:v for n,v in elf.symbols.items() if v[3]&15==6}
    need(set(symbols)=={'errno'},'only errno needs TLS')
    errno_offset,size,index,_=symbols['errno']
    need(size==4 and errno_offset%4==0 and errno_offset+size<=memsz,'bounded errno TLS offset')
    need(elf.sections[index][1]==8 and elf.sections[index][2]&0x400,'errno is TLS NOBITS')
    allocated=[s for s in elf.sections if s[2]&2 and s[5] and not s[2]&0x400]
    allocated.sort(key=lambda s:s[3])
    need(allocated and allocated[0][3]==0x80000000,'fixed raw image base')
    for s in allocated:need(0x80000000<=s[3]<s[3]+s[5]<=0x88000000,'ordinary allocation inside 128MB RAM')
    for left,right in zip(allocated,allocated[1:]):need(left[3]+left[5]<=right[3],'ordinary loaded sections do not overlap')
    image=bytearray(max(s[3]+s[5] for s in allocated)-0x80000000)
    for s in allocated:
        if s[1]!=8:image[s[3]-0x80000000:s[3]-0x80000000+s[5]]=elf.section(s)
    need(bytes(image)==binary.read_bytes(),'raw image exactly matches ordinary allocated ELF sections')
    area,length,_,_=elf.symbols['team_tls_area']
    stacktop=elf.symbols['_stack_top'][0];stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(length==96 and area%16==0 and area+length<=stacktop<=stack<heap<0x88000000,'TLS area, stack and heap boundaries')
    text=metadata.read_text()
    need('TLS_GD' not in text and 'TLSDESC' not in text and 'IRELATIVE' not in text,'only bounded static TLS model')
    sites=[]
    for line in text.splitlines():
        if 'R_RISCV_TLS_GOT_HI20' not in line:continue
        need('errno' in line,'only errno IE relocation')
        pc=int(line.split()[0],16);hi,lo=struct.unpack('<II',elf.read(pc,8))
        need(hi&0x7f==0x17 and lo&0x707f==0x3003 and ((lo>>15)&31)==((hi>>7)&31),'actual AUIPC/LD IE address pair')
        high=hi&0xfffff000;high=high-(1<<32) if high&(1<<31) else high
        low=lo>>20;low=low-4096 if low&2048 else low
        got=pc+high+low;value=struct.unpack('<q',elf.read(got,8))[0]
        need(value==errno_offset,'final IE GOT contains exact errno offset from tp')
        sites.append(dict(pc=hex(pc),got=hex(got),offset=value))
    need(len(sites)==2,'both selected libm errno IE sites resolved')
    return elf,dict(status='MATH_SMOKE_STATIC_ELF_PASS_NOT_RUNTIME',tls_program_header=list(tls[0]),
                    errno_offset=errno_offset,tls_area=hex(area),tls_storage=hex(area+16),tls_capacity=64,
                    ie_sites=sites,inert_relocation_placeholders=inert_relocations,
                    stack_top=hex(stacktop),stack_pointer=hex(stack),heap_start=hex(heap))


def build(output,parent_build,closure):
    need(not output.exists() and not output.is_relative_to(REPO),'fresh build outside source')
    parent=json.loads((parent_build/'build.json').read_text());am=Path(parent['am_home'])
    need(not output.is_relative_to(am) and not output.is_relative_to(parent_build) and not output.is_relative_to(closure),'output outside protected inputs')
    need(parent['accepted'] is True and parent['am_revision']=='086a238062fdfb3281b745a537b361983d0154b5','qualified immutable AM parent')
    need(subprocess.check_output(['git','-C',str(am),'rev-parse','HEAD'],text=True).strip()==parent['am_revision'],'fixed official AM revision')
    need(not subprocess.check_output(['git','-C',str(am),'status','--porcelain=v1','--untracked-files=no'],text=True).strip(),'official AM unchanged')
    external=dict(parent['external_files'])
    for rel in ('Makefile.app','Makefile.compile','Makefile.check','am/arch/riscv64-xs.mk','am/arch/isa/riscv64.mk',
                'am/src/nemu/isa/riscv/boot/loader64.ld','am/src/nemu/ldscript/section.ld'):
        external[str(am/rel)]=sha((am/rel).read_bytes())
    archive=json.loads((closure/'archive.json').read_text());external[archive['path']]=archive['sha256']
    for name,digest in external.items():need(sha(Path(name).read_bytes())==digest,'fixed dependency: '+name)
    output.mkdir(parents=True);state=dict(contract=CONTRACT,status='STARTED',started_at=h.now(),target_runtime_ready=False)
    save(output/'state.json',state)
    try:
        files=[HERE/name for name in FILES]+[HERE.parent/'check.py',HERE.parent/'generate.py',REPO/'team/optimizations/o2/r2-safe-tail/linked_gate.py']
        pins={str(p.relative_to(REPO)):sha(p.read_bytes()) for p in files}
        source=output/'source';source.mkdir()
        for p in files:
            target=source/'repo'/p.relative_to(REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        for name in FILES:
            if name.endswith(('.c','.h','.S')):shutil.copyfile(HERE/name,source/name)
        shutil.copyfile(HERE/'smoke_makefile',source/'Makefile')
        rows=inputs()
        header=['#include "math_eval.h"',f'#define MATH_CASES {len(rows)}','static const struct math_input math_inputs[MATH_CASES] = {']
        header += ['{'+','.join(str(x) if j<4 else 'UINT64_C(0x%016x)'%x for j,x in enumerate(row))+'},' for row in rows]
        (source/'math_inputs.h').write_text('\n'.join(header+['};','']))
        save(output/'inputs.json',rows);save(output/'source-pins.json',pins);save(output/'external-pins.json',external)
        host=shutil.which('gcc');cross=shutil.which('riscv64-linux-gnu-gcc');make=shutil.which('make')
        need(host and cross and make,'installed host and target tools')
        prefix=cross[:-3];tools={'host-gcc':host,'gcc':cross,'make':make}
        tools.update({n:prefix+n for n in ('ld','ar','nm','readelf','objdump','objcopy')})
        toolpins={n:dict(path=p,resolved=str(Path(p).resolve()),sha256=sha(Path(p).read_bytes())) for n,p in tools.items()}
        save(output/'tools.json',toolpins)
        flags=['-std=gnu11','-O2','-fno-builtin','-ffp-contract=off','-fno-fast-math','-fno-lto']
        command([host,*flags,source/'smoke_gold.c',source/'math_eval.c','-I'+str(source),'-lm','-o',output/'host-gold'],output,'host-compile')
        command([output/'host-gold'],output,'host-gold')
        command(['ldd',output/'host-gold'],output,'host-libraries')
        hostlibs={str(Path(p).resolve()):sha(Path(p).read_bytes()) for p in re.findall(r'(/[^\s()]+)',(output/'host-libraries.stdout.log').read_text()) if Path(p).is_file()}
        expected=[]
        for i,line in enumerate((output/'host-gold.stdout.log').read_text().splitlines()):
            number,a,b,error,exceptions=line.split();need(int(number)==i,'complete ordered host goldens')
            expected.append((int(a,16),int(b,16),int(error),int(exceptions)))
        need(len(expected)==24 and [x[2] for x in expected[:16]]==[12345]*16 and [x[2] for x in expected[16:]]==[33]*5+[34]*3,'normal sentinel and actual eight domain/range writes')
        lines=['static const struct math_expected math_expected[MATH_CASES] = {']
        lines += ['{UINT64_C(0x%016x),UINT64_C(0x%016x),%d,%d},'%r for r in expected]
        (source/'math_expected.h').write_text('\n'.join(lines+['};','']))
        clean_keys=('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD')
        clean=['env',*[item for key in clean_keys for item in ('-u',key)],'AM_HOME='+str(am),'LINUX_GNU_TOOLCHAIN=1']
        # --emit-relocs retains static audit records; none are loadable runtime relocations.
        command([*clean,make,'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
                 'CROSS_COMPILE='+prefix,'MATH_OBJ_ROOT='+str(output/'objects'),'BINARY='+str(output/'math-smoke'),
                 'MATH_ARCHIVE='+archive['path'],'-o','am','-o','klib','-j1','image'],
                output,'target-build',timeout=180)
        command([tools['readelf'],'-W','-h','-A','-l','-s','-r',output/'math-smoke.elf'],output,'target-metadata')
        command([tools['objdump'],'-drwC',output/'math-smoke.elf'],output,'target-disassembly')
        elf,inspection=executable(output/'math-smoke.elf',output/'math-smoke.bin',output/'target-metadata.stdout.log')
        # Real ELF rejection: a nominally inert record becomes a runtime fixup.
        relas=[s for s in elf.sections if s[1]==4 and s[2]&2 and s[5]]
        need(relas,'this installed linker has its recorded R_NONE placeholder')
        damaged=bytearray(elf.raw);struct.pack_into('<Q',damaged,relas[0][4]+8,3)
        (output/'bad-runtime-relocation.elf').write_bytes(damaged)
        try:
            executable(output/'bad-runtime-relocation.elf',output/'math-smoke.bin',output/'target-metadata.stdout.log')
            raise AssertionError('nonzero runtime relocation accepted')
        except ValueError as error:
            need('no runtime relocation' in str(error),'specific relocation rejection')
            save(output/'relocation-negative.json',dict(status='EXPECTED_REJECTION',reason=str(error),sha256=sha(damaged)))
        need(elf.symbol_data('math_inputs')==b''.join(struct.pack('<4I2Q',*r) for r in rows),'compiled exact raw math inputs')
        need(elf.symbol_data('math_expected')==b''.join(struct.pack('<QQiI',*r) for r in expected),'compiled exact host goldens')
        meta=(output/'target-metadata.stdout.log').read_text()
        need('__stack_chk_fail' in meta and 'team_guard_control' in elf.symbols,'real guarded negative path linked')
        image=(output/'math-smoke.bin').read_bytes();control=elf.symbols['math_control'][0]-0x80000000
        need(image[control:control+4]==bytes(4),'canonical normal control value')
        controls=[]
        for value,name in ((1,'bad-golden'),(2,'bad-guard')):
            changed=bytearray(image);changed[control:control+4]=struct.pack('<I',value)
            (output/(name+'.bin')).write_bytes(changed)
            controls.append(dict(name=name,mode=value,offset=control,sha256=sha(changed)))
        for name,digest in external.items():need(sha(Path(name).read_bytes())==digest,'dependency remains unchanged')
        for rel,digest in pins.items():need(sha((REPO/rel).read_bytes())==digest and sha((source/'repo'/rel).read_bytes())==digest,'source and snapshot remain unchanged')
        for p,digest in hostlibs.items():need(sha(Path(p).read_bytes())==digest,'host libm remained fixed')
        for t in toolpins.values():need(str(Path(t['path']).resolve())==t['resolved'] and sha(Path(t['path']).read_bytes())==t['sha256'],'tools remained fixed')
        inspection.update(contract=CONTRACT,source_pins=pins,external_pins=external,host_libraries=hostlibs,
                          artifacts={name:sha((output/name).read_bytes()) for name in ('math-smoke.elf','math-smoke.bin','bad-golden.bin','bad-guard.bin')},
                          controls=controls,inputs=rows,expected=expected,am_home=str(am),
                          target_runtime_ready=False,target_emu_runs=0,performance_qualified=False)
        save(output/'result.json',inspection);state.update(status=inspection['status'],result_sha256=sha((output/'result.json').read_bytes()))
        return inspection
    except BaseException as error:state.update(status='FAILED',error=repr(error));raise
    finally:state['finished_at']=h.now();save(output/'state.json',state)


if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('smoke build signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--parent-build',type=Path,required=True);p.add_argument('--closure',type=Path,required=True)
    args=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    result=build(args.output.resolve(),args.parent_build.resolve(),args.closure.resolve())
    print(json.dumps({k:result[k] for k in ('status','errno_offset','ie_sites','target_runtime_ready')},indent=2))
