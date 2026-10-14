"""One finite, newly compiled shard of the historical 117-case matrix."""
import gzip, hashlib, importlib.util, json, re, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
repo = root / 'repo'
spec = importlib.util.spec_from_file_location('driver', repo / 'team/scripts/t12-tests.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
out = root / 'runs/legacy-shard0-run'
out.mkdir(exist_ok=False)
build = root / 'runs/legacy-shard0-build'
data = root / 'runs/legacy-shard0-data'
image = build / 'vdot-exceptions.bin'
source = (build / 'team.sha').read_text().strip()
assert source == 'a4fea8f69f8c2c58f986858481257d3424a903f0'
provenance = driver.g.verify_build(build, image, data, 'vdot', 'full')
for name, digest in provenance['source_sha256'].items():
    relative = str(Path(name).relative_to(repo))
    blob = subprocess.check_output(['git', '-C', str(repo), 'cat-file', 'blob', source + ':' + relative])
    assert hashlib.sha256(blob).hexdigest() == digest, relative
assets = json.loads((root / 'runs/preflight/assets.json').read_text())['assets']
for key in ('emu', 'reference', 'flash'):
    assert driver.sha(assets[key]['path']) == assets[key]['sha256'] == driver.checker.PINS[key]
old = Path('/home/lizufan/xiangshan-t10-t11-supervisor-20261013')
reference_check = driver.g.verify_nemu(old / 'nemu-xs-tval/reference', Path(assets['reference']['path']), 'reference')
driver.write(out / 'reference-verification.json', reference_check)
driver.write(out / 'provenance-check.json', dict(status='SOURCE_BUILD_REFERENCE_VERIFIED', source=source, build_provenance_sha256=driver.sha(build / 'workload-provenance.json'), assets={k: assets[k] for k in ('emu', 'reference', 'flash')}))
cmd = [assets['emu']['path'], '-i', str(image), '--flash', assets['flash']['path'], '--ram-size=128MB', '--diff', assets['reference']['path'], '-C', '1000000', '--no-snapshot']
process = driver.child(cmd, out / 'run.log', timeout=900, cwd=out)
driver.write(out / 'receipt.json', dict(source=source, build=str(build), image_sha256=driver.sha(image), run_log_sha256=driver.sha(out / 'run.log'), **process))
(out / 'run.log.gz').write_bytes(gzip.compress((out / 'run.log').read_bytes(), mtime=0))
driver.success(process)
driver.g.verify_build(build, image, data, 'vdot', 'full')
text = (out / 'run.log').read_text(errors='replace')
assert not re.search(r'EXCEEDING|cycle limit|signal received', text, re.I), 'incomplete simulator termination'
check = [sys.executable, '-B', str(repo / 'team/scripts/check-vdot-run.py'), str(out / 'run.log'), '--mode', 'full', '--exit-code', str(process['exit_code']), '--data', str(data), '--require-diff']
checked_process = driver.child(check, out / 'check.log', timeout=60, cwd=root)
driver.success(checked_process)
checked = json.loads((out / 'check.log').read_text())
assert checked['executed'] == 15
driver.write(out / 'checked.json', checked)
print(json.dumps(checked), flush=True)
