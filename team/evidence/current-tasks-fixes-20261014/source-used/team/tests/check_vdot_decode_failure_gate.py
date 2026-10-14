"""Run the delivery entry with a failing compiler driver; stale PASS must vanish."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def check(repo, evidence):
    evidence.mkdir(parents=True, exist_ok=True)
    driver = evidence / 'failing-mill'
    driver.write_bytes(b'#!/bin/sh\nif [ "$1" = "--version" ]; then\n'
                       b'  echo "Mill Build Tool version 0.12.3"\n  exit 0\nfi\nexit 17\n')
    driver.chmod(0o700)
    receipt = evidence / 'check.json'
    receipt.write_bytes(b'{"status":"STALE_PASS"}\n')
    env = dict(os.environ, TEAM_EVIDENCE_DIR=str(evidence), VDOT_MILL=str(driver))
    result = subprocess.run(['bash', str(repo / 'team/scripts/vdot-decode-tests.sh')],
                            cwd=repo, env=env, capture_output=True)
    (evidence / 'rejection.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode != 0 and not receipt.exists(), 'Compiler failure retained or manufactured PASS'
    assert (evidence / 'test.status').read_text().strip() == 'exit_code=17', 'Wrong failure stage'
    assert not (evidence / 'rtl/VdotDecodeHarness.sv').exists(), 'Failed run reached RTL/lint acceptance'
    print(json.dumps(dict(status='VDOT_DECODE_FAILURE_GATE_PASS',compiler_exit=17,old_pass_removed=True),sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    check(args.repo.resolve(), args.evidence.resolve())
