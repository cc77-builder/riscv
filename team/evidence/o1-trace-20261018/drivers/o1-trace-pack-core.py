import hashlib, json, shutil, tarfile
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv')
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018')
core=cache/'source-0d8e5ae781e51a3c'
out=repo/'team/evidence/o1-trace-20261018'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
completion=json.loads((cache/'core-runs-01/completion.json').read_text())
batch=json.loads((cache/'batch-01/result.json').read_text())
if completion['status']!='O1_CORE_OBSERVATION_MILESTONE_PASS' or batch['status']!='O1_BATCH128_HANDOFF_OBSERVATION_PASS':raise SystemExit('incomplete runs')
paths=[]
for folder in ('core-build','core-runs-01','batch-01'):
    paths.extend(p for p in sorted((cache/folder).rglob('*')) if p.is_file())
paths.extend(cache/n for n in ('core-run-command.json','core-run-driver.log','core-run-driver.status'))
archive=out/'core-validation.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=6) as target:
    for p in paths:target.add(p,arcname=p.relative_to(cache).as_posix(),recursive=False)
(out/'core-payload.json').write_text(json.dumps(dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,files={p.relative_to(cache).as_posix():sha(p) for p in paths}),indent=2)+'\n')
# Freeze actual physical compiler inputs independently from later report edits.
binding=json.loads((core/'build/source-binding.json').read_text())
with tarfile.open(out/'compiler-inputs.tar.gz','w:gz') as target:
    for name, expected in sorted(binding['physical_root_sha256'].items()):
        if sha(core/name)!=expected:raise SystemExit('compiler input drift: '+name)
        target.add(core/name,arcname=name,recursive=False)
    target.add(core/'build/source-binding.json',arcname='build/source-binding.json',recursive=False)
pack=repo/'team/out/o1-trace-20261018-core-pack'
for name in ('source-pack.json','changes.patch'):
    shutil.copyfile(pack/name,out/name)
checked={}
for p in sorted((core/'build/rtl').glob('*.sv')):
    data=p.read_bytes()
    if b'O1_EXU_BEGIN' in data or b'O1_ROB_BEGIN' in data:
        dest=out/'instrumented-rtl'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest);checked[p.name]=sha(p)
for name in ('o1-trace-final-host.py','o1-trace-follow-build.py','o1-trace-batch.py','o1-trace-pack-core.py'):
    shutil.copyfile(repo/'team/out'/name,out/'drivers'/name)
for src,dest in ((cache/'core-runs-01/control/trace.json','control-trace.json'),(cache/'core-runs-01/control/checked.json','control-check.json'),(cache/'batch-01/trace.json','batch-trace.json')):
    shutil.copyfile(src,out/dest)
(out/'completion.json').write_text(json.dumps(dict(status='O1_OBSERVATION_MILESTONE_PASS',core_runs=3,parent_modes=3,
    emu_sha256=completion['emu_sha256'],source_pack_sha256=binding['source_pack_sha256'],root_inputs=len(binding['physical_root_sha256']),
    dependency_revisions=len(binding['modules']),parent_archive_sha256=sha(out/'parent-validation.tar.gz'),core_archive_sha256=sha(archive),
    compiler_inputs_sha256=sha(out/'compiler-inputs.tar.gz'),instrumented_rtl=checked,default_o1_enabled=False,full_T12_T13_acceptance=False),indent=2)+'\n')
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),files=len(paths))))
