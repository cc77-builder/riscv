"""Bounded-memory transport of the existing SHA256-object ZIP evidence format."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('prior_evidence_transport', HERE.parents[1] / 'archive.py')
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
need, safe = old.need, old.safe
BLOCK = 1024 * 1024


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(BLOCK), b''): digest.update(block)
    return digest.hexdigest()


def copy_checked(source, destination, expected_size, expected_sha):
    digest = hashlib.sha256(); total = 0
    for block in iter(lambda: source.read(BLOCK), b''):
        total += len(block); need(total <= expected_size, 'stream does not exceed declared complete object size')
        digest.update(block)
        if destination is not None: destination.write(block)
    need(total == expected_size and digest.hexdigest() == expected_sha, 'every complete streamed object has exact bytes')


def manifest_check(manifest, members):
    need(manifest['format'] == 'sha256-object-zip-v1', 'unchanged transport format')
    files = manifest['files']; seen = set(); objects = {}
    need(isinstance(files, list), 'explicit manifest file list')
    for row in files:
        safe(row['path']); folded = row['path'].casefold()
        need(folded not in seen, 'unique portable restored file path'); seen.add(folded)
        key, size = row['sha256'], row['size']
        need(re.fullmatch('[0-9a-f]{64}', key) is not None and type(size) is int and size >= 0, 'exact object digest and size')
        need(key not in objects or objects[key] == size, 'same object has same full length'); objects[key] = size
    for path in seen:
        need(all('/'.join(path.split('/')[:i]) not in seen for i in range(1, len(path.split('/')))), 'no file is also a directory')
    need(len(members) == len(set(members)) and set(members) == {'manifest.json'} | {'objects/' + key for key in objects},
         'unique and exact ZIP membership')
    need(manifest['file_count'] == len(files) and manifest['original_bytes'] == sum(row['size'] for row in files) and
         manifest['unique_objects'] == len(objects) and manifest['unique_bytes'] == sum(objects.values()), 'exact manifest aggregates')
    return files, objects


def seal(inputs, output):
    output = Path(output).resolve(); need(not output.exists(), 'fresh streaming archive output')
    entries = []; objects = {}; labels = set(); roots = []
    for value in inputs:
        label, location = value.split('=', 1); safe(label)
        need('/' not in label and label.casefold() not in labels, 'one unique portable root label')
        labels.add(label.casefold()); root = Path(location).resolve(); need(root.is_dir(), 'actual evidence root')
        need(not output.is_relative_to(root), 'archive output outside all evidence inputs'); roots.append(root)
        for path in sorted(root.rglob('*')):
            need(not path.is_symlink(), 'ordinary evidence files, no symlinks')
            if not path.is_file(): continue
            size = path.stat().st_size; key = sha(path)
            need(path.stat().st_size == size, 'source length stable while scanning')
            name = label + '/' + path.relative_to(root).as_posix(); safe(name)
            entries.append(dict(path=name, size=size, sha256=key)); objects.setdefault(key, (path, size))
            need(objects[key][1] == size, 'same source object size')
    manifest = dict(format='sha256-object-zip-v1', archiver_sha256=sha(__file__),
        parent_path_checker_sha256=sha(Path(old.__file__)), files=entries, file_count=len(entries),
        original_bytes=sum(row['size'] for row in entries), unique_objects=len(objects), unique_bytes=sum(value[1] for value in objects.values()),
        storage_policy='1MiB streaming; SHA256 object deduplication; DEFLATE level 3; no hardlinks')
    manifest_check(manifest, ['manifest.json', *('objects/' + key for key in objects)])
    output.mkdir(parents=True); encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    with zipfile.ZipFile(output / 'payload.zip', 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as archive:
        info = zipfile.ZipInfo('manifest.json', date_time=(1980, 1, 1, 0, 0, 0))
        archive.writestr(info, encoded, compress_type=zipfile.ZIP_DEFLATED, compresslevel=3)
        for key, (path, size) in sorted(objects.items()):
            with path.open('rb') as source, archive.open('objects/' + key, 'w', force_zip64=True) as destination:
                copy_checked(source, destination, size, key)
    (output / 'manifest.json').write_bytes(encoded)
    report = verify(output / 'payload.zip')
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def verify(archive, output=None, expected=None):
    archive = Path(archive); digest = sha(archive)
    if expected is not None: need(digest == expected, 'published archive SHA256')
    if output is not None:
        output = Path(output).resolve(); need(not output.exists(), 'fresh restore root')
    with zipfile.ZipFile(archive) as zipped:
        info = zipped.getinfo('manifest.json')
        need(info.file_size <= 64 * 1024 * 1024, 'bounded complete manifest')
        manifest = json.loads(zipped.read(info)); files, objects = manifest_check(manifest, zipped.namelist())
        for key, size in objects.items():
            info = zipped.getinfo('objects/' + key); need(info.file_size == size, 'declared ZIP object length')
            with zipped.open(info) as source: copy_checked(source, None, size, key)
        if output is not None:
            output.mkdir(parents=True); restored = {}
            for row in files:
                key, size = row['sha256'], row['size']; path = output / row['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                if key in restored:
                    with restored[key].open('rb') as source, path.open('xb') as destination:
                        copy_checked(source, destination, size, key)
                else:
                    with zipped.open('objects/' + key) as source, path.open('xb') as destination:
                        copy_checked(source, destination, size, key)
                    restored[key] = path
            for row in files:
                path = output / row['path']
                need(path.is_file() and not path.is_symlink() and path.stat().st_size == row['size'] and sha(path) == row['sha256'],
                     'every final ordinary restored file matches original bytes')
    return dict(status='ARCHIVE_BYTES_PASS', archive_sha256=digest, archive_bytes=archive.stat().st_size,
        file_count=len(files), original_bytes=manifest['original_bytes'], unique_objects=len(objects),
        restored=output is not None, streaming=True, block_bytes=BLOCK, performance_qualified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('seal'); p.add_argument('--input', action='append', required=True); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('verify'); p.add_argument('--archive', type=Path, required=True); p.add_argument('--output', type=Path)
    p.add_argument('--expected-sha256')
    args = parser.parse_args()
    result = seal(args.input, args.output) if args.action == 'seal' else verify(args.archive, args.output, args.expected_sha256)
    print(json.dumps(result, indent=2))
