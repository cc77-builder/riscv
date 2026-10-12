"""Run the real RTL test with one deliberately wrong upper-byte expectation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vectors', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    vectors = args.vectors.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    original = vectors.read_bytes()
    lines = original.decode().splitlines()
    require(len(lines) == 12023, 'Use the full reviewed hardware corpus')
    first = lines[1].split('\t')
    require(first[0] == 'D00' and int(first[9],16) == 0, 'Unexpected diagnostic fixture')
    first[9] = f'{1 << 120:032x}'
    lines[1] = '\t'.join(first)
    negative = output/'wrong-expected.tsv'
    require(negative != vectors, 'Do not overwrite the actual model inputs')
    negative.write_bytes(('\n'.join(lines)+'\n').encode())
    command = ['sbt','-batch','-J-XX:ActiveProcessorCount=2','-J-Xmx2g',
               'testOnly VdotExecSpec -- -z "match the independent model"']
    env = dict(os.environ, VDOT_HW_VECTORS=str(negative))
    run = subprocess.run(command, cwd=root/'team/hardware/vdot', env=env,
                         capture_output=True,text=True,timeout=240)
    log = run.stdout+run.stderr
    (output/'test.log').write_bytes(log.encode())
    (output/'commands.json').write_bytes((json.dumps(dict(command=command,vectors=str(negative)),indent=2)+'\n').encode())
    require(run.returncode != 0 and 'Tests: succeeded 0, failed 1' in log, 'Controlled wrong expectation was not detected')
    for field in ('contract=vdot-s8x8-r32-v0.1','id=D00','tag=0','instruction=0x294050b',
                  'vd=10 vs1=8 vs2=9','src1_128=','src2_128=', 'vl=8 vtype=0x0 vstart=0x0 vs=1',
                  'expected128=0x1000000000000000000000000000000', 'actual128=0x0'):
        require(field in log,'Missing actual diagnostic field: '+field)
    require('VDOT_HW_MODEL_PASS' not in log,'Unexpected positive pass marker')
    require(vectors.read_bytes()==original,'Actual model vectors changed')
    result = dict(status='CONTROLLED_HIGH_BYTE_FAILURE_DETECTED',exit_code=run.returncode,
                  original_vectors_unchanged=True,source_modified=False,
                  original_vectors_sha256=hashlib.sha256(original).hexdigest(),
                  negative_vectors_sha256=hashlib.sha256(negative.read_bytes()).hexdigest(),
                  diagnostic_fields_checked=True)
    (output/'summary.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(result,sort_keys=True))
