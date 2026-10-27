"""Small independent negative checks over actual ELF and completed raw evidence.

No new EMU, no mutation of a frozen artifact. Machine words are changed through
an in-memory view; the raw counter fault is injected into a temporary copy.
Threshold checks use exact integer boundary cases, not the measured result.
"""
import argparse
import copy
from pathlib import Path
import re
import shutil
import struct
import tempfile
import run as e


class ChangedLeaf:
    def __init__(self, elf, name, index, word):
        self.elf, self.name, self.symbols = elf, name, elf.symbols
        raw = bytearray(elf.symbol_data(name))
        struct.pack_into('<I', raw, index*4, word)
        self.raw = bytes(raw)

    def symbol_data(self, name):
        return self.raw if name == self.name else self.elf.symbol_data(name)


def tests(repo, build, run):
    e.verification(repo, build)
    manifest=e.read(build/'source/manifest.json')
    elf=e.g.ELF((build/'vdot-perf.elf').read_bytes())
    outcomes=[]

    def reject(name, action, fragment):
        try:
            action()
        except ValueError as exc:
            message=str(exc)
            e.g.require(fragment in message, 'wrong mutation rejection: '+name+': '+message)
            outcomes.append(dict(name=name,rejected=True,reason=message))
        else:
            raise ValueError('mutation incorrectly accepted: '+name)

    def words(kind):
        return list(struct.unpack('<'+'I'*(e.gen.LEAVES[kind][1]//4),elf.symbol_data(e.gen.NEW[kind])))

    vdot=words(0)
    i=next(j for j,w in enumerate(vdot) if w&0xfe00707f==0x0200000b)
    changed=ChangedLeaf(elf,e.gen.NEW[0],i,vdot[i]^(1<<20))
    reject('arithmetic-source-bit',lambda:e.gen.machine_certificate(
        elf.symbol_data(e.gen.LEAVES[0][0]),changed.raw,0),'unapproved split machine word change')

    first=words(4)
    i=next(j for j,w in enumerate(first) if w&0x707f==0x7057 and (w>>15)&31==16)
    changed=ChangedLeaf(elf,e.gen.NEW[4],i,(first[i]&~(31<<15))|(8<<15))
    data=bytes(v&255 for v in manifest['inputs'][0])
    reject('actual-vl16-to-vl8',lambda:e.traced.path(changed,manifest['rows'][10],data),'complete X vector read coverage')

    i=next(j for j,w in enumerate(first) if w&127==0x07)
    changed=ChangedLeaf(elf,e.gen.NEW[4],i,first[i]&~(1<<25))
    reject('masked-vector-load',lambda:e.traced.path(changed,manifest['rows'][10],data),'unsupported vector memory encoding/state')

    # a3 still points to slots[0], 304 bytes after old packed[0]. The final
    # t6 += 16 is dead after the last full-vector store, so this discarded load
    # preserves outputs and control while violating the no-copy contract.
    i=max(j for j,w in enumerate(vdot) if w==0x010f8f93)
    load=((-304&4095)<<20)|(13<<15)|(4<<12)|0x03
    changed=ChangedLeaf(elf,e.gen.NEW[0],i,load)
    reject('discarded-old-packed-read',lambda:e.traced.path(changed,manifest['rows'][6],data),
           'split scalar load intersects old packed input')

    directory=run/'runs/recovery'
    receipt=e.read(directory/'result.json')
    e.normal(repo,build,directory,receipt)
    with tempfile.TemporaryDirectory(prefix='split-counter-mutation-') as tmp:
        dest=Path(tmp)
        shutil.copyfile(directory/'stdout.log',dest/'stdout.log')
        raw=(directory/'stderr.log').read_text()
        pattern=r'(?m)^(T13_COUNTER_ENQUEUE [^\n]*? rob=)([01])(:)'
        mutated,count=re.subn(pattern,lambda m:m[1]+str(1-int(m[2]))+m[3],raw,count=1)
        e.g.require(count==1,'actual counter event for mutation')
        (dest/'stderr.log').write_text(mutated)
        reject('raw-counter-rob-flag',lambda:e.normal(repo,build,dest,receipt),'counter identity mismatch')

    def synthetic(packed=20000,split=19000,anchor=100):
        result=[]
        for step in manifest['plan']:
            row=manifest['rows'][step['index']]
            result.append(dict(id=row['id'],phase=step['phase'],repeat=step['repeat'],dataset=step['dataset'],
                order_group=step['order_group'],anchor_position=step['anchor_position'],instructions=1,
                cycles=anchor if row['id']==12 else packed if row['id']<6 else split))
        return result

    boundary=synthetic()
    for s in boundary:
        if s['id']==12 and s['anchor_position']=='end':s['cycles']=101
    result=e.selection(boundary,manifest)
    e.g.require(result['interface_qualified'] and all(a['passed'] for a in result['anchors']),
                'exact 5% interface and 1% anchor must pass')
    bad=copy.deepcopy(boundary)
    next(s for s in bad if s['id']==12 and s['phase']=='measured' and s['anchor_position']=='end')['cycles']+=1
    e.g.require(e.selection(bad,manifest)['decision']=='HOLD_CONTEXT_VARIATION','above 1% anchor must hold')
    bad=synthetic()
    next(s for s in bad if s['id']==6 and s['phase']=='measured')['cycles']+=1
    e.g.require(e.selection(bad,manifest)['decision']=='STOP_INTERFACE','below 5% total reduction must stop')
    outcomes.append(dict(name='integer-interface-and-anchor-boundaries',passed=True))

    boundary=synthetic()
    for s in boundary:
        if 6<=s['id']<12:s['cycles']=20200 if s['dataset']==0 else 18000
    e.g.require(e.selection(boundary,manifest)['interface_qualified'],'exact 1% dataset regression must pass')
    next(s for s in boundary if s['id']==6 and s['dataset']==0 and s['phase']=='measured')['cycles']+=1
    e.g.require(not e.selection(boundary,manifest)['interface_qualified'],'above 1% dataset regression must fail')
    outcomes.append(dict(name='integer-dataset-regression-boundary',passed=True))

    boundary=synthetic(packed=25000,split=20000)
    for s in boundary:
        if s['id']==6:s['cycles']=19900
    e.g.require(e.selection(boundary,manifest)['decision']=='VDOT_PREFERRED_IN_THIS_PLAN','exact 0.5% VDot must pass')
    next(s for s in boundary if s['id']==6 and s['phase']=='measured')['cycles']+=1
    e.g.require(e.selection(boundary,manifest)['decision']=='KEEP_RVV_EXPLICIT','below 0.5% in one cell must not prefer VDot')
    outcomes.append(dict(name='integer-six-cell-vdot-boundary',passed=True))
    return dict(status='SPLIT_TARGETED_NEGATIVE_CHECKS_PASS',new_emu_runs=0,checks=outcomes,
                image_sha256=e.g.sha(build/'vdot-perf.bin'),source_sha256=e.g.sha(__file__))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    e.g.require(not out.exists(),'fresh mutation report required')
    e.parent.outside_inputs(out,[e.ROOT,a.build.resolve(),a.run.resolve()])
    result=tests(e.ROOT,a.build.resolve(),a.run.resolve());e.g.save(out,result)
    print(result)
