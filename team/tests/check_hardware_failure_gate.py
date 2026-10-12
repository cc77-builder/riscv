"""Actual failed rerun must invalidate a preceding successful RTL conclusion."""
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
    parser.add_argument('--previous-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run_dir = args.previous_run.resolve()
    output = args.output.resolve()
    root = Path(__file__).resolve().parents[2]
    require(output != run_dir, 'Keep probe results separate from the run being invalidated')
    check = run_dir/'check.json'
    previous = check.read_bytes()
    require(json.loads(previous)['status'] == 'VDOT_STANDALONE_RTL_PASS', 'Start from a genuine successful run')
    output.mkdir(parents=True, exist_ok=True)
    (output/'previous-check.json').write_bytes(previous)
    launcher = output/'deliberately-missing-launcher.jar'
    require(not launcher.exists(), 'Failure launcher unexpectedly exists')
    env = dict(os.environ, TEAM_EVIDENCE_DIR=str(run_dir), VDOT_SBT_LAUNCH_JAR=str(launcher))
    run = subprocess.run(['bash', str(root/'team/scripts/vdot-hardware-tests.sh')],
                         cwd=root, env=env, capture_output=True, text=True, timeout=120)
    (output/'run.log').write_bytes((run.stdout+run.stderr).encode())
    (output/'emit.log').write_bytes((run_dir/'emit.log').read_bytes())
    require(run.returncode != 0, 'Broken launcher unexpectedly passed')
    require(not check.exists(), 'Old PASS survived a failed rerun')
    require('Unable to access jarfile' in (run_dir/'emit.log').read_text(), 'Unexpected failure cause')
    result = dict(status='FAILED_RERUN_INVALIDATION_PASS', exit_code=run.returncode,
                  previous_check_sha256=hashlib.sha256(previous).hexdigest(),
                  old_pass_removed=True, source_modified=False,
                  python_optimize=os.environ.get('PYTHONOPTIMIZE','0'))
    (output/'summary.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(result,sort_keys=True))
