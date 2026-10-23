#!/usr/bin/env python3
"""Require the complete sealed S2 archive, byte-for-byte, in the Git index.

This read-only gate catches files silently omitted by repository ignore rules.
It does not stage files, launch EMU, or replace the architecture audit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess

import merged_evidence as e

g = e.g


def git(repo, *args, data=None):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(repo), *args], input=data)


def verify(repo, archive_path):
    repo, archive_path = repo.resolve(), archive_path.resolve()
    g.require(archive_path.is_relative_to(repo), 'archive must be inside the repository')
    e.bind_modules(repo)
    archive = e.portable(repo).Archive(archive_path)
    g.require(archive.manifest.get('contract') == e.m.CONTRACT, 'wrong archive contract')
    relative = archive_path.relative_to(repo).as_posix()
    expected = {relative + '/' + r['stored'] for r in archive.manifest['files']}
    expected.update(relative + '/' + n for n in ('archive-manifest.json', 'archive-manifest.sha256', 'archive-check.json'))
    actual = {p.relative_to(repo).as_posix() for p in archive_path.rglob('*') if p.is_file()}
    g.require(actual == expected, 'archive disk inventory differs from manifest and three metadata files')
    cached = e.m.read_json(archive_path / 'archive-check.json')
    g.require(cached == dict(status='R2_MERGED_ARCHIVE_BYTES_PASS', **archive.bytes_result), 'cached byte check differs')
    staged = {p.decode('utf-8') for p in git(repo, 'ls-files', '-z', '--', relative).split(b'\0') if p}
    missing, extra = sorted(expected - staged), sorted(staged - expected)
    g.require(not missing and not extra,
              'archive index inventory incomplete: missing=%d extra=%d; first=%r' % (len(missing), len(extra), missing[:3]))
    names = sorted(expected)
    requests = ''.join(':' + n + '\n' for n in names).encode('utf-8')
    stream = io.BytesIO(git(repo, 'cat-file', '--batch', data=requests))
    for name in names:
        header = stream.readline().split()
        g.require(len(header) == 3 and header[1] == b'blob', 'missing staged blob: ' + name)
        raw = stream.read(int(header[2]))
        g.require(stream.read(1) == b'\n' and raw == (repo / name).read_bytes(), 'staged archive bytes differ: ' + name)
    g.require(not stream.read(), 'extra Git blob output')
    return dict(status='R2_MERGED_ARCHIVE_COMPLETE_GIT_INDEX_PASS',
                created_utc=datetime.now(timezone.utc).isoformat(),
                source_base=git(repo, 'rev-parse', 'HEAD').decode().strip(),
                checker_sha256=g.sha(Path(__file__)), archive=archive.bytes_result,
                archive_files_in_git_index=len(names), missing=0, extra=0,
                new_emu_runs=0, architecture_replayed=False,
                scope='Complete manifest inventory and exact stored bytes in Git index; architecture audit remains separate')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        g.require(not a.output.exists(), 'output already exists')
        result = verify(a.repo, a.archive)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        g.save(a.output, result)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        p.exit(2, 'R2_MERGED_INDEX_REJECTED: ' + str(exc) + '\n')
