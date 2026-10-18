#!/usr/bin/env python3
"""Replay frozen real-parent binaries and the current reviewed trace checker."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED = 'e2b4b01a76bbfe07de9d5d7b6e1b40cb7902b9e16655aeee810f625c9ed481a2'
sys.path.insert(0, str(ROOT/'team/optimizations/o1'))
from check_trace import audit, require
from audit_trace_negatives import check as negative_check


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main(out):
    archive = HERE/'parent-validation.tar.gz'
    require(sha(archive) == EXPECTED, 'frozen parent archive changed')
    out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as source:
        seen, total = set(), 0
        for item in source:
            name = PurePosixPath(item.name)
            require(not name.is_absolute() and '..' not in name.parts and item.isfile()
                    and item.name not in seen, 'unsafe/duplicate archive member')
            total += item.size
            require(total < 1024**3, 'unexpected archive size')
            seen.add(item.name)
            target = out/name
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(item) as src, target.open('wb') as dst:
                shutil.copyfileobj(src, dst)
    expected = json.loads((HERE/'parent-payload.json').read_text())['files']
    require(set(expected) == seen and all(sha(out/n) == value for n, value in expected.items()),
            'archive file inventory/content differs')
    results = []
    for mode in range(3):
        folder = out/f'parent-02/mode-{mode}'
        executable = folder/'obj/VVDotExuTestTop'
        executable.chmod(0o755)
        log = out/f'replay-{mode}.log'
        command = [str(executable), str(out/'parent-02/vectors.tsv'), str(mode), '-', 'strict-idle']
        with log.open('wb') as stream:
            code = subprocess.run(command, cwd=out, stdout=stream, stderr=subprocess.STDOUT).returncode
        require(code == 0 and sha(log) == sha(folder/'results.log'), 'real-parent replay differs')
        checked = audit(log.read_text().splitlines(), mode, 'parent')
        require(checked == json.loads((out/f'final-parent-checks/mode-{mode}.json').read_text()),
                'independent parser result differs')
        results.append(dict(mode=mode, exit_code=code, log_sha256=sha(log), checked=checked))
    negative = negative_check(out/'replay-2.log')
    result = dict(status='O1_PARENT_ARCHIVE_REPLAY_PASS', modes=results, negatives=negative,
                  archive_sha256=EXPECTED, checker_sha256=sha(ROOT/'team/optimizations/o1/check_trace.py'))
    (out/'replay.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=lambda x: Path(x).resolve())
    main(parser.parse_args().output)
