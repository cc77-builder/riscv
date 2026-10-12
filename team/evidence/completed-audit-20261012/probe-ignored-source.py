"""Reversible ignored-source probe; no builds or binary modifications."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

target=Path('/home/amesotten/.cache/codex-rvinno/t08/delivered/standalone')
root=Path('/mnt/c/Code/RVInno/riscv')
manifest=json.loads((root/'team/patches/nemu/manifest.json').read_text())
prefix=target/'src/utils/build'
created=not prefix.exists()
prefix.mkdir(exist_ok=True)
file=prefix/f'team-audit-{uuid.uuid4().hex}.c'
file.write_text('void team_audit_ignored_source(void) {}\n')
try:
    relative=str(file.relative_to(target))
    ignored=subprocess.run(['git','-C',str(target),'check-ignore','-v',relative],capture_output=True,text=True)
    untracked=subprocess.check_output(['git','-C',str(target),'ls-files','--others','--exclude-standard','-z']).decode().split('\0')
    changed=subprocess.check_output(['git','-C',str(target),'diff','HEAD','--name-only']).decode().splitlines()
    source_hashes_ok=all(hashlib.sha256((target/p).read_bytes()).hexdigest()==d for p,d in manifest['patched_source_sha256'].items())
    accepted=source_hashes_ok and set(changed)<=set(manifest['patched_source_sha256']) and set(filter(None,untracked))<=set(manifest['patched_source_sha256'])
    found=relative in subprocess.check_output(['find','src/utils','-name','*.c'],cwd=target,text=True).splitlines()
    result=dict(ignored=ignored.returncode==0,git_ignore_rule=ignored.stdout.strip(),
                current_source_guard_accepts=accepted,actual_source_collection_includes=found,
                no_build_executed=True,patch_sources_unchanged=source_hashes_ok)
    if not all(result[k] for k in ('ignored','current_source_guard_accepts','actual_source_collection_includes','patch_sources_unchanged')):
        raise RuntimeError(result)
finally:
    file.unlink()
    if created: prefix.rmdir()
result['injected_file_removed']=not file.exists()
path=root/'team/out/completed-audit-20261012/ignored-source.json'
path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
