"""Compare the current compiler/test inputs with this reviewed run, without executing archived code."""
import hashlib
import json
import runpy
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
binding = json.loads((HERE/'source-binding.json').read_bytes())
helper = runpy.run_path(str(ROOT/'team/scripts/prepare-core-baseline.py'))
actual = helper['root_inputs'](ROOT)
if actual != binding['tested_root_git_blobs']:
    raise RuntimeError('Current compiler inputs differ from tested source')
extra = (
    'team/rtl/vdot/GenerateVDotExu.scala', 'team/rtl/vdot/prepare_vectors.py',
    'team/optimizations/o1/parent_test.cpp', 'team/optimizations/o1/check-parent.sh',
    'team/optimizations/o1/parent.vlt', 'team/models/vdot/model.py',
    'team/models/vdot/generate.py', 'team/models/vdot/data/manifest.json',
    'team/models/vdot/data/directed.jsonl', 'team/models/vdot/data/random.jsonl',
)
with tarfile.open(HERE/'tested-inputs.tar.gz') as archive:
    for name in extra:
        old = archive.extractfile(name).read()
        if hashlib.sha256(old).hexdigest() != binding['tested_sha256'][name]:
            raise RuntimeError('Archived source digest differs: '+name)
        if old.replace(b'\r\n', b'\n') != (ROOT/name).read_bytes().replace(b'\r\n', b'\n'):
            raise RuntimeError('Current test input differs: '+name)
result = dict(status='VFEX4_CURRENT_SOURCE_MATCH', compiler_inputs=len(actual),
              additional_test_inputs=len(extra), normalization='Git canonical text / LF',
              archive_sha256=hashlib.sha256((HERE/'tested-inputs.tar.gz').read_bytes()).hexdigest())
(HERE/'workspace-match.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result))
