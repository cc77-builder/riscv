import gzip, importlib.util, json, subprocess, sys
from pathlib import Path
repo=Path.cwd()
sys.path.insert(0,str(repo/'team/workloads/vdot-perf'))
import check
out=repo/'team/out/james-sync-20261017'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
current=load('current',repo/'team/scripts/check-vdot-regression.py')
old=out/'frozen-t14-control.py'
old.write_bytes(subprocess.check_output(['git','show','a877e0575:team/scripts/check-vdot-regression.py']))
frozen=load('frozen',old)
archive=repo/'team/evidence/t14-optimization-20261016'
rows=[]
manifest=json.loads((archive/'control-sweep/build/data/manifest.json').read_text())
for variant,latency in [('baseline',3),('candidate',2)]:
    folder=archive/'control-sweep'/variant
    text=check.read_text(folder/'run.log');rc=json.loads((folder/'result.json').read_text())['exit_code']
    a=current.check(text,manifest,rc,fu_latency=latency);b=frozen.check(text,manifest,rc,fu_latency=latency)
    check.require(a['status']==b['status']=='T12_CONTROL_REGRESSION_PASS','control failed')
    rows.append(dict(variant=variant,current=a,frozen=b,differing_keys=[k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)]))
(out/'t14-current-control.json').write_text(json.dumps(rows,indent=2)+'\n')
# Historical equality is checked with the exact historical control observer;
# the current checker above separately validates all current correctness gates.
v=load('historical_t14',repo/'team/scripts/verify-t14-archive.py')
original=v.module
def module(name,file):
    if file=='check-vdot-regression.py':return frozen
    return original(name,file)
v.module=module
v.verify(archive,out/'t14-historical-replay')
