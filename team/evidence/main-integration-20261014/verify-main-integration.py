from pathlib import Path
import hashlib
import json
import subprocess
import sys
import importlib.util
import time

root = Path(__file__).resolve().parents[2]
evidence = root / 'team/evidence/main-integration-20261014'
evidence.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(root / 'team/scripts'))
spec = importlib.util.spec_from_file_location('core_pack', root / 'team/scripts/prepare-core-baseline.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def git(*args):
    return subprocess.check_output(['git', *args], cwd=root).decode().strip()

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(name, value):
    (evidence / name).write_bytes(value.encode('utf-8'))

def dump(name, value):
    write(name, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

before = '5389bde799f5ce1e7939e4eeed5fe9bcdc2325a3'
source = '9bb544812df9b424e399ae3ca91899a904f583bd'
require(git('rev-parse', 'HEAD') == source and git('branch', '--show-current') == 'main', 'Unexpected integration HEAD')
require(git('rev-parse', 'HEAD^{tree}') == git('rev-parse', 'James_Hotten^{tree}'), 'Integration tree differs')
names = git('diff', '--name-only', before, source).splitlines()
write('changes.txt', '\n'.join(names) + '\n')
write('diff-summary.txt', git('diff', '--shortstat', before, source) + '\n')
write('commits.txt', git('log', '--format=%H %s', before + '..' + source) + '\n')
archives = {}
for manifest in sorted(root.joinpath('team/evidence').rglob('archive.sha256')):
    if manifest.parent == evidence:
        continue
    lines = manifest.read_text().splitlines()
    for line in lines:
        expected, name = line.split('  ', 1)
        require(sha(manifest.parent / name) == expected, 'Archive changed: ' + str(manifest.parent / name))
    archives[manifest.parent.name] = len(lines)
dump('inherited-archives.json', {'status': 'PASS', 'archives': archives, 'total_files': sum(archives.values())})
pack = root / 'team/out/t10-source-pack-20261014-v5/source-pack.json'
frozen = json.loads(pack.read_bytes())
require(core.root_inputs(root) == frozen['canonical_root_inputs'], 'Compiler input differs from inherited T10 pack')
require(core.modules(root) == frozen['modules'], 'Pinned modules differ')
dump('source-binding-check.json', {'status': 'PASS', 'source_pack_sha256': sha(pack), 'canonical_compiler_inputs': len(frozen['canonical_root_inputs']), 'pinned_modules': len(frozen['modules']), 'scope': 'Current canonical root files and module revisions checked against inherited T10 pack; full-core simulation not rerun'})

command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'team/tests', '-p', 'test_*.py', '-v']
start = time.monotonic()
with (evidence / 'python-tests.log').open('wb') as log:
    result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
elapsed = time.monotonic() - start
write('python-tests.status', 'exit_code=' + str(result.returncode) + '\n')
require(result.returncode == 0, 'Python regression failed; see evidence log')
require('Ran 33 tests' in (evidence / 'python-tests.log').read_text() and (evidence / 'python-tests.log').read_text().rstrip().endswith('OK'), 'Missing actual test summary')
dump('integration-check.json', {'status': 'LOCAL_MAIN_INTEGRATION_PASS', 'base': before, 'source': source, 'source_tree': git('rev-parse', source + '^{tree}'), 'merge_method': 'fast-forward', 'changed_files': len(names), 'archive_files_verified': sum(archives.values()), 'archives_verified': len(archives), 'python_methods_pass': 33, 'python_command': command, 'elapsed_seconds': round(elapsed, 3), 'platform': sys.platform, 'remote_main_pushed': False, 't11_complete': False, 'member_review_signed': False, 'heavy_simulation_rerun': False})
print(json.dumps({'status': 'LOCAL_MAIN_INTEGRATION_PASS', 'inherited_archives': len(archives), 'archive_files_verified': sum(archives.values()), 'python_methods_pass': 33, 'elapsed_seconds': round(elapsed, 3), 'compiler_inputs': len(frozen['canonical_root_inputs'])}, sort_keys=True))
