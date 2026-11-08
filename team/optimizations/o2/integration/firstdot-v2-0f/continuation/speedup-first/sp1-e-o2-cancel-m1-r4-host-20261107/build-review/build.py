#!/usr/bin/env python3
"""Compile/link only. Reuses existing read-only AM archives without make recursion."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'software'
AM=Path('/home/riscv/riscv-lab/xs-env/nexus-am')
OUT=ROOT/'build-review'/sys.argv[1]
OUT.mkdir(exist_ok=False)
(OUT/'source').mkdir()
for p in SRC.iterdir():
    if p.is_file(): shutil.copyfile(p,OUT/'source'/p.name)
def pin(p):
    p=Path(p); data=p.read_bytes()
    return {'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
archive_paths=[AM/'am/build/am-riscv64-xs.a',AM/'libs/klib/build/klib-riscv64-xs.a']
deps=archive_paths+[AM/'am/src/nemu/isa/riscv/boot/loader64.ld', AM/'am/src/nemu/ldscript/section.ld']
commands=[]
for name in ['gcc','ld','objdump','objcopy','readelf','nm','ar']:
    deps.append(Path(shutil.which('riscv64-linux-gnu-'+name)).resolve())
before=[pin(p) for p in deps]
(OUT/'DEPENDENCIES_BEFORE.json').write_text(json.dumps(before,indent=2)+'\n')
def run(argv, name):
    started=time.time()
    proc=subprocess.run(argv,cwd=SRC,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    (OUT/(name+'.stdout')).write_bytes(proc.stdout)
    (OUT/(name+'.stderr')).write_bytes(proc.stderr)
    receipt={'argv':argv,'cwd':str(SRC),'exit_code':proc.returncode,'elapsed_seconds':time.time()-started}
    commands.append(receipt)
    (OUT/'COMMANDS.json').write_text(json.dumps(commands,indent=2)+'\n')
    if proc.returncode: raise RuntimeError(f'{name} failed: {proc.returncode}')
    return proc.stdout
includes=[SRC, AM/'libs/klib/include', AM/'am', AM/'am/include', AM/'am/src/nemu/include', AM/'am/src/xs/include']
common=['-fno-pic','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany']+['-I'+str(p) for p in includes]
cflags=['-O2','-MMD','-Wall','-Werror','-ggdb','-std=gnu11','-static','-ffreestanding','-fno-builtin','-fno-stack-protector',
        '-fno-asynchronous-unwind-tables','-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-tree-loop-distribute-patterns',
        '-Wno-main','-D__ISA__="riscv64"','-D__ISA_RISCV64__','-D__PLATFORM__="xs"','-D__PLATFORM_XS__',
        '-D__ARCH__=riscv64-xs','-D__ARCH_RISCV64_XS','-DARCH_H="arch/riscv64-xs.h"','-DISA_H="riscv.h"']
status='FAIL_BUILD'
try:
    for name in ('main','judge','data'):
        run(['riscv64-linux-gnu-gcc',*common,*cflags,'-c',str(SRC/(name+'.c')),'-o',str(OUT/(name+'.o'))],name)
    run(['riscv64-linux-gnu-gcc',*common,'-O0','-MMD','-c',str(SRC/'kernels.S'),'-o',str(OUT/'kernels.o')],'kernels')
    elf=OUT/'o2-cancel.elf'
    run(['riscv64-linux-gnu-ld','-melf64lriscv','-L'+str(AM/'am/src/nemu/ldscript'),'-T',str(deps[2]),'--gc-sections',
         '-Map='+str(OUT/'o2-cancel.map'),'-o',str(elf),'--start-group',*[str(OUT/(n+'.o')) for n in ('main','judge','data','kernels')],
         *map(str,archive_paths),'--end-group'],'link')
    for stem in ('kernels.o','o2-cancel.elf'):
        run(['riscv64-linux-gnu-objdump','-d','-M','no-aliases',str(OUT/stem)],stem+'.objdump')
        run(['riscv64-linux-gnu-readelf','-h','-S','-A','-r',str(OUT/stem)],stem+'.readelf')
        run(['riscv64-linux-gnu-nm','-n','-S',str(OUT/stem)],stem+'.nm')
    run(['riscv64-linux-gnu-objcopy','-S','--set-section-flags','.bss=alloc,contents','-O','binary',str(elf),str(OUT/'o2-cancel.bin')],'objcopy')
    for index,p in enumerate(archive_paths): run(['riscv64-linux-gnu-ar','t',str(p)],f'archive-{index}')
    status='PASS_GNU_BUILD_ONLY'
finally:
    after=[pin(p) for p in deps]
    (OUT/'DEPENDENCIES_AFTER.json').write_text(json.dumps(after,indent=2)+'\n')
    if before!=after: status='FAIL_DEPENDENCY_DRIFT'
    (OUT/'RESULT.json').write_text(json.dumps({'status':status,'target_runs':0,'native_reference_loads':0,
        'shared_dependency_unchanged':before==after,'commands':len(commands),'outputs':[pin(p) for p in OUT.iterdir() if p.suffix in ('.o','.elf','.bin')]},indent=2)+'\n')
    print(status)
