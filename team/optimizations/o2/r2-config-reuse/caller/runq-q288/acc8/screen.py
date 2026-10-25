"""Bounded host/GNU screening of eight strict FP32 row accumulators.

Reuses the Q288 fixture, independent oracle, qualified integer leaves and build
engine. This entry point deliberately has no EMU action and makes no cycle claim.
"""
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
import argparse
import importlib.util
import json
import os
import shutil
import struct

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
ROOT=HERE.parents[6]
REL=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/acc8')
CONTRACT='r2-s3-runq-q288-acc8-screen-v1'
BASELINE_ELF_SHA='7f2c3d6de93f979cc252379a8fe2147e0d7ff121b0a38151f4604ee832884f26'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

base=load('acc8_q288_engine',PARENT/'run.py')
check=load('acc8_q288_check',PARENT/'check.py')
gen=base.gen
trace=base.traced
original_sources=base.sources
original_generate=base.generate
need,sha=base.g.require,base.g.sha

def sources(repo):
    found=original_sources(repo)
    found.update({str(REL/n):sha(HERE/n) for n in ('q288.c','screen.py','CONTRACT.md')})
    return found

def generate(repo,out):
    with base.adapt(gen,CONTRACT=CONTRACT):
        manifest=original_generate(repo,out)
    shutil.copyfile(HERE/'q288.c',out/'q288.c')
    manifest.update(screen_only=True,target_runtime_qualified=False,
                    wrapper_variant='eight-explicit-fp32-accumulators',
                    weight_scale_order='each exact row/group once between consecutive leaves')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

def candidate_path(elf,row,fixture,dataset=0):
    return trace.path(elf,row,fixture,dataset,scale_order='group',profile=True)

@contextmanager
def variant():
    with base.adapt(base,CONTRACT=CONTRACT,sources=sources,generate=generate,
                    traced=SimpleNamespace(path=candidate_path)):
        yield

def host(out):
    out.mkdir(parents=True,exist_ok=False)
    actual=check.native(out/'positive',HERE/'q288.c')
    # A row mix-up keeps every FP opcode count unchanged; only a value oracle
    # can reject it. Keep the actual mutant C, compiler output and failure.
    source=(HERE/'q288.c').read_text()
    before='s1 = s1 + a1;'
    need(source.count(before)==1,'unique row mutant site')
    bad=out/'wrong-row.c';bad.write_text(source.replace(before,'s1 = s0 + a1;'))
    try:
        check.native(out/'wrong-row',bad)
    except ValueError as error:
        need(str(error)=='native row-major vs packed wrapper bitwise','specific row mutant rejection')
        rejected=dict(mutated_source_sha256=sha(bad),error=str(error))
    else:
        raise ValueError('row mutant incorrectly accepted')
    result=dict(status='ACC8_HOST_ORACLE_AND_ROW_MUTANT_PASS',contract=CONTRACT,
                positive=actual,row_mutant=rejected,new_emu_runs=0,
                target_runtime_qualified=False,application_performance_qualified=False)
    base.g.save(out/'result.json',result)
    return result

def elf_controls(build,out):
    with variant():
        positive=check.elf_controls(ROOT,build,out/'existing-controls',engine=base)
    blob=(build/'vdot-perf.elf').read_bytes();elf=base.g.ELF(blob)
    body=elf.symbol_data('q288_full');offset=blob.find(body)
    need(offset>=0 and blob.find(body,offset+1)<0,'unique wrapper bytes')
    # The candidate newly keeps eight sums in fs*. Verify that an actual
    # corrupted restore is rejected by the existing full-width ABI sentinel.
    restores=[(i*4,w) for i,(w,) in enumerate(struct.iter_unpack('<I',body))
              if w&127==7 and (w>>12)&7==3 and (w>>15)&31==2
              and (w>>7)&31 in (8,9,18,19,20,21,22,23)]
    need(len(restores)==8,'eight actual LP64D floating restores')
    off,word=restores[0]
    mutant=(word&0x000fffff)|((((word>>20)-8)&4095)<<20)
    changed=bytearray(blob);struct.pack_into('<I',changed,offset+off,mutant)
    row=json.loads((build/'source/manifest.json').read_text())['rows'][0]
    try:
        candidate_path(base.g.ELF(bytes(changed)),row,gen.fixtures())
    except ValueError as error:
        need(str(error)=='FP callee-saved registers balanced','specific FP restore rejection')
        rejection=dict(pc=elf.symbols['q288_full'][0]+off,original_word=hex(word),
                       mutated_word=hex(mutant),error=str(error),
                       mutated_elf_sha256=check.sha(changed))
    else:
        raise ValueError('FP restore mutant incorrectly accepted')
    result=dict(status='ACC8_ACTUAL_ELF_REJECTIONS_PASS',contract=CONTRACT,
                existing=positive,fp_restore=rejection,new_emu_runs=0)
    base.g.save(out/'result.json',result)
    return result

