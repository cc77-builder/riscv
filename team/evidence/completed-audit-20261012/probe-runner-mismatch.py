"""Audit reproduction using a copied old image; only temporary comment is restored."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root=Path('/mnt/c/Code/RVInno/riscv')
audit=root/'team/out/completed-audit-20261012'
build=audit/'copied-build';data=audit/'runner-data';evidence=audit/'runner-mismatch'
build.mkdir(exist_ok=True)
origin=root/'team/out/t05e-build-xs-full'
subprocess.run(['python3',str(root/'team/tests/generate_vdot_cases.py'),'--output',str(data)],check=True,capture_output=True)
inputs=[]
for line in (origin/'inputs.sha256').read_text().splitlines():
    digest,path=line.split('  ',1)
    copied=data/Path(path).name
    if hashlib.sha256(copied.read_bytes()).hexdigest()!=digest:
        raise RuntimeError('Copied input does not match existing image')
    inputs.append(f'{digest}  {copied}\n')
(build/'inputs.sha256').write_text(''.join(inputs))
images=[]
for line in (origin/'workload.sha256').read_text().splitlines():
    digest,path=line.split('  ',1);dest=build/Path(path).name
    shutil.copyfile(path,dest)
    if hashlib.sha256(dest.read_bytes()).hexdigest()!=digest: raise RuntimeError('Copied image digest')
    images.append(f'{digest}  {dest}\n')
(build/'workload.sha256').write_text(''.join(images))
shutil.copyfile(origin/'source.sha256',build/'source.sha256')
source=root/'team/workloads/vdot-exceptions/main.c'
original=source.read_bytes();modified=original+b'\n/* Audit-only post-build source change; restored after run. */\n'
before=hashlib.sha256(original).hexdigest();after=hashlib.sha256(modified).hexdigest()
binary=Path('/home/amesotten/.cache/codex-rvinno/t08/delivered/standalone/build/riscv64-nemu-interpreter')
recorded_checkout=Path('/home/amesotten/.cache/codex-rvinno/t08/delivered/reference')
env=dict(os.environ,VDOT_DATA=str(data),VDOT_IMAGE=str(build/'vdot-exceptions.bin'),
         NEMU_HOME=str(recorded_checkout),VDOT_NEMU_BIN=str(binary),VDOT_RUN_TIMEOUT='120s',TEAM_EVIDENCE_DIR=str(evidence))
source.write_bytes(modified)
try:
    result=subprocess.run(['bash',str(root/'team/scripts/vdot-tests.sh'),'run-nemu','full'],env=env,capture_output=True,text=True,timeout=150)
    (audit/'runner-mismatch-driver.log').write_text(result.stdout+result.stderr)
    if result.returncode!=0: raise RuntimeError(result.stdout+result.stderr)
    if f'{after}  {source}' not in (evidence/'source.sha256').read_text(): raise RuntimeError('Current source was not recorded')
    if (evidence/'nemu.config').read_bytes()!=(recorded_checkout/'.config').read_bytes(): raise RuntimeError('Config did not come from selected checkout')
    log=(evidence/'run.log').read_text()
    if 'planned=115 executed=115 passed=115 failed=0 unreachable=0' not in log: raise RuntimeError('Incomplete real run')
finally:
    if source.read_bytes()!=modified: raise RuntimeError('Unexpected concurrent source edit; not overwriting it')
    source.write_bytes(original)
output=dict(runner_accepted_stale_compiled_source=True,current_main_sha256=after,compiled_original_main_sha256=before,
            runner_accepted_mismatched_checkout_and_binary=True,recorded_checkout=str(recorded_checkout),executed_binary=str(binary),
            real_guest_cases_passed=115,exit_code=result.returncode,source_restored=source.read_bytes()==original,
            original_images_unchanged=True)
(audit/'runner-mismatch-summary.json').write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
print(json.dumps(output,sort_keys=True))
