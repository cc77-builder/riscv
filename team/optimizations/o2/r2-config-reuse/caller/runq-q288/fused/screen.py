"""Actual-ELF finite-value screen; no EMU, cycle claim, or default change."""
from pathlib import Path
import argparse
import ast
import copy
import ctypes as C
import hashlib
import importlib.util
import json
import os
import random
import shutil
import struct
import subprocess
import time
import zipfile

import generate
import model

HERE = Path(__file__).resolve().parent
REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused')
PARENT = REL.parent
CONTRACT = 'r2-s3-runq-q288-fused-screen-v1'
FIXTURE_SHA = 'e2862fb802754c473a0c9cb8a949b30ed55eaee647aae9ef7e1d566168122987'
ORACLE_SHA = '6e72ed5b4e6b4ea804d34212e9e84d9001207eea076a26a8a835f2a1c29f9dec'
ACC8_ZIP_SHA = 'b3fc245f9f2f5a63e6ce1e65cf984ca44c5df15910d995f6f65d7e3add247cac'
ACC8_ELF_SHA = '8fcb7bb4fda1ce7dcc2cf4c41f83bfed3733cee363df2cf2a3d760a737103888'
need = model.need


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def command(argv, cwd, index):
    start = time.time()
    proc = subprocess.run([str(v) for v in argv], cwd=cwd, capture_output=True, timeout=60)
    for name, raw in (('stdout',proc.stdout),('stderr',proc.stderr)):
        (cwd/f'{index:02}-{name}.log').write_bytes(raw)
    result = dict(argv=[str(v) for v in argv], cwd=str(cwd), exit_code=proc.returncode,
                  elapsed_seconds=time.time()-start, stdout_sha256=sha(proc.stdout), stderr_sha256=sha(proc.stderr))
    save(cwd/f'{index:02}-command.json',result)
    need(proc.returncode == 0, 'actual compiler/tool execution')
    return result


def fixtures(source):
    """Reuse exactly the frozen fixture functions without importing run engines."""
    raw = Path(source).read_bytes()
    need(sha(raw) == FIXTURE_SHA, 'frozen full-Q fixture generator')
    names = ('f32','from_bits','bits','bytes8','bytes32','fixtures')
    nodes = [n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in names]
    need([n.name for n in nodes] == list(names), 'exact fixture function extraction')
    namespace = {'struct':struct}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
    return namespace['fixtures']()


SHIM = r'''
#include <stdint.h>
#include <fenv.h>
#include <math.h>
typedef union { uint32_t u; float f; } bits;
int host_rne(void) { return fesetround(FE_TONEAREST); }
uint32_t host_mul(uint32_t a, uint32_t b) { bits x={.u=a},y={.u=b},z; z.f=x.f*y.f;return z.u; }
uint32_t host_add(uint32_t a, uint32_t b) { bits x={.u=a},y={.u=b},z; z.f=x.f+y.f;return z.u; }
uint32_t host_convert(int32_t a) { bits z; z.f=(float)a;return z.u; }
uint32_t host_fma_witness(void) {
    volatile uint32_t v[4]={0x3d000000,0x3d000000,0x3d000001,0x3cfffffe};
    bits a={.u=v[0]},b={.u=v[1]},c={.u=v[2]},d={.u=v[3]},z;
    float first=(-1.0f*a.f)*b.f;z.f=fmaf(c.f,d.f,first);return z.u;
}
'''


