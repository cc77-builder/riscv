"""Aggregate both completed software plans independently of the runtime driver."""
import hashlib,importlib.util,json
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv');cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
spec=importlib.util.spec_from_file_location('compact',repo/'team/scripts/check_t12_compact.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
summary={}
for baseline,count in (('original',190),('lean',199)):
    folder=cache/'runs'/('software-'+baseline);data=cache/'workloads'/('software-'+baseline)/'data'
    receipt=load(folder/'result.json')
    m.require(receipt['exit_code']==0 and 'verification_error' not in receipt,'software failure')
    m.require(all(sha(folder/n)==h for n,h in receipt['raw_sha256'].items()),'raw log changed')
    m.require(all(sha(Path(p))==h for p,h in receipt['files'].items()),'runtime file changed')
    checked=m.check((folder/'stderr.log').read_text()+(folder/'stdout.log').read_text(),data,0,count,receipt['exit_code'])
    m.require(checked==load(folder/'checked.json'),'runtime check differs')
    plan=m.aggregate([checked],data)
    m.require(plan['executed']==count and plan['baseline']==baseline,'incomplete/wrong plan')
    target=folder/'plan.json'
    with target.open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
    summary[baseline]=dict(status=plan['status'],executed=plan['executed'],metrics=len(plan['metrics']),pairs=len(plan['pairs']),manifest_sha256=sha(data/'manifest.json'))
target=cache/'runs/software-plans.json'
with target.open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print(json.dumps(summary))
