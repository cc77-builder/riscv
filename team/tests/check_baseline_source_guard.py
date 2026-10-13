"""Prove stale compiled-source rejection with a reversible source comment."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--nemu',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args = parser.parse_args()
    def require(condition,message):
        if not condition: raise RuntimeError(message)
    root = Path(__file__).resolve().parents[2]
    source = root/'team/workloads/rvv-baseline/main.c'
    image = args.build/'rvv-baseline.bin'
    original = source.read_bytes()
    image_digest = hashlib.sha256(image.read_bytes()).hexdigest()
    args.evidence.mkdir(parents=True,exist_ok=True)
    env = dict(os.environ, BASELINE_DATA=str(args.data), BASELINE_IMAGE=str(image),
               VDOT_NEMU_BIN=str(args.nemu), TEAM_EVIDENCE_DIR=str(args.evidence))
    source.write_bytes(original+b'\n/* Controlled stale-source test; restored after rejection. */\n')
    try:
        result = subprocess.run(['bash',str(root/'team/scripts/baseline-tests.sh'),'run-nemu'],
                                env=env,capture_output=True,text=True,timeout=60)
        (args.evidence/'rejection.log').write_text(result.stdout+result.stderr)
        (args.evidence/'exit-code.txt').write_text(str(result.returncode)+'\n')
        require(result.returncode != 0,'Stale source accepted')
        require('digest mismatch' in result.stderr and str(source) in result.stderr,result.stderr)
        require(not (args.evidence/'run.log').exists(),'Stale binary was executed')
    finally:
        source.write_bytes(original)
    require(source.read_bytes() == original,'Source restoration failed')
    require(hashlib.sha256(image.read_bytes()).hexdigest() == image_digest,'Image changed')
    output = dict(stale_source_rejected=True,exit_code=result.returncode,
                  original_source_restored=True,image_unchanged=True)
    (args.evidence/'summary.json').write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
    print(json.dumps(output,sort_keys=True))
