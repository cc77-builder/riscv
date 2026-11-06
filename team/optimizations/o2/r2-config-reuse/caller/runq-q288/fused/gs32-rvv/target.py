"""Generate, compile and inspect one GS32/TA/FR target image.

Reuses the unchanged team fixture, guest judge and timer. Runtime scheduling is
separate; this file never launches an EMU or rebuilds the immutable AM libraries.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import time

import generate
import screen

CONTRACT = 'r2-s3-runq-gs32-rvv-target-v1'
ORDER = (2, 0, 1, 2, 2, 1, 0, 2)
WRAPPERS = (generate.NAME, 'q288_tail_vdot', 'q288_fused_rvv4')
METHODS = (5, 0, 5)
NEED = generate.need
REL = generate.REL
BASE_PINS = {
    'phased/tail/target/generate.py':'8369f553aaf642cb2de84ca40506e04f67b5458c6c3992f4d540dc5af7c1c9b5',
    'phased/tail/target/main.c':'39b1e2910d6e01ee0894895425f588fa9b6a85853d6b3fb32e866719f61c5390',
    'phased/target/generate.py':'410137991477f8f77ec5ca918e4067697f20a10daf3f48ea3e1fc1eb6c165618',
    'target/generate.py':'e9d5771c267b3544a5b37d239cf82ab047bd1fa32eff0e2e1f634a21fabc753c',
    'phased/candidate.py':'2b487c60b53e25dbc04eba4c2eac4bd175e1573837863194de463d6a27df2399',
    'phased/tail/candidate.py':'3a75e09640fdf789c11cf8a9050cd716ca3fde12732cb500f3f123adb0b50697',
}
FUNCTION_PINS = {
    'q288_fused_rvv4':'66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab',
    'q288_tail_vdot':'b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3',
}
LIB_PINS = {
    'am/build/am-riscv64-xs.a':'57501f59d55d1b15116d9022ffc2d5efcc74bcde8c5674d7f31db0714e04b933',
    'libs/klib/build/klib-riscv64-xs.a':'f45d8c2049384123642b8c5d4a86f46be285d785ac5d16438eee510347eafda1',
    'am/src/nemu/isa/riscv/boot/loader64.ld':'fe4ba29b61bc7dfba5c79a2fce331a22026ac74ead7c91296c60e24108392eab',
    'am/src/nemu/ldscript/section.ld':'7a203251fc9ea3e34e615bd8d8587d18022bf053cbe60e1eb0689299a7bb4152',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def produce(repo, out):
    for name, pin in BASE_PINS.items():
        NEED(sha((repo/REL/name).read_bytes()) == pin, 'unchanged generator input ' + name)
    parent = screen.load('gs32_target_base', repo/REL/'phased/tail/target/generate.py',
                         BASE_PINS['phased/tail/target/generate.py'])
    manifest = parent.generate(repo, out)
    NEED(tuple(x['index'] for x in manifest['plan']) == ORDER, 'unchanged balanced window order')
    old_header = (out/'data.h').read_text()
    changes = {
        '#define Q_CONTRACT "'+parent.CONTRACT+'"':'#define Q_CONTRACT "'+CONTRACT+'"',
        'q_wrapper const q_wrappers[3] = {q288_phased_vdot,q288_tail_vdot,q288_fused_rvv4};':
            'q_wrapper const q_wrappers[3] = {'+','.join(WRAPPERS)+'};',
        'static const unsigned q_methods[3] __attribute__((aligned(16),used)) = {0,0,5};':
            'static const unsigned q_methods[3] __attribute__((aligned(16),used)) = {5,0,5};',
        'typedef void (*q_wrapper)(struct q288_context *);':
            'extern void '+generate.NAME+'(struct q288_context *);\ntypedef void (*q_wrapper)(struct q288_context *);',
    }
    header = old_header
    for before, after in changes.items():
        NEED(header.count(before) == 1, 'one generated header replacement')
        header = header.replace(before, after)
    (out/'data.h').write_text(header)
    shell, public = generate.load_parent(repo)
    assembly = (out/'fused.S').read_text()
    NEED(generate.NAME not in assembly, 'new function is absent before appending')
    (out/'fused.S').write_text(assembly+generate.function(shell, public))
    manifest['rows'][0].update(algorithm=5,method='rvv',variant='gs32',label='gs32-rvv',
                               dots=0,leaf=parent.parent.NEW[5],wrapper=generate.NAME)
    manifest.update(contract=CONTRACT,expected_dots=62209,
        statistics='two reverse-order GS32/TA observations and all four FR anchors; replay is not a new sample',
        selection_scope='GS32 versus unchanged TA and unchanged FR in this ELF',
        changed_candidate_function_words=None,candidate_instruction_count_change=None,
        structural_hypothesis='one full-GS32 widening reduction per output row; no new ISA or layout',
        parallel_policy='one single-thread EMU per isolated process; all required normal observations retained')
    NEED(sum(manifest['rows'][c['arm']]['dots'] for c in manifest['call_plan'])+1 == 62209,
         'derived full-campaign dot8 count')
    NEED(sha((out/'main.c').read_bytes()) == BASE_PINS['phased/tail/target/main.c'],
         'guest judge unchanged byte for byte')
    save(out/'manifest.json', manifest)
    # Read-only generator modules and explicit immutable producer inputs.
    inputs = {str(repo/REL/name):pin for name,pin in BASE_PINS.items()}
    for module in list(sys.modules.values()):
        file = getattr(module, '__file__', None)
        if file and Path(file).is_file() and Path(file).resolve().is_relative_to(repo):
            inputs[str(Path(file).resolve())] = sha(Path(file).read_bytes())
    for name, pin in parent.parent.INPUT_PINS.items():
        inputs[str(repo/name)] = pin
    save(out/'producer-inputs.json', inputs)
    return manifest


def command(argv, out, label):
    start = time.monotonic()
    p = subprocess.run([str(x) for x in argv], cwd=out, capture_output=True, timeout=120)
    (out/(label+'.stdout.log')).write_bytes(p.stdout)
    (out/(label+'.stderr.log')).write_bytes(p.stderr)
    record = dict(argv=[str(x) for x in argv],returncode=p.returncode,
                  elapsed_seconds=time.monotonic()-start,
                  stdout_sha256=sha(p.stdout),stderr_sha256=sha(p.stderr))
    save(out/(label+'.json'),record)
    NEED(p.returncode == 0, 'command failed '+label+': '+p.stderr.decode(errors='replace'))
    return record


def build(repo, am, out, jobs):
    NEED(not out.exists() and not out.is_relative_to(repo), 'fresh isolated build')
    NEED(1 <= jobs <= 4, 'global budget permits at most four compile workers')
    out.mkdir(parents=True)
    for name,pin in LIB_PINS.items():
        NEED(sha((am/name).read_bytes()) == pin, 'pinned immutable AM input '+name)
    produce(repo, out/'source')
    source = out/'source'
    objects = out/'objects'; objects.mkdir()
    cc = shutil.which('riscv64-linux-gnu-gcc')
    ld = shutil.which('riscv64-linux-gnu-ld')
    objcopy = shutil.which('riscv64-linux-gnu-objcopy')
    NEED(all((cc,ld,objcopy)), 'GNU target tools available')
    common = [cc,'-fno-pic','-march=rv64gv','-mcmodel=medany','-mabi=lp64d','-mno-relax','-I'+str(source)]
    cflags = ['-std=gnu11','-ffreestanding','-fno-tree-vectorize','-fno-tree-slp-vectorize',
              '-fno-tree-loop-distribute-patterns','-fno-ipa-cp','-fno-ipa-icf',
              '-fno-optimize-sibling-calls','-fno-lto','-ffp-contract=off','-fno-fast-math',
              '-static','-O2','-Wall','-Werror','-fno-asynchronous-unwind-tables',
              '-fno-builtin','-fno-stack-protector','-Wno-main']
    units = ('main.c','q288.c','oracle.c','timers.S','kernels.S','fused.S')
    def compile_one(name):
        flags = cflags if name.endswith('.c') else ['-O0']
        return command(common+flags+['-c',source/name,'-o',objects/(Path(name).stem+'.o')],out,'compile-'+Path(name).stem)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        records = list(pool.map(compile_one, units))
    records.append(command([ld,'-melf64lriscv','-L',am/'am/src/nemu/ldscript',
        '-T',am/'am/src/nemu/isa/riscv/boot/loader64.ld','--undefined=q288_full','--gc-sections',
        '-o',out/'gs32-target.elf','--start-group',
        *[objects/(Path(n).stem+'.o') for n in units],am/'am/build/am-riscv64-xs.a',
        am/'libs/klib/build/klib-riscv64-xs.a','--end-group'],out,'link'))
    records.append(command([objcopy,'-S','--set-section-flags','.bss=alloc,contents','-O','binary',
                            out/'gs32-target.elf',out/'gs32-target.bin'],out,'objcopy'))
    for name,pin in LIB_PINS.items():
        NEED(sha((am/name).read_bytes()) == pin, 'AM input unchanged after link '+name)
    result = dict(contract=CONTRACT,status='GS32_TARGET_BUILD_COMPLETE',commands=records,
        elf_sha256=sha((out/'gs32-target.elf').read_bytes()),
        bin_sha256=sha((out/'gs32-target.bin').read_bytes()),compile_workers=jobs,
        tools={str(Path(t).resolve()):sha(Path(t).read_bytes()) for t in (cc,ld,objcopy)},
        immutable_am_inputs={str(am/n):pin for n,pin in LIB_PINS.items()},
        target_runtime_qualified=False,performance_qualified=False)
    save(out/'build.json',result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--am-home',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--jobs',type=int,default=1)
    args = p.parse_args()
    sys.dont_write_bytecode = True
    result = build(args.repo.resolve(),args.am_home.resolve(),args.output.resolve(),args.jobs)
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','immutable_am_inputs')},indent=2))


if __name__ == '__main__':
    main()
