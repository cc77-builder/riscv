"""Recheck sealed T13 runs with current gates; do not replay old checker code."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'team/workloads/vdot-perf'))
import check
import analyze

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args=parser.parse_args()
out=args.output.resolve()
check.require(not out.exists() and not out.is_relative_to(ROOT/'team/evidence'), 'use a fresh work directory')
archive=ROOT/'team/evidence/james-fullcore-20261016'
check.require(sha(archive/'file-manifest.json') == '629b739abd128dc9887fc4bd0557f7c252e159da81b84ae39aa6fb0bc464596b', 'sealed manifest changed')
for name,digest in read(archive/'file-manifest.json')['files'].items():
    check.require(Path(name).name==name and sha(archive/name)==digest, 'archive identity changed')
out.mkdir(parents=True)
inventories=read(archive/'bundle-files.json')
for bundle in ('runs','workloads'):
    entries=inventories[bundle]
    with tarfile.open(archive/(bundle+'.tar.gz')) as tar:
        members=tar.getmembers()
        check.require(len(members)==len(entries) and {m.name for m in members}==set(entries),'bundle inventory')
        for member in members:
            target=(out/bundle/member.name).resolve()
            check.require(member.isfile() and target.is_relative_to(out/bundle),'unsafe archive member')
            data=tar.extractfile(member).read()
            check.require(len(data)==entries[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==entries[member.name]['sha256'],'member changed')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
work,runs=out/'workloads',out/'runs'
completion=read(runs/'completion.json')
smoke=read(runs/'smoke-hello-vadd/result.json')
roles=check.runtime_roles(smoke['command'])
external={roles[role]:smoke['files'][roles[role]] for role in ('emu','reference','flash')}
check.require(external[roles['emu']]==completion['emu_sha256'] and external[roles['reference']]==completion['reference_sha256'],'runtime identity')
source={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'team/workloads/vdot-perf/check.py',ROOT/'team/workloads/vdot-perf/analyze.py',ROOT/'team/scripts/check-vdot-regression.py')}
cal=check.verify(work/'calibration',runs/'calibration/calibration-r0',external)
check.require(cal==read(runs/'calibration-check.json') and len(cal['samples'])==13,'calibration changed')
result=analyze.analyze(work/'t13-images',runs/'t13-main',work/'t13-stream',runs/'t13-stream',out/'analysis',external)
check.require(result==read(runs/'analysis/result.json'),'T13 result changed')
check.require(source=={name:sha(ROOT/name) for name in source},'checker changed during recheck')
receipt=dict(status='T13_CURRENT_GATES_RECHECK_PASS', calibration_windows=13, accepted_runs=126,
             performance_windows=1404, all_results_identical=True, hardware_rerun=False,
             current_source_sha256=source, hardware_source=completion['source'])
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(receipt))
