"""Export one deduplicated ordinary-C Q288 assembly object source."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,tempfile

REL=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased')
PINS={'phased':'410137991477f8f77ec5ca918e4067697f20a10daf3f48ea3e1fc1eb6c165618',
      'tail':'8369f553aaf642cb2de84ca40506e04f67b5458c6c3992f4d540dc5af7c1c9b5'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)

def export(repo,out,variant):
    need(variant in PINS and not out.exists() and not out.is_relative_to(repo),'fresh export outside repository')
    path=repo/REL/('tail/target/generate.py' if variant=='tail' else 'target/generate.py')
    need(sha(path.read_bytes())==PINS[variant],'fixed reviewed target generator')
    spec=importlib.util.spec_from_file_location('q288_export_generator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='q288-c-export-') as temp:
        generated=Path(temp)/'generated';module.generate(repo,generated);raw=(generated/'fused.S').read_bytes()
    text=raw.decode();symbols=['q288_fused_vdot','q288_fused_rvv4','q288_phased_vdot']
    if variant=='tail':symbols.append('q288_tail_vdot')
    need(all(text.count('.global '+name+'\n')==text.count(name+':\n')==1 for name in symbols),
         'exactly one definition of every ordinary-C entry and RVV fallback')
    need(text.count('.global ')==len(symbols),'no unexpected global assembly symbol')
    out.mkdir(parents=True);(out/'q288-kernels.S').write_bytes(raw)
    result=dict(status='Q288_DEDUPLICATED_SOURCE_EXPORTED',variant=variant,generator=path.relative_to(repo).as_posix(),
        generator_sha256=PINS[variant],assembly_sha256=sha(raw),symbols=symbols,
        new_emu_runs=0,performance_qualified_by_export=False,stable_default_changed=False,
        note='Link this assembly once with q288.c; do not also link static-screen phased.o/tail.o or old fused.o')
    (out/'export.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--variant',choices=tuple(PINS),required=True);a=p.parse_args()
    print(json.dumps(export(a.repo.resolve(),a.output.resolve(),a.variant),indent=2))
