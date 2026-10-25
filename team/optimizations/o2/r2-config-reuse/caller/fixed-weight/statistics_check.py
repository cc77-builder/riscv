"""Independent UART statistics and fixed threshold calculation, no ISA claim.

Uses only Python standard library; does not import the experiment's generator,
path checker, selection function or normal validator. Full runtime qualification
still comes from the separate raw-evidence audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

CONTRACT='r2-s3-fixed-weight-8x32-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def need(ok,msg):
    if not ok:raise ValueError(msg)

def compute(build,run):
    manifest=read(build/'source/manifest.json');br=read(build/'build.json')
    need(br['accepted'] is True and br['exit_code']==0 and br['contract']==manifest['contract']==CONTRACT,'qualified contract')
    need(manifest['counts']==[1,4] and manifest['primary_count']==4,'fixed count groups')
    manual=[]
    for dataset in range(3):
        for group,n in enumerate((1,4)):
            for repeat in range(6):
                order=list(range(12)) if repeat%2==0 else list(range(11,-1,-1))
                for position,choice in enumerate([12]+order+[12]):
                    manual.append(dict(index=13*group+choice,dataset=dataset,repeat=repeat,
                        phase='first' if repeat==0 else 'warmup' if repeat==1 else 'measured',
                        order_group=repeat%2,anchor_position=('start' if position==0 else 'end') if choice==12 else None))
    need(manual==manifest['plan'] and len(manual)==504,'independent plan order')
    all_samples=[];raw_bindings={}
    for label in ('recovery','replay'):
        directory=run/'runs'/label;rec=read(directory/'result.json')
        need(rec['process_started'] and rec['exit_code']==0 and not rec.get('timed_out') and
            rec['image_sha256']==sha(build/'vdot-perf.bin'),'actual successful same-image run')
        pins={n:sha(directory/n) for n in ('stdout.log','stderr.log')}
        need(rec['raw_sha256']==pins,'raw log binding')
        raw_bindings[label]=dict(receipt_sha256=sha(directory/'result.json'),raw_sha256=pins)
        plain=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',(directory/'stdout.log').read_text())
        need(plain.count('FIXED_BEGIN contract='+CONTRACT+' windows=504')==1 and
             plain.count('FIXED_FUNCTIONAL calls=168 controls=8')==1 and
             plain.count('FIXED_END windows=504 failures=0')==1 and plain.count('HIT GOOD TRAP')==1,'complete UART markers')
        rows=[tuple(map(int,m)) for m in re.findall(r'(?m)^FW (\d+) (\d+) (\d+)\r?$',plain)]
        need(len(rows)==504 and [r[0] for r in rows]==list(range(504)),'complete ordered UART windows')
        all_samples.append([dict(step,seq=seq,cycles=cycles,instructions=insns) for step,(seq,cycles,insns) in zip(manual,rows)])
    need(all_samples[0]==all_samples[1],'independent complete UART replay equality')
    samples=all_samples[0];cached=read(run/'runs/recovery/validation.json');groups={}
    for group,n in enumerate((1,4)):
        methods=[]
        for choice in range(12):
            rows=[s for s in samples if s['index']==group*13+choice and s['repeat']>=2]
            need(len(rows)==12,'independent formal sample count')
            data=[sum(s['cycles'] for s in rows if s['dataset']==d) for d in range(3)]
            order=[sum(s['cycles'] for s in rows if s['order_group']==o) for o in range(2)]
            cells=[sum(s['cycles'] for s in rows if (s['dataset'],s['order_group'])==(d,o)) for d in range(3) for o in range(2)]
            total=sum(s['cycles'] for s in rows);row=manifest['rows'][group*13+choice]
            methods.append(dict(id=choice,mode='packed' if choice<6 else 'split',algorithm=choice%6,leaf=row['leaf'],
                total=total,mean=total/12,mean_per_vector_including_setup=total/(12*n),
                by_dataset=data,by_order=order,by_dataset_order=cells,cycles=[s['cycles'] for s in rows],
                instructions=sorted({s['instructions'] for s in rows})))
        pairs=[dict(algorithm=i,reduction=1-methods[i+6]['total']/methods[i]['total'],
            by_dataset=[1-b/a for a,b in zip(methods[i]['by_dataset'],methods[i+6]['by_dataset'])],
            passed=methods[i+6]['total']*100<=methods[i]['total']*95 and
                all(b*100<=a*101 for a,b in zip(methods[i]['by_dataset'],methods[i+6]['by_dataset']))) for i in range(6)]
        anchors=[]
        for d in range(3):
            groups_for_d=[]
            for o in range(2):
                for pos in ('start','end'):
                    rows=[s for s in samples if s['index']==13*group+12 and s['repeat']>=2 and
                        (s['dataset'],s['order_group'],s['anchor_position'])==(d,o,pos)]
                    need(len(rows)==2,'independent anchor coverage')
                    groups_for_d.append(dict(order=o,position=pos,total=sum(s['cycles'] for s in rows)))
            totals=[s['total'] for s in groups_for_d]
            anchors.append(dict(dataset=d,groups=groups_for_d,variation=max(totals)/min(totals)-1,
                passed=max(totals)*100<=min(totals)*101))
        rvv=min(methods[7:12],key=lambda r:(r['total'],r['algorithm']));vdot=methods[6]
        interface=all(r['passed'] for r in pairs);context=all(r['passed'] for r in anchors)
        dot_ok=all(v*1000<=r*995 for v,r in zip(vdot['by_dataset_order'],rvv['by_dataset_order']))
        decision='STOP_INTERFACE' if not interface else 'HOLD_CONTEXT_VARIATION' if not context else 'VDOT_PREFERRED_IN_THIS_PLAN' if dot_ok else 'KEEP_RVV_EXPLICIT'
        result=dict(count=n,primary=n==4,mean_cycles_includes_weight_setup=True,methods=methods,pairs=pairs,anchors=anchors,
            interface_qualified=interface,decision=decision,observed_lowest_rvv=rvv['leaf'],
            selected_method=None if not interface or not context else vdot['leaf'] if dot_ok else rvv['leaf'],
            vdot_reduction_by_dataset=[1-v/r for v,r in zip(vdot['by_dataset'],rvv['by_dataset'])],
            vdot_reduction_by_order=[1-v/r for v,r in zip(vdot['by_order'],rvv['by_order'])],
            vdot_reduction_by_dataset_order=[1-v/r for v,r in zip(vdot['by_dataset_order'],rvv['by_dataset_order'])],
            stable_default_changed=False)
        need(result==cached['selection']['by_count'][str(n)],'independent statistics/decision differs: N='+str(n))
        groups[str(n)]=result
    expected_selection=dict(by_count=groups,primary_count=4,decision=groups['4']['decision'],
        interface_qualified=groups['4']['interface_qualified'],selected_method=groups['4']['selected_method'],
        stable_default_changed=False,application_scope='bounded fixed-A stream example, not an LLM')
    need(cached['selection']==expected_selection,'complete independent selection and primary N4 identity')
    return dict(status='FIXED_WEIGHT_INDEPENDENT_UART_STATISTICS_PASS',contract=CONTRACT,windows=504,
        formal_method_windows=288,formal_anchor_windows=48,by_count=groups,
        primary_count=4,decision=groups['4']['decision'],selected_method=groups['4']['selected_method'],
        qualified_image_sha256=sha(build/'vdot-perf.bin'),build_sha256=sha(build/'build.json'),
        manifest_sha256=sha(build/'source/manifest.json'),checker_sha256=sha(__file__),
        raw_bindings=raw_bindings,new_emu_runs=0,scope='independent raw UART/plan/threshold arithmetic; no replacement ISA qualification')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','run','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();need(not out.exists(),'fresh independent report')
    need(not out.is_relative_to(a.build.resolve()) and not out.is_relative_to(a.run.resolve()) and
         not out.is_relative_to(Path(__file__).resolve().parent),'external independent report')
    result=compute(a.build.resolve(),a.run.resolve());out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