def oracle_library(oracle, headers, out):
    out.mkdir(parents=True,exist_ok=False)
    need(sha(Path(oracle).read_bytes()) == ORACLE_SHA, 'unchanged independent row-major C oracle')
    shutil.copyfile(oracle,out/'oracle.c')
    for name,path in headers.items(): shutil.copyfile(path,out/name)
    (out/'shim.c').write_text(SHIM)
    compiler=shutil.which('gcc'); need(compiler,'host GNU compiler')
    argv=[compiler,'-std=gnu11','-O2','-fPIC','-shared','-ffp-contract=off','-fno-fast-math',
          '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-lto','-Wall','-Wextra','-Werror',
          'oracle.c','shim.c','-lm','-o','oracle.so']
    record=command(argv,out,0)
    lib=C.CDLL(str(out/'oracle.so'))
    lib.q288_oracle.argtypes=[C.c_void_p]*5;lib.q288_oracle.restype=None
    for name in ('host_add','host_mul'):
        fn=getattr(lib,name);fn.argtypes=[C.c_uint32,C.c_uint32];fn.restype=C.c_uint32
    lib.host_convert.argtypes=[C.c_int32];lib.host_convert.restype=C.c_uint32
    lib.host_fma_witness.restype=C.c_uint32
    need(lib.host_rne()==0,'host round-to-nearest-even')
    need(lib.host_fma_witness()==0xa3800000,'actual contracted operation differs from strict witness')
    save(out/'identity.json',dict(command=record,compiler_sha256=sha(Path(compiler).read_bytes()),
                                  library_sha256=sha((out/'oracle.so').read_bytes()),oracle_sha256=ORACLE_SHA))
    return lib


def fp_primitive_checks(lib):
    # Explicit zeros, ties, normal/subnormal boundary, integer precision and
    # deterministic finite random inputs. Overflow/NaN/Inf remain out of scope.
    values=[0,0x80000000,1,0x80000001,0x7fffff,0x807fffff,0x800000,0x80800000,
            0x3f000000,0x3f800000,0x3f800001,0xbf800000,0x33800000,0x33000000,
            0x3fc00000,0x7f7fffff,0xff7fffff]
    pairs=[(a,b) for a in values for b in values]
    rng=random.Random(28832)
    for _ in range(4096):
        a,b=rng.getrandbits(32),rng.getrandbits(32)
        if ((a>>23)&255)!=255 and ((b>>23)&255)!=255:pairs.append((a,b))
    counts={}; excluded={}
    for label,fn,actual in (('add',model.add,lib.host_add),('multiply',model.multiply,lib.host_mul)):
        counts[label]=excluded[label]=0
        for a,b in pairs:
            expected=actual(a,b)
            if (expected>>23)&255 == 255:
                excluded[label]+=1;continue
            need(fn(a,b)==expected,'exact binary32 '+label+' primitive vs independent native C')
            counts[label]+=1
    integers=[0,1,-1,1<<19,-(1<<19),(1<<24)-1,1<<24,(1<<24)+1,(1<<24)+3,
              -(1<<24)-1,2147483647,-2147483648]+[rng.randrange(-(1<<31),1<<31) for _ in range(4096)]
    for value in integers:need(model.round_binary32(value,0)==lib.host_convert(value),'signed int32 conversion RNE')
    return dict(status='FINITE_FP_PRIMITIVES_PASS',counts=counts,integer_conversions=len(integers),
                nonfinite_results_excluded=excluded,domain='finite binary32 result, RNE; no fflags model')


def python_golden(f,d):
    bits=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
    f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
    unpack=lambda x:struct.unpack('<f',struct.pack('<I',x))[0]
    result=[]
    for r in range(288):
        value=0.0
        for g in range(9):
            dot=sum(f['weight'][r*288+g*32+k]*f['inputs'][d][g*32+k] for k in range(32))
            product=f32(f32(float(dot)*unpack(f['weight_scale'][r*9+g]))*unpack(f['input_scale'][d][g]))
            value=f32(value+product)
        result.append(bits(value))
    return result


def native_golden(lib,f,d):
    raw8=lambda seq:bytes(v&255 for v in seq)
    raw32=lambda seq:struct.pack('<'+'I'*len(seq),*seq)
    inputs=[C.create_string_buffer(raw) for raw in
            (raw8(f['inputs'][d]),raw32(f['input_scale'][d]),raw8(f['weight']),raw32(f['weight_scale']))]
    before=[bytes(v) for v in inputs];output=C.create_string_buffer(1152)
    lib.q288_oracle(C.addressof(output),*(C.addressof(v) for v in inputs))
    need([bytes(v) for v in inputs]==before,'oracle inputs readonly')
    return list(struct.unpack('<288I',output.raw))


