#!/usr/bin/env python3
"""Require the complete sealed S2 archive, byte-for-byte, in the Git index.

This read-only gate catches files silently omitted by repository ignore rules.
It does not stage files, launch EMU, or replace the architecture audit.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess

import merged_evidence as e

g = e.g


def git(repo, *args, data=None):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(repo), *args], input=data)


def index_entries(raw):
    """Parse NUL-delimited staged entries, accepting ordinary resolved files only."""
    g.require(not raw or raw.endswith(b'\0'), 'unterminated Git index inventory')
    entries = {}
    for record in raw.split(b'\0')[:-1]:
        header, separator, path = record.partition(b'\t')
        fields = header.split()
        g.require(separator and len(fields) == 3 and path, 'malformed Git index entry')
        mode, oid, stage = fields
        name = path.decode('utf-8')
        g.require(stage == b'0', 'unmerged Git index entry: ' + name)
        g.require(mode in (b'100644', b'100755'), 'non-regular Git index mode: ' + name)
        g.require(len(oid) in (40, 64) and all(c in b'0123456789abcdef' for c in oid),
                  'invalid Git index object identity: ' + name)
        g.require(name not in entries, 'duplicate Git index path: ' + name)
        entries[name] = dict(mode=mode.decode('ascii'), oid=oid.decode('ascii'))
    return entries


def check_output_path(archive_path, output):
    """Do not invalidate a sealed archive by writing the receipt inside it."""
    archive_path, resolved_output = archive_path.resolve(), output.resolve()
    g.require(not resolved_output.is_relative_to(archive_path), 'output must be outside the archive')
    g.require(not output.exists() and not output.is_symlink(), 'output already exists')


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
    entries = index_entries(git(repo, 'ls-files', '--stage', '-z', '--', relative))
    staged = set(entries)
    missing, extra = sorted(expected - staged), sorted(staged - expected)
    g.require(not missing and not extra,
              'archive index inventory incomplete: missing=%d extra=%d; first=%r' % (len(missing), len(extra), missing[:3]))
    names = sorted(expected)
    requests = ''.join(entries[n]['oid'] + '\n' for n in names).encode('ascii')
    stream = io.BytesIO(git(repo, 'cat-file', '--batch', data=requests))
    for name in names:
        header = stream.readline().split()
        g.require(len(header) == 3 and header[0].decode('ascii') == entries[name]['oid']
                  and header[1] == b'blob', 'missing staged blob: ' + name)
        raw = stream.read(int(header[2]))
        g.require(stream.read(1) == b'\n' and raw == (repo / name).read_bytes(), 'staged archive bytes differ: ' + name)
    g.require(not stream.read(), 'extra Git blob output')
    return dict(status='R2_MERGED_ARCHIVE_COMPLETE_GIT_INDEX_PASS',
                created_utc=datetime.now(timezone.utc).isoformat(),
                source_base=git(repo, 'rev-parse', 'HEAD').decode().strip(),
                checker_sha256=g.sha(Path(__file__)), archive=archive.bytes_result,
                archive_files_in_git_index=len(names), missing=0, extra=0,
                git_file_modes=dict(sorted(Counter(v['mode'] for v in entries.values()).items())),
                new_emu_runs=0, architecture_replayed=False,
                scope='Complete manifest inventory, ordinary stage-0 file modes and exact stored bytes in Git index; architecture audit remains separate')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        check_output_path(a.archive, a.output)
        result = verify(a.repo, a.archive)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        g.save(a.output, result)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        p.exit(2, 'R2_MERGED_INDEX_REJECTED: ' + str(exc) + '\n')
