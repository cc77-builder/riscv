"""Targeted fixed-stream checker mutations; frozen artifacts are never modified.

N=1 passing while N=4 rejects stale step addresses shows why the new lifecycle
coverage matters. Vector-result values remain opaque to the path checker and
are independently checked by the C oracle, host faults and live DiffTest.
"""
import argparse
import copy
from pathlib import Path
import re
import shutil
import struct
import tempfile
import run as e

class ChangedFunction:
    def __init__(self,elf,name,index,word):
        self.elf,self.name,self.symbols=elf,name,elf.symbols
        raw=bytearray(elf.symbol_data(name));struct.pack_into('<I',raw,index*4,word);self.raw=bytes(raw)
    def symbol_data(self,name):return self.raw if name==self.name else self.elf.symbol_data(name)

def selection_tests(manifest):
    outcomes=[]
    def synthetic(packed=20000,split=19000):
        result=[]
        for step in manifest['plan']:
            row=manifest['rows'][step['index']]
            result.append(dict(id=row['id'],n=row['n'],phase=step['phase'],repeat=step['repeat'],dataset=step['dataset'],
                order_group=step['order_group'],anchor_position=step['anchor_position'],instructions=1,
                cycles=100 if row['anchor'] else packed if row['mode']=='packed' else split))
        return result
    for count,base in ((1,0),(4,13)):
        other=str(4 if count==1 else 1)
        boundary=synthetic()
        for s in boundary:
            if s['id']==base+12 and s['anchor_position']=='end':s['cycles']=101
        result=e.selection(boundary,manifest)
        e.g.require(all(v['interface_qualified'] for v in result['by_count'].values()) and
            all(a['passed'] for a in result['by_count'][str(count)]['anchors']),'exact 5%/1% thresholds')
        bad=copy.deepcopy(boundary)
        next(s for s in bad if s['id']==base+12 and s['phase']=='measured' and s['anchor_position']=='end')['cycles']+=1
        checked=e.selection(bad,manifest)
        e.g.require(checked['by_count'][str(count)]['decision']=='HOLD_CONTEXT_VARIATION' and
            checked['by_count'][other]==result['by_count'][other],'anchor boundary and N isolation')
        bad=synthetic();good=e.selection(bad,manifest)
        next(s for s in bad if s['id']==base+6 and s['phase']=='measured')['cycles']+=1
        checked=e.selection(bad,manifest)
        e.g.require(checked['by_count'][str(count)]['decision']=='STOP_INTERFACE' and
            checked['by_count'][other]==good['by_count'][other],'interface boundary and N isolation')
        boundary=synthetic()
        for s in boundary:
            if base+6<=s['id']<base+12:s['cycles']=20200 if s['dataset']==0 else 18000
        e.g.require(e.selection(boundary,manifest)['by_count'][str(count)]['interface_qualified'],'exact dataset regression boundary')
        next(s for s in boundary if s['id']==base+6 and s['dataset']==0 and s['phase']=='measured')['cycles']+=1
        e.g.require(not e.selection(boundary,manifest)['by_count'][str(count)]['interface_qualified'],'above dataset regression boundary')
        boundary=synthetic(packed=25000,split=20000)
        for s in boundary:
            if s['id']==base+6:s['cycles']=19900
        e.g.require(e.selection(boundary,manifest)['by_count'][str(count)]['decision']=='VDOT_PREFERRED_IN_THIS_PLAN','exact 0.5% vdot boundary')
        next(s for s in boundary if s['id']==base+6 and s['phase']=='measured')['cycles']+=1
        checked=e.selection(boundary,manifest)
        e.g.require(checked['by_count'][str(count)]['decision']=='KEEP_RVV_EXPLICIT','one-cell vdot boundary')
        e.g.require(checked['decision']==checked['by_count']['4']['decision'],'N4 primary decision only')
        outcomes.append(dict(name='integer-boundaries-and-independent-N-selection',count=count,passed=True))
    different=synthetic(packed=25000,split=20000)
    for s in different:
        if s['id'] in (7,24):s['cycles']=19000
    chosen=e.selection(different,manifest)
    e.g.require(chosen['by_count']['1']['observed_lowest_rvv']==manifest['rows'][7]['leaf'] and
        chosen['by_count']['4']['observed_lowest_rvv']==manifest['rows'][24]['leaf'],
        'independent lowest RVV in each N group')
    e.g.require(chosen['selected_method']==chosen['by_count']['4']['selected_method'] and
        chosen['interface_qualified']==chosen['by_count']['4']['interface_qualified'],'primary N4 selection identity')
    outcomes.append(dict(name='different-fastest-rvv-by-count',passed=True))
    return outcomes