def compare(baseline,build,out):
    need(sha(baseline/'vdot-perf.elf')==BASELINE_ELF_SHA,'pinned original ELF')
    with variant():
        verified=base.verification(ROOT,build)
    old=base.g.ELF((baseline/'vdot-perf.elf').read_bytes())
    new=base.g.ELF((build/'vdot-perf.elf').read_bytes())
    need(old.symbol_data('q288_pack')==new.symbol_data('q288_pack'),'complete pack machine code unchanged')
    fixture=gen.fixtures()
    rows=json.loads((build/'source/manifest.json').read_text())['rows']
    comparisons=[]
    for row in rows:
        if row['kind']!='Q':continue
        need(old.symbol_data(row['leaf'])==new.symbol_data(row['leaf']),
             'complete integer leaf bytes unchanged')
        _,before=trace.path(old,row,fixture,profile=True)
        _,after=candidate_path(new,row,fixture)
        need(before['fp_operations']==after['fp_operations'] and before['calls']==after['calls'],
             'identical arithmetic and call cardinalities')
        comparisons.append(dict(id=row['id'],leaf=row['leaf'],before=before,after=after,
            instruction_reduction=1-after['instructions']/before['instructions']))
    need(len(comparisons)==6,'all qualified controls in static comparison')
    pass_gate=all(100*v['after']['instructions']<=95*v['before']['instructions'] and
                  v['after']['cost_profile']['stack_accesses'].get('fload',0)==8 and
                  v['after']['cost_profile']['stack_accesses'].get('fstore',0)==8
                  for v in comparisons)
    result=dict(status='ACC8_STATIC_SCREEN_PASS' if pass_gate else 'ACC8_STOP_STATIC_SCREEN',
        contract=CONTRACT,baseline_elf_sha256=BASELINE_ELF_SHA,candidate_elf_sha256=sha(build/'vdot-perf.elf'),
        comparisons=comparisons,verification=verified,gate='each full Q path >=5% fewer instructions; only eight FP ABI loads/stores',
        new_emu_runs=0,target_runtime_qualified=False,application_performance_qualified=False,
        decision='candidate for a new bounded target contract; not a deployed default' if pass_gate else 'stop before EMU')
    base.g.save(out,result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action',required=True,choices=('host','build','verify','elf','compare'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--build',type=Path)
    parser.add_argument('--baseline-build',type=Path)
    parser.add_argument('--identity',type=Path)
    args=parser.parse_args();out=args.output.resolve()
    need(not out.exists(),'fresh output required')
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    identity=(args.identity or ROOT/base.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json').resolve()
    cfg=base.parent.parent_identity(ROOT,identity)['configuration']
    inputs=[ROOT,identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    if args.build:inputs.append(args.build.resolve())
    if args.baseline_build:inputs.append(args.baseline_build.resolve())
    base.parent.outside_inputs(out,inputs)
    if args.action=='host':result=host(out)
    elif args.action=='build':
        with variant():result=base.build(ROOT,identity,out)
    elif args.action=='verify':
        need(args.build is not None,'build required')
        with variant():result=base.verification(ROOT,args.build.resolve())
        base.g.save(out,result)
    elif args.action=='elf':
        need(args.build is not None,'build required')
        result=elf_controls(args.build.resolve(),out)
    else:
        need(args.build and args.baseline_build,'both builds required')
        result=compare(args.baseline_build.resolve(),args.build.resolve(),out)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
