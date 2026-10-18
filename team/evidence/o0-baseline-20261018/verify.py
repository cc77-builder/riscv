"""Extract the sealed baseline evidence and independently recheck all 54 runs.

No EMU or RISC-V compiler is needed. Use this evidence's Git version of the
checker; source drift is rejected against the actual campaign's snapshots.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'team/optimizations/o0'))
import summarize_matrix
import matrix_check as check

ARTIFACTS_SHA = '8e3f1f3c39c7530e8b96787c3bdb470b62de45edf9a3d3a6159039a24328fbdb'
BUILD_ARCHIVE_SHA = '9a15c18502ac745aec60a6c29ddcfe7e6bced58d6026156c2034294add5398de'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(bundle, target):
    with tarfile.open(bundle) as archive:
        members = archive.getmembers()
        names = set()
        total = 0
        for member in members:
            name = member.name
            parts = PurePosixPath(name).parts
            check.require(parts and not name.startswith('/') and '\\' not in name and ':' not in name
                          and '..' not in parts, 'unsafe tar path')
            check.require(member.isfile() or member.isdir(), 'links/special members are not accepted')
            canonical = '/'.join(parts).casefold()
            check.require(canonical not in names, 'duplicate tar path')
            names.add(canonical)
            total += member.size
        check.require(total <= 1024*1024*1024, 'archive exceeds 1 GiB limit')
        target.mkdir(parents=True, exist_ok=False)
        for member in members:
            dest = check.sealed.contained(target, member.name)
            if member.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, dest.open('xb') as sink:
                    shutil.copyfileobj(source, sink)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    check.require(not output.exists(), 'output already exists')
    check.require(not output.is_relative_to((ROOT/'team/evidence').resolve()), 'use a fresh work directory')
    check.require(sha(HERE/'artifacts.json') == ARTIFACTS_SHA, 'sealed artifact manifest changed')
    artifacts = check.sealed.strict_json((HERE/'artifacts.json').read_bytes())
    for name, record in artifacts.items():
        path = check.sealed.contained(HERE, name)
        check.require(path.stat().st_size == record['bytes'] and sha(path) == record['sha256'], 'artifact changed: '+name)
    builds = HERE.parent/'o0-progress-20261017'
    check.require(sha(builds/'matrix-images.tar.gz') == BUILD_ARCHIVE_SHA, 'build archive changed')
    check.require(sha(builds/'matrix-build.json') == check.BUILD_SHA, 'build receipt changed')
    extract(builds/'matrix-images.tar.gz', output/'images')
    shutil.copyfile(builds/'matrix-build.json', output/'images/result.json')
    extract(HERE/'runs.tar.gz', output/'runs')
    result = summarize_matrix.summarize(output/'images', output/'runs', offline=True)
    saved = check.sealed.strict_json((HERE/'summary.json').read_bytes())
    check.require(result == saved, 'independent summary differs from sealed result')
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(result['status'])


if __name__ == '__main__':
    main()