def tests(repo,build,run=None):
    valid=e.verification(repo,build);manifest=e.read(build/'source/manifest.json')
    elf=e.g.ELF((build/'vdot-perf.elf').read_bytes());data=bytes(v&255 for v in manifest['inputs'][0])
    outcomes=[]
    def reject(name,action,fragment):
        try:action()
        except ValueError as exc:
            message=str(exc);e.g.require(fragment in message,'wrong rejection: '+name+': '+message)
            outcomes.append(dict(name=name,rejected=True,reason=message))
        else:raise ValueError('accepted broken boundary: '+name)
    def words(name):
        raw=elf.symbol_data(name);return list(struct.unpack('<'+'I'*(len(raw)//4),raw))
    def change(name,before,after,last=False):
        values=words(name);indices=[i for i,w in enumerate(values) if w==before]
        e.g.require(indices and (last or len(indices)==1),'actual GNU mutation location: '+name)
        return ChangedFunction(elf,name,indices[-1] if last else indices[0],after)
    # Exact selected GNU words, from the actual qualified ELF, not guessed C paths.
    cases=[
        ('split-stale-x','fixed_split',0x02098993,0x00098993,False,6,'split step arguments/stale x/output stride'),
        ('split-slot-overwrite','fixed_split',0x08048493,0x00048493,False,6,'split step arguments/stale x/output stride'),
        ('split-tight-y-overlap','fixed_split',0x00591713,0x00491713,False,6,'all intermediate tight outputs'),
        ('packed-stale-x','fixed_packed',0x02040413,0x00040413,True,0,'packed A/x content at actual leaf call'),
    ]
    for label,name,before,after,last,row_id,fragment in cases:
        changed=change(name,before,after,last)
        # With only one step the bad inter-step update is dead; N=4 must catch it.
        e.traced.path(changed,manifest['rows'][row_id],data)
        reject(label,lambda:e.traced.path(changed,manifest['rows'][row_id+13],data),fragment)
        outcomes[-1].update(n1_passed=True,n4_rejected=True,before=f'{before:08x}',after=f'{after:08x}')
    changed=change('fixed_split',0x03853a03,0x00300a13)
    reject('omit-fourth-step-count3',lambda:e.traced.path(changed,manifest['rows'][19],data),'stream call cardinality')
    changed=change('fixed_packed',0x10078613,0x08078613)
    reject('half-weight-preparation',lambda:e.traced.path(changed,manifest['rows'][13],data),'packed A/x content at actual leaf call')
    vdot=words(e.gen.NEW[0]);i=next(j for j,w in enumerate(vdot) if w&0xfe00707f==0x0200000b)
    changed=ChangedFunction(elf,e.gen.NEW[0],i,vdot[i]^(1<<20))
    reject('arithmetic-source-bit',lambda:e.gen.machine_certificate(elf.symbol_data(e.gen.LEAVES[0][0]),changed.raw,0),
        'unapproved split machine word change')
    # a3 retains the selected step's slot base. This load is architecturally
    # discarded, but it would access packed scratch from the no-copy interface.
    i=max(j for j,w in enumerate(vdot) if w==0x010f8f93)
    delta=elf.symbols['fixed_packed_buffer'][0]-elf.symbols['fixed_slots'][0]
    e.g.require(-2048<=delta<2048,'discarded-load immediate')
    load=((delta&4095)<<20)|(13<<15)|(4<<12)|0x03
    changed=ChangedFunction(elf,e.gen.NEW[0],i,load)
    reject('discarded-packed-read',lambda:e.traced.path(changed,manifest['rows'][6],data),
        'split scalar load intersects old packed input')
    outcomes.extend(selection_tests(manifest))
    if run is None:
        return dict(status='FIXED_WEIGHT_ELF_AND_SELECTION_NEGATIVES_PASS',contract=e.CONTRACT,checks=outcomes,
            image_sha256=valid['image_sha256'],source_sha256=e.g.sha(__file__),new_emu_runs=0,
            scope='actual ELF paths and synthetic selection boundaries; no raw-runtime qualification')
    directory=run/'runs/recovery';receipt=e.read(directory/'result.json')
    baseline=e.normal(repo,build,directory,receipt)
    with tempfile.TemporaryDirectory(prefix='fixed-raw-negative-') as tmp:
        dest=Path(tmp);shutil.copyfile(directory/'stdout.log',dest/'stdout.log')
        raw=(directory/'stderr.log').read_text()
        mutated,count=re.subn(r'(?m)^(T13_COUNTER_ENQUEUE [^\n]*? rob=)([01])(:)',
            lambda m:m[1]+str(1-int(m[2]))+m[3],raw,count=1)
        e.g.require(count==1,'actual counter identity event')
        (dest/'stderr.log').write_text(mutated)
        reject('raw-counter-rob-flag',lambda:e.normal(repo,build,dest,receipt),'counter identity mismatch')
    return dict(status='FIXED_WEIGHT_TARGETED_NEGATIVES_PASS',contract=e.CONTRACT,new_emu_runs=0,checks=outcomes,
        image_sha256=valid['image_sha256'],manifest_sha256=e.g.sha(build/'source/manifest.json'),
        source_sha256=e.g.sha(__file__),normal_validation_sha256=e.digest((directory/'validation.json').read_bytes()),
        committed_vdot=baseline['committed_vdot'],scope='address/control/identity rejection and integer boundaries; vector values require independent oracle')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--run',type=Path)
    a=p.parse_args();out=a.output.resolve();e.g.require(not out.exists(),'fresh mutation report')
    e.parent.outside_inputs(out,[e.ROOT,a.build.resolve()]+([a.run.resolve()] if a.run else []))
    result=tests(e.ROOT,a.build.resolve(),a.run.resolve() if a.run else None);e.g.save(out,result);print(result)
