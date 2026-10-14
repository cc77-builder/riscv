#!/usr/bin/env python3
"""Verify a real compiled baseline rejects a different optimization profile."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
for name in ('target', 'pack', 'evidence', 'nemu', 'am', 'mill', 'output'):
    parser.add_argument('--' + name, required=True, type=Path)
args = parser.parse_args()
output = args.output.resolve()
require(not output.exists(), 'Use a fresh negative-test directory')
output.mkdir(parents=True)
for name in ('fir-input.sha256', 'rtl.sha256'):
    shutil.copyfile(args.evidence / name, output / name)
target = args.target.resolve()
stamp = target / 'build/emu-compile/core-compile-profile.json'
before = stamp.read_bytes()
binary = target / 'build/emu'
before_binary = digest(binary)
receipt = output / 'check.json'
receipt.write_text('{"status":"STALE_RECEIPT_TEST"}\n', encoding='utf-8')
env = os.environ.copy()
env.update(CORE_SOURCE_PACK=str(args.pack.resolve()), TEAM_EVIDENCE_DIR=str(output),
           CORE_MILL=str(args.mill.resolve()), NEMU_HOME=str(args.nemu.resolve()), AM_HOME=str(args.am.resolve()),
           CORE_CXX='clang++-19', CORE_CC='clang-19', CORE_OPT_FAST='-O2', CORE_COMPILE_JOBS='2')
driver = Path(__file__).resolve().parents[1] / 'scripts/core-baseline-compile.sh'
result = subprocess.run(['bash', str(driver)], cwd=target, env=env, capture_output=True, text=True)
(output / 'rejection.log').write_text(result.stdout + result.stderr, encoding='utf-8')
require(result.returncode != 0 and 'Compiler/profile changed or unbound cached objects' in result.stdout + result.stderr,
        'Different compiler profile was not rejected at the cache gate')
require(stamp.read_bytes() == before and digest(binary) == before_binary, 'Negative test changed the valid build')
require(not receipt.exists(), 'Old receipt survived failed cache validation')
print('CORE_COMPILE_CACHE_PROFILE_REJECTION_PASS requested_opt=-O2 compiled_opt=-O1 binary_unchanged=true receipt_absent=true')