def numeric_checks(elf, fixture_source, oracle_source, headers, machine_path, out):
    out.mkdir(parents=True,exist_ok=False)
    lib=oracle_library(oracle_source,headers,out/'oracle')
    primitive=fp_primitive_checks(lib)
    base=fixtures(fixture_source);cases=[]; machines={}; summaries=[]
    for d in (0,1,0,2):cases.append(('x'+str(d),base,d))
    for name,w,x in (('min-min',[-128]*82944,[-128]*288),('max-max',[127]*82944,[127]*288),
                     ('min-max',[-128]*82944,[127]*288),('zero-weight',[0]*82944,base['inputs'][0])):
        f=copy.deepcopy(base);f['weight']=w;f['inputs'][0]=x
        f['packed']=[w[(8*t+r)*288+g*32+k] for t in range(36) for g in range(9) for r in range(8) for k in range(32)]
        cases.append((name,f,0))
    cls=model.machine_class(machine_path)
    for i,(name,f,d) in enumerate(cases):
        golden=native_golden(lib,f,d)
        need(golden==python_golden(f,d),'independent native C and Python full-Q golden')
        if i<4:need(golden==f['golden'][d],'frozen fixture golden identity')
        if i==0:need(golden[0]==0,'strict FMA witness preserved')
        row=dict(case=name,index=i,dataset=d,packed_sha256=sha(bytes(v&255 for v in f['packed'])),
                 golden_bits=golden,methods={})
        for kind in ('vdot','rvv4'):
            align=(0,0) if i<4 else ((i*3)%16,(i*7)%16)
            m=cls(f,d,poison=0x28800+i,alignment=align)
            if i in (1,2,3):
                previous=machines[kind]
                need(m.regions['packed']==previous.regions['packed'],'same packed W for x0/x1/x0/x2')
                m.regions['packed']=previous.regions['packed']
                m.v=[bytearray(v) for v in previous.v]
            m.execute_function(elf,'q288_fused_'+kind)
            row['methods'][kind]=m.check_full(kind,golden)
            row['methods'][kind]['byte_alignment']=align
            machines[kind]=m
        summaries.append(row)
    result=dict(status='FUSED_ACTUAL_ELF_NUMERIC_PASS',elf_sha256=sha(elf.raw),cases=summaries,
                primitives=primitive,fma_witness=dict(strict=0,fused=0xa3800000),new_emu_runs=0,
                target_runtime_qualified=False,performance_qualified=False)
    save(out/'result.json',result)
    return result


