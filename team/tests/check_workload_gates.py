"""Exercise actual drivers: stale source, wrong checkout and changed config."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def require(condition,message):
    if not condition: raise RuntimeError(message)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',choices=('vdot','baseline'),required=True)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--nemu-home',type=Path,required=True)
    p.add_argument('--wrong-home',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[2]
    source=root/'team/workloads'/('vdot-exceptions' if a.kind=='vdot' else 'rvv-baseline')/'main.c'
    image=a.build/('vdot-exceptions.bin' if a.kind=='vdot' else 'rvv-baseline.bin')
    binary=a.nemu_home/'build/riscv64-nemu-interpreter'
    original=source.read_bytes()
    config=a.nemu_home/'.config';original_config=config.read_bytes()
    image_digest=hashlib.sha256(image.read_bytes()).hexdigest()
    a.evidence.mkdir(parents=True,exist_ok=True)
    results=[]
    for kind in ('stale-source','wrong-checkout','changed-config'):
        evidence=a.evidence/kind
        env=dict(os.environ,NEMU_HOME=str(a.wrong_home if kind=='wrong-checkout' else a.nemu_home),
                 VDOT_NEMU_BIN=str(binary),TEAM_EVIDENCE_DIR=str(evidence))
        if a.kind=='vdot': env.update(VDOT_DATA=str(a.data),VDOT_IMAGE=str(image))
        else: env.update(BASELINE_DATA=str(a.data),BASELINE_IMAGE=str(image))
        mutated=original+b'\n/* Controlled stale-source negative; restore below. */\n'
        changed_config=original_config+b'\n# Controlled config-drift negative\n'
        if kind=='stale-source': source.write_bytes(mutated)
        if kind=='changed-config': config.write_bytes(changed_config)
        try:
            script='vdot-tests.sh' if a.kind=='vdot' else 'baseline-tests.sh'
            run=subprocess.run(['bash',str(root/'team/scripts'/script),'run-nemu'],env=env,
                               capture_output=True,text=True,timeout=120)
            (a.evidence/f'{kind}.log').write_text(run.stdout+run.stderr)
            require(run.returncode!=0 and not (evidence/'run.log').exists(),f'{kind}: guest executed or test accepted')
            wanted={'stale-source':'digest mismatch','wrong-checkout':'executable and source checkout mismatch',
                    'changed-config':'config changed after build'}[kind]
            require(wanted in run.stderr,run.stderr)
            results.append(dict(kind=kind,rejected=True,guest_executed=False,exit_code=run.returncode))
        finally:
            if kind=='stale-source':
                require(source.read_bytes()==mutated,'Concurrent source change: not overwriting it')
                source.write_bytes(original)
            if kind=='changed-config':
                require(config.read_bytes()==changed_config,'Concurrent config change: not overwriting it')
                config.write_bytes(original_config)
    require(source.read_bytes()==original and config.read_bytes()==original_config,'Restoration failed')
    require(hashlib.sha256(image.read_bytes()).hexdigest()==image_digest,'Image changed')
    result=dict(kind=a.kind,tests=results,source_config_restored=True,image_unchanged=True)
    (a.evidence/'summary.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
