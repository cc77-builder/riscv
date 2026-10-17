"""Recheck all sealed unified images using the integrated acceptance gates."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path.cwd()
OUT = ROOT/'team/out/james-sync-20261017'
ARCHIVE = ROOT/'team/evidence/unified-vdot-20261017/archive'
sys.path.insert(0, str(ROOT/'team/workloads/unified-vdot'))
import check
spec = importlib.util.spec_from_file_location('suite', ROOT/'team/workloads/unified-vdot/run-suite.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)
files = json.loads((ARCHIVE/'文件校验.json').read_text())['files']
for name, expected in files.items():
    path = (ARCHIVE/name).resolve()
    check.require(path.is_relative_to(ARCHIVE.resolve()), 'unsafe storage path')
    check.require(check.sha(path) == expected, 'stored bytes changed: '+name)
images = OUT/'unified-images'
images.mkdir(exist_ok=False)
with tarfile.open(ARCHIVE/'测试镜像与构建快照.tar.gz') as archive:
    archive.extractall(images, filter='data')
result = dict(status='RUNNING', historical=True, hardware_rerun=False, stored_files=len(files), variants={})
for variant in ('ours', 'jade', 'shishui', 'redoop'):
    items = []
    for build in sorted((images/variant).iterdir()):
        manifest = json.loads((build/'data/manifest.json').read_text())
        items.append(dict(name=build.name, suite=manifest['suite'], dataset=manifest['dataset'],
                          shard=manifest['shard'], path=str(build), replays=1))
    suite.validate_inventory(items, variant)
    samples = []
    records = []
    saved_suite = json.loads((ARCHIVE/'验证证据'/variant/'result.json').read_text())
    for item in items:
        run = ARCHIVE/'验证证据'/variant/item['name']
        raw = json.loads((run/'result.json').read_text())
        verdict = check.verify(Path(item['path']), run, raw['files'])
        saved = json.loads((run/'check.json').read_text())
        check.require(verdict == saved, 'recomputed result differs: '+variant+'/'+item['name'])
        records.append(dict(image=item['name'], windows=len(verdict['samples'])))
        samples.extend(dict(row, variant=variant, stage=item['suite'], run=str(run)) for row in verdict['samples'])
    def key(row):
        return {k:v for k,v in row.items() if k!='run'}
    canonical = lambda rows: sorted((json.dumps(key(r),sort_keys=True) for r in rows))
    check.require(canonical(samples) == canonical(saved_suite['samples']), 'suite sample inventory changed')
    result['variants'][variant] = dict(images=len(items), windows=len(samples), runs=records)
    (OUT/'unified-replay.json').write_text(json.dumps(result, indent=2)+'\n')
    print(variant, len(items), len(samples), flush=True)
result['status']='UNIFIED_ARCHIVE_CURRENT_CHECKER_PASS'
check.require(sum(r['images'] for r in result['variants'].values())==64, 'image count')
check.require(sum(r['windows'] for r in result['variants'].values())==860, 'window count')
(OUT/'unified-replay.json').write_text(json.dumps(result, indent=2)+'\n')
