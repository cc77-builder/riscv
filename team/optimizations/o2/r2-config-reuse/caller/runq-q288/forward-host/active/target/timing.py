"""Locate quantization and Q/K/V on already-qualified retirement timelines.

These are ordered retirement coordinates, not causal or removable cycle costs.
The sum of five coordinate intervals equals the existing whole-window CSR delta.
No new EMU execution or independent performance sample is created.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,importlib.util,json,os,zipfile
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('qkv_timing_runtime',HERE/'run.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);g=e.g
ELF_SHA='be7412fdc3d9c1f0dac167f6bbc61fac03eed2454f04652cd3ca321d9296d7d6'
STAGES=('quantize','Q','K','V')
INTERVALS=('entry_to_quantize','quantize_to_Q','Q_to_K','K_to_V','V_to_exit')

def path_labels(elf,path,row):
    ranges={n:(elf.symbols[n][0],elf.symbols[n][0]+len(elf.symbol_data(n)))
            for n in ('split_measure','qkv_boundary','qkv_quantize',row['kernel'])}
    labels=[];projection=-1
    for pc,word in path:
        names=[name for name,(lo,hi) in ranges.items() if lo<=pc<hi]
        g.require(len(names)==1,'unique owner for every retired path word')
        owner=names[0]
        if owner==row['kernel']:
            if pc==ranges[owner][0]:projection+=1
            g.require(0<=projection<3,'exactly three sequential projection entries')
            label=STAGES[1+projection]
        else:label={'split_measure':'timer','qkv_boundary':'wrapper','qkv_quantize':'quantize'}[owner]
        labels.append(label)
    g.require(projection==2,'all Q/K/V entries reached')
    bounds={}
    for stage in STAGES:
        positions=[i for i,label in enumerate(labels) if label==stage]
        g.require(positions and positions==list(range(positions[0],positions[-1]+1)),
                  'one contiguous dynamic function call for '+stage)
        bounds[stage]=(positions[0],positions[-1])
    g.require(all(bounds[a][1]<bounds[b][0] for a,b in zip(STAGES,STAGES[1:])),'quantize then Q/K/V')
    return labels,bounds

def coordinates(elf,path,row,records,sample):
    labels,bounds=path_labels(elf,path,row);ticks=[];position=0
    for event in records:
        count=event['count'];covered=path[position:position+count]
        g.require(len(covered)==count and (event['pc'],event['word'])==covered[0],'actual record/path correspondence')
        if count>1:
            g.require(not any(word&127 in (0x63,0x6f,0x67) for _,word in covered),'no control in compressed record')
            g.require(len(set(labels[position:position+count]))==1,'no compressed record crosses function ownership')
        ticks.extend([event['cycle']]*count);position+=count
    g.require(position==len(path) and all(a<=b for a,b in zip(ticks,ticks[1:])), 'complete ordered retirement coordinates')
    start,end=sample['sample_ticks'][1:3]
    cuts=[start]+[ticks[bounds[stage][0]] for stage in STAGES]+[end]
    g.require(all(a<=b for a,b in zip(cuts,cuts[1:])) and end-start==sample['cycles'],'coordinate cuts within actual CSR window')
    intervals={name:b-a for name,a,b in zip(INTERVALS,cuts,cuts[1:])}
    g.require(sum(intervals.values())==sample['cycles'],'exact whole-window coordinate partition')
    phases={stage:dict(first_path_index=bounds[stage][0],last_path_index=bounds[stage][1],
        first_retire_tick=ticks[bounds[stage][0]],last_retire_tick=ticks[bounds[stage][1]],
        retired_span_inclusive=ticks[bounds[stage][1]]-ticks[bounds[stage][0]]+1,
        retired_instructions=bounds[stage][1]-bounds[stage][0]+1) for stage in STAGES}
    return dict(seq=sample['seq'],id=sample['id'],kernel=row['kernel'],cycles=sample['cycles'],
        csr_instret=sample['instructions'],whole_marker_instructions=len(path),ownership_instructions=dict(Counter(labels)),
        sample_start_tick=start,sample_end_tick=end,intervals=intervals,phases=phases)

def analyze(archive,qualification,out):
    g.require(not out.exists() and not out.is_relative_to(archive) and not out.is_relative_to(e.ROOT),
              'fresh diagnostic output outside inputs')
    manifest=e.read(archive/'archive-manifest.json');qualified=e.read(qualification)
    g.require(manifest['contract']==e.CONTRACT and manifest['format']=='split-evidence-zip-v1','qualified archive contract')
    g.require(qualified['status']=='ACTUAL_QKV_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS' and
              qualified['archive_manifest_sha256']==g.sha(archive/'archive-manifest.json'),'completed matching fresh-source qualification')
    g.require(g.sha(archive/'payload.zip')==manifest['payload_sha256'],'whole raw payload identity')
    members={row['path']:row for row in manifest['files']};g.require(len(members)==len(manifest['files']),'unique member inventory')
    pins=e.sources(e.ROOT);used={};results={}
    with zipfile.ZipFile(archive/'payload.zip') as z:
        def accept(name,raw):
            row=members[name];pin=e.digest(raw)
            g.require(len(raw)==row['raw_bytes'] and pin==row['raw_sha256'],'raw member identity '+name)
            used[name]=pin;return raw
        def read(name):return accept(name,z.read(name))
        def doc(name):return json.loads(read(name))
        build=doc('build/build.json')
        g.require(build['accepted'] is True and build['software_files']==pins,'same complete runtime source closure')
        raw=read('build/vdot-perf.elf');g.require(e.digest(raw)==ELF_SHA,'fixed measured ELF')
        elf=g.ELF(raw);plan=doc('build/source/manifest.json');paths,_=e.paths_for_plan(elf,plan)
        counter=g.load('qkv_timing_counter',e.ROOT/'team/workloads/unified-vdot/check.py')
        counter.walk=lambda stream:stream
        for label in ('recovery','replay'):
            name='run/runs/'+label+'/stderr.log';fingerprint=hashlib.sha256();size=0;lines=[]
            with z.open(name) as stream:
                for line in stream:
                    size+=len(line);fingerprint.update(line)
                    if line.startswith(b'T13_'):lines.append(line.decode('utf-8'))
            row=members[name];pin=fingerprint.hexdigest()
            g.require(size==row['raw_bytes'] and pin==row['raw_sha256'],'complete original stderr identity')
            used[name]=pin;events=counter.parse_events(''.join(lines));del lines
            samples=counter.trace_windows(events,plan,paths)
            cached=doc('run/runs/'+label+'/validation.json')
            g.require(cached['status']=='ACTUAL_QKV_DIFFTEST_AND_COMPLETE_PLAN_PASS' and
                      cached['contract']==e.CONTRACT and len(samples)==len(cached['samples'])==6,'qualified complete normal result')
            g.require(all(a=={k:b[k] for k in a} for a,b in zip(samples,cached['samples'])),'all CSR/path samples equal original validation')
            windows=[];current=None
            for event in events['RETIRE']:
                if event['word']==counter.START:current=[]
                if current is not None:current.append(event)
                if event['word']==counter.STOP:windows.append(current);current=None
            g.require(current is None and len(windows)==6,'complete six-window inventory')
            results[label]=[coordinates(elf,paths[step['index']],plan['rows'][step['index']],records,sample)
                for step,records,sample in zip(plan['plan'],windows,samples)]
    g.require(results['recovery']==results['replay'],'all retirement coordinate rows reproduced exactly')
    g.require(e.sources(e.ROOT)==pins,'runtime source closure unchanged')
    result=dict(status='ACTUAL_QKV_RETIREMENT_COORDINATES_PASS',contract=e.CONTRACT,
        archive_manifest_sha256=g.sha(archive/'archive-manifest.json'),payload_sha256=manifest['payload_sha256'],
        qualification_sha256=g.sha(qualification),elf_sha256=ELF_SHA,auditor_sha256=g.sha(__file__),
        source_files=pins,raw_members=used,windows=results['recovery'],replay_identical=True,new_emu_runs=0,
        coordinate_definition='half-open differences between CSR start, first retiring instructions of quantize/Q/K/V, and CSR end',
        causal_attribution=False,independent_component_benchmark=False,removable_cycle_budget=False,
        includes_wrapper_and_overlap_effects=True,adds_performance_samples=False)
    out.mkdir(parents=True);g.save(out/'result.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','qualification','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    result=analyze(a.archive.resolve(),a.qualification.resolve(),a.output.resolve())
    print(json.dumps({k:result[k] for k in ('status','windows','replay_identical','new_emu_runs')},indent=2))
