#!/usr/bin/env python3
"""Replay S2 v1 evidence in its explicit, immutable Linux source context.

The development checkout keeps its newer checks. Host tests compile fixtures;
no EMU is run, and no old pins are changed to accommodate new sources.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

REVISION = 'bca14d45b07ff07a86a7f54bce2b25870e60e2f3'
MANIFEST_SHA = '1d42aa417c2793b997fbf1db89f05c1d2a5dcb49644ff14aa29395621bd129ed'
REL = Path('team/optimizations/o2/r2-safe-tail')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_paths(repo, archive, output):
    require(sys.platform == 'linux', 'use a native Linux or WSL Python for the frozen LF generators')
    require(not output.exists() and not output.is_symlink(), 'output must be a new directory')
    for source in (repo, archive):
        require(not output.resolve().is_relative_to(source.resolve()), 'output must be outside source inputs')
    raw = (archive / 'archive-manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA, 'not the fixed S2 v1 archive')


def run(repo, archive, output, tool_bin):
    repo, archive = repo.resolve(), archive.resolve()
    validate_paths(repo, archive, output)
    tool_bin = tool_bin.resolve()
    require(not output.resolve().is_relative_to(tool_bin), 'output must be outside tool inputs')
    env = {'PATH': str(tool_bin) + ':/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC'}
    tools = {}
    for name in ('clang', 'ld.lld', 'llvm-objcopy'):
        executable = shutil.which(name, path=env['PATH'])
        require(executable is not None, 'missing host-test tool: ' + name)
        tools[executable] = hashlib.sha256(Path(executable).read_bytes()).hexdigest()
    output = output.resolve()
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', REVISION + '^{commit}'], text=True).strip()
    require(revision == REVISION, 'frozen source commit unavailable')
    output.mkdir(parents=True)
    state = dict(status='RUNNING', frozen_revision=REVISION, archive=str(archive),
                 manifest_sha256=MANIFEST_SHA, new_emu_runs=0,
                 source_checkout=str(repo), started=datetime.now(timezone.utc).isoformat(),
                 historical_environment_fully_bound=False, current_source_fullcore_acceptance=False,
                 host_tools_sha256=tools, environment=env, steps=[])
    def save():
        (output / 'state.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    def command(name, argv, cwd=None):
        step = dict(name=name, argv=list(map(str, argv)), cwd=str(cwd) if cwd else None,
                    started=datetime.now(timezone.utc).isoformat(), exit_code=None)
        state['steps'].append(step)
        save()
        with (output / (name + '.log')).open('xb') as log:
            result = subprocess.run(step['argv'], cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                    env=env)
        step.update(exit_code=result.returncode, finished=datetime.now(timezone.utc).isoformat())
        save()
        require(result.returncode == 0, 'failed step: ' + name + '; original log preserved')
    save()
    try:
        context = output / 'frozen-source'
        command('clone', ['git', 'clone', '--shared', '--no-checkout', '-c', 'core.autocrlf=false', repo, context])
        # Tests and auditors need team sources; evidence is supplied separately.
        # Sparse checkout avoids duplicating multi-gigabyte historical archives.
        command('sparse', ['git', '-C', context, 'sparse-checkout', 'set', '--no-cone',
                           '/team/', '!/team/**/evidence/', '!/team/evidence/'])
        command('checkout', ['git', '-C', context, 'checkout', '--detach', REVISION])
        command('fixture-source', ['git', '-C', context, 'restore', '--source', REVISION,
                                   '--worktree', '--ignore-skip-worktree-bits', '--',
                                   'team/evidence/t10-t11-fullcore-20261013/matrix/negative-fixture.c'])
        for i, executable in enumerate(tools):
            command('tool-version-' + str(i), [executable, '--version'])
        command('host-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', REL,
                               '-p', 'test_*.py'], context)
        command('architecture-audit', [sys.executable, '-B', context / REL / 'merged_evidence.py',
                                      '--repo', context, '--action', 'audit', '--archive', archive,
                                      '--output', output / 'architecture-audit.json'], context)
        result = json.loads((output / 'architecture-audit.json').read_text())
        require(result['status'] == 'R2_MERGED_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS', 'unexpected audit result')
        require(all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p, sha in tools.items()),
                'host-test tool changed during replay')
        state.update(status='FROZEN_S2_REPLAY_PASS', formal_windows=result['formal_windows'],
                     normal_runs=result['normal_runs'], expected_negative_runs=result['expected_negative_runs'])
    except BaseException as exc:
        state.update(status='FAILED', error=repr(exc))
        raise
    finally:
        state['finished'] = datetime.now(timezone.utc).isoformat()
        save()
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tool-bin', type=Path, default=Path('/usr/bin'),
                        help='explicit directory containing clang, ld.lld and llvm-objcopy')
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.repo, args.archive, args.output, args.tool_bin)))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, 'FROZEN_S2_REPLAY_REJECTED: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
