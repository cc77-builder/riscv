"""Verify the exact staged MERGE-REG deliverable, including external reports."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--git', default='git')
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
repo, output = a.repo.resolve(), a.output.resolve()
assert not output.exists()
prefix = 'team/optimizations/o2/fullcore/'
evidence = repo / prefix / 'evidence/merged-regression-v1'
assert output.parent == evidence
expected = {prefix + n for n in ('.gitattributes', 'MERGED_REGRESSION.md', 'MERGED_REGRESSION_RESULT.md',
            'merged_regression.py', 'merged_regression_evidence.py', 'test_merged_regression.py', 'test_merged_regression_evidence.py')}
expected |= {'team/docs/development-route-current.md', '开发计分板.md'}
expected |= {f.relative_to(repo).as_posix() for f in evidence.rglob('*') if f.is_file()}
def git(*args, data=None):
    return subprocess.check_output([a.git, '-C', str(repo), *args], input=data)
changed = {n.decode() for n in git('diff', '--cached', '--name-only', '-z').split(b'\0') if n}
assert changed == expected, {'missing': sorted(expected-changed), 'extra': sorted(changed-expected)}
entries = {}
for line in git('ls-files', '--stage', '-z', '--', prefix, 'team/docs/development-route-current.md', '开发计分板.md').split(b'\0'):
    if not line: continue
    meta, name = line.split(b'\t', 1)
    mode, oid, stage = meta.decode().split()
    path = name.decode()
    if path not in changed: continue
    assert mode == '100644' and stage == '0' and path not in entries
    entries[path] = oid
assert set(entries) == changed
stream = io.BytesIO(git('cat-file', '--batch', data=''.join(entries[n]+'\n' for n in sorted(entries)).encode()))
hashes, size = {}, 0
for name in sorted(entries):
    header = stream.readline().split()
    assert header[0].decode() == entries[name] and header[1] == b'blob'
    raw = stream.read(int(header[2]))
    assert stream.read(1) == b'\n' and raw == (repo/name).read_bytes(), name
    hashes[name] = hashlib.sha256(raw).hexdigest()
    size += len(raw)
assert not stream.read()
result = dict(status='MERGE_REG_COMPLETE_STAGED_DELIVERY_PASS', head=git('rev-parse','HEAD').decode().strip(),
              checked_files=len(entries), checked_bytes=size, file_sha256=hashes,
              scope='exact selected source/docs/archive/reports; this newly generated report is added and checked separately',
              new_emu_runs=0)
output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='file_sha256'},ensure_ascii=False))
