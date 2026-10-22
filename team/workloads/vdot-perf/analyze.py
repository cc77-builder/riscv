"""Verify the complete T13 campaign before exporting paired comparisons."""
import argparse
from collections import defaultdict
import csv
import importlib.util
import json
from pathlib import Path
from statistics import median
import check as c


def fu_statistics(text, fu_latency=3):
    path=Path(__file__).resolve().parents[2]/'scripts/check-vdot-regression.py'
    spec=importlib.util.spec_from_file_location('t12_observer',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    events,_=module.extract_events(text)
    events=module.normalize_fu_cycles(events, min_response_latency=fu_latency)
    pending=None;latencies=[];accepted=0;killed=0;stalls=0;committed=0
    intervals=[];previous=None
    for cycle,order,kind,f in sorted(events,key=lambda e:(e[0],e[1])):
        if kind=='ACCEPT':
            c.require(pending is None,'two FU requests');accepted+=1
            if previous is not None:intervals.append(cycle-previous)
            previous=cycle;pending=(cycle,f['rob'],f['pdest'])
        elif kind=='RESPONSE':
            c.require(pending is not None and (f['rob'],f['pdest'])==pending[1:],'FU response identity')
            c.require(f['illegal']=='0' and int(f['data'],16)>>32==0,'invalid FU response')
            latencies.append(cycle-pending[0]);pending=None
        elif kind=='KILL':
            c.require(pending is not None and f['rob']==pending[1],'FU kill identity');killed+=1;pending=None
        elif kind=='STALL':stalls+=1
        elif kind=='COMMIT':committed+=1
    c.require(pending is None and accepted==len(latencies)+killed,'FU conservation')
    return dict(accepted=accepted,responses=len(latencies),killed=killed,stalls=stalls,committed=committed,
                response_latency_min=min(latencies,default=None),response_latency_max=max(latencies,default=None),
                response_latency_histogram={str(x):latencies.count(x) for x in sorted(set(latencies))},
                acceptance_interval_min=min(intervals,default=None),scope='all accepted transactions, including speculation; gated ticks normalized per parent handshake')


def analyze(images,runs,stream_images,stream_runs,out,external=None,fu_latency=3):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    selected=[]
    for source,logs,only_stream in [(Path(images),Path(runs),False),(Path(stream_images),Path(stream_runs),True)]:
        inventory=json.loads((source/'images.json').read_text())['images']
        for image in inventory:
            is_stream=image['suite']=='performance' and image['shard'] in (7,8,9)
            if is_stream!=only_stream:continue
            for replay in range(image['replays']):
                name=image['name']+f'-r{replay}'
                selected.append((image,replay,source/image['name'],logs/name))
    c.require(len(selected)==126,'expected 9 functional and 117 performance runs')
    samples=[];receipts=[]
    for image,replay,build,run in selected:
        result=c.verify(build,run,external)
        if image['suite']=='performance' and image['shard'] in (7,8,9):
            c.require(json.loads((build/'data/manifest.json').read_text()).get('shared_stream'),'stream input not shared')
        fu=fu_statistics(c.read_text(run/'stderr.log'), fu_latency=fu_latency)
        expected=sum(r['dots'] for r in result['samples'] if r['method']=='vdot')
        c.require(fu['committed']==expected,'FU/architectural dot count mismatch')
        result['fu']=fu
        (out/(run.name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        receipts.append(dict(name=run.name,image=image['name'],replay=replay,suite=image['suite'],samples=len(result['samples']),fu=fu))
        for row in result['samples']:
            samples.append(dict(row,image=image['name'],replay=replay,suite=image['suite'],run=run.name))
    c.require(sum(r['suite']=='functional' for r in samples)==108,'functional cardinality')
    perf=[r for r in samples if r['suite']=='performance']
    c.require(len(perf)==1404,'performance cardinality')
    replay_groups=defaultdict(list)
    for r in perf:replay_groups[(r['image'],r['seq'])].append(r)
    for key,group in replay_groups.items():
        c.require(sorted(r['replay'] for r in group)==[0,1,2],'missing/duplicate replay')
        c.require(len({(r['cycles'],r['instructions']) for r in group})==1,'replay divergence '+str(key))
    pairs=defaultdict(dict)
    for r in perf:
        key=(r['scenario'],r['n'],r['dataset'],r['replay'],r['repeat'],r['phase'])
        c.require(r['method'] not in pairs[key],'duplicate paired sample');pairs[key][r['method']]=r
    pair_rows=[]
    for (scenario,n,dataset,replay,repeat,phase),group in sorted(pairs.items()):
        c.require(set(group)=={'vdot','rvv'},'missing paired method')
        v,r=group['vdot'],group['rvv'];c.require(v['dots']==r['dots'],'pair size')
        pair_rows.append(dict(scenario=scenario,n=n,dataset=dataset,replay=replay,repeat=repeat,phase=phase,dots=v['dots'],vdot_cycles=v['cycles'],rvv_cycles=r['cycles'],vdot_instructions=v['instructions'],rvv_instructions=r['instructions'],speedup=r['cycles']/v['cycles'],cycle_reduction=1-v['cycles']/r['cycles']))
    stats=[]
    for key in sorted({(r['scenario'],r['n'],r['dataset']) for r in pair_rows}):
        group=[r for r in pair_rows if (r['scenario'],r['n'],r['dataset'])==key and r['phase']=='measured' and r['replay']==0]
        c.require(len(group)==4,'measured round count')
        row=dict(zip(('scenario','n','dataset'),key));row['dots']=group[0]['dots']
        for method in ('vdot','rvv'):
            values=[r[method+'_cycles'] for r in group]
            row.update({method+'_min':min(values),method+'_median':median(values),method+'_max':max(values),method+'_cycles_per_dot':median(values)/row['dots'],method+'_instructions':group[0][method+'_instructions']})
        values=[r['speedup'] for r in group]
        row.update(speedup_min=min(values),speedup_median=median(values),speedup_max=max(values))
        stats.append(row)
    for name,rows in [('samples',samples),('pairs',pair_rows),('summary',stats)]:
        with (out/(name+'.csv')).open('w',newline='') as f:
            fields=[k for k in rows[0] if k not in ('counter_values','sample_ticks')]
            writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
        (out/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
    result=dict(status='T13_FAIR_CYCLE_COMPARISON_PASS',runs=len(receipts),functional_calls=108,performance_windows=1404,unique_images=48,paired_configurations=39,measured_rounds_per_config=4,fresh_replays=3,replay_identical=True,receipt=receipts,summary=stats,excluded='Original stream-v3 uses different input buffers; all 27 original stream runs are diagnostic only. Selection was fixed before inspecting their cycles.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('receipt','summary')}))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('images','runs','stream-images','stream-runs','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--external',type=Path)
    p.add_argument('--fu-latency',type=int,choices=(2,3),default=3)
    a=p.parse_args();analyze(a.images,a.runs,a.stream_images,a.stream_runs,a.output,json.loads(a.external.read_text()) if a.external else None,fu_latency=a.fu_latency)
