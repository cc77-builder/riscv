#!/usr/bin/env python3
"""Inspect and restore unchanged historical evidence using Python's standard library."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_path(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or str(p) != name:
        raise ValueError('Unsafe relative path: ' + name)
    return p


class History:
    def __init__(self, here=HERE, root=ROOT):
        self.here = Path(here).resolve()
        self.root = Path(root).resolve()
        self.manifest = json.loads((self.here / 'manifest.json').read_text(encoding='utf-8'))
        self.entries = {e['path']: e for e in self.manifest['files']}
        if len(self.entries) != len(self.manifest['files']):
            raise ValueError('Duplicate inventory paths')
        self.archives = {a['path']: a for a in self.manifest['archives']}
        self.checked = set()
        self.opened = {}
        for name in self.entries:
            safe_path(name)
        for name in self.archives:
            safe_path(name)

    def check_archive(self, name):
        if name in self.checked:
            return
        item = self.archives[name]
        path = self.here / safe_path(name)
        if not path.is_file() or path.stat().st_size != item['size'] or file_sha(path) != item['sha256']:
            raise ValueError('Archive checksum mismatch: ' + name)
        self.checked.add(name)

    def read(self, name):
        e = self.entries[name]
        if e['storage'] == 'archive':
            self.check_archive(e['archive'])
            if e['archive'] not in self.opened:
                self.opened[e['archive']] = zipfile.ZipFile(self.here / e['archive'])
            data = self.opened[e['archive']].read(name)
        else:
            data = (self.root / safe_path(e.get('original_copy', name))).read_bytes()
        if len(data) != e['size'] or sha(data) != e['sha256']:
            raise ValueError('File checksum mismatch: ' + name)
        return data

    def verify(self, prefix=''):
        count = 0
        for name, e in self.entries.items():
            if e['storage'] == 'archive' and name.startswith(prefix):
                self.read(name)
                count += 1
        return count

    def restore(self, destination, prefix=''):
        destination = Path(destination).absolute()
        if destination.is_symlink():
            raise ValueError('Destination must not be a symlink')
        destination = destination.resolve()
        selected = [e for e in self.entries.values() if e['storage'] == 'archive' and e['path'].startswith(prefix)]
        # Preflight the complete request before creating any file.
        for e in selected:
            path = destination / safe_path(e['path'])
            if not path.resolve().is_relative_to(destination):
                raise ValueError('Destination escapes through a symlink: ' + e['path'])
            cur = path
            while cur != destination:
                if cur.is_symlink():
                    raise ValueError('Symlink in destination: ' + str(cur))
                cur = cur.parent
            if path.exists() and (not path.is_file() or file_sha(path) != e['sha256']):
                raise ValueError('Refusing to overwrite a different existing file: ' + str(path))
            self.check_archive(e['archive'])
        written = skipped = 0
        for e in selected:
            path = destination / e['path']
            if path.exists():
                skipped += 1
                continue
            data = self.read(e['path'])
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as f:
                f.write(data)
            os.chmod(path, int(e['mode'], 8) & 0o777)
            written += 1
        return {'written': written, 'already_identical': skipped}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('list', help='List original log paths, storage and hashes')
    p.add_argument('--contains', default='')
    p = sub.add_parser('show', help='Show an original text log, transparently decoding gzip')
    p.add_argument('path')
    p.add_argument('--head', type=int, default=80)
    p = sub.add_parser('verify', help='Verify all archived files against their original SHA-256')
    p.add_argument('--prefix', default='')
    p = sub.add_parser('restore', help='Restore original paths; never overwrite different files')
    p.add_argument('--to', required=True, type=Path)
    p.add_argument('--prefix', default='')
    args = parser.parse_args()
    history = History()
    if args.command == 'list':
        for name, e in history.entries.items():
            if (e['run_log'] or e.get('category') == 'text_log') and args.contains in name:
                print(name, e['storage'], e.get('archive', ''), e['sha256'], sep='\t')
    elif args.command == 'show':
        data = history.read(args.path)
        if args.path.endswith('.gz'):
            data = gzip.decompress(data)
        lines = data.decode('utf-8', errors='replace').splitlines()
        print('\n'.join(lines[:args.head] if args.head > 0 else lines))
    elif args.command == 'verify':
        print(json.dumps({'status': 'LOG_VERIFY_PASS', 'files': history.verify(args.prefix)}))
    else:
        print(json.dumps({'status': 'LOG_RESTORE_PASS', **history.restore(args.to, args.prefix)}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(1)
