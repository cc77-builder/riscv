#!/usr/bin/env python3
"""One-shot R3 evidence sealing recipe; archived as the actually executed tool."""
import gzip, hashlib, importlib.util, json, pathlib, shutil, subprocess, os
os.sched_setaffinity(0, set(sorted(os.sched_getaffinity(0))[:4]))
root = pathlib.Path('/home/lizufan/riscv-lab/r3-perf-20261025-0001')
repo = root / 'source'
windows = pathlib.Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan')
staging = windows / 'r3-perf-runtime-20261025-0001'
destination = windows / 'working-r3-perf-20261025-0001/team/optimizations/o4/perf/evidence/r3-parent-v2'
output = root / 'archive-01'
assert not output.exists() and not destination.exists()
assert json.loads((root/'run-02/runner.status.json').read_text())['passed']
assert json.loads((root/'run-01/runner.status.json').read_text())['passed'] is False
for form in ('raw', 'gzip'):
    result = json.loads((root/f'post-{form}-audit.json').read_text())
    assert result['status'] == 'R3_PERF_PAYLOAD_REPLAY_PASS'
    assert len(result['evidence_mutations']) == 8
    assert all(item['detected'] for item in result['evidence_mutations'].values())
subprocess.run(['git', '-C', str(repo), 'diff', '--exit-code', 'HEAD', '--',
                'src', 'build.sc', '.gitmodules', 'team/rtl/vdot', 'team/models/vdot'],
               check=True, stdout=subprocess.PIPE)
assert not subprocess.check_output(['git', '-C', str(repo), 'ls-files', '--others',
                                    '--exclude-standard', '--', 'src', 'build.sc'])
payloads = {}
def add(name, path):
    assert name not in payloads
    payloads[name] = path
for stage in ('run-01', 'run-02'):
    for path in sorted((root/stage).rglob('*')):
        if path.is_file() and 'obj' not in path.relative_to(root/stage).parts:
            add(path.relative_to(root).as_posix(), path)
names = [
'setup.json', 'setup.log', 'transfer-v1.json', 'working-tree-v1.patch',
'preflight-v1.log', 'tool-launcher.json', 'bin/mill',
'launch-01.command.sh', 'launch-01.state.json', 'launch-01.log',
'launch-02.command.sh', 'launch-02.state.json', 'launch-02.log',
'post-source.json', 'post-audit-commands.json',
'post-raw-audit.json', 'post-raw-audit.log', 'post-gzip-audit.json', 'post-gzip-audit.log',
'consumer-generated-v1.json', 'consumer-source-v1.json', 'historical-reuse-v1.json',
't17-binding-v1.json', 'run-identity-v1.json']
for name in names:
    add('runtime/'+name, root/name)
for item in json.loads((root/'transfer-v1.json').read_text()):
    path = repo/item['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
    add('run-source/'+item['path'], path)
for name, sha in json.loads((root/'post-source.json').read_text()).items():
    path = root/'post-source'/name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
    add('post-source/'+name, path)
for name in ('consumer-generated.py', 'historical-reuse.py', 'consumer-source.py',
             'post-audit.py', 'binding.py', 'seal-r3.py'):
    add('executed-tools/'+name, staging/name)
for name in ('locations.json', 'review-summary.json'):
    add('runtime/'+name, staging/name)
output.mkdir()
entries = []
for name, path in sorted(payloads.items()):
    raw = path.read_bytes()
    assert not raw.startswith(b'\x7fELF')
    compress = len(raw) > 262144
    stored = name + '.gz' if compress else name
    data = gzip.compress(raw, compresslevel=9, mtime=0) if compress else raw
    dest = output/'files'/stored
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    entries.append(dict(path=name, stored=stored, gzip=compress, bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(), stored_bytes=len(data),
        stored_sha256=hashlib.sha256(data).hexdigest()))
(output/'manifest.json').write_text(json.dumps(dict(format=1,entries=entries),indent=2)+'\n')
(output/'external-artifacts.json').write_text(json.dumps(dict(
    scope='Build caches and obj files remain in the isolated native runtime; actual executable identity is in run-02/artifacts.json. Historical T17/O4/H1 bytes are reused by fixed manifests, not duplicated.',
    binary=json.loads((root/'run-02/artifacts.json').read_text())[1],
    runtime=str(root), base_bundle_sha256=json.loads((root/'setup.json').read_text())['bundle_sha256']
),indent=2)+'\n')
verifier = repo/'team/optimizations/o2/result-width/h1/seal.py'
assert hashlib.sha256(verifier.read_bytes()).hexdigest() == 'bc8e490ba981a468387bd90bddda1d9ccccb91b63ca39861a8fefd615b49a034'
spec = importlib.util.spec_from_file_location('existing_byte_verifier', verifier)
module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
byte_result = module.verify(output)
receipt = dict(status='R3_ARCHIVE_BYTE_CHECK_PASS',scope='format-1 byte validation only; no new H1 qualification',
    reused_verifier_result=byte_result, manifest_sha256=hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest(),
    stored_bytes=sum(e['stored_bytes'] for e in entries), payload_files=len(entries),
    largest_stored_blob=max(e['stored_bytes'] for e in entries))
(root/'archive-byte-linux.json').write_text(json.dumps(receipt,indent=2)+'\n')
shutil.copytree(output, destination)
print(json.dumps(receipt, sort_keys=True))
