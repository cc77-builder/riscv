"""New lifecycle/plan; unchanged qualified packed and split arithmetic leaves."""
from pathlib import Path
import importlib.util
import json
import shutil

HERE=Path(__file__).resolve().parent
REL=Path('team/optimizations/o2/r2-config-reuse/caller/fixed-weight')
CONTRACT='r2-s3-fixed-weight-8x32-v1'
BASE='3d56e84aca5cc63bf235f6fbcf76ce8079c9581c'
MAX_CYCLES=8000000
spec=importlib.util.spec_from_file_location('fixed_split_generator',HERE.parent/'split/generate.py')
up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
LEAVES,NEW,CONFIG,S0,FIRST=up.LEAVES,up.NEW,up.CONFIG,up.S0,up.FIRST
INPUT_PINS,raw,machine_certificate=up.INPUT_PINS,up.raw,up.machine_certificate
FILES=up.FILES+('fixed.h','fixed.c')

def generate(repo,out,base_inputs):
    manifest=up.generate(repo,out,base_inputs)
    out=Path(out)
    for name in ('fixed.h','fixed.c','main.c'):shutil.copyfile(HERE/name,out/name)
    (out/'Makefile').write_text(up.MAKEFILE.replace(
        'main.c caller.c split.c timers.S','main.c fixed.c timers.S'))
    inputs=[]
    for packed in manifest['inputs']:
        a,x=packed[:256],packed[256:]
        sequence=[((x[k]+t*(11+2*k)+128)%256)-128 for t in range(4) for k in range(32)]
        inputs.append(a+sequence)
    for values in inputs[:3]:
        golden=[[sum(values[r*32+k]*values[256+t*32+k] for k in range(32)) for r in range(8)] for t in range(4)]
        up.need(all(golden[i]!=golden[i-1] for i in range(1,4)), 'representative stream must detect stale x')
    rows=[]
    for count in (1,4):
        for mode in ('packed','split'):
            for i,leaf in enumerate(LEAVES):
                rows.append(dict(id=len(rows),mode=mode,algorithm=i,method='vdot' if i==0 else 'rvv',
                    scope='complete_stream',scenario='fixed-weight',n=count,dots=32*count if i==0 else 0,
                    leaf=NEW[i] if mode=='split' else leaf[0],
                    wrapper='fixed_split' if mode=='split' else 'fixed_packed',anchor=False))
        rows.append(dict(rows[-6],id=len(rows),anchor=True))
    plan=[]
    for d in range(3):
        for group,count in enumerate((1,4)):
            for rep in range(6):
                order=list(range(12))[::1 if rep%2==0 else -1]
                for j,index in enumerate([12]+order+[12]):
                    plan.append(dict(index=group*13+index,dataset=d,repeat=rep,
                        phase='first' if rep==0 else 'warmup' if rep==1 else 'measured',
                        order_group=rep%2,anchor_position=('start' if j==0 else 'end') if index==12 else None))
    header=['#include "fixed.h"',f'#define FIXED_CONTRACT "{CONTRACT}"',f'#define FIXED_WINDOWS {len(plan)}',
            'static const int8_t fixed_inputs[7][384] __attribute__((aligned(16),used)) = {']
    header+=['{'+','.join(map(str,values))+'},' for values in inputs]+['};']
    header+=['extern void '+row[0]+'(const int8_t *,void *);' for row in LEAVES]
    header+=['caller_leaf const packed_entries[6]={'+','.join(row[0] for row in LEAVES)+'};',
             'split_leaf const split_entries[6]={'+','.join(NEW)+'};']
    (out/'data.h').write_text('\n'.join(header)+'\n')
    functional_vdot_steps=7*2*2*4
    measured_vdot_steps=sum(rows[s['index']]['n'] for s in plan if rows[s['index']]['method']=='vdot')
    manifest=dict(contract=CONTRACT,source_base=BASE,dataset=-1,datasets=[0,1,2],shape=[8,32],counts=[1,4],
        primary_count=4,inputs=inputs,rows=rows,plan=plan,custom_mask=0xfe00707f,custom_match=0x0200000b,
        functional_calls=168,judge_fault_controls=8,functional_vdot_steps=functional_vdot_steps,
        measured_vdot_steps=measured_vdot_steps,expected_dots=32*(functional_vdot_steps+measured_vdot_steps),
        formal_method_windows=288,formal_anchor_windows=48,max_cycles=MAX_CYCLES,
        conditioning='one split/firstdot-RVV stream of matching N before every complete measurement',
        primary_metric='complete stream including one-time packed A copy and every step; no component subtraction',
        hardware_changed=False,stable_default_changed=False,normal_uart_deferred=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