def elf_controls(elf,fixture_source,machine_path,out):
    out.mkdir(parents=True,exist_ok=False)
    fixture=fixtures(fixture_source);cls=model.machine_class(machine_path);results=[]
    for kind in ('vdot','rvv4'):
        name='q288_fused_'+kind;addr,_,file_offset=elf.symbols[name]
        words=[w for w, in struct.iter_unpack('<I',elf.symbol_data(name))]
        find=lambda predicate:next(i for i,w in enumerate(words) if predicate(w))
        convert=find(lambda w:w&127==0x57 and w>>26==0x12 and (w>>12)&7==1)
        slide=find(lambda w:w&127==0x57 and w>>26==0x0e and (w>>15)&31==1)
        stride=find(lambda w:w&0x000fffff==0x00000e13 and w>>20==36)
        mul=find(lambda w:w&127==0x57 and w>>26==0x24 and (w>>12)&7==1)
        acc=find(lambda w:w&127==0x57 and w>>26==0 and (w>>12)&7==1)
        csr=find(lambda w:w==0x00f3d073)
        mutants=[('unsigned-conversion',convert,lambda w:w^(1<<15)),
                 ('wrong-gather-row',slide,lambda w:(w&~(31<<20))|(2<<20)),
                 ('wrong-weight-stride',stride,lambda w:(w&0x000fffff)|(32<<20)),
                 ('multiply-replaced-by-add',mul,lambda w:w&~(63<<26)),
                 ('wrong-accumulator-row',acc,lambda w:(w&~(31<<20))|(10<<20)),
                 ('callee-saved-clobber',len(words)-2,lambda w:(w&~(31<<7))|(8<<7)),
                 ('missing-vcsr-reset',csr,lambda w:0x00000013)]
        for label,index,change in mutants:
            before=words[index];after=change(before);need(before!=after,'actual word mutation')
            raw=bytearray(elf.raw);struct.pack_into('<I',raw,file_offset+4*index,after)
            path=out/f'{kind}-{label}.elf';path.write_bytes(raw)
            m=cls(fixture,0,poison=771)
            try:m.execute_function(model.ELF(bytes(raw)),name).check_full(kind,fixture['golden'][0])
            except ValueError as error:
                results.append(dict(method=kind,name=label,pc=hex(addr+4*index),original_word=hex(before),
                    mutated_word=hex(after),mutated_elf_sha256=sha(raw),error=str(error),executed_instructions=len(m.path)))
            else:raise ValueError('actual ELF mutant accepted: '+kind+' '+label)
        # Preserve valid opcodes, FP operation counts and all source reads, but
        # exchange the two scalar-scale multiplications. Rounding must catch it.
        need(words[mul+1]&127==7 and words[mul+2]>>26==0x24 and (words[mul+2]>>12)&7==5,
             'exact three-word scale-order witness')
        raw=bytearray(elf.raw)
        reordered=[words[mul+1],words[mul+2],words[mul]]
        struct.pack_into('<3I',raw,file_offset+4*mul,*reordered)
        (out/f'{kind}-wrong-rounding-order.elf').write_bytes(raw)
        m=cls(fixture,0,poison=771)
        try:m.execute_function(model.ELF(bytes(raw)),name).check_full(kind,fixture['golden'][0])
        except ValueError as error:
            need(str(error)=='actual ELF full-Q bitwise output','specific rounding-order rejection')
            results.append(dict(method=kind,name='wrong-rounding-order',pc=hex(addr+4*mul),
                original_words=[hex(v) for v in words[mul:mul+3]],mutated_words=[hex(v) for v in reordered],
                mutated_elf_sha256=sha(raw),error=str(error),executed_instructions=len(m.path),
                unchanged_fp_element_counts=dict(m.fp_counts)))
        else:raise ValueError('scale-order ELF mutant accepted: '+kind)
    result=dict(status='FUSED_ACTUAL_ELF_REJECTIONS_PASS',controls=results,elf_sha256=sha(elf.raw),new_emu_runs=0)
    save(out/'result.json',result)
    return result


def baseline_comparison(repo,numeric,out):
    archive=repo/PARENT/'acc8/evidence/screen-v1/raw.zip'
    need(sha(archive.read_bytes())==ACC8_ZIP_SHA,'exact frozen acc8 screen archive')
    with zipfile.ZipFile(archive) as z:
        raw=z.read('run/build-01/vdot-perf.elf')
    need(sha(raw)==ACC8_ELF_SHA,'actual qualified acc8 baseline ELF')
    (out/'acc8-baseline.elf').write_bytes(raw)
    trace_source=repo/PARENT/'trace.py'
    need(sha(trace_source.read_bytes())=='ff996761bc0fbd8b3ef1987217d0f0b3877ed04c8f59ae8e346c24a22c9d2299',
         'unchanged complete-Q instruction/address checker')
    spec=importlib.util.spec_from_file_location('fused_screen_baseline_trace',trace_source)
    trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)
    original=model.ELF(raw);fixture=fixtures(repo/PARENT/'generate.py');comparisons=[]
    for kind in ('vdot','rvv4'):
        row=dict(kind='Q',algorithm=0 if kind=='vdot' else 5,method='vdot' if kind=='vdot' else 'rvv',
                 wrapper='q288_full',leaf='split_gemv_8x32_'+kind)
        _,before=trace.path(original,row,fixture,scale_order='group',profile=True)
        after=numeric['cases'][0]['methods'][kind]
        timer=before['cost_profile']['instructions_by_function']['split_measure']
        count=before['instructions']-timer
        need(count>0 and timer==16,'actual baseline function/timer decomposition')
        comparisons.append(dict(method=kind,baseline_function_instructions=count,
            candidate_function_instructions=after['function_instructions'],
            function_instruction_reduction=1-after['function_instructions']/count,
            baseline_marker_instructions=before['instructions'],unchanged_timer_instructions=timer,
            candidate_with_same_timer_projection=after['function_instructions']+timer,
            baseline_profile=before['cost_profile'],candidate_counts=after['counts'],
            candidate_stack_used_bytes=after['stack_used_bytes']))
    passed=all(v['candidate_function_instructions']*100<=v['baseline_function_instructions']*95 and
               v['candidate_stack_used_bytes']==0 for v in comparisons)
    result=dict(status='FUSED_STATIC_SCREEN_PASS' if passed else 'FUSED_STOP_STATIC_SCREEN',
                baseline_elf_sha256=ACC8_ELF_SHA,comparisons=comparisons,
                measured_boundary='actual complete function body; excludes the same timer overhead',
                timer_projection_is_not_executed_candidate_timer=True,
                performance_qualified=False,new_emu_runs=0)
    save(out/'comparison.json',result)
    return result


