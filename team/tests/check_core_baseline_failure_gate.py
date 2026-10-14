#!/usr/bin/env python3
"""Prove that a failed real build invalidates a pre-existing T04 receipt."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


parser = argparse.ArgumentParser(description=__doc__)
for name in ('source', 'pack', 'target', 'evidence', 'nemu', 'output'):
    parser.add_argument('--' + name, required=True, type=Path)
parser.add_argument('--ignored-root', action='store_true', help='Also probe ignored root resource inputs after the real build/run')
args = parser.parse_args()
output = args.output.resolve()
require(not output.exists(), 'Use a fresh negative-test directory')
output.mkdir(parents=True)
for name in ('source-binding.json', 'dependency-sources.json'):
    shutil.copyfile(args.evidence / name, output / name)
failed_status = (args.evidence / 'build-attempt-1.status').read_text().strip()
require(failed_status == 'exit_code=2', 'Expected the preserved Mill-launch failure')
shutil.copyfile(args.evidence / 'build-attempt-1.status', output / 'build.status')
shutil.copyfile(args.evidence / 'build-attempt-1.log', output / 'build.log')
receipt = output / 'check.json'
receipt.write_text(json.dumps(dict(status='STALE_RECEIPT_TEST')), encoding='utf-8')
checker = Path(__file__).resolve().parents[1] / 'scripts/check-core-baseline.py'
command = [sys.executable, str(checker)]
for name in ('source', 'pack', 'target', 'nemu'):
    command += ['--' + name, str(getattr(args, name).resolve())]
command += ['--evidence', str(output)]
result = subprocess.run(command, capture_output=True, text=True)
(output / 'rejection.log').write_text(result.stdout + result.stderr, encoding='utf-8')
require(result.returncode != 0, 'Failed build was accepted')
require('build did not exit successfully' in result.stderr, 'Unexpected rejection reason')
require(not receipt.exists(), 'Old receipt survived the failed recheck')
print('CORE_BASELINE_STALE_RECEIPT_REJECTION_PASS failed_build_exit=2 receipt_absent=true')
if args.ignored_root:
    target = args.target.resolve()
    binding = json.loads((target / 'build/source-binding.json').read_bytes())
    require(binding['build_copy'] == str(target), 'Target is not the recorded native build copy')
    parent = target / 'src/main/resources/.worksheet'
    require(not parent.exists(), 'Probe directory already exists')
    parent.mkdir()
    probe = parent / 't04-unknown.h'
    try:
        probe.write_text('/* T04 controlled ignored resource probe; never compiled. */\n', encoding='utf-8')
        ignored = subprocess.run(['git', '-C', str(target), 'check-ignore', '-q', str(probe)])
        require(ignored.returncode == 0, 'Probe is not ignored by Git')
        receipt.write_text(json.dumps(dict(status='STALE_RECEIPT_TEST')), encoding='utf-8')
        result = subprocess.run(command, capture_output=True, text=True)
        (output / 'ignored-root-rejection.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        require(result.returncode != 0 and 'Unknown root compiler input (including ignored paths)' in result.stderr,
                'Ignored root resource was not rejected for its source input')
        require(not receipt.exists(), 'Old receipt survived the ignored-source recheck')
    finally:
        probe.unlink(missing_ok=True)
        parent.rmdir()
    print('CORE_BASELINE_IGNORED_ROOT_REJECTION_PASS restored=true receipt_absent=true')
