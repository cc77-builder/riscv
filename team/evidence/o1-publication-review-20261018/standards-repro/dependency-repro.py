import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import shutil

root=Path('/mnt/c/Code/RVInno/riscv')
helper=runpy.run_path(str(root/'team/scripts/prepare-core-baseline.py'))
out=Path(tempfile.mkdtemp(prefix='rvinno-dependency-review-',dir='/home/amesotten/.cache/codex-rvinno'))
source=out/'source';source.mkdir()
def git(*args):
    return subprocess.run(['git','-C',str(source),'-c','user.name=Review Fixture',
      '-c','user.email=review-fixture@example.invalid',*args],capture_output=True,text=True,check=True).stdout
git('init')
(source/'src/main/scala').mkdir(parents=True)
(source/'src/main/scala/Review.scala').write_text('object Review {}\n')
git('-c','protocol.file.allow=always','submodule','add',str(root/'yunsuan'),'yunsuan')
git('add','.')
git('commit','-m','isolated provenance fixture')
pack=out/'pack'
captured=io.StringIO()
with contextlib.redirect_stdout(captured):
    helper['pack'](source,pack)
    helper['materialize'](source,pack,out/'cache')
target=Path((pack/'build-copy.txt').read_text().strip())
extra=target/'yunsuan/src/main/scala/ReviewOnlyExtra.scala'
extra.write_text('package yunsuan\nobject ReviewOnlyExtra { val unknownCompilerInput = 1 }\n')
with contextlib.redirect_stdout(captured):
    helper['verify'](source,pack,target)
unknown=subprocess.check_output(['git','-C',str(target/'yunsuan'),'ls-files','--others','--exclude-standard'],text=True)
result={'output':str(out),'untracked_dependency_input':str(extra),
        'untracked_inventory':unknown.splitlines(),'verification':captured.getvalue(),
        'accepted_after_extra_compiler_input':True}
(out/'reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
receipt=root/'team/out/o1-publication-review-20261018/standards-repro'
receipt.mkdir(parents=True,exist_ok=True)
shutil.copyfile(out/'reproduction.json',receipt/'dependency.json')
shutil.copyfile(__file__,receipt/'dependency-repro.py')
print(json.dumps(result,indent=2))
