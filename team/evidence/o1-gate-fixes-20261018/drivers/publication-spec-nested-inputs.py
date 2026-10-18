from pathlib import Path
import tempfile,runpy,subprocess,json
root=Path('/mnt/c/Code/RVInno/riscv')
helper=runpy.run_path(str(root/'team/scripts/prepare-core-baseline.py'))
results=[]
with tempfile.TemporaryDirectory(prefix='o1-spec-dependency-') as tmp:
    base=Path(tmp)
    for name,source_rel,extra_rel in [('cde','rocket-chip/cde','cde/src/Extra.ignored.scala'),('hardfloat','rocket-chip/hardfloat','hardfloat/src/main/scala/Extra.ignored.scala')]:
        dep=base/name
        subprocess.run(['git','clone','--shared',str(root/source_rel),str(dep)],check=True,capture_output=True)
        revision=subprocess.check_output(['git','-C',str(dep),'rev-parse','HEAD'],text=True).strip()
        with (dep/'.git/info/exclude').open('a') as f:f.write('\n*.ignored.scala\n')
        extra=dep/extra_rel;extra.parent.mkdir(exist_ok=True,parents=True);extra.write_text('object ExtraUnboundCompilerInput {}\n')
        ignored=subprocess.check_output(['git','-C',str(dep),'ls-files','--others','--ignored','--exclude-standard'],text=True).strip()
        helper['verify_dependencies'](base,{name:revision})
        results.append(dict(dependency=source_rel,ignored_source=ignored,verifier_result='PASS',root_compile_binding='build.sc millSourcePath '+source_rel+'/'+name))
print(json.dumps(results,indent=2))
(root/'team/out/publication-spec-nested-inputs.json').write_text(json.dumps(results,indent=2)+'\n')
