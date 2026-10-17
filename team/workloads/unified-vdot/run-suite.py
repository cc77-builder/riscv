"""Correctness gates precede benchmark acceptance; no remote mutation."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import campaign
import check


def validate_inventory(images, variant):
    expected = {(suite, dataset, shard): shards
                for suite, dataset, shards in [('smoke', 0, 1), ('functional', 0, 3)]
                + [('performance', dataset, 4) for dataset in range(3)]
                for shard in range(shards)}
    check.require(len(images) == len(expected), 'incomplete image inventory')
    seen, paths = set(), set()
    for item in images:
        key = (item['suite'], item['dataset'], item['shard'])
        check.require(key in expected and key not in seen, 'duplicate/unknown image')
        seen.add(key)
        name = f'{key[0]}-d{key[1]}-s{key[2]:02d}'
        check.require(item['name'] == name and item['replays'] == 1, 'image name/replay binding mismatch')
        path = Path(item['path']).resolve()
        check.require(path not in paths, 'duplicate image path')
        paths.add(path)
        manifest = json.loads((path/'data/manifest.json').read_text())
        check.require(manifest['variant'] == variant, 'image variant binding mismatch')
        check.require((manifest['suite'], manifest['dataset'], manifest['shard']) == key
                      and manifest['shards'] == expected[key], 'image manifest binding mismatch')
        check.require(manifest.get('shared_stream') is True, 'shared input contract missing')


def main(a):
    a.output.mkdir(parents=True,exist_ok=False)
    images=json.loads((a.images/'images.json').read_text())['images']
    validate_inventory(images, a.variant)
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
