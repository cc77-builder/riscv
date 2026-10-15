#!/usr/bin/env python3
"""Test coordination assumptions in disposable LOCAL Git repositories only.

No network, user repository, credentials, hooks, or GitHub settings are used.
This is a protocol experiment, NOT a deployed branch-locking service.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not __debug__:
        raise RuntimeError('Run without -O: assertions are part of the experiment')
    git = shutil.which('git')
    if git is None:
        raise RuntimeError('git executable is required')
    checks: list[dict] = []
    with tempfile.TemporaryDirectory(prefix='vdot-handoff-probe-') as temporary:
        root = Path(temporary)
        env = dict(os.environ)
        # Ignore unrelated parent-process Git configuration and discovery state.
        for key in list(env):
            if key.startswith('GIT_'):
                env.pop(key)
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_TERMINAL_PROMPT='0', GIT_AUTHOR_DATE='2000-01-01T00:00:00Z',
                   GIT_COMMITTER_DATE='2000-01-01T00:00:00Z')

        def run(where: Path, *argv: str, check: bool = True) -> subprocess.CompletedProcess:
            result = subprocess.run([git, '-c', 'protocol.file.allow=always',
                                     '-c', 'core.hooksPath=' + str(root/'no-hooks'),
                                     '-C', str(where), *argv], env=env,
                                    capture_output=True, text=True, timeout=20)
            if check and result.returncode:
                raise RuntimeError('Git experiment failed: ' + ' '.join(argv) + '\n' + result.stderr)
            return result

        def record(name: str, condition: bool, **facts: object) -> None:
            if not condition:
                raise AssertionError(name)
            checks.append(dict(name=name, passed=True, **facts))

        def config(where: Path, who: str) -> None:
            run(where, 'config', 'user.name', 'Probe ' + who)
            run(where, 'config', 'user.email', who.lower() + '@example.invalid')
            run(where, 'config', 'commit.gpgsign', 'false')

        def save(where: Path, value: dict, message: str) -> str:
            (where/'handoff.json').write_text(json.dumps(value, sort_keys=True) + '\n', encoding='utf-8')
            run(where, 'add', 'handoff.json')
            run(where, 'commit', '-m', message)
            return run(where, 'rev-parse', 'HEAD').stdout.strip()

        def clone(name: str, remote: Path) -> Path:
            where = root/name
            run(root, 'clone', str(remote), str(where))
            config(where, name)
            return where

        def can_claim(state: dict) -> bool:
            # No automatic expiry. This is an ADVISORY protocol check, not ACL.
            return state.get('state') == 'released' and state.get('holder') is None

        seed = root/'seed'; seed.mkdir()
        run(seed, 'init', '-b', 'shared'); config(seed, 'seed')
        (seed/'README.md').write_text('Synthetic protocol fixture.\n', encoding='utf-8')
        run(seed, 'add', 'README.md')
        initial = save(seed, dict(state='released', holder=None), 'initial released state')
        remote = root/'canonical.git'
        run(root, 'init', '--bare', str(remote))
        run(remote, 'symbolic-ref', 'HEAD', 'refs/heads/shared')
        run(seed, 'push', str(remote), 'HEAD:refs/heads/shared')
        a = clone('alpha', remote); b = clone('beta', remote)
        intents = {}
        for who, where in [('alpha', a), ('beta', b)]:
            intents[who] = save(where, dict(state='held', holder=who,
                                           base_sha=initial, planned_end='2000-01-01T01:00:00Z'),
                                'claim by ' + who)
        barrier = threading.Barrier(2)
        def race(where: Path) -> subprocess.CompletedProcess:
            barrier.wait(timeout=10)
            return run(where, 'push', 'origin', 'HEAD:refs/heads/shared', check=False)
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(race, a); future_b = executor.submit(race, b)
            results = {'alpha': future_a.result(), 'beta': future_b.result()}
        winners = [who for who, result in results.items() if result.returncode == 0]
        record('one_canonical_ref_accepts_only_one_concurrent_stale_base_claim', len(winners) == 1,
               push_returncodes={who: result.returncode for who, result in results.items()})
        winner = winners[0]; loser = 'beta' if winner == 'alpha' else 'alpha'
        holder = json.loads(run(remote, 'show', 'shared:handoff.json').stdout)
        record('remote_state_identifies_actual_winner', holder['holder'] == winner)
        record('fresh_read_of_held_state_refuses_second_claim', not can_claim(holder))
        record('expired_planned_end_is_not_permission_to_steal', not can_claim(holder),
               synthetic_planned_end=holder['planned_end'])

        outsider = clone('outsider', remote)
        (outsider/'uncoordinated.txt').write_text('Not authorized by the advisory handoff protocol.\n', encoding='utf-8')
        run(outsider, 'add', 'uncoordinated.txt'); run(outsider, 'commit', '-m', 'negative control: bypass advisory ownership')
        direct = run(outsider, 'push', 'origin', 'HEAD:refs/heads/shared', check=False)
        record('negative_control_ff_push_is_not_a_person_or_module_lock', direct.returncode == 0,
               interpretation='Git accepted a non-holder descendant; protocol/permission enforcement is separate')
        newest = run(remote, 'rev-parse', 'shared').stdout.strip()
        record('review_sha_does_not_follow_a_moving_branch', newest != intents[winner])

        losing_clone = a if loser == 'alpha' else b
        (losing_clone/'untracked-work.txt').write_text('Preserve this work; do not reset --hard.\n', encoding='utf-8')
        dirty = run(losing_clone, 'status', '--porcelain', '--untracked-files=all').stdout
        record('preflight_detects_untracked_work', bool(dirty.strip()))
        record('losing_unpublished_commit_is_preserved',
               run(losing_clone, 'cat-file', '-t', intents[loser]).stdout.strip() == 'commit')

        winning_clone = a if winner == 'alpha' else b
        run(winning_clone, 'fetch', 'origin')
        run(winning_clone, 'merge', '--ff-only', 'origin/shared')
        released = save(winning_clone, dict(state='released', holder=None, previous_holder=winner,
                                           handed_off_code_sha=newest, evidence='synthetic fixture only'), 'explicit release')
        run(winning_clone, 'push', 'origin', 'HEAD:refs/heads/shared')
        nxt = clone('next-shift', remote)
        released_state = json.loads((nxt/'handoff.json').read_text(encoding='utf-8'))
        record('explicit_release_enables_next_shift', can_claim(released_state))
        next_sha = save(nxt, dict(state='held', holder='next-shift', base_sha=released), 'next shift claims reviewed handoff')
        run(nxt, 'push', 'origin', 'HEAD:refs/heads/shared')
        record('handoff_preserves_previous_code_history',
               run(nxt, 'merge-base', '--is-ancestor', intents[winner], next_sha, check=False).returncode == 0)
        review_dir = root/'immutable-review'
        run(nxt, 'worktree', 'add', '--detach', str(review_dir), released)
        record('independent_review_worktree_is_bound_to_exact_sha',
               run(review_dir, 'rev-parse', 'HEAD').stdout.strip() == released and
               run(review_dir, 'symbolic-ref', '-q', 'HEAD', check=False).returncode != 0)

        fork_success = []
        for idx in (1, 2):
            fork = root/('fork' + str(idx) + '.git')
            run(root, 'init', '--bare', str(fork))
            run(fork, 'symbolic-ref', 'HEAD', 'refs/heads/shared')
            run(seed, 'push', str(fork), initial + ':refs/heads/shared')
            work = clone('fork-worker' + str(idx), fork)
            save(work, dict(state='held', holder='worker' + str(idx), base_sha=initial), 'independent fork claim')
            fork_success.append(run(work, 'push', 'origin', 'HEAD:refs/heads/shared', check=False).returncode == 0)
        record('negative_control_two_forks_do_not_share_a_mutex', all(fork_success),
               interpretation='Both independent forks accepted a claim from the same initial state')
        version = run(root, '--version').stdout.strip()
    output = dict(schema=1, scope='disposable local Git only; no GitHub or team settings changed',
                  ran_at_utc=datetime.now(timezone.utc).isoformat(), git_version=version,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  checks=checks, passed=True, check_count=len(checks),
                  limitations=['cooperative protocol is not an access-control boundary',
                               'not a production lock implementation', 'not a test on the actual team repository'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, check_count=len(checks), git_version=version)))


if __name__ == '__main__':
    main()
