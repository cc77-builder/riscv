"""Verify the integration bundle without extracting or executing its contents."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


files = json.loads((root/'file-manifest.json').read_text())['files']
present = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
require(present == set(files) | {'file-manifest.json'}, 'file inventory')
for name, digest in files.items():
    path = (root/name).resolve()
    require(path.is_relative_to(root), 'path escape')
    require(sha(path.read_bytes()) == digest, 'file hash '+name)
for name, record in json.loads((root/'raw-logs.json').read_text()).items():
    data = gzip.decompress((root/(name+'.gz')).read_bytes())
    require(len(data) == record['raw_bytes'] and sha(data) == record['raw_sha256'], 'raw log '+name)
bundles = json.loads((root/'bundle-files.json').read_text())
for name, records in bundles.items():
    with tarfile.open(root/(name+'.tar.gz'), 'r:gz') as tar:
        members = tar.getmembers()
        require(len(members) == len(records) and {m.name for m in members} == set(records), 'tar inventory')
        for member in members:
            require(member.isfile(), 'non-file member')
            data = tar.extractfile(member).read()
            record = records[member.name]
            require(len(data) == record['bytes'] and sha(data) == record['sha256'], 'tar member '+member.name)
print('JAMES_T13_INTEGRATION_ARCHIVE_PASS files='+str(len(files))+' bundles='+str(len(bundles)))