def full_screen(repo,out):
    repo,out=repo.resolve(),out.resolve()
    need(not out.exists() and not out.is_relative_to(repo),'fresh output outside checkout')
    out.mkdir(parents=True)
    source_paths=[repo/PARENT/'generate.py',repo/PARENT/'oracle.c',repo/PARENT/'q288.h',
                  repo/PARENT/'trace.py',repo/PARENT.parent/'caller.h',repo/PARENT.parent/'split/split.h',
                  repo/'team/optimizations/o2/r2-safe-tail/machine_model.py',repo/generate.PUBLIC,
                  repo/PARENT/'acc8/evidence/screen-v1/raw.zip']+[HERE/n for n in ('generate.py','model.py','screen.py','CONTRACT.md')]
    pins={str(p):sha(p.read_bytes()) for p in source_paths}
    commands=[]
    source=generate.generate(repo,out/'source')
    gcc=shutil.which('riscv64-linux-gnu-gcc');need(gcc,'GNU RISC-V toolchain')
    prefix=[gcc,'-march=rv64gv','-mabi=lp64d','-mno-relax']
    commands.append(command(prefix+['-c',out/'source/fused.S','-o',out/'fused.o'],out,0))
    commands.append(command(prefix+['-static','-no-pie','-nostdlib','-nostartfiles',
        '-Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,q288_fused_vdot',out/'fused.o','-o',out/'fused.elf'],out,1))
    # Independently compile the unchanged public source to certify the retained
    # integer core machine words; never rewrite it or a frozen reference object.
    commands.append(command(prefix+['-c',repo/generate.PUBLIC,'-o',out/'public-reference.o'],out,2))
    elf=model.ELF((out/'fused.elf').read_bytes());reference=model.ELF((out/'public-reference.o').read_bytes())
    refs={name:reference.symbol_data(name).hex() for name in
          ('config_reuse_gemv_8x32_reuse_vdot','config_reuse_gemv_8x32_reuse_rvv')}
    certificates={kind:model.core_certificate(elf,refs,kind) for kind in ('vdot','rvv4')}
    save(out/'integer-core-certificate.json',certificates)
    header_paths={'q288.h':repo/PARENT/'q288.h','caller.h':repo/PARENT.parent/'caller.h',
                  'split.h':repo/PARENT.parent/'split/split.h'}
    integer_model=repo/'team/optimizations/o2/r2-safe-tail/machine_model.py'
    numeric=numeric_checks(elf,repo/PARENT/'generate.py',repo/PARENT/'oracle.c',header_paths,integer_model,out/'numeric')
    controls=elf_controls(elf,repo/PARENT/'generate.py',integer_model,out/'elf-controls')
    comparison=baseline_comparison(repo,numeric,out)
    need(all(sha(Path(p).read_bytes())==v for p,v in pins.items()),'all screen inputs unchanged')
    for source_path in source_paths:
        target=out/'source-snapshot'/source_path.relative_to(repo)
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source_path,target)
    result=dict(status=comparison['status'],contract=CONTRACT,source_files=pins,
                compiler_sha256=sha(Path(gcc).read_bytes()),commands=commands,source_generation=source,
                elf_sha256=sha(elf.raw),certificates=certificates,numeric_status=numeric['status'],
                controls_status=controls['status'],control_count=len(controls['controls']),
                comparisons=comparison['comparisons'],new_emu_runs=0,target_runtime_qualified=False,
                performance_qualified=False)
    save(out/'result.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=HERE.parents[6]);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    print(json.dumps(full_screen(a.repo,a.output),indent=2))
