"""Build a GNU static library and compare every function to a verified build ELF.

The deliverable includes both required headers, ordinary C wrapper and generated
assembly. It never changes the stable library or chooses a kernel for callers.
"""
import argparse
import json
from pathlib import Path
import shutil
import run as e

EXAMPLE='''#include "split.h"

/* The caller enables VS on the qualified RV64/lp64d, VLEN128 platform first.
 * A and x are independent, valid, disjoint int8 buffers; y has 8 int32 values.
 * The selected entry below illustrates the ABI, not a new default decision.
 */
void split_example(const int8_t *a, const int8_t *x, int32_t *y) {
    _Alignas(16) struct caller_slot slots[8];
    struct split_context context = {
        .a=a, .x=x, .y=y, .slots=slots, .entry=split_gemv_8x32_vdot
    };
    split_full(&context);
}
'''

CFLAGS=['-std=gnu11','-O2','-ffreestanding','-fno-tree-vectorize','-fno-tree-slp-vectorize',
        '-fno-tree-loop-distribute-patterns','-fno-ipa-cp','-fno-ipa-icf','-fno-optimize-sibling-calls',
        '-fno-lto','-mno-relax','-mabi=lp64d','-fno-pic','-march=rv64gv','-mcmodel=medany',
        '-static','-Wall','-Werror','-fno-asynchronous-unwind-tables','-fno-builtin','-fno-stack-protector']


def build(qualified,out):
    valid=e.verification(e.ROOT,qualified)
    br=e.read(qualified/'build.json')
    e.g.require(br['accepted'] is True,'accepted linked build required')
    e.parent.outside_inputs(out,[e.ROOT,qualified])
    out.mkdir(parents=True,exist_ok=False)
    for n in ('split.h','caller.h','split.c','kernels.S'):
        shutil.copyfile(qualified/'source'/n,out/n)
    (out/'example.c').write_text(EXAMPLE)
    # Use the exact known toolchain and existing team process receipt utility.
    tools={k:v['path'] for k,v in br['toolchain'].items()}
    for k in ('gcc','ar','ld','readelf'):
        e.g.require(e.g.sha(tools[k])==br['toolchain'][k]['sha256'],'qualified tool changed: '+k)
    nm=shutil.which(tools['gcc'][:-3]+'nm')
    e.g.require(nm is not None,'GNU nm required')
    identity=e.ROOT/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    ident=e.parent.parent_identity(e.ROOT,identity)
    f,_=e.parent.runtime(e.ROOT,ident)
    commands=[
        ('compile-wrapper',[tools['gcc'],*CFLAGS,'-c','split.c','-o','split.o']),
        ('compile-kernels',[tools['gcc'],'-march=rv64gv','-mabi=lp64d','-mno-relax','-c','kernels.S','-o','kernels.o']),
        ('archive',[tools['ar'],'rcsD','libxs_split_8x32.a','split.o','kernels.o']),
        ('members',[tools['ar'],'t','libxs_split_8x32.a']),
        ('extract-wrapper',[tools['ar'],'p','libxs_split_8x32.a','split.o']),
        ('extract-kernels',[tools['ar'],'p','libxs_split_8x32.a','kernels.o']),
        ('compile-example',[tools['gcc'],*CFLAGS,'-c','example.c','-o','example.o']),
        ('link-example',[tools['ld'],'-r','-o','example-linked.o','example.o','libxs_split_8x32.a']),
        ('unresolved',[nm,'-u','example-linked.o']),
    ]
    source={n:e.g.sha(out/n) for n in ('split.h','caller.h','split.c','kernels.S','example.c')}
    state=dict(status='BUILDING',contract=e.CONTRACT,started=e.now(),qualified_image_sha256=valid['image_sha256'],
               qualified_build_sha256=e.g.sha(qualified/'build.json'),sources=source,commands=[],new_emu_runs=0)
    e.g.save(out/'library.json',state)
    try:
        for label,argv in commands:state['commands'].append(f.command(argv,out,out/'commands'/label))
        e.g.require((out/'commands/members/stdout.log').read_text().splitlines()==['split.o','kernels.o'],'archive members')
        for role,name in (('wrapper','split.o'),('kernels','kernels.o')):
            e.g.require((out/'commands'/('extract-'+role)/'stdout.log').read_bytes()==(out/name).read_bytes(),'actual archive member bytes')
        e.g.require(not (out/'commands/unresolved/stdout.log').read_bytes(),'example unresolved symbol')
        actual=e.g.ELF((qualified/'vdot-perf.elf').read_bytes())
        objects={n:e.g.ELF((out/n).read_bytes()) for n in ('split.o','kernels.o')}
        functions={}
        for name in ('split_full',*e.gen.NEW):
            raw=objects['split.o' if name=='split_full' else 'kernels.o'].symbol_data(name)
            e.g.require(raw==actual.symbol_data(name),'library differs from selected ELF function: '+name)
            functions[name]=dict(bytes=len(raw),sha256=e.digest(raw))
        e.g.require({n for obj in objects.values() for n in obj.symbols if n.startswith('split_')}==set(functions),
                    'library split public symbol inventory')
        for n,h in source.items():e.g.require(e.g.sha(out/n)==h,'library source drift')
        state.update(status='SPLIT_GNU_LIBRARY_AND_CONSUMER_LINK_PASS',functions=functions,
            artifacts={n:e.g.sha(out/n) for n in ('split.o','kernels.o','libxs_split_8x32.a','example.o','example-linked.o')},
            toolchain={k:dict(path=tools[k],sha256=e.g.sha(tools[k])) for k in ('gcc','ar','ld')},
            nm=dict(path=nm,sha256=e.g.sha(nm)),example_scope='GNU C11 compile and relocatable link; not a new runtime experiment')
    except BaseException as exc:
        state.update(status='FAILED',error=repr(exc));raise
    finally:
        state['finished']=e.now();e.g.save(out/'library.json',state)
    return state


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--qualified-build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    e.g.require(not out.exists(),'fresh library output required')
    result=build(a.qualified_build.resolve(),out)
    print(json.dumps({k:result[k] for k in ('status','qualified_image_sha256','functions','new_emu_runs')},indent=2))
