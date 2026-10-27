"""Build the optional fixed-A C library and link all qualified entry points.

The four archive members are extracted and checked. A final executable resolves
relocations before every wrapper/leaf is compared to the qualified benchmark ELF.
This standalone library must not be mixed with other libraries defining the same
packed/config_reuse/r4/firstdot/split symbols. It does not change an R5 default.
"""
import argparse
import json
from pathlib import Path
import shutil
import run as e

helper=e.g.load('fixed_parent_library',e.PARENT_DIR/'library.py')
CFLAGS=helper.CFLAGS
MEMBERS=('fixed.o','gemv.o','strong.o','kernels.o')
EXAMPLE='''#include "fixed_entries.h"

/* Caller enables VS. count must be exactly 1 or 4; A[256], X[count*32],
 * Y[count*8] are valid/disjoint. The entry is an explicit caller decision.
 * This example uses local scratch and retains every full intermediate slot.
 */
void fixed_stream_example(const int8_t *a,const int8_t *x,int32_t *y,
                          size_t count,split_leaf entry) {
    _Alignas(16) struct caller_slot slots[FIXED_MAX_COUNT*8];
    int8_t packed[288];
    struct fixed_context context={.a=a,.x=x,.y=y,.slots=slots,.packed=packed,
        .packed_entry=config_reuse_gemv_8x32_reuse_vdot,
        .split_entry=entry,.count=count};
    fixed_split(&context);
}
'''

