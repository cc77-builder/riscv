"""An unsuccessful real FU test rerun must invalidate a previous PASS."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def check(success):
    root = Path(__file__).resolve().parents[2]
    previous = json.loads((success / 'check.json').read_bytes())
    if previous.get('status') != 'VDOT_XIANGSHAN_FU_INTERFACE_PASS':
        raise RuntimeError('A successful real-interface run is required first')
    with tempfile.TemporaryDirectory(prefix='vdot-fu-failed-rerun-') as temp:
        evidence = Path(temp) / 'evidence with spaces'
        evidence.mkdir()
        (evidence / 'check.json').write_bytes((success / 'check.json').read_bytes())
        launcher = Path(temp) / 'fault-mill'
        launcher.write_bytes(b'#!/bin/sh\nif [ "$1" = "--version" ]; then\n'
                             b'  echo "Mill Build Tool version 0.12.3"\n  exit 0\nfi\n'
                             b'echo VDOT_FU_EXPECTED_LAUNCH_FAILURE >&2\nexit 17\n')
        launcher.chmod(0o755)
        env = dict(os.environ, TEAM_EVIDENCE_DIR=str(evidence), VDOT_MILL=str(launcher))
        run = subprocess.run(['bash', str(root / 'team/scripts/vdot-fu-tests.sh')],
                             cwd=root, env=env, text=True, capture_output=True, timeout=900)
        if run.returncode != 17 or (evidence / 'check.json').exists():
            raise RuntimeError(f'Failure gate did not invalidate old PASS: {run.returncode} {run.stderr}')
        if 'VDOT_FU_EXPECTED_LAUNCH_FAILURE' not in (evidence / 'emit.log').read_text():
            raise RuntimeError('The actual emit-stage failure was not reached')
    print(json.dumps(dict(status='VDOT_FU_FAILURE_GATE_PASS',exit_code=17,
                          stale_pass_removed=True,original_evidence_preserved=True),sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--success', type=Path, required=True)
    check(parser.parse_args().success.resolve())
