"""Validate newly finished T13 runs; final paired analysis remains mandatory."""
import json,sys
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
repo=Path('/mnt/c/Code/RVInno/riscv');root=Path((repo/'team/out/james-fullcore-20261016/build-copy.txt').read_text().strip())
sys.path.insert(0,str(root/'team/workloads/vdot-perf'))
import check as c
import analyze
runs=cache/'runs';out=runs/'incremental-checks';out.mkdir(exist_ok=True)
for label in ('t13-main','t13-stream'):
    target=out/label;target.mkdir(exist_ok=True);new=0
    for receipt in sorted((runs/label).glob('*/result.json')):
        saved=target/(receipt.parent.name+'.json')
        if saved.exists():continue
        record=json.loads(receipt.read_text())
        try:
            result=c.verify(Path(record['build']),receipt.parent)
            fu=analyze.fu_statistics(c.read_text(receipt.parent/'stderr.log'))
            c.require(fu['committed']==sum(r['dots'] for r in result['samples'] if r['method']=='vdot'),'FU/architectural dot mismatch')
            result['fu']=fu
        except Exception as error:
            failure=dict(run=str(receipt.parent),error=repr(error))
            (target/(receipt.parent.name+'.failure.json')).write_text(json.dumps(failure,indent=2)+'\n');raise
        with saved.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        new+=1
    print(label,'new verified',new,'total verified',len(list(target.glob('*.json'))),flush=True)