def build(qualified,out):
    valid=e.verification(e.ROOT,qualified);br=e.read(qualified/'build.json')
    e.g.require(br['accepted'] is True,'accepted build required')
    e.parent.outside_inputs(out,[e.ROOT,qualified]);out.mkdir(parents=True,exist_ok=False)
    source_names=('fixed.h','split.h','caller.h','fixed.c','gemv.S','strong.S','kernels.S')
    for n in source_names:shutil.copyfile(qualified/'source'/n,out/n)
    header='#ifndef XS_FIXED_WEIGHT_ENTRIES_H\n#define XS_FIXED_WEIGHT_ENTRIES_H\n#include "fixed.h"\n'
    header+='/* Packed leaves consume 256B A followed by 32B x, and write 8 full slots. */\n'
    header+='\n'.join('void '+row[0]+'(const int8_t *,void *);' for row in e.gen.LEAVES)+'\n#endif\n'
    (out/'fixed_entries.h').write_text(header);(out/'example.c').write_text(EXAMPLE)
    consumer='''#include "fixed_entries.h"
static int8_t a[256],x[128],packed[288];
static int32_t y[32];
static _Alignas(16) struct caller_slot slots[32];
static struct fixed_context context={a,x,y,slots,packed,0,0,4};
'''
    consumer+='static caller_leaf const old_entries[6]={'+','.join(r[0] for r in e.gen.LEAVES)+'};\n'
    consumer+='static split_leaf const new_entries[6]={'+','.join(e.gen.NEW)+'};\n'
    consumer+='''void fixed_link_entry(void) {
    for(unsigned i=0;i<6;++i) {
        context.packed_entry=old_entries[i];context.split_entry=new_entries[i];
        fixed_packed(&context);fixed_split(&context);
    }
}
'''
    (out/'link-all.c').write_text(consumer)
    tools={k:v['path'] for k,v in br['toolchain'].items()}
    for k in ('gcc','ar','ld','readelf'):e.g.require(e.g.sha(tools[k])==br['toolchain'][k]['sha256'],'qualified tool drift: '+k)
    nm=shutil.which(tools['gcc'][:-3]+'nm');e.g.require(nm is not None,'GNU nm')
    identity=e.ROOT/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    f,_=e.parent.runtime(e.ROOT,e.parent.parent_identity(e.ROOT,identity))
    commands=[('compile-fixed',[tools['gcc'],*CFLAGS,'-c','fixed.c','-o','fixed.o'])]
    commands += [('compile-'+name,[tools['gcc'],'-march=rv64gv','-mabi=lp64d','-mno-relax','-c',name+'.S','-o',name+'.o'])
                 for name in ('gemv','strong','kernels')]
    commands += [('archive',[tools['ar'],'rcsD','libxs_fixed_weight_8x32.a',*MEMBERS]),
                 ('members',[tools['ar'],'t','libxs_fixed_weight_8x32.a'])]
    commands += [('extract-'+n,[tools['ar'],'p','libxs_fixed_weight_8x32.a',n]) for n in MEMBERS]
    commands += [('compile-example',[tools['gcc'],*CFLAGS,'-c','example.c','-o','example.o']),
                 ('compile-all',[tools['gcc'],*CFLAGS,'-c','link-all.c','-o','link-all.o']),
                 ('link-all',[tools['ld'],'--no-relax','-m','elf64lriscv','-Ttext=0x80000000',
                    '-e','fixed_link_entry','-o','consumer.elf','link-all.o','example.o',
                    '--whole-archive','libxs_fixed_weight_8x32.a','--no-whole-archive']),
                 ('unresolved',[nm,'-u','consumer.elf']),('elf-header',[tools['readelf'],'-h','consumer.elf'])]
    names=source_names+('fixed_entries.h','example.c','link-all.c')
    source={n:e.g.sha(out/n) for n in names}
    state=dict(status='BUILDING',contract=e.CONTRACT,started=e.now(),qualified_image_sha256=valid['image_sha256'],
        qualified_build_sha256=e.g.sha(qualified/'build.json'),sources=source,commands=[],new_emu_runs=0,
        tool_sources={Path(__file__).resolve().relative_to(e.ROOT).as_posix():e.g.sha(__file__),
                      (e.PARENT_DIR/'library.py').relative_to(e.ROOT).as_posix():e.g.sha(e.PARENT_DIR/'library.py')})
    e.g.save(out/'library.json',state)
    try:
        for label,argv in commands:state['commands'].append(f.command(argv,out,out/'commands'/label))
        e.g.require((out/'commands/members/stdout.log').read_text().splitlines()==list(MEMBERS),'exact archive inventory')
        objects={}
        for n in MEMBERS:
            raw=(out/'commands'/('extract-'+n)/'stdout.log').read_bytes()
            e.g.require(raw==(out/n).read_bytes(),'actual archive member: '+n)
            objects[n]=e.g.ELF(raw)
        e.g.require(not (out/'commands/unresolved/stdout.log').read_bytes(),'consumer unresolved symbol')
        final=e.g.ELF((out/'consumer.elf').read_bytes());actual=e.g.ELF((qualified/'vdot-perf.elf').read_bytes())
        e.g.require(final.kind==2 and final.entry==final.symbols['fixed_link_entry'][0] and
            not any(p[0] in (2,3) for p in final.segments) and
            any(p[0]==1 and p[1]&1 and p[3]<=final.entry<p[3]+p[5] for p in final.segments),
            'statically relocated consumer executable')
        e.g.require(not any(s[1] in (4,9) and s[5] for s in final.sections),'unresolved relocation section')
        functions={}
        wanted={'fixed_packed','fixed_split',*e.old.PUBLIC_LEAVES,*(r[0] for r in e.gen.LEAVES),*e.gen.NEW}
        prefixes=('fixed_','config_reuse_gemv_','r4_gemv_','firstdot_gemv_','split_gemv_')
        public={n for obj in objects.values() for n in obj.symbols if n.startswith(prefixes)}
        e.g.require(public==wanted,'library public function inventory')
        for name in sorted(wanted):
            owners=[n for n,obj in objects.items() if name in obj.symbols]
            e.g.require(len(owners)==1,'unique archive function: '+name)
            member=objects[owners[0]].symbol_data(name);linked=final.symbol_data(name);reference=actual.symbol_data(name)
            e.g.require(member==linked==reference,'member/final/qualified machine bytes: '+name)
            functions[name]=dict(member=owners[0],bytes=len(linked),sha256=e.digest(linked))
        for n,h in source.items():e.g.require(e.g.sha(out/n)==h,'library source drift')
        state.update(status='FIXED_WEIGHT_GNU_LIBRARY_AND_FINAL_LINK_PASS',functions=functions,
            artifacts={n:e.g.sha(out/n) for n in (*MEMBERS,'libxs_fixed_weight_8x32.a','example.o','link-all.o','consumer.elf')},
            toolchain={k:dict(path=tools[k],sha256=e.g.sha(tools[k])) for k in ('gcc','ar','ld','readelf')},
            nm=dict(path=nm,sha256=e.g.sha(nm)),scope='all archive members and final executable checked; not an additional ISA run',
            link_rule='standalone library; no other archive/object may define these public symbols')
    except BaseException as exc:
        state.update(status='FAILED',error=repr(exc));raise
    finally:state['finished']=e.now();e.g.save(out/'library.json',state)
    return state

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--qualified-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();e.g.require(not out.exists(),'fresh library output')
    result=build(a.qualified_build.resolve(),out)
    print(json.dumps({k:result[k] for k in ('status','qualified_image_sha256','functions','new_emu_runs')},indent=2))
