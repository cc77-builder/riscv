import hashlib, json, shutil, subprocess, tarfile
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv')
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018')
out=repo/'team/evidence/o1-trace-20261018'
out.mkdir(exist_ok=False)
(out/'.gitattributes').write_text('* -text -whitespace\n')
selected=[]
for folder in ('parent-01','parent-02','flag-checks','flag-checks-direct','flag-checks-direct-02','trace-off-equivalence','final-parent-checks'):
    for path in sorted((cache/folder).rglob('*')):
        if not path.is_file():continue
        parts=path.relative_to(cache/folder).parts
        if 'obj' in parts and path.name!='VVDotExuTestTop':continue
        selected.append(path)
selected.append(cache/'real-trace-negatives.json')
archive=out/'parent-validation.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
    for path in selected:tar.add(path,arcname=path.relative_to(cache).as_posix(),recursive=False)
with (out/'host-tests.log').open('wb') as log:
    rc=subprocess.run(['python3','-OO','-B','-m','unittest','discover','-s',str(repo/'team/optimizations/o1'),'-p','test_*.py','-v'],stdout=log,stderr=subprocess.STDOUT).returncode
if rc:raise SystemExit('host tests failed')
for name in ('o1-trace-parent-run.sh','o1-trace-core-build.sh','o1-trace-flag-check.sh','o1-trace-flags.py','o1-trace-off-equivalence.py','o1-trace-recheck.py','o1-trace-pack-parent.py'):
    (out/'drivers').mkdir(exist_ok=True)
    shutil.copyfile(repo/'team/out'/name,out/'drivers'/name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(out/'parent-payload.json').write_text(json.dumps(dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
    files={p.relative_to(cache).as_posix():sha(p) for p in selected}),indent=2)+'\n')
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),files=len(selected))))
