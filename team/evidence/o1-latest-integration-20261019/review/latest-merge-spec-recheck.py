"""Read sealed upstream performance evidence; recompute without hardware."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path('/mnt/c/Code/RVInno/riscv')
BASE = ROOT / 'team/optimizations/o1/evidence/20261018-performance-ab'
OUT = ROOT / 'team/out/latest-merge-spec-recheck.json'

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def sha(body):
    return hashlib.sha256(body).hexdigest()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def read_json(path):
    if path.is_file():
        return json.loads(path.read_text())
    return json.loads(gzip.decompress(Path(str(path)+'.gz').read_bytes()))

mapping = json.loads((BASE / 'file-map.json').read_text())
for row in mapping:
    raw = (BASE / row['archive']).read_bytes()
    require(sha(raw) == row['archive_sha256'] and len(raw) == row['archive_bytes'], 'archive bytes drift')
    source = gzip.decompress(raw) if row['storage'] == 'gzip' else raw
    require(sha(source) == row['source_sha256'] and len(source) == row['source_bytes'], 'original bytes drift')
manifest = json.loads((BASE / 'archive-manifest.json').read_text())
campaign = BASE / 'files/work/campaign-01'
body = gzip.decompress((campaign / 'result.json.gz').read_bytes())
require(sha(body) == manifest['campaign_result_sha256'], 'campaign result identity')
result = json.loads(body)
compare = load('frozen_paired_compare', BASE / 'files/source/compare.py')
fresh = compare.summarize(result['samples'])
require(fresh == result['rows'], 'frozen statistics mismatch')
compare.compare_replays(result['runs'])
observer = load('current_event_observer', ROOT / 'team/optimizations/o1/fullcore/analyze.py')
gate = load('current_event_gate', ROOT / 'team/optimizations/o1/audit/runtime_gate.py')
checked = []
for row in result['runs']:
    run = campaign / row['mode'] / row['stage'] / (row['image'] + '-r' + str(row['replay']))
    # Original runner uses Path.read_text(): preserve the same universal-newline interpretation.
    streams = [gzip.decompress((run / (name + '.log.gz')).read_bytes()).decode('utf-8').replace('\r\n','\n').replace('\r','\n') for name in ('stderr','stdout')]
    for stream in streams:
        gate.validate_failure_markers(stream)
    actual = observer.analyze(''.join(streams))
    require(actual == read_json(run / 'observation.json'), 'hardened event reparse differs: ' + str(run))
    require(read_json(run / 'result.json') == row, 'run/campaign record differs')
    require((run / 'exit-code.txt').read_text().strip() == '0', 'exit code differs')
    checked.append(str(run.relative_to(campaign)))
receipt = dict(status='LATEST_BRANCH_PERFORMANCE_OFFLINE_RECHECK_PASS', archive_files=len(mapping),
               raw_observations_rechecked=len(checked), samples=len(result['samples']),
               measured_samples=sum(s['stage']=='performance' and s['phase']=='measured' and s['replay']==0 for s in result['samples']),
               frozen_statistics_equal=True, frozen_replays_equal=True,
               current_analyzer_sha256=sha(Path(observer.__file__).read_bytes()),
               frozen_compare_sha256=sha(Path(compare.__file__).read_bytes()),
               new_emu_executed=False, merged_hardware_validation=False, rows=fresh, runs=checked)
with OUT.open('x') as stream:
    json.dump(receipt, stream, indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k not in ('rows','runs')}))
