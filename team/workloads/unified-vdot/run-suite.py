"""Correctness gates precede benchmark acceptance; no remote mutation."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import campaign
import check


def main(a):
    a.output.mkdir(parents=True,exist_ok=False)
    images=json.loads((a.images/'images.json').read_text())['images']
    state={'variant':a.variant,'status':'RUNNING','stages':[], 'started':campaign.now()}
    campaign.save(a.output/'state.json',state)
    all_samples=[]
    for stage in ('smoke','functional','performance'):
        folder=a.output/(stage+'-input');folder.mkdir()
        selected=[x for x in images if x['suite']==stage]
        check.require(selected,'empty stage')
        campaign.save(folder/'images.json',{'images':selected})
        out=a.output/stage
        campaign.run(SimpleNamespace(output=out,images=folder,emu=a.emu,
             reference=a.reference,flash=a.flash,jobs=a.jobs))
        accepted=[]
        for item in selected:
            run=out/(item['name']+'-r0')
            verdict=check.verify(Path(item['path']),run)
            campaign.save(run/'check.json',verdict)
            accepted.append({'name':item['name'],'samples':len(verdict['samples'])})
            for sample in verdict['samples']:
                all_samples.append(dict(sample,variant=a.variant,stage=stage,run=str(run)))
        state['stages'].append({'name':stage,'status':'PASS','images':accepted})
        campaign.save(a.output/'state.json',state)
        print(a.variant+' '+stage+' CALIBRATED_DIFFTEST_PASS',flush=True)
    state.update(status='UNIFIED_FULLCORE_PASS',finished=campaign.now(),samples=all_samples)
    campaign.save(a.output/'result.json',state)
    campaign.save(a.output/'state.json',{k:v for k,v in state.items() if k!='samples'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant',required=True,choices=('ours','jade','shishui','redoop'))
    for name in ('images','output','emu','reference','flash'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--jobs',type=int,default=2)
    a=p.parse_args()
    try:main(a)
    except Exception as e:
        campaign.save(a.output/'failure.json',{'error':repr(e),'when':campaign.now()})
        raise
