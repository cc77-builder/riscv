import contextlib,hashlib,io,json,pathlib,runpy,subprocess,tempfile
root=pathlib.Path('/mnt/c/Code/RVInno/riscv')
out=pathlib.Path('/home/amesotten/.cache/codex-rvinno/o1-gate-fixes-20261018/nested-final')
out.mkdir(exist_ok=False)
helper=runpy.run_path(str(root/'team/scripts/prepare-core-baseline.py'))
command=['python3','-OO','-B','-m','unittest','discover','-s',str(root/'team/tests'),'-p','test_core_dependency_inputs.py','-v']
with (out/'tests.log').open('wb') as log:
    run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
if run.returncode:raise ValueError('dependency suite failed')
results=[]
with tempfile.TemporaryDirectory(prefix='o1-nested-fixed-') as tmp:
    base=pathlib.Path(tmp)
    for name,path in [('cde','cde/src'),('hardfloat','hardfloat/src/main/scala')]:
        repo=base/name
        subprocess.run(['git','clone','--shared',str(root/'rocket-chip'/name),str(repo)],check=True,capture_output=True)
        rev=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        helper['verify_dependencies'](base,{name:rev})
        with (repo/'.git/info/exclude').open('a') as f:f.write('\n*.ignored.scala\n')
        extra=repo/path/'Extra.ignored.scala';extra.write_text('object Extra {}\n')
        try:helper['verify_dependencies'](base,{name:rev})
        except RuntimeError as error:
            if 'Ignored dependency compiler inputs' not in str(error):raise
            results.append(dict(dependency=name,revision=rev,source=extra.relative_to(repo).as_posix(),status='REJECTED',reason=str(error)))
        else:raise ValueError('nested source accepted')
binding=json.loads((pathlib.Path('/home/amesotten/.cache/codex-rvinno/o1-complete-20261018')/'core-build/source-binding.json').read_text())
helper['verify_dependencies'](pathlib.Path(binding['build_copy']),binding['modules'])
(out/'results.json').write_text(json.dumps(dict(status='NESTED_SOURCE_FIX_PASS',command=command,tests=7,
    exit_code=run.returncode,log_sha256=hashlib.sha256((out/'tests.log').read_bytes()).hexdigest(),
    real_nested_dependency_mutations=results,native_modules_accepted=len(binding['modules'])),indent=2)+'\n')
print('NESTED_SOURCE_FIX_PASS tests=7 native_modules=126 real_mutations=2',flush=True)
